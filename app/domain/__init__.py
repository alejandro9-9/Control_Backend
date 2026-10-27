"""Núcleo del dominio de la aplicación."""

from .finanzas import (
    CategoriaGastoNombre,
    CategoriaTipoGasto,
    ControlGastoMensual,
    ControlGastoSemanal,
    Gasto,
    TipoGasto,
)
from .gamificacion import (
    MovimientoPuntaje,
    NombreRango,
    OrigenPuntaje,
    RANGOS,
    Rango,
    TipoMovimientoPuntaje,
    obtener_rango,
)
from .productividad import (
    ControlDiario,
    ControlSemanal,
    EstadoActividad,
    Objetivo,
    TareaControl,
    TipoObjetivo,
)

__all__ = [
    "CategoriaGastoNombre",
    "CategoriaTipoGasto",
    "ControlDiario",
    "ControlGastoMensual",
    "ControlGastoSemanal",
    "ControlSemanal",
    "EstadoActividad",
    "Gasto",
    "MovimientoPuntaje",
    "NombreRango",
    "Objetivo",
    "OrigenPuntaje",
    "RANGOS",
    "Rango",
    "TareaControl",
    "TipoGasto",
    "TipoMovimientoPuntaje",
    "TipoObjetivo",
    "obtener_rango",
]
