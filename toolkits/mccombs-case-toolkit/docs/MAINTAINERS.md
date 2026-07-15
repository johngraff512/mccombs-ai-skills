# Maintainer Guide

## Source of truth

Edit skill-specific content under `src/skills/<skill-name>/`. Edit shared content once under `src/shared/`.

Do not edit files under `build/` or `dist/`; they are regenerated.

## Shared-resource injection

`toolkit.json` lists every file copied into each skill at build time. This solves two portability problems:

1. Independent ChatGPT skills cannot reference `../shared/`.
2. The Fact-Checker and Refresher need the Case Generator document script even when installed alone.

## Platform metadata

- ChatGPT display metadata: `platforms/chatgpt/agents/*.yaml`
- Claude plugin metadata: `platforms/claude/.claude-plugin/plugin.json`

Keep platform-specific tool names out of canonical `SKILL.md` files. Prefer phrases such as “read the uploaded document,” “search current sources,” and “edit the file.”

## Release process

1. Update `VERSION`, `toolkit.json`, the Claude plugin manifest, and version notes in the seven `SKILL.md` files.
2. Update `CHANGELOG.md`.
3. Run `python3 scripts/build.py --clean --target all`.
4. Run `python3 scripts/validate.py`.
5. Smoke-test at least one Word generator and the slide generator in an environment with the declared Node dependencies.
6. Publish the source ZIP, Claude plugin ZIP, and ChatGPT distribution bundle.
