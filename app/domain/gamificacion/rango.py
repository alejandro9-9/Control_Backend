from __future__ import annotations

from dataclasses import dataclass

from .enums import NombreRango


@dataclass(frozen=True)
class Rango:
    nombre: NombreRango
    minimo: int
    maximo: int | None

    def __post_init__(self) -> None:
        if self.maximo is not None and self.minimo > self.maximo:
            raise ValueError("El mínimo del rango no puede superar al máximo.")

    def contiene(self, puntaje: int | float) -> bool:
        if puntaje < self.minimo:
            return False
        if self.maximo is None:
            return True
        return puntaje <= self.maximo


RANGOS = [
    Rango(NombreRango.DESPOJO_HUMANO, minimo=0, maximo=79),
    Rango(NombreRango.MEDIOCRE, minimo=80, maximo=130),
    Rango(NombreRango.PELEADOR, minimo=131, maximo=148),
    Rango(NombreRango.EL_MEJOR, minimo=149, maximo=159),
    Rango(NombreRango.INDISCUTIBLE, minimo=160, maximo=199),
    Rango(NombreRango.DEIDAD, minimo=200, maximo=None),
]


def obtener_rango(puntaje: int | float) -> Rango:
    # Los incumplimientos y penalizaciones pueden dejar temporalmente el
    # puntaje por debajo de cero. En ese caso corresponde al rango más bajo.
    if puntaje < RANGOS[0].minimo:
        return RANGOS[0]
    for rango in RANGOS:
        if rango.contiene(puntaje):
            return rango
    raise ValueError(f"No existe rango para el puntaje {puntaje}.")
