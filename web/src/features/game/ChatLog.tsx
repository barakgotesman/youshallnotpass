import { useEffect, useRef } from 'react'
import { GUARD_GREETING, GUARD_NAME } from './copy'
import type { ChatEntry } from './messages'

/** Props for {@link ChatLog}. */
type ChatLogProps = {
  /** Messages to show, oldest first. */
  entries: ChatEntry[]
  /** True while the guard is composing a reply. */
  guardIsReplying: boolean
}

/** Props for {@link Bubble}. */
type BubbleProps = {
  entry: ChatEntry
}

/**
 * One message. Guard messages carry his name; blocked ones thump.
 *
 * @param props - See {@link BubbleProps}.
 * @returns A message bubble.
 */
function Bubble({ entry }: BubbleProps) {
  const fromPlayer = entry.role === 'user'
  // A blocked reply is an in-world refusal; it gets its own look so the
  // player feels the wall without learning what built it.
  const refused = !fromPlayer && entry.excluded

  return (
    <li className={`message-in flex flex-col ${fromPlayer ? 'items-end' : 'items-start'}`}>
      {!fromPlayer && <span className="mb-1 font-display text-sm text-lantern">{GUARD_NAME}</span>}
      <p
        className={[
          'max-w-[85%] whitespace-pre-wrap break-words rounded-2xl px-4 py-2 leading-snug',
          fromPlayer ? 'bg-ember-deep text-ink' : 'bg-panel-raised text-ink',
          refused ? 'staff-thump italic text-danger' : '',
        ].join(' ')}
      >
        {entry.content}
      </p>
    </li>
  )
}

/**
 * The scrolling conversation, with the guard's greeting always on top.
 *
 * Marked as a live log so screen readers announce new replies.
 *
 * @param props - See {@link ChatLogProps}.
 * @returns The message list.
 */
export function ChatLog({ entries, guardIsReplying }: ChatLogProps) {
  const endRef = useRef<HTMLDivElement>(null)

  // Keep the newest message in view as the conversation grows.
  useEffect(() => {
    endRef.current?.scrollIntoView({ block: 'end' })
  }, [entries.length, guardIsReplying])

  return (
    <div role="log" aria-live="polite" className="min-h-0 flex-1 overflow-y-auto px-4 py-4">
      <ul className="flex flex-col gap-4">
        <li className="flex flex-col items-start">
          <span className="mb-1 font-display text-sm text-lantern">{GUARD_NAME}</span>
          <p className="max-w-[85%] rounded-2xl bg-panel-raised px-4 py-2 leading-snug">
            {GUARD_GREETING}
          </p>
        </li>
        {entries.map((entry) => (
          <Bubble key={entry.id} entry={entry} />
        ))}
        {guardIsReplying && (
          <li className="text-sm italic text-ink-muted">
            {GUARD_NAME} strokes his beard and considers you…
          </li>
        )}
      </ul>
      <div ref={endRef} />
    </div>
  )
}
