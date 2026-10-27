"""Casos de uso de gamificación."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.domain.gamificacion import (
    MovimientoPuntaje,
    OrigenPuntaje,
    TipoMovimientoPuntaje,
    obtener_rango,
)

from .dto import ResumenPuntaje
from .ports import Clock, Repository


class RegistrarMovimientoPuntaje:
    def __init__(self, repository: Repository[MovimientoPuntaje], clock: Clock) -> None:
        self.repository = repository
        self.clock = clock

    def execute(
        self,
        puntos: int,
        origen: OrigenPuntaje,
        motivo: str,
        tipo: TipoMovimientoPuntaje,
        *,
        fecha_hora: datetime | None = None,
        referencia_id: UUID | None = None,
    ) -> MovimientoPuntaje:
        # El tipo es la fuente de verdad del signo. Así una penalización
        # enviada como valor positivo nunca incrementa el puntaje acumulado.
        puntos = abs(puntos) if tipo is TipoMovimientoPuntaje.BONIFICACION else -abs(puntos)
        movimiento = MovimientoPuntaje(
            puntos=puntos,
            origen=origen,
            motivo=motivo,
            fecha_hora=fecha_hora or self.clock.now(),
            tipo=tipo,
            referencia_id=referencia_id,
        )
        return self.repository.save(movimiento)


class ObtenerResumenPuntaje:
    def __init__(self, repository: Repository[MovimientoPuntaje]) -> None:
        self.repository = repository

    def execute(self) -> ResumenPuntaje:
        movimientos = self.repository.list()
        total = sum(movimiento.puntos for movimiento in movimientos)
        return ResumenPuntaje(
            total_puntos=total,
            movimientos=len(movimientos),
            rango=obtener_rango(total).nombre,
        )
