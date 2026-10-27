"""Casos de uso de finanzas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from app.domain.finanzas import (
    CategoriaGastoNombre,
    CategoriaTipoGasto,
    ControlGastoMensual,
    ControlGastoSemanal,
    Gasto,
    TipoGasto,
)

from .dto import ResumenGasto
from .ports import Repository


def _obtener_semanal(
    repository: Repository[ControlGastoSemanal], entity_id: UUID
) -> ControlGastoSemanal:
    entity = repository.get(entity_id)
    if entity is None:
        raise LookupError(f"No existe el control de gasto semanal {entity_id}.")
    return entity


def _obtener_mensual(
    repository: Repository[ControlGastoMensual], entity_id: UUID
) -> ControlGastoMensual:
    entity = repository.get(entity_id)
    if entity is None:
        raise LookupError(f"No existe el control de gasto mensual {entity_id}.")
    return entity


class CrearCategoriaGasto:
    def __init__(self, repository: Repository[CategoriaTipoGasto]) -> None:
        self.repository = repository

    def execute(
        self,
        nombre: CategoriaGastoNombre,
        descripcion: str | None = None,
    ) -> CategoriaTipoGasto:
        categoria = CategoriaTipoGasto(nombre=nombre, descripcion=descripcion)
        return self.repository.save(categoria)


class CrearTipoGasto:
    def __init__(
        self,
        repository: Repository[TipoGasto],
        categoria_repository: Repository[CategoriaTipoGasto],
    ) -> None:
        self.repository = repository
        self.categoria_repository = categoria_repository

    def execute(
        self,
        nombre: str,
        categoria_id: UUID,
        descripcion: str | None = None,
    ) -> TipoGasto:
        categoria = self.categoria_repository.get(categoria_id)
        if categoria is None:
            raise LookupError(f"No existe la categoría de gasto {categoria_id}.")
        tipo = TipoGasto(nombre=nombre, categoria=categoria, descripcion=descripcion)
        return self.repository.save(tipo)


class CrearControlGastoSemanal:
    def __init__(self, repository: Repository[ControlGastoSemanal]) -> None:
        self.repository = repository

    def execute(
        self,
        fecha_inicio: date,
        fecha_fin: date,
        limite_gasto: Decimal,
    ) -> ControlGastoSemanal:
        control = ControlGastoSemanal(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            limite_gasto=limite_gasto,
        )
        return self.repository.save(control)


class CrearControlGastoMensual:
    def __init__(self, repository: Repository[ControlGastoMensual]) -> None:
        self.repository = repository

    def execute(
        self,
        anio: int,
        mes: int,
        presupuesto: Decimal,
    ) -> ControlGastoMensual:
        control = ControlGastoMensual(
            anio=anio,
            mes=mes,
            presupuesto=presupuesto,
        )
        return self.repository.save(control)


class RegistrarGastoSemanal:
    def __init__(self, repository: Repository[ControlGastoSemanal]) -> None:
        self.repository = repository

    def execute(
        self,
        control_id: UUID,
        nombre: str,
        importe: Decimal,
        tipo_gasto: TipoGasto,
        fecha_hora: datetime,
        *,
        descripcion: str | None = None,
        puntaje_generado: int = 0,
    ) -> Gasto:
        control = _obtener_semanal(self.repository, control_id)
        gasto = Gasto(
            nombre=nombre,
            importe=importe,
            tipo_gasto=tipo_gasto,
            fecha_hora=fecha_hora,
            descripcion=descripcion,
            puntaje_generado=puntaje_generado,
        )
        control.registrar_gasto(gasto)
        self.repository.save(control)
        return gasto


class RegistrarGastoMensual:
    def __init__(self, repository: Repository[ControlGastoMensual]) -> None:
        self.repository = repository

    def execute(
        self,
        control_id: UUID,
        nombre: str,
        importe: Decimal,
        tipo_gasto: TipoGasto,
        fecha_hora: datetime,
        *,
        descripcion: str | None = None,
        puntaje_generado: int = 0,
    ) -> Gasto:
        control = _obtener_mensual(self.repository, control_id)
        gasto = Gasto(
            nombre=nombre,
            importe=importe,
            tipo_gasto=tipo_gasto,
            fecha_hora=fecha_hora,
            descripcion=descripcion,
            puntaje_generado=puntaje_generado,
        )
        control.registrar_gasto(gasto)
        self.repository.save(control)
        return gasto


class ObtenerResumenGastoSemanal:
    def __init__(self, repository: Repository[ControlGastoSemanal]) -> None:
        self.repository = repository

    def execute(self, control_id: UUID) -> ResumenGasto:
        control = _obtener_semanal(self.repository, control_id)
        return ResumenGasto(
            control_id=control.id,
            total_gastado=control.total_gastado(),
            limite_o_presupuesto=control.limite_gasto,
            saldo=control.disponible(),
            porcentaje_consumido=(
                Decimal("0")
                if control.limite_gasto == Decimal("0")
                else (control.total_gastado() / control.limite_gasto) * Decimal("100")
            ),
            excedido=control.excedio_limite(),
        )


class ObtenerResumenGastoMensual:
    def __init__(self, repository: Repository[ControlGastoMensual]) -> None:
        self.repository = repository

    def execute(self, control_id: UUID) -> ResumenGasto:
        control = _obtener_mensual(self.repository, control_id)
        return ResumenGasto(
            control_id=control.id,
            total_gastado=control.total_gastado(),
            limite_o_presupuesto=control.presupuesto,
            saldo=control.saldo_presupuesto(),
            porcentaje_consumido=control.porcentaje_consumido(),
            excedido=control.total_gastado() > control.presupuesto,
        )
