import { useState, type FormEvent } from 'react'
import { NEXT_LEVEL_SOON } from './copy'
import type { GuessStatus } from './useGame'

/** Props for {@link GuessForm}. */
type GuessFormProps = {
  /** Result of the latest guess. */
  status: GuessStatus
  /**
   * Called with the trimmed guess.
   * @returns A promise that settles when the server has answered.
   */
  onGuess: (text: string) => Promise<void>
}

/**
 * Where the player speaks the password they think they extracted.
 *
 * Kept visually apart from the chat on purpose: chatting is the attack,
 * guessing is the finish, and players must always be able to find it.
 *
 * @param props - See {@link GuessFormProps}.
 * @returns The guess form, or the cleared state once the gate is open.
 */
export function GuessForm({ status, onGuess }: GuessFormProps) {
  const [text, setText] = useState('')

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const trimmed = text.trim()
    if (!trimmed || status.kind === 'checking') return
    await onGuess(trimmed)
  }

  if (status.kind === 'correct') {
    return (
      <div role="status" className="rounded-2xl border border-lantern bg-panel p-4 text-center">
        <p className="font-display text-xl text-lantern">{status.message}</p>
        <p className="mt-1 text-ink-muted">{NEXT_LEVEL_SOON}</p>
      </div>
    )
  }

  const feedback = status.kind === 'wrong' || status.kind === 'error' ? status.message : null

  return (
    <form onSubmit={handleSubmit} className="rounded-2xl border border-line bg-panel/95 p-3">
      <label htmlFor="password-guess" className="mb-2 block font-display text-lg">
        Think you know it? Speak the word.
      </label>
      <div className="flex gap-2">
        <input
          id="password-guess"
          value={text}
          onChange={(event) => setText(event.target.value)}
          maxLength={100}
          autoComplete="off"
          spellCheck={false}
          placeholder="The password, if you dare"
          className="min-w-0 flex-1 rounded-xl border border-line bg-night px-4 py-2 text-ink placeholder:text-ink-muted"
        />
        <button
          type="submit"
          disabled={status.kind === 'checking' || !text.trim()}
          className="rounded-xl border border-lantern px-5 py-2 font-bold text-lantern transition-colors hover:bg-lantern hover:text-night disabled:cursor-not-allowed disabled:opacity-40"
        >
          Speak
        </button>
      </div>
      {feedback && (
        <p role="alert" className="mt-2 text-danger">
          {feedback}
        </p>
      )}
    </form>
  )
}
