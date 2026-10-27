from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from .gasto import Gasto


@dataclass
class ControlGastoSemanal:
    fecha_inicio: date
    fecha_fin: date
    limite_gasto: Decimal
    gastos: list[Gasto] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.fecha_inicio > self.fecha_fin:
            raise ValueError("La fecha de inicio no puede ser posterior a la fecha fin.")
        if self.limite_gasto < Decimal("0"):
            raise ValueError("El límite de gasto no puede ser negativo.")
        for gasto in self.gastos:
            self._validar_fecha(gasto)

    def _validar_fecha(self, gasto: Gasto) -> None:
        fecha = gasto.fecha_operativa()
        if not self.fecha_inicio <= fecha <= self.fecha_fin:
            raise ValueError("El gasto no pertenece a esta semana.")

    def registrar_gasto(self, gasto: Gasto) -> None:
        self._validar_fecha(gasto)
        self.gastos.append(gasto)

    def total_gastado(self) -> Decimal:
        return sum(
            (gasto.importe for gasto in self.gastos if gasto.is_active),
            start=Decimal("0"),
        )

    def disponible(self) -> Decimal:
        return self.limite_gasto - self.total_gastado()

    def excedio_limite(self) -> bool:
        return self.total_gastado() > self.limite_gasto
