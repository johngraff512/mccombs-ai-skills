# New Quizzes (quiz_lti)

New Quizzes are a different engine from Classic Quizzes, and the difference is not cosmetic.
Roughly: **everything about how a New Quiz behaves as coursework runs on the ordinary Canvas
API and works fine in bulk. Everything about what is inside it runs on a different service
that may not be reachable at all from a browser session.** Establish which half you are in
before planning anything.

Claims below marked *(undocumented)* were not found in Instructure's API documentation. Verify
them on the instance before relying on them; do not present them to an instructor as fact.

---

## 1. Detection — do this first

New Quizzes **do not appear in `GET /api/v1/courses/:cid/quizzes` at all.** That endpoint
returns only `Quizzes::Quiz` records. A course that looks empty of quizzes may be full of them.

Both kinds surface in the Assignments API:

| | `submission_types` | Marker |
|---|---|---|
| Classic Quiz (graded) | `["online_quiz"]` | `quiz_id` present |
| New Quiz | `["external_tool"]` | `is_quiz_lti_assignment === true` |
| Plain LTI assignment | `["external_tool"]` | no quiz flag |

```js
const isNewQuiz = a => a.is_quiz_lti_assignment === true;
const isClassic = a => (a.submission_types || []).includes('online_quiz');
```

**Test truthily.** Canvas sets `is_quiz_lti_assignment` *only when true* — on a Classic Quiz or
an ordinary assignment the key is absent, not `false`. Never branch on `=== false`. The field is
also not in the published Assignment schema, so pair it with the `submission_types` check rather
than trusting it alone. Do not pattern-match the tool URL; its shape is undocumented.

Ungraded surveys and practice quizzes have no Assignment row and appear only in the Quizzes API.
A complete inventory therefore needs **both** endpoints, deduplicated on `quiz_id`.

## 2. What works in bulk on `/api/v1/` — most of the job

For a New Quiz, `PUT /api/v1/courses/:cid/assignments/:aid` handles `due_at`, `unlock_at`,
`lock_at`, `published`, `assignment_group_id`, `omit_from_final_grade`, `position`, `name`, and
overrides. Re-dating a series, bulk publish/unpublish, and moving items between groups all work
exactly as they do for assignments — **no New Quizzes-specific API required.** This is the path
to prefer for anything it can do.

Two things to respect:

- **`submission_types` is frozen** on a New Quiz. Never send it. Canvas lists it in
  `frozen_attributes` for exactly this reason.
- **`points_possible` rescales grades** rather than being cosmetic: New Quizzes scales the raw
  item score into the assignment-level total, so changing it changes what students earned.
  *(The scaling behaviour is undocumented by Instructure — institutional guides describe it, and
  it matches observed behaviour.)* Treat bulk `points_possible` edits on New Quizzes as
  grade-affecting and confirm explicitly before running one.

### The override-replacement trap

Straight from the Assignments API, worth quoting because it deletes data:

> If the `assignment[assignment_overrides]` key is absent, any existing overrides are kept as is.
> If the `assignment[assignment_overrides]` key is present, existing overrides are updated or
> deleted (and new ones created, as necessary) to match the provided list.

So sending a partial list **silently deletes the overrides you left out** — including a student
accommodation someone set last week. For surgical edits use the separate Assignment Overrides
API (`/api/v1/courses/:cid/assignments/:aid/overrides/...`) and leave the key off the PUT.

### Skip assignments that are mid-duplication

`workflow_state` of `duplicating` or `failed_to_duplicate` still appears in assignment listings.
A bulk date script will happily write to a half-created copy. Filter them out.

## 3. Duplication — the reverse of Classic

This inverts the Classic rule, so read it carefully:

- **Classic Quiz:** `POST /assignments/:aid/duplicate` returns **HTTP 400
  `quiz duplication not implemented`**. Rebuild question by question (api-notes §2).
- **New Quiz:** the same endpoint **works.**

But it is **asynchronous.** The POST returns immediately with `workflow_state: "duplicating"`;
the copy is not ready yet. Poll until the state leaves `duplicating`:

```js
const dup = await J(`/api/v1/courses/${CID}/assignments/${srcId}/duplicate`, {method:'POST'});
let a = dup;
for (let i = 0; i < 30 && a.workflow_state === 'duplicating'; i++) {
  await new Promise(r => setTimeout(r, 2000));
  a = await J(`/api/v1/courses/${CID}/assignments/${dup.id}`);
}
if (a.workflow_state === 'failed_to_duplicate') throw new Error(`duplicate failed: ${dup.id}`);
```

Three consequences:

- **A 200 does not mean success.** Canvas sweeps rows stuck in `duplicating` and marks them
  `failed_to_duplicate` later, so a duplicate can fail after your call returned.
- **The copy arrives unpublished**, always. Publishing is a separate PUT — which is the right
  order anyway.
- **Serialize, don't parallelize.** The content copy happens in the external quiz service.
  Firing 28 duplicates at once is untested territory *(undocumented)*; duplicate one, poll,
  proceed.

## 4. `/api/quiz/v1/` — probe before you promise anything

Question content and accommodations live at `/api/quiz/v1/...`, which is **not a Canvas route**.
It is a separate service reachable at the Canvas hostname because the hosted edge routes that
prefix to it. Every documented example authenticates with `Authorization: Bearer <token>`, never
cookies, and the New Quizzes UI reaches it from inside an LTI iframe with its own session — not
from the Canvas page.

**Whether Canvas session cookies authenticate against it is undocumented, and it may simply not
work from a logged-in browser page.** That is the whole basis of this skill's access model, so
find out before building a plan on it:

```js
const nqReachable = await fetch(`/api/quiz/v1/courses/${CID}/quizzes`, {credentials:'same-origin'})
  .then(r => r.ok).catch(() => false);
```

- **Reachable** → items and accommodations are available this session.
- **Not reachable** → say so plainly. These features need a Canvas API access token supplied
  out-of-band, which this skill does not use and should not ask for. Offer the `/api/v1/` half
  of the job and let the instructor do the rest in the Canvas UI.

Never design a job whose core depends on `/api/quiz/v1/` when an `/api/v1/` path exists.

### Question content

`GET|POST|PATCH|DELETE /api/quiz/v1/courses/:cid/quizzes/:assignment_id/items` — note the New
Quiz is addressed by its **Canvas assignment ID**, which is why detection comes first. Only
`QuestionItem` types can be created or updated; stimulus items, bank items and bank entries are
read-only via API and must be built in the UI. Community reports of the items endpoint returning
an empty array for a populated quiz are unresolved *(undocumented)* — verify against a known
quiz before trusting a bulk read.

### Accommodations

Two endpoints, both taking a **JSON array** — the bulk mechanism is built in:

| | Endpoint |
|---|---|
| Course-level (all quizzes) | `POST /api/quiz/v1/courses/:cid/accommodations` |
| Quiz-level | `POST /api/quiz/v1/courses/:cid/quizzes/:assignment_id/accommodations` |

`extra_time` is **minutes**, range 0–10080. `reduce_choices_enabled` works at both levels.
`extra_attempts` is **quiz-level only**; `apply_to_in_progress_quiz_sessions` is
**course-level only**.

**Inspect the response — a 200 does not mean everything applied:**

```json
{ "message": "Accommodations processed",
  "successful": [{"user_id": 5}],
  "failed": [{"user_id": 6, "error": "User is not in any in-progress quiz sessions..."}] }
```

Canvas's instructor guide states only one accommodation can be set per student per course, so a
second course-level POST **replaces** rather than adds. Whether course-level accommodations
apply to New Quizzes created *after* the POST is **undocumented** — the guide's "all quizzes in
a course" phrasing implies yes, but confirm on the instance rather than promising it.

> **Documentation bug worth knowing:** the accommodations docs declare the endpoints under
> `/api/quiz/v1/` but their curl examples show `/api/v1/`. The endpoint declarations and the
> OAuth scope strings agree on `/api/quiz/v1/`; use that.

## 5. Capability summary

| Operation | Classic | New Quiz |
|---|---|---|
| Appears in `/courses/:id/quizzes` | yes | **no** — Assignments API only |
| Bulk dates, publish, group, position | yes | yes, via Assignments API |
| `points_possible` | yes | yes — **rescales grades** |
| Assignment overrides | yes | yes — mind the replacement trap |
| `POST .../duplicate` | **no** (400) | **yes** — async, poll |
| Read/write questions | Quiz Questions API (`/api/v1/`) | `/api/quiz/v1/.../items` — probe first |
| Bulk extra time | Quiz Extensions (`/api/v1/`) | accommodations (`/api/quiz/v1/`) — probe first |
| Works from a browser session | yes | `/api/v1/` half yes; `/api/quiz/v1/` half unknown |
