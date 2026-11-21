"""B2/B3 · Lanzar y consultar optimizaciones."""
import io

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import db as dbmod
from ..auth import solo_administracion
from ..config import settings
from ..db import get_db
from ..engine.horario import etiqueta_bloque
from ..models import Corrida
from ..schemas import CorridaIn
from ..services.corridas import procesar_corrida
from ..services.excel import malla_excel

router = APIRouter(prefix="/api/corridas", tags=["corridas"], dependencies=[Depends(solo_administracion)])


def _resumen(c: Corrida, con_malla: bool = False) -> dict:
    out = {"id": c.id, "fecha": c.fecha.isoformat(timespec="seconds"), "semestre": c.semestre, "parametros": c.parametros,
           "estado": c.estado, "mensaje": c.mensaje, "tiempo_s": c.tiempo_s, "indicadores": c.indicadores, "indicadores_base": c.indicadores_base}
    if con_malla:
        out["malla"] = [{"curso": a.curso, "seccion": a.seccion, "departamento": a.departamento, "dia": a.dia,
                         "bloque": etiqueta_bloque({"dia": a.dia, "inicio": a.inicio, "fin": a.fin}),
                         "sala": a.sala_codigo, "capacidad": a.capacidad, "inscritos": a.inscritos} for a in c.asignaciones]
    return out


@router.post("", status_code=202)
def lanzar(datos: CorridaIn, fondo: BackgroundTasks, db: Session = Depends(get_db)):
    c = Corrida(semestre=datos.semestre, estado="en_curso", parametros={
        "departamentos": datos.departamentos, "lam": datos.lam, "fijas": datos.fijas,
        "max_segundos": datos.max_segundos or settings.solver_max_segundos})
    db.add(c)
    db.commit()
    fondo.add_task(procesar_corrida, dbmod.SessionLocal, c.id)
    return {"id": c.id, "estado": c.estado}


@router.get("")
def listar(db: Session = Depends(get_db)):
    return [_resumen(c) for c in db.scalars(select(Corrida).order_by(Corrida.id.desc()).limit(50))]


@router.get("/{corrida_id}")
def detalle(corrida_id: int, db: Session = Depends(get_db)):
    c = db.get(Corrida, corrida_id)
    if not c:
        raise HTTPException(404, "Corrida no encontrada")
    return _resumen(c, con_malla=True)


@router.get("/{corrida_id}/excel")
def excel(corrida_id: int, db: Session = Depends(get_db)):
    c = db.get(Corrida, corrida_id)
    if not c:
        raise HTTPException(404, "Corrida no encontrada")
    return StreamingResponse(io.BytesIO(malla_excel(c)), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": f'attachment; filename="malla_corrida_{c.id}.xlsx"'})
