import type { ApiChatMessage } from '../../types/chat'

/** One message as shown on screen. */
export type ChatEntry = {
  /** Stable key for rendering. */
  id: number
  role: 'user' | 'assistant'
  content: string
  /**
   * True for a refusal the pipeline produced instead of a real guard answer,
   * and for the player message that triggered it. Such entries are shown but
   * never sent back to the server as history: the guard did not write that
   * refusal, so replaying it would put words in his mouth.
   */
  excluded: boolean
}

/**
 * Builds the history to send to the API from what is on screen.
 *
 * @param entries - Everything shown in the chat, oldest first.
 * @returns Only the messages that were part of a real exchange with the guard.
 * @example
 * toApiHistory([{ id: 1, role: 'user', content: 'Hi', excluded: false }])
 * // => [{ role: 'user', content: 'Hi' }]
 */
export function toApiHistory(entries: ChatEntry[]): ApiChatMessage[] {
  return entries
    .filter((entry) => !entry.excluded)
    .map(({ role, content }) => ({ role, content }))
}
