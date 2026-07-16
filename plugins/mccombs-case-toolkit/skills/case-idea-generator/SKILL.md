---
name: case-idea-generator
description: "Generate curated business case ideas for MBA/EMBA instruction. Use this skill when a faculty member wants to brainstorm case ideas for a course, module, or framework. Triggers on: case ideas, brainstorm cases, what companies could I write a case about, find me a good case topic, case idea generator, suggest cases for my course, case topic ideas."
metadata:
  summary: "Brainstorm curated business-case ideas matched to your course, module, or framework."
  category: Case Writing
  version: "1.3.1"
---

# Case Idea Generator

> McCombs Case Toolkit version 1.3.1

Generate a curated set of 3–5 business case ideas for MBA/EMBA instruction, delivered as a McCombs-branded Word document. This skill works across all McCombs departments — Strategy, Marketing, Finance, Operations, MIS, and Accounting. See `references/discipline-guide.md` for department-specific frameworks and dilemma types.

## Description

Use this skill when a faculty member wants to brainstorm case ideas for a course, module, or framework. The skill takes a topic, strategic framework, industry, or course context and produces a short list of high-potential case ideas — each with enough detail to evaluate whether it's worth developing into a full teaching case.

**Trigger phrases:** "case ideas," "brainstorm cases," "what companies could I write a case about," "find me a good case topic," "case idea generator," "suggest cases for my course"

## Workflow

### Phase 1: Gather Inputs

Ask the instructor for context. At minimum, get ONE of the following:

- **Topic or framework** (e.g., Strategy: "competitive advantage," "platform strategy," "Five Forces"; Finance: "capital structure," "valuation," "M&A"; Marketing: "customer segmentation," "brand repositioning," "pricing strategy"; Operations: "supply chain risk," "quality management"; MIS: "digital transformation," "data governance")
- **Industry or sector** (e.g., "healthcare AI," "electric vehicles," "fintech")
- **Course context** (e.g., "second week of MBA Strategic Management — we cover industry analysis," or "module 3 of Financial Analysis — we cover capital allocation")
- **A specific company or situation** they've been thinking about

Also ask (if not provided):

- **Target audience**: MBA, EMBA, undergraduate, or executive education
- **Recency preference**: Should ideas be current (last 1-2 years) or is historical ok?
- **Any companies or industries to avoid?** (e.g., cases they already use)

### Phase 2: Research and Identify Ideas

Use **web search** to find 3–5 companies/situations that meet these criteria:

1. **Genuine dilemma** — not just an interesting company, but a specific decision point where reasonable people could disagree (this may be a strategic, financial, marketing, operational, or technology dilemma depending on the discipline)
2. **Identifiable protagonist** — a named decision-maker (CEO, founder, division head, CFO, CMO, CTO, CIO) facing the dilemma
3. **Teachable frameworks** — the situation naturally lends itself to at least 2 frameworks in the discipline (see `references/discipline-guide.md` for framework lists by department)
4. **Data availability** — sufficient public information exists (financials, press coverage, analyst reports) to write a full case
5. **Student engagement** — the company or industry is relevant and interesting to the target audience

For each idea, gather enough detail to write a compelling summary. Prioritize specificity over breadth — a concrete dilemma beats a vague "this company is interesting."

### Phase 3: Structure the Ideas

For each case idea, prepare the following elements:

| Element | Description |
|---------|-------------|
| **Company** | Name and brief identifier (e.g., "Stripe — fintech payments infrastructure") |
| **Protagonist** | Named decision-maker and their role |
| **The Dilemma** | 2-3 sentence description of the specific strategic decision. Must be a genuine fork in the road with at least 2 defensible paths |
| **Why It's Teachable** | What makes this case pedagogically valuable — what will students learn? |
| **Key Frameworks** | 2-3 strategic frameworks that apply (e.g., Five Forces, VRIO, platform economics, network effects) |
| **Strategic Options** | 2-3 distinct paths the protagonist could take |
| **Data Availability** | Assessment of whether enough public data exists to write a full case (financial data, press coverage, industry reports). Flag any gaps |
| **Timeliness** | Is this situation current, recent, or historical? Any risk of the situation resolving before the case is written? |
| **Source leads** | 3-5 specific sources to start from (articles, reports, filings) |

### Phase 4: Generate the Document

Write the content as a JSON object following the schema below, then generate the .docx:

```json
{
  "title": "Case Ideas: [Topic/Framework]",
  "meta": "McCombs School of Business  |  [Date]",
  "context": {
    "requestedBy": "Faculty name (if known)",
    "topic": "The topic, framework, or course context provided",
    "audience": "MBA / EMBA / Undergraduate / Executive Education",
    "generatedDate": "Month Year"
  },
  "ideas": [
    {
      "company": "Company Name — brief identifier",
      "protagonist": "Name, Title",
      "dilemma": "2-3 sentence description of the specific strategic decision...",
      "whyTeachable": "What makes this pedagogically valuable...",
      "frameworks": ["Framework 1", "Framework 2", "Framework 3"],
      "strategicOptions": [
        "Option 1: brief description",
        "Option 2: brief description",
        "Option 3: brief description (if applicable)"
      ],
      "dataAvailability": "Assessment of public data availability...",
      "timeliness": "Current / Recent / Historical — with context",
      "sourceleads": [
        "Source 1: description",
        "Source 2: description",
        "Source 3: description"
      ]
    }
  ],
  "selectionNotes": "Brief note on how these ideas were selected and any patterns across them"
}
```

Then run the docx generation script:

```bash
node <skill-path>/scripts/generate_ideas_docx.js <input.json> <output.docx>
```

### Phase 5: Review and Iterate

Present the document to the instructor. They may want to:
- Drop ideas that don't fit
- Ask for deeper research on a promising idea
- Request additional ideas in a different direction
- Take a strong idea directly into the Case Generator skill

When an instructor wants to develop an idea into a full case, hand off to the **Case Generator** skill with the idea's details as the starting brief.

## Quality Standards

Each case idea must pass these checks:

- [ ] The dilemma is specific — not "Company X faces challenges" but "CEO Y must decide between A and B by Q3 2026"
- [ ] At least 2 strategic options are genuinely defensible
- [ ] The situation maps to identifiable frameworks
- [ ] Sufficient public data exists to write a full case
- [ ] The protagonist is a real, named person
- [ ] Source leads are specific (not just "Google it")

## References

- `references/idea-quality.md` — criteria for evaluating case idea quality
- `assets/mccombs_logo.png` — McCombs logo for document header
