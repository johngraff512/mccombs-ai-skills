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

## v0.2.0 — 2026-07-15

- McCombs Case Toolkit v1.3.0: dual-platform source tree at `toolkits/mccombs-case-toolkit/` (canonical src + shared-resource injection + platform overlays). `plugins/mccombs-case-toolkit/` is now built output; CI enforces sync. Skills are fully self-contained — all external-reference warnings resolved.
- Integration edits to the toolkit (John notified): build.py frontmatter whitelist relaxed to allow spec-standard optional fields; `metadata.category`/`metadata.version` added to the 7 source SKILL.mds so catalog filtering and version display keep working.
- `mccombs-slides` moved to `community-skills` (it is not part of the case toolkit).
- Releases now include platform-specific toolkit bundles (Claude plugin zip + ChatGPT distribution bundle) built from source in CI.

## v0.2.1 — 2026-07-15

- Catalog: "Needs local software" skills (currently just `beamer`) now show a download link for their zip alongside the plugin-marketplace instructions, with guidance to unzip into `~/.claude/skills/` for Claude Code and a warning that uploading to claude.ai's hosted Skills won't work (required software isn't preinstalled there). Previously these skills had no download link even though the zip ships in every release.

## v0.3.0 — 2026-07-15

- Catalog redesigned for browsing at scale (app-store-style directory): compact card grid grouped by category, sticky toolbar with live search count, category chips with counts, and sort (by category / A–Z / recently updated). Install instructions moved off the cards — each card shows a one-sentence summary, compatibility badge, and platform marks, with full install steps on the skill's detail page.
- Skill detail pages redesigned: hero summary card, per-platform expandable install steps, "Good to know" compatibility notes, then the full README/SKILL.md. Toolkit page gets the same treatment.
- Dark-mode support across all catalog pages (follows the reader's system preference).
- New frontmatter convention: `metadata.summary` — a one-sentence plain-English summary shown on catalog cards. Added to all 12 skills; the validator now warns when it's missing and the catalog falls back to sentence-boundary truncation of the description.
- Versions bumped for the frontmatter addition: business-ai-tools and community-skills skills to 1.0.1; McCombs Case Toolkit to 1.3.1.
