"""PA-02 / PA-03 reales: compara la plataforma contra la asignación MANUAL del semestre.

    python -m scripts.comparar_manual salas.xlsx secciones.xlsx traslados.xlsx manual.xlsx [--lam 1]

manual.xlsx: columnas curso, seccion, sala (la sala que la secretaría asignó a cada sección).
Imprime los indicadores y si se cumplen CA-03 (≥15 % menos asientos vacíos) y CA-04 (≥10 % menos tiempo de traslado, sin subir asientos >5 %).
"""
import argparse

import pandas as pd

from app.engine.horario import parsear_horario
from app.engine.indicadores import calcular
from app.engine.solver import resolver
from app.validacion import leer_planilla, validar


def _leer(ruta):
    with open(ruta, "rb") as f:
        return leer_planilla(f.read(), ruta)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("salas"), ap.add_argument("secciones"), ap.add_argument("traslados"), ap.add_argument("manual")
    ap.add_argument("--lam", type=float, default=1.0, help="asientos vacíos que se acepta pagar por ahorrar 1 minuto")
    ap.add_argument("--segundos", type=float, default=60)
    a = ap.parse_args()

    sv, e1 = validar("salas", _leer(a.salas))
    if e1:
        raise SystemExit(f"salas.xlsx con errores: {e1[:3]}")
    salas = [{"codigo": m.codigo, "edificio": m.edificio, "piso": m.piso, "capacidad": m.capacidad, "tipo": m.tipo} for m in sv]
    tv, e3 = validar("traslados", _leer(a.traslados), edificios={s["edificio"] for s in salas})
    if e3:
        raise SystemExit(f"traslados.xlsx con errores: {e3[:3]}")
    traslados = [(m.edificio_a, m.edificio_b, m.minutos) for m in tv]
    secv, e2 = validar("secciones", _leer(a.secciones), {s["codigo"]: s for s in salas})
    if e2:
        raise SystemExit(f"secciones.xlsx con errores: {e2[:3]}")
    secs = [{**m.model_dump(), "bloques": parsear_horario(m.horario)} for m in secv]

    man = pd.read_excel(a.manual, dtype=str) if a.manual.endswith(".xlsx") else pd.read_csv(a.manual, dtype=str)
    manual = {f"{r.curso.strip()}-{r.seccion.strip()}": r.sala.strip() for r in man.itertuples()}
    ind_manual = calcular(salas, secs, manual, traslados)
    r0 = resolver(salas, secs, lam=0, max_segundos=a.segundos, traslados=traslados)["indicadores"]
    r1 = resolver(salas, secs, lam=a.lam, max_segundos=a.segundos, traslados=traslados)["indicadores"]

    pct = lambda antes, despues: 100 * (antes - despues) / antes if antes else 0.0  # noqa: E731
    print(pd.DataFrame({"manual": ind_manual, "plataforma λ=0": r0, f"plataforma λ={a.lam}": r1}).to_string())
    m3 = pct(ind_manual["asientos_vacios"], r0["asientos_vacios"])
    m4 = pct(ind_manual["traslado_promedio_min"], r1["traslado_promedio_min"])
    sube = 100 * (r1["asientos_vacios"] - r0["asientos_vacios"]) / r0["asientos_vacios"] if r0["asientos_vacios"] else 0
    print(f"\nCA-03 (≥15 % menos asientos vacíos): {m3:.1f} % → {'CUMPLE' if m3 >= 15 else 'NO CUMPLE'}")
    print(f"CA-04 (≥10 % menos traslado y asientos vacíos ≤ +5 %): {m4:.1f} % menos tiempo de traslado, {sube:+.1f} % asientos → {'CUMPLE' if m4 >= 10 and sube <= 5 else 'NO CUMPLE'}")


if __name__ == "__main__":
    main()
