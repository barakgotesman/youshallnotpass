/** Body returned by `GET /api/progress`. Mirrors `ProgressResponse` in `api/routes/progress.py`. */
export type ProgressResponse = {
  /** Ids of the levels this player has beaten. */
  cleared_levels: number[]
}

/**
 * Why the API refused a request with HTTP 429, from the `detail.code` field.
 *
 * `slow_down` means this player is going too fast; `vault_closed` means the
 * shared daily budget is spent (or the limiter is down), for everyone.
 */
export type LimitCode = 'slow_down' | 'vault_closed'
