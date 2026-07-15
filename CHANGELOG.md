# Changelog

## v0.1.0 — 2026-07-14

Initial scaffold.

- `mccombs-case-toolkit` v1.2.0 (8 skills, John Graff)
- `business-ai-tools` v1.0.0 (4 skills adapted from Ben Bentzin's [claude-code repo](https://github.com/AI-Business-Tools/claude-code), MIT)
- CI: spec validation, cross-platform classification, zip packaging, catalog generation

## v0.1.2 — 2026-07-15

- Catalog: category filter buttons; per-skill version and last-updated date; toolkit cards show plugin version.
- All 12 skills tagged with `metadata.category` and `metadata.version` in frontmatter (spec-standard fields, safe on both platforms).
- Validator now warns when a skill lacks category or version metadata.
