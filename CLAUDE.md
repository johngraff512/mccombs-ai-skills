# CLAUDE.md — mccombs-ai-skills

Cross-platform AI skills repository for McCombs faculty. One skill authored once in the [Agent Skills open standard](https://agentskills.io/specification) format, distributed to both Claude EDU and ChatGPT. Owner: John Graff (johngraff512). Public repo; catalog published via GitHub Pages from `/docs` on `master`.

## Architecture (read before editing)

- `plugins/<name>/skills/<skill>/` — installable skills. For most plugins this is the source of truth. **Exception:** `plugins/mccombs-case-toolkit/` is BUILT OUTPUT — never edit it directly.
- `toolkits/mccombs-case-toolkit/` — canonical source for the case toolkit: `src/skills/` + `src/shared/` (shared resources injected per-skill at build time via `toolkit.json`), `platforms/` overlays (ChatGPT yaml, Claude plugin.json), own `scripts/build.py` and `scripts/validate.py`. After editing source: `python3 toolkits/mccombs-case-toolkit/scripts/build.py --clean --target claude`, copy `build/claude/skills` over `plugins/mccombs-case-toolkit/skills`, commit both. CI has a drift check that fails if they diverge.
- `scripts/check_skills.py` — spec validator + platform classifier. Classifications: `both`, `both-with-caveats`, `claude-code-only` (badge: "Needs local software"; triggered by allowed-tools containing `Bash(`), `claude-only` (MCP/local-Claude deps). Signals must stay in plain faculty-facing language.
- `scripts/package_skills.py` — per-skill zips + `<plugin>-plugin.zip` bundles into `dist/` (gitignored).
- `scripts/build_catalog.py` — generates `docs/index.html` + per-skill pages (`docs/skills/`) + toolkit pages (`docs/toolkits/`) from `docs/compat-report.json`. A plugin gets a "Plug-in" card only if `toolkits/<name>/` exists. Faculty-facing terminology: "Plug-in (for Claude only)" — plug-ins work on claude.ai web, desktop, Cowork, and Claude Code (verified: support.claude.com/en/articles/13837440); ChatGPT has no plug-ins.
- `.github/workflows/validate.yml` — PR/push: validate → drift check → package → catalog (committed back on master by CI). Tags `v*`: release with all zips including toolkit platform bundles built from source.

## Conventions

- Frontmatter: spec fields only (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`). Every skill should carry `metadata.category` (one of: Case Writing, Class Preparation, Slides & Presentations, Research & Summaries, Decision Support, General), `metadata.version` — bump version on every content change; the catalog surfaces it to faculty — and `metadata.summary`: one plain-English sentence (<200 chars) shown on catalog cards; without it the catalog falls back to truncating the description, which reads poorly.
- No `../` references escaping a skill folder (packager bundles them as a workaround, but fix at source; case toolkit solves this via build-time injection).
- Contributor flow: PR (web upload path documented in CONTRIBUTING.md for non-Git faculty) → CI checks → maintainer merge → tag release. Contact: john.graff@mccombs.utexas.edu.
- `business-ai-tools` skills are adapted from Ben Bentzin's MIT repo (github.com/AI-Business-Tools/claude-code) — keep attribution; upstream sync is manual. Known upstream issues we fixed locally: beamer YAML quoting + description length.

## Release checklist

1. `python3 scripts/check_skills.py --strict --json docs/compat-report.json`
2. If toolkit source changed: rebuild (see above) and verify drift check passes locally: `diff -r toolkits/mccombs-case-toolkit/build/claude/skills plugins/mccombs-case-toolkit/skills`
3. `python3 scripts/build_catalog.py` and eyeball `docs/index.html` — requires the `markdown` package (CI installs it; without it every detail page silently degrades to `<pre>` rendering)
4. Update CHANGELOG.md; commit; push; `git tag v0.x.y && git push --tags`
5. Verify: Actions green, release assets present, catalog live at johngraff512.github.io/mccombs-ai-skills

## Related context outside this repo

- SharePoint draft page "AI Skills for Teaching & Learning" on the MOII Faculty Working Group site (John publishes when ready).
- UT admin path: Claude EDU org skill provisioning and ChatGPT workspace skill publishing can pull from this repo's releases — pending discussion with UT-IT.
