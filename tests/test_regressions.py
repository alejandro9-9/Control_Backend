from datetime import date, datetime, timezone
from decimal import Decimal
from unittest import TestCase

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.domain import (
    CategoriaGastoNombre,
    CategoriaTipoGasto,
    ControlGastoMensual,
    ControlGastoSemanal,
    Gasto,
    TipoGasto,
)
from app.domain.gamificacion import (
    MovimientoPuntaje,
    NombreRango,
    OrigenPuntaje,
    TipoMovimientoPuntaje,
    obtener_rango,
)
from app.domain.productividad import (
    ControlDiario,
    ControlSemanal,
    EstadoActividad,
    Objetivo,
    TipoObjetivo,
    TareaControl,
)
from app.infrastructure.postgres import SqlAlchemyControlSemanalRepository, init_database


class RegressionTests(TestCase):
    def test_negative_score_uses_lowest_rank(self) -> None:
        self.assertEqual(obtener_rango(-1).nombre, NombreRango.DESPOJO_HUMANO)

    def test_movement_type_normalizes_sign(self) -> None:
        bonus = MovimientoPuntaje(
            5,
            OrigenPuntaje.CONTROL,
            "bono",
            datetime.now(timezone.utc),
            TipoMovimientoPuntaje.BONIFICACION,
        )
        penalty = MovimientoPuntaje(
            5,
            OrigenPuntaje.CONTROL,
            "penalización",
            datetime.now(timezone.utc),
            TipoMovimientoPuntaje.PENALIZACION,
        )
        self.assertEqual(bonus.puntos, 5)
        self.assertEqual(penalty.puntos, -5)

    def test_finance_uses_business_date_after_utc_normalization(self) -> None:
        tipo = TipoGasto("Comida", CategoriaTipoGasto(CategoriaGastoNombre.BUENO))
        gasto = Gasto(
            "Cena",
            Decimal("10.00"),
            tipo,
            datetime.fromisoformat("2026-10-01T23:30:00-05:00"),
        )
        weekly = ControlGastoSemanal(date(2026, 10, 1), date(2026, 10, 1), Decimal("100"))
        monthly = ControlGastoMensual(2026, 10, Decimal("100"))
        weekly.registrar_gasto(gasto)
        monthly.registrar_gasto(gasto)
        self.assertEqual(gasto.fecha_operativa(), date(2026, 10, 1))

    def test_concurrent_weekly_updates_preserve_both_children(self) -> None:
        engine = create_engine(
            "sqlite+pysqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        init_database(engine)
        session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        repository = SqlAlchemyControlSemanalRepository(session_factory)

        original = repository.save(ControlSemanal(date(2026, 1, 1), date(2026, 1, 7)))
        first = repository.get(original.id)
        second = repository.get(original.id)
        first_day = ControlDiario(date(2026, 1, 1))
        first_day.agregar_tarea(TareaControl("A", date(2026, 1, 1)))
        first.agregar_control_diario(first_day)
        repository.save(first)
        second_day = ControlDiario(date(2026, 1, 2))
        second_day.agregar_tarea(TareaControl("B", date(2026, 1, 2)))
        second.agregar_control_diario(second_day)
        repository.save(second)

        final = repository.get(original.id)
        self.assertEqual(
            {task.nombre for daily in final.controles_diarios for task in daily.tareas},
            {"A", "B"},
        )

    def test_objective_dates_must_belong_to_week(self) -> None:
        week = ControlSemanal(date(2026, 1, 5), date(2026, 1, 11))
        objective = Objetivo(
            "Fuera de periodo",
            TipoObjetivo.MISION,
            5,
            -2,
            fecha_inicio=date(2026, 1, 12),
        )
        with self.assertRaises(ValueError):
            week.agregar_objetivo(objective)

    def test_week_must_cover_seven_days(self) -> None:
        with self.assertRaises(ValueError):
            ControlSemanal(date(2026, 1, 5), date(2026, 1, 10))

    def test_daily_control_cannot_be_duplicated_for_same_date(self) -> None:
        week = ControlSemanal(date(2026, 1, 5), date(2026, 1, 11))
        week.agregar_control_diario(ControlDiario(date(2026, 1, 5)))
        with self.assertRaises(ValueError):
            week.agregar_control_diario(ControlDiario(date(2026, 1, 5)))

    def test_cancelled_items_do_not_contribute_to_scores_or_expenses(self) -> None:
        week = ControlSemanal(date(2026, 1, 5), date(2026, 1, 11))
        objective = Objetivo(
            "Actividad cancelada",
            TipoObjetivo.MISION,
            10,
            -2,
            estado=EstadoActividad.CANCELADA,
        )
        week.agregar_objetivo(objective)
        self.assertEqual(week.calcular_puntaje_total(), 0)

        tipo = TipoGasto("Comida", CategoriaTipoGasto(CategoriaGastoNombre.BUENO))
        expense = Gasto("Compra anulada", Decimal("25.00"), tipo, datetime(2026, 1, 5, 10))
        expense.is_active = False
        control = ControlGastoSemanal(date(2026, 1, 5), date(2026, 1, 11), Decimal("100"), [expense])
        self.assertEqual(control.total_gastado(), Decimal("0"))


if __name__ == "__main__":
    import unittest

    unittest.main()
