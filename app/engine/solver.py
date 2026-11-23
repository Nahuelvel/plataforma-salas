"""Formulación CP-SAT del LLD (bloque B2).

Variable   x[c, s] = 1 si la sección c va en la sala s.
Duras      (1) una sala por sección, (2) capacidad y tipo, (3) sin choques sala-bloque.
Objetivo   min  Σ (capacidad − inscritos) · n_bloques  +  λ · minutos de traslado entre clases consecutivas del mismo nivel.
"""
import time

from ortools.sat.python import cp_model

from .horario import se_traslapan
from .indicadores import calcular, clave, pares_consecutivos
from .traslado import tabla, tiempo

ESCALA = 1000  # el objetivo debe ser entero: 1 asiento vacío = 1000; 1 décima de minuto = round(λ · 100)
# λ = cuántos asientos vacíos se acepta «pagar» por ahorrar 1 minuto de traslado


def resolver(
    salas: list[dict],
    secciones: list[dict],
    lam: float = 0.0,
    max_segundos: float = 60.0,
    hilos: int = 8,
    fijas: dict[str, str] | None = None,
    traslados: list | None = None,
) -> dict:
    """Resuelve un departamento. ``fijas`` = {"CURSO-SEC": "COD_SALA"} para fijar una sala y recalcular."""
    fijas = fijas or {}
    t_tabla = tabla(traslados)
    t0 = time.perf_counter()
    modelo = cp_model.CpModel()
    sec_por_clave = {clave(s): s for s in secciones}
    x: dict[tuple[str, str], cp_model.IntVar] = {}
    cand: dict[str, list[str]] = {}

    # (1)+(2) Variables solo para pares que caben (capacidad ≥ inscritos y tipo requerido)
    sin_sala: list[str] = []
    for k, sec in sec_por_clave.items():
        candidatas = [
            s for s in salas
            if s["tipo"] == sec["tipo_sala"] and s["capacidad"] >= sec["inscritos"]
            and (k not in fijas or s["codigo"] == fijas[k])
        ]
        if not candidatas:
            sin_sala.append(k)
            continue
        cand[k] = [s["codigo"] for s in candidatas]
        for s in candidatas:
            x[k, s["codigo"]] = modelo.NewBoolVar(f"x_{k}_{s['codigo']}")
        modelo.AddExactlyOne(x[k, s["codigo"]] for s in candidatas)
    if sin_sala:
        return _resultado("infactible", {}, salas, secciones, t0, traslados, mensaje=f"Sin sala posible para: {', '.join(sin_sala)}")

    # (3) Sin choques: dos secciones con bloques traslapados no pueden compartir sala
    claves = list(sec_por_clave)
    for i, ka in enumerate(claves):
        for kb in claves[i + 1:]:
            if any(se_traslapan(a, b) for a in sec_por_clave[ka]["bloques"] for b in sec_por_clave[kb]["bloques"]):
                for s in salas:
                    if (ka, s["codigo"]) in x and (kb, s["codigo"]) in x:
                        modelo.AddAtMostOne([x[ka, s["codigo"]], x[kb, s["codigo"]]])

    # Objetivo
    sala_por_cod = {s["codigo"]: s for s in salas}
    terminos = []
    for (k, cod), var in x.items():
        vacios = (sala_por_cod[cod]["capacidad"] - sec_por_clave[k]["inscritos"]) * len(sec_por_clave[k]["bloques"])
        terminos.append(ESCALA * vacios * var)

    peso_dist = round(lam * ESCALA / 10)  # el modelo cuenta décimas de minuto (enteros)
    if peso_dist > 0:
        for ka, kb in pares_consecutivos(secciones):
            dist_par = {(sa, sb): round(10 * tiempo(sala_por_cod[sa], sala_por_cod[sb], t_tabla)) for sa in cand[ka] for sb in cand[kb]}
            maxd = max(dist_par.values(), default=0)
            if maxd == 0:
                continue
            d = modelo.NewIntVar(0, maxd, f"d_{ka}_{kb}")
            for (sa, sb), dist in dist_par.items():
                if dist > 0:
                    modelo.Add(d >= dist * (x[ka, sa] + x[kb, sb] - 1))  # d vale el tiempo real si ambas se eligen
            terminos.append(peso_dist * d)
    modelo.Minimize(sum(terminos))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max_segundos
    solver.parameters.num_workers = hilos
    estado = solver.Solve(modelo)

    nombres = {cp_model.OPTIMAL: "optima", cp_model.FEASIBLE: "factible"}
    if estado not in nombres:
        return _resultado("infactible", {}, salas, secciones, t0, traslados, mensaje="No se encontró una asignación que cumpla las restricciones")
    asignacion = {k: cod for (k, cod), var in x.items() if solver.Value(var) == 1}
    return _resultado(nombres[estado], asignacion, salas, secciones, t0, traslados)


def _resultado(estado: str, asignacion: dict, salas: list[dict], secciones: list[dict], t0: float, traslados: list | None, mensaje: str = "") -> dict:
    return {
        "estado": estado,
        "mensaje": mensaje,
        "tiempo_s": round(time.perf_counter() - t0, 3),
        "asignacion": asignacion,
        "indicadores": calcular(salas, secciones, asignacion, traslados),
    }
