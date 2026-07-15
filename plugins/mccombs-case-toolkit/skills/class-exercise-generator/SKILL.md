---
name: class-exercise-generator
description: "Generate a menu of interactive class exercises for a case discussion or lecture session. Use this skill when a faculty member or instructor wants activities for a class — poll questions, think-pair-share, small group breakouts, debates, framework applications, or any structured classroom exercises. Triggers on: class exercises, in-class activities, exercises for this case, engagement activities, interactive exercises, what activities should I use, breakout exercises, discussion exercises. Also triggers when an instructor has a case and wants to build engaging activities around it."
---

# Class Exercise Generator Skill

Generate a curated menu of 5-8 interactive exercises for a single class session, delivered as a McCombs-branded instructor guide. This skill works across all McCombs departments — Strategy, Marketing, Finance, Operations, MIS, and Accounting. See `../shared/discipline-guide.md` for department-specific guidance on exercise framing.

## What This Skill Produces

A single **Instructor Exercise Guide** (.docx) containing a mix of exercises an instructor can choose from when facilitating a case discussion or lecture. The guide includes everything the instructor needs — the exercise descriptions, timing, facilitation instructions, student-facing content to display or distribute, and answer guidance — all in one document.

A typical guide for a 75-minute case discussion might include:

- 1-2 **Quick-fire exercises** (polls, short-answer prompts) — 2-5 min each
- 1-2 **Think-Pair-Share** exercises — 5-8 min each
- 1-2 **Small group breakouts** — 10-15 min each
- 1 **Flagship exercise** (structured debate, role play, framework deep-dive) — 15-30 min
- The instructor picks what fits their flow; they don't use all of them

## Exercise Types

Read `references/exercise-types.md` for detailed design guidance on each type.

| Type | Format | Typical Duration | Student Materials? |
|------|--------|------------------|--------------------|
| **Poll / Vote** | Show of hands, clicker, or anonymous poll | 2-3 min | Question on slide/screen |
| **Short Answer** | Cold-call or voluntary response to a focused question | 3-5 min | Question on slide/screen |
| **Think-Pair-Share** | Individual reflection → partner discussion → share with class | 5-8 min | Prompt on slide/screen |
| **Small Group Breakout** | Teams of 3-5 analyze a question, then report out | 10-20 min | Optional discussion guide |
| **Framework Application** | Groups apply a framework (Five Forces, VRIO, etc.) to the case | 12-20 min | Worksheet template |
| **Structured Debate** | Teams argue assigned positions; class votes | 20-35 min | Position assignments + analysis guide |
| **Role Play** | Students adopt stakeholder roles and negotiate/present | 20-35 min | Role cards |
| **Decision Memo** | Write a 1-page recommendation memo | 12-20 min | Memo template |
| **Gallery Walk** | Teams create visuals, then rotate and annotate | 25-40 min | Poster prompts + annotation guide |

## Workflow

### Phase 1: Gather Inputs

Get these from the instructor:

**Required:**
- **The case or topic** — case JSON, uploaded document, or description
- **Session length** — how many total minutes for the class?
- **Class size** — approximate number of students (this affects report-out time, group sizes, and exercise feasibility)

**Helpful:**
- **Learning objectives** — what should students take away?
- **Class format** — is this entirely case discussion, or part lecture / part discussion?
- **Instructor style** — do they prefer high-energy activities, or more reflective ones?
- **Physical constraints** — room layout, breakout spaces, available tech (polling tools, whiteboards)
- **Exercises to avoid** — anything they've already used recently or don't like

### Phase 2: Design the Exercise Menu

**Key principle:** The menu should be **flexible, not prescriptive.** The instructor won't use every exercise. The guide gives them options that they can mix and match based on how the class discussion unfolds.

**Design the mix based on these factors:**

1. **Case content** — What dilemmas, data, and frameworks does the case naturally lend itself to? A case with strong competing positions favors debate; a data-heavy case favors framework application.

2. **Session length** — Longer sessions can accommodate more and longer exercises.
   - 50-minute session: 4-5 exercises (mostly quick-fire + 1 breakout or flagship)
   - 75-minute session: 5-7 exercises (mix of quick-fire, TPS, breakout, 1 flagship)
   - 90-minute session: 6-8 exercises (full mix with potentially 2 flagship options)

3. **Class size** — This critically affects timing, especially for report-outs.
   - **Report-out scaling:** If 10 groups each get 2 min to report, that's 20 minutes. If 3 groups each get 3 min, that's 9 minutes. The guide must account for this.
   - **Group formation time:** Larger classes take longer to form groups. Budget 2-3 min for classes >60.
   - **Poll/vote feasibility:** Show-of-hands works for <60; larger classes need digital polling.
   - For exercises with report-outs, always note: "Select 3-4 groups to present (not all groups need to report out)."

4. **Discussion arc** — Exercises should follow the natural arc of a case discussion:
   - **Opening** — warm-up exercises that activate prior knowledge (polls, short-answer)
   - **Analysis** — exercises that deepen understanding (TPS, framework application, breakouts)
   - **Synthesis** — exercises that force a decision or position (debate, decision memo, vote)
   - **Close** — reflection exercises (takeaway TPS, exit poll)

5. **Energy management** — Alternate between individual/pair work and group work. Don't stack three small-group exercises back-to-back.

### Phase 3: Write the Content

Create a JSON object following the schema documented at the top of the generation script (`scripts/generate_exercise_docx.js`).

For each exercise, include:
- **What it is** and how it works
- **When to use it** in the class flow (Opening, Analysis, Synthesis, Close)
- **Exact timing** broken down by phase, with explicit notes on how class size affects timing
- **The prompt/question** — exactly what the instructor says or displays
- **Facilitation notes** — what to watch for, how to manage
- **Student-facing content** (if any) — what to project, distribute, or display
- **Debrief transition** — how to connect the exercise back to the discussion
- **Answer guidance** — expected student responses and what to probe

### Phase 4: Generate the Document

```bash
node <skill-path>/scripts/generate_exercise_docx.js <input.json> <output.docx>
```

The script produces a single instructor guide with:
- Title page with session overview and learning objectives
- Exercise menu summary (which exercises, when to use them, which are essential vs. optional)
- Each exercise as a self-contained card with all facilitation details
- Student-facing content embedded inline (marked clearly for display/distribution)
- Answer guidance for exercises that need it
- Suggested session flow at the end

### Phase 5: Review and Iterate

The instructor may want to:
- Swap one exercise type for another
- Adjust timing for their class size
- Add or remove exercises
- Modify prompts or questions
- Adjust the suggested flow

## Key Design Principles

1. **The menu is flexible** — not every exercise gets used. Mark which are essential and which are optional.
2. **Report-out time scales with class size** — always calculate and note this explicitly.
3. **Exercises build on each other** — later exercises should reference insights from earlier ones.
4. **Student-facing content is embedded** — the instructor doesn't need a separate document. They display the prompt on screen or read it aloud.
5. **Energy management matters** — alternate active/reflective, individual/group, short/long.
6. **The debrief is where learning happens** — every exercise needs a clear bridge back to the case discussion.

## References

- `references/exercise-types.md` — detailed design patterns for each exercise type
- `assets/mccombs_logo.png` — McCombs logo for document header
