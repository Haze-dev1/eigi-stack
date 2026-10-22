---
name: eigi-scope-discipline
description: Keeps Eigi planning and implementation scoped to what is actually required, with every addition beyond the source requirement tagged and listed for approval. Use whenever writing or reviewing a PRD, TRD, ADR, data model, schema, implementation plan, migration plan, ticket breakdown, or the code that follows from them. Use it even when the user only says "write the data models", "plan this out", "break this into tasks", or "build this feature" without mentioning scope — this skill decides what goes in and what gets flagged instead of built. Apply alongside eigi-backend-standards and eigi-frontend-standards, which govern how the in-scope work is structured.
---

# Eigi Scope Discipline

Build exactly what the source requirement asks for. Everything beyond it gets flagged for a human decision, never added silently.

## Priority order

**First priority: follow the Eigi house standards.** `eigi-backend-standards` and `eigi-frontend-standards` govern how work is structured — layering, folder placement, docstrings on every function, logging format, error handling, schemas and models, `.gitignore` hygiene, component boundaries, API client placement. These are not optional and are never trimmed. If this skill and a standards skill ever appear to conflict, the standards skill wins.

**Second priority: cut what is not needed.** Within the structure the standards require, include only what the source requirement asks for. Flag everything else for approval instead of building it.

The two do not actually conflict: the standards say how a thing is built, this skill says whether it gets built at all. A route that exists for a stated requirement gets the full house treatment — docstrings, logs, error handling, the correct layer. A route that exists for a requirement nobody asked for does not get built in the first place. Never cite scope discipline as a reason to skip a house standard on work that is in scope.

## The four tests

Apply these to every table, field, endpoint, component, phase, section, and abstraction before including it.

**1. Is there a stated requirement that needs this now?**
A specific line in the source document, not "might need," not "good practice." If yes, it is `(required)`. If no, it is not in scope by default — continue to test 2.

**2. Does skipping it cause a real, current problem?**
Data loss, a security hole, a state a user can actually reach that corrupts or leaks something, or the feature simply not functioning. If yes, it is `(required)` even if unstated — but say in one line what breaks without it, because the user is trusting this judgment. If the harm is hypothetical or only arrives at scale you do not have, it is not this.

**3. Is it solving for scale or flexibility you do not have yet?**
Multi-tenancy, pluggable providers, configurable behavior with one configuration, generic base classes for one implementation, caching before a measured performance problem, queues before a measured throughput problem, versioning schemes for content that has never been versioned. Cut it. Designing for a hypothetical v2 instead of the stated v1 is the most common failure here.

**4. Would removing it make the artifact harder to understand?**
If removing a layer makes things simpler, the layer was indirection for its own sake. An enum with one value, a wrapper model around a single field, a service that only forwards to one CRUD method, an interface with one implementation — these add a concept for no present benefit. Cut them.

## Tagging rules

Tag every proposed element inline:

- `(required)` — cite the source line or state the concrete failure it prevents. One line, no more.
- `(recommendation)` — anything beyond the source requirement, with a one-line reason.

Never mix them silently. At the end of every artifact, add a section titled **Not in scope — decide before building** listing every `(recommendation)` item as an approve-or-cut list. Each entry gets: what it is, what it costs to add now, and what it costs to add later instead. If that list is empty, say so explicitly.

Do not build `(recommendation)` items. List them and stop. They enter scope only when the user approves them, and once approved they become `(required)` in the next revision of the artifact.

## Per-artifact rules

**PRD** — Describe the problem, the users, and what success looks like. Do not specify implementation, data shape, or architecture. Requirements that came from the user stay separate from requirements you are proposing.

**TRD** — Answer only the PRD. Do not introduce infrastructure, services, or integrations the PRD does not need. Every component traces to a PRD line or a test-2 failure.

**ADR** — One decision per record. State the constraint forcing it, the options considered, the choice, and the consequences. Do not decide things that are not yet forced; an undecided question is a better ADR than a premature one. Record what was rejected and why, so it is not re-litigated.

**Data models** — Every collection, table, field, index, and enum passes the four tests. Specifically:
- No field for data nothing reads yet.
- No table for a concept a hash, a foreign key, or an existing field already covers.
- No soft-delete, audit trail, versioning, or history unless a requirement reads it back.
- No index without a query that uses it.
- Unbounded growth gets its own collection; bounded lists stay embedded.
- Prefer the simpler mechanism when two work (a filtered update over a transaction, a signed cookie over a stored record) and note the tradeoff in one line.

**Implementation plan** — Every step maps to a requirement. Do not add phases for monitoring, admin tooling, analytics, rate limiting, caching, feature flags, or abstraction layers unless a requirement names them or the feature cannot function without them. Those go in the not-in-scope list. Sequence by dependency, not by ambition.

**Tickets** — One ticket per plan step. Acceptance criteria restate the requirement; they do not add to it.

**Implementation** — Write what the ticket asks for, structured per the relevant Eigi standards skill. No configurability, no future-proofing, no extra dependencies. Duplication of a few lines beats a wrong abstraction; abstract on the third occurrence, not the first. Error handling, validation, and logging follow the standards skills — that is house style, not scope creep. Anything beyond it gets flagged, not written.

## Before writing anything non-trivial

Give a short plan first: the approach, and an explicit list of what you are **not** building and why. Wait for confirmation. Catching over-building at the plan stage costs a paragraph; catching it after the artifact is written costs a rewrite.

## Ask, do not guess

When a requirement is ambiguous, ask rather than resolving it by building the more capable version. The reader is often not a specialist in the area being planned and cannot always spot the difference between necessary and impressive. Silence on a judgment call is a failure of this skill, not a shortcut through it.

Two things are never cut under scope discipline: security and data integrity. If a requirement is silent on authorization, ownership checks, secret handling, or data loss, that is a gap to raise, not a licence to omit.

## Finish checklist

- The relevant Eigi standards skill was applied in full to everything in scope — this is checked first.
- No house standard was skipped on the grounds of minimalism.
- Every element tagged `(required)` or `(recommendation)`.
- Every `(required)` cites a source line or names a concrete failure.
- The **Not in scope — decide before building** section exists, even if empty.
- No `(recommendation)` item was actually built.
- Nothing designed for scale, flexibility, or a v2 that is not in the source document.
- No abstraction wrapping a single implementation.
- Ambiguities raised as questions rather than resolved by building more.
