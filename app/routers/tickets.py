"""B4 · Reportes por QR y mesa de incidencias."""
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import solo_administracion, usuario_actual
from ..db import get_db
from ..models import Sala, Ticket
from ..schemas import TicketIn, TicketPatch
from ..services.correo import avisar_soporte
from ..services.corridas import tiene_clase_ahora
from ..services.qr import png_qr, url_sala

router = APIRouter(tags=["tickets"])


def _json(t: Ticket) -> dict:
    return {"id": t.id, "sala": t.sala.codigo, "categoria": t.categoria, "descripcion": t.descripcion, "estado": t.estado,
            "prioridad": t.prioridad, "creado": t.creado.isoformat(timespec="seconds"),
            "cerrado": t.cerrado.isoformat(timespec="seconds") if t.cerrado else None}


@router.post("/api/tickets", status_code=201)  # público: quien escanea el QR no inicia sesión
def crear(datos: TicketIn, fondo: BackgroundTasks, db: Session = Depends(get_db)):
    sala = db.scalar(select(Sala).where(Sala.codigo == datos.sala))
    if not sala:
        raise HTTPException(404, "Sala no encontrada")
    prioridad = "alta" if tiene_clase_ahora(db, sala.codigo) else "normal"
    t = Ticket(sala_id=sala.id, categoria=datos.categoria, descripcion=datos.descripcion, prioridad=prioridad)
    db.add(t)
    db.commit()
    fondo.add_task(avisar_soporte, f"[{prioridad.upper()}] Falla en sala {sala.codigo}: {datos.categoria}",
                   f"Sala {sala.codigo}\nCategoría: {datos.categoria}\nDescripción: {datos.descripcion}\nTicket #{t.id}")
    return _json(t)


@router.get("/api/tickets")
def listar(estado: str | None = Query(None), sala: str | None = Query(None), db: Session = Depends(get_db), _: str = Depends(usuario_actual)):
    q = select(Ticket).join(Sala).order_by(Ticket.id.desc()).limit(500)
    if estado:
        q = q.where(Ticket.estado == estado)
    if sala:
        q = q.where(Sala.codigo == sala)
    tickets = sorted(db.scalars(q), key=lambda t: (t.prioridad != "alta", t.estado == "resuelto", -t.id))
    return [_json(t) for t in tickets]


@router.patch("/api/tickets/{ticket_id}")
def actualizar(ticket_id: int, datos: TicketPatch, db: Session = Depends(get_db), _: str = Depends(usuario_actual)):
    t = db.get(Ticket, ticket_id)
    if not t:
        raise HTTPException(404, "Ticket no encontrado")
    t.estado = datos.estado
    t.cerrado = datetime.now() if datos.estado == "resuelto" else None
    db.commit()
    return _json(t)


@router.get("/api/salas/{codigo}/qr.png")
def qr(codigo: str, db: Session = Depends(get_db), _: str = Depends(solo_administracion)):
    if not db.scalar(select(Sala).where(Sala.codigo == codigo)):
        raise HTTPException(404, "Sala no encontrada")
    return Response(png_qr(codigo), media_type="image/png")


@router.get("/api/salas")
def salas(db: Session = Depends(get_db), _: str = Depends(usuario_actual)):
    return [{"codigo": s.codigo, "edificio": s.edificio.nombre, "piso": s.piso, "capacidad": s.capacidad, "tipo": s.tipo,
             "url_qr": url_sala(s.codigo)} for s in db.scalars(select(Sala).order_by(Sala.codigo))]
