# Canvas bulk operations

Make the same change across many Canvas items at once — with an audit before and a
verification pass after.

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

Four safeguards are worth calling out:

**It makes you confirm the course.** Writing to the wrong course is the only genuinely
unrecoverable mistake here, and it's easy to make — institutions reuse course names
across sections, terms, and years, and most instructors have a dozen shells in their
account. The skill lists your teacher-role courses with ID, term, section, and SIS ID and
requires explicit confirmation before any write.

**It verifies by reading back.** The Canvas API will accept a write it did not actually
perform, particularly on quizzes with unpublished changes. Items are re-read and compared
field by field after the change.

**It can only change one course.** Being enrolled as Teacher doesn't mean a course is
yours — faculty add each other to sections to review a setup or share material, and
nothing in Canvas distinguishes your section from a colleague's. At the start of a session
you name one course as the write target; everything else is read-only, and every write is
routed through a guard that refuses a mismatched course ID. Copying a colleague's material
into your section works; editing their course does not.

**It minimizes student data rather than avoiding it.** Most of the work is item-level and
never touches students. Where a job genuinely is student-scoped — extra-time
accommodations across a quiz series, availability overrides for a group — it works in
Canvas user IDs rather than names, keeps identities out of exported records, and never
writes down *why* anyone has an accommodation. Rosters, gradebooks and submissions are
never pulled speculatively. Bulk grade changes, and anything that would replace existing
accommodation or override records, still stop and ask first.

## What it can do

`references/recipes.md` carries worked snippets for the jobs that come up most:

- Copy a classic quiz N times, renumbered and re-dated
- Bulk publish or unpublish a series
- Find duplicate or wrong answer keys across a set of quizzes
- Retire a superseded series without deleting grade history
- Shift a set of dates by a fixed offset
- Orient yourself in an unfamiliar course
- Apply extra-time accommodations for a group of students across a whole quiz series

`references/new-quizzes.md` covers Canvas's newer quiz engine, which behaves differently
enough to matter. New Quizzes never appear in the quizzes API at all — a course full of
them can look empty — so the skill identifies them first. Bulk dates, publish state, groups
and overrides work normally; duplication works too (Classic quizzes are the ones that
can't be duplicated). Their question content and accommodations live on a separate
Instructure service whose reachability from a browser login isn't documented, so the skill
tests for it and tells you plainly if that half isn't available rather than guessing.

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
| `references/recipes.md` | Worked snippets for seven common bulk jobs |
| `references/course-audit-checklist.md` | Ten categories of what actually breaks in a course |
| `references/new-quizzes.md` | Canvas's newer quiz engine: how to spot one, what works in bulk, async duplication, the override-replacement trap, accommodations |
| `references/canvas-api-notes.md` | Authentication, quizzes vs. assignments, the unpublished-changes trap, dates/locks/DST, pagination, idempotency, endpoint reference, keeping responses small |
| `scripts/build_schedule.py` | Term schedule and DST-correct UTC timestamp generator |
| `scripts/test_build_schedule.py` | 26 tests for the schedule logic |

The schedule builder resolves timezone offsets per date from the IANA database, so a term
that crosses a daylight-saving boundary doesn't end up with its last several weeks shifted
by an hour — the most common silent failure in bulk Canvas date edits.

A note on cost: bulk work gets expensive if it pulls whole Canvas objects and screenshots
into the conversation, and both add up faster than they look. The skill fetches full
records into the browser but hands back only the fields a job needs, audits by reporting
what deviates rather than dumping every item, and reads pages as text instead of taking
screenshots unless the question is genuinely visual.
