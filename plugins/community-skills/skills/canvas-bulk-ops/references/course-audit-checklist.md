# Course audit: what actually breaks

A catalogue of how Canvas courses are wrong, ordered by how quietly the failure reaches
students. Use it as a menu, not a script — pick what fits the course in front of you.

The organizing insight: a copied course breaks in two independent ways. **Time drift** —
every date belongs to a term that has ended. **Ownership drift** — the content still points
at another person's files, banks, tools, and policies. A course copied from a colleague's
prior-year section has both, stacked.

Almost none of it looks wrong from the teacher view. It looks wrong from the student view,
in week three, in the gradebook.

## Contents

1. Shell and settings
2. Dates
3. Grading structure
4. Quizzes
5. Content integrity
6. External tools
7. Communication
8. Accessibility
9. Content-level checks (the ones settings audits miss)
10. Ordering

---

## 1. Shell and settings

- **Term** is the upcoming one, not inherited from the source.
- **Participation dates** deliberately set. An end date in the past makes the course
  read-only; "restrict students from viewing after end date" makes it vanish entirely.
- **Course time zone** correct — and the instructor's *personal* profile timezone too.
  A mismatch means every date displays shifted, and they will "fix" correct dates into
  incorrect ones.
- **Blueprint status.** A child course may refuse edits; a parent will push everything to
  associated courses on next sync.
- **Enrollments.** The colleague may still be enrolled as teacher, with access to the new
  students' grades. Worth raising directly.
- **Leftover sections** from the source, which break section-specific due dates.

## 2. Dates

Check the *distribution*, not item by item. If the section meets Tue/Thu and the due-date
weekday histogram is full of Mon/Wed, the whole calendar came from a different meeting
pattern and needs rebuilding rather than nudging — that is the roll-forward job, not an
audit fix.

- **All three date fields**, not just due: `unlock_at`, `due_at`, `lock_at`. The "until"
  date is what silently locks students out.
- **Inverted windows** — available-from after due, available-until before due. Both are
  legal in Canvas and both are impossible to submit.
- **Assignment overrides** ("Assign to" rows for individual students or sections). These
  survive imports, still reference the source's sections, and quietly beat the visible date.
- **Module lock-until dates**, separate from item dates.
- **Items dated outside the term** in either direction.
- **New-term holidays** don't collide with deadlines.
- **Calendar events and announcements** carrying last year's dates.

## 3. Grading structure

- **Group weights sum to 100%.** With weighted grading on, a total of 97 or 140 means every
  student's grade is computed on the wrong denominator, all semester, with nothing in the
  interface complaining. This is the highest-value single check in this document.
- **Duplicated group names** are the fingerprint of a shell imported twice. Where there are
  duplicate groups there are usually duplicate assignments, both counting.
- **Everything in the right group** — copies sometimes dump content into "Imported Assignments."
- **Grade posting policy** (automatic vs manual), course-level and per-assignment. A
  colleague's manual-posting habit will surprise you.
- **Late and missing submission policies** — auto-deduct and auto-zero carry over and start
  firing on each due date.
- **Grading scheme** matches the syllabus cutoffs.
- **Rubrics** attached, points reconciling with the assignment.
- **Gradebook empty** of real student data; Test Student submissions cleared.

## 4. Quizzes

Quizzes fail loudly, on quiz day, in front of everyone.

- **Question count is nonzero.** Banks don't always import; a published quiz can have zero
  questions, and the index page won't show it.
- **Question banks** exist in *this* course rather than linking to the colleague's. A
  question group pulling "5 from Bank X" fails silently if the bank didn't come along.
- **Inherited access codes and IP filters** from a proctored session lock everyone out.
- **The unpublished-changes state** shows students the previous version — for an imported
  quiz, often no questions at all. Not reliably exposed in the quiz JSON; read the rendered
  page. See canvas-api-notes.md §3.
- **Results visibility and correct-answer release** — last year's windows are both a leak
  risk and a lockout risk.
- **Classic vs New Quizzes.** Cross-course copying of New Quizzes is notoriously lossy, and
  it is a different API. Identify which engine before planning anything.
- **Accommodations do not copy.** Extended time is a per-quiz Moderate setting. It is an
  accessibility obligation and very easy to forget on quiz 14.

## 5. Content integrity

- **Links containing the source course ID.** Assignment descriptions, pages, and the
  syllabus routinely carry `/courses/<their-id>/...` links. These resolve fine for an
  instructor with access to both courses and 404 for every student. Scan descriptions, page
  bodies, and the syllabus for course IDs that aren't this one.
- **Canvas's own Course Link Validator** (Settings → Validate Links in Content) catches the
  file and media links an HTML scan can't resolve. Run it after edits, not before.
- **Files published**, not restricted or hidden unintentionally.
- **Embedded media** — cross-account video rarely copies with permissions intact. Confirm
  playback as a student, and confirm captions came too.
- **Cloud-drive embeds** belong to the colleague's account and need re-sharing.
- **Redistribution rights** for scanned chapters, licensed datasets, purchased cases. A real
  institutional risk on an inherited course, and worth asking the colleague about directly.

## 6. External tools

Almost all LTI integrations are paired to the originating course and instructor account, and
need re-establishing every term regardless of what the copy suggests:

- Plagiarism tools (Turnitin and similar), enabled per-assignment
- Publisher integrations, which require a fresh course pairing each term
- Conferencing links pointing at the colleague's recurring meeting
- Engagement tools re-provisioned for this course
- LTI placements in course navigation that show a config error to students

## 7. Communication

- **Announcements fire on publish.** Copied announcements with a past delayed-post date, or
  none at all, email every student the moment the course goes live.
- **Syllabus** carries the colleague's name, office hours, room, and meeting times.
- **Institutional boilerplate** changes annually: integrity, accommodations, Title IX, mental
  health, drop dates. An AI-use policy is very likely absent from an older copy.
- **Attached syllabus PDF** matches the Canvas syllabus page. Students find the discrepancy.
- **Home page and course navigation** — items the colleague hid stay hidden.

## 8. Accessibility

Worth a pass on inherited content, which frequently has none of this: alt text on images,
real headings rather than bolded text, descriptive link text, captions and transcripts on
video, sufficient contrast in hand-built HTML, text-based rather than un-OCR'd PDFs. The
rich content editor has a built-in accessibility checker.

## 9. Content-level checks

This section is small and it is where the interesting findings live. Everything above
inspects *settings*. These read what is actually *in* the items, which is the only way to
catch a whole class of error.

- **Duplicate answer keys** across a series where each item should be unique — a per-class
  password, word-of-the-day, or access code. One query dumps them all; repeats are usually a
  copy-paste error that lets students answer with the wrong value. See recipes.md §3.
- **Answers that don't match their prompts.** A duplicate is a signal, not a verdict — read
  both prompts before concluding which is wrong, and confirm the intended answer against an
  authoritative source rather than your own reading of the clue.
- **Empty or truncated question sets** where the count looks plausible but the content didn't
  survive.
- **Placeholder text** left in from a previous build.

## 10. Ordering

Sequence matters mainly because it avoids rework:

1. Shell, term, participation dates — everything downstream depends on the container.
2. Delete or unpublish what isn't being used. Auditing content you'll discard is wasted effort.
3. The date sweep across what remains.
4. Grading structure.
5. Quizzes and banks — budget real time here.
6. Links, files, media, external tools.
7. Syllabus, home page, navigation, announcements.
8. Accessibility.
9. Link Validator, then **Student View**, then publish.

**Student View replaces about ten individual checks.** Walk week one as a student: open the
first module, open the first assignment, start the first quiz, look at Grades. Know its
limits — it doesn't reflect differentiated assignments or enrollment-date restrictions well.

## A note on what an audit is for

Report; don't fix unasked. A good fraction of what looks wrong is deliberate — the points
value they meant, the item kept unpublished for reference, the session that's a fieldwork
day. You cannot distinguish those from bugs by inspection, and an instructor who finds you
"corrected" an intentional choice will reasonably stop trusting the rest of the audit.

Rank findings by consequence and say plainly which ones reach students.
