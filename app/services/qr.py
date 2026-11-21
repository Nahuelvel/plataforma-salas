"""B4 · Placas QR: un código por sala, corrección de errores nivel H (30 %)."""
import io

import qrcode
from qrcode.constants import ERROR_CORRECT_H

from ..config import settings


def url_sala(codigo: str) -> str:
    return f"{settings.base_url.rstrip('/')}/r/{codigo}"


def png_qr(codigo: str) -> bytes:
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_H, box_size=12, border=4)
    qr.add_data(url_sala(codigo))
    qr.make(fit=True)
    buf = io.BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(buf, format="PNG")
    return buf.getvalue()
