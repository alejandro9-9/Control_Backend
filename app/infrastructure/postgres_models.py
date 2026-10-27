"""Modelos SQLAlchemy para PostgreSQL."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ControlSemanalModel(Base):
    __tablename__ = "controles_semanales"
    __table_args__ = (
        UniqueConstraint(
            "fecha_inicio",
            "fecha_fin",
            name="uq_controles_semanales_periodo",
        ),
        CheckConstraint("fecha_inicio <= fecha_fin", name="ck_controles_semanales_fechas"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    controles_diarios: Mapped[list["ControlDiarioModel"]] = relationship(
        back_populates="control_semanal",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ControlDiarioModel.fecha",
    )
    objetivos: Mapped[list["ObjetivoModel"]] = relationship(
        back_populates="control_semanal",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ControlDiarioModel(Base):
    __tablename__ = "controles_diarios"
    __table_args__ = (
        UniqueConstraint(
            "control_semanal_id",
            "fecha",
            name="uq_controles_diarios_semana_fecha",
        ),
        CheckConstraint("puntos_base >= 0", name="ck_controles_diarios_puntos_base"),
        CheckConstraint(
            "penalizacion_incumplimiento >= 0",
            name="ck_controles_diarios_penalizacion",
        ),
        CheckConstraint("bono_sobrecarga >= 0", name="ck_controles_diarios_bono"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    control_semanal_id: Mapped[UUID] = mapped_column(
        ForeignKey("controles_semanales.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    puntos_base: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    penalizacion_incumplimiento: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    bono_sobrecarga: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    control_semanal: Mapped[ControlSemanalModel] = relationship(back_populates="controles_diarios")
    tareas: Mapped[list["TareaControlModel"]] = relationship(
        back_populates="control_diario",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="TareaControlModel.fecha_programada, TareaControlModel.nombre",
    )


class TareaControlModel(Base):
    __tablename__ = "tareas_control"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('pendiente', 'cumplida', 'incumplida', 'cancelada')",
            name="ck_tareas_control_estado",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    control_diario_id: Mapped[UUID] = mapped_column(
        ForeignKey("controles_diarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    fecha_programada: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    es_sobrecarga: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    descripcion: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    control_diario: Mapped[ControlDiarioModel] = relationship(back_populates="tareas")


class ObjetivoModel(Base):
    __tablename__ = "objetivos"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('mision', 'pendiente', 'promesa', 'limite', 'tiro')",
            name="ck_objetivos_tipo",
        ),
        CheckConstraint(
            "estado IN ('pendiente', 'cumplida', 'incumplida', 'cancelada')",
            name="ck_objetivos_estado",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    control_semanal_id: Mapped[UUID] = mapped_column(
        ForeignKey("controles_semanales.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    puntos_cumplimiento: Mapped[int] = mapped_column(Integer, nullable=False)
    puntos_incumplimiento: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    fecha_inicio: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    fecha_limite: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    descripcion: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    control_semanal: Mapped[ControlSemanalModel] = relationship(back_populates="objetivos")


class CategoriaTipoGastoModel(Base):
    __tablename__ = "categorias_tipo_gasto"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    descripcion: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    tipos: Mapped[list["TipoGastoModel"]] = relationship(back_populates="categoria")


class TipoGastoModel(Base):
    __tablename__ = "tipos_gasto"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    categoria_id: Mapped[UUID] = mapped_column(
        ForeignKey("categorias_tipo_gasto.id"), nullable=False, index=True
    )
    descripcion: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    categoria: Mapped[CategoriaTipoGastoModel] = relationship(back_populates="tipos")


class ControlGastoSemanalModel(Base):
    __tablename__ = "controles_gasto_semanales"
    __table_args__ = (
        UniqueConstraint(
            "fecha_inicio",
            "fecha_fin",
            name="uq_controles_gasto_semanales_periodo",
        ),
        CheckConstraint(
            "fecha_inicio <= fecha_fin", name="ck_controles_gasto_semanales_fechas"
        ),
        CheckConstraint("limite_gasto >= 0", name="ck_controles_gasto_semanales_limite"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    limite_gasto: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    gastos: Mapped[list["GastoModel"]] = relationship(
        back_populates="control_semanal",
        foreign_keys="GastoModel.control_gasto_semanal_id",
        lazy="selectin",
    )


class ControlGastoMensualModel(Base):
    __tablename__ = "controles_gasto_mensuales"
    __table_args__ = (
        CheckConstraint("anio >= 1", name="ck_controles_gasto_mensuales_anio"),
        CheckConstraint("mes BETWEEN 1 AND 12", name="ck_controles_gasto_mensuales_mes"),
        CheckConstraint("presupuesto >= 0", name="ck_controles_gasto_mensuales_presupuesto"),
        UniqueConstraint("anio", "mes", name="uq_controles_gasto_mensuales_periodo"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)
    presupuesto: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    gastos: Mapped[list["GastoModel"]] = relationship(
        back_populates="control_mensual",
        foreign_keys="GastoModel.control_gasto_mensual_id",
        lazy="selectin",
    )


class GastoModel(Base):
    __tablename__ = "gastos"
    __table_args__ = (
        CheckConstraint("importe > 0", name="ck_gastos_importe_positivo"),
        CheckConstraint(
            "(control_gasto_semanal_id IS NOT NULL AND control_gasto_mensual_id IS NULL) "
            "OR (control_gasto_semanal_id IS NULL AND control_gasto_mensual_id IS NOT NULL)",
            name="ck_gastos_un_control",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    importe: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    tipo_gasto_id: Mapped[UUID] = mapped_column(ForeignKey("tipos_gasto.id"), nullable=False)
    fecha_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    puntaje_generado: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    control_gasto_semanal_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("controles_gasto_semanales.id", ondelete="SET NULL"), nullable=True, index=True
    )
    control_gasto_mensual_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("controles_gasto_mensuales.id", ondelete="SET NULL"), nullable=True, index=True
    )
    tipo_gasto: Mapped[TipoGastoModel] = relationship()
    control_semanal: Mapped[Optional[ControlGastoSemanalModel]] = relationship(
        back_populates="gastos", foreign_keys=[control_gasto_semanal_id]
    )
    control_mensual: Mapped[Optional[ControlGastoMensualModel]] = relationship(
        back_populates="gastos", foreign_keys=[control_gasto_mensual_id]
    )


class MovimientoPuntajeModel(Base):
    __tablename__ = "movimientos_puntaje"
    __table_args__ = (
        CheckConstraint(
            "(tipo = 'bonificacion' AND puntos >= 0) OR "
            "(tipo = 'penalizacion' AND puntos <= 0)",
            name="ck_movimientos_puntaje_signo",
        ),
        CheckConstraint(
            "origen IN ('control', 'mision', 'pendiente', 'promesa', 'limite', "
            "'tiro', 'gasto', 'sobrecarga')",
            name="ck_movimientos_puntaje_origen",
        ),
        CheckConstraint(
            "tipo IN ('bonificacion', 'penalizacion')",
            name="ck_movimientos_puntaje_tipo",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    puntos: Mapped[int] = mapped_column(Integer, nullable=False)
    origen: Mapped[str] = mapped_column(String(30), nullable=False)
    motivo: Mapped[str] = mapped_column(String(500), nullable=False)
    fecha_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    referencia_id: Mapped[Optional[UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
