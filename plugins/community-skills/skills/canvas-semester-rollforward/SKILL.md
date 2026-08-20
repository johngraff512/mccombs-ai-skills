---
name: canvas-semester-rollforward
description: Re-date an imported Canvas course shell onto a new term's real meeting pattern — fixing due dates, availability windows, and session numbering across a whole series of assignments or quizzes at once. Use this skill whenever someone mentions rolling a Canvas course forward to a new semester, copying or importing a course shell, fixing dates after a course copy, a course whose assignment dates are on the wrong days of the week, shifting due dates for a new term, or updating a recurring series (attendance, participation, weekly quizzes, reading responses) to new class dates. Trigger even if they don't say "Canvas" or "roll forward" — phrases like "the dates are all wrong after I copied last semester's course," "my Monday/Wednesday assignments need to be Tuesday/Thursday," or "update all the due dates for spring" are the same job. Also use when planning such a change, not just executing it.
metadata:
  summary: "Re-date a copied Canvas course onto a new term's meeting pattern, fixing due dates, availability windows, and session numbers."
  category: Course Administration
  version: "1.1.0"
  examples:
    - "The dates are all wrong after I copied last semester's course."
    - "My Monday/Wednesday assignments need to be Tuesday/Thursday."
    - "Roll my fall course forward to the spring calendar."
---

# Canvas semester roll-forward

## Requirements

This skill needs the **Claude for Chrome** browser extension and a Chrome tab already
signed in to your institution's Canvas. It works by calling the Canvas REST API from
inside that authenticated session, so there is no API token to create or store — but it
cannot run anywhere without a live browser to drive.

You also need teacher-level access to the course being changed.


## The problem this solves

Instructors build a course once and copy it forward. Canvas copies the content but the
dates come along from the old term — often the old *meeting pattern* too. A Monday/Wednesday
course copied into a Tuesday/Thursday section arrives with every assignment due on days
the class does not meet. Twenty-eight items, each needing a new date, an availability
window, and a session number that lines up with the syllabus.

Done by hand this is an hour of clicking and a near-certainty of at least one error.
The errors are quiet ones: an assignment due during a holiday, a quiz that opens an hour
late for the last month of the term because daylight saving ended, a session number that
drifted after a break week.

## The approach, in one line

Audit what exists → build the correct schedule → propose a mapping and get it approved →
change one item and stop → verify → do the rest → verify again → leave a record.

The stop after one item is the part people want to skip. Don't. A wrong assumption caught
on item 1 costs one fix; caught on item 28 it costs 28, plus whatever students already saw.

---

## Step 1: Lock onto exactly one course

Getting this wrong is the only truly unrecoverable mistake here — edits land in someone
else's course, or last year's section, and nobody notices for weeks.

List the instructor's courses and confirm the target explicitly:

```js
const courses = await J('/api/v1/courses?enrollment_type=teacher&per_page=100&include[]=term&include[]=sections');
```

Show name, course ID, term, section, and SIS ID, and have the user confirm before any
write. Institutions reuse course names across sections and years, so match on the section
or unique number rather than the name. Once confirmed, put the course ID in a constant and
scope every call to it.

If more than one course matches what the user described, stop and ask. Never pick the
most recent one and proceed.

Confirming *which* course is only half the job: also confirm it is **theirs to change**. See
"Whose course is this? Declare the write scope" immediately below — being enrolled as Teacher
is not evidence of ownership.

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

## Step 2: Establish the real schedule

You need four facts: meeting days, term start and end, the local time window, and the
no-class dates.

Confirm rather than infer. The course's `syllabus_body` usually states the meeting pattern
and room, and `time_zone` gives the timezone:

```js
const c = await J(`/api/v1/courses/${CID}?include[]=syllabus_body&include[]=sections`);
```

**Holidays are not an edge case.** Nearly every term has a break, and forgetting it shifts
every session number after it. Ask directly which dates have no class — Thanksgiving,
spring break, a campus holiday, a fieldwork day the instructor already knows about.
If the instructor has a session plan or syllabus schedule, read it: it is the authoritative
list of sessions and usually reveals the breaks implicitly through gaps.

Then build the schedule with the bundled script rather than computing dates inline:

```bash
python scripts/build_schedule.py --start 2026-08-25 --end 2026-12-03 \
    --days TR --open 10:35 --close 10:55 --tz America/Chicago \
    --skip 2026-11-24,2026-11-26
```

It resolves each date's UTC offset independently, which is what keeps a fall term from
silently shifting by an hour after daylight saving ends. Run
`python scripts/test_build_schedule.py` if you have changed the script or want to confirm
the environment behaves — 26 tests cover both DST directions, holiday skips, and a
regression case verified against live Canvas data.

Cross-check the session count against the instructor's own plan. If the script says 30 and
their syllabus says 28, you have found a missing holiday — resolve it before continuing,
because that discrepancy will otherwise become an off-by-two error across half the term.

### Moving between fall and spring

Carrying a series from a fall shell into a spring section (or the reverse) is the most
error-prone version of this job, because three things change at once and none of them are
visible in the copied course:

- **The holidays are entirely different.** Fall has Thanksgiving; spring has a full break
  week plus assorted campus holidays. Neither calendar transfers, and nothing in Canvas
  will tell you the old ones no longer apply.
- **Daylight saving moves the opposite direction**, and in spring the transition often falls
  *inside* the break week — so the UTC offset changes across a gap where no class meets.
  Handled automatically, but it means eyeballing "the offsets all match" is not a check.
- **The session count will differ.** A fall series almost never has exactly the right number
  of items for a spring term. Expect a mismatch and reconcile it explicitly rather than
  assuming a 1:1 mapping.

The script has **no holiday calendar and does not try to guess one** — it only skips dates
you pass to `--skip`. So the schedule is exactly as good as the no-class list you were
given. Get that list from the instructor or their academic calendar and read it back to
them before building anything. When the item count and session count disagree, present the
options (leave the tail uncovered, start later, create the extras unpublished with
placeholders) rather than picking one.

## Step 3: Map existing items to sessions

Pull every item in the affected group, paging properly (see references/canvas-api-notes.md
§5 — a 100-item page cap silently truncates).

Classify each item first — assignment, Classic Quiz, or New Quiz. New Quizzes are invisible to
the quizzes endpoint and surface only as assignments (`references/new-quizzes.md` §1), so a
series counted from the wrong endpoint will be short.

Pull **items**, not people. Re-dating a series needs dates, titles, points, and published
state; it does not need a roster or any student's submissions. See "Student data: minimize, don't
avoid" below for how student-scoped work is handled.

Most series are numbered in their titles (`3 - Participation`, `Quiz 7`,
`Reading Response 12`). Parse the number and map item N to session N. Then look hard at
what doesn't fit:

- **Gaps in numbering.** If items exist for 1–9, 11–12, 14–24, 26–28, then 10, 13, and 25
  are missing. Ask whether to fill them or preserve the gaps — both are legitimate, and
  the instructor knows which.
- **More items than sessions,** or fewer. Never silently truncate; report the mismatch.
- **Items that aren't part of the series** sitting in the same group (an optional
  check-in, a final reflection). Leave them alone and say that you did.
- **A competing parallel series.** If the group already holds two overlapping sets — the
  old imported one and a new one the instructor started building — flag it. Creating more
  items alongside a series that should be retired makes the gradebook wrong in a way that
  is tedious to unwind later.

Present the mapping as a table before writing anything: session number, current date,
proposed date, weekday, and the new window. This is the moment the instructor catches
"session 12 is our fieldwork day, there's no class."

## Step 4: Pilot one item, then stop

Change a single item. Then check it — fetch it back, and confirm against the rendered page,
not just the API response: the date, window, weekday, points, published state, and that
nothing else moved.

Check the page **as text**: fetch it and test for the banner string in the page, returning a
boolean. Do not screenshot to read text — that costs up to ~4,784 tokens and answers nothing
a string match can't (§8).

Report what you changed and what you verified, and wait for approval. Resist the urge to
continue because it "obviously worked."

## Step 5: Run the rest, then verify everything

Loop over the remaining items. Make the loop idempotent — check for existing items and skip
them — because an interrupted run keeps executing server-side and re-running it blind
creates duplicates (references/canvas-api-notes.md §6).

Return a tally from the loop, not the changed objects (§8). Then verify all of them, not a
sample — comparing **in the page** and returning `{checked, matched, mismatches: [...]}`:

- Every item's `unlock_at`, `due_at`, and `lock_at` match the computed schedule exactly
- Every date falls on a real meeting day
- No duplicates, no items left on old dates
- Points, group, and published state unchanged from before
- For quizzes: no unpublished-changes banner (§3)

**Recompute independently.** Rebuild the expected timestamps from the source schedule in a
separate step — a different script, a different environment — and diff against what Canvas
now holds. Verifying with the same code that wrote the data only proves the code is
self-consistent.

## Step 6: Leave a record

Write a CSV with one row per item: session number, item ID, weekday, local date, local
open and close times, UTC timestamps, points, published state, and a direct URL. Save it
somewhere the instructor keeps working files.

This is not bookkeeping for its own sake. It is what lets them check your work at a glance,
what they will diff against next semester, and what makes a mistake findable later.

---

## Things worth surfacing even though nobody asked

While auditing you will see problems adjacent to the task. Mention them; don't fix them
without asking.

- **Assignment group weights that don't sum to 100%**, especially with duplicated group
  names — the signature of a double import. This distorts grades.
- **Duplicate answer keys** across a series where each item should be unique. Dumping all
  the answers and checking for repeats takes one query and catches real bugs.
- **Items dated outside the term.**
- **A parallel series** that should probably be retired.

Auditing *content*, not just settings, is what catches the errors that would otherwise
reach students.

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

**Never delete.** Unpublish instead. Unpublishing hides an item from students and removes
it from grade calculations, and is one click to reverse. If the instructor truly wants
deletion, let them do it themselves.

**Never publish something with placeholder content.** If you create items that need
instructor input — an access code, a per-class password, a prompt only they can write —
create them unpublished, use an obvious `PLACEHOLDER` value, and tell them exactly which
items need attention before publishing. A published placeholder awards credit for the
wrong answer.

## Reference

`references/canvas-api-notes.md` — authentication and CSRF, why classic quizzes cannot be
duplicated, the unpublished-changes trap and how to clear it, date/lock semantics,
pagination, idempotency, and an endpoint table. Read it before your first write.

`references/new-quizzes.md` — read it whenever the course contains a New Quiz. They do not
appear in the quizzes endpoint, so a series can be larger than it looks; re-dating them works
normally through the Assignments API, but the override-replacement trap in §2 will silently
delete student accommodations if you send a partial override list.
