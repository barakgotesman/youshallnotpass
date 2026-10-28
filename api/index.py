"""FastAPI application entrypoint.

Vercel looks for an ASGI object named ``app`` in a supported entrypoint file;
``api/index.py`` is one of them, so no extra Vercel config is needed to find it.
"""

from fastapi import FastAPI

from api.routes import chat, guess, health, progress

# All routes live under /api so that, on Vercel, the same domain can serve the
# static frontend at "/" and this app at "/api/*" without any CORS setup.
app = FastAPI(title="You Shall Not Pass", docs_url=None, redoc_url=None)

app.include_router(health.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(guess.router, prefix="/api")
app.include_router(progress.router, prefix="/api")
