"""Punto de entrada del backend HTTP."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DataError, IntegrityError

from app.api.routes import router
from app.infrastructure.database import engine, settings
from app.infrastructure.postgres import init_database


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_database(engine)
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins(),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(router)

    @application.exception_handler(IntegrityError)
    async def integrity_error_handler(_: Request, __: IntegrityError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": "La operación viola una restricción de datos."},
        )

    @application.exception_handler(DataError)
    async def data_error_handler(_: Request, __: DataError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": "Los datos exceden los límites admitidos."},
        )

    return application


app = create_app()
