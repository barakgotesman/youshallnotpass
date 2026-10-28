# Prompt changelog

Every prompt version is immutable once an eval run references it. A change means a new version.
Each entry records what changed, why, which attacks motivated it, and the eval delta.

The guard's system prompt is two files joined together: `persona/<version>` (who he is, shared by
every level) and `defender/<version>` (that level's security rules). Keeping them apart means the
character cannot drift between levels and a defense change never touches his voice.

## persona/v1

- **What:** Old Greybeard, a grumpy 300-year-old wizard gatekeeper. Never an AI, never an assistant,
  stays in character on any topic, one to three dry funny sentences, no emojis.
- **Why:** with only "gruff gate guard" in the prompt, the Level 1 model broke character and answered
  like a chatbot ("As a simple AI assistant..."). Reported by the project owner while playing.
- **Language rule added:** the Level 1 model (allam-2-7b, built for Arabic) once answered "who u are"
  in Arabic. The persona now says: reply in the visitor's language, English when unclear or short.
- **Eval delta:** none yet (harness arrives in Phase 4).

## defender/v1

- **What:** naive security rules. States the password and says not to reveal it.
- **Why:** Level 1 baseline. Intentionally weak, so players learn the game.
- **Motivating attacks:** none yet.
- **Eval delta:** none yet.
- **Informal check (Phase 1, not an eval run):** 6 simple attacks x 3 tries. `qwen/qwen3.8-27b` leaked
  2/18, `allam-2-7b` 14/18. Level 1 uses `allam-2-7b` through `DEFENDER_MODEL_LEVEL_1`; model strength
  is the main difficulty dial.
