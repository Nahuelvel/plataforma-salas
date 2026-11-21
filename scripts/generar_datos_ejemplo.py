"""Genera planillas FICTICIAS de ejemplo (Ing. Eléctrica + Geología) para desarrollar y probar sin datos reales.

    python scripts/generar_datos_ejemplo.py [carpeta_salida] [factor_escala]

factor_escala = 3 genera un caso 3 veces más grande (prueba de escala de PA-04).
"""
import random
import sys
from pathlib import Path

import pandas as pd

EDIFICIOS = {"Eléctrica": (0, 0), "Geología": (260, 140), "Central": (120, 40)}
SALAS = [  # (código, edificio, piso, capacidad, tipo)
    ("E-101", "Eléctrica", 1, 30, "catedra"), ("E-102", "Eléctrica", 1, 45, "catedra"), ("E-201", "Eléctrica", 2, 60, "catedra"),
    ("E-LAB1", "Eléctrica", 1, 24, "laboratorio"), ("E-LAB2", "Eléctrica", 2, 20, "laboratorio"),
    ("G-101", "Geología", 1, 35, "catedra"), ("G-102", "Geología", 1, 50, "catedra"), ("G-201", "Geología", 2, 80, "catedra"),
    ("G-LAB1", "Geología", 1, 25, "laboratorio"),
    ("C-101", "Central", 1, 40, "catedra"), ("C-102", "Central", 1, 70, "catedra"), ("C-201", "Central", 2, 100, "catedra"),
    ("C-LAB1", "Central", 1, 30, "laboratorio"), ("C-202", "Central", 2, 55, "catedra"),
]
PATRONES = ["LU {a}; MI {a}", "MA {a}; JU {a}", "LU {a}; MI {b}", "MA {b}; VI {a}", "VI {a}"]
HORAS = ["08:15-09:45", "10:00-11:30", "11:45-13:15", "14:30-16:00", "16:15-17:45"]


def generar(salida: Path, factor: int = 1, semilla: int = 7) -> None:
    rnd = random.Random(semilla)
    salida.mkdir(parents=True, exist_ok=True)
    salas = []
    for i in range(factor):
        for cod, ed, piso, cap, tipo in SALAS:
            x, y = EDIFICIOS[ed]
            salas.append({"codigo_sala": cod if i == 0 else f"{cod}-{i}", "edificio": ed if i == 0 else f"{ed} {i}",
                          "piso": piso, "capacidad": cap, "tipo": tipo, "edificio_x": x + 400 * i, "edificio_y": y})
    secciones = []
    for depto, prefijo, n_cursos in [("ELECTRICA", "ELO", 9 * factor), ("GEOLOGIA", "GEO", 8 * factor)]:
        for c in range(n_cursos):
            nivel = 1 + c % 4
            for sec in range(1, rnd.choice([1, 2, 2]) + 1):
                lab = rnd.random() < 0.18
                a, b = rnd.sample(HORAS, 2)
                secciones.append({
                    "curso": f"{prefijo}{100 * nivel + c:03d}", "seccion": sec, "departamento": depto,
                    "inscritos": rnd.randint(10, 24) if lab else rnd.randint(18, 58), "nivel": nivel,
                    "tipo_sala": "laboratorio" if lab else "catedra", "horario": rnd.choice(PATRONES).format(a=a, b=b)})
    pd.DataFrame(salas).to_excel(salida / "salas.xlsx", index=False)
    pd.DataFrame(secciones).to_excel(salida / "secciones.xlsx", index=False)
    print(f"{len(salas)} salas y {len(secciones)} secciones en {salida}")


if __name__ == "__main__":
    generar(Path(sys.argv[1] if len(sys.argv) > 1 else "data/ejemplo"), int(sys.argv[2]) if len(sys.argv) > 2 else 1)
