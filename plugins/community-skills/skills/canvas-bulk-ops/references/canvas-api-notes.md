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

New Quizzes (`quiz_lti`) are a different engine entirely and are not covered here; if
you encounter one, say so rather than guessing.

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
