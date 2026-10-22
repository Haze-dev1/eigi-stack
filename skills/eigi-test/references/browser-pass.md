# Browser pass on a small model

The browser pass is the long, mechanical part of the run: clicking through journeys and noting what happens. Hand it to a subagent on the smallest model tier your harness offers, and keep judging (reproducing failures, writing the report) for yourself.

## Dispatch

| Harness | How |
|---|---|
| Claude Code | `Agent` tool with `model: "haiku"`. Step up to `"sonnet"` only if haiku fails to operate the browser twice. |
| T3 Code | `orchestrator_capabilities`, pick the smallest model of the current provider, then `delegate_task`. |
| Codex | Spawn a subagent on the smallest model in the harness's live model list; read the list rather than recalling names. |
| No subagents | Run the pass yourself and note "browser pass not delegated" in the report. |

The subagent uses whichever browser tool it has: T3 preview tools (`preview_open`, `preview_snapshot`, `preview_click`, …), Claude in Chrome, or a Playwright MCP. With none available the pass is BLOCKED; say so.

Give it 8–12 journeys per dispatch. For more, split by role into parallel subagents. They share one database, so give each its own seeded accounts.

## Brief

Fill the `<…>` slots and send the whole block as the subagent's prompt.

```text
You are running a browser QA pass on <PROJECT>, <one-line description>, at <FRONTEND_URL>
(API at <API_URL>). You observe and report. You change no code and no files
other than the screenshots you save.

Signing in: open <FRONTEND_URL>, run
  localStorage.setItem("<TOKEN KEY>", "<TOKEN>")
then reload. Accounts:
<role | email | token, one per line>

Theme: localStorage.setItem("<THEME KEY>", "light" | "dark"), then reload.
Narrow layout: resize to 390x844. If the window ignores the resize, load the page inside a
390px-wide same-origin iframe instead.

Journeys:
<ID. role · start URL · steps · expected result>

Run every journey at desktop width in light theme, then repeat its key screen at 390px in
dark theme. On every screen also check for:
- console errors, and network responses with status 4xx/5xx (note URL and status)
- raw error text, stack traces, or "undefined"/"null" shown to the user
- horizontal overflow: document.documentElement.scrollWidth > window.innerWidth
- controls you cannot reach or see focus on with the keyboard

Never click: file downloads, payments, anything that emails a real address, or delete,
suspend or withdraw actions, unless the journey says to.

Reply with one table, then a list of anything odd outside the journeys:
| ID | role | what you did | expected | actual | PASS / FAIL / PARTIAL / BLOCKED | evidence (screenshot path, console/network lines) |
Mark a journey BLOCKED (with the reason) rather than guessing when something stops you.
```

LRN's values for those slots: `<PROJECT>` LRN, `<FRONTEND_URL>` `http://localhost:3765`, `<API_URL>` `http://localhost:8765`, `<TOKEN KEY>` `lrn_access_token`, `<THEME KEY>` `lrn-theme`. A project with no dark theme drops the theme line and the dark pass.

## After it returns

Reproduce every FAIL and PARTIAL yourself before it goes in the report: replay the step in the browser, or `curl` the endpoint the failing network call hit. Report the model used, plus anything you could not reproduce, as "unconfirmed (small-model report)".
