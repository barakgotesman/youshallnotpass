import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react'

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
  const boxRef = useRef<HTMLTextAreaElement>(null)

  // Grow with the text up to a few lines, like a messenger composer.
  useEffect(() => {
    const box = boxRef.current
    if (!box) return
    box.style.height = 'auto'
    box.style.height = `${Math.min(box.scrollHeight, 128)}px`
  }, [text])

  // Hand focus back after the guard answers so the player can keep typing without clicking.
  useEffect(() => {
    if (!disabled) boxRef.current?.focus()
  }, [disabled])

  // Enter sends, Shift+Enter adds a line; the usual chat convention.
  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault()
      event.currentTarget.form?.requestSubmit()
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    if (await onSend(trimmed)) setText('')
  }

  return (
    <form onSubmit={handleSubmit} className="border-t border-line p-3 sm:px-6 sm:py-4">
      {error && (
        <p role="alert" className="mb-2 text-sm text-danger">
          {error}
        </p>
      )}
      <div className="flex items-end gap-2">
        <label htmlFor="chat-message" className="sr-only">
          Your message to the guard
        </label>
        <textarea
          ref={boxRef}
          id="chat-message"
          rows={1}
          value={text}
          onChange={(event) => setText(event.target.value)}
          onKeyDown={handleKeyDown}
          maxLength={MAX_MESSAGE_CHARS}
          autoComplete="off"
          placeholder="Message Old Greybeard…"
          className="min-w-0 flex-1 resize-none rounded-2xl border border-line bg-night px-4 py-2 leading-snug text-ink placeholder:text-ink-muted"
        />
        <button
          type="submit"
          disabled={disabled || !text.trim()}
          className="rounded-2xl bg-ember px-5 py-2 font-bold text-night transition-[opacity,transform] duration-150 ease-out hover:opacity-90 active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-40"
        >
          Send
        </button>
      </div>
    </form>
  )
}
