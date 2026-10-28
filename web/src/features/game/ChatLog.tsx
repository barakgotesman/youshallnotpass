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

/** Props for {@link Avatar}. */
type AvatarProps = {
  /** Hide the portrait but keep its space, so grouped bubbles stay aligned. */
  hidden?: boolean
}

/**
 * The guard's round portrait, shown beside his messages like a contact photo.
 *
 * @param props - See {@link AvatarProps}.
 * @returns A small circular badge.
 */
function Avatar({ hidden = false }: AvatarProps) {
  return (
    <span
      aria-hidden="true"
      className={[
        'flex size-8 shrink-0 items-center justify-center rounded-full border border-lantern/50 bg-panel-raised font-display text-base text-lantern',
        hidden ? 'invisible' : '',
      ].join(' ')}
    >
      G
    </span>
  )
}

/**
 * The three bobbing dots a person sees while the other side is typing.
 *
 * @returns A guard-side bubble containing the typing indicator.
 */
function TypingBubble() {
  return (
    <li className="message-in flex items-end gap-2">
      <Avatar />
      <p
        role="status"
        aria-label={`${GUARD_NAME} is typing`}
        className="flex items-center gap-1 rounded-2xl rounded-bl-md bg-panel-raised px-4 py-3.5"
      >
        <span className="typing-dot size-2 rounded-full bg-ink-muted" />
        <span className="typing-dot size-2 rounded-full bg-ink-muted" />
        <span className="typing-dot size-2 rounded-full bg-ink-muted" />
      </p>
    </li>
  )
}

/**
 * Formats a timestamp the way chat apps do: hours and minutes only.
 *
 * @param epochMs - Time in epoch milliseconds.
 * @returns A short local time such as "14:05".
 */
function formatTime(epochMs: number): string {
  return new Date(epochMs).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

/** Props for {@link Message}. */
type MessageProps = {
  entry: ChatEntry
  /** True when the previous message has the same sender, so the portrait and spacing collapse. */
  continuesGroup: boolean
  /** True when the next message has a different sender (or none), so the time shows here. */
  endsGroup: boolean
}

/**
 * One message, laid out like a messenger: portrait and tail on the group's edge,
 * time under the last bubble of a run. Blocked replies thump.
 *
 * @param props - See {@link MessageProps}.
 * @returns A message row.
 */
function Message({ entry, continuesGroup, endsGroup }: MessageProps) {
  const fromPlayer = entry.role === 'user'
  // A blocked reply is an in-world refusal; it gets its own look so the
  // player feels the wall without learning what built it.
  const refused = !fromPlayer && entry.excluded
  // The sharp "tail" corner only appears on the last bubble of a run.
  const tail = endsGroup ? (fromPlayer ? 'rounded-br-md' : 'rounded-bl-md') : ''

  return (
    <li
      className={[
        'message-in flex flex-col',
        fromPlayer ? 'items-end' : 'items-start',
        // Tight spacing inside a run, looser between speakers.
        continuesGroup ? '-mt-3' : '',
      ].join(' ')}
    >
      <div className={`flex max-w-[85%] lg:max-w-[70%] items-end gap-2 ${fromPlayer ? 'flex-row-reverse' : ''}`}>
        {!fromPlayer && <Avatar hidden={!endsGroup} />}
        <p
          className={[
            'whitespace-pre-wrap break-words rounded-2xl px-4 py-2 leading-snug',
            tail,
            fromPlayer ? 'bg-ember-deep text-ink' : 'bg-panel-raised text-ink',
            refused ? 'staff-thump italic text-danger' : '',
          ].join(' ')}
        >
          {entry.content}
        </p>
      </div>
      {endsGroup && (
        <time
          dateTime={new Date(entry.sentAt).toISOString()}
          className={`mt-1 text-xs text-ink-muted ${fromPlayer ? '' : 'ml-10'}`}
        >
          {formatTime(entry.sentAt)}
        </time>
      )}
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
    <div role="log" aria-live="polite" className="min-h-0 flex-1 overflow-y-auto px-4 py-5 sm:px-6">
      <ul className="flex flex-col gap-4">
        <li className="flex items-end gap-2">
          <Avatar />
          <p className="max-w-[85%] lg:max-w-[70%] rounded-2xl rounded-bl-md bg-panel-raised px-4 py-2 leading-snug">
            {GUARD_GREETING}
          </p>
        </li>
        {entries.map((entry, index) => (
          <Message
            key={entry.id}
            entry={entry}
            // The greeting is the guard's, so a guard reply right after it never happens
            // before a player message; only entry-to-entry grouping matters here.
            continuesGroup={index > 0 && entries[index - 1].role === entry.role}
            endsGroup={entries[index + 1]?.role !== entry.role}
          />
        ))}
        {guardIsReplying && <TypingBubble />}
      </ul>
      <div ref={endRef} />
    </div>
  )
}
