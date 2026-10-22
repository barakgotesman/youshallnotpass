/**
 * Response of `GET /api/health`.
 *
 * Mirrors the `HealthResponse` Pydantic model in `api/routes/health.py`.
 * Keep the two in sync: this file is the frontend's only view of the contract.
 */
export type HealthResponse = {
  /** Always "ok" when the API process is up. */
  status: 'ok'
  /** Whether a database URL is configured (not whether it is reachable). */
  database_configured: boolean
}
