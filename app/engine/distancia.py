"""Distancia entre salas: metros entre edificios + 10 m por piso de diferencia."""
import math

METROS_POR_PISO = 10


def distancia(sala_a: dict, sala_b: dict) -> int:
    """Cada sala es un dict con edificio_x, edificio_y (m) y piso."""
    ax, ay = sala_a.get("edificio_x") or 0.0, sala_a.get("edificio_y") or 0.0
    bx, by = sala_b.get("edificio_x") or 0.0, sala_b.get("edificio_y") or 0.0
    metros = math.hypot(ax - bx, ay - by)
    pisos = abs(int(sala_a.get("piso", 0)) - int(sala_b.get("piso", 0)))
    return round(metros + METROS_POR_PISO * pisos)
