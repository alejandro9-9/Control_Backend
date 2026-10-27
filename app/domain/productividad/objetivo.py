from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from uuid import UUID, uuid4

from .enums import EstadoActividad, TipoObjetivo


@dataclass
class Objetivo:
    """Objetivo puntuable de una semana."""

    nombre: str
    tipo: TipoObjetivo
    puntos_cumplimiento: int
    puntos_incumplimiento: int
    estado: EstadoActividad = EstadoActividad.PENDIENTE
    fecha_inicio: date | None = None
    fecha_limite: date | None = None
    descripcion: str | None = None
    is_active: bool = True
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.nombre.strip():
            raise ValueError("El nombre del objetivo es obligatorio.")
        if self.fecha_inicio and self.fecha_limite and self.fecha_inicio > self.fecha_limite:
            raise ValueError("La fecha de inicio no puede ser posterior a la fecha límite.")

    def completar(self) -> None:
        self.estado = EstadoActividad.CUMPLIDA

    def incumplir(self) -> None:
        self.estado = EstadoActividad.INCUMPLIDA

    def cancelar(self) -> None:
        self.estado = EstadoActividad.CANCELADA

    def calcular_puntaje(self) -> int:
        if self.estado is EstadoActividad.CUMPLIDA:
            return self.puntos_cumplimiento
        if self.estado is EstadoActividad.INCUMPLIDA:
            return self.puntos_incumplimiento
        return 0
