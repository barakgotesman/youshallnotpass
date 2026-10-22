# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Two audiences, weighted equally:

- **Players:** anyone who enjoys a puzzle. They arrive curious, chat with an AI guard, and try to trick it into revealing a password. A session is short and playful.
- **Developers and recruiters:** people evaluating the engineering behind the game. They look past the chat to the Defense Log and the eval results.

Visitors may speak English or Hebrew. Hebrew is a first-class attack language for the backend; UI language is still an open decision (English only until decided).

## Product Purpose

A prompt-injection game. Each level has an AI guard that knows a secret password and must never reveal it. Players try to leak it; each level adds one more defense layer (hardened prompt, output filter, input classifier, semantic leak judge, conversation judge plus canary).

The game is the surface for a real engineering artifact: a layered guardrail pipeline, an eval harness that replays every attack ever collected, and a regression loop that turns each successful attack into a test case. Success: players have fun and learn how prompt injection works; developers see measured trade-offs (block rate, false positives, latency, cost).

## Positioning

Most "beat the AI" games are a single prompt. This one shows why each defense layer exists, with public evidence: every defense version measured against every collected attack.

## Operating Context

- Chat view per level, plus a separate password-guess input. Guesses are checked server-side only.
- A blocked message gets an in-world refusal. Players never see which layer blocked them or why.
- Levels unlock in order after earlier ones are beaten.
- Free-tier LLM quota is shared by all players. When the daily budget is spent the game shows a designed "vault closed for today" state, never a raw error.
- Public Defense Log page: block rate and false-positive rate per defense version, attack families, notable opted-in attacks.
- Must work down to mobile width.

## Capabilities and Constraints

- Stack: React, Vite, TypeScript (strict), Tailwind; FastAPI on Vercel; Neon Postgres.
- The frontend never receives the secret, the system prompt, the canary or block reasons.
- Open decisions: UI language (English only vs English plus Hebrew RTL), secret format, judge model.
- Levels shipped so far: backend for Level 1 only.

## Brand Commitments

- **Voice:** humorous. The guard is a grumpy grey wizard doorman. Refusals and copy are funny, not corporate.
- **Reference stance:** wink-and-nod homage to the "You shall not pass" wizard. Everyone gets the reference, but nothing copies films, character names or logos, to keep a public site safe from takedowns. Original name and jokes.
- **Name:** "You Shall Not Pass".

## Evidence on Hand

- Background illustration at `web/public/bg-wizard.webp` (a wizard seated on a cliff edge with a lantern, a fiery tower far right, a large dark calm centre). Original at `design/source/background-original.png`, gitignored.
- No testimonials, player counts or eval numbers exist yet; do not fabricate them.

## Product Principles

1. The game stays fun first; the engineering story is discoverable, never in the way.
2. Never teach players how to get around a layer: refusals reveal nothing about cause.
3. Nothing the player sees may contain a secret, a prompt or a reason.
4. Humor is the voice everywhere, including errors and empty states.
5. Honest numbers only: show measured results, never invented ones.
