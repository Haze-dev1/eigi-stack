---
name: eigi-test
description: Full test pass ending in one evidence report — static gates, unit suites, live-database integration tests, a structure and quality audit, an edge-case matrix, live API probes with log checks, and a browser pass delegated to a small model. Project-agnostic: step 0 derives the stack, commands, accounts, and journeys before anything runs, and the LRN profile ships with it. Use when asked to test, QA, or verify a project or a branch, before opening or merging a PR, before a promotion, or when checking that code sits in the right layers and logs correctly.
---

# Test pass

One run proves a change (or the whole app) on seven fronts and ends in one report. Every front ends **green**, **red**, or **not run (reason)**. Green comes only from a command you ran this session and its exit code — never from skipped tests, mocked providers, or old evidence.

## Guardrails

- **Local only.** Throwaway services, a made-up secret, and ports that are not the developer's own. Never point a run at a real database, a real provider account, or a shared environment, and start every server or script from an empty working directory so no `.env` from the project is picked up.
- **Providers in outage mode.** Point each provider base URL at a dead port (`http://127.0.0.1:9` is the usual one) so grading, LLM, mail, and voice calls fail fast and bill nothing. Real provider calls need a call budget the user approves for this run.
- **Report, don't fix.** Findings go in the report. Change product code only when the user asks, after the report.
- **Stop what you started, by PID.** `pkill -f` matches your own shell and kills the run.

## 0. Resolve the project profile

Everything below runs against a profile. Assemble it before running anything, in this order:

1. The repo's `AGENTS.md`, `docs/`, and CI workflow — the CI file is the only trustworthy source for the commands the project actually runs.
2. The bundled [LRN profile](#lrn-profile) when the repo is LRN.
3. The code itself, for whatever the first two leave unsaid.

Write the profile down — six lines, each sourced from something you opened:

```
Stack ....... language, framework, runtime version as declared, package manager
Commands .... lint, typecheck, unit, integration, build — exactly as the project runs them
Services .... what must run locally (database, cache, queue), and on which ports
Accounts .... how test identities are created, and the roles that matter
Journeys .... the doc that names user flows, or the changed features when none exists
Spec ........ the tracker or spec files that define what "correct" means
```

A front with no profile line is **not run** with that reason — never invented. Where the profile is silent, use the defaults named in each step and say so in the report.

When the repo keeps a docs tree, most of the profile is already written down. Read it before the code:

| Doc | Answers |
|---|---|
| `docs/product.md` | why it exists, who for, what a user and a tenant are |
| `docs/userflow.md` | the journeys a browser pass reproduces |
| `docs/ADR.md` | why it is built that way; decisions that must not be silently reversed |
| `docs/specs/*.md` | what one feature must do; its acceptance criteria |
| `docs/plans/*.md`, `docs/tracker/` | when it gets done, and where it stands today |
| `docs/edgecases/` | sample payloads to replay in the matrix |
| `docs/review/` | where this report goes |

Any of those may be absent or half-written. Absent is a `not run` reason on the front that needed it, not a licence to guess.

## 1. Scope

Pick the mode: **changed** (default; files since the merge base against the promotion branch the profile names, plus untracked) or **full** (the user asks for the whole app, or a promotion). List the files and map each to a feature or domain, using the profile's tracker or spec when it has one.

Done when every changed file maps to a feature or is labelled infra/docs-only.

## 2. Static and unit gates

Run every command the profile lists, always as full suites, never a subset filtered to the changed files. Use the project's own runner (`uv run`, `poetry run`, the venv, `npm`, `make`). Check the declared runtime version against the installed one first and switch when it is outside the declared range.

Done when each command has an exit code and its pass/skip/fail counts recorded.

## 3. Live-database integration tests

The step-2 skips are mostly database-gated tests (transactions, unique indexes, concurrency). Start the throwaway service per the profile and rerun the suite so those tests join the rest — for LRN that is [lrn §2](references/lrn.md#2-live-database-tests).

Done when the `-rs` summary shows no skip caused by a missing database flag; the skips left are invariant tests owned by later work. A failure here is a real finding even when step 2 was green: fakes don't reproduce write conflicts.

## 4. Structure audit

Two halves, and both are required.

**Machine half.** Run the project's own auditor when it ships one — LRN's is `scripts/audit_layers.py` beside this file:

```bash
python3 <this-skill-dir>/scripts/audit_layers.py          # changed mode
python3 <this-skill-dir>/scripts/audit_layers.py --all    # full mode
```

`<this-skill-dir>` is the directory holding this `SKILL.md`; in a Claude-style install that is `~/.claude/skills/eigi-test/`. When the project ships nothing, say the front is not run and compensate in the judgement half.

LRN's codes, for reading the output:

| Code | Rule |
|---|---|
| `LAYER` | Forbidden import for the file's layer (route→CRUD/database, CRUD→controller/fastapi, schema/model→services, service→HTTP glue) |
| `DOC001`–`DOC005` | Missing docstring, no two-line summary, missing `Args` / `Raises` / `Returns` |
| `LOG001`–`LOG005` | Route without an entry log or a catch-all `except`; public method without an entry log; stdlib `logging` or `print`; sensitive value interpolated into a log |
| `FE001`–`FE004` | Raw `fetch` outside the API layer, `console.log`, non-public env var, token key outside its one module |

**Judgement half.** Load the project's standards skills (the ones the profile names) and read each changed file against them. Then look for what no script sees: business rules in the entry layer; persistence outside the store layer; a domain error flattened into a 500; response schemas exposing storage-only fields; UI calling the API client instead of its feature module; missing loading, empty, or error states.

Done when every audit line and every changed file has a verdict: violation, or acceptable with a reason. In changed mode, split findings into **new** (lines this branch touched) and **pre-existing**.

## 5. Edge-case matrix

For each changed behaviour, walk every category in the project's case catalogue — [edge-cases](references/edge-cases.md) is the one LRN uses, and its categories transfer — and write one row per case that applies: the case, then where it is proven — an existing test (`tests/…::name`), a live probe (step 6), a browser journey (step 7), or **GAP**. Replay the payloads in `docs/edgecases/` whenever one matches a row.

Done when no row is blank and every category has rows or a one-line reason it does not apply.

## 6. Live API probes and log check

Start the API and create accounts per the profile — LRN: [lrn §3](references/lrn.md#3-api-and-accounts). For every matrix row assigned to this step, send the request with `curl` and check:

- **Response**: expected status; body free of stack traces, answer keys, rubrics, and other tenants' data.
- **Logs** (`<workdir>/logs/debug.log` under the LRN profile; uvicorn's stdout does not carry application logs): an entry line, `WARNING` for expected rejections, `ERROR` with `Error in …` for failures, and no secrets anywhere in the file:

  ```bash
  grep -nE 'eyJ[A-Za-z0-9_-]{20,}|Bearer [A-Za-z0-9]|otp=|password|api[_-]?key' "$W/logs/debug.log"
  ```

Done when every step-6 row has a status verdict and a log verdict.

## 7. Browser pass on a small model

Start the frontend per the profile — LRN: [lrn §4](references/lrn.md#4-frontend). Build the journey list from the changed features, the profile's journey doc, and the matrix rows assigned to this step. Dispatch it per [browser-pass](references/browser-pass.md) to a subagent on the smallest model tier your harness offers.

A small model's FAIL is a lead, not a verdict: reproduce every FAIL and PARTIAL yourself, in the browser or with a `curl` against the same endpoint, before reporting it.

Done when every journey is PASS, FAIL (reproduced), or BLOCKED (with reason), and each has evidence.

## 8. Report and teardown

Tear down per the profile — LRN: [lrn §5](references/lrn.md#5-teardown) — then report:

```markdown
## Test pass — <project>, <mode>, <branch> @ <short sha>, <date>

| Front | Result | Evidence |
|---|---|---|
| Profile resolved | yes/no | the six lines, and where each came from |
| Static (lint, types) | green/red | exit codes |
| Unit + build | green/red | passed/skipped/failed counts |
| Live-DB integration | green/red | counts; failing test ids |
| Structure audit | N new, M pre-existing | top codes |
| Edge cases | X tested, Y live, Z gaps | |
| API probes + logs | green/red | |
| Browser (model used) | n PASS / n FAIL / n BLOCKED | screenshot paths |

### Findings (most severe first)
- `path:line` — defect — how to reproduce — severity

### Gaps (edge cases nothing proves)
### Not run (and why)
```

If the project keeps a tracker, record the evidence in it per the project's own protocol. A finding already covered by a spec's deferral note is tagged `known` and kept out of the severity ranking. When the project has a review directory (`docs/review/`), write the report there too, and re-read any existing report for the same area so the new one supersedes rather than repeats it.

## LRN profile

Loaded when the repo is LRN — the FastAPI/Odmantic + MongoDB backend with a Next.js frontend, `development` integrated into `main`.

- **Commands.** Backend through `backend/.venv/bin/python`: `ruff check backend`, `mypy --config-file backend/pyproject.toml backend`, `pytest -q`. Frontend: `npm run lint && npm run typecheck && npm test && npm run build`, with the Node version from `frontend/.nvmrc`.
- **Local stack and ports.** [lrn](references/lrn.md): MongoDB on 27027 (single-node replica set), API on 8765, web on 3765, outage mode via `EIGI_BASE_URL=http://127.0.0.1:9`.
- **Accounts.** `scripts/seed_users.py` writes `users.json` with two students and a superadmin; roles are student, institution_admin, superadmin; the browser token key is `lrn_access_token`.
- **Audit.** `scripts/audit_layers.py`, codes as in step 4.
- **Docs.** `docs/userflow.md` for role journeys; `docs/specs/*.md` per feature; `docs/plans/implementation-plan.md` for architecture, invariants, and the `sec-state-protocol` that says how evidence is recorded; `docs/tracker/progress.json` and `docs/tracker/features/*.json` for state; `docs/ADR.md` for history; `docs/edgecases/*.json` for sample payloads; `docs/review/` receives the report. Where a doc is absent, read the status from the specs and the tracker instead.
- **Promotion branch pair.** `development` → `main`; `development` is also the base for every PR.
- **Case catalogue.** [edge-cases](references/edge-cases.md).

Its scripts and references assume these paths, so treat a repo that merely resembles this shape as needing its own profile lines rather than the LRN ones.
