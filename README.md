# Control Backend

API REST para control semanal de productividad, finanzas y gamificación.

## Tecnologías

- Python 3.12
- FastAPI + Uvicorn
- SQLAlchemy + Psycopg
- PostgreSQL 16
- Docker / Docker Compose

## Desarrollo local

```powershell
Copy-Item .env.example .env
docker compose up --build
```

La API queda disponible en `http://localhost:8001` y su health check en `/api/v1/health`.

## Variables de producción

- `DATABASE_URL`: conexión PostgreSQL compatible con Psycopg.
- `CORS_ORIGINS`: dominios permitidos del frontend.
- `APP_ENV=production`.
