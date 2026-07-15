---
name: teaching-note-generator
description: "Generate comprehensive instructor teaching notes for business cases. Use this skill when a faculty member or instructor wants a teaching note, instructor guide, teaching plan, discussion guide, or class facilitation guide for a business case. Triggers on: teaching note, instructor note, discussion plan, teaching guide, how to teach this case, class plan, board plan, discussion questions, teaching plan, case facilitation, instructor copy. Also triggers immediately after the Case Generator produces a case when the instructor asks for accompanying teaching materials."
metadata:
  category: Class Preparation
  version: "1.0"
---

# Teaching Note Generator Skill

Create professional, classroom-ready instructor teaching notes as McCombs-branded Word documents. This skill works across all McCombs departments — Strategy, Marketing, Finance, Operations, MIS, and Accounting. See `../shared/discipline-guide.md` for department-specific guidance on discussion questions, board plans, and teaching points.

## What This Skill Produces

A polished INSTRUCTOR COPY .docx teaching note containing:
- Synopsis of the case
- Learning objectives with pedagogical context
- Suggested course positioning and prerequisite topics
- Pre-class assignment questions (given to students before class)
- Teaching plan with session timing
- Discussion questions with analysis, teaching points, and board capture notes
- Board plan (suggested visual layout for capturing discussion)
- Optional epilogue (what actually happened after the case)

## Workflow

### Phase 1: Gather Inputs

Collect these before generating:

1. **The case**: Either —
   - The JSON file from the Case Generator (preferred — gives full structured access to all case content), or
   - An uploaded case document (Word .docx or PDF — Claude will read and extract the content)

2. **Session length**: How long is the class session? (e.g., 75 minutes, 90 minutes)

3. **Key emphasis**: Are there specific frameworks, concepts, or discussion angles the instructor wants to prioritize? Or any sections they want to omit?

4. **Epilogue**: Does the instructor want to include an epilogue? If so, do they know what actually happened (or should Claude research it)?

If the case was just generated in the same session, most of this is already known — confirm session length and proceed.

### Phase 2: Analyze the Case

Before writing, think through the case as an experienced case method instructor would:

- What is the core disciplinary tension? What makes this a genuinely hard decision? (For strategy: competitive positioning. For finance: capital allocation or valuation. For marketing: customer or brand choices. For operations: efficiency vs. quality trade-offs.)
- What frameworks apply? Use the discipline's frameworks — strategy (Five Forces, RBV, BCG), finance (DCF, WACC, capital structure), marketing (STP, CLV, pricing models), operations (process mapping, bottleneck analysis), MIS (system architecture, build-vs-buy), accounting (audit risk model, materiality). See `../shared/discipline-guide.md` for comprehensive lists.
- What will students likely argue? What are the 2-3 most defensible positions?
- What are the common mistakes or misreadings students make with this type of case?
- What order should the discussion unfold to build insight progressively?
- What should be on the board at the end of class?

This analysis is the foundation for high-quality discussion questions and teaching points.

### Phase 3: Generate the Teaching Note

Read `references/teaching-note-structure.md` for the full structural guidelines. Generate all sections:

1. **Synopsis** — 2-3 paragraph neutral summary of the case. Does not reveal a "right answer."
2. **Learning Objectives** — Restate from the case; add brief pedagogical context for each (what student behavior demonstrates this objective)
3. **Suggested Positioning** — Where in a course curriculum this case fits best; prerequisite topics; paired readings if relevant
4. **Pre-Class Assignment Questions** — 2-4 questions given to students before class to ensure preparation; these are not identical to in-class discussion questions
5. **Teaching Plan** — Session timeline as a table: Time | Phase | Activity | Instructor Goal
6. **Discussion Questions + Analysis** — 4-8 questions in suggested discussion order, each with: purpose, key teaching points, anticipated student responses, and board capture note
7. **Board Plan** — Visual layout of what to capture on the board/slides during discussion
8. **Epilogue** (if requested) — What actually happened; keep it brief and place at the very end so instructors can choose when to reveal it

### Phase 4: Generate the Document

Use `scripts/generate_teaching_note_docx.js` to produce the .docx. The schema is documented at the top of the script. Here's the structure:

```json
{
  "title": "Teaching Note: Case Title",
  "meta": "MBA Strategic Management  |  February 2026  |  INSTRUCTOR COPY — NOT FOR DISTRIBUTION",
  "synopsis": "Paragraph 1...\n\nParagraph 2...",
  "learningObjectives": [
    { "objective": "Evaluate how Nvidia builds competitive advantage...", "context": "Students demonstrate this by applying Five Forces..." }
  ],
  "positioning": {
    "suggestedCourses": ["MBA Strategic Management", "Competitive Strategy"],
    "whereinCurriculum": "Best placed in weeks 3-5 when covering competitive advantage and platform strategy...",
    "prerequisiteTopics": ["Porter's Five Forces", "Resource-Based View", "Platform/ecosystem strategy"],
    "pairedReadings": ["Porter, 'What is Strategy?' HBR 1996", "Barney, 'Firm Resources and Sustained Competitive Advantage' 1991"]
  },
  "preClassQuestions": [
    "What is Nvidia's primary source of competitive advantage, and how durable is it?",
    "Which of the three strategic paths would you recommend to Jensen Huang, and why?"
  ],
  "teachingPlan": [
    { "minutes": "0–10", "phase": "Opening", "activity": "Cold call 2 students on pre-class Q1. Map initial responses on board.", "goal": "Establish baseline understanding; surface divergent views early." },
    { "minutes": "10–30", "phase": "Competitive Analysis", "activity": "Small group discussion: apply Five Forces to Nvidia's position.", "goal": "Reveal the structural sources of advantage — and fragility." }
  ],
  "discussionQuestions": [
    {
      "question": "What is Nvidia's competitive advantage, and which parts of it are most durable?",
      "timing": "Minutes 0–20",
      "purpose": "Opens the competitive analysis; surfaces whether students see hardware vs. software as the real moat.",
      "teachingPoints": [
        "CUDA is the moat, not the GPU — the hardware is increasingly replicable",
        "Switching costs are embedded in developer workflows, not just code",
        "Four million CUDA developers represent a self-reinforcing ecosystem"
      ],
      "anticipatedResponses": "Most students will cite GPU performance first. Push them: if AMD matches GPU specs, why doesn't Nvidia lose share? This surfaces the software ecosystem argument.",
      "boardCapture": "Column 1: Sources of Advantage → list hardware vs. software items separately"
    }
  ],
  "boardPlan": {
    "description": "Three-column layout. Build left-to-right as discussion progresses.",
    "columns": [
      { "header": "Sources of Advantage", "points": ["CUDA ecosystem (4M devs)", "One-year product cadence", "Full-stack integration", "Supply chain relationships"] },
      { "header": "Competitive Threats", "points": ["Hyperscaler custom silicon (44.6% ASIC growth)", "AMD + OpenAI (ROCm open-source)", "China export ban ($50B gap)", "Customer → competitor dynamic"] },
      { "header": "Strategic Options", "points": ["Fortify the moat (R&D acceleration)", "Open the platform (CUDA portability)", "Evolve beyond chips (AI factory)"] }
    ]
  },
  "epilogue": "Optional text describing what actually happened..."
}
```

Run the script:
```bash
node <skill-path>/scripts/generate_teaching_note_docx.js teaching_note_data.json output.docx
```

### Phase 5: Review and Iterate

After generating, ask the instructor:
- Does the discussion sequence feel right for their teaching style?
- Are the timing estimates realistic for their class format?
- Do they want to add or remove any sections?

## Key Reminders

- Teaching notes are INSTRUCTOR ONLY — always include the "NOT FOR DISTRIBUTION" header
- Discussion questions should build progressively: open → analyze → evaluate → synthesize
- Teaching points are what the instructor should draw out; anticipated responses are what students will actually say (often different)
- The board plan should tell the visual story of the class — what a student photographs at the end of class should capture the key insights
- For McCombs branding specs, see `../case-generator/references/docx-branding.md`
