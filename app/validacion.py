"""Lectura y validación de planillas (Excel/CSV). Cada error indica fila y columna (criterio CA-06)."""
import io
from collections import Counter

import pandas as pd
from pydantic import ValidationError

from .schemas import ErrorFila, SalaIn, SeccionIn, TrasladoIn

COLUMNAS = {
    "salas": {"obligatorias": ["codigo_sala", "edificio", "piso", "capacidad", "tipo"], "opcionales": []},
    "traslados": {"obligatorias": ["edificio_a", "edificio_b", "minutos"], "opcionales": []},
    "secciones": {"obligatorias": ["curso", "seccion", "inscritos", "nivel", "tipo_sala", "horario"], "opcionales": ["departamento"]},
}
# nombre de columna de la planilla → campo del esquema
ALIAS = {"codigo_sala": "codigo"}
ALIAS_INV = {v: k for k, v in ALIAS.items()}


def leer_planilla(contenido: bytes, nombre: str) -> pd.DataFrame:
    """Lee xlsx o csv como texto/objetos (sin inferir tipos: así detectamos «abc» en una capacidad)."""
    if nombre.lower().endswith(".csv"):
        return pd.read_csv(io.BytesIO(contenido), dtype=object, keep_default_na=False, sep=None, engine="python")
    return pd.read_excel(io.BytesIO(contenido), dtype=object)


def _vacio(v) -> bool:
    return v is None or (isinstance(v, float) and pd.isna(v)) or (isinstance(v, str) and not v.strip()) or v is pd.NA


def _fila_a_dict(fila: dict) -> dict:
    out = {}
    for k, v in fila.items():
        if _vacio(v):
            continue
        if isinstance(v, str):
            v = v.strip()
        # enteros de Excel que llegan como 30.0
        if isinstance(v, float) and v.is_integer():
            v = int(v)
        out[ALIAS.get(k, k)] = v
    return out


def _mensaje_pydantic(e: dict) -> str:
    t = e["type"]
    if t == "missing":
        return "falta el valor"
    if t in ("int_parsing", "int_from_float", "float_parsing"):
        return "debe ser un número válido"
    if t == "greater_than":
        return f"debe ser mayor que {e['ctx']['gt']}"
    if t == "greater_than_equal":
        return f"debe ser mayor o igual que {e['ctx']['ge']}"
    if t == "literal_error":
        return "valor no permitido; use «catedra» o «laboratorio»"
    if t == "value_error":
        return str(e["ctx"]["error"])
    return e["msg"]


def validar(kind: str, df: pd.DataFrame, salas_existentes: dict[str, dict] | None = None, edificios: set[str] | None = None) -> tuple[list, list[ErrorFila]]:
    """Devuelve (filas válidas como objetos del esquema, errores). Si hay errores, no se carga nada."""
    esquema = {"salas": SalaIn, "secciones": SeccionIn, "traslados": TrasladoIn}[kind]
    cfg = COLUMNAS[kind]
    errores: list[ErrorFila] = []

    df = df.rename(columns=lambda c: str(c).strip().lower())
    faltantes = [c for c in cfg["obligatorias"] if c not in df.columns]
    for c in faltantes:
        errores.append(ErrorFila(fila=1, columna=c, mensaje="columna obligatoria ausente"))
    if faltantes:
        return [], errores
    if len(df) == 0:
        return [], [ErrorFila(fila=None, columna=None, mensaje="la planilla no tiene filas")]

    validas: list = []
    for i, fila in enumerate(df.to_dict("records")):
        n = i + 2  # fila de Excel: +1 por el encabezado, +1 porque Excel parte en 1
        try:
            validas.append((n, esquema.model_validate(_fila_a_dict(fila))))
        except ValidationError as ex:
            for e in ex.errors():
                campo = str(e["loc"][0]) if e["loc"] else None
                errores.append(ErrorFila(fila=n, columna=ALIAS_INV.get(campo, campo), mensaje=_mensaje_pydantic(e)))

    # Duplicados
    if kind == "salas":
        llave, col = (lambda m: m.codigo), "codigo_sala"
    elif kind == "secciones":
        llave, col = (lambda m: (m.curso, m.seccion)), "seccion"
    else:
        llave, col = (lambda m: frozenset((m.edificio_a, m.edificio_b))), "edificio_b"
    cuenta = Counter(llave(m) for _, m in validas)
    vistos = set()
    for n, m in validas:
        k = llave(m)
        if cuenta[k] > 1:
            if k in vistos:
                errores.append(ErrorFila(fila=n, columna=col, mensaje=f"duplicado: {k if kind != 'traslados' else m.edificio_a + ' – ' + m.edificio_b}"))
            vistos.add(k)

    # Traslados: origen y destino distintos; ambos edificios deben existir en las salas cargadas
    if kind == "traslados":
        for n, m in validas:
            if m.edificio_a == m.edificio_b:
                errores.append(ErrorFila(fila=n, columna="edificio_b", mensaje="origen y destino son el mismo edificio (dentro de un edificio el traslado es 0 y no se declara)"))
            for c, nombre in (("edificio_a", m.edificio_a), ("edificio_b", m.edificio_b)):
                if edificios is not None and nombre not in edificios:
                    errores.append(ErrorFila(fila=n, columna=c, mensaje=f"edificio «{nombre}» no existe en las salas cargadas"))

    # Secciones: debe existir al menos una sala del tipo pedido con capacidad suficiente
    if kind == "secciones" and salas_existentes is not None:
        for n, m in validas:
            if not any(s["tipo"] == m.tipo_sala and s["capacidad"] >= m.inscritos for s in salas_existentes.values()):
                errores.append(ErrorFila(fila=n, columna="tipo_sala", mensaje=f"no existe una sala de tipo «{m.tipo_sala}» con capacidad ≥ {m.inscritos}"))

    errores.sort(key=lambda e: (e.fila or 0, e.columna or ""))
    return [m for _, m in validas], errores
