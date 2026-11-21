"""B4 · Flujo QR de punta a punta (parte automatizable de PA-07; las lecturas con celulares reales se hacen a mano)."""
import time
from datetime import datetime

from app.services import corridas as svc
from app.services.qr import png_qr, url_sala
from tests.conftest import ADMIN, SOPORTE, correr


def test_qr_apunta_a_la_pagina_de_la_sala(cargado):
    r = cargado.get("/api/salas/E-101/qr.png", headers=ADMIN)
    assert r.status_code == 200 and r.content[:8] == b"\x89PNG\r\n\x1a\n"
    assert url_sala("E-101").endswith("/r/E-101")
    assert len(png_qr("E-101")) > 500
    page = cargado.get("/r/E-101")  # sin login
    assert page.status_code == 200 and "E-101" in page.text
    assert cargado.get("/r/NO-EXISTE").status_code == 404


def test_ticket_desde_qr_aparece_en_la_mesa_en_menos_de_10s(cargado):
    t0 = time.perf_counter()
    r = cargado.post("/api/tickets", json={"sala": "E-101", "categoria": "proyector", "descripcion": "no enciende"})  # público
    assert r.status_code == 201
    mesa = cargado.get("/api/tickets", headers=SOPORTE).json()
    assert time.perf_counter() - t0 <= 10
    assert mesa[0]["sala"] == "E-101" and mesa[0]["estado"] == "abierto" and mesa[0]["categoria"] == "proyector"


def test_ticket_con_datos_invalidos(cargado):
    assert cargado.post("/api/tickets", json={"sala": "E-101", "categoria": "otra_cosa"}).status_code == 422
    assert cargado.post("/api/tickets", json={"sala": "ZZZ", "categoria": "otro"}).status_code == 404


def test_estados_del_ticket(cargado):
    tid = cargado.post("/api/tickets", json={"sala": "E-101", "categoria": "otro"}).json()["id"]
    r = cargado.patch(f"/api/tickets/{tid}", headers=SOPORTE, json={"estado": "en_curso"}).json()
    assert r["estado"] == "en_curso" and r["cerrado"] is None
    r = cargado.patch(f"/api/tickets/{tid}", headers=SOPORTE, json={"estado": "resuelto"}).json()
    assert r["estado"] == "resuelto" and r["cerrado"] is not None
    assert cargado.patch(f"/api/tickets/{tid}", headers=SOPORTE, json={"estado": "inventado"}).status_code == 422


def test_listar_tickets_requiere_login(cargado):
    assert cargado.get("/api/tickets").status_code == 401


def test_prioridad_alta_si_hay_clase_ahora(cargado):
    c = correr(cargado)
    a = c["malla"][0]
    dias = ["LU", "MA", "MI", "JU", "VI", "SA"]
    # busca un día/hora de ese bloque y comprueba la regla con un «ahora» inyectado
    from app import db as dbmod
    ahora = datetime(2026, 11, 16 + dias.index(a["dia"]), 12, 0)  # 16-nov-2026 es lunes
    with dbmod.SessionLocal() as db:
        inicio = next(x for x in db.scalars(__import__("sqlalchemy").select(svc.Asignacion)) if x.sala_codigo == a["sala"] and x.dia == a["dia"])
        ahora = ahora.replace(hour=inicio.inicio // 60, minute=inicio.inicio % 60)
        assert svc.tiene_clase_ahora(db, a["sala"], ahora) is True
        assert svc.tiene_clase_ahora(db, a["sala"], ahora.replace(hour=23, minute=30)) is False
        assert svc.tiene_clase_ahora(db, a["sala"], datetime(2026, 11, 22, 10, 0)) is False  # domingo


def test_prioridad_normal_sin_corridas(cargado):
    assert cargado.post("/api/tickets", json={"sala": "E-101", "categoria": "otro"}).json()["prioridad"] == "normal"
