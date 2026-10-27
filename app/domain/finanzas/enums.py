from __future__ import annotations

from enum import Enum


class CategoriaGastoNombre(str, Enum):
    BUENO = "bueno"
    INTERMEDIO = "intermedio"
    MALO = "malo"
