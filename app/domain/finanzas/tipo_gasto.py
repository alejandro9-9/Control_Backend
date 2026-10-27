from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from .categoria_tipo_gasto import CategoriaTipoGasto


@dataclass
class TipoGasto:
    nombre: str
    categoria: CategoriaTipoGasto
    descripcion: str | None = None
    is_active: bool = True
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.nombre.strip():
            raise ValueError("El nombre del tipo de gasto es obligatorio.")
