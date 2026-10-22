---
version: 1
slug: "web-src-features-game-gamepage-tsx"
primary_target: "web/src/features/game/GamePage.tsx"
related_targets: []
---

# Game screen (Level 1)

Mode: Operate. A player chats with the guard and separately speaks a password guess.

## Audience and task
Players trying to trick the guard; developers glancing at craft. Tasks: send messages, read replies, submit a guess. Constraints: no secrets, prompts or block reasons ever shown; mobile to desktop; English only for now.

## Decisions
- First screen is the chat itself (no title screen). Level select arrives with Level 2.
- Pinned by the user: funny wink-and-nod wizard doorman; their illustration `web/public/bg-wizard.webp` is the background.
- Unresolved: Hebrew/RTL UI; Defense Log page design; vault-closed state.

## Direction contract

THESIS: A working chat screen that sits inside the illustration, a lantern-lit cliff above a fiery fortress, rather than on a plain app background. It refuses the generic chat-bubble-on-grey layout.

OWN-WORLD: Night-blue ground sampled from the art, ember orange (the tower glow) for actions and danger, lantern gold for focus and success, cool blue-grey text tints. Almendra for the wizard's voice and wordmark, Alegreya Sans for all reading. Standard controls throughout.

STORY: The visitor understands in seconds they face a grumpy gatekeeper, can type to him at once, and can find the separate "Speak the word" control. Refusals and errors are funny and reveal nothing about cause.

FIRST VIEWPORT: Full-bleed illustration, wizard bottom-left. Centered panel (max 680px): wordmark and level label above; guard's greeting and chat inside; message input at the panel foot; a distinct guess form under the panel. Mobile: panel fills the width, background shifts to the fiery tower.

SIGNATURE MOVE: the lantern glow behind the wizard pulses while the guard is replying and floods gold when the gate opens.

FORM: Operate chat screen, standard web controls. seed: none (pinned brief).

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
