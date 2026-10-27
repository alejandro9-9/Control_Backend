from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from .enums import CategoriaGastoNombre


@dataclass
class CategoriaTipoGasto:
    nombre: CategoriaGastoNombre
    descripcion: str | None = None
    is_active: bool = True
    id: UUID = field(default_factory=uuid4)
