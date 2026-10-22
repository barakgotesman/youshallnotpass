import { GamePage } from './features/game/GamePage'

/**
 * Application root. Only the game exists so far; routing arrives with the
 * Defense Log page.
 *
 * @returns The app.
 */
export default function App() {
  return <GamePage />
}
