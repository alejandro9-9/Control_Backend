from __future__ import annotations

from enum import Enum


class EstadoActividad(str, Enum):
    PENDIENTE = "pendiente"
    CUMPLIDA = "cumplida"
    INCUMPLIDA = "incumplida"
    CANCELADA = "cancelada"


class TipoObjetivo(str, Enum):
    MISION = "mision"
    PENDIENTE = "pendiente"
    PROMESA = "promesa"
    LIMITE = "limite"
    TIRO = "tiro"
