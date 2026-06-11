"""Genera imágenes PNG del tablero de Codenames."""
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

CELL_W = 150
CELL_H = 78
PAD = 7
COLS = 5
ROWS = 5

_FONT_PATH = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

# (background_hex, text_hex)
_PALETTE = {
    "unrevealed":    ("#E8E8E8", "#1A1A1A"),
    "rojo":          ("#C0392B", "#FFFFFF"),
    "azul":          ("#1A5276", "#FFFFFF"),
    "neutral":       ("#797D7F", "#FFFFFF"),
    "asesino":       ("#1C2833", "#FFFFFF"),
    "agente":        ("#1E8449", "#FFFFFF"),
    "revealed_rojo":    ("#F1948A", "#5D0000"),
    "revealed_azul":    ("#7FB3D3", "#0A2942"),
    "revealed_neutral": ("#CACFD2", "#3D3D3D"),
    "revealed_asesino": ("#4D5656", "#CCCCCC"),
    "revealed_agente":  ("#82E0AA", "#0A3D1F"),
}
_BG = "#2C3E50"


def _hex_rgb(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _load_font(size):
    try:
        return ImageFont.truetype(_FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()


def _fit_text(draw, text, font_size, max_w):
    """Retorna (font, text_to_draw) reduciendo fuente o truncando si no entra."""
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


def _draw_cell(draw, x, y, word, numero, bg_hex, fg_hex, revealed=False):
    bg = _hex_rgb(bg_hex)
    fg = _hex_rgb(fg_hex)
    draw.rectangle([x, y, x + CELL_W - 1, y + CELL_H - 1], fill=bg, outline=_hex_rgb("#FFFFFF"), width=1)

    # Número pequeño arriba-izquierda
    num_font = _load_font(11)
    draw.text((x + 5, y + 4), str(numero), font=num_font, fill=fg)

    # Palabra centrada
    font, label = _fit_text(draw, word.upper(), 17, CELL_W - 16)
    try:
        bbox = draw.textbbox((0, 0), label, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        tw, th = draw.textsize(label, font=font)
    draw.text((x + (CELL_W - tw) // 2, y + (CELL_H - th) // 2 + 4), label, font=font, fill=fg)

    # Tachado si ya fue revelada
    if revealed:
        mid_y = y + CELL_H // 2
        draw.line([(x + 6, mid_y), (x + CELL_W - 6, mid_y)], fill=fg, width=2)


def render_board(tablero, mode="public", key=None):
    """
    mode: "public" | "spymaster" | "duo_key"
    key: dict {numero: tipo_str} — requerido para duo_key
    Retorna BytesIO con imagen PNG.
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

        word = card["word"]
        numero = card["numero"]
        revealed = card["revealed"]
        tipo = card.get("tipo") or "neutral"

        if mode in ("public", "duo_public"):
            if revealed:
                key_tipo = tipo if tipo else "neutral"
                bg, fg = _PALETTE.get(f"revealed_{key_tipo}", _PALETTE["revealed_neutral"])
            else:
                bg, fg = _PALETTE["unrevealed"]
        elif mode == "spymaster":
            if revealed:
                bg, fg = _PALETTE.get(f"revealed_{tipo}", _PALETTE["revealed_neutral"])
            else:
                bg, fg = _PALETTE.get(tipo, _PALETTE["unrevealed"])
        elif mode == "duo_key" and key:
            tipo_key = key.get(numero, "neutral")
            if revealed:
                bg, fg = _PALETTE.get(f"revealed_{tipo_key}", _PALETTE["revealed_neutral"])
            else:
                bg, fg = _PALETTE.get(tipo_key, _PALETTE["unrevealed"])
        else:
            bg, fg = _PALETTE["unrevealed"]

        _draw_cell(draw, x, y, word, numero, bg, fg, revealed=revealed)

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
