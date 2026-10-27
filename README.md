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

## Despliegue en Render + Neon

El archivo `render.yaml` define el servicio Docker y el health check
`/api/v1/health`. Configura en Render `DATABASE_URL` con la URL de Neon y
`CORS_ORIGINS` con el dominio de Vercel. El contenedor usa automáticamente la
variable `PORT` entregada por Render.
