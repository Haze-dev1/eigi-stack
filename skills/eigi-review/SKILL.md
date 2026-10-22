---
name: eigi-review
description: Critical review of a project or a change — a pre-merge diff review by default, a whole-project audit on request. Works on any stack, because it first derives the project's own contract (standards, spec, commands, conventions) and then applies fifteen invariants to it. Every finding cites file:line and carries a severity. Eigi repos load the bundled profile, including its overrides, automatically.
---

# Review

Review only. You read, run checks, and report. The working tree stays exactly as you found it: no edits, no staging, no commits.

Your posture is **adversarial**: every contract is broken until you have traced it through every layer that touches it. Every claim in the report is backed by a `file:line` you opened or a command you ran.

## Modes

| Mode | Target | Chosen when |
|---|---|---|
| **diff** | everything that differs from the base branch, plus uncommitted work | there is a branch or PR to review; the default whenever a base can be found |
| **project** | the whole tree at HEAD, module by module | the user says "review the project", there is no branch to compare against, or a release or promotion audit is asked for |

State the mode in the first line of the report. Everything below is shared; steps 2, 5, and 7 branch by mode.

## Steps

### 1. Resolve the contract

The review checks the code against *this project's* rules, not a generic ideal. Assemble the contract, in this order, stopping when a source answers a question:

1. **Standards skills** — any `SKILL.md` in a sibling directory (`../*/SKILL.md`) or in the project's skill directories whose stack matches what is in play. Read the skill and every file in its `references/`.
2. **Repo documents** — `AGENTS.md`, `CLAUDE.md`, README, `CHANGELOG`; then the `docs/` tree by role: `product.md` (who it serves and what for), `userflow.md` (the journeys), `ADR.md` (why, and what must not be silently reversed), `specs/` (what one feature must do), `plans/` and `tracker/` (when, and where it stands), `edgecases/` (sample payloads). A missing doc is not a failure; a doc that contradicts the code is a finding.
3. **Manifests and CI** — `pyproject.toml`, `package.json`, `go.mod`, lint/typecheck/test config, and the CI workflow, which is the only trustworthy source for the commands the project actually runs.
4. **The code itself**, for whatever the first three leave unsaid.

Then write the **profile** — five lines, each sourced from a file you opened:

```
Stack .............. language, framework, versions as declared
Layering ........... the allowed call direction, and what may not import what
Commands ........... lint, typecheck, test, build — exactly as the project runs them
Spec ............... the file(s) that define behaviour, and what they own
Conventions ........ naming, URLs/versioning, logging, error mapping, where state lives
```

Where the profile is silent, the lenses' defaults apply, and you say so. If the profile contradicts a bundled standards skill, the profile wins and the conflict gets one line in the report.

Done when the five lines are written and every one has a file behind it.

### 2. Scope

**diff mode**

```bash
git status --short
git diff HEAD                                   # uncommitted work
git rev-parse --abbrev-ref origin/HEAD          # base; fall back to develop, then main
git diff <base>...HEAD --stat && git diff <base>...HEAD
git log <base>..HEAD --oneline
```

The **changed set** is the union of uncommitted and branch changes. Read every changed file in full. Then read the **far end of every contract** each change touches: the schema a route declares, the controller it calls, the store and model beneath, the tests that exercise it, and every doc or tracker file that names it (`grep` the identifiers).

**project mode**

1. **Inventory.** `git ls-files`, or `find` outside a repo. Count source, test, doc, and config files per area.
2. **Map.** For each layer the profile names, list the modules and the call path each belongs to. The map is a deliverable, not scratch work.
3. **Order by risk.** auth and tenancy → money and billing → data destruction, migration, and bulk operations → external integrations, webhooks, callbacks → public API surface → core domain → everything else.
4. **Read.** In full: everything in the first six bands, and every module the profile marks as load-bearing. For the remainder, run each lens as a `grep`/AST-driven sweep across the tree instead of reading file by file.
5. **Mark.** Every module gets `read`, `sampled`, or `skipped (reason)` in the map, so the report states its own coverage.

Scale rule: below ~200 source files, read everything; above it, risk order decides what is read in full and the report says which choice you made.

Done when (diff) every changed file and the far side of its contracts has been read, or (project) every module carries a mark and every `read` module was read in full.

### 3. Validation

Use the commands from the profile — CI config, `Makefile`, `package.json` scripts, `pyproject` tool sections. Run them through the project's own runner (`uv run`, `poetry run`, the venv, `npm`, `make`). Only when the profile names none, fall back to:

| Stack | Commands |
|---|---|
| Python | `ruff check .` · `mypy .` · `pytest -rs` (captures skip reasons) |
| Node/TS | `npm ci` · `npm run lint` · `npm run typecheck` · `npm test` · `npm run build` |
| Go | `go vet ./...` · `go test ./...` · `go build ./...` |

Before running anything, compare declared versions (`requires-python`, `.python-version`, `package.json` `engines`, `.nvmrc`, `go.mod`) against the installed toolchain; a mismatch is a finding, and you run on the declared version when it is available.

Snapshot `git status --short`, run the checks, snapshot again. A missing script is itself a finding. Any file the checks created or modified is a finding. Record pass/fail, counts (passed / failed / skipped with reasons), and warnings, including framework config warnings printed during build.

Done when every command has a recorded result or a recorded reason it could not run.

### 4. Apply every lens

Walk the **Lenses** below against the scoped set. The lenses are invariants; the profile supplies the concrete form each takes in this project. Done when each lens has been applied to every scoped file, not when enough findings have piled up.

### 5. Re-review

When a previous review is available — pasted into the conversation, in a file the user names, or a prior report from this skill — check every earlier point for **full** completion: a rename carried through files, classes, collections, and docs; a fix reflected in docs and tracker; a feature called done whose test is no longer skipped. A partially addressed point is re-raised with the remaining gaps listed exactly.

In project mode, the previous report also sets the baseline: findings already listed there and still present are `pre-existing`, not new.

### 6. Verify

For each candidate finding: reopen the cited line, state the concrete failure (the input or state that produces the wrong result), and tie it to a lens, a profile line, or a spec clause. Drop any finding that has none of these. Assign severity from the rubric.

### 7. Report

Write the report in the **Output format** below, in the mode you declared.

## Lenses

1. **Contract coherence.** Each fact has one source of truth, and every layer that carries it agrees: the entry point's signature, the request and response shapes, the function it calls, the query beneath, the stored field, the docs, and the tests.
   - A value accepted in two places with one silently ignored (date in both path and body).
   - A name that promises data that doesn't exist (`selected_option_id` when options carry only `position`).
   - An endpoint whose name and docs describe different behaviour from its response (an "export" returning metadata).
   - Mixed numbering conventions (0- vs 1-based) with the bound matching the wrong one (`ge=1`).

2. **Data integrity.** What can destroy, orphan, or leak stored data.
   - A projection or response model sharing a collection with the full model, so saving it overwrites the fields it omits. Projections are read-only types, never persistable.
   - Ambiguous ownership parameters (`owner_id`) where the model has distinct owner fields. Query the exact field.
   - Multi-field ownership or state transitions without a transaction; revoked access paths that still work afterwards (an old anonymous cookie still reading a claimed record).

3. **Auth boundary.** Every entry point is classified: public, anonymous, authenticated, or webhook. Identity is resolved in one place, injected, and passed inward explicitly. Owner-scoped endpoints enforce ownership on the server. Routes that set or clear session state can reach the response object; sign-out identifies the session, revokes it, and clears the cookie.

4. **Exact guards.** Allowlists, target checks, and safety confirmations match exactly what they claim. Compare the full identity: scheme, host, **effective port**, database, and every host of a multi-host URI. A guard that admits more than it names is a finding.

5. **Blast radius.** Bulk or destructive paths (`--complete`, deactivate, cleanup, delete, overwrite, migrate) touch only records this operation owns, scoped by version, source, or purpose.

6. **HTTP semantics.** A caller fault returns 4xx; a server fault returns 5xx. An invalid webhook signature is 400; a transient provider or database failure is 500. Domain errors pass through unchanged instead of being flattened into a 500.

7. **Validation.**
   - Typed, constrained input at the boundary: email types, enums or literals for controlled values, numeric and length bounds on years, scores, weights, counts, durations, and positions.
   - Existing enums reused wherever a plain `str` stands in (`difficulty_filter: str | None` → `Difficulty | None`); sweep for siblings.
   - No unvalidated field reaching a query, a template, a shell, or a filename.

8. **Layer ownership.** Imports follow the profile's direction. Lifecycle decisions (approval, reactivation, deactivation, versioning) sit in the layer the profile names, with persistence below it receiving explicit instructions. Definitions live beside what stores them; a shared module is justified only by actual sharing.

9. **Naming.** One domain vocabulary end to end: file, class, table or collection, route, schema, method, and URL.
   - A **partial rename** is a finding; list every straggler.
   - Methods name their verb and object (`export_account_data`, `request_account_deletion`), never bare `export`/`delete`.
   - One domain per module; a grab-bag module is split per domain.
   - A folder or naming convention that diverges from the project's siblings is flagged for the decision to be confirmed and documented.

10. **Spec compliance.** Code matches the authoritative spec: rules, category sets, approved values, scoring. A divergence requires either the code to change or the spec to be updated with formal approval. Check that downstream consumers (reports, charts, exports, clients) stay compatible with what is stored.

11. **Logging.**
    - Unexpected-exception handlers record the trace (`logging.exception(...)` or `exc_info=True`).
    - A request or correlation ID is bound through a context variable and filter, so every success and failure record carries it.
    - Secrets, tokens, cookies, and sensitive payloads stay out of every log line.

12. **Tests.** Tests cover the contract, not a sample.
    - Parameterized over every registered route, valid inputs, asserting the expected status.
    - An inventory assertion catches unregistered routes and checks the URL convention the profile declares.
    - Failure paths covered: invalid signature, wrong owner, invalid input.
    - Skipped tests reported with count and reason, and every skip attributed to a tracked issue.

13. **Honest docs.** README, plans, `AGENTS.md`, and tracker files match the current code: paths, filenames, spelling, test counts, validation results. Deferred work is written as deferred, never as complete. A README covers purpose, architecture, folder responsibilities, setup, environment, and run and test commands.

14. **Toolchain.**
    - Framework config holds only options the installed version supports; linting stays its own command.
    - Runtime versions declared where the project declares them (`engines`, `.nvmrc`, `requires-python`, `go.mod`) and compatible with the dependencies' requirements.
    - A frontend or service that exists only as folders or comment placeholders fails to build: a Blocker.

15. **API surface and versioning.** The URL a client calls is the URL the server declares, and every part of the path is visible in one place.
    - The version prefix comes from the profile. Any part of it applied centrally (`include_router(prefix=...)`, `APIRouter(prefix=...)`, a parent version router, a mounted sub-app) when the profile says decorators declare full paths is a finding.
    - A route missing the prefix, carrying it twice (`/api/v1/api/v1/...`), or using a different one beside the project's.
    - A frontend call whose effective URL (base URL env + path literal) lacks the prefix.
    - A changed or removed public URL: compare paths removed in the diff against those added. Moving a central prefix into decorators must leave every effective URL identical.
    - Route logs, token URLs, tests, and docs use the same full path as the declaration.

## Eigi profile

Load this section when the repo is an Eigi repo — FastAPI with Odmantic over MongoDB, and a Next.js frontend — or when `eigi-backend-standards` / `eigi-frontend-standards` sit beside this skill. It fills the five profile lines with the values the team has settled on, and it overrides the standards skills where the Eigi reviewer's feedback conflicts.

**Layering.** `route → controller → service and/or CRUD`. Routes do HTTP only; controllers orchestrate; CRUDs own persistence; services own integration and computation. `docs/plans/implementation-plan.md` holds the durable invariants; the package tree itself is the authority on how it is shaped today.

**Logging.** Entry logs on routes (`Calling METHOD /v1/... endpoint`) and on public controller, CRUD, and service methods (`Executing ...`). Unexpected-exception handlers use `logging.exception(...)` while keeping the standards' message format (`Error in ClassName.method: ...`). Standard-library `logging` and `print` are both findings.

**Auth.** Identity comes from a shared dependency injected with `Depends` and passed to the controller, replacing per-route `decodeJWT` blocks.

**Enums.** Sit beside the model that stores them; a standalone `enums.py` is justified only by sharing across models.

**HTTP status.** Invalid webhook signatures return 400.

**Versioning.** Every route declares its complete versioned path in its own decorator and routers register with no path prefix, so the decorator, route log, OpenAPI path, tests, and frontend client all show the same string:

```python
attempt_router = APIRouter()


@attempt_router.post("/v1/attempts")
async def start_attempt(...):
    ...


app.include_router(attempt_router, tags=["Attempts"])
```

The prefix is the one the repo already exposes — read it from existing routes, do not assume (`/v1` in eigi-lrn). Existing public URLs keep their exact path. `/health` is the only unversioned route. Webhooks and OAuth callbacks (`/v1/billing/webhook`, `/v1/email/webhook`, `/v1/auth/oauth/{provider}/callback`) carry the prefix because providers are registered against those URLs.

**Frontend.** `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` are all required. UI code calls its feature's `api.ts`, never the API client directly; loading, empty, and error states exist.

For worked findings from real Eigi reviews, written in the voice the report must use, read [references/examples.md](references/examples.md) before writing an Eigi report.

## Severity

- **Blocker**: data loss or corruption; another tenant's or owner's data reachable without server-side auth; a guard that admits the wrong target; build, typecheck, or test failure; a contract that cannot work as declared.
- **High**: spec divergence; wrong 4xx/5xx on an external integration; an unscoped destructive operation; missing validation on external input; work described as done that is not; a public URL unversioned, double-versioned, or changed; a frontend call to the wrong path.
- **Medium**: logging gaps; contract tests missing or sample-only; naming inconsistent across layers; stale docs or tracker; toolchain drift; business rules in the wrong layer; a version prefix applied centrally instead of where the profile puts it.
- **Low**: naming polish, module splits, spelling.

In project mode a finding the diff mode would never have seen is still reported, tagged `pre-existing` so it is not mistaken for something this change introduced.

## Output format

Group related symptoms under one numbered item (all identity plumbing is one item, not one per route). Order required changes by severity. Write in the imperative with "Please:" bullets. When two fixes are valid, name both, then state the recommended one and why. Reserve "consider" for optional additions inside an item.

```markdown
## Review: <branch> vs <base>, or <project> at <short sha> (<mode>, <N> files)

**Contract:** <stack + versions> · <layering> · <commands> · <spec source>

**Verdict:** diff mode — Not ready to merge: <n> Blocker, <n> High, <n> Medium, <n> Low.
            project mode — <n> Blocker, <n> High, <n> Medium, <n> Low across <m> modules (<k> pre-existing).

### Required changes

#### 1. [Blocker] <Imperative title>
`path/file.py:42` · `path/other.py:17`

<What is wrong, stated as fact.> <The consequence: what breaks, for whom, under which input.>

Please:
- <Concrete action.>
- <Concrete action.>

Recommended: <option>, because <reason>.   ← only when choosing between designs
```

### Naming

| Current | Rename to | Where | Severity |
|---|---|---|---|
| `card_controller.py` | `flashcard_controller.py` | `backend/.../card_controller.py` | Medium |

### Validation results

Python <x.y.z> (declared <spec>) · Node <x.y.z> (declared <spec>)

| Check | Result |
|---|---|
| ruff | passed |
| pytest | 56 passed, 6 skipped (reasons: …) |
| npm run build | failed: <first error line> |

Working tree after validation: clean | changed: <files>

### Coverage

Project mode only. The module map with each module's mark, and what was sampled rather than read.

### Out of scope

- <Area deliberately not reviewed, and why it does not block.>

<One sentence: the state the project or change will be in once the required changes land.>
```

A clean review keeps the same headings, a verdict of **Ready to merge** (diff) or **No blockers** (project), and the validation table.
