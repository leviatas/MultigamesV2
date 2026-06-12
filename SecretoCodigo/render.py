"""Genera imágenes PNG del tablero de Secreto Código."""
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

CELL_W = 170
CELL_H = 90
PAD = 7
COLS = 5
ROWS = 5

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


def _draw_cell(draw, x, y, word, numero, bg_hex, fg_hex, mark=None, revealed=False):
    """
    mark    : None | "check" (agente encontrado) | "miss_corner" (neutral pisado)
    revealed: True dibuja tachado diagonal sobre la carta
    """
    bg = _hex_rgb(bg_hex)
    fg = _hex_rgb(fg_hex)
    draw.rectangle([x, y, x + CELL_W - 1, y + CELL_H - 1], fill=bg, outline=_hex_rgb("#FFFFFF"), width=1)

    # Número pequeño arriba-izquierda
    num_font = _load_font(11)
    draw.text((x + 5, y + 4), str(numero), font=num_font, fill=fg)

    if mark == "check":
        draw.text((x + CELL_W - 18, y + 3), "✓", font=num_font, fill=fg)
    elif mark == "miss_corner":
        # Triángulo naranja en esquina superior derecha para indicar "miss"
        pts = [(x + CELL_W - 18, y + 1), (x + CELL_W - 1, y + 1), (x + CELL_W - 1, y + 18)]
        draw.polygon(pts, fill=_hex_rgb("#E67E22"))

    # Palabra centrada
    font, label = _fit_text(draw, word.upper(), 24, CELL_W - 12)
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


def render_board(tablero, mode="public", key=None, partner_key=None):
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

        _draw_cell(draw, x, y, word, numero, bg, fg, mark=mark, revealed=revealed)

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
