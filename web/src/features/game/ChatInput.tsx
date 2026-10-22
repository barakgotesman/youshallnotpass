import { useState, type FormEvent } from 'react'

/** Server-side cap on one message; mirrored here so the box stops typing at the limit. */
const MAX_MESSAGE_CHARS = 1000

/** Props for {@link ChatInput}. */
type ChatInputProps = {
  /** True while a reply is pending; the box stays usable but sending is paused. */
  disabled: boolean
  /** Message for the player when the last send failed. */
  error: string | null
  /**
   * Called with the trimmed message.
   * @returns True if the message was accepted, so the box can clear.
   */
  onSend: (text: string) => Promise<boolean>
}

/**
 * The box where the player talks to the guard.
 *
 * Enter sends; a failed send keeps the text so nothing the player typed is lost.
 *
 * @param props - See {@link ChatInputProps}.
 * @returns The message form.
 */
export function ChatInput({ disabled, error, onSend }: ChatInputProps) {
  const [text, setText] = useState('')

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    if (await onSend(trimmed)) setText('')
  }

  return (
    <form onSubmit={handleSubmit} className="border-t border-line p-3">
      {error && (
        <p role="alert" className="mb-2 text-sm text-danger">
          {error}
        </p>
      )}
      <div className="flex gap-2">
        <label htmlFor="chat-message" className="sr-only">
          Your message to the guard
        </label>
        <input
          id="chat-message"
          value={text}
          onChange={(event) => setText(event.target.value)}
          maxLength={MAX_MESSAGE_CHARS}
          autoComplete="off"
          placeholder="Try your luck…"
          className="min-w-0 flex-1 rounded-xl border border-line bg-night px-4 py-2 text-ink placeholder:text-ink-muted"
        />
        <button
          type="submit"
          disabled={disabled || !text.trim()}
          className="rounded-xl bg-ember px-5 py-2 font-bold text-night transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Send
        </button>
      </div>
    </form>
  )
}
