from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from uuid import UUID, uuid4

from .control_diario import ControlDiario
from .enums import TipoObjetivo
from .objetivo import Objetivo


@dataclass
class ControlSemanal:
    """Agrega controles diarios y objetivos dentro de una semana."""

    fecha_inicio: date
    fecha_fin: date
    controles_diarios: list[ControlDiario] = field(default_factory=list)
    objetivos: list[Objetivo] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.fecha_inicio > self.fecha_fin:
            raise ValueError("La fecha de inicio no puede ser posterior a la fecha fin.")
        if (self.fecha_fin - self.fecha_inicio).days != 6:
            raise ValueError("Un control semanal debe cubrir exactamente siete días.")
        fechas_diarias: set[date] = set()
        for control in self.controles_diarios:
            self._validar_fecha_en_semana(control.fecha)
            if control.fecha in fechas_diarias:
                raise ValueError("No puede haber más de un control diario para la misma fecha.")
            fechas_diarias.add(control.fecha)
        for objetivo in self.objetivos:
            self._validar_objetivo_en_semana(objetivo)

    def _validar_fecha_en_semana(self, fecha: date) -> None:
        if not self.fecha_inicio <= fecha <= self.fecha_fin:
            raise ValueError("La fecha debe pertenecer al período semanal.")

    def agregar_control_diario(self, control: ControlDiario) -> None:
        self._validar_fecha_en_semana(control.fecha)
        if any(item.fecha == control.fecha for item in self.controles_diarios):
            raise ValueError("Ya existe un control diario para esa fecha.")
        self.controles_diarios.append(control)

    def agregar_objetivo(self, objetivo: Objetivo) -> None:
        self._validar_objetivo_en_semana(objetivo)
        self.objetivos.append(objetivo)

    def _validar_objetivo_en_semana(self, objetivo: Objetivo) -> None:
        if objetivo.fecha_inicio is not None:
            self._validar_fecha_en_semana(objetivo.fecha_inicio)
        if objetivo.fecha_limite is not None:
            self._validar_fecha_en_semana(objetivo.fecha_limite)

    def puntos_control(self) -> int:
        return sum(control.calcular_puntaje() for control in self.controles_diarios)

    def puntos_por_tipo(self, tipo: TipoObjetivo) -> int:
        return sum(
            objetivo.calcular_puntaje()
            for objetivo in self.objetivos
            if objetivo.is_active and objetivo.tipo is tipo
        )

    def puntos_misiones(self) -> int:
        return self.puntos_por_tipo(TipoObjetivo.MISION)

    def puntos_pendientes(self) -> int:
        return self.puntos_por_tipo(TipoObjetivo.PENDIENTE)

    def puntos_promesas(self) -> int:
        return self.puntos_por_tipo(TipoObjetivo.PROMESA)

    def puntos_limites(self) -> int:
        return self.puntos_por_tipo(TipoObjetivo.LIMITE)

    def puntos_tiros(self) -> int:
        return self.puntos_por_tipo(TipoObjetivo.TIRO)

    def calcular_puntaje_total(self) -> int:
        return (
            self.puntos_control()
            + self.puntos_misiones()
            + self.puntos_pendientes()
            + self.puntos_promesas()
            + self.puntos_limites()
            + self.puntos_tiros()
        )
