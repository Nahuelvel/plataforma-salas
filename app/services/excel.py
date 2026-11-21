"""Exportación de la malla (PA-06): sección, curso, bloque, sala, capacidad e inscritos."""
import io

import pandas as pd

from ..engine.horario import etiqueta_bloque
from ..models import Corrida

INDICADORES = {
    "asientos_vacios": "Asientos vacíos",
    "aforo_util_pct": "Aforo útil (%)",
    "distancia_promedio": "Distancia promedio entre clases consecutivas (m)",
    "choques": "Choques sala-bloque",
    "violaciones_capacidad": "Violaciones de capacidad/tipo",
    "secciones_sin_asignar": "Secciones sin asignar",
}


def malla_excel(c: Corrida) -> bytes:
    filas = [
        {
            "sección": f"{a.curso}-{a.seccion}",
            "curso": a.curso,
            "departamento": a.departamento,
            "bloque": etiqueta_bloque({"dia": a.dia, "inicio": a.inicio, "fin": a.fin}),
            "sala": a.sala_codigo,
            "capacidad": a.capacidad,
            "inscritos": a.inscritos,
        }
        for a in sorted(c.asignaciones, key=lambda a: (a.curso, a.seccion, a.dia, a.inicio))
    ]
    ind = [{"indicador": nombre, "plataforma": c.indicadores.get(k), "referencia (primera sala que cabe)": c.indicadores_base.get(k)} for k, nombre in INDICADORES.items()]
    ind += [{"indicador": "Estado", "plataforma": c.estado, "referencia (primera sala que cabe)": ""},
            {"indicador": "Tiempo de cálculo (s)", "plataforma": c.tiempo_s, "referencia (primera sala que cabe)": ""},
            {"indicador": "Parámetros", "plataforma": str(c.parametros), "referencia (primera sala que cabe)": ""}]
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        pd.DataFrame(filas, columns=["sección", "curso", "departamento", "bloque", "sala", "capacidad", "inscritos"]).to_excel(w, sheet_name="Malla", index=False)
        pd.DataFrame(ind).to_excel(w, sheet_name="Indicadores", index=False)
        for ws in w.book.worksheets:
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = min(60, max(len(str(c.value or "")) for c in col) + 2)
    return buf.getvalue()
