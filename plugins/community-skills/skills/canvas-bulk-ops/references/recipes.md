# Recipes for common bulk Canvas jobs

Patterns for jobs that come up repeatedly. Each assumes the `J()` fetch helper and a
confirmed `CID` from SKILL.md step 1, and assumes you have already done a read-only audit.

## Contents

1. Copy a classic quiz N times
2. Bulk publish / unpublish a series
3. Content audit: find duplicate or wrong answer keys
4. Retire a superseded series
5. Shift a set of dates by an offset
6. Find what's actually in a course

---

## 1. Copy a classic quiz N times

Canvas cannot duplicate quizzes through the API, so build each copy from the source. Copy
the question objects programmatically — never retype question HTML.

Order matters: **create unpublished → add questions → set points → publish last.** Adding
questions to an already-published quiz strands students on a version with no questions
until you clear the flag (canvas-api-notes.md §3).

```js
const src = await J(`/api/v1/courses/${CID}/quizzes/${SRC_QID}`);
const sq  = (await J(`/api/v1/courses/${CID}/quizzes/${SRC_QID}/questions?per_page=100`))
              .sort((a,b) => (a.position||0) - (b.position||0));

async function makeCopy(title, unlockISO, dueISO) {
  const q = await J(`/api/v1/courses/${CID}/quizzes`, {method:'POST', body: JSON.stringify({quiz:{
    title,
    description: src.description,
    quiz_type: src.quiz_type,
    assignment_group_id: src.assignment_group_id,
    time_limit: src.time_limit,
    shuffle_answers: src.shuffle_answers,
    hide_results: src.hide_results,
    show_correct_answers: src.show_correct_answers,
    allowed_attempts: src.allowed_attempts,
    one_question_at_a_time: src.one_question_at_a_time,
    scoring_policy: src.scoring_policy,
    cant_go_back: src.cant_go_back,
    anonymous_submissions: src.anonymous_submissions,
    published: false,                       // publish last
    unlock_at: unlockISO, due_at: dueISO, lock_at: src.lock_at,
  }})});

  for (const s of sq) {
    await J(`/api/v1/courses/${CID}/quizzes/${q.id}/questions`, {method:'POST', body: JSON.stringify({question:{
      question_name: s.question_name,
      question_text: s.question_text,
      question_type: s.question_type,
      points_possible: s.points_possible,
      position: s.position,
      correct_comments: s.correct_comments,
      incorrect_comments: s.incorrect_comments,
      neutral_comments: s.neutral_comments,
      answers: (s.answers||[]).map(a => ({
        answer_text: a.text, answer_html: a.html,
        answer_weight: a.weight, answer_comments: a.comments,
      })),
    }})});
  }

  // A graded survey may carry points_possible independent of its questions' sum.
  // Match the source rather than assuming the sum is right.
  await J(`/api/v1/courses/${CID}/quizzes/${q.id}`, {method:'PUT',
    body: JSON.stringify({quiz:{points_possible: src.points_possible, notify_of_update:false}})});
  await J(`/api/v1/courses/${CID}/quizzes/${q.id}`, {method:'PUT',
    body: JSON.stringify({quiz:{published:true, notify_of_update:false}})});
  return q.id;
}
```

Verify each copy against the source on: quiz type, points, question count, question text
and type in order, assignment group, attempts, hide-results, description, published state.
Then check every copy for the unpublished-changes banner.

Note `position` reads back as `null` from the API even when display order is correct —
confirm order from the rendered edit page rather than trusting that field.

## 2. Bulk publish / unpublish a series

```js
for (const a of targets) {
  if (!a.published) continue;                       // idempotent
  await J(`/api/v1/courses/${CID}/assignments/${a.id}`, {method:'PUT',
    body: JSON.stringify({assignment:{published:false}})});
}
```

Canvas refuses to unpublish an item that already has student submissions. That refusal is
correct — surface it rather than working around it.

Prefer unpublishing to deleting, always. It hides the item from students, removes it from
grade calculations, and reverses in one click.

## 3. Content audit: find duplicate or wrong answer keys

Series where each item should hold a unique value — a per-class password, word-of-the-day,
access code — drift silently when someone copies an item and forgets to change the answer.
Settings checks never catch this. Dumping the content does:

```js
const answers = {};
for (const a of series) {
  const qs = await J(`/api/v1/courses/${CID}/quizzes/${a.quiz_id}/questions?per_page=100`);
  const key = (qs[0].answers||[]).map(x => (x.text||'').trim()).join('/');
  (answers[key] = answers[key] || []).push(a.name);
}
const dupes = Object.entries(answers).filter(([, v]) => v.length > 1);
```

A duplicate is a signal, not a verdict — read both prompts before concluding which one is
wrong, and confirm the intended answer from an authoritative source rather than your own
reading of the clue. Report and let the instructor decide.

To fix an answer on a **published** quiz, edit the question then run the
unpublish/republish cycle to clear the banner (canvas-api-notes.md §3).

## 4. Retire a superseded series

When a course shell carries an old series that a new one replaces, the old items keep
counting toward the group total and clutter the student view.

Identify precisely with an exact regex on the title — loose matching catches items the
instructor wants kept. Confirm the list with them, then unpublish. Report the resulting
group composition: how many items remain published, their total points, and anything in
the group that belongs to neither series.

## 5. Shift a set of dates by an offset

For a snow day or a syllabus slip, where the pattern holds but everything moves:

```js
const shiftDays = 2;
const shift = iso => {
  const d = new Date(iso);
  d.setUTCDate(d.getUTCDate() + shiftDays);
  return d.toISOString().replace(/\.\d{3}Z$/, 'Z');
};
```

Naive UTC arithmetic breaks across a DST boundary: shifting a date from October into
November keeps the UTC clock time and therefore moves the *local* time by an hour. If the
shift crosses a transition, rebuild from local time with a timezone library instead — the
`build_schedule.py` script in the `canvas-semester-rollforward` skill does this correctly.

After any shift, re-check that every date still lands on a real meeting day.

## 6. Find what's actually in a course

Orient before doing anything else:

```js
const groups = await J(`/api/v1/courses/${CID}/assignment_groups?per_page=100`);
let all = [], page = 1;
while (page <= 20) {
  const b = await J(`/api/v1/courses/${CID}/assignments?per_page=100&page=${page}`);
  all = all.concat(b); if (b.length < 100) break; page++;
}
const summary = groups.map(g => ({
  name: g.name, id: g.id, weight: g.group_weight,
  count: all.filter(a => a.assignment_group_id === g.id).length,
}));
const weightTotal = groups.reduce((s, g) => s + (g.group_weight || 0), 0);
```

Two things to look at immediately:

- **Do group weights sum to 100?** If not, and especially if group *names* repeat, the
  course has content from more than one import. Flag it — it distorts every student's grade.
- **Do item counts match the syllabus?** A group with 23 items where the syllabus promises
  28 means gaps worth understanding before you add anything.
