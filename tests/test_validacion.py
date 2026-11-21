"""PA-05 · CA-06: 10 de 10 planillas con errores rechazadas, cada una indicando fila y columna."""
import pandas as pd
import pytest

from tests.conftest import subir, xlsx

SALAS_OK = pd.DataFrame({"codigo_sala": ["A-1", "A-2"], "edificio": ["A", "A"], "piso": [1, 2], "capacidad": [40, 25], "tipo": ["catedra", "laboratorio"]})
SEC_OK = pd.DataFrame({"curso": ["C1", "C2"], "seccion": [1, 1], "inscritos": [30, 20], "nivel": [1, 1], "tipo_sala": ["catedra", "laboratorio"],
                       "horario": ["LU 10:15-11:45; MI 10:15-11:45", "MA 08:00-09:30"]})


def mod(df, fila, col, valor):
    d = df.copy().astype(object)
    d.loc[fila, col] = valor
    return d


# (descripción, planilla, DataFrame con error, fila esperada, columna esperada)
SALAS_MALAS = [
    ("columna faltante", SALAS_OK.drop(columns=["capacidad"]), 1, "capacidad"),
    ("capacidad negativa", mod(SALAS_OK, 1, "capacidad", -5), 3, "capacidad"),
    ("capacidad no numérica", mod(SALAS_OK, 0, "capacidad", "abc"), 2, "capacidad"),
    ("tipo de sala inexistente", mod(SALAS_OK, 1, "tipo", "auditorio"), 3, "tipo"),
    ("sala duplicada", mod(SALAS_OK, 1, "codigo_sala", "A-1"), 3, "codigo_sala"),
]
SECCIONES_MALAS = [
    ("sección duplicada", mod(SEC_OK, 1, "curso", "C1"), 3, "seccion"),
    ("horario mal escrito", mod(SEC_OK, 0, "horario", "lunes por la mañana"), 2, "horario"),
    ("término antes del inicio", mod(SEC_OK, 1, "horario", "MA 10:00-09:00"), 3, "horario"),
    ("inscritos en cero", mod(SEC_OK, 0, "inscritos", 0), 2, "inscritos"),
    ("sin sala con capacidad suficiente", mod(SEC_OK, 1, "inscritos", 500), 3, "tipo_sala"),
]


@pytest.fixture()
def con_salas(client):
    assert subir(client, "salas", xlsx(SALAS_OK)).json()["ok"]
    return client


@pytest.mark.parametrize("nombre,df,fila,col", SALAS_MALAS, ids=[c[0] for c in SALAS_MALAS])
def test_salas_con_error_se_rechazan(client, nombre, df, fila, col):
    r = subir(client, "salas", xlsx(df)).json()
    assert r["ok"] is False and r["filas_cargadas"] == 0
    assert any(e["fila"] == fila and e["columna"] == col for e in r["errores"]), r["errores"]


@pytest.mark.parametrize("nombre,df,fila,col", SECCIONES_MALAS, ids=[c[0] for c in SECCIONES_MALAS])
def test_secciones_con_error_se_rechazan(con_salas, nombre, df, fila, col):
    r = subir(con_salas, "secciones", xlsx(df)).json()
    assert r["ok"] is False
    assert any(e["fila"] == fila and e["columna"] == col for e in r["errores"]), r["errores"]


def test_planillas_correctas_se_aceptan(con_salas):
    r = subir(con_salas, "secciones", xlsx(SEC_OK)).json()
    assert r["ok"] and r["filas_cargadas"] == 2


def test_archivo_ilegible_no_tumba_el_servidor(client):
    r = subir(client, "salas", b"esto no es un excel")
    assert r.status_code == 200 and r.json()["ok"] is False


def test_csv_tambien_se_acepta(client):
    csv = SALAS_OK.to_csv(index=False).encode()
    assert subir(client, "salas", csv, nombre="salas.csv").json()["ok"]


def test_carga_exige_rol_administracion(client):
    r = client.post("/api/datos/salas", files={"archivo": ("s.xlsx", xlsx(SALAS_OK))})
    assert r.status_code == 401
