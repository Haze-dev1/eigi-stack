# Eigi Review Examples

Real findings from eigi-lrn reviews, one per lens pattern. Each shows the defect, the consequence the reviewer named, and the exact ask. Match this voice: fact, consequence, "Please:", recommendation.

eigi-lrn facts below (scoring, categories, `docs/tracker/progress.json`, RAS tickets) illustrate the method; in other repos, read that repo's spec.

---

## Contract coherence: value in two places

**[Medium] Fix the study-plan update contract**
`PATCH /api/v1/plan/{day}` receives the date both in the URL and in `UpdatePlanSlotRequest`, while only the URL value is forwarded.

Please use one source of truth. Recommended:
- Declare `day: date` as the path parameter.
- Remove `day` from `UpdatePlanSlotRequest`.
- Keep only `category_id` in the body.

## Contract coherence: name promises missing data

**[High] Fix option identification**
The request schemas use `selected_option_id`, but question options only contain `position`.

Please choose one consistent design:
- Add a real stable ID to every option, or
- Rename the field to `selected_option_position`.

Also use one numbering convention everywhere. If option positions start at 1, validate the selected position with `ge=1`.

## Contract coherence: route says one thing, returns another

**[High] Fix the account-export contract**
`GET /api/v1/me/export` says it streams the user's JSON data, but `ExportMetadataResponse` only returns `media_type` and `streamed`.

Please either:
- Return the actual export using `StreamingResponse` or a JSON response, or
- Rename the endpoint and schema if it only creates or describes an export request.

The route name, documentation, controller method, and response must describe the same behavior.

## Data integrity: persistable projection

**[Blocker] Make `QuestionStem` non-persistable**
`Question` and `QuestionStem` use the same MongoDB `questions` collection. Because `QuestionStem` omits the correct answer and explanation, accidentally saving it overwrites the full question and destroys answer-key data.

Please change `QuestionStem` and `QuestionStemOption` into Pydantic projection/response models that cannot be passed to `engine.save()`. Only the complete internal `Question` model should be writable to `questions`.

## Data integrity: ambiguous ownership

**[Blocker] Make attempt ownership explicit**
`CRUDAttempt` accepts a generic `owner_id`, but `DiagnosticAttempt` has separate `user_id` and `anonymous_visitor_id` fields.

Please:
- Pass `RequestIdentity`, or explicit `user_id` and `visitor_id`, instead of `owner_id`.
- Query the correct ownership field.
- During identification, assign `user_id` and clear `anonymous_visitor_id` in the same MongoDB transaction.
- Ensure the old anonymous cookie cannot access the attempt after it has been claimed.

## Auth boundary

**[Blocker] Complete the authentication contract**
The project uses secure opaque session cookies, but the route signatures cannot support the flow.

Please:
- Make `resolve_request_identity` read the session/visitor cookies using `Request`, `Cookie`, or suitable dependencies.
- Inject `RequestIdentity` into every authenticated or owner-specific endpoint using `Depends`, and pass it explicitly to the controller.
- Inject `Response` into magic-link verification and OAuth callback routes so they can set the session cookie.
- Inject request/response into sign-out so it can identify the session, revoke it, and delete the cookie.
- Clearly distinguish public, anonymous, authenticated, and webhook endpoints.

Account, billing, report, plan, and practice endpoints must not rely on the frontend for protection.

## Exact guards

**[Medium] The exact target allowlist ignores MongoDB ports**
`backend/content/pipeline.py` builds the approved target from `urlsplit(parseable).hostname`, which excludes the port. `mongodb://localhost:27017/lrn` and `mongodb://localhost:27018/lrn` both match `localhost/lrn`.

Please compare the effective port for ordinary MongoDB URIs and handle multi-host replica-set URIs correctly.

## Blast radius

**[High] `--complete` may disable unrelated categories**
With `--complete`, the command disables every category not in the new category file, including categories created for another question version or purpose.

Please scope deactivation to categories owned by this seed (corpus version or source).

## HTTP semantics

**[High] Correct webhook error handling**
Invalid Stripe or Resend webhook signatures return 500. The request itself is invalid.

Please:
- Return 400 for invalid signatures and 500 only for real temporary server failures, in both webhook flows.
- Add tests covering invalid signatures.

## Validation: existing enum bypassed

**[Medium] Use the `Difficulty` enum**
`PracticeSession.difficulty_filter` is `str | None`. Please change it to `Difficulty | None`, and check whether any other controlled fields should use existing enums instead of plain strings.

## Layer ownership: lifecycle rules in CRUD

**[Medium] Move content lifecycle decisions out of `CRUDContentSeed`**
`CRUDContentSeed.seed()` mixes persistence with lifecycle decisions: automatic approval, reactivation, deactivation.

Please introduce a `ContentSeedService` to orchestrate the seed and decide approval, reactivation, complete-seed deactivation, and corpus-version behavior. Keep `CRUDContentSeed` focused on MongoDB reads, writes, and transaction-safe persistence. The rules become easier to understand, test, and change safely.

## Layer ownership: detached enums file

**[Low] Keep enums beside their model**
`enums.py` holds values used only by one model's fields. Please define the enum in that model's module.

## Naming: partial rename (re-review)

**[Medium] Complete the flashcard naming**
The naming is still mixed: `flashcard_router.py` and `FlashcardState` sit beside `card_controller.py`, `CardController`, `card_crud.py`, `CRUDCard`, `card_states`, `card_sessions`.

Please use flashcard consistently for internal backend names: `flashcard_controller.py`, `FlashcardController`, `flashcard_crud.py`, `CRUDFlashcard`, `flashcard_states`, `flashcard_sessions`. The public URL `/api/v1/cards` can remain if that name is intentional.

## Naming table

| Current | Rename to |
|---|---|
| `bank_router.py` | `question_bank_router.py` |
| `/api/v1/bank/categories` | `/api/v1/question-bank/categories` |
| `plan_controller.py` | `study_plan_controller.py` |
| `AccountController.export()` | `export_account_data()` |
| `AccountController.delete()` | `request_account_deletion()` |
| `EmailEvent.type` | `event_type` |
| `learning_request.py` | `practice_request.py`, `warmup_request.py`, `flashcard_request.py`, `study_plan_request.py` |

## API versioning

Reviewer's comment on merge: "routes ki versioning proper nhi hai abhi bhi" (route versioning still isn't proper).

**[Medium] Declare the versioned path in each route decorator**
The API aggregator applies the version centrally with `app.include_router(attempt_router, prefix="/api/v1")`, while decorators declare `/attempts`. The route file hides its real URL, and the route log `Calling POST /attempts endpoint` no longer matches the path clients call.

Please:
- Declare the complete path in every decorator: `@attempt_router.post("/api/v1/attempts")`.
- Register routers without a path prefix: `app.include_router(attempt_router)`.
- Keep every effective URL identical. Existing public paths do not change.
- Keep `/health` as the only unversioned route. `/api/v1/billing/webhook`, `/api/v1/email/webhook`, and `/api/v1/auth/oauth/{provider}/callback` stay versioned.
- Add a test asserting every OpenAPI path starts with `/api/v1` except `/health`.

## Spec compliance

**[High] Fix the scoring rule**
The implementation gives -1 for an incorrect answer, but the repository's specification defines Correct +3, Incorrect +1, Unanswered 0.

Please change the implementation and tests to match the approved rule. If -1 has received formal product approval, update the authoritative specification instead.

**[High] Fix the diagnostic categories**
The approved diagnostic scores Accounting, Valuation, M&A, LBO Mechanics, Markets, and Judgment. The blueprint uses DCF and COMPS instead of Markets and Judgment.

Please use the approved groups and ensure stored scores remain compatible with reports, radar charts, and benchmarks.

## Logging

**[Medium] Improve logging**
`JsonFormatter` can include tracebacks, but routes call `logging.error(...)` without exception info.

Please:
- Use `logging.exception(...)` inside unexpected-exception handlers, or pass `exc_info=True`.
- Bind the request ID to every record using a `ContextVar` and logging filter, in both success and failure logs.
- Keep secrets, tokens, cookies, and sensitive payloads out of logs.

## Tests

**[Medium] Strengthen scaffold tests**
`test_stub_routes.py` verifies only one unfinished endpoint.

Please add a parameterized contract test covering all registered stub endpoints, with valid required inputs, confirming each returns 501. Also consider asserting the OpenAPI path and operation inventory so unregistered routes are detected.

## Honest docs

**[High] Clarify the attempt-claim transaction status**
The method names improved, but the MongoDB transaction is still not implemented and its test remains skipped under RAS-19.

If implementation belongs to RAS-19, please document it as deferred. Do not describe the transaction as completed.

**[Medium] Correct documentation and tracker**
The implementation plan still mentions `/api/v1/bank/categories`; the code uses `/api/v1/question-bank/categories`. `progress.json` reports outdated frontend test counts. Please update both with current results.

## Toolchain

**[Medium] Fix the Next.js configuration warning**
Next.js 16 does not recognize the `eslint` option in `next.config.mjs`.

Please remove it and keep linting as a separate command: `npm run lint && npm run typecheck && npm test && npm run build`. Declare Node in `package.json` `engines` and `.nvmrc`, matching the installed `jsdom` requirement (`"node": ">=22.22.2 <23"`), and Python via `requires-python`.

**[Blocker] Complete the basic frontend setup**
The frontend contains only folders and comment-based placeholder pages. Please add `package.json`, `layout.tsx`, `tsconfig.json`, configuration files, and basic page components so it runs and builds.

## Out of scope

- The missing Docker and CI/CD configuration is not part of this review and is not a blocker for this scaffold.
