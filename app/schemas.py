"""Esquemas Pydantic v2: todo intercambio con la API y toda fila de planilla pasa por aquí."""
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .engine.horario import parsear_horario

TipoSala = Literal["catedra", "laboratorio"]
CATEGORIAS = ["proyector", "computador", "aire_acondicionado", "insumos", "mobiliario", "otro"]


def _norm_tipo(v):
    if isinstance(v, str):
        v = v.strip().lower().replace("á", "a")
    return v


class SalaIn(BaseModel):
    codigo: str = Field(min_length=1, max_length=40)
    edificio: str = Field(min_length=1, max_length=80)
    piso: int
    capacidad: int = Field(gt=0)
    tipo: TipoSala

    _t = field_validator("tipo", mode="before")(_norm_tipo)

    @field_validator("codigo", "edificio", mode="before")
    @classmethod
    def _txt(cls, v):
        return str(v).strip() if v is not None else v


class SeccionIn(BaseModel):
    curso: str = Field(min_length=1, max_length=40)
    seccion: str = Field(min_length=1, max_length=10)
    inscritos: int = Field(gt=0)
    nivel: int = Field(ge=1)
    tipo_sala: TipoSala
    horario: str
    departamento: str = "GENERAL"

    _t = field_validator("tipo_sala", mode="before")(_norm_tipo)

    @field_validator("curso", "seccion", "departamento", mode="before")
    @classmethod
    def _txt(cls, v):
        return str(v).strip() if v is not None else v

    @field_validator("horario")
    @classmethod
    def _horario(cls, v):
        parsear_horario(v)  # ValueError con mensaje claro
        return v


class TrasladoIn(BaseModel):
    edificio_a: str = Field(min_length=1, max_length=80)
    edificio_b: str = Field(min_length=1, max_length=80)
    minutos: float = Field(ge=0, le=120)

    @field_validator("edificio_a", "edificio_b", mode="before")
    @classmethod
    def _txt(cls, v):
        return str(v).strip() if v is not None else v


class ErrorFila(BaseModel):
    fila: int | None  # fila de la planilla (la 1 es el encabezado); None si el error es de toda la planilla
    columna: str | None
    mensaje: str


class ResultadoCarga(BaseModel):
    ok: bool
    filas_leidas: int
    filas_cargadas: int = 0
    errores: list[ErrorFila] = []


class CorridaIn(BaseModel):
    semestre: str = Field(min_length=1, max_length=10)
    departamentos: list[str] = Field(default_factory=list, description="Vacío = todos")
    lam: float = Field(default=0.0, ge=0, description="λ (asientos vacíos que se acepta pagar por ahorrar 1 minuto de traslado): 0 = plan Básico (solo aforo); >0 = plan Pro (aforo + tiempos de traslado)")
    max_segundos: float | None = Field(default=None, gt=0, le=600)
    fijas: dict[str, str] = Field(default_factory=dict, description='Fija una sala: {"CURSO-SEC": "COD_SALA"}')


class TicketIn(BaseModel):
    sala: str = Field(min_length=1)
    categoria: Literal["proyector", "computador", "aire_acondicionado", "insumos", "mobiliario", "otro"]
    descripcion: str = Field(default="", max_length=1000)


class TicketPatch(BaseModel):
    estado: Literal["abierto", "en_curso", "resuelto"]
