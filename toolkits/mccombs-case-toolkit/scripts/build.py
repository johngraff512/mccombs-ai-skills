#!/usr/bin/env python3
"""Build the McCombs Case Toolkit for ChatGPT and Claude."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
BUILD = ROOT / "build"
DIST = ROOT / "dist"
MANIFEST = json.loads((ROOT / "toolkit.json").read_text(encoding="utf-8"))
VERSION = MANIFEST["version"]
MAX_SKILL_ZIP_BYTES = 25 * 1024 * 1024


def clean() -> None:
    shutil.rmtree(BUILD, ignore_errors=True)
    shutil.rmtree(DIST, ignore_errors=True)


def copy_resource(source_rel: str, dest: Path) -> None:
    source = SRC / source_rel
    if not source.exists():
        raise FileNotFoundError(f"Missing shared resource: {source}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)


def write_package_json(skill_dir: Path, skill_name: str, dependencies: dict[str, str]) -> None:
    if not dependencies:
        return
    package = {
        "name": f"mccombs-{skill_name}",
        "version": VERSION,
        "private": True,
        "description": f"Runtime dependencies for the {skill_name} skill.",
        "dependencies": dependencies,
    }
    (skill_dir / "package.json").write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")


def validate_frontmatter(skill_dir: Path) -> None:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        raise ValueError(f"Missing SKILL.md: {skill_dir}")
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"Invalid YAML frontmatter: {skill_md}")
    frontmatter = match.group(1)
    keys = []
    for line in frontmatter.splitlines():
        if line and not line.startswith((" ", "\t")) and ":" in line:
            keys.append(line.split(":", 1)[0].strip())
    allowed = {"name", "description", "license", "compatibility", "metadata"}
    if not {"name", "description"} <= set(keys) or not set(keys) <= allowed:
        raise ValueError(f"SKILL.md frontmatter must contain name and description, and only spec fields {sorted(allowed)}: {skill_md}")
    name_match = re.search(r"^name:\s*([^\n]+)$", frontmatter, flags=re.MULTILINE)
    if not name_match or not re.fullmatch(r"[a-z0-9-]+", name_match.group(1).strip().strip('"\'')):
        raise ValueError(f"Invalid skill name: {skill_md}")


def validate_skill(skill_dir: Path, chatgpt: bool) -> None:
    validate_frontmatter(skill_dir)
    if chatgpt and not (skill_dir / "agents" / "openai.yaml").exists():
        raise ValueError(f"Missing agents/openai.yaml: {skill_dir}")
    for path in skill_dir.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for forbidden in ("../shared/", "../case-generator/", "/path/to/skills/", "Claude will", "should Claude"):
            if forbidden in text:
                raise ValueError(f"Non-portable reference {forbidden!r} in {path}")
    for path in skill_dir.rglob("*.js"):
        if not path.read_text(encoding="utf-8").startswith("#!/usr/bin/env node"):
            raise ValueError(f"Expected Node shebang in {path}")


def stage_skill(skill_name: str, target: str) -> Path:
    source_skill = SRC / "skills" / skill_name
    if not source_skill.exists():
        raise FileNotFoundError(source_skill)
    skill_dir = BUILD / target / "skills" / skill_name
    if skill_dir.exists():
        shutil.rmtree(skill_dir)
    shutil.copytree(source_skill, skill_dir)
    config = MANIFEST["skills"][skill_name]
    for source_rel, dest_rel in config.get("copies", []):
        copy_resource(source_rel, skill_dir / dest_rel)
    write_package_json(skill_dir, skill_name, config.get("npm_dependencies", {}))
    if target == "chatgpt":
        agent_src = ROOT / "platforms" / "chatgpt" / "agents" / f"{skill_name}.yaml"
        agent_dst = skill_dir / "agents" / "openai.yaml"
        agent_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(agent_src, agent_dst)
    validate_skill(skill_dir, chatgpt=(target == "chatgpt"))
    return skill_dir


def zip_tree(source: Path, output: Path, include_root: bool = True) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source.rglob("*")):
            if not path.is_file():
                continue
            arc = path.relative_to(source.parent if include_root else source)
            info = zipfile.ZipInfo(str(arc).replace("\\", "/"), date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if path.suffix == ".js" else 0o644) << 16
            zf.writestr(info, path.read_bytes())


def build_chatgpt() -> list[Path]:
    outputs: list[Path] = []
    install_root = BUILD / "chatgpt-installer"
    if install_root.exists():
        shutil.rmtree(install_root)
    install_root.mkdir(parents=True, exist_ok=True)
    install_lines = [
        "# McCombs Case Toolkit 1.3.0 — ChatGPT Installation",
        "",
        "This is a distribution bundle, not a multi-skill upload. Unzip it first, then install each `skill.zip` separately.",
        "",
        "Recommended order:",
    ]
    for index, skill_name in enumerate(MANIFEST["skills"], start=1):
        skill_dir = stage_skill(skill_name, "chatgpt")
        out_dir = DIST / "chatgpt" / skill_name
        out = out_dir / "skill.zip"
        zip_tree(skill_dir, out, include_root=True)
        if out.stat().st_size > MAX_SKILL_ZIP_BYTES:
            raise ValueError(f"{out} exceeds the 25 MB ChatGPT upload limit")
        outputs.append(out)
        numbered = install_root / f"{index:02d}-{skill_name}"
        numbered.mkdir(parents=True, exist_ok=True)
        shutil.copy2(out, numbered / "skill.zip")
        install_lines.append(f"{index}. `{numbered.name}/skill.zip`")
    install_lines.extend([
        "",
        "After installation, use natural prompts such as ‘Fact-check this case’ or explicitly name the McCombs skill.",
    ])
    (install_root / "INSTALL.md").write_text("\n".join(install_lines) + "\n", encoding="utf-8")
    bundle = DIST / "chatgpt" / f"mccombs-case-toolkit-chatgpt-v{VERSION}.zip"
    zip_tree(install_root, bundle, include_root=False)
    outputs.append(bundle)
    return outputs


def build_claude() -> Path:
    plugin_root = BUILD / "claude-plugin"
    if plugin_root.exists():
        shutil.rmtree(plugin_root)
    (plugin_root / "skills").mkdir(parents=True, exist_ok=True)
    for skill_name in MANIFEST["skills"]:
        staged = stage_skill(skill_name, "claude")
        shutil.copytree(staged, plugin_root / "skills" / skill_name)
    shutil.copytree(ROOT / "platforms" / "claude" / ".claude-plugin", plugin_root / ".claude-plugin")
    shutil.copy2(ROOT / "platforms" / "claude" / "README.md", plugin_root / "README.md")
    shutil.copy2(ROOT / "VERSION", plugin_root / "VERSION")
    out = DIST / "claude" / f"mccombs-case-toolkit-v{VERSION}.zip"
    zip_tree(plugin_root, out, include_root=False)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=["all", "chatgpt", "claude"], default="all")
    parser.add_argument("--clean", action="store_true", help="Remove build and dist before building")
    args = parser.parse_args()
    if args.clean:
        clean()
    if args.target in {"all", "chatgpt"}:
        for path in build_chatgpt():
            print(path.relative_to(ROOT))
    if args.target in {"all", "claude"}:
        print(build_claude().relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
