# McCombs AI Skills

A shared repository of AI skills for teaching and learning at the McCombs School of Business, UT Austin. One skill, authored once in the [Agent Skills open standard](https://agentskills.io/specification), distributed to both platforms UT has standardized on: **Claude EDU** and **ChatGPT**.

Maintained by the AI Faculty Working Group.

## For faculty: installing a skill

Browse the **[skill catalog](https://johngraff512.github.io/mccombs-ai-skills/)** — each skill card shows a compatibility badge and install buttons.

| Platform | How to install |
|---|---|
| **Claude (EDU / desktop)** | Settings → Capabilities → Skills → Upload skill → choose the skill's `.zip` from the catalog |
| **Claude Code** | `/plugin marketplace add johngraff512/mccombs-ai-skills` then `/plugin install mccombs-case-toolkit` |
| **ChatGPT (UT workspace)** | Skills → Create → Upload from your computer → choose the same `.zip` |

Claude Code marketplace installs update automatically. ChatGPT and manual Claude uploads are point-in-time copies — the catalog page shows version numbers and update dates so you know when to re-download.

## What's in the repo

| Plugin | Skills | Author |
|---|---|---|
| `mccombs-case-toolkit` | case-idea-generator, case-generator, case-factcheck, teaching-note-generator, class-exercise-generator, slide-generator, case-refresher, mccombs-slides | John Graff |
| `business-ai-tools` | ai-council, summary-academic, summary-general, beamer | [Ben Bentzin](https://github.com/AI-Business-Tools/claude-code) (MIT) |

## For contributors: submitting or updating a skill

1. Fork/branch, add your skill folder under `plugins/<plugin>/skills/<skill-name>/` (must contain `SKILL.md`; see the [spec](https://agentskills.io/specification)).
2. Open a pull request — the template walks you through the checklist, including a **manual test on both platforms**.
3. CI automatically validates every PR:
   - **Spec compliance** — frontmatter fields, naming rules, description limits, oversized SKILL.md
   - **Cross-platform classification** — each skill is tagged `Both platforms`, `Both (see notes)`, or `Claude only`, based on Claude-specific frontmatter, bundled scripts, MCP dependencies, and external file references
4. A working-group maintainer reviews and merges. On merge, the catalog regenerates; on a version tag (`git tag v0.2.0 && git push --tags`), zips are published to a GitHub Release that the catalog links to.

Run the checks locally before pushing:

```bash
pip install pyyaml
python3 scripts/check_skills.py                 # validation + compatibility report
python3 scripts/package_skills.py               # build zips into dist/
python3 scripts/check_skills.py --json docs/compat-report.json && python3 scripts/build_catalog.py
open docs/index.html                            # preview the catalog
```

## Repo layout

```
.claude-plugin/marketplace.json      Claude plugin marketplace manifest
plugins/<plugin>/
  .claude-plugin/plugin.json         Plugin metadata (name, version, author)
  skills/<skill-name>/SKILL.md       One folder per skill (Agent Skills spec)
scripts/check_skills.py              Spec validator + platform classifier (CI)
scripts/package_skills.py            Builds per-skill zips for ChatGPT upload
scripts/build_catalog.py             Generates docs/index.html (GitHub Pages)
.github/workflows/validate.yml       CI: validate → package → catalog → release
docs/                                Published catalog (enable Pages from /docs)
```

## One-time setup after pushing to GitHub

2. Repo Settings → Pages → Source: `main` branch, `/docs` folder.
3. Repo Settings → Actions → General → Workflow permissions: "Read and write" (lets CI commit the regenerated catalog).
4. Tag the first release: `git tag v0.1.0 && git push --tags`.

## Platform notes

- Skills follow the [Agent Skills specification](https://agentskills.io/specification); both OpenAI and Anthropic products read the same `SKILL.md` format.
- Claude-specific frontmatter (`allowed-tools`, `model`, `triggers`, etc.) is ignored by other platforms — skills still load, but behavior may differ. The classifier flags these.
- Skills bundling scripts require code execution to be enabled on the platform.
- If UT admins centrally provision skills (Claude EDU org skills / ChatGPT workspace publishing), they should pull from this repo's latest release.

## License

Repository tooling: MIT. Each plugin/skill carries its own license and attribution — see plugin.json files. `business-ai-tools` skills are MIT, © Ben Bentzin.
