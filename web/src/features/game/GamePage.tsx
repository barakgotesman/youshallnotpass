import { useState } from 'react'
import { Backdrop, type GlowState } from './Backdrop'
import { ChatInput } from './ChatInput'
import { ChatLog } from './ChatLog'
import { GUARD_NAME } from './copy'
import { GuessForm } from './GuessForm'
import { useGame } from './useGame'
import { VaultClosed } from './VaultClosed'

/** Level the screen plays. Level select arrives with Level 2. */
const CURRENT_LEVEL = 1

/**
 * The whole Level 1 screen: illustration, chat with the guard, and the guess.
 *
 * Chat is the main act, so it gets the full height and most of the width. On
 * wide screens a slim left column holds the title and the guess, leaving the
 * wizard in the illustration visible beneath it. On phones the chat takes the
 * whole screen and the guess folds away behind a header button.
 *
 * @returns The game page.
 */
export function GamePage() {
  const game = useGame(CURRENT_LEVEL)
  // Phones only: whether the guess form is unfolded. Wide screens always show it.
  const [guessOpen, setGuessOpen] = useState(false)

  // The lantern reflects the story: busy while the guard replies, ablaze when beaten.
  const glow: GlowState =
    game.guess.kind === 'correct' ? 'open' : game.guardIsReplying ? 'thinking' : 'idle'

  return (
    <div className="relative h-dvh overflow-hidden bg-night">
      <Backdrop glow={glow} />
      <div className="relative mx-auto flex h-full max-w-[1400px] flex-col gap-2 p-2 sm:p-4 lg:grid lg:grid-cols-[minmax(280px,360px)_minmax(0,1fr)] lg:gap-6 lg:p-6">
        <aside className="flex flex-col gap-3">
          <header className="flex items-center justify-between gap-3 px-1">
            <div>
              <h1 className="font-display text-xl font-bold sm:text-2xl lg:text-3xl">
                You Shall Not Pass
              </h1>
              <p className="text-sm text-ink-muted lg:text-base">Level 1 · The Gate</p>
            </div>
            <button
              type="button"
              onClick={() => setGuessOpen((open) => !open)}
              aria-expanded={guessOpen}
              aria-controls="guess-panel"
              className="rounded-xl border border-lantern px-3 py-1.5 font-bold text-lantern transition-transform duration-150 ease-out active:scale-[0.97] lg:hidden"
            >
              {guessOpen ? 'Close' : 'Know the word?'}
            </button>
          </header>
          <div id="guess-panel" className={`${guessOpen ? 'block' : 'hidden'} lg:block`}>
            <GuessForm status={game.guess} onGuess={game.submitGuess} />
          </div>
        </aside>
        <main className="flex min-h-0 flex-1 flex-col">
          {game.vaultClosed ? (
            <VaultClosed />
          ) : (
            <section
              aria-label="Conversation with the guard"
              className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-line bg-panel/95 shadow-2xl shadow-black/50"
            >
              <div className="flex items-center gap-3 border-b border-line px-4 py-2.5 sm:px-6">
                <span
                  aria-hidden="true"
                  className="flex size-10 items-center justify-center rounded-full border border-lantern/50 bg-panel-raised font-display text-xl text-lantern"
                >
                  G
                </span>
                <div className="leading-tight">
                  <p className="font-display text-lg">{GUARD_NAME}</p>
                  <p className="text-sm text-ink-muted">
                    {game.guardIsReplying ? 'typing…' : 'at the gate'}
                  </p>
                </div>
              </div>
              <ChatLog entries={game.entries} guardIsReplying={game.guardIsReplying} />
              <ChatInput
                disabled={game.guardIsReplying}
                error={game.chatError}
                onSend={game.sendMessage}
              />
            </section>
          )}
        </main>
      </div>
    </div>
  )
}
