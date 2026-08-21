#!/usr/bin/env python3
"""Package each skill as a standalone zip for ChatGPT upload (and manual Claude upload).

Produces dist/<skill-name>.zip with the skill folder at the zip root, e.g.
  case-generator.zip
    case-generator/
      SKILL.md
      references/...

If a skill references files outside its folder (../shared/...), those files are
copied into the zip under the skill folder at _bundled/<original-path> and a
warning is printed — fix the SKILL.md reference or restructure the skill.
"""

import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
EXT_REF = re.compile(r"(\.\./[\w\-./]+)")

# Git does not preserve mtimes, so a fresh checkout would stamp every zip entry with
# the checkout time and produce byte-different archives from identical content. These
# zips are committed to docs/downloads/ and served from Pages, so that churn would add
# hundreds of KB to history on every CI run. Pin the timestamp: a zip changes only when
# a skill's content actually changes.
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)  # earliest value the zip format can represent


def _add(zf: zipfile.ZipFile, path: Path, arcname) -> None:
    """zf.write() with a fixed timestamp and normalised permissions."""
    info = zipfile.ZipInfo(str(arcname), date_time=ZIP_EPOCH)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    zf.writestr(info, path.read_bytes())


def package(skill_dir: Path) -> Path:
    DIST.mkdir(exist_ok=True)
    out = DIST / f"{skill_dir.name}.zip"
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8", errors="replace")
    external = [r for r in EXT_REF.findall(text) if (skill_dir / r).resolve().exists()]

    with tempfile.TemporaryDirectory() as td:
        staged = Path(td) / skill_dir.name
        shutil.copytree(skill_dir, staged)
        for ref in external:
            src = (skill_dir / ref).resolve()
            dest = staged / "_bundled" / src.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            print(f"  WARN {skill_dir.name}: bundled external reference {ref} -> _bundled/{src.name} "
                  "(update SKILL.md to reference it inside the skill)")
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(staged.rglob("*")):
                if f.is_file():
                    _add(zf, f, f.relative_to(staged.parent))
    return out


def package_plugin(plugin_dir: Path) -> Path:
    """Zip a whole plugin (all its skills + metadata) as <plugin>-plugin.zip."""
    DIST.mkdir(exist_ok=True)
    out = DIST / f"{plugin_dir.name}-plugin.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(plugin_dir.rglob("*")):
            if f.is_file():
                _add(zf, f, f.relative_to(plugin_dir.parent))
    return out


def main():
    count = 0
    for skill_md in sorted(ROOT.glob("plugins/*/skills/*/SKILL.md")):
        out = package(skill_md.parent)
        print(f"  built {out.relative_to(ROOT)}")
        count += 1
    print(f"\nPackaged {count} skills into {DIST.relative_to(ROOT)}/")
    if not count:
        sys.exit("No skills found under plugins/*/skills/")
    for plugin_dir in sorted(ROOT.glob("plugins/*")):
        if any(plugin_dir.glob("skills/*/SKILL.md")):
            out = package_plugin(plugin_dir)
            print(f"  built {out.relative_to(ROOT)} (full plugin)")


if __name__ == "__main__":
    main()
