#!/usr/bin/env python3
"""Validate skills against the Agent Skills spec and classify platform compatibility.

Spec reference: https://agentskills.io/specification
Frontmatter fields defined by the spec: name, description (required);
license, compatibility, metadata, allowed-tools (optional).

Classification:
  both              - clean cross-platform skill (Claude EDU + ChatGPT)
  both-with-caveats - works on both, but has Claude-specific frontmatter
                      (ignored elsewhere) and/or bundled scripts that need
                      code execution enabled on the platform
  claude-only       - hard dependency on Claude-side features (MCP tools,
                      ~/.claude paths, session transcripts, subagents)

Usage:
  python3 scripts/check_skills.py [--strict] [--json PATH]
  --strict : exit 1 on any ERROR (use in CI)
  --json   : also write a machine-readable report (used by build_catalog.py)
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
PLUGINS_DIR = ROOT / "plugins"

SPEC_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
# Non-spec fields commonly used by Claude Code / Claude apps. Other platforms ignore them.
CLAUDE_FIELDS = {"triggers", "model", "effort", "argument-hint", "context", "hooks", "disable-model-invocation"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# Hard Claude-only dependency signals (body text)
CLAUDE_ONLY_PATTERNS = [
    (re.compile(r"\bmcp__\w+"), "references MCP connector tools"),
    (re.compile(r"~/\.claude\b|\.claude/skills"), "depends on local Claude environment paths"),
    (re.compile(r"\bsession transcripts?\b", re.I), "depends on Claude session transcripts"),
]
# Soft Claude-leaning signals (work elsewhere, degraded or ignored)
CLAUDE_SOFT_PATTERNS = [
    (re.compile(r"\bClaude Code\b"), "written with Claude Code in mind"),
    (re.compile(r"\bsub-?agents?\b", re.I), "uses subagents (Claude feature)"),
]
SCRIPT_EXTS = {".py", ".sh", ".js", ".ts", ".rb"}
MD_REF_RE = re.compile(r"\]\(([^)#][^)]*)\)|(?:^|[\s`(])((?:scripts/|references/|assets/)[\w\-./]+)", re.M)
EXT_REF_RE = re.compile(r"\.\./[\w\-./]+")


def parse_frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return None, "missing or malformed YAML frontmatter block"
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        return None, f"frontmatter is not valid YAML: {e}"
    if not isinstance(fm, dict):
        return None, "frontmatter did not parse to a mapping"
    return fm, None


def check_skill(skill_dir: Path):
    r = {
        "skill": skill_dir.name,
        "plugin": skill_dir.parent.parent.name,
        "errors": [], "warnings": [], "signals": [],
        "classification": "both",
        "description": "", "version": None, "license": None, "category": "General",
    }
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        r["errors"].append("SKILL.md missing")
        return r
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    fm, err = parse_frontmatter(text)
    if err:
        r["errors"].append(err)
        return r

    # --- spec compliance ---
    name = fm.get("name")
    if not name:
        r["errors"].append("frontmatter missing required 'name'")
    else:
        if not NAME_RE.match(str(name)):
            r["errors"].append(f"name '{name}' violates spec (lowercase alphanumerics and single hyphens)")
        if len(str(name)) > 64:
            r["errors"].append("name exceeds 64 characters")
        if str(name) != skill_dir.name:
            r["errors"].append(f"name '{name}' does not match directory '{skill_dir.name}'")

    desc = fm.get("description")
    if not desc or not str(desc).strip():
        r["errors"].append("frontmatter missing required 'description'")
    elif len(str(desc)) > 1024:
        r["errors"].append(f"description is {len(str(desc))} chars (spec max 1024)")
    r["description"] = str(desc or "")[:300]

    compat = fm.get("compatibility")
    if compat and len(str(compat)) > 500:
        r["errors"].append("compatibility field exceeds 500 characters")

    meta = fm.get("metadata") or {}
    if isinstance(meta, dict):
        r["version"] = meta.get("version")
        r["category"] = meta.get("category", "General")
        if "category" not in meta:
            r["warnings"].append("no metadata.category — will show as 'General' in the catalog")
        if "version" not in meta:
            r["warnings"].append("no metadata.version — updates won't be visible to faculty; add one")
    r["license"] = fm.get("license")

    body_lines = text.count("\n") + 1
    if body_lines > 500:
        r["warnings"].append(f"SKILL.md is {body_lines} lines (spec recommends <500; move detail to references/)")

    unknown = set(fm) - SPEC_FIELDS
    claude_fields = unknown & CLAUDE_FIELDS
    truly_unknown = unknown - CLAUDE_FIELDS
    if claude_fields:
        r["signals"].append(f"Claude-specific frontmatter (ignored on other platforms): {', '.join(sorted(claude_fields))}")
    if truly_unknown:
        r["warnings"].append(f"unknown frontmatter fields: {', '.join(sorted(truly_unknown))}")

    # --- file references ---
    for ref in sorted(set(EXT_REF_RE.findall(text))):
        r["warnings"].append(
            f"external reference '{ref}' escapes the skill folder — breaks when the skill "
            "is packaged standalone (e.g. ChatGPT zip upload); bundle the file inside the skill instead")
        if "has external file references" not in r["signals"]:
            r["signals"].append("has external file references")
    for m in MD_REF_RE.finditer(text):
        ref = (m.group(1) or m.group(2) or "").strip()
        if not ref or ref.startswith(("http://", "https://", "mailto:", "../")):
            continue
        if "/" in ref and not (skill_dir / ref).exists():
            r["warnings"].append(f"referenced file not found: {ref}")

    # --- platform classification ---
    hard, soft = [], []
    for pat, why in CLAUDE_ONLY_PATTERNS:
        if pat.search(text):
            hard.append(why)
    for pat, why in CLAUDE_SOFT_PATTERNS:
        if pat.search(text):
            soft.append(why)

    scripts = [p for p in skill_dir.rglob("*") if p.suffix in SCRIPT_EXTS]
    if scripts:
        soft.append(f"bundles {len(scripts)} script(s) — requires code execution enabled on the platform")
    at = str(fm.get("allowed-tools", ""))
    if "Bash(" in at or re.search(r"\b(Agent|Task|Skill)\b", at):
        soft.append("allowed-tools pre-approves shell/agent tools (Claude Code oriented)")

    r["signals"].extend(hard + soft)
    if hard:
        r["classification"] = "claude-only"
    elif soft or claude_fields:
        r["classification"] = "both-with-caveats"
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    results = []
    for plugin_dir in sorted(PLUGINS_DIR.iterdir()):
        skills_dir = plugin_dir / "skills"
        if not skills_dir.is_dir():
            continue
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            if not (skill_dir / "SKILL.md").exists():
                print(f"  (info) {plugin_dir.name}/{skill_dir.name}: no SKILL.md — treated as shared resources, skipped")
                continue
            results.append(check_skill(skill_dir))

    n_err = sum(len(r["errors"]) for r in results)
    badge = {"both": "BOTH PLATFORMS", "both-with-caveats": "BOTH (caveats)", "claude-only": "CLAUDE ONLY"}
    print(f"\nChecked {len(results)} skills — {n_err} error(s)\n" + "=" * 72)
    for r in results:
        print(f"\n{r['plugin']}/{r['skill']}  [{badge[r['classification']]}]")
        for e in r["errors"]:
            print(f"  ERROR   {e}")
        for w in r["warnings"]:
            print(f"  WARN    {w}")
        for s in r["signals"]:
            print(f"  signal  {s}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(results, indent=2))
        print(f"\nJSON report: {args.json}")

    if args.strict and n_err:
        sys.exit(1)


if __name__ == "__main__":
    main()
