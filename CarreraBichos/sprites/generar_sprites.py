# -*- coding: utf-8 -*-
"""Regenera los PNG de los bichos a partir de bichos.html (dibujados con <canvas>).

Uso (desde la raíz del repo):
    python CarreraBichos/sprites/generar_sprites.py [ruta-a-chrome]

Abre bichos.html con Chrome/Chromium headless (el mismo que usa html2image), lee
los sprites que exporta el canvas y los guarda como {bicho}_{gesto}.png en esta
carpeta. Sólo hace falta correrlo al cambiar los dibujos: los PNG se versionan.
"""
import base64
import html
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

CARPETA = os.path.dirname(os.path.abspath(__file__))
PX = 384  # lado de cada sprite: alcanza para el podio (150 px x supersampling x 1.28)

CANDIDATOS = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "C:/Program Files/Google/Chrome/Application/chrome.exe"]


def buscar_chrome():
    for c in CANDIDATOS:
        ruta = shutil.which(c) or (c if os.path.isfile(c) else None)
        if ruta:
            return ruta
    sys.exit("No encontré Chrome/Chromium: pasá la ruta como argumento.")


def buscar_navegador():
    # Preferimos chrome-headless-shell de Playwright si está: arranca más rápido y no
    # necesita D-Bus ni sesión gráfica.
    for raiz in ("/opt/pw-browsers", os.path.expanduser("~/.cache/ms-playwright")):
        if os.path.isdir(raiz):
            for nombre in sorted(os.listdir(raiz), reverse=True):
                for sub in ("chrome-headless-shell-linux64", "chrome-linux"):
                    for exe in ("chrome-headless-shell", "chrome"):
                        ruta = os.path.join(raiz, nombre, sub, exe)
                        if os.path.isfile(ruta):
                            return ruta
    return buscar_chrome()


def main():
    chrome = sys.argv[1] if len(sys.argv) > 1 else buscar_navegador()
    url = "file://" + os.path.join(CARPETA, "bichos.html").replace("\\", "/") + "?exportar&px={}".format(PX)
    with tempfile.TemporaryDirectory() as perfil:
        dom = subprocess.run(
            [chrome, "--headless", "--no-sandbox", "--disable-gpu", "--user-data-dir=" + perfil,
             "--dump-dom", url],
            check=True, capture_output=True, text=True, timeout=120,
        ).stdout
    m = re.search(r'<pre id="sprites">(.*?)</pre>', dom, re.S)
    if not m:
        sys.exit("bichos.html no exportó los sprites (¿error de JS?).")
    sprites = json.loads(html.unescape(m.group(1)))
    from PIL import Image
    for nombre, data_url in sorted(sprites.items()):
        png = Image.open(io.BytesIO(base64.b64decode(data_url.split(",", 1)[1])))
        # Paleta de 256 colores con alfa: pesa ~4 veces menos y no se nota al achicar.
        png.quantize(256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE).save(
            os.path.join(CARPETA, nombre + ".png"), optimize=True)
    print("{} sprites guardados en {}".format(len(sprites), CARPETA))


if __name__ == "__main__":
    main()
