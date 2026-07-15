#!/usr/bin/env python3
"""Validate source integrity and built packages for the McCombs Case Toolkit."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "toolkit.json").read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    expected = set(MANIFEST["skills"])
    actual = {p.name for p in (ROOT / "src" / "skills").iterdir() if p.is_dir()}
    if expected != actual:
        errors.append(f"Skill set mismatch: expected {sorted(expected)}, found {sorted(actual)}")

    for path in (ROOT / "src").rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if "Claude will" in text or "should Claude" in text:
            errors.append(f"Platform-specific wording remains in {path}")

    for path in (ROOT / "src").rglob("*.js"):
        result = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
        if result.returncode:
            errors.append(f"JavaScript syntax error in {path}: {result.stderr.strip()}")

    for target in ("chatgpt", "claude"):
        build_dir = ROOT / "build" / target / "skills"
        if build_dir.exists():
            for skill in build_dir.iterdir():
                if not (skill / "SKILL.md").exists():
                    errors.append(f"Missing SKILL.md in {skill}")
                if target == "chatgpt" and not (skill / "agents" / "openai.yaml").exists():
                    errors.append(f"Missing ChatGPT metadata in {skill}")

    for skill_name in expected:
        archive = ROOT / "dist" / "chatgpt" / skill_name / "skill.zip"
        if archive.exists():
            with zipfile.ZipFile(archive) as zf:
                names = set(zf.namelist())
                if f"{skill_name}/SKILL.md" not in names:
                    errors.append(f"Incorrect root layout in {archive}")
                if f"{skill_name}/agents/openai.yaml" not in names:
                    errors.append(f"Missing agents/openai.yaml in {archive}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Validation passed for source, staged skills, and package layouts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
