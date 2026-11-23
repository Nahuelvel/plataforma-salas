import base64
import io
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app import db as dbmod
from app.config import settings
from app.main import app
from app.models import Base

EJEMPLO = Path(__file__).resolve().parents[1] / "data" / "ejemplo"


def _auth(usuario, clave):
    return {"Authorization": "Basic " + base64.b64encode(f"{usuario}:{clave}".encode()).decode()}


ADMIN = _auth(settings.admin_user, settings.admin_password)
SOPORTE = _auth(settings.soporte_user, settings.soporte_password)


@pytest.fixture()
def client(monkeypatch):
    """Cliente con una base SQLite en memoria nueva en cada prueba."""
    engine = dbmod.crear_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Sesion = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    monkeypatch.setattr(dbmod, "SessionLocal", Sesion)  # lo usan las tareas en segundo plano

    def _db():
        s = Sesion()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[dbmod.get_db] = _db
    yield TestClient(app)
    app.dependency_overrides.clear()


def xlsx(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()


def subir(client, tipo, contenido: bytes, nombre="planilla.xlsx", semestre="2026-1"):
    params = {"semestre": semestre} if tipo == "secciones" else {}
    return client.post(f"/api/datos/{tipo}", params=params, headers=ADMIN, files={"archivo": (nombre, contenido)})


@pytest.fixture()
def cargado(client):
    """Cliente con las planillas de ejemplo (Eléctrica + Geología) ya cargadas."""
    assert subir(client, "salas", (EJEMPLO / "salas.xlsx").read_bytes()).json()["ok"]
    assert subir(client, "traslados", (EJEMPLO / "traslados.xlsx").read_bytes()).json()["ok"]
    assert subir(client, "secciones", (EJEMPLO / "secciones.xlsx").read_bytes()).json()["ok"]
    return client


def correr(client, **extra):
    r = client.post("/api/corridas", headers=ADMIN, json={"semestre": "2026-1", "max_segundos": 20, **extra})
    assert r.status_code == 202
    return client.get(f"/api/corridas/{r.json()['id']}", headers=ADMIN).json()
