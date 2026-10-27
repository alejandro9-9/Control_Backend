from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from uuid import UUID, uuid4

from .enums import EstadoActividad


@dataclass
class TareaControl:
    """Tarea del control diario, con transiciones explícitas de estado."""

    nombre: str
    fecha_programada: date
    estado: EstadoActividad = EstadoActividad.PENDIENTE
    es_sobrecarga: bool = False
    descripcion: str | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.nombre.strip():
            raise ValueError("El nombre de la tarea es obligatorio.")

    def completar(self) -> None:
        self.estado = EstadoActividad.CUMPLIDA

    def incumplir(self) -> None:
        self.estado = EstadoActividad.INCUMPLIDA

    def cancelar(self) -> None:
        self.estado = EstadoActividad.CANCELADA
