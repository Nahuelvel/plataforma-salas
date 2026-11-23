"""Pruebas alfa sobre el motor: PA-01 a PA-04 (criterios CA-01 a CA-05). Se repiten en cada cambio (regresión)."""
import time
from collections import defaultdict

import pandas as pd
import pytest

from app.engine.baseline import primera_sala_que_cabe
from app.engine.horario import parsear_horario, se_traslapan
from app.engine.indicadores import calcular, clave
from app.engine.solver import resolver
from tests.conftest import EJEMPLO


def cargar_ejemplo(carpeta=EJEMPLO):
    salas = pd.read_excel(carpeta / "salas.xlsx").rename(columns={"codigo_sala": "codigo"}).to_dict("records")
    secs = pd.read_excel(carpeta / "secciones.xlsx").to_dict("records")
    for s in secs:
        s["bloques"] = parsear_horario(s["horario"])
        s["curso"], s["seccion"] = str(s["curso"]), str(s["seccion"])
    traslados = [(r["edificio_a"], r["edificio_b"], r["minutos"]) for r in pd.read_excel(carpeta / "traslados.xlsx").to_dict("records")]
    return salas, secs, traslados


@pytest.fixture(scope="module")
def caso():
    return cargar_ejemplo()


def test_pa01_capacidad_y_choques(caso):
    """CA-01 y CA-02: verificación independiente de `calcular` (revisa la tabla fila por fila)."""
    salas, secs, tr = caso
    res = resolver(salas, secs, lam=0, max_segundos=30, traslados=tr)
    assert res["estado"] in ("optima", "factible")
    asign = res["asignacion"]
    assert len(asign) == len(secs), "todas las secciones deben quedar asignadas"
    sala = {s["codigo"]: s for s in salas}
    for s in secs:
        r = sala[asign[clave(s)]]
        assert r["capacidad"] >= s["inscritos"], f"capacidad violada en {clave(s)}"
        assert r["tipo"] == s["tipo_sala"]
    por_sala = defaultdict(list)
    for s in secs:
        for b in s["bloques"]:
            por_sala[asign[clave(s)]].append((clave(s), b))
    for cod, lista in por_sala.items():
        for i, (ka, a) in enumerate(lista):
            for kb, b in lista[i + 1:]:
                assert ka == kb or not se_traslapan(a, b), f"choque en {cod}: {ka} vs {kb}"
    assert res["indicadores"]["choques"] == 0 and res["indicadores"]["violaciones_capacidad"] == 0


def test_pa02_aforo_contra_referencia(caso):
    """CA-03 (versión automática): contra «primera sala donde cabe». La prueba real usa la asignación manual (scripts/comparar_manual.py)."""
    salas, secs, tr = caso
    base = calcular(salas, secs, primera_sala_que_cabe(salas, secs), tr)
    res = resolver(salas, secs, lam=0, max_segundos=30, traslados=tr)["indicadores"]
    mejora = 100 * (base["asientos_vacios"] - res["asientos_vacios"]) / base["asientos_vacios"]
    print(f"PA-02: {base['asientos_vacios']} → {res['asientos_vacios']} asientos vacíos ({mejora:.1f}% menos)")
    assert mejora >= 15 and res["aforo_util_pct"] > base["aforo_util_pct"]


def test_pa03_traslado_con_lambda(caso):
    """CA-04: con λ > 0 baja el tiempo de traslado promedio y los asientos vacíos suben poco."""
    salas, secs, tr = caso
    a = resolver(salas, secs, lam=0, max_segundos=30, traslados=tr)["indicadores"]
    b = resolver(salas, secs, lam=1, max_segundos=30, traslados=tr)["indicadores"]
    print(f"PA-03: traslado {a['traslado_promedio_min']} → {b['traslado_promedio_min']} min; asientos {a['asientos_vacios']} → {b['asientos_vacios']}")
    assert b["traslado_promedio_min"] <= 0.9 * a["traslado_promedio_min"]
    assert b["asientos_vacios"] <= 1.05 * a["asientos_vacios"]
    assert b["choques"] == 0


def test_pa04_tiempo_de_calculo(caso):
    """CA-05: 5 corridas del caso base, cada una ≤ 60 s."""
    salas, secs, tr = caso
    for _ in range(5):
        t0 = time.perf_counter()
        res = resolver(salas, secs, lam=1, max_segundos=60, traslados=tr)
        assert res["estado"] in ("optima", "factible")
        assert time.perf_counter() - t0 <= 60


def test_pa04_escala_x3_informativa(tmp_path):
    """Caso 3 veces más grande: el límite de tiempo debe entregar al menos una solución factible."""
    from scripts.generar_datos_ejemplo import generar
    generar(tmp_path, factor=3)
    salas, secs, tr = cargar_ejemplo(tmp_path)
    res = resolver(salas, secs, lam=1, max_segundos=10, traslados=tr)
    print(f"escala x3: {len(secs)} secciones → {res['estado']} en {res['tiempo_s']} s")
    assert res["estado"] in ("optima", "factible") and res["indicadores"]["choques"] == 0


def test_sala_fija_se_respeta(caso):
    salas, secs, tr = caso
    k = clave(secs[0])
    cod = next(s["codigo"] for s in salas if s["tipo"] == secs[0]["tipo_sala"] and s["capacidad"] >= secs[0]["inscritos"])
    res = resolver(salas, secs, max_segundos=20, fijas={k: cod}, traslados=tr)
    assert res["asignacion"][k] == cod


def test_infactible_se_informa():
    salas = [{"codigo": "A", "edificio": "X", "piso": 1, "capacidad": 20, "tipo": "catedra"}]
    secs = [{"curso": "C1", "seccion": "1", "inscritos": 20, "nivel": 1, "tipo_sala": "catedra", "bloques": parsear_horario("LU 08:00-09:00")},
            {"curso": "C2", "seccion": "1", "inscritos": 20, "nivel": 1, "tipo_sala": "catedra", "bloques": parsear_horario("LU 08:30-09:30")}]
    res = resolver(salas, secs, max_segundos=5)
    assert res["estado"] == "infactible"
