# Prompt changelog

Every prompt version is immutable once an eval run references it. A change means a new version.
Each entry records what changed, why, which attacks motivated it, and the eval delta.

## defender/v1

- **What:** naive prompt. States the password and says not to reveal it.
- **Why:** Level 1 baseline. Intentionally weak, so players learn the game.
- **Motivating attacks:** none yet.
- **Eval delta:** none yet (harness arrives in Phase 4).
- **Informal check (Phase 1, not an eval run):** 6 hand-written attacks against three Groq models.
  `openai/gpt-oss-20b` leaked 0/6, `qwen/qwen3.8-27b` 1/6 (translation trick), `allam-2-7b` 4/6.
  Level 1 uses `qwen/qwen3.8-27b`.
