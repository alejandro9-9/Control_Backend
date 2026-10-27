from datetime import date, datetime
from decimal import Decimal
import unittest

from app.domain import (
    CategoriaGastoNombre,
    CategoriaTipoGasto,
    EstadoActividad,
    TipoGasto,
    TipoObjetivo,
)
from app.domain.gamificacion import OrigenPuntaje, TipoMovimientoPuntaje
from app.infrastructure import build_container


class ApplicationFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.container = build_container()

    def test_productividad_calcula_resumen_semanal(self) -> None:
        semana = self.container.crear_control_semanal.execute(
            date(2026, 9, 21), date(2026, 9, 27)
        )
        tarea = self.container.agregar_tarea.execute(
            semana.id,
            "Terminar tareas Cibertec",
            date(2026, 9, 25),
            estado=EstadoActividad.INCUMPLIDA,
        )
        self.container.agregar_tarea.execute(
            semana.id,
            "Estudiar Python extra",
            date(2026, 9, 25),
            estado=EstadoActividad.CUMPLIDA,
            es_sobrecarga=True,
        )
        self.container.agregar_objetivo.execute(
            semana.id,
            "Vender un teléfono",
            TipoObjetivo.MISION,
            5,
            -2,
            estado=EstadoActividad.CUMPLIDA,
        )

        resumen = self.container.obtener_resumen_semanal.execute(semana.id)
        self.assertEqual(resumen.puntos_total, 11)
        self.assertEqual(resumen.rango.value, "DESPOJO HUMANO")

        self.container.actualizar_estado_tarea.execute(
            semana.id, tarea.id, EstadoActividad.CUMPLIDA
        )
        self.assertEqual(
            self.container.obtener_resumen_semanal.execute(semana.id).puntos_total,
            13,
        )

    def test_finanzas_calcula_saldo_y_porcentaje(self) -> None:
        categoria = CategoriaTipoGasto(CategoriaGastoNombre.BUENO)
        tipo = TipoGasto("Estudios", categoria)
        semanal = self.container.crear_control_gasto_semanal.execute(
            date(2026, 9, 21), date(2026, 9, 27), Decimal("100")
        )
        mensual = self.container.crear_control_gasto_mensual.execute(
            2026, 9, Decimal("200")
        )

        self.container.registrar_gasto_semanal.execute(
            semanal.id,
            "Curso",
            Decimal("50"),
            tipo,
            datetime(2026, 9, 25, 10),
        )
        self.container.registrar_gasto_mensual.execute(
            mensual.id,
            "Curso",
            Decimal("50"),
            tipo,
            datetime(2026, 9, 25, 10),
        )

        resumen_semanal = self.container.obtener_resumen_gasto_semanal.execute(
            semanal.id
        )
        resumen_mensual = self.container.obtener_resumen_gasto_mensual.execute(
            mensual.id
        )
        self.assertEqual(resumen_semanal.saldo, Decimal("50"))
        self.assertEqual(resumen_mensual.porcentaje_consumido, Decimal("25"))

    def test_gamificacion_conserva_movimientos_signed(self) -> None:
        self.container.registrar_movimiento_puntaje.execute(
            7,
            OrigenPuntaje.CONTROL,
            "Base del día",
            TipoMovimientoPuntaje.BONIFICACION,
        )
        self.container.registrar_movimiento_puntaje.execute(
            -2,
            OrigenPuntaje.CONTROL,
            "Incumplimiento",
            TipoMovimientoPuntaje.PENALIZACION,
        )

        resumen = self.container.obtener_resumen_puntaje.execute()
        self.assertEqual(resumen.total_puntos, 5)
        self.assertEqual(resumen.movimientos, 2)


if __name__ == "__main__":
    unittest.main()
