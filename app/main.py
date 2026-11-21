from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import db as dbmod
from .auth import solo_administracion, usuario_actual
from .models import Base, Sala
from .routers import corridas, datos, tickets
from .schemas import CATEGORIAS

plantillas = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    Base.metadata.create_all(dbmod.engine)  # PMV: sin migraciones; ver docs/ARQUITECTURA.md
    yield


app = FastAPI(title="Plataforma de Asignación y Reportes en Salas", version="0.1.0", lifespan=ciclo_de_vida)
app.include_router(datos.router)
app.include_router(corridas.router)
app.include_router(tickets.router)


@app.get("/health", include_in_schema=False)
def health():
    return {"ok": True}


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def inicio(request: Request):
    return plantillas.TemplateResponse(request, "inicio.html")


@app.get("/panel", response_class=HTMLResponse, include_in_schema=False)
def panel(request: Request, _: str = Depends(solo_administracion)):
    return plantillas.TemplateResponse(request, "panel.html")


@app.get("/incidencias", response_class=HTMLResponse, include_in_schema=False)
def incidencias(request: Request, _: str = Depends(usuario_actual)):
    return plantillas.TemplateResponse(request, "incidencias.html")


@app.get("/r/{codigo}", response_class=HTMLResponse, include_in_schema=False)
def reportar(codigo: str, request: Request, db: Session = Depends(dbmod.get_db)):
    """Página que abre el QR de la sala: sin login ni app."""
    if not db.scalar(select(Sala).where(Sala.codigo == codigo)):
        raise HTTPException(404, "Sala no encontrada")
    return plantillas.TemplateResponse(request, "reporte.html", {"sala": codigo, "categorias": CATEGORIAS})
