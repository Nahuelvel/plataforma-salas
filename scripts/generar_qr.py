"""Genera de una vez la placa QR de cada sala (PNG con el código de sala y la URL corta impresos como respaldo).

    python -m scripts.generar_qr salas.xlsx carpeta_salida [--base-url https://salas.midominio.cl]

Imprimir en vinilo laminado de 10 × 10 cm (el QR usa corrección de errores nivel H).
"""
import argparse
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont
from qrcode.constants import ERROR_CORRECT_H

from app.validacion import leer_planilla, validar

DPI = 300
LADO = round(10 / 2.54 * DPI)  # 10 cm


def placa(codigo: str, url: str) -> Image.Image:
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_H, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    lienzo = Image.new("RGB", (LADO, LADO), "white")
    lado_qr = int(LADO * 0.62)
    lienzo.paste(img_qr.resize((lado_qr, lado_qr), Image.NEAREST), ((LADO - lado_qr) // 2, int(LADO * 0.19)))
    d = ImageDraw.Draw(lienzo)

    def fuente(px):
        for nombre in ("DejaVuSans-Bold.ttf", "Arial.ttf"):
            try:
                return ImageFont.truetype(nombre, px)
            except OSError:
                pass
        return ImageFont.load_default()

    d.text((LADO // 2, int(LADO * 0.06)), "¿Algo no funciona?", fill="black", font=fuente(int(LADO * 0.065)), anchor="mm")
    d.text((LADO // 2, int(LADO * 0.13)), "Escanea y avísanos", fill="black", font=fuente(int(LADO * 0.065)), anchor="mm")
    d.text((LADO // 2, int(LADO * 0.88)), codigo, fill="black", font=fuente(int(LADO * 0.07)), anchor="mm")
    d.text((LADO // 2, int(LADO * 0.95)), url.replace("https://", "").replace("http://", ""), fill="black", font=fuente(int(LADO * 0.04)), anchor="mm")
    return lienzo


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("salas"), ap.add_argument("salida")
    ap.add_argument("--base-url", default="http://localhost:8000")
    a = ap.parse_args()
    with open(a.salas, "rb") as f:
        validas, errores = validar("salas", leer_planilla(f.read(), a.salas))
    if errores:
        raise SystemExit(f"salas con errores: {errores[:3]}")
    out = Path(a.salida)
    out.mkdir(parents=True, exist_ok=True)
    for m in validas:
        placa(m.codigo, f"{a.base_url.rstrip('/')}/r/{m.codigo}").save(out / f"qr_{m.codigo}.png", dpi=(DPI, DPI))
    print(f"{len(validas)} placas en {out}")


if __name__ == "__main__":
    main()
