"""Rutas HTTP del backend."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.dto import ResumenGasto, ResumenPuntaje, ResumenSemanal
from app.domain.finanzas import CategoriaGastoNombre
from app.infrastructure.database import SessionLocal
from app.infrastructure.postgres import database_is_ready
from app.infrastructure.postgres_container import PostgresAppContainer

from .schemas import (
    CategoriaCreate,
    CategoriaResponse,
    ControlGastoDetalleResponse,
    ControlGastoMensualCreate,
    ControlGastoResponse,
    ControlGastoSemanalCreate,
    GastoCreate,
    GastoListadoResponse,
    GastoResponse,
    MovimientoCreate,
    MovimientoResponse,
    ObjetivoCreate,
    ObjetivoResponse,
    ResumenGastoResponse,
    ResumenPuntajeResponse,
    ResumenSemanalResponse,
    SemanaDetalleResponse,
    SemanaCreate,
    SemanaResponse,
    TareaCreate,
    TareaResponse,
    TareaStateUpdate,
    TipoGastoCreate,
    TipoGastoResponse,
)

router = APIRouter(prefix="/api/v1")


def get_container() -> PostgresAppContainer:
    return PostgresAppContainer(SessionLocal)


def _handle_not_found(error: LookupError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))


@router.get("/health")
def health() -> dict[str, str]:
    try:
        database_is_ready(SessionLocal)
    except Exception as error:
        raise HTTPException(status_code=503, detail="Base de datos no disponible") from error
    return {"status": "ok", "database": "ok"}


@router.post("/semanas", response_model=SemanaResponse, status_code=201)
def crear_semana(command: SemanaCreate, container: PostgresAppContainer = Depends(get_container)):
    existing = next(
        (
            item
            for item in container.controles_semanales.list()
            if item.fecha_inicio == command.fecha_inicio and item.fecha_fin == command.fecha_fin
        ),
        None,
    )
    if existing is not None:
        return existing
    try:
        control = container.crear_control_semanal.execute(
            command.fecha_inicio, command.fecha_fin
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return control


@router.get("/semanas", response_model=list[SemanaResponse])
def listar_semanas(container: PostgresAppContainer = Depends(get_container)):
    return container.controles_semanales.list()


@router.post("/semanas/{control_id}/tareas", response_model=TareaResponse, status_code=201)
def agregar_tarea(
    control_id: UUID,
    command: TareaCreate,
    container: PostgresAppContainer = Depends(get_container),
):
    try:
        return container.agregar_tarea.execute(
            control_id,
            command.nombre,
            command.fecha_programada,
            estado=command.estado,
            es_sobrecarga=command.es_sobrecarga,
            descripcion=command.descripcion,
        )
    except LookupError as error:
        raise _handle_not_found(error) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.patch(
    "/semanas/{control_id}/tareas/{tarea_id}",
    response_model=TareaResponse,
)
def actualizar_tarea(
    control_id: UUID,
    tarea_id: UUID,
    command: TareaStateUpdate,
    container: PostgresAppContainer = Depends(get_container),
):
    try:
        return container.actualizar_estado_tarea.execute(control_id, tarea_id, command.estado)
    except LookupError as error:
        raise _handle_not_found(error) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/semanas/{control_id}/objetivos", response_model=ObjetivoResponse, status_code=201)
def agregar_objetivo(
    control_id: UUID,
    command: ObjetivoCreate,
    container: PostgresAppContainer = Depends(get_container),
):
    try:
        objetivo = container.agregar_objetivo.execute(
            control_id,
            command.nombre,
            command.tipo,
            command.puntos_cumplimiento,
            command.puntos_incumplimiento,
            estado=command.estado,
            fecha_inicio=command.fecha_inicio,
            fecha_limite=command.fecha_limite,
            descripcion=command.descripcion,
        )
    except LookupError as error:
        raise _handle_not_found(error) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return objetivo


@router.patch(
    "/semanas/{control_id}/objetivos/{objetivo_id}",
    response_model=ObjetivoResponse,
)
def actualizar_objetivo(
    control_id: UUID,
    objetivo_id: UUID,
    command: TareaStateUpdate,
    container: PostgresAppContainer = Depends(get_container),
):
    try:
        return container.actualizar_estado_objetivo.execute(control_id, objetivo_id, command.estado)
    except LookupError as error:
        raise _handle_not_found(error) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/semanas/{control_id}/detalle", response_model=SemanaDetalleResponse)
def detalle_semanal(
    control_id: UUID,
    container: PostgresAppContainer = Depends(get_container),
):
    try:
        control = container.controles_semanales.get(control_id)
        if control is None:
            raise LookupError(f"No existe el control semanal {control_id}.")
        resumen: ResumenSemanal = container.obtener_resumen_semanal.execute(control_id)
    except LookupError as error:
        raise _handle_not_found(error) from error
    return {
        "id": control.id,
        "fecha_inicio": control.fecha_inicio,
        "fecha_fin": control.fecha_fin,
        "puntos_control": resumen.puntos_control,
        "puntos_misiones": resumen.puntos_misiones,
        "puntos_pendientes": resumen.puntos_pendientes,
        "puntos_promesas": resumen.puntos_promesas,
        "puntos_limites": resumen.puntos_limites,
        "puntos_tiros": resumen.puntos_tiros,
        "puntos_total": resumen.puntos_total,
        "rango": resumen.rango.value,
        "objetivos": [objetivo for objetivo in control.objetivos if objetivo.is_active],
        "controles_diarios": [
            {
                "id": diario.id,
                "fecha": diario.fecha,
                "puntos_base": diario.puntos_base,
                "penalizacion_incumplimiento": diario.penalizacion_incumplimiento,
                "bono_sobrecarga": diario.bono_sobrecarga,
                "puntos": diario.calcular_puntaje(),
                "tareas": diario.tareas,
            }
            for diario in control.controles_diarios
        ],
    }


@router.get("/semanas/{control_id}/resumen", response_model=ResumenSemanalResponse)
def resumen_semanal(
    control_id: UUID,
    container: PostgresAppContainer = Depends(get_container),
):
    try:
        resumen: ResumenSemanal = container.obtener_resumen_semanal.execute(control_id)
    except LookupError as error:
        raise _handle_not_found(error) from error
    return {**resumen.__dict__, "rango": resumen.rango.value}


@router.get("/finanzas/catalogo", response_model=list[TipoGastoResponse])
def catalogo_gastos(
    container: PostgresAppContainer = Depends(get_container),
):
    """Devuelve categorías/tipos listos para que el formulario registre gastos.

    Las categorías base se crean de forma idempotente para que una instalación
    nueva no obligue al usuario a configurar el catálogo manualmente.
    """
    categorias = container.categorias_tipo_gasto.list()
    for nombre in CategoriaGastoNombre:
        categoria = next((item for item in categorias if item.nombre == nombre), None)
        if categoria is None:
            categoria = container.crear_categoria_gasto.execute(nombre)
            categorias.append(categoria)

    tipos = container.tipos_gasto.list()
    for categoria in categorias:
        tipo = next((item for item in tipos if item.categoria.id == categoria.id), None)
        if tipo is None:
            tipo = container.crear_tipo_gasto.execute(
                categoria.nombre.value.title(), categoria.id, f"Gastos {categoria.nombre.value}"
            )
            tipos.append(tipo)

    return [
        {
            "id": tipo.id,
            "nombre": tipo.nombre,
            "categoria_id": tipo.categoria.id,
            "categoria": tipo.categoria.nombre,
            "descripcion": tipo.descripcion,
            "is_active": tipo.is_active,
        }
        for tipo in tipos
        if tipo.is_active
    ]


@router.get(
    "/finanzas/controles/semanales/periodo",
    response_model=ControlGastoDetalleResponse,
)
def control_gasto_por_periodo(
    fecha_inicio: date = Query(...),
    fecha_fin: date = Query(...),
    container: PostgresAppContainer = Depends(get_container),
):
    control = next(
        (
            item
            for item in container.controles_gasto_semanales.list()
            if item.fecha_inicio == fecha_inicio and item.fecha_fin == fecha_fin
        ),
        None,
    )
    if control is None:
        raise HTTPException(status_code=404, detail="No existe un control financiero para ese período.")
    return {
        "id": control.id,
        "fecha_inicio": control.fecha_inicio,
        "fecha_fin": control.fecha_fin,
        "limite_gasto": control.limite_gasto,
        "saldo": control.disponible(),
    }


@router.post("/finanzas/categorias", response_model=CategoriaResponse, status_code=201)
def crear_categoria(
    command: CategoriaCreate,
    container: PostgresAppContainer = Depends(get_container),
):
    categoria = container.crear_categoria_gasto.execute(command.nombre, command.descripcion)
    return categoria


@router.post("/finanzas/tipos-gasto", response_model=TipoGastoResponse, status_code=201)
def crear_tipo_gasto(
    command: TipoGastoCreate,
    container: PostgresAppContainer = Depends(get_container),
):
    try:
        tipo = container.crear_tipo_gasto.execute(
            command.nombre, command.categoria_id, command.descripcion
        )
    except LookupError as error:
        raise _handle_not_found(error) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {
        "id": tipo.id,
        "nombre": tipo.nombre,
        "categoria_id": tipo.categoria.id,
        "categoria": tipo.categoria.nombre,
        "descripcion": tipo.descripcion,
        "is_active": tipo.is_active,
    }


@router.post("/finanzas/controles/semanales", response_model=ControlGastoResponse, status_code=201)
def crear_control_gasto_semanal(
    command: ControlGastoSemanalCreate,
    container: PostgresAppContainer = Depends(get_container),
):
    existing = next(
        (
            item
            for item in container.controles_gasto_semanales.list()
            if item.fecha_inicio == command.fecha_inicio and item.fecha_fin == command.fecha_fin
        ),
        None,
    )
    if existing is not None:
        return {"id": existing.id, "saldo": existing.disponible()}
    try:
        control = container.crear_control_gasto_semanal.execute(
            command.fecha_inicio, command.fecha_fin, command.limite_gasto
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"id": control.id, "saldo": control.disponible()}


@router.post("/finanzas/controles/mensuales", response_model=ControlGastoResponse, status_code=201)
def crear_control_gasto_mensual(
    command: ControlGastoMensualCreate,
    container: PostgresAppContainer = Depends(get_container),
):
    try:
        control = container.crear_control_gasto_mensual.execute(
            command.anio, command.mes, command.presupuesto
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"id": control.id, "saldo": control.saldo_presupuesto()}


@router.post("/finanzas/controles/semanales/{control_id}/gastos", response_model=GastoResponse, status_code=201)
def registrar_gasto_semanal(
    control_id: UUID,
    command: GastoCreate,
    container: PostgresAppContainer = Depends(get_container),
):
    tipo = container.tipos_gasto.get(command.tipo_gasto_id)
    if tipo is None:
        raise HTTPException(status_code=404, detail="Tipo de gasto no encontrado")
    try:
        gasto = container.registrar_gasto_semanal.execute(
            control_id,
            command.nombre,
            command.importe,
            tipo,
            command.fecha_hora,
            descripcion=command.descripcion,
            puntaje_generado=command.puntaje_generado,
        )
    except LookupError as error:
        raise _handle_not_found(error) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {
        "id": gasto.id,
        "nombre": gasto.nombre,
        "importe": gasto.importe,
        "tipo_gasto_id": gasto.tipo_gasto.id,
        "fecha_hora": gasto.fecha_hora,
        "descripcion": gasto.descripcion,
        "puntaje_generado": gasto.puntaje_generado,
    }


@router.get(
    "/finanzas/controles/semanales/{control_id}/gastos",
    response_model=list[GastoListadoResponse],
)
def listar_gastos_semanales(
    control_id: UUID,
    container: PostgresAppContainer = Depends(get_container),
):
    control = container.controles_gasto_semanales.get(control_id)
    if control is None:
        raise HTTPException(status_code=404, detail="Control financiero no encontrado")
    return [
        {
            "id": gasto.id,
            "nombre": gasto.nombre,
            "importe": gasto.importe,
            "tipo_gasto_id": gasto.tipo_gasto.id,
            "tipo_gasto": gasto.tipo_gasto.nombre,
            "categoria": gasto.tipo_gasto.categoria.nombre,
            "fecha_hora": gasto.fecha_hora,
            "descripcion": gasto.descripcion,
            "puntaje_generado": gasto.puntaje_generado,
        }
        for gasto in control.gastos
        if gasto.is_active
    ]


@router.post("/finanzas/controles/mensuales/{control_id}/gastos", response_model=GastoResponse, status_code=201)
def registrar_gasto_mensual(
    control_id: UUID,
    command: GastoCreate,
    container: PostgresAppContainer = Depends(get_container),
):
    tipo = container.tipos_gasto.get(command.tipo_gasto_id)
    if tipo is None:
        raise HTTPException(status_code=404, detail="Tipo de gasto no encontrado")
    try:
        gasto = container.registrar_gasto_mensual.execute(
            control_id,
            command.nombre,
            command.importe,
            tipo,
            command.fecha_hora,
            descripcion=command.descripcion,
            puntaje_generado=command.puntaje_generado,
        )
    except LookupError as error:
        raise _handle_not_found(error) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {
        "id": gasto.id,
        "nombre": gasto.nombre,
        "importe": gasto.importe,
        "tipo_gasto_id": gasto.tipo_gasto.id,
        "fecha_hora": gasto.fecha_hora,
        "descripcion": gasto.descripcion,
        "puntaje_generado": gasto.puntaje_generado,
    }


@router.get("/finanzas/controles/semanales/{control_id}/resumen", response_model=ResumenGastoResponse)
def resumen_gasto_semanal(
    control_id: UUID,
    container: PostgresAppContainer = Depends(get_container),
):
    try:
        resumen: ResumenGasto = container.obtener_resumen_gasto_semanal.execute(control_id)
    except LookupError as error:
        raise _handle_not_found(error) from error
    return resumen


@router.get("/finanzas/controles/mensuales/{control_id}/resumen", response_model=ResumenGastoResponse)
def resumen_gasto_mensual(
    control_id: UUID,
    container: PostgresAppContainer = Depends(get_container),
):
    try:
        resumen: ResumenGasto = container.obtener_resumen_gasto_mensual.execute(control_id)
    except LookupError as error:
        raise _handle_not_found(error) from error
    return resumen


@router.post("/gamificacion/movimientos", response_model=MovimientoResponse, status_code=201)
def registrar_movimiento(
    command: MovimientoCreate,
    container: PostgresAppContainer = Depends(get_container),
):
    try:
        return container.registrar_movimiento_puntaje.execute(
            command.puntos,
            command.origen,
            command.motivo,
            command.tipo,
            fecha_hora=command.fecha_hora,
            referencia_id=command.referencia_id,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/gamificacion/movimientos", response_model=list[MovimientoResponse])
def listar_movimientos(container: PostgresAppContainer = Depends(get_container)):
    movimientos = container.movimientos_puntaje.list()
    return sorted(movimientos, key=lambda movimiento: movimiento.fecha_hora, reverse=True)


@router.get("/gamificacion/resumen", response_model=ResumenPuntajeResponse)
def resumen_puntaje(container: PostgresAppContainer = Depends(get_container)):
    resumen: ResumenPuntaje = container.obtener_resumen_puntaje.execute()
    return {**resumen.__dict__, "rango": resumen.rango.value}
