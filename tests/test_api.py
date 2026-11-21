"""Flujo completo de administración: carga → corrida → malla → Excel (PA-06 automatizable) y roles."""
import io

import pandas as pd

from tests.conftest import ADMIN, SOPORTE, correr


def test_flujo_completo(cargado):
    c = correr(cargado, departamentos=["ELECTRICA", "GEOLOGIA"], lam=0.03)
    assert c["estado"] in ("optima", "factible")
    assert c["indicadores"]["choques"] == 0 and c["indicadores"]["violaciones_capacidad"] == 0
    assert c["indicadores"]["asientos_vacios"] < c["indicadores_base"]["asientos_vacios"]
    assert c["parametros"]["lam"] == 0.03  # la corrida guarda sus parámetros para repetirla
    assert len(c["malla"]) > 0

    r = cargado.get(f"/api/corridas/{c['id']}/excel", headers=ADMIN)
    assert r.status_code == 200
    malla = pd.read_excel(io.BytesIO(r.content), sheet_name="Malla")
    for col in ["sección", "curso", "bloque", "sala", "capacidad", "inscritos"]:  # columnas pedidas en PA-06
        assert col in malla.columns
    assert len(malla) == len(c["malla"])
    assert "Indicadores" in pd.ExcelFile(io.BytesIO(r.content)).sheet_names


def test_corrida_sin_datos_queda_en_error(client):
    c = correr(client)
    assert c["estado"] == "error" and "secciones" in c["mensaje"]


def test_filtrar_por_departamento(cargado):
    c = correr(cargado, departamentos=["GEOLOGIA"])
    assert {m["departamento"] for m in c["malla"]} == {"GEOLOGIA"}


def test_soporte_no_accede_al_panel_ni_a_los_datos(cargado):
    assert cargado.get("/panel", headers=SOPORTE).status_code == 403
    assert cargado.post("/api/corridas", headers=SOPORTE, json={"semestre": "2026-1"}).status_code == 403
    assert cargado.get("/panel").status_code == 401
    assert cargado.get("/panel", headers=ADMIN).status_code == 200


def test_credenciales_incorrectas(client):
    assert client.get("/incidencias", auth=("admin", "mala")).status_code == 401
