"""Adaptadores SQLAlchemy para PostgreSQL."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import TypeVar
from uuid import UUID

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, joinedload, selectinload, sessionmaker

from app.application.ports import Repository
from app.domain.finanzas import (
    CategoriaTipoGasto,
    ControlGastoMensual,
    ControlGastoSemanal,
    Gasto,
    TipoGasto,
)
from app.domain.gamificacion import MovimientoPuntaje, OrigenPuntaje, TipoMovimientoPuntaje
from app.domain.productividad import (
    ControlDiario,
    ControlSemanal,
    EstadoActividad,
    Objetivo,
    TareaControl,
    TipoObjetivo,
)

from .postgres_models import (
    Base,
    CategoriaTipoGastoModel,
    ControlDiarioModel,
    ControlGastoMensualModel,
    ControlGastoSemanalModel,
    ControlSemanalModel,
    GastoModel,
    MovimientoPuntajeModel,
    ObjetivoModel,
    TareaControlModel,
    TipoGastoModel,
)

T = TypeVar("T")


def create_engine_and_session_factory(database_url: str):
    engine = create_engine(database_url, pool_pre_ping=True, future=True)
    return engine, sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_database(engine) -> None:
    Base.metadata.create_all(engine)
    if engine.dialect.name == "postgresql":
        _ensure_postgres_constraints(engine)


def _ensure_postgres_constraints(engine) -> None:
    """Aplica restricciones nuevas también a volúmenes creados previamente.

    ``create_all`` no modifica tablas existentes. Esta capa idempotente evita
    que el volumen local de Docker quede sin las mismas garantías que una
    instalación nueva mientras se incorpora un sistema formal de migraciones.
    """
    constraints = (
        ("controles_semanales", "ck_controles_semanales_fechas", "fecha_inicio <= fecha_fin"),
        ("controles_diarios", "ck_controles_diarios_puntos_base", "puntos_base >= 0"),
        (
            "controles_diarios",
            "ck_controles_diarios_penalizacion",
            "penalizacion_incumplimiento >= 0",
        ),
        ("controles_diarios", "ck_controles_diarios_bono", "bono_sobrecarga >= 0"),
        (
            "tareas_control",
            "ck_tareas_control_estado",
            "estado IN ('pendiente', 'cumplida', 'incumplida', 'cancelada')",
        ),
        (
            "objetivos",
            "ck_objetivos_tipo",
            "tipo IN ('mision', 'pendiente', 'promesa', 'limite', 'tiro')",
        ),
        (
            "objetivos",
            "ck_objetivos_estado",
            "estado IN ('pendiente', 'cumplida', 'incumplida', 'cancelada')",
        ),
        (
            "controles_gasto_semanales",
            "ck_controles_gasto_semanales_fechas",
            "fecha_inicio <= fecha_fin",
        ),
        (
            "controles_gasto_semanales",
            "ck_controles_gasto_semanales_limite",
            "limite_gasto >= 0",
        ),
        ("controles_gasto_mensuales", "ck_controles_gasto_mensuales_anio", "anio >= 1"),
        (
            "controles_gasto_mensuales",
            "ck_controles_gasto_mensuales_mes",
            "mes BETWEEN 1 AND 12",
        ),
        (
            "controles_gasto_mensuales",
            "ck_controles_gasto_mensuales_presupuesto",
            "presupuesto >= 0",
        ),
        ("gastos", "ck_gastos_importe_positivo", "importe > 0"),
        (
            "gastos",
            "ck_gastos_un_control",
            "(control_gasto_semanal_id IS NOT NULL AND control_gasto_mensual_id IS NULL) "
            "OR (control_gasto_semanal_id IS NULL AND control_gasto_mensual_id IS NOT NULL)",
        ),
        (
            "movimientos_puntaje",
            "ck_movimientos_puntaje_signo",
            "(tipo = 'bonificacion' AND puntos >= 0) OR "
            "(tipo = 'penalizacion' AND puntos <= 0)",
        ),
        (
            "movimientos_puntaje",
            "ck_movimientos_puntaje_origen",
            "origen IN ('control', 'mision', 'pendiente', 'promesa', 'limite', 'tiro', 'gasto', 'sobrecarga')",
        ),
        (
            "movimientos_puntaje",
            "ck_movimientos_puntaje_tipo",
            "tipo IN ('bonificacion', 'penalizacion')",
        ),
    )
    with engine.begin() as connection:
        for table, name, expression in constraints:
            connection.execute(
                text(
                    "DO $$ BEGIN "
                    f"IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '{name}') THEN "
                    f"ALTER TABLE {table} ADD CONSTRAINT {name} CHECK ({expression}); "
                    "END IF; END $$;"
                )
            )
        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "uq_controles_gasto_mensuales_periodo_idx "
                "ON controles_gasto_mensuales (anio, mes)"
            )
        )
        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "uq_controles_diarios_semana_fecha_idx "
                "ON controles_diarios (control_semanal_id, fecha)"
            )
        )
        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "uq_controles_semanales_periodo_idx "
                "ON controles_semanales (fecha_inicio, fecha_fin)"
            )
        )
        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "uq_controles_gasto_semanales_periodo_idx "
                "ON controles_gasto_semanales (fecha_inicio, fecha_fin)"
            )
        )


def database_is_ready(session_factory: Callable[[], Session]) -> bool:
    with session_factory() as session:
        session.execute(text("SELECT 1"))
    return True


class SqlAlchemyRepository(Repository[T]):
    """Base para repositorios que abren una sesión por operación."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self.session_factory = session_factory


class SqlAlchemyControlSemanalRepository(SqlAlchemyRepository[ControlSemanal]):
    def save(self, entity: ControlSemanal) -> ControlSemanal:
        with self.session_factory() as session:
            _upsert_control_semanal(session, entity)
            session.commit()
        return entity

    def get(self, entity_id: UUID) -> ControlSemanal | None:
        with self.session_factory() as session:
            stmt = (
                select(ControlSemanalModel)
                .where(ControlSemanalModel.id == entity_id)
                .options(
                    selectinload(ControlSemanalModel.controles_diarios).selectinload(
                        ControlDiarioModel.tareas
                    ),
                    selectinload(ControlSemanalModel.objetivos),
                )
            )
            model = session.scalar(stmt)
            return None if model is None else _control_semanal_to_domain(model)

    def list(self) -> list[ControlSemanal]:
        with self.session_factory() as session:
            models = session.scalars(
                select(ControlSemanalModel).options(
                    selectinload(ControlSemanalModel.controles_diarios).selectinload(
                        ControlDiarioModel.tareas
                    ),
                    selectinload(ControlSemanalModel.objetivos),
                )
            ).all()
            return [_control_semanal_to_domain(model) for model in models]

    def delete(self, entity_id: UUID) -> None:
        with self.session_factory() as session:
            model = session.get(ControlSemanalModel, entity_id)
            if model is not None:
                session.delete(model)
                session.commit()


class SqlAlchemyControlGastoSemanalRepository(SqlAlchemyRepository[ControlGastoSemanal]):
    def save(self, entity: ControlGastoSemanal) -> ControlGastoSemanal:
        with self.session_factory() as session:
            model = session.get(ControlGastoSemanalModel, entity.id)
            if model is None:
                model = ControlGastoSemanalModel(id=entity.id)
            model.fecha_inicio = entity.fecha_inicio
            model.fecha_fin = entity.fecha_fin
            model.limite_gasto = entity.limite_gasto
            session.add(model)
            for gasto in entity.gastos:
                _save_gasto(session, gasto, semanal_id=entity.id)
            session.commit()
        return entity

    def get(self, entity_id: UUID) -> ControlGastoSemanal | None:
        with self.session_factory() as session:
            stmt = select(ControlGastoSemanalModel).where(
                ControlGastoSemanalModel.id == entity_id
            )
            model = session.scalar(stmt)
            if model is None:
                return None
            return _control_gasto_semanal_to_domain(model)

    def list(self) -> list[ControlGastoSemanal]:
        with self.session_factory() as session:
            models = session.scalars(select(ControlGastoSemanalModel)).all()
            return [_control_gasto_semanal_to_domain(model) for model in models]

    def delete(self, entity_id: UUID) -> None:
        with self.session_factory() as session:
            model = session.get(ControlGastoSemanalModel, entity_id)
            if model is not None:
                session.delete(model)
                session.commit()


class SqlAlchemyControlGastoMensualRepository(SqlAlchemyRepository[ControlGastoMensual]):
    def save(self, entity: ControlGastoMensual) -> ControlGastoMensual:
        with self.session_factory() as session:
            model = session.get(ControlGastoMensualModel, entity.id)
            if model is None:
                model = ControlGastoMensualModel(id=entity.id)
            model.anio = entity.anio
            model.mes = entity.mes
            model.presupuesto = entity.presupuesto
            session.add(model)
            for gasto in entity.gastos:
                _save_gasto(session, gasto, mensual_id=entity.id)
            session.commit()
        return entity

    def get(self, entity_id: UUID) -> ControlGastoMensual | None:
        with self.session_factory() as session:
            model = session.get(ControlGastoMensualModel, entity_id)
            return None if model is None else _control_gasto_mensual_to_domain(model)

    def list(self) -> list[ControlGastoMensual]:
        with self.session_factory() as session:
            models = session.scalars(select(ControlGastoMensualModel)).all()
            return [_control_gasto_mensual_to_domain(model) for model in models]

    def delete(self, entity_id: UUID) -> None:
        with self.session_factory() as session:
            model = session.get(ControlGastoMensualModel, entity_id)
            if model is not None:
                session.delete(model)
                session.commit()


class SqlAlchemyCategoriaTipoGastoRepository(SqlAlchemyRepository[CategoriaTipoGasto]):
    def save(self, entity: CategoriaTipoGasto) -> CategoriaTipoGasto:
        with self.session_factory() as session:
            session.merge(_categoria_to_model(entity))
            session.commit()
        return entity

    def get(self, entity_id: UUID) -> CategoriaTipoGasto | None:
        with self.session_factory() as session:
            model = session.get(CategoriaTipoGastoModel, entity_id)
            return None if model is None else _categoria_to_domain(model)

    def list(self) -> list[CategoriaTipoGasto]:
        with self.session_factory() as session:
            return [_categoria_to_domain(model) for model in session.scalars(select(CategoriaTipoGastoModel)).all()]

    def delete(self, entity_id: UUID) -> None:
        with self.session_factory() as session:
            model = session.get(CategoriaTipoGastoModel, entity_id)
            if model is not None:
                session.delete(model)
                session.commit()


class SqlAlchemyTipoGastoRepository(SqlAlchemyRepository[TipoGasto]):
    def save(self, entity: TipoGasto) -> TipoGasto:
        with self.session_factory() as session:
            session.merge(_tipo_to_model(entity))
            session.commit()
        return entity

    def get(self, entity_id: UUID) -> TipoGasto | None:
        with self.session_factory() as session:
            model = session.scalar(
                select(TipoGastoModel)
                .where(TipoGastoModel.id == entity_id)
                .options(joinedload(TipoGastoModel.categoria))
            )
            return None if model is None else _tipo_to_domain(model)

    def list(self) -> list[TipoGasto]:
        with self.session_factory() as session:
            models = session.scalars(
                select(TipoGastoModel).options(joinedload(TipoGastoModel.categoria))
            ).all()
            return [_tipo_to_domain(model) for model in models]

    def delete(self, entity_id: UUID) -> None:
        with self.session_factory() as session:
            model = session.get(TipoGastoModel, entity_id)
            if model is not None:
                session.delete(model)
                session.commit()


class SqlAlchemyMovimientoPuntajeRepository(SqlAlchemyRepository[MovimientoPuntaje]):
    def save(self, entity: MovimientoPuntaje) -> MovimientoPuntaje:
        with self.session_factory() as session:
            session.merge(_movimiento_to_model(entity))
            session.commit()
        return entity

    def get(self, entity_id: UUID) -> MovimientoPuntaje | None:
        with self.session_factory() as session:
            model = session.get(MovimientoPuntajeModel, entity_id)
            return None if model is None else _movimiento_to_domain(model)

    def list(self) -> list[MovimientoPuntaje]:
        with self.session_factory() as session:
            models = session.scalars(select(MovimientoPuntajeModel)).all()
            return [_movimiento_to_domain(model) for model in models]

    def delete(self, entity_id: UUID) -> None:
        with self.session_factory() as session:
            model = session.get(MovimientoPuntajeModel, entity_id)
            if model is not None:
                session.delete(model)
                session.commit()


def _control_semanal_to_model(entity: ControlSemanal) -> ControlSemanalModel:
    model = ControlSemanalModel(
        id=entity.id,
        fecha_inicio=entity.fecha_inicio,
        fecha_fin=entity.fecha_fin,
    )
    model.controles_diarios = [_control_diario_to_model(control) for control in entity.controles_diarios]
    model.objetivos = [_objetivo_to_model(objetivo) for objetivo in entity.objetivos]
    return model


def _upsert_control_semanal(session: Session, entity: ControlSemanal) -> None:
    """Actualiza un agregado sin borrar hijos que otra solicitud haya creado.

    ``merge`` sobre una colección completa interpreta la fotografía del objeto
    como verdad absoluta. Dos solicitudes que leen la misma semana y agregan
    tareas distintas podían eliminarse mutuamente. Los hijos se actualizan por
    identidad y los que no vienen en la fotografía se conservan; las bajas
    deben hacerse mediante una operación explícita.
    """
    model = session.get(ControlSemanalModel, entity.id)
    if model is None:
        model = ControlSemanalModel(id=entity.id)
        session.add(model)
    model.fecha_inicio = entity.fecha_inicio
    model.fecha_fin = entity.fecha_fin
    session.flush()

    for control in entity.controles_diarios:
        diario = session.get(ControlDiarioModel, control.id)
        if diario is None:
            diario = session.scalar(
                select(ControlDiarioModel).where(
                    ControlDiarioModel.control_semanal_id == entity.id,
                    ControlDiarioModel.fecha == control.fecha,
                )
            )
        if diario is None:
            diario = ControlDiarioModel(id=control.id)
            session.add(diario)
        diario.control_semanal_id = entity.id
        diario.fecha = control.fecha
        diario.puntos_base = control.puntos_base
        diario.penalizacion_incumplimiento = control.penalizacion_incumplimiento
        diario.bono_sobrecarga = control.bono_sobrecarga
        session.flush()
        for tarea in control.tareas:
            tarea_model = session.get(TareaControlModel, tarea.id)
            if tarea_model is None:
                tarea_model = TareaControlModel(id=tarea.id)
                session.add(tarea_model)
            tarea_model.control_diario_id = control.id
            tarea_model.nombre = tarea.nombre
            tarea_model.fecha_programada = tarea.fecha_programada
            tarea_model.estado = tarea.estado.value
            tarea_model.es_sobrecarga = tarea.es_sobrecarga
            tarea_model.descripcion = tarea.descripcion

    for objetivo in entity.objetivos:
        objetivo_model = session.get(ObjetivoModel, objetivo.id)
        if objetivo_model is None:
            objetivo_model = ObjetivoModel(id=objetivo.id)
            session.add(objetivo_model)
        objetivo_model.control_semanal_id = entity.id
        objetivo_model.nombre = objetivo.nombre
        objetivo_model.tipo = objetivo.tipo.value
        objetivo_model.puntos_cumplimiento = objetivo.puntos_cumplimiento
        objetivo_model.puntos_incumplimiento = objetivo.puntos_incumplimiento
        objetivo_model.estado = objetivo.estado.value
        objetivo_model.fecha_inicio = objetivo.fecha_inicio
        objetivo_model.fecha_limite = objetivo.fecha_limite
        objetivo_model.descripcion = objetivo.descripcion
        objetivo_model.is_active = objetivo.is_active


def _control_diario_to_model(entity: ControlDiario) -> ControlDiarioModel:
    model = ControlDiarioModel(
        id=entity.id,
        fecha=entity.fecha,
        puntos_base=entity.puntos_base,
        penalizacion_incumplimiento=entity.penalizacion_incumplimiento,
        bono_sobrecarga=entity.bono_sobrecarga,
    )
    model.tareas = [_tarea_to_model(tarea) for tarea in entity.tareas]
    return model


def _tarea_to_model(entity: TareaControl) -> TareaControlModel:
    return TareaControlModel(
        id=entity.id,
        nombre=entity.nombre,
        fecha_programada=entity.fecha_programada,
        estado=entity.estado.value,
        es_sobrecarga=entity.es_sobrecarga,
        descripcion=entity.descripcion,
    )


def _objetivo_to_model(entity: Objetivo) -> ObjetivoModel:
    return ObjetivoModel(
        id=entity.id,
        nombre=entity.nombre,
        tipo=entity.tipo.value,
        puntos_cumplimiento=entity.puntos_cumplimiento,
        puntos_incumplimiento=entity.puntos_incumplimiento,
        estado=entity.estado.value,
        fecha_inicio=entity.fecha_inicio,
        fecha_limite=entity.fecha_limite,
        descripcion=entity.descripcion,
        is_active=entity.is_active,
    )


def _control_semanal_to_domain(model: ControlSemanalModel) -> ControlSemanal:
    return ControlSemanal(
        fecha_inicio=model.fecha_inicio,
        fecha_fin=model.fecha_fin,
        controles_diarios=[_control_diario_to_domain(item) for item in model.controles_diarios],
        objetivos=[_objetivo_to_domain(item) for item in model.objetivos],
        id=model.id,
    )


def _control_diario_to_domain(model: ControlDiarioModel) -> ControlDiario:
    return ControlDiario(
        fecha=model.fecha,
        tareas=[_tarea_to_domain(item) for item in model.tareas],
        puntos_base=model.puntos_base,
        penalizacion_incumplimiento=model.penalizacion_incumplimiento,
        bono_sobrecarga=model.bono_sobrecarga,
        id=model.id,
    )


def _tarea_to_domain(model: TareaControlModel) -> TareaControl:
    return TareaControl(
        nombre=model.nombre,
        fecha_programada=model.fecha_programada,
        estado=EstadoActividad(model.estado),
        es_sobrecarga=model.es_sobrecarga,
        descripcion=model.descripcion,
        id=model.id,
    )


def _objetivo_to_domain(model: ObjetivoModel) -> Objetivo:
    return Objetivo(
        nombre=model.nombre,
        tipo=TipoObjetivo(model.tipo),
        puntos_cumplimiento=model.puntos_cumplimiento,
        puntos_incumplimiento=model.puntos_incumplimiento,
        estado=EstadoActividad(model.estado),
        fecha_inicio=model.fecha_inicio,
        fecha_limite=model.fecha_limite,
        descripcion=model.descripcion,
        is_active=model.is_active,
        id=model.id,
    )


def _categoria_to_model(entity: CategoriaTipoGasto) -> CategoriaTipoGastoModel:
    return CategoriaTipoGastoModel(
        id=entity.id,
        nombre=entity.nombre.value,
        descripcion=entity.descripcion,
        is_active=entity.is_active,
    )


def _categoria_to_domain(model: CategoriaTipoGastoModel) -> CategoriaTipoGasto:
    from app.domain.finanzas import CategoriaGastoNombre

    return CategoriaTipoGasto(
        nombre=CategoriaGastoNombre(model.nombre),
        descripcion=model.descripcion,
        is_active=model.is_active,
        id=model.id,
    )


def _tipo_to_model(entity: TipoGasto) -> TipoGastoModel:
    return TipoGastoModel(
        id=entity.id,
        nombre=entity.nombre,
        categoria_id=entity.categoria.id,
        descripcion=entity.descripcion,
        is_active=entity.is_active,
    )


def _tipo_to_domain(model: TipoGastoModel) -> TipoGasto:
    return TipoGasto(
        nombre=model.nombre,
        categoria=_categoria_to_domain(model.categoria),
        descripcion=model.descripcion,
        is_active=model.is_active,
        id=model.id,
    )


def _save_gasto(
    session: Session,
    entity: Gasto,
    *,
    semanal_id: UUID | None = None,
    mensual_id: UUID | None = None,
) -> None:
    session.merge(_categoria_to_model(entity.tipo_gasto.categoria))
    session.merge(_tipo_to_model(entity.tipo_gasto))
    model = session.get(GastoModel, entity.id) or GastoModel(id=entity.id)
    model.nombre = entity.nombre
    model.importe = entity.importe
    model.tipo_gasto_id = entity.tipo_gasto.id
    model.fecha_hora = entity.fecha_hora
    model.descripcion = entity.descripcion
    model.puntaje_generado = entity.puntaje_generado
    model.is_active = entity.is_active
    if semanal_id is not None:
        model.control_gasto_semanal_id = semanal_id
    if mensual_id is not None:
        model.control_gasto_mensual_id = mensual_id
    session.add(model)


def _gasto_to_domain(model: GastoModel) -> Gasto:
    return Gasto(
        nombre=model.nombre,
        importe=model.importe,
        tipo_gasto=_tipo_to_domain(model.tipo_gasto),
        fecha_hora=model.fecha_hora,
        descripcion=model.descripcion,
        puntaje_generado=model.puntaje_generado,
        is_active=model.is_active,
        id=model.id,
    )


def _control_gasto_semanal_to_domain(model: ControlGastoSemanalModel) -> ControlGastoSemanal:
    return ControlGastoSemanal(
        fecha_inicio=model.fecha_inicio,
        fecha_fin=model.fecha_fin,
        limite_gasto=model.limite_gasto,
        gastos=[_gasto_to_domain(item) for item in model.gastos],
        id=model.id,
    )


def _control_gasto_mensual_to_domain(model: ControlGastoMensualModel) -> ControlGastoMensual:
    return ControlGastoMensual(
        anio=model.anio,
        mes=model.mes,
        presupuesto=model.presupuesto,
        gastos=[_gasto_to_domain(item) for item in model.gastos],
        id=model.id,
    )


def _movimiento_to_model(entity: MovimientoPuntaje) -> MovimientoPuntajeModel:
    return MovimientoPuntajeModel(
        id=entity.id,
        puntos=entity.puntos,
        origen=entity.origen.value,
        motivo=entity.motivo,
        fecha_hora=entity.fecha_hora,
        tipo=entity.tipo.value,
        referencia_id=entity.referencia_id,
    )


def _movimiento_to_domain(model: MovimientoPuntajeModel) -> MovimientoPuntaje:
    return MovimientoPuntaje(
        puntos=model.puntos,
        origen=OrigenPuntaje(model.origen),
        motivo=model.motivo,
        fecha_hora=model.fecha_hora,
        tipo=TipoMovimientoPuntaje(model.tipo),
        referencia_id=model.referencia_id,
        id=model.id,
    )
