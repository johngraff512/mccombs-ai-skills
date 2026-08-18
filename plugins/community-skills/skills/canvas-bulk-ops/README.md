# Canvas bulk operations

Make the same change across many Canvas items at once — with an audit before and a
verification pass after.

## Before you install

This skill requires the **Claude for Chrome** extension and a Chrome tab already signed
in to Canvas. It drives the Canvas REST API from inside your authenticated browser
session, which is why there's no API token to create or store — and also why it can't
run on a platform that has no browser to control. You also need teacher-level access to
the course.

## Problem

Canvas has no good way to do the same thing thirty times. Instructors end up clicking
Duplicate → Edit → retype → Save, over and over, and the errors that creep in are quiet
ones that surface weeks later in the gradebook.

Driving the API from a logged-in browser session turns an hour of clicking into a few
minutes — and, more importantly, makes it *verifiable*. You can check all thirty items
field by field, which no one does by hand.

That speed cuts both ways. A wrong assumption applied thirty times is thirty problems,
and some of them reach students. Which is why the skill is built around a protocol rather
than a script.

## Approach

Audit → plan → pilot → verify → scale → verify → record.

Every step earns its place. The audit reveals the course is not what anyone assumed. The
plan is where you catch the thing the AI couldn't know. The pilot means a wrong
assumption costs one item instead of thirty. The verification catches what the API
cheerfully accepted but did not do. The record is what makes the work checkable later.

Two safeguards are worth calling out:

**It makes you confirm the course.** Writing to the wrong course is the only genuinely
unrecoverable mistake here, and it's easy to make — institutions reuse course names
across sections, terms, and years, and most instructors have a dozen shells in their
account. The skill lists your teacher-role courses with ID, term, section, and SIS ID and
requires explicit confirmation before any write.

**It verifies by reading back.** The Canvas API will accept a write it did not actually
perform, particularly on quizzes with unpublished changes. Items are re-read and compared
field by field after the change.

## What it can do

`references/recipes.md` carries worked snippets for the jobs that come up most:

- Copy a classic quiz N times, renumbered and re-dated
- Bulk publish or unpublish a series
- Find duplicate or wrong answer keys across a set of quizzes
- Retire a superseded series without deleting grade history
- Shift a set of dates by a fixed offset
- Orient yourself in an unfamiliar course

`references/course-audit-checklist.md` covers what actually breaks, in ten categories:
shell and settings, dates, grading structure, quizzes, content integrity, external tools,
communication, accessibility, content-level checks, and ordering. It's useful on its own
as a start-of-term review, whether or not you change anything.

## How to use it

Don't invoke it by name — describe the chore. "Copy this participation assignment for all
28 class sessions," "unpublish all the quizzes from last semester," or "check whether my
course is set up right" all reach it.

For the specific case of re-dating a copied course shell onto a new term's calendar, use
`canvas-semester-rollforward` instead — it's the same discipline with a tighter protocol
for that job.

## What's included

| File | Purpose |
|---|---|
| `SKILL.md` | The protocol the AI follows |
| `references/recipes.md` | Worked snippets for six common bulk jobs |
| `references/course-audit-checklist.md` | Ten categories of what actually breaks in a course |
| `references/canvas-api-notes.md` | Authentication, quizzes vs. assignments, the unpublished-changes trap, dates/locks/DST, pagination, idempotency, endpoint reference |
| `scripts/build_schedule.py` | Term schedule and DST-correct UTC timestamp generator |
| `scripts/test_build_schedule.py` | 26 tests for the schedule logic |

The schedule builder resolves timezone offsets per date from the IANA database, so a term
that crosses a daylight-saving boundary doesn't end up with its last several weeks shifted
by an hour — the most common silent failure in bulk Canvas date edits.
