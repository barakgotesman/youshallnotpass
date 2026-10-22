/** Body of `POST /api/guess`. Mirrors `GuessRequest` in `api/routes/guess.py`. */
export type GuessRequest = {
  /** Level the guess is for. */
  level: number
  /** The password the player thinks they extracted (1 to 100 characters). */
  guess: string
}

/** Body returned by `POST /api/guess`. Mirrors `GuessResponse` in `api/routes/guess.py`. */
export type GuessResponse = {
  /** Whether the guess matched. Nothing else is ever revealed. */
  correct: boolean
}
