"""Casos de uso de la aplicación."""

from .finanzas import (
    CrearCategoriaGasto,
    CrearControlGastoMensual,
    CrearControlGastoSemanal,
    CrearTipoGasto,
    ObtenerResumenGastoMensual,
    ObtenerResumenGastoSemanal,
    RegistrarGastoMensual,
    RegistrarGastoSemanal,
)
from .gamificacion import ObtenerResumenPuntaje, RegistrarMovimientoPuntaje
from .productividad import (
    ActualizarEstadoTarea,
    AgregarObjetivo,
    AgregarTarea,
    CrearControlSemanal,
    ObtenerResumenSemanal,
)

__all__ = [
    "ActualizarEstadoTarea",
    "AgregarObjetivo",
    "AgregarTarea",
    "CrearControlSemanal",
    "CrearControlGastoMensual",
    "CrearControlGastoSemanal",
    "CrearCategoriaGasto",
    "CrearTipoGasto",
    "ObtenerResumenGastoMensual",
    "ObtenerResumenGastoSemanal",
    "ObtenerResumenPuntaje",
    "ObtenerResumenSemanal",
    "RegistrarGastoMensual",
    "RegistrarGastoSemanal",
    "RegistrarMovimientoPuntaje",
]
