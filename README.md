# eigi-stack

A bundled set of skills for Eigi work: understand the code before changing it,
follow the repo's backend/frontend standards, delete more than you add, prove it
securely, verify it against the running stack, and write it down plainly.

## Layout

```
eigi-stack/
├── plugin.json                  manifest (name, version, skill list)
├── .eigi-stack-provenance.json  per-skill source and copy date
└── skills/
    ├── how/ why/ architect/ figure-it-out/ in-your-own-words/
    ├── unslop/ technical-writing/
    ├── eigi-backend-standards/ eigi-frontend-standards/ eigi-review/ eigi-scope-discipline/
    ├── ponytail/ ponytail-review/
    ├── eigi-security-review/ eigi-security-fixes/
    ├── grilling/ grill-me/
    └── eigi-test/
```

18 skills, 74 files, 480 KB. Each is a folder with `SKILL.md` plus any
`references/` or `scripts/` it ships. Frontmatter across all 18 costs about
1,700 tokens per turn once installed; bodies load only when a skill is invoked.

## Understanding before changing

| Skill | Brief |
|---|---|
| `how` | Explores a subsystem and explains architecture, runtime flow, and ownership/layering. Use before changing something you don't yet model. Its teaching mode turns the same exploration into one plain explanation for a person, pulling reasons from `why`. |
| `why` | Digs out design rationale from git, issues, docs, chat, logs, and analytics in parallel; returns a cited read on decisions and tradeoffs. |
| `architect` | Sketches types, signatures, and module boundaries with `not implemented` bodies before code. |
| `figure-it-out` | Auditable playbook for large ambiguous work: hypothesis loop, decision log, rigor scaled to the task. |
| `in-your-own-words` | Restates the goal it thinks you stated, so a misread surfaces before any work happens. |
| `grilling` | Relentless interview about a plan, decision, or design: maps it as a design tree, asks the whole frontier in numbered rounds with a recommended answer each, and doesn't act until the tree is empty and you agree. |
| `grill-me` | Seven-line alias that just calls `grilling`. Kept so the phrase "grill me" resolves; it needs `grilling` beside it to do anything. |

## Eigi standards

| Skill | Brief |
|---|---|
| `eigi-backend-standards` | FastAPI/MongoDB layering, folder placement, docstrings, logging, schemas, models. Self-contained: ships its own folder template and examples. |
| `eigi-frontend-standards` | Folder structure, component boundaries, API clients, styling, state, env handling, tests for frontend apps. |
| `eigi-review` | Critical review in the Eigi lead reviewer's style, in two modes: a pre-merge diff review (default) or a whole-project audit. Derives the project's contract first, so the same skill reviews any stack. |
| `eigi-scope-discipline` | Keeps plans and code scoped to the requirement; every addition beyond it gets tagged and listed for approval. |

## Less code

| Skill | Brief |
|---|---|
| `ponytail` | Forces the laziest solution that works: YAGNI first, stdlib before custom code, native features before dependencies. Levels: lite, full, ultra. |
| `ponytail-review` | Review focused only on over-engineering — what to delete, what replaces it. |

## Security

| Skill | Brief |
|---|---|
| `eigi-security-review` | One pass: threat-model the change for broken access control and tenant isolation, walk an OWASP/CWE checklist over every changed file, load the pattern catalogue for what the code actually does, run whichever scanners are installed, and end with a severity-ranked fix list plus BLOCK or PROCEED WITH NOTES. Diff by default, whole-system pre-launch. |
| `eigi-security-fixes` | Works that list one finding at a time: fix in isolation, fix siblings of the same pattern, run the finding's verify-after check, then re-check the diff against four criteria and stop on a partial fix. |

## Verification

| Skill | Brief |
|---|---|
| `eigi-test` | One QA pass on seven fronts — static gates, unit suites, live-database tests, a structure/quality audit, an edge-case matrix, live API probes with log checks, and a browser pass delegated to a small model — ending in one evidence report. Derives the project's profile before running, ships the LRN profile. Reports, never fixes. |

## Writing

| Skill | Brief |
|---|---|
| `unslop` | Cuts AI tells: vocabulary, filler, hedging, formatting tics. |
| `technical-writing` | Layered standard: Diátaxis structure, Google developer style, STE instruction rules, Global English. |

## Gaps

The pstack skills (`architect`, `figure-it-out`, `why`, `technical-writing`)
used to name pstack skills and Cursor settings this stack does not ship. Those
references were rewritten to point at what is here; see [Modified](#modified).

### Paths that assume an install location

Every skill here is a folder that can sit anywhere. One still assumes a path:

| Skill | Assumption | Effect when installed elsewhere |
|---|---|---|
| `eigi-test` | `references/lrn.md` defaults `SKILL_DIR` to `~/.claude/skills/eigi-test` | works, but point `SKILL_DIR` at the real folder so the audit script resolves |

`eigi-security-review` Step 0 expects the project's own security rules
(`AGENTS.md` section, `security-rules.md`, `docs/SECURITY-DATA-FLOW.md`) and says
so when they are absent. LRN keeps a rules file at `.codex/skills/security-rules.md`;
it is not bundled here.

The pattern catalogue under `eigi-security-review/references/catalog/` ships
seventeen topic guides but only three language or infrastructure guides: Python,
JavaScript, Docker. Upstream also promised Go, Rust, Java, Kubernetes,
Terraform, CI pipeline, and cloud guides; they were never written. The skill says
so in Step 4 and reasons from the closest guide instead of implying coverage.

`~/.claude/skills/` also holds `grill-with-docs`, a second alias that calls
`grilling` plus `domain-modeling`. It is not bundled because `domain-modeling`
isn't: copy both if you want ADR-and-glossary capture during an interview.

## Modified

| Skill | Source | Change |
|---|---|---|
| `eigi-test` | arena `.claude/skills/lrn-test`, 106 lines | Rewritten as `eigi-test`: step 0 resolves a six-line project profile (stack, commands, services, accounts, journeys, spec) before anything runs, the seven fronts and the evidence rules are unchanged, and every LRN specific — ports, commands, seed script, tracker paths, roles, `lrn_access_token` — moved into the `LRN profile` section and `references/lrn.md`. Hardcoded `.claude/skills/lrn-test/` paths replaced with `<this-skill-dir>` / `SKILL_DIR`. |
| `eigi-security-review` | `review-app-security` (SKILL + 6 references), `security-gate` (strictness rules, scanner table, verdict), `security-review` (17 topic guides, 2 language guides, Docker) | Merged four skills into one. The review passes now run as steps 0–8 of a single flow: scanners and the input-to-sink trace sit before triage, the catalogue is demoted to `references/catalog/` and loaded by what the code touches, and the two output contracts become one, ending in `BLOCK` / `PROCEED WITH NOTES`. Dropped the duplicated `METHODOLOGY.md` single-file copy and both per-skill READMEs. Fixed: the hardcoded `.claude/skills/` probe that printed a permanent "degraded" banner, and the seven catalogue guides that were never written (now stated in Step 4). Added a data-layer note: the RLS advice is Postgres-shaped, so on MongoDB the check is the tenant id in every filter and no `$ne`/`$where`/`$expr` from a request body. |
| `eigi-security-fixes` | `apply-security-fixes`, 96 lines | Now the only place fix verification lives: the four criteria and `fixed` / `partial` / `regressed` moved in from the review, so the old cross-skill "run fix-verification mode" call is gone. Re-verification runs against the diff the fix produced. |
| `how` | pstack `how`, 36 lines | Teaching mode folded in from `teach` (21 lines) and the dead `pstack-models.mdc` / `poteto-mode` spawn paragraph replaced with what a read-only subagent actually is. `teach` was pure composition over `how` + `why`. |
| `eigi-backend-standards` | `Eigi/lrn/.codex/skills/`, 109 lines | De-referenced. It named `agent-360/backend/vaani_core` as the canonical implementation, a path that does not exist anywhere on this machine, so every "go and read the reference" instruction dead-ended. The rules, the folder template, and `references/examples.md` now stand on their own. |
| `architect` | pstack `architect` | Phase B no longer runs `arena`: it produces two or more candidates itself, or one subagent each on the default model, and records the synthesis in the rationale. Phase C now always stops for sign-off. `interrogate` became `grilling`; the `pstack-models.mdc` runner slugs and every "per the X principle skill" pointer were dropped with the rules kept, here and in `references/runner-prompt.md` and `references/rationale-template.md`. |
| `figure-it-out` | pstack `figure-it-out` | Dropped the read-`poteto-mode` first step and every principle-skill pointer, keeping each rule. Phase A now waits for a go-ahead. `arena` and `laziness-protocol` became `architect` and `ponytail`; `show-me-your-work` became a decision log kept in the plan file. |
| `why` | pstack `why` | Replaced the `pstack-models.mdc` slugs, the `poteto-mode` subagent pointer, and the Cursor `generalPurpose` / `mcps/` instructions with the default model and the MCP tools available in the session. |
| `technical-writing` | pstack `technical-writing` | "swarm logs" became "agent logs". |
| `eigi-review` | `Projects/review/skills/eigi-review`, 222 lines | Rewritten to 265 lines. Two modes: **diff** (default, unchanged job) and **project** (whole-tree audit, risk-ordered, with a coverage map). Scope is now derived rather than assumed: step 1 assembles a five-line contract from standards skills, repo docs, and CI config, so the lenses work on any stack. Eigi's conventions survive intact as the `Eigi profile` section, which also carries the Overrides. **Diverged from upstream — do not replace with a fresh copy.** |

## Sources

| Skills | Copied from |
|---|---|
| `how` `why` `architect` `figure-it-out` `technical-writing` (all modified) `in-your-own-words` `unslop` | `cursor/plugins` → `pstack/skills/` at `d1453c1` |
| `eigi-backend-standards` `eigi-frontend-standards` | `Eigi/lrn/.codex/skills/` |
| `eigi-review` (modified — see above) | `Projects/review/skills/eigi-review` |
| `eigi-scope-discipline` `ponytail` `ponytail-review` `grilling` `grill-me` | `~/.claude/skills/` |
| `eigi-security-review` (merged) `eigi-security-fixes` (merged) | `review-app-security` + `security-gate` + `security-review` from this arena and `~/.claude/skills/`; `apply-security-fixes` from this arena |
| `lrn-test` (now `eigi-test`, modified) | this arena's `.claude/skills/` |

## Required docs

The three profile-driven skills — `eigi-review`, `eigi-test`, `eigi-security-review` — read the project before they act. This is the tree they expect. Every entry is optional on its own: a missing doc costs that line of the profile and the skill says so, rather than inventing one.

| Doc | Answers | Read by |
|---|---|---|
| `AGENTS.md` | house rules, layering, the commands to run, and a `## Security rules` section | all three |
| `CLAUDE.md`, `README.md`, `CHANGELOG.md` | context, history, whatever `AGENTS.md` leaves out | review |
| `docs/product.md` | why the product exists, who it serves, what a user and a tenant are | review, test |
| `docs/userflow.md` | the journeys a browser pass reproduces | review, test |
| `docs/ADR.md` | decisions that must not be silently reversed | review, test |
| `docs/specs/*.md` | what one feature must do, its acceptance criteria, its deferral notes | review, test |
| `docs/plans/implementation-plan.md` | durable invariants, architecture, and the protocol for recording evidence | review, test |
| `docs/tracker/progress.json`, `docs/tracker/features/*.json` | where each feature stands today | test |
| `docs/edgecases/*.json` | payloads to replay in the edge-case matrix | test |
| `docs/review/` | where the report is written, and where prior reports live | test, security |
| `docs/SECURITY-DATA-FLOW.md` (or root `SECURITY-DATA-FLOW.md`, `docs/data-flow.md`) | trust boundaries, what crosses them | security |
| `docs/security-rules.md` (or the `AGENTS.md` section) | the invariants security is checked against | security |
| `pyproject.toml` / `package.json`, CI workflow | the commands the project actually runs | all three |

`docs/architecture.md` and `docs/known-gaps.md` are deliberately **not** part of this set. The code is the architecture, and the tree can be read directly; deferral status belongs in each spec's own note and in the tracker, where it stays next to the thing it defers.

## Using it

Nothing here loads automatically. To make these active, either copy the folders
into a project's `.claude/skills/`, or open `eigi-stack/` as its own project.

Both `eigi-test` and `eigi-review` resolve a project profile before acting, and
both read it from the same place: `AGENTS.md` plus the docs tree in
[Required docs](#required-docs). A project without that tree gets a smaller
profile, and the skill says which lines it could not fill.
