"""Tiempo de traslado entre salas, en minutos.

    tiempo = minutos entre edificios (tabla medida a mano) + MIN_POR_PISO × |piso₁ − piso₂|

Dentro de un mismo edificio el término de edificios es 0. Si falta un par de edificios en la tabla se usa
``defecto_min`` (la API avisa en la corrida qué pares faltaban).
"""

MIN_POR_PISO = 0.5
DEFECTO_MIN = 5.0


def tabla(traslados: list | None) -> dict[frozenset, float]:
    """traslados: [(edificio_a, edificio_b, minutos), ...] → {frozenset({a, b}): minutos} (simétrica)."""
    return {frozenset((a, b)): float(m) for a, b, m in (traslados or [])}


def tiempo(sala_a: dict, sala_b: dict, t: dict[frozenset, float], defecto_min: float = DEFECTO_MIN, min_por_piso: float = MIN_POR_PISO) -> float:
    """Cada sala es un dict con ``edificio`` (nombre) y ``piso``."""
    ea, eb = sala_a["edificio"], sala_b["edificio"]
    entre = 0.0 if ea == eb else t.get(frozenset((ea, eb)), defecto_min)
    return round(entre + min_por_piso * abs(int(sala_a.get("piso", 0)) - int(sala_b.get("piso", 0))), 2)


def pares_faltantes(edificios: list[str], t: dict[frozenset, float]) -> list[tuple[str, str]]:
    ed = sorted(set(edificios))
    return [(a, b) for i, a in enumerate(ed) for b in ed[i + 1:] if frozenset((a, b)) not in t]
