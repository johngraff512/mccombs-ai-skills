# Canvas semester roll-forward

Re-date an imported Canvas course onto a new term's real meeting pattern — due dates,
availability windows, and session numbering across a whole series at once.

## Before you install

This skill requires the **Claude for Chrome** extension and a Chrome tab already signed
in to Canvas. It drives the Canvas REST API from inside your authenticated browser
session, which is why there's no API token to create or store — and also why it can't
run on a platform that has no browser to control. You also need teacher-level access to
the course.

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
| `references/canvas-api-notes.md` | Authentication, quizzes vs. assignments, the unpublished-changes trap, dates/locks/DST, pagination, idempotency, endpoint reference |
| `scripts/build_schedule.py` | Term schedule and DST-correct UTC timestamp generator |
| `scripts/test_build_schedule.py` | 26 tests for the schedule logic |
