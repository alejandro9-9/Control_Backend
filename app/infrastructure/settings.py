"""Configuración de infraestructura basada en variables de entorno."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "Productividad Finanzas API"
    environment: str = "development"
    database_url: str = (
        "postgresql+psycopg://app:app@localhost:5432/productividad_finanzas"
    )
    cors_origins: str = (
        "http://localhost:5173,http://localhost:5174,"
        "http://127.0.0.1:5173,http://127.0.0.1:5174"
    )

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_name=os.getenv("APP_NAME", cls.app_name),
            environment=os.getenv("APP_ENV", cls.environment),
            database_url=os.getenv("DATABASE_URL", cls.database_url),
            cors_origins=os.getenv("CORS_ORIGINS", cls.cors_origins),
        )

    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
