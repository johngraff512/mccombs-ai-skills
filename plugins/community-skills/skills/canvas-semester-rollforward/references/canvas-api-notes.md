# Canvas API notes for bulk work

Hard-won behaviors that cost real debugging time. Read this before writing to Canvas.

## Contents

1. Getting authenticated access
2. Quizzes are not assignments
3. The unpublished-changes trap
4. Dates, locks, and DST
5. Pagination and search
6. Interruptions and idempotency
7. Endpoint quick reference
8. Keeping responses small

---

## 1. Getting authenticated access

The reliable path is to run `fetch` from inside a page already logged into Canvas,
using the browser's own session cookies. No API token to store, no separate auth.

Canvas requires a CSRF token on writes. It lives in the `_csrf_token` cookie and must
be URL-decoded:

```js
const csrf = decodeURIComponent((document.cookie.match(/_csrf_token=([^;]+)/) || [])[1] || '');
```

Canvas prefixes some JSON responses with `while(1);` as an anti-hijacking measure.
Strip it before parsing. A helper worth defining once per session:

```js
const J = async (url, opts) => {
  const r = await fetch(url, Object.assign({
    credentials: 'same-origin',
    headers: {
      'X-CSRF-Token': csrf,
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    },
  }, opts || {}));
  const t = (await r.text()).replace(/^while\(1\);/, '');
  if (!r.ok) throw new Error(`${r.status} ${url} :: ${t.slice(0, 200)}`);
  return JSON.parse(t);
};
```

Throwing on non-2xx matters. Without it a failed write returns an HTML error page that
parses as garbage or silently yields undefined, and a loop of 30 writes reports success
while having done nothing.

## 2. Quizzes are not assignments

Anything with `submission_types: ["online_quiz"]` is a Classic Quiz. It appears in the
assignments API but most assignment operations do not apply. Work through
`/api/v1/courses/:cid/quizzes/:qid` instead, using the `quiz_id` from the assignment.

`POST /api/v1/courses/:cid/assignments/:aid/duplicate` returns **HTTP 400
`{"error":"quiz duplication not implemented"}`** for classic quizzes. There is no quiz
duplicate endpoint. To copy a quiz, read the source quiz and its questions, then create
a new quiz and re-post each question. Copy the question objects programmatically in the
page rather than transcribing text — question bodies are HTML with markup that is easy
to corrupt by hand, and rubric tables are long.

New Quizzes (`quiz_lti`) are a different engine and are covered in
`references/new-quizzes.md` — **read it before touching one.** In short: they never appear
in the quizzes endpoint, they are addressed as assignments, dates and publish state work
normally in bulk, and — unlike Classic Quizzes — `duplicate` *does* work on them, though
asynchronously. Their question content and accommodations live on a separate service that
may not accept browser session cookies at all; probe before promising it.

## 3. The unpublished-changes trap

This one silently harms students, so it deserves care.

Any change to a **question** on an already-published quiz puts the quiz into an
unpublished-changes state. Canvas shows "You have made changes to the questions in this
quiz. These changes will not appear for students until you save the quiz." Until it is
cleared, students see the previous version — which, for a quiz you just built, means
**no questions at all**.

Re-saving through `PUT /quizzes/:qid` does **not** clear it. What does:

```js
await J(`/api/v1/courses/${CID}/quizzes/${qid}`, {method:'PUT', body: JSON.stringify({quiz:{published:false, notify_of_update:false}})});
await new Promise(r => setTimeout(r, 800));
await J(`/api/v1/courses/${CID}/quizzes/${qid}`, {method:'PUT', body: JSON.stringify({quiz:{published:true,  notify_of_update:false}})});
```

Better still, avoid it when creating: **create unpublished → add questions → set points
→ publish last.** Then the state never arises.

Editing only dates on a published quiz does **not** trigger it.

Verify rather than assume — the flag is not exposed reliably in the quiz JSON, so check
the rendered page:

```js
const html = await (await fetch(`/courses/${CID}/quizzes/${qid}`, {credentials:'same-origin'})).text();
const dirty = /changes to the questions in this quiz/.test(html);
```

Always set `notify_of_update: false` on bulk edits unless you intend to email every
student in the course about each one.

## 4. Dates, locks, and DST

Canvas stores and returns UTC. Send ISO8601 with an explicit `Z`.

- `unlock_at` — when students can see/open it
- `due_at` — when it is due
- `lock_at` — when submission closes. Many timed in-class activities set `lock_at` equal
  to `due_at`; check what the existing items do and match rather than inventing a policy.

Compute each date's UTC offset separately from the IANA database. A term that starts in
daylight time and ends in standard time will otherwise have its final weeks off by an
hour, in the direction that makes an activity open *before* you arrive. `scripts/build_schedule.py`
handles this; its test suite covers both fall and spring transitions.

The strongest available check on your time math: recompute the timestamps for an item
that **already exists and is known correct**, and compare to what Canvas stores. If your
computed value matches byte-for-byte, the method is sound.

## 5. Pagination and search

The API caps at 100 per page and does not warn when results are truncated. A course with
111 assignments returns 100 and looks complete. Always page:

```js
let all = [], page = 1;
while (page <= 20) {
  const batch = await J(`/api/v1/courses/${CID}/assignments?per_page=100&page=${page}`);
  all = all.concat(batch);
  if (batch.length < 100) break;
  page++;
}
```

`search_term` works on assignments and quizzes and is handy, but it matches loosely —
confirm with an exact regex on the title before acting on the result.

Watch for **en dashes** in titles (`–`, U+2013) where you assumed a hyphen (`-`). Titles
typed in a rich-text editor frequently contain them, and an exact-match filter that
assumes the wrong character silently returns nothing.

## 6. Interruptions and idempotency

A long-running script in the page **keeps executing even if the calling tool call is
interrupted or times out**. If you re-run a create loop after an interruption without
checking, you get duplicates.

Make create loops idempotent. Fetch existing titles first and skip what already exists:

```js
const existing = new Set((await J(`/api/v1/courses/${CID}/quizzes?per_page=100`)).map(q => q.title));
for (const item of plan) {
  if (existing.has(item.title)) { log(`${item.title}: SKIP already exists`); continue; }
  // ...create...
}
```

After any interruption, **audit before writing**: list what exists, compare to the plan,
and report duplicates or gaps before touching anything.

## 7. Endpoint quick reference

| Task | Call |
|---|---|
| Teacher's courses | `GET /api/v1/courses?enrollment_type=teacher&include[]=term&include[]=sections` |
| Course detail + syllabus | `GET /api/v1/courses/:cid?include[]=syllabus_body&include[]=sections` |
| Assignments | `GET /api/v1/courses/:cid/assignments?per_page=100&page=N` |
| Assignment groups | `GET /api/v1/courses/:cid/assignment_groups?per_page=100` |
| Quiz detail | `GET /api/v1/courses/:cid/quizzes/:qid` |
| Quiz questions | `GET /api/v1/courses/:cid/quizzes/:qid/questions?per_page=100` |
| Create quiz | `POST /api/v1/courses/:cid/quizzes` body `{quiz:{...}}` |
| Add question | `POST /api/v1/courses/:cid/quizzes/:qid/questions` body `{question:{...}}` |
| Update quiz | `PUT /api/v1/courses/:cid/quizzes/:qid` body `{quiz:{...}}` |
| Update assignment | `PUT /api/v1/courses/:cid/assignments/:aid` body `{assignment:{...}}` |
| Rendered page (banner check) | `GET /courses/:cid/quizzes/:qid` (HTML, not API) |

The course's own timezone is on the course object as `time_zone`. The syllabus body
often states the real meeting pattern and room — useful for confirming a schedule
rather than assuming one.

---

## 8. Keeping responses small

Everything here is one idea: **there are two hops, and only the second one is expensive.**

Canvas → the page → the model. The full object always makes the first hop; `J()` pulls
every field into a JavaScript variable and nothing is filtered out. What costs tokens is
what the page hands *back*. A field you didn't return is still in the page — retrieving it
later is one line against data already in memory, not another API call. So returning less
is never a restriction on what you can see; guessing wrong costs a cheap follow-up.

Measured on 28 representative assignment objects: the full dump runs ~13,600 tokens. The
same 28 items, with all 46 comparable fields checked, reported as anomalies only, runs
**~86 tokens**.

### Return a projection, not the object

There is no fixed field list — project what the task needs. A core of `id`, `name`,
`course_id` (the write guard reads it) and `published`, plus:

| Job | Add |
|---|---|
| Dates | `due_at`, `unlock_at`, `lock_at`, `only_visible_to_overrides`, `has_overrides` |
| Grading setup | `points_possible`, `grading_type`, `assignment_group_id`, `omit_from_final_grade`, `grading_standard_id`, `post_manually` |
| Submission settings | `submission_types`, `allowed_attempts`, `allowed_extensions`, `peer_reviews`, `anonymous_grading`, `moderated_grading` |
| Quiz config | `quiz_id`, `time_limit`, `shuffle_answers`, `scoring_policy`, `one_question_at_a_time`, `hide_results`, `access_code`, `ip_filter` |
| Differentiation | `group_category_id`, `grade_group_students_individually`, the overrides list |
| Modules / ordering | `position`, module membership |

Never return `secure_params`, `lti_context_id`, `submissions_download_url`,
`max_name_length`, `integration_data`, or the `grader_*` / `anonymous_*` booleans nobody
set — that is most of the bytes. `description` and `question_text` are HTML and often the
largest fields in the object: return them only when the job is *about* content.

### For audits, return findings rather than fields

Comparing items against each other inside the page scales to any number of fields, because
the output tracks the number of *problems*, not the number of fields checked.

```js
const skip = new Set(['id','name','due_at','unlock_at','lock_at','quiz_id','position',
                      'html_url','submissions_download_url','secure_params','description']);
const anomalies = [];
for (const k of Object.keys(items[0]).filter(k => !skip.has(k))) {
  const vals = items.map(it => JSON.stringify(it[k]));
  const mode = [...vals.reduce((m,v) => m.set(v,(m.get(v)||0)+1), new Map())]
                 .sort((a,b) => b[1]-a[1])[0][0];
  vals.forEach((v,i) => { if (v !== mode)
    anomalies.push({item: items[i].name, field: k, value: JSON.parse(v), expected: JSON.parse(mode)}); });
}
return {checked_items: items.length, anomalies};
```

Deviation from the mode is a *candidate*, not a defect — a deliberately double-weighted
item will surface here. Report them; don't fix them.

### Fetch narrowly

`include[]` parameters multiply the payload: `include[]=items` on a module list pulls every
nested page, quiz, and assignment link. Over-fetching also **truncates**, and a truncated
response costs additional paginated calls to recover — so the bloat is paid twice. Ask for
nested content only when the task touches item-level content.

When you already know which IDs you care about, fetch those rather than re-paginating the
whole collection.

### Batches report counts, not rows

Per-item GET-then-PUT for idempotency is correct and should stay. Returning all N result
objects buys no safety. Return the tally, and failures in full:

```js
return {changed: done.length, skipped: skipped.length, failed};   // not the N objects
```

### Verification returns a diff

"Check every item" means compare every item — inside the page — and return only what
disagrees. `{checked: 28, matched: 26, mismatches: [...]}` proves more than 28 dumped
objects, because it is a mechanical comparison rather than a visual scan.

### Read rendered pages as text

Confirming what Canvas actually serves does **not** mean taking a screenshot. A full-page
browser capture costs up to ~4,784 visual tokens on a high-resolution model (~1,568 on
standard); `get_page_text` on the same page is typically 1,000–3,000, and a fetch-plus-regex
that returns a boolean — as in §3 — costs almost nothing.

Reduce in the page and return the answer, not the markup:

```js
const html = await (await fetch(`/courses/${CID}/quizzes/${qid}`, {credentials:'same-origin'})).text();
return {dirty: /changes to the questions in this quiz/.test(html)};   // never return html
```

Screenshots are for things only pixels can settle: an icon state, a colour, a layout
problem, something rendering wrong. Not for reading text.
