"""Acceso con usuario y contraseña (HTTP Basic). Dos roles: administración y soporte."""
import secrets

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .config import settings

_basic = HTTPBasic(realm="Plataforma de salas")


def _rol(cred: HTTPBasicCredentials) -> str | None:
    def ok(u, p, usuario, clave):
        return secrets.compare_digest(u.encode(), usuario.encode()) & secrets.compare_digest(p.encode(), clave.encode())

    if ok(cred.username, cred.password, settings.admin_user, settings.admin_password):
        return "administracion"
    if ok(cred.username, cred.password, settings.soporte_user, settings.soporte_password):
        return "soporte"
    return None


def usuario_actual(cred: HTTPBasicCredentials = Depends(_basic)) -> str:
    rol = _rol(cred)
    if rol is None:
        raise HTTPException(401, "Usuario o contraseña incorrectos", headers={"WWW-Authenticate": 'Basic realm="Plataforma de salas"'})
    return rol


def solo_administracion(rol: str = Depends(usuario_actual)) -> str:
    if rol != "administracion":
        raise HTTPException(403, "Solo para administración")
    return rol
