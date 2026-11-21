"""Indicadores de una asignación (los usan la corrida, el Excel y las pruebas PA-01 a PA-04)."""
from collections import defaultdict

from .distancia import distancia
from .horario import se_traslapan


def clave(seccion: dict) -> str:
    return f"{seccion['curso']}-{seccion['seccion']}"


def pares_consecutivos(secciones: list[dict], max_hueco_min: int = 30) -> list[tuple[str, str]]:
    """Pares de secciones del mismo nivel y día, una a continuación de la otra (hueco ≤ max_hueco_min).

    Son las «clases consecutivas del mismo nivel» de la función objetivo.
    """
    por_nivel_dia = defaultdict(list)
    for s in secciones:
        for b in s["bloques"]:
            por_nivel_dia[(s["nivel"], b["dia"])].append((b["inicio"], b["fin"], clave(s)))
    pares = set()
    for lista in por_nivel_dia.values():
        lista.sort()
        for (_, fin_a, ca), (ini_b, _, cb) in zip(lista, lista[1:], strict=False):
            if ca != cb and 0 <= ini_b - fin_a <= max_hueco_min:
                pares.add(tuple(sorted((ca, cb))))
    return sorted(pares)


def calcular(salas: list[dict], secciones: list[dict], asignacion: dict[str, str]) -> dict:
    """asignacion: {"CURSO-SEC": "COD_SALA"}. Devuelve los indicadores del LLD."""
    sala_por_cod = {s["codigo"]: s for s in salas}
    sec_por_clave = {clave(s): s for s in secciones}

    asientos_vacios = cap_total = insc_total = 0
    violaciones_capacidad = sin_asignar = 0
    for k, sec in sec_por_clave.items():
        cod = asignacion.get(k)
        if cod is None or cod not in sala_por_cod:
            sin_asignar += 1
            continue
        sala = sala_por_cod[cod]
        n = len(sec["bloques"])  # cada bloque es una fila de la asignación
        if sala["capacidad"] < sec["inscritos"] or sala["tipo"] != sec["tipo_sala"]:
            violaciones_capacidad += 1
        asientos_vacios += (sala["capacidad"] - sec["inscritos"]) * n
        cap_total += sala["capacidad"] * n
        insc_total += sec["inscritos"] * n

    # Choques: dos secciones en la misma sala con bloques traslapados
    por_sala = defaultdict(list)
    for k, cod in asignacion.items():
        if k in sec_por_clave:
            por_sala[cod].append(k)
    choques = 0
    for claves in por_sala.values():
        for i, ka in enumerate(claves):
            for kb in claves[i + 1:]:
                if any(se_traslapan(a, b) for a in sec_por_clave[ka]["bloques"] for b in sec_por_clave[kb]["bloques"]):
                    choques += 1

    # Distancia promedio entre clases consecutivas del mismo nivel
    dists = []
    for ka, kb in pares_consecutivos(secciones):
        if ka in asignacion and kb in asignacion and asignacion[ka] in sala_por_cod and asignacion[kb] in sala_por_cod:
            dists.append(distancia(sala_por_cod[asignacion[ka]], sala_por_cod[asignacion[kb]]))
    return {
        "asientos_vacios": asientos_vacios,
        "aforo_util_pct": round(100 * insc_total / cap_total, 2) if cap_total else 0.0,
        "distancia_promedio": round(sum(dists) / len(dists), 2) if dists else 0.0,
        "choques": choques,
        "violaciones_capacidad": violaciones_capacidad,
        "secciones_sin_asignar": sin_asignar,
        "secciones_total": len(sec_por_clave),
    }
