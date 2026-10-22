# You Shall Not Pass

A prompt-injection game with a layered guardrail pipeline and an eval harness.
See `CLAUDE.md` for the design. Full README comes in the final phase.

## Local development

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn api.index:app --reload --env-file .env   # API on :8000

cd web && npm install && npm run dev  # frontend on :5173, proxies /api to :8000
```
