from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from .enums import OrigenPuntaje, TipoMovimientoPuntaje


@dataclass(frozen=True)
class MovimientoPuntaje:
    """Movimiento auditable que explica un cambio en el puntaje."""

    puntos: int
    origen: OrigenPuntaje
    motivo: str
    fecha_hora: datetime
    tipo: TipoMovimientoPuntaje
    referencia_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.motivo.strip():
            raise ValueError("El motivo del movimiento es obligatorio.")
        signed_points = (
            abs(self.puntos)
            if self.tipo is TipoMovimientoPuntaje.BONIFICACION
            else -abs(self.puntos)
        )
        object.__setattr__(self, "puntos", signed_points)
