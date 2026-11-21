"""Alerta por correo a soporte (SMTP). Sin SMTP_HOST configurado solo deja una línea en el log."""
import logging
import smtplib
from email.message import EmailMessage

from ..config import settings

log = logging.getLogger("correo")


def avisar_soporte(asunto: str, cuerpo: str) -> None:
    if not settings.smtp_host:
        log.info("SMTP no configurado; alerta no enviada: %s", asunto)
        return
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = asunto, settings.smtp_user or settings.correo_soporte, settings.correo_soporte
    msg.set_content(cuerpo)
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as s:
            s.starttls()
            if settings.smtp_user:
                s.login(settings.smtp_user, settings.smtp_password)
            s.send_message(msg)
    except Exception:  # un correo caído no debe romper el reporte
        log.exception("No se pudo enviar el correo de alerta")
