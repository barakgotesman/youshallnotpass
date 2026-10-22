import { useCallback, useState } from 'react'
import { postChat, postGuess } from '../../lib/api'
import { CHAT_FAILED, GUESS_CORRECT, GUESS_FAILED, wrongGuessLine } from './copy'
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

  const sendMessage = useCallback(
    async (text: string): Promise<boolean> => {
      if (guardIsReplying) return false
      setChatError(null)
      const userEntry: ChatEntry = { id: Date.now(), role: 'user', content: text, excluded: false }
      setEntries((current) => [...current, userEntry])
      setGuardIsReplying(true)
      try {
        const history = [...toApiHistory(entries), { role: 'user' as const, content: text }]
        const { reply, blocked } = await postChat(level, history)
        setEntries((current) => [
          // A blocked turn is shown but excluded from future history.
          ...current.map((entry) => (entry.id === userEntry.id ? { ...entry, excluded: blocked } : entry)),
          { id: userEntry.id + 1, role: 'assistant', content: reply, excluded: blocked },
        ])
        return true
      } catch {
        // Take the unanswered message back off the screen so the player can retry it.
        setEntries((current) => current.filter((entry) => entry.id !== userEntry.id))
        setChatError(CHAT_FAILED)
        return false
      } finally {
        setGuardIsReplying(false)
      }
    },
    [entries, guardIsReplying, level],
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
      } catch {
        setGuess({ kind: 'error', message: GUESS_FAILED })
      }
    },
    [level, wrongCount],
  )

  return { entries, guardIsReplying, chatError, guess, sendMessage, submitGuess }
}
