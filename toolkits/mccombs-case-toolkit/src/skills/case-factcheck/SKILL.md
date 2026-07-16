---
name: case-factcheck
description: "Systematically verify all factual claims in a business case before downstream materials are built. Use this skill when an instructor wants to fact-check a case, verify case data, or check case accuracy before generating teaching notes, exercises, or slides. Triggers on: fact-check this case, verify the case, check the facts, case fact-check, verify case data, fact check, factcheck, check case accuracy, verify case claims, are the facts right."
metadata:
  summary: "Verify every factual claim in a case before you build teaching materials on top of it."
  category: Case Writing
  version: "1.3.1"
---

# Case Fact-Checker

> McCombs Case Toolkit version 1.3.1

Systematically verify every factual claim in a business case. Designed to run after the Case Generator and before the Teaching Note Generator, Class Exercise Generator, or Slide Generator, so corrections are made once in the source and never cascade across multiple files. See `references/factcheck-guidelines.md` for the claim taxonomy and verification standards.

## What This Skill Produces

1. A structured **fact-check report** (`factcheck_report.md`) documenting every verified claim, its status, the primary source used, and any corrections
2. A **corrected case markdown** (`case.md`) with all approved fixes applied
3. A **regenerated .docx** with corrections and McCombs branding

## Position in the Case Toolkit Pipeline

```
Case Idea Generator → Case Generator → Case Fact-Check → Teaching Note Generator
                                                                    ↓
                                                          Class Exercise Generator
                                                                    ↓
                                                            Slide Generator
```

Run this skill immediately after the Case Generator completes. All downstream materials (teaching notes, exercises, slides) will then build on verified content.

## File Organization

All intermediate files go in the existing `<foldername>_build/` subdirectory. Final deliverables stay in the working directory.

```
<working-directory>/
├── [Company or Topic] Case.docx            ← regenerated with corrections
└── <foldername>_build/
    ├── case.md                              ← corrected (original backed up as case_pre-factcheck.md)
    ├── case_pre-factcheck.md                ← backup of original case before corrections
    ├── outline.md                           ← unchanged from Case Generator
    └── factcheck_report.md                  ← structured verification report
```

Reuse the existing `<foldername>_build/` directory. Do not create a new one.

## Workflow

### Phase 1: Locate the Case

Find the case content to verify:

1. **Preferred path:** Look for `<foldername>_build/case.md` in the working directory. If it exists, use it (this is the output of the Case Generator).
2. **Alternative:** If a path to a .docx or PDF is provided, read it directly.
3. **Fallback:** If no case content is found, ask the instructor which file to verify.

Read `references/factcheck-guidelines.md` for the claim taxonomy and verification standards.

### Phase 2: Extract Claims

Parse the case content and extract every verifiable factual claim into a structured list. Organize claims into these categories:

| Category | Examples |
|----------|----------|
| **Financial data** | Revenue, profit, margins, stock prices, market cap, headcount, growth rates |
| **Dates and timelines** | When events occurred, chronological sequence, duration of periods |
| **Names and titles** | People's names and spellings, job titles, company names, product names |
| **Quotes and attributions** | Direct quotes, who said what, where it was published |
| **Events and actions** | What was announced, what happened, corporate actions taken |
| **Market and industry data** | Market share, rankings, industry statistics, competitor data |

For each claim, record:
- The claim as stated in the case
- The category
- The source cited in the case (if any)
- Where it appears (section and approximate location)

**Present the extracted claim list to the instructor** with a count by category (e.g., "I found 34 verifiable claims: 12 financial, 6 dates, 4 names, 3 quotes, 5 events, 4 market data"). Ask: "Proceed with verification, or adjust the scope?"

This is a decision point. Wait for confirmation before proceeding.

### Phase 3: Verify Claims

For each claim, search for verification using primary sources. Prioritize sources in this order:

1. **SEC filings** (10-K, 10-Q, 8-K, proxy statements) for financial data
2. **Earnings releases and investor presentations** for quarterly/annual figures
3. **Official press releases** for corporate announcements
4. **Court filings and regulatory documents** for legal matters
5. **Major financial data providers** (company IR pages, stock exchanges) for market data
6. **Reputable journalism** (WSJ, NYT, Bloomberg, Reuters, FT) for events and quotes

Assign each claim a verification status:

| Status | Meaning | Action |
|--------|---------|--------|
| **Confirmed** | Verified against a primary source | No change needed |
| **Corrected** | Primary source contradicts the claim | Correction provided with source |
| **Adjusted** | Claim approximately right but imprecise | More accurate figure or phrasing provided |
| **Unverifiable** | No primary source found to confirm or deny | Flagged for instructor decision |
| **Disputed** | Multiple credible sources give conflicting data | Options presented with sources |

**Verification discipline:**
- Do not assume a claim is correct because it appears in the case. Verify independently.
- When financial figures differ between sources, prefer the company's own filings (10-K, earnings release) over journalist reports.
- For quotes, verify the exact wording and the original publication. Flag paraphrases presented as direct quotes.
- For headcount and employee data, note whether the figure is end-of-period, average, or full-time-equivalent, as these often differ.
- For stock prices, note whether the figure is closing price, intraday, or adjusted for splits.
- When a claim attributes a statement to a person (e.g., "the CEO said"), verify both the quote and the attribution.

### Phase 4: Present Report

Generate `<foldername>_build/factcheck_report.md` with this structure:

```markdown
# Fact-Check Report: [Case Title]

**Date:** [YYYY-MM-DD]
**Case file:** case.md
**Claims verified:** [N]
**Result summary:** [N] confirmed, [N] corrected, [N] adjusted, [N] unverifiable, [N] disputed

## Summary of Changes

[1-2 paragraph overview of what was found. Lead with the most significant corrections.]

## Corrections Required

[List each Corrected or Adjusted claim with the current text, the corrected text, and the source.]

### [Claim number]. [Brief description]
- **Category:** [financial / date / name / quote / event / market]
- **Current text:** "[exact text from case]"
- **Corrected text:** "[corrected version]"
- **Source:** [Chicago Author-Date citation]
- **Impact:** [How this affects the case narrative, if at all]

## Unverifiable Claims

[List each claim that could not be verified, with a note on what was searched and why it could not be confirmed.]

## Disputed Claims

[List each claim where sources conflict, with the options and sources for each.]

## Confirmed Claims

[Brief summary table of confirmed claims, grouped by category.]

| # | Claim | Category | Source |
|---|-------|----------|--------|
| 1 | [claim summary] | Financial | [source] |
| ... | ... | ... | ... |
```

**Present the report to the instructor.** Walk through each correction and flag, and ask: "Approve these corrections? Any claims you want handled differently?"

This is a decision point. Wait for approval before applying corrections.

### Phase 5: Apply Corrections

After instructor approval:

1. **Back up the original:** Copy `case.md` to `case_pre-factcheck.md` in the build directory
2. **Apply corrections** to `case.md` by editing the file. Apply only the corrections the instructor approved.
3. **Regenerate the .docx** using the Case Generator's bundled docx script (see `scripts/generate_case_docx.js`). Build a JSON payload from the corrected case.md following the same format the Case Generator uses, then run the script to produce the branded .docx.
4. **Confirm completion** to the instructor with a summary: how many corrections applied, which claims remain unverifiable or disputed.

**Handoff prompts:**
> "Generate a teaching note for this case?"
> "Create exercises for this case discussion?"
> "Build slides for the case session?"

## Key Reminders

- This skill verifies facts, not pedagogy. Do not second-guess analytical framing, learning objectives, or narrative choices.
- Back up the original case.md before applying any changes.
- Financial figures from SEC filings override journalist reports. Company filings are the primary source of truth for company data.
- Present the full report before changing anything. The instructor decides which corrections to apply.
- Claims attributed as someone's statement (e.g., "Dorsey claimed $500K per employee") are verified for attribution accuracy, not for whether the underlying claim is true. The case may deliberately present disputed claims as part of the dilemma.

## References

- `references/factcheck-guidelines.md`: claim taxonomy and verification standards
- `references/case-structure.md`: case writing guidelines for understanding the source document
- `references/discipline-guide.md`: department-specific guidance
- `scripts/generate_case_docx.js`: vendored case document generator used to regenerate an approved corrected case
- `assets/mccombs_logo.png`: McCombs logo used by the document generator
