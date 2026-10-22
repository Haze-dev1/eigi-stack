---
name: how
description: "Use for \"how does X work\", code walkthroughs before changing something, placement / ownership / layering questions (\"where should this live\", \"which package owns this\", \"is this the right layer\"), and teaching requests (\"teach me this\", \"help me really understand X\", \"explain this change or subsystem to me\"). Explains subsystem architecture, runtime flow, and onboarding mental models; in teaching mode it turns that into one plain account a person actually understands."
disable-model-invocation: true
---

# How

Explore the codebase to answer "how does X work?" questions. Produce architectural explanations at the level of a senior engineer onboarding onto a subsystem, enough to build a working mental model, not so much that it reads like annotated source code.

Every spawn is a read-only general-purpose subagent: it may read, search, and run inspection commands, and it writes nothing. Pick the smallest model that reads code well for explorers, and a stronger one for the explainer that has to write the answer. If the harness rejects a model slug, fall back to its default and say which one you used.

## 1. Assess complexity

If the scope is ambiguous, state your interpretation and explore. The user can redirect.

- **Simple** (a single module, a small utility, a narrow question such as "how does function X work"): no explorers. Spawn one explainer that explores and explains in one pass, built from `references/explainer-prompt.md` without the explorer-findings section. Go to step 4.
- **Complex** (a subsystem spanning multiple files or services, a cross-cutting feature, a full architectural overview): go to step 2.

When in doubt, take the simple path.

## 2. Explore (complex only)

Decompose the question into 2 to 4 angles, each a distinct slice of the subsystem. Spawn all explorers in a single message, each with `references/explorer-prompt.md` and its angle filled in.

## 3. Synthesize (complex only)

Once all explorers have returned, spawn one explainer with `references/explainer-prompt.md` and every explorer's findings filled in.

## 4. Present

Present the explainer's output. Light edits for clarity or context from the conversation are fine. Do not substantially rewrite it.

## Teaching mode

When the ask is to understand, not to change ("teach me this", "help me really understand X", "explain this change"), the exploration above is step one and the explanation is the deliverable. Nothing gets edited.

1. Decide the few things they should walk away understanding, from why they are asking (about to change it, reviewing it, debugging it, new to it) and what they already know. Both are read from the conversation, not quizzed out of them. Skip what they plainly know; put the depth where the question is.
2. Run `why` alongside for the reasons and keep its confidence language intact, since its hedges are findings and not style. Keep it narrow by default, a scoped question plus git and one source, because the full sweep is slow.
3. Start with a plain definition: name the thing, say what it is in general terms the way a senior engineer would say it out loud, then tie it to the case in front of you. Build from there: how it works, the deeper reasons, the edge cases. For each part, explain the problem it solves and the mechanism. Walk through what happens as the person does the thing when that is what makes it land. Listing functions and constants is reference, not teaching. No framing labels ("the key insight", "at its core", "TL;DR", "here is the part worth slowing down on"). Give the smallest complete answer first, a sentence or two, then stop. Add layers when they ask.
4. Keep it a conversation. Offer to go deeper or move on and follow their lead. No quizzes, no pacing theater, no asking them to say it back, no announcing that a part is hard. When you would pause, stop and let them respond.
5. Show, don't only tell. Open the diff or the code when that lands it faster. For anything with three or more moving parts, draw a short series of diagrams where each one adds a single part, never one all-at-once diagram; a single all-at-once figure is reference, not teaching. Mermaid for flows and structure, an image for spatial ideas like layout and scroll position. A single simple point needs no figure.

Write it through `unslop`, in plain spoken English, tight rather than terse. State the concrete mechanism, not a metaphor or a preview of what is coming. Sentence case, one name per concept, no mirror sentences, no tidy closers. The words in these steps are directions to you, not labels to print.

**Reply:** the explanation itself, never a report about what you did.

## Output format

The explanation uses the sections defined in `references/explainer-prompt.md`, dropping any that do not apply: Overview, Key Concepts, How It Works, Where Things Live, Gotchas.
