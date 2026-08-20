# Canvas semester roll-forward

Re-date an imported Canvas course onto a new term's real meeting pattern — due dates,
availability windows, and session numbering across a whole series at once.

## Before you install

This skill requires the **Claude for Chrome** extension and a Chrome tab already signed
in to Canvas. It drives the Canvas REST API from inside your authenticated browser
session, which is why there's no API token to create or store — and also why it can't
run on a platform that has no browser to control. You also need teacher-level access to
the course.

The trade-off for having no token is that the skill inherits exactly your Canvas
permissions and every action is logged as you — which is why the first thing it does is
make you name the one course it is allowed to change.

## Problem

Instructors build a course once and copy it forward. Canvas copies the content but the
dates come along from the old term — often the old *meeting pattern* too. A
Monday/Wednesday course copied into a Tuesday/Thursday section arrives with every
assignment due on days the class does not meet. Twenty-eight items, each needing a new
date, an availability window, and a session number that lines up with the syllabus.

Done by hand it's an hour of clicking and a near-certainty of at least one error. The
errors are quiet ones: an assignment due during a holiday, a quiz that opens an hour late
for the last month of term because daylight saving ended, a session number that drifted
after a break week. They surface later, in the gradebook, when a student complains.

## Approach

Audit what exists → build the correct schedule → propose a mapping and get it approved →
change one item and stop → verify → do the rest → verify again → leave a record.

The stop after one item is the part people want to skip. A wrong assumption caught on
item 1 costs one fix; caught on item 28 it costs 28, plus whatever students already saw.

Two other safeguards matter as much:

**It makes you confirm the course.** Writing to the wrong course is the only genuinely
unrecoverable mistake here, and it's easy to make — institutions reuse course names
across sections, terms, and years. The skill lists your teacher-role courses with ID,
term, section, and SIS ID and requires an explicit confirmation before any write. If more
than one course matches what you described, it stops and asks rather than guessing.

**It can only change one course.** Being enrolled as Teacher doesn't mean a course is
yours — faculty add each other to sections to review a setup or share material, and
nothing in Canvas distinguishes your section from a colleague's. You name one course as
the write target at the start; everything else is read-only, and every write is routed
through a guard that refuses a mismatched course ID.

**It leaves student accommodations alone.** Re-dating a series needs dates, titles, points
and published state, not a roster, and none is fetched. Where a job genuinely is
student-scoped it works in Canvas user IDs rather than names and keeps identities out of
exported records. Sending a partial override list to Canvas silently deletes the overrides
you left out — including an accommodation someone set last week — so the skill edits
overrides surgically rather than wholesale.

**It verifies by reading back.** The Canvas API will accept a write it did not actually
perform, particularly on quizzes with unpublished changes. Every item is re-read and
compared field by field, which nobody does by hand.

## The daylight-saving trap

The most common silent failure in bulk Canvas date work. A fall term starting in CDT and
ending in CST will have its final weeks shifted by an hour if you compute one UTC offset
and reuse it — a quiz that opens at the wrong time for the last month of the term.

`scripts/build_schedule.py` resolves the offset per date from the IANA timezone database,
so each session gets the offset actually in effect that day. It also handles skip dates
for holidays and break weeks, and emits either a readable table or JSON.

```bash
python3 build_schedule.py --start 2026-08-25 --end 2026-12-03 \
    --days Tue,Thu --open 10:35 --close 10:55 --tz America/Chicago \
    --skip 2026-11-26,2026-11-27
```

The script ships with 26 tests (`scripts/test_build_schedule.py`). Run
`python3 -m pytest test_build_schedule.py` if you modify it.

## New Quizzes

Canvas's newer quiz engine behaves differently in one way that matters here: **New Quizzes
never appear in the quizzes API at all.** A series counted from that endpoint will be short,
and a course full of them can look empty. The skill classifies every item first — assignment,
Classic Quiz, or New Quiz — before counting anything.

Re-dating New Quizzes themselves works normally: they are addressed as assignments, so due
dates, availability windows, publish state and groups all behave as they do everywhere else.
`references/new-quizzes.md` has the details, including the override trap above.

## How to use it

Don't invoke it by name — describe the job. "The dates are all wrong after I copied last
semester's course," "my Monday/Wednesday assignments need to be Tuesday/Thursday," or
"roll my fall course forward to the spring calendar" all reach it.

For repetitive Canvas edits that aren't a term roll-forward — duplicating an assignment
for every session, bulk publishing, auditing a course — use `canvas-bulk-ops` instead.

## What's included

| File | Purpose |
|---|---|
| `SKILL.md` | The step-by-step protocol the AI follows |
| `references/new-quizzes.md` | Canvas's newer quiz engine: how to spot one, what re-dates normally, the override-replacement trap |
| `references/canvas-api-notes.md` | Authentication, quizzes vs. assignments, the unpublished-changes trap, dates/locks/DST, pagination, idempotency, endpoint reference |
| `scripts/build_schedule.py` | Term schedule and DST-correct UTC timestamp generator |
| `scripts/test_build_schedule.py` | 26 tests for the schedule logic |
