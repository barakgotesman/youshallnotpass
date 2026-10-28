/**
 * All player-facing wording in one place, in the guard's voice.
 *
 * Kept together so the humor stays consistent and so wording can change
 * without touching logic. Nothing here may hint at which defense layer acted.
 */

/** Name shown for the guard. An original character: a nod to the genre, not a copy. */
export const GUARD_NAME = 'Old Greybeard'

/** Shown above the chat before the player says anything. Never sent to the API. */
export const GUARD_GREETING =
  'Halt. This gate is closed, locked, and my fault if it opens. State your business, or go away. Preferably go away.'

/** Shown when a chat request fails (network, server, or anything else). */
export const CHAT_FAILED = 'A raven carrying your message got lost on the way. Try again.'

/**
 * Shown when this player sends messages too fast.
 *
 * @param seconds - Seconds until they may try again.
 * @returns A line from the guard.
 */
export function slowDownLine(seconds: number): string {
  const wait = seconds >= 90 ? `${Math.ceil(seconds / 60)} minutes` : `${Math.max(seconds, 1)} seconds`
  return `The guard raises a hand. "Slow down, friend. Come back in ${wait}."`
}

/** Headline of the screen shown when the shared daily budget is spent. */
export const VAULT_CLOSED_TITLE = 'The vault is closed for today'

/** Body of the vault-closed screen. */
export const VAULT_CLOSED_BODY =
  'Old Greybeard has gone home to rest his beard. The gate opens again tomorrow, and so does the challenge.'

/** Shown when a guess request fails. */
export const GUESS_FAILED = 'The gate did not hear you. Try speaking again.'

/** Shown after a correct guess. */
export const GUESS_CORRECT =
  'The gate creaks open. Well. That was deeply irritating. Level 1 cleared.'

/** Shown under the cleared state, because Level 2 does not exist yet. */
export const NEXT_LEVEL_SOON = 'Level 2 is still being forged. Come back soon.'

/** Rebukes for wrong guesses, cycled so repeated misses stay funny. */
const WRONG_GUESS_LINES = [
  'Wrong. The gate stays closed and I stay smug.',
  'Not even close. Have you tried a different word?',
  'No. And I am enjoying this more than I should.',
  'That is not the word. I will wait.',
]

/**
 * Picks a rebuke for a wrong guess.
 *
 * @param attempt - How many wrong guesses the player has made, starting at 1.
 * @returns A line from the guard.
 */
export function wrongGuessLine(attempt: number): string {
  return WRONG_GUESS_LINES[(attempt - 1) % WRONG_GUESS_LINES.length]
}
