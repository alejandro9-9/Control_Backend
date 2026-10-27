"""Engine y fábrica de sesiones para el backend HTTP."""

from __future__ import annotations

from .postgres import create_engine_and_session_factory
from .settings import Settings

settings = Settings.from_env()
engine, SessionLocal = create_engine_and_session_factory(settings.database_url)
