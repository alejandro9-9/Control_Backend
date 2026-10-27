"""Puertos que la capa de aplicación necesita de infraestructura."""

from __future__ import annotations

from datetime import datetime
from typing import Generic, Protocol, TypeVar
from uuid import UUID

T = TypeVar("T")


class Repository(Protocol, Generic[T]):
    def save(self, entity: T) -> T:
        ...

    def get(self, entity_id: UUID) -> T | None:
        ...

    def list(self) -> list[T]:
        ...

    def delete(self, entity_id: UUID) -> None:
        ...


class Clock(Protocol):
    def now(self) -> datetime:
        ...
