# Changelog

## 1.3.0

- Added dual-target builds for Claude and ChatGPT.
- Preserved seven independent skills for precise ChatGPT triggering.
- Added ChatGPT `agents/openai.yaml` metadata overlays.
- Made all built skills self-contained by vendoring shared references and required cross-skill generator files at build time.
- Centralized duplicate McCombs branding assets and the case document generator in `src/shared/`.
- Replaced Claude-specific wording and tool references with platform-neutral instructions.
- Added deterministic build, validation, and distribution scripts.
- Added a ChatGPT installer bundle containing seven separately uploadable `skill.zip` packages.

## 1.2.0

- Original Claude plugin release supplied as the migration source.
