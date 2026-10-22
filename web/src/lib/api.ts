import type { ApiChatMessage, ChatRequest, ChatResponse } from '../types/chat'
import type { GuessRequest, GuessResponse } from '../types/guess'

/**
 * Error for any non-2xx answer or network failure from the API.
 *
 * The UI shows an in-world message for every case, so the status is kept only
 * for deciding what to show later (for example "vault closed" on 429).
 */
export class ApiError extends Error {
  /** HTTP status, or 0 when the request never reached the server. */
  readonly status: number

  /**
   * @param status - HTTP status, or 0 for a network failure.
   * @param message - Internal description; never shown to the player.
   */
  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
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
  if (!response.ok) {
    throw new ApiError(response.status, `${path} answered ${response.status}`)
  }
  return (await response.json()) as Response
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
