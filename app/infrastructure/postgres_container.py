"""Composición de casos de uso sobre una sesión PostgreSQL."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.application.finanzas import (
    CrearCategoriaGasto,
    CrearControlGastoMensual,
    CrearControlGastoSemanal,
    CrearTipoGasto,
    ObtenerResumenGastoMensual,
    ObtenerResumenGastoSemanal,
    RegistrarGastoMensual,
    RegistrarGastoSemanal,
)
from app.application.gamificacion import ObtenerResumenPuntaje, RegistrarMovimientoPuntaje
from app.application.productividad import (
    ActualizarEstadoTarea,
    ActualizarEstadoObjetivo,
    AgregarObjetivo,
    AgregarTarea,
    CrearControlSemanal,
    ObtenerResumenSemanal,
)
from app.infrastructure.clock import SystemClock

from .postgres import (
    SqlAlchemyCategoriaTipoGastoRepository,
    SqlAlchemyControlGastoMensualRepository,
    SqlAlchemyControlGastoSemanalRepository,
    SqlAlchemyControlSemanalRepository,
    SqlAlchemyMovimientoPuntajeRepository,
    SqlAlchemyTipoGastoRepository,
)


@dataclass
class PostgresAppContainer:
    """Casos de uso configurados con repositorios PostgreSQL."""

    session_factory: Callable[[], Session]

    def __post_init__(self) -> None:
        factory = self.session_factory
        self.controles_semanales = SqlAlchemyControlSemanalRepository(factory)
        self.controles_gasto_semanales = SqlAlchemyControlGastoSemanalRepository(factory)
        self.controles_gasto_mensuales = SqlAlchemyControlGastoMensualRepository(factory)
        self.categorias_tipo_gasto = SqlAlchemyCategoriaTipoGastoRepository(factory)
        self.tipos_gasto = SqlAlchemyTipoGastoRepository(factory)
        self.movimientos_puntaje = SqlAlchemyMovimientoPuntajeRepository(factory)
        self.clock = SystemClock()

        self.crear_control_semanal = CrearControlSemanal(self.controles_semanales)
        self.agregar_tarea = AgregarTarea(self.controles_semanales)
        self.agregar_objetivo = AgregarObjetivo(self.controles_semanales)
        self.actualizar_estado_tarea = ActualizarEstadoTarea(self.controles_semanales)
        self.actualizar_estado_objetivo = ActualizarEstadoObjetivo(self.controles_semanales)
        self.obtener_resumen_semanal = ObtenerResumenSemanal(self.controles_semanales)

        self.crear_categoria_gasto = CrearCategoriaGasto(self.categorias_tipo_gasto)
        self.crear_tipo_gasto = CrearTipoGasto(self.tipos_gasto, self.categorias_tipo_gasto)
        self.crear_control_gasto_semanal = CrearControlGastoSemanal(
            self.controles_gasto_semanales
        )
        self.registrar_gasto_semanal = RegistrarGastoSemanal(
            self.controles_gasto_semanales
        )
        self.obtener_resumen_gasto_semanal = ObtenerResumenGastoSemanal(
            self.controles_gasto_semanales
        )
        self.crear_control_gasto_mensual = CrearControlGastoMensual(
            self.controles_gasto_mensuales
        )
        self.registrar_gasto_mensual = RegistrarGastoMensual(
            self.controles_gasto_mensuales
        )
        self.obtener_resumen_gasto_mensual = ObtenerResumenGastoMensual(
            self.controles_gasto_mensuales
        )

        self.registrar_movimiento_puntaje = RegistrarMovimientoPuntaje(
            self.movimientos_puntaje, self.clock
        )
        self.obtener_resumen_puntaje = ObtenerResumenPuntaje(self.movimientos_puntaje)
