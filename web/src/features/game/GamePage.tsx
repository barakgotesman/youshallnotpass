import { Backdrop, type GlowState } from './Backdrop'
import { ChatInput } from './ChatInput'
import { ChatLog } from './ChatLog'
import { GuessForm } from './GuessForm'
import { useGame } from './useGame'

/** Level the screen plays. Level select arrives with Level 2. */
const CURRENT_LEVEL = 1

/**
 * The whole Level 1 screen: illustration, chat with the guard, and the guess.
 *
 * @returns The game page.
 */
export function GamePage() {
  const game = useGame(CURRENT_LEVEL)

  // The lantern reflects the story: busy while the guard replies, ablaze when beaten.
  const glow: GlowState =
    game.guess.kind === 'correct' ? 'open' : game.guardIsReplying ? 'thinking' : 'idle'

  return (
    <div className="relative h-dvh overflow-hidden bg-night">
      <Backdrop glow={glow} />
      <div className="relative mx-auto flex h-full max-w-[680px] flex-col gap-3 px-3 py-3 sm:px-4 sm:py-5">
        <header className="flex items-baseline justify-between px-1">
          <h1 className="font-display text-2xl font-bold sm:text-3xl">You Shall Not Pass</h1>
          <p className="text-ink-muted">Level 1 · The Gate</p>
        </header>
        <main className="flex min-h-0 flex-1 flex-col gap-3">
          <section
            aria-label="Conversation with the guard"
            className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-line bg-panel/90"
          >
            <ChatLog entries={game.entries} guardIsReplying={game.guardIsReplying} />
            <ChatInput
              disabled={game.guardIsReplying}
              error={game.chatError}
              onSend={game.sendMessage}
            />
          </section>
          <GuessForm status={game.guess} onGuess={game.submitGuess} />
        </main>
      </div>
    </div>
  )
}
