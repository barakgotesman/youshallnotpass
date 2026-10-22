import type { HealthResponse } from '../types/health'

/**
 * Fetches the API health status.
 *
 * Uses a relative URL so the same code works behind the Vite dev proxy and on
 * Vercel, where the frontend and API share one origin.
 *
 * @returns The parsed health response.
 * @throws Error if the server answers with a non-2xx status.
 * @example
 * const health = await getHealth()
 */
export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch('/api/health')
  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`)
  }
  return (await response.json()) as HealthResponse
}
