"""FastAPI application factory."""

import secrets
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from wko5.api.auth import set_token
from wko5.api.routes import router


def create_app(token: str = None, allowed_origins: list = None):
    if token is None:
        token = secrets.token_urlsafe(32)
    set_token(token)

    app = FastAPI(title="WKO5 Analyzer API")

    if allowed_origins is None:
        allowed_origins = ["http://localhost", "http://127.0.0.1"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization"],
    )

    app.include_router(router)
    return app
