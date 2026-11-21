"""Orquesta una corrida: arma el JSON, lanza el motor como proceso aparte y guarda el resultado."""
import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..engine.horario import DIAS
from ..models import Asignacion, Corrida, Sala, Seccion

log = logging.getLogger("corridas")
RAIZ = Path(__file__).resolve().parents[2]  # raíz del repo, para que «-m app.engine.runner» funcione desde cualquier carpeta


def datos_para_motor(db: Session, semestre: str, departamentos: list[str]):
    salas = [
        {"codigo": s.codigo, "edificio": s.edificio.nombre, "edificio_x": s.edificio.x, "edificio_y": s.edificio.y,
         "piso": s.piso, "capacidad": s.capacidad, "tipo": s.tipo}
        for s in db.scalars(select(Sala))
    ]
    q = select(Seccion).where(Seccion.semestre == semestre)
    if departamentos:
        q = q.where(Seccion.departamento.in_(departamentos))
    secciones = [
        {"curso": s.curso, "seccion": s.seccion, "departamento": s.departamento, "inscritos": s.inscritos,
         "nivel": s.nivel, "tipo_sala": s.tipo_sala, "bloques": s.bloques}
        for s in db.scalars(q)
    ]
    return salas, secciones


def ejecutar_motor(payload: dict, timeout_extra: float = 30.0) -> dict:
    """Lanza ``python -m app.engine.runner`` (proceso separado). El tope real lo pone CP-SAT; el timeout es red de seguridad."""
    proc = subprocess.run(
        [sys.executable, "-m", "app.engine.runner"],
        input=json.dumps(payload), capture_output=True, text=True,
        timeout=payload["max_segundos"] + timeout_extra, cwd=RAIZ,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip()[-500:] or "el motor terminó con error")
    return json.loads(proc.stdout)


def procesar_corrida(session_factory, corrida_id: int) -> None:
    """Se ejecuta en segundo plano. Resuelve por departamento (escala) y junta los resultados."""
    db: Session = session_factory()
    try:
        c = db.get(Corrida, corrida_id)
        p = c.parametros
        salas, secciones = datos_para_motor(db, c.semestre, p["departamentos"])
        if not secciones:
            c.estado, c.mensaje = "error", "No hay secciones cargadas para ese semestre/departamentos"
            db.commit()
            return
        # Los departamentos comparten salas: resolverlos por separado produciría choques entre ellos.
        # Por eso se resuelve junto todo lo seleccionado (el LLD escala eligiendo departamentos en cada corrida).
        res = ejecutar_motor({"salas": salas, "secciones": secciones, "lam": p["lam"], "max_segundos": p["max_segundos"],
                              "hilos": settings.solver_hilos, "fijas": p.get("fijas") or None})
        asignacion, tiempo, estado = res["asignacion"], res["tiempo_s"], res["estado"]
        mensajes = [res["mensaje"]] if res["mensaje"] else []
        indicadores, base_tot = res["indicadores"], res["indicadores_base"]

        sala_por_cod = {s["codigo"]: s for s in salas}
        sec_por_clave = {f"{s['curso']}-{s['seccion']}": s for s in secciones}
        for k, cod in asignacion.items():
            sec = sec_por_clave[k]
            for b in sec["bloques"]:
                c.asignaciones.append(Asignacion(
                    curso=sec["curso"], seccion=sec["seccion"], departamento=sec["departamento"], dia=b["dia"],
                    inicio=b["inicio"], fin=b["fin"], sala_codigo=cod,
                    capacidad=sala_por_cod[cod]["capacidad"], inscritos=sec["inscritos"]))
        c.estado, c.mensaje, c.tiempo_s = estado, "; ".join(mensajes), round(tiempo, 3)
        c.indicadores, c.indicadores_base = indicadores, base_tot or {}
        db.commit()
    except Exception as e:  # la corrida queda marcada como error en vez de quedarse «en curso»
        log.exception("Falló la corrida %s", corrida_id)
        db.rollback()
        c = db.get(Corrida, corrida_id)
        c.estado, c.mensaje = "error", str(e)[:500]
        db.commit()
    finally:
        db.close()


def tiene_clase_ahora(db: Session, sala_codigo: str, ahora: datetime | None = None) -> bool:
    """Prioridad automática de tickets: alta si la sala tiene clase en el bloque actual (según la última corrida publicada)."""
    ahora = ahora or datetime.now(ZoneInfo(settings.zona_horaria))
    if ahora.weekday() >= len(DIAS):
        return False
    minuto = ahora.hour * 60 + ahora.minute
    ultima = db.scalars(select(Corrida).where(Corrida.estado.in_(["optima", "factible"])).order_by(Corrida.id.desc())).first()
    if not ultima:
        return False
    return any(a.sala_codigo == sala_codigo and a.dia == DIAS[ahora.weekday()] and a.inicio <= minuto < a.fin for a in ultima.asignaciones)
