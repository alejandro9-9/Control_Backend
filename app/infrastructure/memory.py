"""Repositorios en memoria para la primera versión del sistema."""

from __future__ import annotations

from typing import Generic, TypeVar
from uuid import UUID

from app.domain.finanzas import ControlGastoMensual, ControlGastoSemanal
from app.domain.gamificacion import MovimientoPuntaje
from app.domain.productividad import ControlSemanal

T = TypeVar("T")


class InMemoryRepository(Generic[T]):
    """Repositorio simple por identidad, reemplazable por un adaptador persistente."""

    def __init__(self) -> None:
        self._items: dict[UUID, T] = {}

    def save(self, entity: T) -> T:
        entity_id = getattr(entity, "id", None)
        if not isinstance(entity_id, UUID):
            raise TypeError("La entidad debe exponer un id UUID.")
        self._items[entity_id] = entity
        return entity

    def get(self, entity_id: UUID) -> T | None:
        return self._items.get(entity_id)

    def list(self) -> list[T]:
        return list(self._items.values())

    def delete(self, entity_id: UUID) -> None:
        self._items.pop(entity_id, None)

    def clear(self) -> None:
        self._items.clear()


class InMemoryControlSemanalRepository(InMemoryRepository[ControlSemanal]):
    pass


class InMemoryControlGastoSemanalRepository(InMemoryRepository[ControlGastoSemanal]):
    pass


class InMemoryControlGastoMensualRepository(InMemoryRepository[ControlGastoMensual]):
    pass


class InMemoryMovimientoPuntajeRepository(InMemoryRepository[MovimientoPuntaje]):
    pass
