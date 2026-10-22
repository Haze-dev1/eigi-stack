---
name: eigi-security-review
description: >-
  Reviews recent changes, or a whole app, for the security problems AI-built
  web apps actually have: broken access control, tenant isolation, checks that
  live only in the UI, input that reaches a real sink, leaked secrets. It
  threat-models the change, walks an OWASP/CWE checklist over every changed
  file, runs whichever scanners are installed, and ends with a severity-ranked
  fix list plus one unhedged verdict, BLOCK or PROCEED WITH NOTES. Use after a
  feature lands, after a batch of AI-generated changes, before launch, or when
  asked "is this safe", "security review", "audit this", "can this be
  exploited". Reviews the diff by default; whole-system in pre-launch mode.
---

# Security review

Static scanners see patterns, not design. Design review sees intent, not the
exploitable line. This pass does both, in one flow, and ends with a list someone
can act on.

**What this is not:** a scanner (it tells you which to run and reports which
were absent), a guarantee (a clean review ships nothing on its own), or the fixer
(that is `eigi-security-fixes`).

Copy this checklist into your reply and work top to bottom. This pass produces
the list; it fixes nothing.

```
Security review:
- [ ] Step 0: Scope, contract, auth helpers
- [ ] Step 1: Change inventory + data-flow map
- [ ] Step 2: Threat-model the changes
- [ ] Step 3: Line-level checklist over every changed file
- [ ] Step 4: Pattern catalogue pass
- [ ] Step 5: Rules drift re-check
- [ ] Step 6: Scanners, dependencies, secrets, exposure
- [ ] Step 7: Triage, confidence, strictness
- [ ] Step 8: Ranked fix list + verdict
```

---

## Step 0 — Scope, contract, auth helpers

**Scope.** Diff mode is the default: everything since the last reviewed commit,
or `git diff` against the base branch plus uncommitted work. If no baseline
exists, ask what was just built and review that. Pre-launch mode reviews the
whole application, and Step 2 walks each trust boundary instead of each changed
file.

**Contract.** Read, in this order, whatever exists: a security rules section in
`AGENTS.md` / `CLAUDE.md`; `docs/security-rules.md` or `security-rules.md`; a
data-flow note (`docs/SECURITY-DATA-FLOW.md`, `SECURITY-DATA-FLOW.md`,
`docs/data-flow.md`). A missing file is a scope note, not a finding. A rule the
code violates is a finding, tagged `rules drift` in Step 5.

**Auth helpers.** Open the source of every guard the change relies on:
`requireUser`, `getSession`, `assertTeamAdmin`, a role decorator, route
middleware, an RLS policy, an Odmantic dependency. Read what it actually checks.
A function named `assertTeamAdmin` can still check the wrong thing. If the
source cannot be found, every verdict that depends on it is marked
`needs human eyes`.

---

## Step 1 — Change inventory and data flow

One row per review target, filled in as you go:

| File | Target (route / query / mutation / auth check / form / config / migration) | Trust boundary crossed | Verdict |
|---|---|---|---|
| `app/api/orders/[id]/route.ts` | `GET` handler + `db.order.findUnique` | browser → server → DB | (Steps 2–4) |

Every row ends with a finding ID or `safe — <file:line that makes it safe>`. A
skipped row needs a stated reason. This is what stops the review from covering
only the two most interesting files.

If no data-flow note exists, build a rough one as you go, or offer to write one
from [references/data-flow-note.md](references/data-flow-note.md).

State the scope and baseline, then show the inventory before continuing.

---

## Step 2 — Threat-model the changes

Full method, worked examples, STRIDE crosswalk:
[references/threat-model.md](references/threat-model.md).

For each new or changed endpoint, route, query, mutation, or form:

1. **Which trust boundaries does it touch?** browser → server, server → database,
   webhook → handler, app → third-party API.
2. **Who can call this, and as whom?** Walk IDOR and tenant isolation: can user A
   read or change user B's data by editing an id, a cookie, or a body field?
   Confirm the ownership check runs on the server, per record, not just "someone
   is logged in". Trace each caller-controlled identifier end to end and confirm
   the authz check and the fetch key on the *same* id. A check on `body.orgId`
   feeding a fetch by `params.projectId` is still broken.
3. **What is the worst malicious input?** Oversized, wrong tenant, replayed,
   someone else's token, negative or overflowing number, unexpected type, an
   operator where a value belongs.
4. **What happens when it fails?** Does it fail closed? Does the error leak a
   stack trace, an internal path, a database error, or another user's data?

Then critique your own four answers. A model reviewing its own code misses
roughly a fifth of real issues on the first pass; go back over each answer
looking for what you rationalized away. Anything not clearly safe becomes a
candidate for Step 8.

---

## Step 3 — Line-level checklist

Work through [references/checklist.md](references/checklist.md) against every
changed file: roughly twenty items ordered by how often they appear in
AI-generated code, each with what to look for and what a fix looks like, plus a
cross-file block for what a diff hides (a shared helper relaxed, a new caller
that drops a guard, a write verb missing the read path's check).

The long tail — SSRF, deserialization, SSTI, mass assignment — is in
[references/checklist-extended.md](references/checklist-extended.md). Scan it
too in pre-launch mode, or when the change touches network calls, file handling,
or serialization.

**Calibration.** Before writing a finding, check it isn't already handled
elsewhere in the change: an auth guard, ORM parameterization, framework CSRF, a
schema validator. Keep genuine low-severity findings for this audience — an
unvalidated input or a stack trace in an error is worth reporting without a
proven exploit — but a review padded with theoretical findings gets ignored.

**Data layer.** The checklist's RLS and migration advice assumes Postgres. On a
document store (MongoDB through Odmantic, Firestore) there is no RLS: the
equivalent check is that every query carries the owning id in its filter, and
that caller-supplied objects never reach the query as operators — `$ne`,
`$gt`, `$where`, `$expr`, `$regex` in a request body are injection, not a
filter. A `find` or `update_one` without the tenant id in its filter is the
finding, whatever the schema says.

---

## Step 4 — Pattern catalogue

Load only what the change touches. `references/catalog/` holds seventeen
vulnerability guides plus language and infrastructure notes; the selection is by
what the code is, not by what you already know.

| Change touches | Load |
|---|---|
| Routes, endpoints, GraphQL | `authorization.md`, `authentication.md`, `injection.md`, `api-security.md` |
| Templates, frontend, rich text | `xss.md`, `csrf.md` |
| Uploads, file paths, XML | `file-security.md` |
| Tokens, crypto, secrets, PII | `cryptography.md`, `data-protection.md` |
| Serialization, queues, caches | `deserialization.md` |
| Outbound requests, webhooks | `ssrf.md` |
| Workflows, money, state machines | `business-logic.md` |
| Headers, CORS, debug flags | `misconfiguration.md` |
| CI, lockfiles, build scripts | `supply-chain.md` |
| Errors, audit logs | `error-handling.md`, `logging.md` |
| WebSockets, LLM calls, prototype keys | `modern-threats.md` |

Then the language (`catalog/languages/python.md` for `.py`, FastAPI, Django,
Flask; `catalog/languages/javascript.md` for `.ts`, `.tsx`, Next.js, Express,
React) and `catalog/infrastructure/docker.md` when a Dockerfile changes.

Only these three ship: Python, JavaScript, Docker. If the change is Go, Rust,
Java, Kubernetes, Terraform, CI pipeline, or cloud IAM, say which guide was
missing and reason from the closest one — do not silently imply coverage that
does not exist.

---

## Step 5 — Rules drift re-check

If the project keeps a security rules block, work through it rule by rule against
the changed code, assuming the rules faded from context during a long session. A
violated rule is a finding, tagged `rules drift`. If there is no rules block,
recommend a short plain-language one in `AGENTS.md` and move on.

---

## Step 6 — Scanners, dependencies, secrets, exposure

Deterministic tools first: cheap, they do not hallucinate, and they anchor the
reasoning. Check each with `command -v` and run what exists.

| Target | Tool |
|---|---|
| Secrets | `gitleaks detect`, `trufflehog filesystem` |
| Python | `bandit -r` |
| Node | `npm audit`, `osv-scanner` |
| Rust | `cargo audit` |
| Multi-language | `semgrep --config auto` |

Report which ran and which were absent, by name, as a table. "No findings" from a
tool that is not installed is not a clean bill of health, and a reader who cannot
tell the difference will take it as one.

For what to do about dependencies, secrets in history, and public exposure, see
[references/dependencies-secrets.md](references/dependencies-secrets.md). The
one judgment that is yours: is a newly public endpoint, bucket, or field *meant*
to be public?

---

## Step 7 — Triage, confidence, strictness

Read [references/strictness-rules.md](references/strictness-rules.md) every run.
It is the part that stops a finding being talked down, and every rule in it has a
reasonable-sounding counterargument that arrives exactly when you are writing
the finding.

**Confidence.**

| Level | Criteria | Action |
|---|---|---|
| HIGH | Vulnerable pattern and attacker-controlled input confirmed | Report with severity |
| MEDIUM | Vulnerable pattern, input source unclear | Note as `needs human eyes` |
| LOW | Theoretical, defense-in-depth | Do not report |

**Trace before you report.** Where does the value enter? What boundary does it
cross? What is the worst outcome for someone who fully controls it? A pattern
match without a confirmed attacker-controlled source is a false positive, and
false positives are not free: they train the reader to skim, which is how the
real finding gets missed. If the source cannot be confirmed, drop the severity
and say what is unconfirmed rather than asserting it.

State the path concretely: "request body `filename` at `api/upload.py:31`,
unvalidated, reaches `open()` at `storage/local.py:12`". A finding without a path
is a guess wearing a severity label.

**Do not flag:** test fixtures, dead or commented code, constants and
deployment configuration, values the framework already escapes or parameterizes,
or a privileged path that requires prior authentication (note the requirement
instead). The catalogue files carry the per-framework detail.

---

## Step 8 — Ranked fix list and verdict

Format, severity rubric, and fix-session instructions:
[references/output-format.md](references/output-format.md).

Rank Critical → High → Medium → Low. Each finding gets what is wrong in one
sentence, a concrete failure scenario, the fix, a confidence tag, and whether a
scanner would also have caught it. Critical and High findings also get a
paste-ready fix-session prompt and a plain-steps **Verify after** check. Put a
**Fix order** block above the findings when there is more than one Critical or
High, or when a fix has a prerequisite.

Then one line, alone:

- **`BLOCK`** — any Critical finding, or any High finding at high confidence.
- **`PROCEED WITH NOTES`** — otherwise.

Nothing in between and no hedging. An ambiguous security verdict gets read as
approval, because that is what the reader wants it to say.

In pre-launch mode add a go / no-go line: any unresolved Critical means do not
launch. If nothing was found, say so plainly and say what was examined and what
was not; the unexamined part is the useful half of that answer.

Hand the list to `eigi-security-fixes`, which applies one finding at a time and
verifies each against these same criteria.

---

## Scope

Owns security. Not correctness (`eigi-review`), not structure, not minimality
(`ponytail-review`). Where a bug is both a correctness and a security issue,
report it here with the attacker path; the security framing decides whether it
blocks.

The catalogue in `references/catalog/` derives from the OWASP Cheat Sheet Series
under CC BY-SA 4.0; see [LICENSE](LICENSE).
