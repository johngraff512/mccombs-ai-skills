---
name: case-generator
description: "Generate professional business cases for classroom teaching. Use this skill when a faculty member or instructor wants to create a business case about a company or topic, write a case study for class, build teaching materials around a strategic dilemma, or produce a case document with McCombs branding. Triggers on: business case, case study, case about [company], write a case, generate a case, teaching case, case for my class, strategic case, company case, topic case, case creation, new case. Also triggers when someone provides a company name and learning objectives and wants classroom-ready materials."
metadata:
  category: Case Writing
  version: "1.3.0"
---

# Case Generator Skill

> McCombs Case Toolkit version 1.3.0

Create professional, classroom-ready business cases as McCombs-branded Word documents. This skill works across all McCombs departments — Strategy, Marketing, Finance, Operations, MIS, and Accounting. See `references/discipline-guide.md` for department-specific guidance on framing, frameworks, and exhibits.

## What This Skill Produces

A polished .docx business case document containing:
- McCombs School of Business logo header
- Opening hook with protagonist and decision
- Company/industry background with historical context
- The core dilemma with tensions, trade-offs, and constraints
- Supporting evidence and exhibits
- Closing that restates the decision to be made
- Sources section with all references

## Workflow

### Phase 1: Gather Information from the Instructor

Before doing any research or writing, collect these inputs through conversation:

1. **Case type**: Company-specific or topic-specific?
2. **Company/topic**: Which company, or what topic/trend?
3. **Learning objectives**: 2-5 learning objectives for the class session. Each objective must start with a Bloom's taxonomy action verb (analyze, evaluate, assess, apply, create, etc.) and specify both the skill and the framework or context. If the instructor provides topics instead of properly formed objectives, reformulate them into Bloom's format and confirm. Examples by discipline:
   - Strategy: "Evaluate how [company] builds and sustains competitive advantage by applying Porter's Five Forces and resource-based view frameworks."
   - Finance: "Analyze the capital allocation decision using DCF and comparable company valuation frameworks."
   - Marketing: "Evaluate the company's market positioning by applying segmentation, targeting, and positioning (STP) analysis."
   - Operations: "Assess the supply chain trade-offs using process mapping and bottleneck analysis."
   - MIS: "Evaluate the build-vs-buy technology decision using IT portfolio management frameworks."
4. **Course level**: Undergraduate, MBA, or Executive MBA?
5. **Discipline**: Strategy, Marketing, Finance, Operations, Management, etc.
6. **Instructor-provided materials** (optional): Any URLs, PDFs, or articles the instructor has already found

If the instructor provides a company name and objectives upfront, confirm the details and proceed. Don't force them through unnecessary questions if they've been clear about what they want.

### Phase 2: Research

Use web search to find current, relevant content about the company or topic. Search for:

- Recent news articles (within the last 6-12 months)
- Strategic decisions, challenges, or dilemmas the company faces
- Executive quotes or perspectives
- Financial or operational data points
- Competitive landscape context
- Multiple stakeholder perspectives

For **topic-specific cases**, also search for:
- 2-3 companies illustrating different approaches to the topic
- Industry trends and evolution
- Conflicting viewpoints from experts

If the instructor provided URLs or uploaded documents, read those first and use them as primary sources. Supplement with web search to fill gaps.

**Research quality matters.** Aim for 5-10 substantive sources. Flag for the instructor if you can't find enough current coverage of their chosen company/topic.

### Phase 3: Outline and Confirm

Present a brief outline to the instructor before writing the full case:

- **Protagonist**: Who is the decision-maker?
- **Core dilemma**: What decision must they make? What are the 2+ viable options?
- **Key tensions**: What makes this decision hard?
- **Proposed sections**: Brief description of background, evidence, and exhibits you plan to include

Wait for the instructor's confirmation or adjustments before proceeding to writing.

### Phase 4: Write the Case

Read `references/case-structure.md` for the detailed case writing guidelines. The case narrative should follow this structure:

**For company-specific cases:**
1. Opening hook (the protagonist faces a decision)
2. Company background (history, industry context, competitive position)
3. The dilemma (what happened, stakeholder perspectives, constraints)
4. Supporting evidence (data, quotes, market information)
5. Exhibits (financial tables, competitive comparisons, timelines)
6. Closing (restate the decision; do NOT resolve it)

**For topic-specific cases:**
1. Opening (the topic/trend and why it matters now)
2. Concept overview (definitions, frameworks, key questions)
3. Company examples (2-3 companies showing different approaches)
4. Comparative analysis (outcomes, trade-offs, what worked and what didn't)
5. Closing dilemma (given these examples, what should a leader do?)

**Writing principles (these are essential):**
- Write in engaging, narrative prose — not like a textbook
- Maintain ambiguity: there must be 2+ defensible positions. Never signal a "right answer"
- Use real quotes, real data, real stakeholder names where possible
- Keep the case concise: target 3-5 pages of text plus 1-2 pages of exhibits
- Write at the appropriate level for the course (MBA cases assume more business sophistication than undergraduate)
- **Every specific data point must trace to a source.** The Sources section at the end is the primary citation record. Do not include any industry figure, financial statistic, market share estimate, or executive quote that doesn't have a corresponding numbered entry there. Attribute claims naturally in the prose (e.g., "per Nvidia's FY2025 annual report..." or "according to industry analysts...") rather than using footnote numbers for routine citations.
- **Use footnotes sparingly and only for clarification.** A footnote is appropriate when a specific claim is accurate but requires contextual nuance that would break the narrative if written inline — for example, when a term was used by a speaker in a broader context than how it reads in the case. Most cases need zero to two footnotes at most. See `references/case-structure.md` for the full guidance.

### Phase 5: Generate the Document

Use the bundled script `scripts/generate_case_docx.js` to produce the .docx file. This script handles all McCombs branding (logo, colors, fonts, margins, page numbers) automatically. You do not need to read the docx skill or write docx-js code from scratch.

**How to use the script:**

1. Write a JSON file containing the structured case content. The schema is documented at the top of the script, but here's the structure:

```json
{
  "title": "Case Title",
  "subtitle": "Optional tagline",
  "meta": "MBA Strategic Management  |  February 2026",
  "learningObjectives": ["Objective 1...", "Objective 2..."],
  "sections": [
    {
      "heading": "Section Title",
      "content": [
        { "type": "paragraph", "text": "Body text..." },
        { "type": "paragraph", "runs": [
            { "text": "Bold lead. ", "bold": true },
            { "text": "Regular text continues..." }
        ]},
        { "type": "subheading", "text": "Subsection Title" },
        { "type": "paragraph", "text": "More text..." }
      ]
    }
  ],
  "exhibits": [
    {
      "title": "Exhibit 1: Financial Summary",
      "headers": ["Metric", "FY2023", "FY2024"],
      "rows": [
        { "cells": ["Revenue", "$27B", "$61B"], "bold_first": true }
      ],
      "source": "Source: Company reports."
    }
  ],
  "footnotes": {
    "1": "Clarifying context for a nuanced claim — use sparingly."
  },
  "sources": ["Source 1...", "Source 2..."]
}
```

2. Run the script:
```bash
node <skill-path>/scripts/generate_case_docx.js case_data.json output.docx
```

The script produces a fully formatted McCombs-branded document with the logo header, Burnt Orange accent rule, learning objectives block, heading hierarchy, exhibit tables with branded styling, numbered sources, and page numbers in the footer.

**Content types supported in section `content` arrays:**
- `{ "type": "paragraph", "text": "..." }` — standard body paragraph
- `{ "type": "paragraph", "runs": [...] }` — paragraph with mixed formatting (bold, italic). Each run accepts: `text`, `bold`, `italics`, `color`
- `{ "type": "subheading", "text": "..." }` — H2 subsection heading (renders in ALL CAPS Burnt Orange)

### Phase 6: Review and Iterate

After generating the initial document, ask the instructor:
- Does the case capture the right dilemma?
- Is the difficulty level appropriate for their students?
- Would they like to adjust emphasis, add/remove sections, or change the narrative angle?
- Are there gaps in evidence or perspective they'd like filled?

Regenerate based on feedback. The instructor should be able to refine iteratively without starting over.

## Key Reminders

- The case must present a genuine dilemma with no obvious answer. If you find yourself writing toward a conclusion, stop and reframe.
- Cases should feel current and relevant. Prioritize recent events and data.
- Attribution matters. Include a Sources section at the end of the document listing all references.
- The output is always a .docx file saved to the user's working folder.
- When in doubt about tone, write like the best business journalism: clear, specific, and narrative-driven.
