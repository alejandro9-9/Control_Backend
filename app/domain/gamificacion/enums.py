from __future__ import annotations

from enum import Enum


class TipoMovimientoPuntaje(str, Enum):
    BONIFICACION = "bonificacion"
    PENALIZACION = "penalizacion"


class OrigenPuntaje(str, Enum):
    CONTROL = "control"
    MISION = "mision"
    PENDIENTE = "pendiente"
    PROMESA = "promesa"
    LIMITE = "limite"
    TIRO = "tiro"
    GASTO = "gasto"
    SOBRECARGA = "sobrecarga"


class NombreRango(str, Enum):
    DESPOJO_HUMANO = "DESPOJO HUMANO"
    MEDIOCRE = "MEDIOCRE"
    PELEADOR = "PELEADOR"
    EL_MEJOR = "EL MEJOR"
    INDISCUTIBLE = "INDISCUTIBLE"
    DEIDAD = "DEIDAD"
