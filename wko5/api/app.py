"""FastAPI application factory."""

import secrets
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from wko5.api.auth import set_token
from wko5.api.routes import router

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


def create_app(token: str = None, allowed_origins: list = None):
    if token is None:
        token = secrets.token_urlsafe(32)
    set_token(token)

    app = FastAPI(title="WKO5 Analyzer API")

    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_origins=allowed_origins or [],
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization"],
    )

    # API routes first so they take priority
    app.include_router(router)

    # Static file serving for the frontend SPA
    if FRONTEND_DIR.is_dir():
        app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
        app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
        app.mount("/lib", StaticFiles(directory=FRONTEND_DIR / "lib"), name="lib")

        # Catch-all: serve index.html for any non-API path (SPA routing)
        @app.get("/{full_path:path}", response_class=HTMLResponse)
        async def serve_spa(request: Request, full_path: str = ""):
            return (FRONTEND_DIR / "index.html").read_text()

    return app
