# Edge-case catalogue

The categories are the reusable part; every concrete case below is drawn from LRN's domain, and another project swaps in its own nouns (its roles, its tenants, its state machines) while keeping the shape.

Walk every category for each changed behaviour. A category applies when the behaviour touches what it names; otherwise give one line saying why it does not. Each case becomes a matrix row proven by a test, a live probe, a browser journey, or marked GAP.

## Auth and roles
- No token, forged token, expired token → 401; a token whose `session_version` is stale (after sign-out everywhere) → 401.
- Suspended or inactive account → 403; signing in again reactivates only where the product says so.
- Every role (student, institution_admin, superadmin) on every other role's route → 403. Superadmin acting on an institution needs an explicit institution scope.
- Open redirect: `/signin?next=//evil.com` and `next=https://…` stay on-site.

## Tenancy and ownership
- Institution A's owner on B's club, cohort, test, member, report or campaign → 404/403, with no B data in the body.
- Student A on student B's attempt, report, notification, flashcards or interview → 404/403.
- Invalid or foreign ObjectId in a path → 404/422, never 500.

## Answer keys and privacy
- Student-facing responses, PDFs and emails before result release carry no correct answers, rubrics, grader notes, or lead flags/notes (`tests/test_answer_key_leak.py` is the pattern).
- Logs carry IDs and counts only: no tokens, OTPs, passwords, answer text, or full candidate payloads.

## Input validation
- Empty, whitespace-only, at max length, one past max (written answers cap at 3,000 characters), unknown/extra fields → 422.
- Unicode: Devanagari, emoji, right-to-left text, and mixed Hinglish in names and answers.
- Numbers: locale formats (`1,5`), negatives, zero, huge values, NaN-like strings.
- Dates and zones: missing zone, past dates, close before due.

## State machines and concurrency
- Double submit, and two tabs submitting the same attempt.
- Concurrent writes that must stay unique (one current club per student, one active attempt) → one success, one 409, nothing half-written. Only the live-DB tests and live probes prove this; fakes do not.
- Stale revision on review or approval → 409 with a readable message, and the UI shows it.
- Invalid transitions: reopen, withdraw, re-release, edit after publish, apply after rejection.
- Idempotent actions (mark read, mark all read, re-upload the same import) change nothing the second time.

## Time
- Due date vs close deadline; closing while students are mid-attempt (countdown, then saved answers auto-submit and unanswered score 0).
- Timed attempts: countdown follows the server deadline, auto-submit at zero, reload mid-attempt.
- Display in 24-hour time with the zone; a user whose time zone differs from the institution's.
- Reminders and streaks across midnight in the user's zone.

## Lists and pagination
- Empty list, exactly one page, last page, ties in the sort key (stable ordering), invalid or tampered cursor.

## Imports and question banks
- Workbook with errors → error table and nothing imported; valid workbook → plan counts, then import; re-upload → all unchanged.
- Wrong template for the bank (admin vs club columns) → clear column error.
- Banks are append-only: existing questions are never silently rewritten.

## Providers and outages
- Eigi grader, Jev selector, voice agent, Gmail or Google unreachable (outage mode) → a handled 503 or documented fallback, no crash, no retry storm, no billed retries.
- Prompt injection in a free-response answer ("ignore the rubric…") is not obeyed or echoed. Needs real provider calls, so only with an approved budget.

## Frontend states
- Loading, empty, error and disabled states on every changed screen; raw error strings never shown.
- A 401 mid-session clears the token and returns the user to sign-in.
- A test in progress hides navigation and asks before unload.
- 390 px width with no horizontal overflow (`scrollWidth <= innerWidth`), dark theme, keyboard-only use with visible focus.
