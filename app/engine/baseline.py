"""Asignación simple «primera sala donde cabe». Sirve de referencia en PA-02 si no hay asignación manual."""
from .horario import se_traslapan
from .indicadores import clave


def primera_sala_que_cabe(salas: list[dict], secciones: list[dict]) -> dict[str, str]:
    ocupadas: dict[str, list[dict]] = {s["codigo"]: [] for s in salas}
    resultado = {}
    for sec in sorted(secciones, key=lambda s: (-s["inscritos"], clave(s))):
        for sala in sorted(salas, key=lambda s: s["codigo"]):
            if sala["tipo"] != sec["tipo_sala"] or sala["capacidad"] < sec["inscritos"]:
                continue
            if any(se_traslapan(a, b) for a in sec["bloques"] for b in ocupadas[sala["codigo"]]):
                continue
            ocupadas[sala["codigo"]].extend(sec["bloques"])
            resultado[clave(sec)] = sala["codigo"]
            break
    return resultado
