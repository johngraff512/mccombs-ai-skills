---
name: mccombs-slides
description: Create branded PowerPoint presentations following McCombs School of Business style guidelines. Use when creating slides, presentations, or decks for UT Austin McCombs faculty, students, or events. Applies official brand colors (Burnt Orange #C05900), typography (Arial, Arial Black, Georgia), and layout standards. Triggers on requests mentioning McCombs, UT Austin business school, or branded presentation needs.
---

# McCombs Slides Skill

Create professional presentations that follow McCombs School of Business brand standards.

## Quick Reference

| Element | Specification |
|---------|---------------|
| Primary Color | Burnt Orange `#C05900` |
| Secondary Colors | Steel Gray `#9CACB6`, Dark Blue `#005E86` |
| Fonts | Arial (body), Arial Black (headlines), Georgia (serif accent) |
| Slide Size | 16:9 widescreen |

## Workflow

1. Read full style guidelines: `references/style-guidelines.md`
2. Follow the pptx skill for technical creation: `/mnt/skills/public/pptx/SKILL.md`
3. Apply McCombs brand standards throughout
4. Use the template in `assets/UT_MSB_Template.pptx` as reference for layouts
5. **Verify against the source before delivering.** Re-read the source table/figure and
   confirm every measured value plotted or quoted on a slide matches the source. List any
   value you could not verify, and flag illustrative charts explicitly. Do not deliver a
   chart presented as data unless its numbers trace back to the source.

## Brand Colors

### Primary
- **Burnt Orange**: `#C05900` — headlines, accents, title slide backgrounds
- **White**: `#FFFFFF` — backgrounds, text on dark
- **Steel Gray**: `#9CACB6` — secondary accent
- **Warm Gray**: `#D6D2C4` — neutral backgrounds

### Accent (for charts/emphasis)
- Bright Orange: `#F7961F`
- Yellow: `#FFD600`
- Green: `#579C41`
- Dark Blue: `#005E86`
- Teal: `#00A8B6`

## Typography Rules

| Element | Font | Size | Style |
|---------|------|------|-------|
| Headlines | Arial Black | 48pt | ALL CAPS |
| Subtitles | Arial | 24pt | Sentence case |
| Body | Arial | 18pt | Sentence case |
| Captions | Arial | 12-14pt | Sentence case |

## Slide Types

### Title Slide
- Burnt Orange background
- White text, Arial Black, ALL CAPS headline
- White dividing line above presenter info
- Presenter name bold, title regular

### Content Slide
- White background
- Title at top
- 1-3 key points maximum
- Logo placement: lower-left

### Section Divider
- Centered headline
- White or orange background
- Use for transitions between major sections

## Working from a Reference Image

When the user provides a reference image (a slide to match or a paper figure to recreate):

1. Reproduce the **layout** — relative position and grouping of title, columns, cards,
   chart, and captions — rather than inventing a new arrangement.
2. Re-skin it to McCombs brand (colors, Arial/Arial Black/Georgia, 14pt minimum) instead
   of copying the source's styling.
3. Keep all elements native and editable (see Charts and Data).
4. **Preserve the source's wording for findings and claims exactly** — do not paraphrase or
   "improve" a stated finding; if rephrasing is needed, ask first.
5. Save as a **new file**, never overwriting the user's existing slide.

## Content Guidelines

- Use active voice
- Front-load key information
- Keep slides focused and readable
- **Source footer:** every slide built from external material gets a small source line
  (Arial 10–12pt, Steel Gray, bottom-left or bottom-right). Use the cited source when
  known; use "Pre-publication research" when the source is unpublished/illustrative.
  Apply this for consistency across a deck even when a single reference image didn't show
  one — if unsure whether to include it, default to adding it and note it to the user.

## Charts and Data

Apply colors in order: Burnt Orange → Dark Blue → Steel Gray → Bright Orange → Green → Yellow

- Remove unnecessary gridlines
- Use direct data labels when possible
- Avoid 3D effects
- Title every chart clearly

### Rebuild figures as native, editable charts (default)

When recreating a figure from a paper, report, or reference image, build it as a
**native PowerPoint chart or native shapes** — never a pasted screenshot or flattened
image. Axes, gridlines, data series, baselines, and labels must all be individually
editable in PowerPoint. This is the default for every figure unless the user explicitly
asks for an image copy.

### Measured vs. illustrative data — always label it

For every chart, decide and state which it is:

- **Measured** — the plotted values come from the source's actual data/tables. Use these
  exact values; do not round or "clean" them without saying so.
- **Illustrative** — the shape conveys a pattern but the values are not measured. When a
  chart is illustrative, add a small caption such as "Illustrative — not to scale" so it
  is never mistaken for data.

Tell the user, in the delivery message, which charts are measured and which are illustrative.

## Things to Avoid

- Text smaller than 14pt
- Colors outside brand palette
- Clip art or low-quality images
- Busy backgrounds
- Heavy drop shadows or 3D effects
- Horizontal lines separating title from body (use whitespace instead)

## QA Checklist

Before finalizing:
- [ ] Arial/Georgia fonts only
- [ ] Colors match brand palette
- [ ] Text readable at 14pt minimum
- [ ] Consistent alignment throughout
- [ ] All recreated figures are native/editable (no pasted screenshots)
- [ ] Measured values verified against the source; illustrative charts labeled as such
- [ ] Source footer present (or "Pre-publication research"); saved as a new file
