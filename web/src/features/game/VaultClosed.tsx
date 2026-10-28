import { VAULT_CLOSED_BODY, VAULT_CLOSED_TITLE } from './copy'

/**
 * The designed "out of quota" state, shown instead of the chat when the shared
 * daily budget is spent. It replaces the conversation entirely so the player
 * never meets a raw error and never types into a box that cannot answer.
 *
 * @returns A centered closed-gate message.
 */
export function VaultClosed() {
  return (
    <section
      role="status"
      className="flex min-h-0 flex-1 flex-col items-center justify-center gap-3 rounded-2xl border border-line bg-panel/95 p-8 text-center shadow-2xl shadow-black/50"
    >
      <span
        aria-hidden="true"
        className="flex size-14 items-center justify-center rounded-full border border-lantern/50 bg-panel-raised font-display text-2xl text-lantern"
      >
        G
      </span>
      <h2 className="font-display text-2xl text-lantern sm:text-3xl">{VAULT_CLOSED_TITLE}</h2>
      <p className="max-w-md text-ink-muted">{VAULT_CLOSED_BODY}</p>
    </section>
  )
}
