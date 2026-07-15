# McCombs Case Toolkit

**Version 1.3.0**

A dual-target suite of seven AI-powered skills for case-based teaching at the McCombs School of Business, The University of Texas at Austin.

## What changed in 1.3

Version 1.3 introduces one canonical source tree with two build targets:

- **Claude:** one plugin ZIP containing all seven skills.
- **ChatGPT:** seven independent `skill.zip` packages, plus a convenience distribution bundle that must be unzipped before installation.

Shared references, branding assets, and the case document generator are maintained once under `src/shared/` and copied into self-contained skill packages during the build. Platform-specific metadata lives under `platforms/`.

## Skills

| Skill | Purpose |
|---|---|
| Case Idea Generator | Brainstorm 3–5 evidence-backed case concepts |
| Case Generator | Write a classroom-ready business case |
| Case Fact-Checker | Verify claims and produce an approved corrected case |
| Teaching Note Generator | Create an instructor guide and discussion plan |
| Class Exercise Generator | Design interactive classroom activities |
| Slide Generator | Build a McCombs-branded PowerPoint deck |
| Case Refresher | Update a case with current data and developments |

## Repository layout

```text
src/skills/                 Canonical skill-specific instructions and resources
src/shared/                 Shared references, scripts, and brand assets
platforms/chatgpt/          ChatGPT `agents/openai.yaml` overlays
platforms/claude/           Claude plugin manifest
scripts/build.py            Creates both distribution targets
scripts/validate.py         Checks source, scripts, and package layouts
dist/                       Generated packages; not source-controlled
```

## Build

Requires Python 3.10+ and Node.js for JavaScript syntax checks.

```bash
python3 scripts/build.py --clean --target all
python3 scripts/validate.py
```

Generated files:

```text
dist/chatgpt/<skill-name>/skill.zip
dist/chatgpt/mccombs-case-toolkit-chatgpt-v1.3.0.zip
dist/claude/mccombs-case-toolkit-v1.3.0.zip
```

The ChatGPT distribution bundle is not itself installable. Unzip it and install each enclosed `skill.zip` separately.

## Runtime dependencies

Document generators use the Node package `docx`; the slide generator uses `pptxgenjs`. Each built skill includes a small `package.json` declaring the dependency it needs. Managed AI environments may already provide these packages; local testing can use `npm install` inside the staged skill directory.

## Author

John Graff — McCombs School of Business, The University of Texas at Austin
