"""Entidades y reglas de puntuación y rangos."""

from .enums import NombreRango, OrigenPuntaje, TipoMovimientoPuntaje
from .movimiento_puntaje import MovimientoPuntaje
from .rango import RANGOS, Rango, obtener_rango

__all__ = [
    "MovimientoPuntaje",
    "NombreRango",
    "OrigenPuntaje",
    "RANGOS",
    "Rango",
    "TipoMovimientoPuntaje",
    "obtener_rango",
]
