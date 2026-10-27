"""Resultados de lectura expuestos por los casos de uso."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.domain.gamificacion import NombreRango


@dataclass(frozen=True)
class ResumenSemanal:
    control_id: UUID
    fecha_inicio: date
    fecha_fin: date
    puntos_control: int
    puntos_misiones: int
    puntos_pendientes: int
    puntos_promesas: int
    puntos_limites: int
    puntos_tiros: int
    puntos_total: int
    rango: NombreRango


@dataclass(frozen=True)
class ResumenGasto:
    control_id: UUID
    total_gastado: Decimal
    limite_o_presupuesto: Decimal
    saldo: Decimal
    porcentaje_consumido: Decimal
    excedido: bool


@dataclass(frozen=True)
class ResumenPuntaje:
    total_puntos: int
    movimientos: int
    rango: NombreRango
