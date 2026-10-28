import type { ApiChatMessage, ChatRequest, ChatResponse } from '../types/chat'
import type { GuessRequest, GuessResponse } from '../types/guess'
import type { LimitCode, ProgressResponse } from '../types/progress'

/**
 * Error for any non-2xx answer or network failure from the API.
 *
 * The UI shows an in-world message for every case, so the status is kept only
 * for deciding what to show later (for example "vault closed" on 429).
 */
export class ApiError extends Error {
  /** HTTP status, or 0 when the request never reached the server. */
  readonly status: number
  /** Set on a 429: why the request was refused. Null for every other failure. */
  readonly limit: LimitCode | null
  /** Set on a 429: seconds until the player may try again. */
  readonly retryAfter: number

  /**
   * @param status - HTTP status, or 0 for a network failure.
   * @param message - Internal description; never shown to the player.
   * @param limit - Rate-limit code from a 429 body, if any.
   * @param retryAfter - Seconds to wait, from a 429 body.
   */
  constructor(status: number, message: string, limit: LimitCode | null = null, retryAfter = 0) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.limit = limit
    this.retryAfter = retryAfter
  }
}

/**
 * POSTs JSON to the API and parses the JSON answer.
 *
 * Uses relative URLs so the same code works behind the Vite dev proxy and on
 * Vercel, where the frontend and API share one origin.
 *
 * @param path - Path under the API, for example `/api/chat`.
 * @param body - Request body, serialized as JSON.
 * @returns The parsed response body.
 * @throws ApiError on a network failure or a non-2xx status.
 */
async function postJson<Request, Response>(path: string, body: Request): Promise<Response> {
  let response: globalThis.Response
  try {
    response = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
  } catch {
    throw new ApiError(0, 'Network request failed')
  }
  return readJson<Response>(path, response)
}

/**
 * Reads a JSON answer, turning any non-2xx status into an ApiError.
 *
 * A 429 body carries `detail.code` and `detail.retry_after`; they are lifted
 * onto the error so the UI can pick the right designed screen.
 *
 * @param path - Path that was requested, for the error message.
 * @param response - The fetch response.
 * @returns The parsed body.
 * @throws ApiError on a non-2xx status.
 */
async function readJson<Response>(path: string, response: globalThis.Response): Promise<Response> {
  if (response.ok) return (await response.json()) as Response
  let limit: LimitCode | null = null
  let retryAfter = 0
  if (response.status === 429) {
    try {
      const body = (await response.json()) as { detail?: { code?: LimitCode; retry_after?: number } }
      limit = body.detail?.code ?? null
      retryAfter = body.detail?.retry_after ?? 0
    } catch {
      // An unreadable 429 body still means "too many requests"; treat it as slow_down.
      limit = 'slow_down'
    }
  }
  throw new ApiError(response.status, `${path} answered ${response.status}`, limit, retryAfter)
}

/**
 * Sends the conversation to the guard of a level.
 *
 * @param level - Level being played.
 * @param messages - Conversation so far, ending with the player's new message.
 * @returns The guard's reply and whether the turn was blocked.
 * @throws ApiError if the request fails.
 * @example
 * const { reply } = await postChat(1, [{ role: 'user', content: 'Hello' }])
 */
export function postChat(level: number, messages: ApiChatMessage[]): Promise<ChatResponse> {
  return postJson<ChatRequest, ChatResponse>('/api/chat', { level, messages })
}

/**
 * Submits a password guess. The check happens only on the server.
 *
 * @param level - Level the guess is for.
 * @param guess - The password the player typed.
 * @returns Whether the guess was correct.
 * @throws ApiError if the request fails.
 */
export function postGuess(level: number, guess: string): Promise<GuessResponse> {
  return postJson<GuessRequest, GuessResponse>('/api/guess', { level, guess })
}

/**
 * Loads which levels this player has already beaten.
 *
 * @returns The cleared level ids.
 * @throws ApiError if the request fails.
 */
export async function getProgress(): Promise<ProgressResponse> {
  let response: globalThis.Response
  try {
    response = await fetch('/api/progress')
  } catch {
    throw new ApiError(0, 'Network request failed')
  }
  return readJson<ProgressResponse>('/api/progress', response)
}
