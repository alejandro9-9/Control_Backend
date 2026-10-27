"""Composition root de la aplicación."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.application.finanzas import (
    CrearControlGastoMensual,
    CrearControlGastoSemanal,
    ObtenerResumenGastoMensual,
    ObtenerResumenGastoSemanal,
    RegistrarGastoMensual,
    RegistrarGastoSemanal,
)
from app.application.gamificacion import ObtenerResumenPuntaje, RegistrarMovimientoPuntaje
from app.application.productividad import (
    ActualizarEstadoTarea,
    AgregarObjetivo,
    AgregarTarea,
    CrearControlSemanal,
    ObtenerResumenSemanal,
)
from app.domain.finanzas import ControlGastoMensual, ControlGastoSemanal
from app.domain.gamificacion import MovimientoPuntaje
from app.domain.productividad import ControlSemanal

from .clock import SystemClock
from .memory import (
    InMemoryControlGastoMensualRepository,
    InMemoryControlGastoSemanalRepository,
    InMemoryControlSemanalRepository,
    InMemoryMovimientoPuntajeRepository,
)


@dataclass
class AppContainer:
    """Dependencias de la aplicación listas para ser usadas por una interfaz."""

    controles_semanales: InMemoryControlSemanalRepository = field(
        default_factory=InMemoryControlSemanalRepository
    )
    controles_gasto_semanales: InMemoryControlGastoSemanalRepository = field(
        default_factory=InMemoryControlGastoSemanalRepository
    )
    controles_gasto_mensuales: InMemoryControlGastoMensualRepository = field(
        default_factory=InMemoryControlGastoMensualRepository
    )
    movimientos_puntaje: InMemoryMovimientoPuntajeRepository = field(
        default_factory=InMemoryMovimientoPuntajeRepository
    )
    clock: SystemClock = field(default_factory=SystemClock)

    def __post_init__(self) -> None:
        self.crear_control_semanal = CrearControlSemanal(self.controles_semanales)
        self.agregar_tarea = AgregarTarea(self.controles_semanales)
        self.agregar_objetivo = AgregarObjetivo(self.controles_semanales)
        self.actualizar_estado_tarea = ActualizarEstadoTarea(self.controles_semanales)
        self.obtener_resumen_semanal = ObtenerResumenSemanal(self.controles_semanales)

        self.registrar_gasto_semanal = RegistrarGastoSemanal(
            self.controles_gasto_semanales
        )
        self.crear_control_gasto_semanal = CrearControlGastoSemanal(
            self.controles_gasto_semanales
        )
        self.obtener_resumen_gasto_semanal = ObtenerResumenGastoSemanal(
            self.controles_gasto_semanales
        )
        self.registrar_gasto_mensual = RegistrarGastoMensual(
            self.controles_gasto_mensuales
        )
        self.crear_control_gasto_mensual = CrearControlGastoMensual(
            self.controles_gasto_mensuales
        )
        self.obtener_resumen_gasto_mensual = ObtenerResumenGastoMensual(
            self.controles_gasto_mensuales
        )

        self.registrar_movimiento_puntaje = RegistrarMovimientoPuntaje(
            self.movimientos_puntaje, self.clock
        )
        self.obtener_resumen_puntaje = ObtenerResumenPuntaje(self.movimientos_puntaje)


def build_container() -> AppContainer:
    return AppContainer()
