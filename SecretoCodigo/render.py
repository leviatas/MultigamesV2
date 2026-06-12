"""Genera imágenes PNG del tablero de Secreto Código."""
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
import time
import tempfile

_CHROME = "/usr/bin/chromium"
_CHROME_FLAGS = ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu"]

CELL_W = 200
CELL_H = 200
PAD = 10
COLS = 5
ROWS = 5
FONT_SIZE = 46

_FONT_PATH = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

# (background_hex, text_hex)
_PALETTE = {
    # Sin revelar
    "unrevealed":    ("#FFE5CC", "#1A1A1A"),
    # Competitivo — tipo de carta sin revelar
    "rojo":          ("#C0392B", "#FFFFFF"),
    "azul":          ("#1A5276", "#FFFFFF"),
    "neutral":       ("#797D7F", "#FFFFFF"),
    "asesino":       ("#1C2833", "#FFFFFF"),
    # Dúo — clave privada (solo perspectiva propia)
    "agente":        ("#1E8449", "#FFFFFF"),
    # Reveladas — competitivo
    "revealed_rojo":     ("#F1948A", "#5D0000"),
    "revealed_azul":     ("#7FB3D3", "#0A2942"),
    "revealed_neutral":  ("#CACFD2", "#3D3D3D"),
    "revealed_asesino":  ("#4D5656", "#CCCCCC"),
    # Reveladas — modo Dúo público
    "revealed_agente":   ("#27AE60", "#FFFFFF"),   # agente encontrado → verde
    "revealed_miss":     ("#C8C8C8", "#555555"),   # neutral pisado → gris con marca
    "revealed_asesino_duo": ("#1C2833", "#FFFFFF"),
}
_BG = "#2C3E50"


def _hex_rgb(h):
    if isinstance(h, tuple):
        return h
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _load_font(size):
    try:
        return ImageFont.truetype(_FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()


def _fit_text(draw, text, font_size, max_w):
    for size in range(font_size, 7, -1):
        font = _load_font(size)
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            w = bbox[2] - bbox[0]
        except AttributeError:
            w, _ = draw.textsize(text, font=font)
        if w <= max_w:
            return font, text
    return _load_font(8), text[:12] + "…"


def _draw_cell(draw, x, y, word, numero, bg_hex, fg_hex, mark=None, revealed=False, font_size=None):
    """
    mark    : None | "check" (agente encontrado) | "miss_corner" (neutral pisado)
    revealed: True dibuja tachado diagonal sobre la carta
    """
    bg = _hex_rgb(bg_hex)
    fg = _hex_rgb(fg_hex)
    draw.rectangle([x, y, x + CELL_W - 1, y + CELL_H - 1], fill=bg, outline=_hex_rgb("#FFFFFF"), width=1)

    # Número pequeño arriba-izquierda
    num_font = _load_font(15)
    draw.text((x + 6, y + 5), str(numero), font=num_font, fill=fg)

    if mark == "check":
        draw.text((x + CELL_W - 22, y + 4), "✓", font=num_font, fill=fg)
    elif mark == "miss_corner":
        # Triángulo naranja en esquina superior derecha para indicar "miss"
        pts = [(x + CELL_W - 22, y + 1), (x + CELL_W - 1, y + 1), (x + CELL_W - 1, y + 22)]
        draw.polygon(pts, fill=_hex_rgb("#E67E22"))

    # Palabra centrada — tamaño fijo, sin ajuste automático
    font = _load_font(font_size if font_size is not None else FONT_SIZE)
    label = word.upper()
    try:
        bbox = draw.textbbox((0, 0), label, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        tw, th = draw.textsize(label, font=font)
    tx = x + (CELL_W - tw) // 2
    ty = y + (CELL_H - th) // 2 + 4
    draw.text((tx, ty), label, font=font, fill=fg)

    # Tachado sobre la palabra para cartas ya reveladas
    if revealed:
        strike_y = ty + th // 2
        draw.line([(tx, strike_y), (tx + tw, strike_y)], fill=fg, width=2)


def render_board(tablero, mode="public", key=None, partner_key=None, font_size=None):
    """
    mode        : "public" | "spymaster" | "duo_key" | "duo_public"
    key         : {numero: tipo_str} — clave del jugador (duo_key)
    partner_key : ignorado (mantenido por compatibilidad)
    """
    canvas_w = COLS * CELL_W + (COLS + 1) * PAD
    canvas_h = ROWS * CELL_H + (ROWS + 1) * PAD

    img = Image.new("RGB", (canvas_w, canvas_h), _hex_rgb(_BG))
    draw = ImageDraw.Draw(img)

    for i, card in enumerate(tablero):
        col = i % COLS
        row = i // COLS
        x = PAD + col * (CELL_W + PAD)
        y = PAD + row * (CELL_H + PAD)

        word     = card["word"]
        numero   = card["numero"]
        revealed = card["revealed"]
        tipo     = card.get("tipo") or "neutral"
        mark     = None

        if mode in ("public", "spymaster"):
            if revealed:
                bg, fg = _PALETTE.get(f"revealed_{tipo}", _PALETTE["revealed_neutral"])
                mark = "check" if tipo in ("rojo", "azul", "agente") else None
            else:
                if mode == "spymaster":
                    bg, fg = _PALETTE.get(tipo, _PALETTE["unrevealed"])
                else:
                    bg, fg = _PALETTE["unrevealed"]

        elif mode == "duo_key" and key:
            # Clave privada: solo verde/negro/gris — SIN información del compañero
            tipo_mine = key.get(numero, "neutral")
            if revealed:
                if tipo == "agente":
                    bg, fg = _PALETTE["revealed_agente"]
                    mark = "check"
                elif tipo == "asesino":
                    bg, fg = _PALETTE["revealed_asesino_duo"]
                else:
                    bg, fg = _PALETTE["revealed_miss"]
                    mark = "miss_corner"
            else:
                if tipo_mine == "agente":
                    bg, fg = _PALETTE["agente"]
                elif tipo_mine == "asesino":
                    bg, fg = _PALETTE["asesino"]
                else:
                    bg, fg = _PALETTE["unrevealed"]  # gris uniforme — sin distinción de compañero

        elif mode == "duo_public":
            # Tablero público: sin color por defecto; colores solo al revelar
            if revealed:
                if tipo == "agente":
                    bg, fg = _PALETTE["revealed_agente"]
                    mark = "check"
                elif tipo == "asesino":
                    bg, fg = _PALETTE["revealed_asesino_duo"]
                else:
                    # neutral pisado → gris con marca en esquina
                    bg, fg = _PALETTE["revealed_miss"]
                    mark = "miss_corner"
            else:
                bg, fg = _PALETTE["unrevealed"]  # todas iguales sin revelar

        else:
            bg, fg = _PALETTE["unrevealed"]

        _draw_cell(draw, x, y, word, numero, bg, fg, mark=mark, revealed=revealed, font_size=font_size)

    # Pixel único para evitar caché de Telegram (deduplica imágenes idénticas)
    ts = int(time.time() * 1000) % (256 ** 3)
    r, g, b = ts >> 16, (ts >> 8) & 0xFF, ts & 0xFF
    img.putpixel((0, 0), (r, g, b))

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


_HTML_PALETTE = {
    "unrevealed":         ("#FFE5CC", "#1A1A1A"),
    "rojo":               ("#C0392B", "#FFFFFF"),
    "azul":               ("#1A5276", "#FFFFFF"),
    "neutral":            ("#797D7F", "#FFFFFF"),
    "asesino":            ("#1C2833", "#FFFFFF"),
    "agente":             ("#1E8449", "#FFFFFF"),
    "revealed_rojo":      ("#F1948A", "#5D0000"),
    "revealed_azul":      ("#7FB3D3", "#0A2942"),
    "revealed_neutral":   ("#CACFD2", "#3D3D3D"),
    "revealed_asesino":   ("#4D5656", "#CCCCCC"),
    "revealed_agente":    ("#27AE60", "#FFFFFF"),
    "revealed_miss":      ("#C8C8C8", "#555555"),
    "revealed_asesino_duo": ("#1C2833", "#FFFFFF"),
}


def render_board_html(tablero, mode="public", key=None, font_size=None):
    fs = font_size if font_size is not None else FONT_SIZE
    cell = CELL_W
    pad = PAD
    canvas = COLS * cell + (COLS + 1) * pad

    cells_html = ""
    for card in tablero:
        word = card["word"].upper()
        numero = card["numero"]
        revealed = card["revealed"]
        tipo = card.get("tipo") or "neutral"

        if mode == "spymaster":
            palette_key = f"revealed_{tipo}" if revealed else tipo
        else:
            palette_key = f"revealed_{tipo}" if revealed else "unrevealed"

        bg, fg = _HTML_PALETTE.get(palette_key, _HTML_PALETTE["unrevealed"])
        strike = "text-decoration: line-through;" if revealed else ""
        cells_html += f"""
        <div style="
            width:{cell}px; height:{cell}px;
            background:{bg}; color:{fg};
            display:flex; flex-direction:column;
            align-items:center; justify-content:center;
            border:1px solid #fff; border-radius:4px;
            font-size:{fs}px; font-weight:bold;
            font-family:'Liberation Sans', Arial, sans-serif;
            position:relative; overflow:hidden; {strike}
        ">
            <span style="position:absolute;top:4px;left:6px;font-size:13px;opacity:.7;">{numero}</span>
            <span style="text-align:center;padding:4px;word-break:break-word;line-height:1.1;">{word}</span>
        </div>"""

    html = f"""<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:#2C3E50;">
<div style="
    display:grid;
    grid-template-columns:repeat(5,{cell}px);
    gap:{pad}px;
    padding:{pad}px;
    width:{canvas}px;
    background:#2C3E50;
">
{cells_html}
</div>
</body></html>"""
    return html, canvas


def render_html_to_bytesio(tablero, mode="public", key=None, font_size=None):
    """Renderiza el tablero con html2image y devuelve BytesIO."""
    from html2image import Html2Image
    html, canvas = render_board_html(tablero, mode=mode, key=key, font_size=font_size)
    with tempfile.TemporaryDirectory() as tmpdir:
        hti = Html2Image(
            output_path=tmpdir,
            size=(canvas, canvas),
            browser_executable=_CHROME,
            custom_flags=_CHROME_FLAGS,
        )
        paths = hti.screenshot(html_str=html, save_as="board.png")
        with open(paths[0], "rb") as f:
            buf = BytesIO(f.read())
    buf.seek(0)
    return buf
