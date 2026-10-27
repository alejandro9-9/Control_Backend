from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from uuid import UUID, uuid4

from .enums import EstadoActividad
from .tarea_control import TareaControl


@dataclass
class ControlDiario:
    """Calcula el puntaje diario según las reglas del Excel."""

    fecha: date
    tareas: list[TareaControl] = field(default_factory=list)
    puntos_base: int = 7
    penalizacion_incumplimiento: int = 2
    bono_sobrecarga: int = 1
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.puntos_base < 0:
            raise ValueError("Los puntos base no pueden ser negativos.")
        if self.penalizacion_incumplimiento < 0 or self.bono_sobrecarga < 0:
            raise ValueError("Las reglas de puntaje deben ser no negativas.")
        for tarea in self.tareas:
            self._validar_fecha_tarea(tarea)

    def _validar_fecha_tarea(self, tarea: TareaControl) -> None:
        if tarea.fecha_programada != self.fecha:
            raise ValueError("La fecha de la tarea debe coincidir con la fecha del control diario.")

    def agregar_tarea(self, tarea: TareaControl) -> None:
        self._validar_fecha_tarea(tarea)
        self.tareas.append(tarea)

    @property
    def incumplimientos(self) -> int:
        return sum(
            1
            for tarea in self.tareas
            if not tarea.es_sobrecarga and tarea.estado is EstadoActividad.INCUMPLIDA
        )

    @property
    def sobrecargas_cumplidas(self) -> int:
        return sum(
            1
            for tarea in self.tareas
            if tarea.es_sobrecarga and tarea.estado is EstadoActividad.CUMPLIDA
        )

    def calcular_puntaje(self) -> int:
        penalizacion = self.incumplimientos * self.penalizacion_incumplimiento
        bonificacion = self.sobrecargas_cumplidas * self.bono_sobrecarga
        return self.puntos_base - penalizacion + bonificacion
