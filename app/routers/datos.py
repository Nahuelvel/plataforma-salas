"""B1/B3 · Carga y validación de planillas."""
from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..auth import solo_administracion
from ..db import get_db
from ..engine.horario import parsear_horario
from ..models import Edificio, Sala, Seccion, Traslado
from ..schemas import ErrorFila, ResultadoCarga
from ..validacion import leer_planilla, validar

router = APIRouter(prefix="/api/datos", tags=["datos"], dependencies=[Depends(solo_administracion)])


def _leer(archivo: UploadFile, contenido: bytes):
    try:
        return leer_planilla(contenido, archivo.filename or ""), None
    except Exception:
        return None, ResultadoCarga(ok=False, filas_leidas=0, errores=[ErrorFila(fila=None, columna=None, mensaje="no se pudo leer el archivo; suba un .xlsx o .csv válido")])


@router.post("/salas", response_model=ResultadoCarga)
async def cargar_salas(archivo: UploadFile = File(...), db: Session = Depends(get_db)):
    df, falla = _leer(archivo, await archivo.read())
    if falla:
        return falla
    validas, errores = validar("salas", df)
    if errores:
        return ResultadoCarga(ok=False, filas_leidas=len(df), errores=errores)
    edificios = {e.nombre: e for e in db.scalars(select(Edificio))}
    for m in validas:
        e = edificios.get(m.edificio)
        if e is None:
            e = edificios[m.edificio] = Edificio(nombre=m.edificio)
            db.add(e)
        db.flush()
        sala = db.scalar(select(Sala).where(Sala.codigo == m.codigo))
        if sala is None:  # upsert por código: los tickets guardados siguen apuntando a su sala
            db.add(Sala(codigo=m.codigo, edificio_id=e.id, piso=m.piso, capacidad=m.capacidad, tipo=m.tipo))
        else:
            sala.edificio_id, sala.piso, sala.capacidad, sala.tipo = e.id, m.piso, m.capacidad, m.tipo
    db.commit()
    return ResultadoCarga(ok=True, filas_leidas=len(df), filas_cargadas=len(validas))


@router.post("/secciones", response_model=ResultadoCarga)
async def cargar_secciones(semestre: str = Query(..., min_length=1, max_length=10, examples=["2026-1"]),
                           archivo: UploadFile = File(...), db: Session = Depends(get_db)):
    df, falla = _leer(archivo, await archivo.read())
    if falla:
        return falla
    salas = {s.codigo: {"tipo": s.tipo, "capacidad": s.capacidad} for s in db.scalars(select(Sala))}
    if not salas:
        return ResultadoCarga(ok=False, filas_leidas=len(df), errores=[ErrorFila(fila=None, columna=None, mensaje="primero cargue las salas")])
    validas, errores = validar("secciones", df, salas)
    if errores:
        return ResultadoCarga(ok=False, filas_leidas=len(df), errores=errores)
    db.execute(delete(Seccion).where(Seccion.semestre == semestre))  # recargar un semestre lo reemplaza
    for m in validas:
        db.add(Seccion(semestre=semestre, curso=m.curso, seccion=m.seccion, departamento=m.departamento, inscritos=m.inscritos,
                       nivel=m.nivel, tipo_sala=m.tipo_sala, bloques=parsear_horario(m.horario)))
    db.commit()
    return ResultadoCarga(ok=True, filas_leidas=len(df), filas_cargadas=len(validas))


@router.post("/traslados", response_model=ResultadoCarga)
async def cargar_traslados(archivo: UploadFile = File(...), db: Session = Depends(get_db)):
    """Minutos caminando entre edificios: ``edificio_a · edificio_b · minutos``. Reemplaza la tabla completa."""
    df, falla = _leer(archivo, await archivo.read())
    if falla:
        return falla
    por_nombre = {e.nombre: e for e in db.scalars(select(Edificio))}
    if not por_nombre:
        return ResultadoCarga(ok=False, filas_leidas=len(df), errores=[ErrorFila(fila=None, columna=None, mensaje="primero cargue las salas")])
    validas, errores = validar("traslados", df, edificios=set(por_nombre))
    if errores:
        return ResultadoCarga(ok=False, filas_leidas=len(df), errores=errores)
    db.execute(delete(Traslado))
    for m in validas:
        a, b = sorted((por_nombre[m.edificio_a], por_nombre[m.edificio_b]), key=lambda e: e.id)
        db.add(Traslado(edificio_a_id=a.id, edificio_b_id=b.id, minutos=m.minutos))
    db.commit()
    return ResultadoCarga(ok=True, filas_leidas=len(df), filas_cargadas=len(validas))
