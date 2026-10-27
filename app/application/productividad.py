"""Casos de uso de productividad."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from app.domain.gamificacion import obtener_rango
from app.domain.productividad import (
    ControlSemanal,
    EstadoActividad,
    Objetivo,
    TareaControl,
    TipoObjetivo,
)

from .dto import ResumenSemanal
from .ports import Repository


def _obtener_o_fallar(repository: Repository[ControlSemanal], entity_id: UUID) -> ControlSemanal:
    entity = repository.get(entity_id)
    if entity is None:
        raise LookupError(f"No existe el control semanal {entity_id}.")
    return entity


class CrearControlSemanal:
    def __init__(self, repository: Repository[ControlSemanal]) -> None:
        self.repository = repository

    def execute(self, fecha_inicio: date, fecha_fin: date) -> ControlSemanal:
        control = ControlSemanal(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
        return self.repository.save(control)


class AgregarTarea:
    def __init__(self, repository: Repository[ControlSemanal]) -> None:
        self.repository = repository

    def execute(
        self,
        control_id: UUID,
        nombre: str,
        fecha_programada: date,
        *,
        estado: EstadoActividad = EstadoActividad.PENDIENTE,
        es_sobrecarga: bool = False,
        descripcion: str | None = None,
    ) -> TareaControl:
        control = _obtener_o_fallar(self.repository, control_id)
        tarea = TareaControl(
            nombre=nombre,
            fecha_programada=fecha_programada,
            estado=estado,
            es_sobrecarga=es_sobrecarga,
            descripcion=descripcion,
        )
        control_diario = next(
            (item for item in control.controles_diarios if item.fecha == fecha_programada),
            None,
        )
        if control_diario is None:
            from app.domain.productividad import ControlDiario

            control_diario = ControlDiario(fecha=fecha_programada)
            control.agregar_control_diario(control_diario)
        control_diario.agregar_tarea(tarea)
        self.repository.save(control)
        return tarea


class AgregarObjetivo:
    def __init__(self, repository: Repository[ControlSemanal]) -> None:
        self.repository = repository

    def execute(
        self,
        control_id: UUID,
        nombre: str,
        tipo: TipoObjetivo,
        puntos_cumplimiento: int,
        puntos_incumplimiento: int,
        *,
        estado: EstadoActividad = EstadoActividad.PENDIENTE,
        fecha_inicio: date | None = None,
        fecha_limite: date | None = None,
        descripcion: str | None = None,
    ) -> Objetivo:
        control = _obtener_o_fallar(self.repository, control_id)
        objetivo = Objetivo(
            nombre=nombre,
            tipo=tipo,
            puntos_cumplimiento=puntos_cumplimiento,
            puntos_incumplimiento=puntos_incumplimiento,
            estado=estado,
            fecha_inicio=fecha_inicio,
            fecha_limite=fecha_limite,
            descripcion=descripcion,
        )
        control.agregar_objetivo(objetivo)
        self.repository.save(control)
        return objetivo


class ActualizarEstadoObjetivo:
    def __init__(self, repository: Repository[ControlSemanal]) -> None:
        self.repository = repository

    def execute(
        self,
        control_id: UUID,
        objetivo_id: UUID,
        estado: EstadoActividad,
    ) -> Objetivo:
        control = _obtener_o_fallar(self.repository, control_id)
        objetivo = next((item for item in control.objetivos if item.id == objetivo_id), None)
        if objetivo is None:
            raise LookupError(f"No existe el objetivo {objetivo_id} en el control semanal.")
        if estado is EstadoActividad.CUMPLIDA:
            objetivo.completar()
        elif estado is EstadoActividad.INCUMPLIDA:
            objetivo.incumplir()
        elif estado is EstadoActividad.CANCELADA:
            objetivo.cancelar()
        elif estado is EstadoActividad.PENDIENTE:
            objetivo.estado = estado
        else:
            raise ValueError(f"Estado de objetivo no soportado: {estado}.")
        self.repository.save(control)
        return objetivo


class ActualizarEstadoTarea:
    def __init__(self, repository: Repository[ControlSemanal]) -> None:
        self.repository = repository

    def execute(
        self,
        control_id: UUID,
        tarea_id: UUID,
        estado: EstadoActividad,
    ) -> TareaControl:
        control = _obtener_o_fallar(self.repository, control_id)
        tarea = next(
            (
                tarea
                for diario in control.controles_diarios
                for tarea in diario.tareas
                if tarea.id == tarea_id
            ),
            None,
        )
        if tarea is None:
            raise LookupError(f"No existe la tarea {tarea_id} en el control semanal.")
        transiciones = {
            EstadoActividad.CUMPLIDA: tarea.completar,
            EstadoActividad.INCUMPLIDA: tarea.incumplir,
            EstadoActividad.CANCELADA: tarea.cancelar,
        }
        if estado is EstadoActividad.PENDIENTE:
            tarea.estado = estado
        elif estado in transiciones:
            transiciones[estado]()
        else:
            raise ValueError(f"Estado de tarea no soportado: {estado}.")
        self.repository.save(control)
        return tarea


class ObtenerResumenSemanal:
    def __init__(self, repository: Repository[ControlSemanal]) -> None:
        self.repository = repository

    def execute(self, control_id: UUID) -> ResumenSemanal:
        control = _obtener_o_fallar(self.repository, control_id)
        puntos_control = control.puntos_control()
        puntos_misiones = control.puntos_misiones()
        puntos_pendientes = control.puntos_pendientes()
        puntos_promesas = control.puntos_promesas()
        puntos_limites = control.puntos_limites()
        puntos_tiros = control.puntos_tiros()
        total = control.calcular_puntaje_total()
        return ResumenSemanal(
            control_id=control.id,
            fecha_inicio=control.fecha_inicio,
            fecha_fin=control.fecha_fin,
            puntos_control=puntos_control,
            puntos_misiones=puntos_misiones,
            puntos_pendientes=puntos_pendientes,
            puntos_promesas=puntos_promesas,
            puntos_limites=puntos_limites,
            puntos_tiros=puntos_tiros,
            puntos_total=total,
            rango=obtener_rango(total).nombre,
        )
