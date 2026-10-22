import { useEffect, useState } from 'react'
import { getHealth } from './lib/api'

/** Connection state of the hello-world API check. */
type Status = 'loading' | 'ok' | 'error'

/**
 * Phase 0 placeholder screen. It only proves the browser can reach the API.
 * The real game UI is designed in Phase 1 with the design skills.
 *
 * @returns The placeholder page.
 */
export default function App() {
  const [status, setStatus] = useState<Status>('loading')

  useEffect(() => {
    // One-shot check on mount; failure is shown, not thrown, so the page never crashes.
    getHealth()
      .then(() => setStatus('ok'))
      .catch(() => setStatus('error'))
  }, [])

  return (
    <main className="p-6">
      <h1 className="text-2xl font-bold">You Shall Not Pass</h1>
      <p>API status: {status}</p>
    </main>
  )
}
