from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from .tipo_gasto import TipoGasto


@dataclass
class Gasto:
    nombre: str
    importe: Decimal
    tipo_gasto: TipoGasto
    fecha_hora: datetime
    descripcion: str | None = None
    puntaje_generado: int = 0
    is_active: bool = True
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.nombre.strip():
            raise ValueError("El gasto debe tener un nombre.")
        if self.importe <= Decimal("0"):
            raise ValueError("El importe debe ser mayor que cero.")

    def fecha_operativa(self) -> date:
        """Devuelve la fecha en la zona de negocio (Lima).

        PostgreSQL normaliza ``timestamptz`` a UTC al leerlo. Convertir antes
        de validar evita que un gasto cerca de medianoche cambie de día al
        reconstruir el agregado.
        """
        if self.fecha_hora.tzinfo is None:
            return self.fecha_hora.date()
        return self.fecha_hora.astimezone(ZoneInfo("America/Lima")).date()
