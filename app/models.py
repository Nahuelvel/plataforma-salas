"""B1 · Tablas de la base de datos (modelo de datos del LLD).

Simplificación del PMV: los bloques horarios de una sección viven como JSON dentro de ``Seccion.bloques``
(no hay tabla «Bloque» aparte) y ``Asignacion`` guarda los datos de la sección/sala tal como estaban al
correr, para que una corrida antigua siga siendo legible aunque se recarguen las planillas.
"""
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def ahora() -> datetime:
    return datetime.now()


class Edificio(Base):
    __tablename__ = "edificio"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True)


class Traslado(Base):
    """Minutos caminando entre dos edificios (simétrico: se guarda una sola vez por par)."""
    __tablename__ = "traslado"
    __table_args__ = (UniqueConstraint("edificio_a_id", "edificio_b_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    edificio_a_id: Mapped[int] = mapped_column(ForeignKey("edificio.id"))
    edificio_b_id: Mapped[int] = mapped_column(ForeignKey("edificio.id"))
    minutos: Mapped[float] = mapped_column(Float)


class Sala(Base):
    __tablename__ = "sala"
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    edificio_id: Mapped[int] = mapped_column(ForeignKey("edificio.id"))
    piso: Mapped[int] = mapped_column(Integer, default=1)
    capacidad: Mapped[int] = mapped_column(Integer)
    tipo: Mapped[str] = mapped_column(String(20))  # catedra | laboratorio
    edificio: Mapped[Edificio] = relationship()


class Seccion(Base):
    __tablename__ = "seccion"
    __table_args__ = (UniqueConstraint("semestre", "curso", "seccion"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    semestre: Mapped[str] = mapped_column(String(10), index=True)
    curso: Mapped[str] = mapped_column(String(40))
    seccion: Mapped[str] = mapped_column(String(10))
    departamento: Mapped[str] = mapped_column(String(80), default="GENERAL", index=True)
    inscritos: Mapped[int] = mapped_column(Integer)
    nivel: Mapped[int] = mapped_column(Integer)
    tipo_sala: Mapped[str] = mapped_column(String(20))
    bloques: Mapped[list] = mapped_column(JSON)  # [{dia, inicio, fin}] (minutos)


class Corrida(Base):
    __tablename__ = "corrida"
    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=ahora)
    semestre: Mapped[str] = mapped_column(String(10))
    parametros: Mapped[dict] = mapped_column(JSON)  # departamentos, lambda, límites… (permite repetirla)
    estado: Mapped[str] = mapped_column(String(20), default="en_curso")  # en_curso|optima|factible|infactible|error
    mensaje: Mapped[str] = mapped_column(Text, default="")
    tiempo_s: Mapped[float] = mapped_column(Float, default=0.0)
    indicadores: Mapped[dict] = mapped_column(JSON, default=dict)
    indicadores_base: Mapped[dict] = mapped_column(JSON, default=dict)  # «primera sala donde cabe», para comparar
    asignaciones: Mapped[list["Asignacion"]] = relationship(cascade="all, delete-orphan")


class Asignacion(Base):
    __tablename__ = "asignacion"
    id: Mapped[int] = mapped_column(primary_key=True)
    corrida_id: Mapped[int] = mapped_column(ForeignKey("corrida.id"), index=True)
    curso: Mapped[str] = mapped_column(String(40))
    seccion: Mapped[str] = mapped_column(String(10))
    departamento: Mapped[str] = mapped_column(String(80))
    dia: Mapped[str] = mapped_column(String(2))
    inicio: Mapped[int] = mapped_column(Integer)
    fin: Mapped[int] = mapped_column(Integer)
    sala_codigo: Mapped[str] = mapped_column(String(40), index=True)
    capacidad: Mapped[int] = mapped_column(Integer)
    inscritos: Mapped[int] = mapped_column(Integer)


class Ticket(Base):
    __tablename__ = "ticket"
    id: Mapped[int] = mapped_column(primary_key=True)
    sala_id: Mapped[int] = mapped_column(ForeignKey("sala.id"), index=True)
    categoria: Mapped[str] = mapped_column(String(30))
    descripcion: Mapped[str] = mapped_column(Text, default="")
    estado: Mapped[str] = mapped_column(String(20), default="abierto")  # abierto|en_curso|resuelto
    prioridad: Mapped[str] = mapped_column(String(10), default="normal")  # alta si la sala tiene clase ahora
    creado: Mapped[datetime] = mapped_column(DateTime, default=ahora)
    cerrado: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sala: Mapped[Sala] = relationship()
