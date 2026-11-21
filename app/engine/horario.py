"""Lectura del campo «horario»: ``LU 10:15-11:45; MI 10:15-11:45``."""
import re

DIAS = ["LU", "MA", "MI", "JU", "VI", "SA"]
_PATRON = re.compile(r"^(LU|MA|MI|JU|VI|SA)\s+([01]?\d|2[0-3]):([0-5]\d)\s*-\s*([01]?\d|2[0-3]):([0-5]\d)$")


def a_minutos(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def a_hhmm(minutos: int) -> str:
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def parsear_horario(texto: str) -> list[dict]:
    """Devuelve [{dia, inicio, fin}] con inicio/fin en minutos desde las 00:00.

    Lanza ValueError con un mensaje claro si el formato es inválido.
    """
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("horario vacío")
    bloques = []
    for trozo in texto.split(";"):
        trozo = trozo.strip()
        m = _PATRON.match(trozo.upper())
        if not m:
            raise ValueError(f"horario inválido «{trozo}»; formato esperado «LU 10:15-11:45; MI 10:15-11:45»")
        dia, h1, m1, h2, m2 = m.groups()
        ini, fin = int(h1) * 60 + int(m1), int(h2) * 60 + int(m2)
        if fin <= ini:
            raise ValueError(f"horario inválido «{trozo}»: la hora de término debe ser posterior al inicio")
        bloques.append({"dia": dia, "inicio": ini, "fin": fin})
    # Los bloques de una misma sección no pueden traslaparse entre sí
    for i, a in enumerate(bloques):
        for b in bloques[i + 1:]:
            if a["dia"] == b["dia"] and a["inicio"] < b["fin"] and b["inicio"] < a["fin"]:
                raise ValueError("la sección tiene bloques que se traslapan entre sí")
    return bloques


def etiqueta_bloque(b: dict) -> str:
    return f"{b['dia']} {a_hhmm(b['inicio'])}-{a_hhmm(b['fin'])}"


def se_traslapan(a: dict, b: dict) -> bool:
    return a["dia"] == b["dia"] and a["inicio"] < b["fin"] and b["inicio"] < a["fin"]
