/** Who wrote a chat message, as the API understands it. */
export type ChatRole = 'user' | 'assistant'

/**
 * One message in the conversation sent to `POST /api/chat`.
 *
 * Mirrors `ChatMessage` in `api/routes/chat.py`.
 */
export type ApiChatMessage = {
  role: ChatRole
  /** 1 to 1000 characters; the server rejects anything longer. */
  content: string
}

/** Body of `POST /api/chat`. Mirrors `ChatRequest` in `api/routes/chat.py`. */
export type ChatRequest = {
  /** Level being played. */
  level: number
  /** Conversation so far, ending with the player's new message. */
  messages: ApiChatMessage[]
}

/**
 * Body returned by `POST /api/chat`.
 *
 * Mirrors `ChatResponse` in `api/routes/chat.py`. It deliberately has no block
 * reason: the client must never learn which layer stopped a message.
 */
export type ChatResponse = {
  /** The guard's reply, or an in-world refusal. */
  reply: string
  /** True if the pipeline stopped the turn instead of answering normally. */
  blocked: boolean
}
