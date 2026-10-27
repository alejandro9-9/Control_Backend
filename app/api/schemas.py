"""Esquemas de entrada y salida de la API."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.finanzas import CategoriaGastoNombre
from app.domain.gamificacion import OrigenPuntaje, TipoMovimientoPuntaje
from app.domain.productividad import EstadoActividad, TipoObjetivo


class SemanaCreate(BaseModel):
    fecha_inicio: date
    fecha_fin: date

    @model_validator(mode="after")
    def validar_semana(self) -> "SemanaCreate":
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha de inicio no puede ser posterior a la fecha fin.")
        if (self.fecha_fin - self.fecha_inicio).days != 6:
            raise ValueError("La semana debe cubrir exactamente siete días.")
        return self


class SemanaResponse(BaseModel):
    id: UUID
    fecha_inicio: date
    fecha_fin: date


class TareaCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=200)
    fecha_programada: date
    estado: EstadoActividad = EstadoActividad.PENDIENTE
    es_sobrecarga: bool = False
    descripcion: str | None = Field(default=None, max_length=1000)


class TareaStateUpdate(BaseModel):
    estado: EstadoActividad


class TareaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    fecha_programada: date
    estado: EstadoActividad
    es_sobrecarga: bool
    descripcion: str | None


class ObjetivoCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=200)
    tipo: TipoObjetivo
    puntos_cumplimiento: int = Field(ge=-2_147_483_648, le=2_147_483_647)
    puntos_incumplimiento: int = Field(ge=-2_147_483_648, le=2_147_483_647)
    estado: EstadoActividad = EstadoActividad.PENDIENTE
    fecha_inicio: date | None = None
    fecha_limite: date | None = None
    descripcion: str | None = Field(default=None, max_length=1000)


class ObjetivoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    tipo: TipoObjetivo
    puntos_cumplimiento: int
    puntos_incumplimiento: int
    estado: EstadoActividad
    fecha_inicio: date | None
    fecha_limite: date | None
    descripcion: str | None


class ControlDiarioDetalleResponse(BaseModel):
    id: UUID
    fecha: date
    puntos_base: int
    penalizacion_incumplimiento: int
    bono_sobrecarga: int
    puntos: int
    tareas: list[TareaResponse]


class SemanaDetalleResponse(BaseModel):
    id: UUID
    fecha_inicio: date
    fecha_fin: date
    puntos_control: int
    puntos_misiones: int
    puntos_pendientes: int
    puntos_promesas: int
    puntos_limites: int
    puntos_tiros: int
    puntos_total: int
    rango: str
    objetivos: list[ObjetivoResponse]
    controles_diarios: list[ControlDiarioDetalleResponse]


class ResumenSemanalResponse(BaseModel):
    control_id: UUID
    fecha_inicio: date
    fecha_fin: date
    puntos_control: int
    puntos_misiones: int
    puntos_pendientes: int
    puntos_promesas: int
    puntos_limites: int
    puntos_tiros: int
    puntos_total: int
    rango: str


class CategoriaCreate(BaseModel):
    nombre: CategoriaGastoNombre
    descripcion: str | None = Field(default=None, max_length=1000)


class CategoriaResponse(BaseModel):
    id: UUID
    nombre: CategoriaGastoNombre
    descripcion: str | None
    is_active: bool


class TipoGastoCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    categoria_id: UUID
    descripcion: str | None = Field(default=None, max_length=1000)


class TipoGastoResponse(BaseModel):
    id: UUID
    nombre: str
    categoria_id: UUID
    categoria: CategoriaGastoNombre
    descripcion: str | None
    is_active: bool


class ControlGastoSemanalCreate(BaseModel):
    fecha_inicio: date
    fecha_fin: date
    limite_gasto: Decimal = Field(ge=0, max_digits=14, decimal_places=2)

    @model_validator(mode="after")
    def validar_periodo(self) -> "ControlGastoSemanalCreate":
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha de inicio no puede ser posterior a la fecha fin.")
        return self


class ControlGastoMensualCreate(BaseModel):
    anio: int = Field(ge=1)
    mes: int = Field(ge=1, le=12)
    presupuesto: Decimal = Field(ge=0, max_digits=14, decimal_places=2)


class ControlGastoResponse(BaseModel):
    id: UUID
    saldo: Decimal


class ControlGastoDetalleResponse(BaseModel):
    id: UUID
    fecha_inicio: date
    fecha_fin: date
    limite_gasto: Decimal
    saldo: Decimal


class GastoCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=200)
    importe: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    tipo_gasto_id: UUID
    fecha_hora: datetime
    descripcion: str | None = Field(default=None, max_length=1000)
    puntaje_generado: int = Field(default=0, ge=-2_147_483_648, le=2_147_483_647)


class GastoResponse(BaseModel):
    id: UUID
    nombre: str
    importe: Decimal
    tipo_gasto_id: UUID
    fecha_hora: datetime


class GastoListadoResponse(GastoResponse):
    tipo_gasto: str
    categoria: CategoriaGastoNombre
    descripcion: str | None = None
    puntaje_generado: int = 0


class ResumenGastoResponse(BaseModel):
    control_id: UUID
    total_gastado: Decimal
    limite_o_presupuesto: Decimal
    saldo: Decimal
    porcentaje_consumido: Decimal
    excedido: bool


class MovimientoCreate(BaseModel):
    puntos: int = Field(ge=-2_147_483_648, le=2_147_483_647)
    origen: OrigenPuntaje
    motivo: str = Field(min_length=1, max_length=500)
    tipo: TipoMovimientoPuntaje
    referencia_id: UUID | None = None
    fecha_hora: datetime | None = None


class MovimientoResponse(BaseModel):
    id: UUID
    puntos: int
    origen: OrigenPuntaje
    motivo: str
    tipo: TipoMovimientoPuntaje
    fecha_hora: datetime


class ResumenPuntajeResponse(BaseModel):
    total_puntos: int
    movimientos: int
    rango: str
