"""
config.py

Centralized configuration parser with fail-fast startup validation and
environment cascading (.env.production, .env.staging, .env).
"""

from __future__ import annotations

import logging
import os
from typing import NamedTuple
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Determine environment first
_RAW_ENV = os.environ.get("APP_ENV", os.environ.get("ENV", "development")).lower().strip()
APP_ENV = "production" if _RAW_ENV in ("prod", "production") else ("staging" if _RAW_ENV == "staging" else "development")

# Cascade load env files: .env.<APP_ENV> takes precedence over .env
_ENV_FILE = f".env.{APP_ENV}"
if os.path.exists(_ENV_FILE):
    load_dotenv(_ENV_FILE, override=True)
load_dotenv(".env")

_PLACEHOLDER_PREFIXES = ("your_", "YOUR_", "your-project-id", "placeholder_")


def _is_placeholder(val: str) -> bool:
    if not val:
        return True
    val_strip = val.strip()
    return (
        any(val_strip.startswith(p) for p in _PLACEHOLDER_PREFIXES)
        or "your-project-id" in val_strip
        or "your_supabase" in val_strip
    )


class Settings(NamedTuple):
    app_env: str
    gemini_api_key: str
    supabase_url: str
    supabase_key: str
    backend_host: str
    backend_port: int
    allowed_origins: list[str]
    rate_limit_search: int
    rate_limit_max_clients: int

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_gemini_configured(self) -> bool:
        return bool(self.gemini_api_key) and not _is_placeholder(self.gemini_api_key)

    @property
    def is_supabase_configured(self) -> bool:
        return (
            bool(self.supabase_url)
            and bool(self.supabase_key)
            and not _is_placeholder(self.supabase_url)
            and not _is_placeholder(self.supabase_key)
        )


def load_settings() -> Settings:
    origins_raw = os.environ.get(
        "ALLOWED_ORIGINS",
        "http://localhost:4321,http://localhost:3000,https://iem-s-recommendation-system-nudd.vercel.app",
    )
    origins = [o.strip().rstrip("/") for o in origins_raw.split(",") if o.strip()]

    try:
        port = int(os.environ.get("BACKEND_PORT", "8000"))
    except ValueError:
        port = 8000

    try:
        rate_limit = int(os.environ.get("RATE_LIMIT_SEARCH", "30"))
    except ValueError:
        rate_limit = 30
    try:
        max_clients = int(os.environ.get("RATE_LIMIT_MAX_CLIENTS", "10000"))
    except ValueError:
        max_clients = 10000

    return Settings(
        app_env=APP_ENV,
        gemini_api_key=os.environ.get("GEMINI_API_KEY", "").strip(),
        supabase_url=os.environ.get("SUPABASE_URL", "").strip(),
        supabase_key=os.environ.get("SUPABASE_KEY", "").strip(),
        backend_host=os.environ.get("BACKEND_HOST", "0.0.0.0").strip(),
        backend_port=port,
        allowed_origins=origins,
        rate_limit_search=rate_limit,
        rate_limit_max_clients=max(1, max_clients),
    )


settings = load_settings()


def validate_config(s: Settings = settings) -> None:
    """
    Validates configuration on server startup.
    Fails fast in production if required keys are missing or invalid.
    """
    logger.info("Initializing configuration for APP_ENV='%s'", s.app_env)

    if s.is_production:
        missing = []
        if not s.is_gemini_configured:
            missing.append("GEMINI_API_KEY")
        if not s.is_supabase_configured:
            missing.append("SUPABASE_URL / SUPABASE_KEY")
        if not s.allowed_origins or "*" in s.allowed_origins:
            missing.append("a non-wildcard ALLOWED_ORIGINS")

        if missing:
            error_msg = (
                f"FATAL: Production mode ('APP_ENV=production') requires valid secrets, "
                f"but the following are missing or set to placeholders: {', '.join(missing)}"
            )
            logger.critical(error_msg)
            raise RuntimeError(error_msg)
    else:
        if not s.is_gemini_configured:
            logger.warning("GEMINI_API_KEY not configured — using offline fallback target profile.")
        if not s.is_supabase_configured:
            logger.info("Supabase credentials not configured — using local dataset.")

