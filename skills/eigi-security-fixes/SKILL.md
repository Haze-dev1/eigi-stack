---
name: eigi-security-fixes
description: >-
  Works through a security review's fix list one finding at a time, applying
  each fix in isolation, fixing sibling instances of the same pattern, running
  the finding's verify-after check, then re-verifying the diff against four
  criteria and stopping if the fix is only partial. Use after
  eigi-security-review has produced a ranked fix list. It does not hunt for new
  issues; re-run the review for that.
---

# Apply security fixes

Takes the output of `eigi-security-review` and drives the remediation loop the
review hands off: one finding, one fix, one verification, then the next. It
exists because "a fresh session per finding" is the right process and a lossy
hand-off for someone who is not a security engineer. This keeps each fix
scoped, checks it landed, and refuses to march past a fix that did not hold.

**What this does not do:** find new vulnerabilities, re-threat-model, or second
guess the review's severities. It also never rotates a secret, rewrites git
history, or changes a hosting or dashboard setting for you. Those it hands back
with instructions.

```
Apply-fixes progress:
- [ ] Step 0: Load and parse the fix list
- [ ] Step 1: Confirm fix order and manual prerequisites
- [ ] Step 2: Fix one finding in isolation, siblings included
- [ ] Step 3: Run the finding's "Verify after" check
- [ ] Step 4: Re-verify the diff against the four criteria
- [ ] Step 5: Summary, manual actions, re-review
```

---

## Step 0 — Load and parse the fix list

Take the review output, pasted or from a file path. Parse it into an ordered
list of findings, each with severity, `Where`, `Fix`, and for Critical and High
also the fix-session prompt and the `Verify after` steps.

If what you were given has no severity ranking and no per-finding `Where` / `Fix`
structure, **stop**. It is not a review fix list. Tell the user to run
`eigi-security-review` first and bring back its output.

State how many findings there are at each severity, and which ones you will act
on: Critical and High by default, ask before touching Medium or Low.

---

## Step 1 — Confirm fix order and manual prerequisites

- Follow the review's **Fix order** block if it has one. Otherwise propose one —
  prerequisites first, then Critical, then High — and confirm it.
- Surface every step that is not yours to do in the repo: rotating a leaked key,
  changing a dashboard setting, scrubbing git history, revoking a token. List
  them and get the user's acknowledgement before touching code.
- Confirm you can tell fixes apart: ideally one commit per fix, on a branch.

---

## Step 2 — Fix one finding, in isolation

For each finding, one at a time:

- Apply **only** that fix. No refactoring, no reformatting, no "while I'm here"
  changes, no files the finding does not name, unless the next bullet applies.
- **Grep for siblings of the same pattern** and fix those too: other routes with
  the same missing check, the same `select("*")`, the other HTTP verbs on the
  same resource, the other callers of the helper you changed, the other
  collection queries missing the tenant filter. The review may have cited one
  line; the bug is often in three places. List every location changed.
- Keep the change minimal and readable. If the real fix is architectural — a new
  middleware, a schema change, an index or migration — say so and get
  confirmation instead of forcing a shallow patch.
- Produce the diff.

**Get confirmation before** running a migration, changing authentication or
access-control code, installing a package, deleting a file, or pushing.

---

## Step 3 — Run the "Verify after" check

- Automatable (a `curl`, a test you can write and run): do it and show the
  result.
- Needs a browser or a second real account: print the exact steps, and wait for
  the user's result before calling the finding done.
- Always include the "legitimate path still works" step. An access-control fix
  that also locks out the owner is not done.

---

## Step 4 — Re-verify the diff against four criteria

Check the diff you just produced, not the review's promise:

1. **Root cause, not symptom.** Does the fix address the underlying flaw, or
   only the line the finding cited?
2. **No new surface.** Did it introduce an unscoped query, a broadened role, a
   loosened CORS or RLS rule, or a new caller that skips a guard?
3. **Every instance.** Are all the siblings from Step 2 fixed, not just the
   cited one?
4. **Legitimate path intact.** Name the exact click-through that shows the
   feature still works for an authorized user.

`fixed` when all four hold. `partial` when any of 1, 3, or 4 falls short.
`regressed` when 2 fails or a previously verified finding breaks.

- `fixed` → mark it done, next finding.
- `partial` or `regressed` → **stop.** Report what is still open or newly broken,
  take one more focused pass, or hand it back. Do not move on with an unresolved
  finding behind you.

Report the verdict with the lines that justify it. Do not wave it through.

---

## Step 5 — Summary

- **Fixed:** each finding, the files and lines changed, the verify result.
- **Needs your action:** the manual prerequisites, plus anything a fix surfaced
  — a key to rotate, a setting to change, a test to run in a browser.
- **Still open:** anything `partial` or `regressed`, and why.
- **Next:** re-run `eigi-security-review` over the whole diff. Fixes introduce
  regressions, and a clean re-review is the only way to know the list is closed.
  In pre-launch mode, do not launch before that re-review is clean.
