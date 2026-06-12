"""FastAPI application entrypoint."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .database import init_db
from .routes import auth, jobs, pipelines, templates, user

# Repo-root/frontend/dist (main.py is at backend/app/main.py).
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
_API_PREFIXES = ("api/", "health", "docs", "redoc", "openapi.json")

settings = get_settings()


def _configure_logging() -> None:
    Path("logs").mkdir(exist_ok=True)
    handler = RotatingFileHandler(
        "logs/app.log", maxBytes=5_000_000, backupCount=3, encoding="utf-8"
    )
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[handler, logging.StreamHandler()],
    )


_configure_logging()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="No-code microscopy image analysis pipeline platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    from .database import SessionLocal
    from .services.auth_service import seed_demo_user

    db = SessionLocal()
    try:
        seed_demo_user(db)
    finally:
        db.close()
    logging.getLogger("main").info("Database initialized; demo user ready")


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}


app.include_router(auth.router)
app.include_router(pipelines.router)
app.include_router(jobs.router)
app.include_router(templates.router)
app.include_router(user.router)


# --- Serve the built frontend (single-server deploy) -------------------------
# When frontend/dist exists, the API also serves the SPA: real files are
# returned directly and any other (client-routed) path falls back to index.html.
if (FRONTEND_DIST / "index.html").exists():
    if (FRONTEND_DIST / "assets").is_dir():
        app.mount(
            "/assets",
            StaticFiles(directory=FRONTEND_DIST / "assets"),
            name="assets",
        )

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        if full_path.startswith(_API_PREFIXES):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
