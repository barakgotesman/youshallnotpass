import { useCallback, useEffect, useState } from 'react'
import { ApiError, getProgress, postChat, postGuess } from '../../lib/api'
import { CHAT_FAILED, GUESS_CORRECT, GUESS_FAILED, slowDownLine, wrongGuessLine } from './copy'
import { toApiHistory, type ChatEntry } from './messages'

/** Outcome of the player's latest password guess. */
export type GuessStatus =
  | { kind: 'idle' }
  | { kind: 'checking' }
  | { kind: 'wrong'; message: string }
  | { kind: 'error'; message: string }
  | { kind: 'correct'; message: string }

/** Everything the game screen needs, and the actions it can take. */
export type GameState = {
  /** Chat shown on screen, oldest first. */
  entries: ChatEntry[]
  /** True while waiting for the guard's reply. */
  guardIsReplying: boolean
  /** Set when the last chat request failed; cleared on the next send. */
  chatError: string | null
  /** Result of the latest guess. */
  guess: GuessStatus
  /** True once the server says the shared daily budget is spent; the game shows the closed screen. */
  vaultClosed: boolean
  /**
   * Sends a player message to the guard.
   * @param text - The message, already trimmed and non-empty.
   * @returns True if the request was accepted, so the input can be cleared.
   */
  sendMessage: (text: string) => Promise<boolean>
  /**
   * Submits a password guess.
   * @param text - The guess, already trimmed and non-empty.
   */
  submitGuess: (text: string) => Promise<void>
}

/**
 * Holds the state of one level's game: the chat and the guess.
 *
 * The client keeps the conversation and sends it with each message. That is
 * safe because a player can only forge their own chat; the system prompt and
 * the secret stay on the server.
 *
 * @param level - Level being played.
 * @returns State and actions for the game screen.
 * @example
 * const { entries, sendMessage } = useGame(1)
 */
export function useGame(level: number): GameState {
  const [entries, setEntries] = useState<ChatEntry[]>([])
  const [guardIsReplying, setGuardIsReplying] = useState(false)
  const [chatError, setChatError] = useState<string | null>(null)
  const [guess, setGuess] = useState<GuessStatus>({ kind: 'idle' })
  const [wrongCount, setWrongCount] = useState(0)
  const [vaultClosed, setVaultClosed] = useState(false)

  // A returning player who already beat this level sees the cleared state, not a fresh gate.
  // A failed lookup is ignored: the game is fully playable without it.
  useEffect(() => {
    getProgress()
      .then(({ cleared_levels }) => {
        if (cleared_levels.includes(level)) setGuess({ kind: 'correct', message: GUESS_CORRECT })
      })
      .catch(() => undefined)
  }, [level])

  /**
   * Turns a failed request into the right in-world reaction.
   *
   * @param error - What the API call threw.
   * @param fallback - Message for failures that are not rate limits.
   * @returns The line to show the player, or null if the vault-closed screen takes over.
   */
  const explainFailure = useCallback((error: unknown, fallback: string): string | null => {
    if (error instanceof ApiError && error.limit === 'vault_closed') {
      setVaultClosed(true)
      return null
    }
    if (error instanceof ApiError && error.limit === 'slow_down') return slowDownLine(error.retryAfter)
    return fallback
  }, [])

  const sendMessage = useCallback(
    async (text: string): Promise<boolean> => {
      if (guardIsReplying) return false
      setChatError(null)
      const now = Date.now()
      const userEntry: ChatEntry = { id: now, role: 'user', sentAt: now, content: text, excluded: false }
      setEntries((current) => [...current, userEntry])
      setGuardIsReplying(true)
      try {
        const history = [...toApiHistory(entries), { role: 'user' as const, content: text }]
        const { reply, blocked } = await postChat(level, history)
        setEntries((current) => [
          // A blocked turn is shown but excluded from future history.
          ...current.map((entry) => (entry.id === userEntry.id ? { ...entry, excluded: blocked } : entry)),
          { id: userEntry.id + 1, role: 'assistant', sentAt: Date.now(), content: reply, excluded: blocked },
        ])
        return true
      } catch (error) {
        // Take the unanswered message back off the screen so the player can retry it.
        setEntries((current) => current.filter((entry) => entry.id !== userEntry.id))
        setChatError(explainFailure(error, CHAT_FAILED))
        return false
      } finally {
        setGuardIsReplying(false)
      }
    },
    [entries, explainFailure, guardIsReplying, level],
  )

  const submitGuess = useCallback(
    async (text: string): Promise<void> => {
      setGuess({ kind: 'checking' })
      try {
        const { correct } = await postGuess(level, text)
        if (correct) {
          setGuess({ kind: 'correct', message: GUESS_CORRECT })
          return
        }
        const attempt = wrongCount + 1
        setWrongCount(attempt)
        setGuess({ kind: 'wrong', message: wrongGuessLine(attempt) })
      } catch (error) {
        const message = explainFailure(error, GUESS_FAILED)
        setGuess(message === null ? { kind: 'idle' } : { kind: 'error', message })
      }
    },
    [explainFailure, level, wrongCount],
  )

  return { entries, guardIsReplying, chatError, guess, vaultClosed, sendMessage, submitGuess }
}
