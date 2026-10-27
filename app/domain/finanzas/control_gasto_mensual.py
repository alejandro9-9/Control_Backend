from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from .gasto import Gasto


@dataclass
class ControlGastoMensual:
    anio: int
    mes: int
    presupuesto: Decimal
    gastos: list[Gasto] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.anio < 1:
            raise ValueError("El año debe ser positivo.")
        if not 1 <= self.mes <= 12:
            raise ValueError("El mes debe estar entre 1 y 12.")
        if self.presupuesto < Decimal("0"):
            raise ValueError("El presupuesto no puede ser negativo.")
        for gasto in self.gastos:
            self._validar_fecha(gasto)

    def _validar_fecha(self, gasto: Gasto) -> None:
        fecha = gasto.fecha_operativa()
        if fecha.year != self.anio or fecha.month != self.mes:
            raise ValueError("El gasto no pertenece a este mes.")

    def registrar_gasto(self, gasto: Gasto) -> None:
        self._validar_fecha(gasto)
        self.gastos.append(gasto)

    def total_gastado(self) -> Decimal:
        return sum(
            (gasto.importe for gasto in self.gastos if gasto.is_active),
            start=Decimal("0"),
        )

    def saldo_presupuesto(self) -> Decimal:
        return self.presupuesto - self.total_gastado()

    def porcentaje_consumido(self) -> Decimal:
        if self.presupuesto == Decimal("0"):
            return Decimal("0")
        return (self.total_gastado() / self.presupuesto) * Decimal("100")
