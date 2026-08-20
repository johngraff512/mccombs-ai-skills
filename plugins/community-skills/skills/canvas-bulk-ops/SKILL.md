---
name: canvas-bulk-ops
description: Make repetitive changes across many Canvas items at once — duplicating a quiz or assignment for every class session, bulk publishing or unpublishing, mass-editing due dates and availability windows, retiring an old series, or auditing a course for problems like duplicate answer keys and broken assignment group weights. Use this skill whenever someone wants to do the same edit to many Canvas items, describes a repetitive Canvas chore ("I have to copy this assignment for all 28 class sessions"), asks to clean up or audit a Canvas course, or wants to change something across a whole series of assignments or quizzes. Trigger even when they don't name Canvas explicitly — "copy this participation assignment for every class," "unpublish all the old quizzes," or "check whether my course is set up right" are the same job. For the specific case of re-dating a copied course shell onto a new term's calendar, prefer the canvas-semester-rollforward skill.
metadata:
  summary: "Make the same edit across dozens of Canvas assignments or quizzes at once, with an audit and verification pass around it."
  category: Course Administration
  version: "1.1.0"
  examples:
    - "Copy this participation assignment for all 28 class sessions."
    - "Unpublish all the quizzes from last semester."
    - "Check whether my Canvas course is set up right before the term starts."
---

# Canvas bulk operations

## Requirements

This skill needs the **Claude for Chrome** browser extension and a Chrome tab already
signed in to your institution's Canvas. It works by calling the Canvas REST API from
inside that authenticated session, so there is no API token to create or store — but it
cannot run anywhere without a live browser to drive.

You also need teacher-level access to the course being changed.


## What this is for

Canvas has no good way to do the same thing thirty times. Instructors end up clicking
through Duplicate → Edit → retype → Save, over and over, and the errors that creep in are
quiet ones that surface weeks later in the gradebook.

Driving the Canvas REST API from a browser session already logged into Canvas turns that
hour of clicking into a few minutes — and, more importantly, makes it *verifiable*. You can
check all thirty items field by field, which no one does by hand.

That speed cuts both ways. A wrong assumption applied thirty times is thirty problems, and
some of them reach students. The protocol below exists to make that unlikely, and it is
worth following even when the change looks trivial.

## Protocol

**Audit → plan → pilot → verify → scale → verify → record.**

Every step earns its place. The audit reveals the course is not what anyone assumed. The
plan is where the instructor catches the thing you couldn't know. The pilot means a wrong
assumption costs one item. The verification catches what the API cheerfully accepted but
did not do. The record is what makes the work checkable later.

---

## Step 1: Lock onto exactly one course

Writing to the wrong course is the only mistake here that is genuinely hard to undo, and
it is easy to make: institutions reuse course names across sections, terms, and years, and
instructors often have a dozen shells in their account.

```js
const courses = await J('/api/v1/courses?enrollment_type=teacher&per_page=100&include[]=term&include[]=sections');
```

Show the candidates with course ID, name, term, section, and SIS ID, and have the user
confirm which one. Match on section or unique number, not on the name. Then fix the course
ID in a constant and scope every subsequent call to it.

If the description matches more than one course, stop and ask rather than choosing.

Confirming *which* course is only half the job: also confirm it is **theirs to change**. See
"Whose course is this? Declare the write scope" immediately below — being enrolled as Teacher
is not evidence of ownership.

If the user has stated a constraint like "do not touch any other section," treat it as
standing: re-confirm the section on the course object before your first write, and say
which course you are in when you report.

## Whose course is this? Declare the write scope

Being enrolled as Teacher does **not** mean the course is yours to change. Faculty add each
other to courses routinely — so a colleague can look over a setup, or so you can import their
material into your own section. Canvas grants the same Teacher enrollment either way, and
**no field on the course object distinguishes "my section" from "a colleague's section I can
see."** Term, name, and course code will all match. Two sections of the same course in the
same term, one yours and one a colleague's, are nearly indistinguishable in the course list.

There is no way to work this out automatically. So ask, and write the answer down.

### The declaration

Once per session, before the first write, establish two lists explicitly with the instructor:

- **WRITE TARGET** — exactly **one** course. Show its course ID, name, term, section, and SIS
  ID, and have the instructor confirm that this is their own section and that changes should
  land in it. One target per session; there is no such thing as two.
- **READ-ONLY** — every other course the session will touch, named individually: colleagues'
  sections, prior terms, sandboxes, anything opened for comparison or as a copy source.

State both lists back before starting, and name the write target by ID and name in the final
report. If the instructor names a course you cannot map to a single ID, stop and ask rather
than choosing.

### The copy-from-a-colleague pattern

The common shape is: a colleague has a course set up the way you want, you have been added to
it, and you want its material in your section. Source is read-only, target is yours, and
**the direction never reverses.** Say the direction out loud before the first write — "reading
from <source>, writing to <target>" — because the failure mode here is not subtle: it is
editing a colleague's live course while their students are in it.

### Enforce it in code, not in memory

Pin the target in a constant and route every mutating call through a guard that fails closed.
This is what actually protects the other course — a guard that throws cannot be forgotten
thirty items into a loop.

```js
const WRITE_TARGET = 123456;                 // confirmed by the instructor as their own section
const READ_ONLY    = new Set([789012]);      // colleague's section — compare / copy source only

// Every POST / PUT / DELETE goes through this. Nothing else writes.
const W = (path, opts = {}) => {
  const method = (opts.method || 'GET').toUpperCase();
  if (method === 'GET') throw new Error('W() is for writes; use J() to read');
  const m = path.match(/\/courses\/(\d+)/);
  if (!m) throw new Error(`BLOCKED: no course ID in write path ${path}`);
  const cid = Number(m[1]);
  if (cid !== WRITE_TARGET) {
    throw new Error(`BLOCKED: ${method} targets course ${cid}; declared write target is ${WRITE_TARGET}`);
  }
  return J(path, opts);
};
```

Label read-only output too, so a comparison table never reads as though it described the
instructor's own course.

### Rules that follow

- **A course ID not on either list is undeclared.** Stop and declare it before any call that
  uses it — including reads.
- **Never infer ownership.** Not from the name, not from the term, not from recency, not from
  it being the only match, not from the instructor having mentioned it earlier.
- **Findings about a read-only course are findings, not work orders.** Report what you saw and
  let the instructor take it to their colleague. Fixing someone else's course, however obvious
  the fix, is not yours to do.

## Step 2: Audit before you touch anything

Read the whole picture first. Page properly — the API caps at 100 per page and truncates
silently (references/canvas-api-notes.md §5).

Read **items**, not people. The audit needs titles, dates, points, groups, and published
state; it does not need a roster or a gradebook. See "Student data: minimize, don't avoid"
below for how student-scoped work is handled.

`references/recipes.md` §6 has a course-orientation snippet. For a change scoped to one
series, look at:

- What is actually in the target group, and what else is in there that isn't part of the job
- Whether the items are assignments, **classic quizzes**, or **New Quizzes** — all three
  behave differently, and New Quizzes do not appear in the quizzes endpoint at all, so a
  course can look emptier than it is. Classify before planning: `references/new-quizzes.md`
  §1 has the detection test, §5 the capability table
- Numbering gaps, duplicates, and items dated outside the term
- Whether a **parallel series** already exists that the new work would collide with
- Whether assignment group weights sum to 100%

The last two are where the interesting problems live. A course shell that was imported
twice will have duplicated group names and weights summing to something absurd, and adding
items to it makes the gradebook worse.

When the request is a **whole-course review** rather than one series — "is this course set
up right," "I imported this from a colleague," "what should I check before students see
it" — work from `references/course-audit-checklist.md` instead. It catalogues how courses
actually break, ordered by how quietly the failure reaches students, and covers ground this
list does not: question banks that didn't import, links pointing back into the source
course, LTI tools needing re-pairing each term, accommodations that don't copy,
announcements that fire on publish, accessibility.

Report what you found before proposing changes. Frequently the audit changes the job.

### When the job needs a class calendar

Copying an item "for every class session" means you need the session dates. Build them with
the bundled script rather than computing them inline:

```bash
python scripts/build_schedule.py --start 2026-08-25 --end 2026-12-03 \
    --days TR --open 10:35 --close 10:55 --tz America/Chicago \
    --skip 2026-11-24,2026-11-26
```

It resolves each date's UTC offset separately, which is what stops a term that crosses a
daylight-saving boundary from having its last several weeks silently shifted by an hour.
`python scripts/test_build_schedule.py` runs 26 tests covering both DST directions,
cross-semester moves, holiday skips, and a regression case verified against live Canvas data.

The script has **no holiday calendar**. It skips only the dates you give it, so the schedule
is exactly as good as the no-class list you were handed. Ask for that list — breaks, campus
holidays, fieldwork days — and read it back before building. If the session count disagrees
with the number of items the instructor expects, that gap is a missing holiday until proven
otherwise.

## Step 3: Propose a concrete plan

Write out exactly what will change: every item, its current state, its intended state. A
table for a handful; a CSV for thirty.

Show it and wait. The instructor knows things you cannot read from the API — that session
12 is a fieldwork day, that the old series is deliberately kept for reference, that the
points discrepancy you spotted is intentional.

When you notice something that looks wrong but might be deliberate, ask rather than
correcting it. A quiz whose `points_possible` doesn't match the sum of its questions is
legal in Canvas and may be exactly what they want.

## Step 4: Pilot one item and stop

Make the change to a single item. Fetch it back and verify it. Confirm against the
**rendered page**, not only the API response — Canvas will accept a write and still not show
students what you expect (the unpublished-changes trap, API notes §3, is exactly this).

Check it **as text**: fetch the page and test for the banner string in the page, returning a
boolean. Do not screenshot to read text — that costs up to ~4,784 tokens and answers nothing
a string match can't (§8).

Report what you did and what you checked, and wait for approval before continuing. This is
the step that makes everything else safe, and it is the step there is always pressure to
skip.

## Step 5: Run the batch

Make the loop **idempotent**: check what already exists and skip it. This is not
defensive over-engineering — a long-running script keeps executing in the page even when
the calling tool call is interrupted, so a blind re-run creates duplicates (§6).

Work in chunks rather than one enormous call. Catch errors per item so one failure doesn't
abort the rest, and collect them for the summary. **Return a tally, not rows** — `{changed, skipped, failed}`, with failures in full. The per-item idempotency check stays;
the per-item output goes (§8).

## Step 6: Verify everything, independently

Check every item, not a sample. Compare each against the source or the plan on every field
you touched *and* the fields you didn't — points, group, published state, dates. Do the
comparison **in the page** and return the diff: `{checked, matched, mismatches: [...]}`. A
mechanical comparison proves more than dumped objects you scanned by eye, and costs a
fraction (§8).

Then verify a second way. Recompute the expected values from the original inputs in a
separate environment and diff against what Canvas now holds. Checking your work with the
code that did the work only proves it is self-consistent. Recomputing an item whose correct
value was already known — and matching it exactly — is real evidence.

For quizzes, always end by checking for the unpublished-changes banner across every item.

## Step 7: Record it

Produce a CSV: one row per item, with IDs, dates in both local and UTC, relevant settings,
and a direct URL. Save it where the instructor keeps working files.

Then say plainly what changed, what you verified and how, what you deliberately left alone,
and what still needs them.

---

## Student data: minimize, don't avoid

Most of this work never needs to know who the students are — dates, points, publish state and
question content are item-level facts. But some legitimate bulk jobs *are* student-scoped:
extra-time accommodations across a quiz series, availability overrides for a section, extension
records for a group. Those are exactly the repetitive chores Canvas handles badly, and they are
in scope. Doing them by hand across 28 quizzes is where accommodations get missed.

The rule is **minimize, not avoid**.

- **Work in Canvas user IDs, not names.** An accommodation job needs five integers and a number
  of minutes. It does not need to know whose they are or why they have one — and the instructor
  already holds that context. Ask for IDs; don't ask who they are.
- **Don't fetch what the task doesn't need.** No rosters, gradebooks, or submission lists pulled
  speculatively for context. When you need to know whether submissions exist, ask the item
  (`has_submitted_submissions`) or ask for a count.
- **Keep identities out of artifacts.** The CSV records item IDs, dates, settings and counts —
  "5 accommodations applied per quiz", not who received them. Names and email addresses do not
  belong in an exported record, and anything pasted into the conversation persists there.
- **Never record why.** Accommodation status is disability-related. The skill's job is to write
  `extra_time`; the reason stays between the student, the instructor, and the disability
  services office. Never write a reason into a title, description, comment, or log.
- **Report what you touched** — how many records, on which items — in the final summary.

Two things still warrant an explicit confirmation before running, because they change what a
student has already earned rather than how a course is configured: **bulk grade changes**, and
**anything that deletes or replaces existing accommodation or override records** (see the
override-replacement trap in `references/new-quizzes.md`). Confirm those; the rest is ordinary
bulk work.

## Two rules that protect students

**Unpublish, don't delete.** Unpublishing hides an item and removes it from grade
calculations, and reverses in one click. Deletion is a different kind of act — if the
instructor wants it, they can do it themselves.

**Never publish a placeholder.** When items need instructor-supplied content — an access
code, a per-class password, a prompt only they can write — create them unpublished with an
obvious `PLACEHOLDER` value and list exactly which ones need attention. A published
placeholder awards credit for the wrong answer.

## Audit the content, not just the settings

The most valuable findings come from reading what is *in* the items. Settings checks
confirm the structure; content checks find the bugs. Dumping every answer key in a series
and looking for duplicates costs one query and catches copy-paste errors that would
otherwise let every student pass with the wrong answer.

When you find one, verify against an authoritative source before proposing a fix, and let
the instructor decide.

## References

Read what the job needs, not all of it — each file is roughly 1,800–2,500 tokens.
`canvas-api-notes.md` before any write, always. `new-quizzes.md` whenever the course contains
a New Quiz, which the audit determines. `recipes.md` only for the pattern you are actually
running. `course-audit-checklist.md` only for a whole-course review or pre-launch check.

- `references/new-quizzes.md` — detection, what works in bulk on the ordinary API, async
  duplication, the override-replacement trap, the separate-service probe, accommodations.
- `references/canvas-api-notes.md` — authentication and CSRF, quizzes vs assignments, the
  unpublished-changes trap and how to clear it, date/lock semantics and DST, pagination,
  idempotency, endpoint table. **Read before your first write.**
- `references/recipes.md` — worked patterns: copying a classic quiz N times, bulk
  publish/unpublish, duplicate answer-key audits, retiring a superseded series, shifting
  dates by an offset, orienting in an unfamiliar course, and bulk accommodations (§7).
- `references/course-audit-checklist.md` — how courses actually break, by failure mode:
  shell and term settings, dates, grading structure, quizzes and question banks, links and
  media, external tools, communication, accessibility, and content-level checks. Read this
  for whole-course reviews and pre-launch checks, especially on an imported shell.

- `scripts/build_schedule.py` — builds a term's session list with DST-correct UTC
  timestamps. `scripts/test_build_schedule.py` is its 26-test suite; run it if you change
  the script or want to confirm the environment behaves.

The companion `canvas-semester-rollforward` skill covers the specific case of re-dating an
already-imported shell onto a new term. It ships the same schedule script, so either skill
works on its own — you do not need both installed.
