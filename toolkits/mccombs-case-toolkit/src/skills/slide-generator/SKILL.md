---
name: slide-generator
description: "Generate McCombs-branded PowerPoint slide decks for case discussions and lectures. Use this skill when an instructor needs a slide deck for facilitating a case discussion or delivering a lecture. Triggers on: create slides, make a slide deck, case discussion slides, lecture slides, presentation for class, slide generator, slides for this case, case slides."
metadata:
  category: Slides & Presentations
  version: "1.3.0"
---

# Slide Generator

> McCombs Case Toolkit version 1.3.0

Generate McCombs-branded PowerPoint slide decks for case discussions and lectures.

## Description

Use this skill when an instructor needs a slide deck — either for facilitating a case discussion in class or for a general lecture. This skill works across all McCombs departments — Strategy, Marketing, Finance, Operations, MIS, and Accounting. See `references/discipline-guide.md` for department-specific guidance on frameworks and discussion questions. The skill produces a polished .pptx file with McCombs branding (Burnt Orange, Arial/Arial Black, widescreen 16:9 format, logo placement).

**Trigger phrases:** "create slides," "make a slide deck," "case discussion slides," "lecture slides," "presentation for class," "slide generator"

## Two Modes

### Mode A: Case Discussion Slides

Takes a case (case JSON, teaching note JSON, or uploaded case document) and generates a slide deck designed to facilitate a case discussion in class. Typical structure:

1. **Title slide** — case name, course, date
2. **Case setup** (1-2 slides) — protagonist, situation, key context
3. **Discussion question slides** — one per major discussion question, with the question prominently displayed
4. **Framework analysis slides** — pre-built framework templates (Five Forces, VRIO, etc.) for the class to fill in together
5. **Key data/exhibit slides** — important financials, market data, or quotes from the case
6. **Strategic options slide** — the 2-3 paths the protagonist could take
7. **Debate/vote slide** — for structured debate or class vote
8. **Wrap-up slide** — key takeaways and connections to theory
9. **Next class slide** — what to prepare for next time (optional)

### Mode B: General Lecture Slides

Takes a topic, outline, or content and generates a branded lecture deck. The instructor provides the content direction; the skill handles structure and formatting.

## Workflow

### Phase 1: Gather Inputs

Determine which mode is needed and collect:

**For Case Discussion (Mode A):**
- The case — either a case generator JSON file, a teaching note JSON, or an uploaded case document
- Session length (to calibrate number of slides)
- Any specific discussion questions or frameworks to include
- Whether the instructor wants data/exhibit slides

**For General Lecture (Mode B):**
- Topic and key points to cover
- Session length
- Any specific frameworks, examples, or structures they want
- Level of detail (high-level overview vs. detailed lecture)

### Phase 2: Design the Deck Structure

Plan the slide sequence. A well-designed discussion deck typically has 12-20 slides for a 75-minute session:

- **Title slide**: 1
- **Case setup**: 1-2 slides
- **Discussion blocks**: 2-3 slides per major question (question slide + supporting data/framework)
- **Options/synthesis**: 2-3 slides
- **Wrap-up**: 1-2 slides

For lectures, plan 1 slide per 3-5 minutes of content, favoring fewer, cleaner slides.

### Phase 3: Write the Content

Create a JSON object following the schema below. Each slide has a type that determines its layout.

```json
{
  "title": "Deck title",
  "subtitle": "Course name | Date",
  "presenter": "Instructor name",
  "presenterTitle": "Title, Department",
  "slides": [
    {
      "type": "title",
      "headline": "NVIDIA'S AI FORTRESS",
      "subtitle": "Strategic Management Case Discussion",
      "presenter": "Prof. John Graff",
      "presenterTitle": "McCombs School of Business",
      "date": "February 2026"
    },
    {
      "type": "section",
      "headline": "COMPETITIVE ANALYSIS",
      "subtitle": "Understanding Nvidia's moat"
    },
    {
      "type": "content",
      "title": "The AI Chip Landscape",
      "bullets": [
        "Nvidia controls ~80% of AI training chip market",
        "CUDA ecosystem: 4M+ developers, 15+ years of lock-in",
        "$130.5B revenue in FY2025 — up 114% YoY"
      ],
      "footnote": "Source: Nvidia FY2025 Annual Report"
    },
    {
      "type": "question",
      "question": "What is Nvidia's primary source of competitive advantage, and how durable is it?",
      "subtext": "Consider both the hardware and software dimensions"
    },
    {
      "type": "framework",
      "title": "Porter's Five Forces — AI Chips",
      "framework": "five_forces",
      "items": {
        "rivalry": "High — AMD, Intel, hyperscaler custom silicon",
        "newEntrants": "Moderate — huge capital requirements but well-funded entrants",
        "substitutes": "Growing — custom ASICs (Google TPU, Amazon Trainium)",
        "buyerPower": "Increasing — hyperscalers are 40%+ of revenue",
        "supplierPower": "High — TSMC near-monopoly on advanced nodes"
      }
    },
    {
      "type": "two_column",
      "title": "Build vs. Buy: The Hyperscaler Dilemma",
      "leftHeading": "Stay with Nvidia",
      "leftBullets": ["Best-in-class performance", "CUDA ecosystem", "Full-stack integration"],
      "rightHeading": "Build Custom Silicon",
      "rightBullets": ["Lower per-unit cost at scale", "Reduce dependency", "Customize for workloads"]
    },
    {
      "type": "options",
      "title": "Three Strategic Paths",
      "options": [
        { "name": "Fortify the Moat", "description": "Accelerate R&D cadence, deepen CUDA lock-in" },
        { "name": "Open the Platform", "description": "Make CUDA portable, monetize software separately" },
        { "name": "Evolve Beyond Chips", "description": "Become an AI infrastructure company" }
      ]
    },
    {
      "type": "quote",
      "quote": "The more we accelerate, the more you save.",
      "attribution": "Jensen Huang, CES 2025"
    },
    {
      "type": "data",
      "title": "Nvidia Revenue Growth",
      "dataPoints": [
        { "label": "FY2023", "value": "$27.0B" },
        { "label": "FY2024", "value": "$61.0B" },
        { "label": "FY2025", "value": "$130.5B" }
      ],
      "footnote": "Source: Nvidia Annual Reports"
    },
    {
      "type": "takeaway",
      "title": "Key Takeaways",
      "bullets": [
        "Competitive advantage has multiple layers — hardware, software, ecosystem",
        "The moat/motivation paradox: strength invites circumvention",
        "No dominant strategy — each path solves one problem and creates another"
      ]
    },
    {
      "type": "next",
      "title": "Next Class",
      "content": "Read: Apple's Services Strategy case\nPrepare: Pre-class questions 1-3"
    }
  ]
}
```

### Supported Slide Types

| Type | Layout | Use For |
|------|--------|---------|
| `title` | Burnt Orange background, large white headline | Opening slide |
| `section` | Burnt Orange or white, centered headline | Transitions between sections |
| `content` | White background, title + bullets | Standard content |
| `question` | Large centered question text | Discussion prompts |
| `framework` | Structured layout for the named framework | Five Forces, VRIO, etc. |
| `two_column` | Side-by-side comparison | Pros/cons, compare options |
| `options` | Numbered strategic options with descriptions | Decision options |
| `quote` | Large centered quote with attribution | Key quotes from case |
| `data` | Key metrics displayed prominently | Financial data, KPIs |
| `takeaway` | Title + summary bullets | Wrap-up / synthesis |
| `next` | Next class info | Closing slide |
| `blank` | Blank branded slide | Flexible use |

### Phase 4: Generate the Deck

```bash
node <skill-path>/scripts/generate_slides.js <input.json> <output.pptx>
```

### Phase 5: Review and Iterate

Show the instructor a preview. Common adjustments:
- Add or remove slides
- Adjust discussion questions
- Change the framework on a framework slide
- Add data exhibits
- Reorder the flow

## Brand Standards (Built Into Script)

- **Primary color**: Burnt Orange `#BF5700` (note: docx skills use this; the pptx template uses `#C05900` — the script uses `#BF5700` for consistency with the rest of the toolkit)
- **Fonts**: Arial Black for headlines (ALL CAPS), Arial for body text
- **Layout**: 16:9 widescreen
- **Logo**: McCombs logo in lower-left (color version on white, white version on orange backgrounds)
- **Text sizes**: Title 36-44pt, Body 20-24pt, Footnotes 10-12pt

## References

- `references/slide-design.md` — slide design principles and best practices
- `assets/mccombs_logo_color.png` — full-color logo (for white backgrounds)
- `assets/mccombs_logo_white.png` — white logo (for orange backgrounds)
