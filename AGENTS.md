# eigi-stack

A bundle of 18 skills for Eigi work. Work done with this stack runs through those
skills: pick the one that matches the task, read it, and follow it ahead of your
own defaults.

## Running a skill

1. A request to build or change something follows
   [Building a change](#building-a-change). Anything else: match the task to a
   row in [Routing](#routing).
2. Read the skill's `SKILL.md` in full **before** starting the work it covers.
   The skill folder is `skills/<name>/` in this repo, or `.claude/skills/<name>/`
   in a project the stack is installed into.
3. Resolve every relative path in a skill from that skill's own folder. Load its
   `references/` and `scripts/` only when a step sends you there.
4. When a skill says to run another skill (for example "Call the Skill tool with
   `grilling`", or "run the **how** skill"), read that skill's `SKILL.md` and
   continue.
5. Eight skills set `disable-model-invocation: true`. The flag only stops the
   Skill tool from picking them on its own. This file loads them on purpose, so
   read their `SKILL.md` directly.

A skill is done when its own completion criterion is met, not when its last
heading is read.

## Routing

| Skill | Flow step | Load it when you are… |
|---|---|---|
| `in-your-own-words` | 1 | Starting any change, before reading code; or asked to restate the goal. |
| `how` | 2 | Learning how a subsystem works before changing it; asked "how does X work", "where should this live", "which layer owns this", or "teach me X". |
| `why` | 2 | Changing existing behaviour, ownership, or a defensive check; asked "why does X work this way", "why did we pick Y"; chasing a regression or writing a postmortem. |
| `grilling` | 3 | Settling open questions on a change; asked to grill, stress-test, or poke holes in a plan, decision, or design. |
| `grill-me` | — | Asked "grill me". A shortcut that runs `grilling`; the flow runs `grilling` directly. |
| `eigi-scope-discipline` | 4 | Writing or reviewing a PRD, TRD, ADR, data model, schema, plan, ticket breakdown, or the code that follows from one. |
| `architect` | 4, 6 | Adding or reshaping a module, interface, or data model: sketching types and signatures before code. |
| `figure-it-out` | 4, 6 | Facing a migration or a multi-part change too large for one plan of files. |
| `eigi-backend-standards` | 4, 6 | Planning, writing, or reviewing backend code (FastAPI, MongoDB, route → controller → service/CRUD). |
| `eigi-frontend-standards` | 4, 6 | Planning, writing, reviewing, or testing frontend code (React, Next.js, Vite, Vue, Svelte). |
| `ponytail` | 6 | Writing, refactoring, fixing, or choosing a dependency for any code. The standards skills decide structure; ponytail decides size. |
| `ponytail-review` | — | Asked to review for over-engineering, bloat, or what to delete. |
| `eigi-review` | 7 | Reviewing a change before merge (diff mode, default) or auditing a whole project (project mode). |
| `eigi-security-review` | 7 | Reviewing a change or a whole app for access control, tenant isolation, UI-only checks, injection, or leaked secrets; before launch. |
| `eigi-security-fixes` | 7 | Working through the fix list `eigi-security-review` produced. |
| `eigi-test` | 7 | Testing, QA-ing, or verifying a project or branch: before opening or merging a PR, before a promotion. Set `SKILL_DIR` to the `eigi-test` folder so its scripts resolve. |
| `technical-writing` | 4, 8 | Writing a plan, doc, README, RFC, PR description, or commit message. |
| `unslop` | 4, 8 | Finishing any prose a person will read. Runs after `technical-writing`. |

## Building a change

When the user asks for a feature, fix, or enhancement ("I want to do X"), run
these eight steps in order. Each step ends on its criterion; move on only when it
holds.

1. **Restate.** Run `in-your-own-words` on the request, before reading any code.
   Done when the user accepts the restatement; a correction gets a new one.
2. **Read.** Read the target repo's `AGENTS.md`, the docs in
   [Required docs](README.md#required-docs) that exist, and the code the request
   touches. Run `how` on each subsystem the change touches. When the change alters
   existing behaviour, ownership, or a defensive check (a retry, guard, flag, or
   limit), run `why` on it too; its Preserve / Change / Avoid / Risk set goes into
   the plan. Done when you can name every file the change will touch and why each
   is shaped the way it is.
3. **Grill.** Run `grilling` on the request, asking only what step 2 left open:
   intent, priorities, trade-offs. Done when the design tree is empty and the user
   agrees with the answers. For a typo, rename, or one-line change, skip this step
   and say so.
4. **Plan.** With `eigi-scope-discipline` and the standards skills that apply,
   write the plan to `docs/plans/<change-name>.md` in the target repo. It names
   what will be built, file by file, and lists every addition beyond the request
   separately, tagged for approval. Shape it with:
   - `architect` when the change adds or reshapes a module, interface, or data
     model. Its sketch (types, signatures, `not implemented` bodies) and rationale
     go into the plan. Its Phase A reuses step 2's `how` and `why` output.
   - `figure-it-out` when the change is a migration or spans several
     independently landable units. Its playbook (done predicate, rigor level,
     phase list) becomes the plan, and its decision log is a section of the plan
     file.

   Write the plan through `technical-writing`, then `unslop`. Leave
   `docs/plans/implementation-plan.md` as it is: it holds the project's durable
   invariants.
5. **Confirm.** Show the user the plan: what will be built, and what is flagged.
   **Stop and wait for an explicit yes.** Build only what the user approved; a
   change of plan goes back to step 4.
6. **Build.** Implement the approved plan with `eigi-backend-standards` /
   `eigi-frontend-standards` and `ponytail`. When `architect` shaped the plan,
   fill in its sketch (Phase D) and scrap it if the friction pattern of Phase E
   shows up. When `figure-it-out` shaped it, run each unit through its Phase C
   loop and log each one in the plan's decision log. Done when every file in the
   plan is written and the project's lint and type checks pass.
7. **Check.** In this order:
   1. `eigi-review` in diff mode; fix every blocking finding.
   2. `eigi-security-review`, then `eigi-security-fixes` on each finding, until
      the verdict is `PROCEED WITH NOTES`.
   3. `eigi-test` last, so its evidence covers the fixed code.
8. **Report.** One summary for the user, written through `technical-writing` and
   `unslop`: what was built against the plan, the review and security findings
   and what happened to each, the test report's path and result, and anything
   skipped or left open. Commit messages and PR descriptions follow the same two
   skills.

`eigi-review`, `eigi-test`, and `eigi-security-review` build their profile from
the **target** project's `AGENTS.md` and docs, so run the whole flow from the
target repo's root.

## Editing this stack

Three files describe the skill set, and they stay in step with `skills/`:

- `README.md`: the per-skill brief, Gaps, Modified, and Sources tables.
- `plugin.json`: the version and keywords.
- `.eigi-stack-provenance.json`: each skill's source, and a `modified` entry for
  every skill changed from upstream.

When you add, remove, rename, or change a skill, update all three and bump the
version in both JSON files. A skill folder's name matches its frontmatter `name`.

Skills marked `upstream_diverged` in the provenance file are rewrites. Edit them
in place; a fresh upstream copy would undo the rework.
