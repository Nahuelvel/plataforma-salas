"""Proceso aparte para el motor: ``python -m app.engine.runner`` lee JSON por stdin y escribe JSON por stdout.

Así cada asignación es un proceso separado: si el motor se cuelga o consume memoria, no tumba la API.
"""
import json
import sys

from .baseline import primera_sala_que_cabe
from .indicadores import calcular
from .solver import resolver


def main() -> None:
    p = json.load(sys.stdin)
    salas, secciones = p["salas"], p["secciones"]
    res = resolver(salas, secciones, p.get("lam", 0.0), p.get("max_segundos", 60.0), p.get("hilos", 8), p.get("fijas"), p.get("traslados"))
    res["indicadores_base"] = calcular(salas, secciones, primera_sala_que_cabe(salas, secciones), p.get("traslados"))
    json.dump(res, sys.stdout)


if __name__ == "__main__":
    main()
