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
                    zf.write(f, f.relative_to(staged.parent))
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


if __name__ == "__main__":
    main()
