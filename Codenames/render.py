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
    # Competitivo — sin revelar
    "unrevealed":    ("#E8E8E8", "#1A1A1A"),
    "rojo":          ("#C0392B", "#FFFFFF"),
    "azul":          ("#1A5276", "#FFFFFF"),
    "neutral":       ("#797D7F", "#FFFFFF"),
    "asesino":       ("#1C2833", "#FFFFFF"),
    # Dúo — sin revelar
    "agente":        ("#1E8449", "#FFFFFF"),       # mi agente (verde)
    "partner_agente": ("#1A6B8A", "#FFFFFF"),      # mi gris, pero agente del compañero (teal)
    # Reveladas — cualquier modo
    "revealed_rojo":     ("#F1948A", "#5D0000"),
    "revealed_azul":     ("#7FB3D3", "#0A2942"),
    "revealed_neutral":  ("#CACFD2", "#3D3D3D"),
    "revealed_asesino":  ("#4D5656", "#CCCCCC"),
    "revealed_agente":   ("#27AE60", "#FFFFFF"),   # agente encontrado → verde sólido
    "revealed_miss":     ("#95A5A6", "#FFFFFF"),   # neutral pisado → gris oscuro
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


def _draw_cell(draw, x, y, word, numero, bg_hex, fg_hex, mark=None):
    """
    mark: None | "check" (agente encontrado) | "miss" (neutral pisado) | "partner" (agente compañero)
    """
    bg = _hex_rgb(bg_hex)
    fg = _hex_rgb(fg_hex)
    draw.rectangle([x, y, x + CELL_W - 1, y + CELL_H - 1], fill=bg, outline=_hex_rgb("#FFFFFF"), width=1)

    # Número pequeño arriba-izquierda
    num_font = _load_font(11)
    draw.text((x + 5, y + 4), str(numero), font=num_font, fill=fg)

    # Marca arriba-derecha
    if mark == "check":
        draw.text((x + CELL_W - 18, y + 3), "✓", font=num_font, fill=fg)
    elif mark == "miss":
        draw.text((x + CELL_W - 14, y + 3), "✕", font=num_font, fill=fg)
    elif mark == "partner":
        # Pequeño triángulo de borde en la esquina superior derecha para indicar "del compañero"
        pts = [(x + CELL_W - 14, y + 1), (x + CELL_W - 1, y + 1), (x + CELL_W - 1, y + 14)]
        draw.polygon(pts, fill=_hex_rgb("#82E0AA"))

    # Palabra centrada
    font, label = _fit_text(draw, word.upper(), 17, CELL_W - 16)
    try:
        bbox = draw.textbbox((0, 0), label, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        tw, th = draw.textsize(label, font=font)
    draw.text((x + (CELL_W - tw) // 2, y + (CELL_H - th) // 2 + 4), label, font=font, fill=fg)


def render_board(tablero, mode="public", key=None, partner_key=None):
    """
    mode        : "public" | "spymaster" | "duo_key" | "duo_public"
    key         : {numero: tipo_str} — clave del jugador (duo_key)
    partner_key : {numero: tipo_str} — clave del compañero (duo_key), para marcar sus agentes
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

        word    = card["word"]
        numero  = card["numero"]
        revealed = card["revealed"]
        tipo    = card.get("tipo") or "neutral"
        mark    = None

        if mode in ("public", "duo_public"):
            if revealed:
                if tipo == "agente":
                    bg, fg = _PALETTE["revealed_agente"]
                    mark = "check"
                elif tipo == "asesino":
                    bg, fg = _PALETTE["revealed_asesino"]
                else:
                    bg, fg = _PALETTE["revealed_miss"]
                    mark = "miss"
            else:
                bg, fg = _PALETTE["unrevealed"]

        elif mode == "spymaster":
            if revealed:
                bg, fg = _PALETTE.get(f"revealed_{tipo}", _PALETTE["revealed_neutral"])
                mark = "check" if tipo == "agente" else ("miss" if tipo == "neutral" else None)
            else:
                bg, fg = _PALETTE.get(tipo, _PALETTE["unrevealed"])

        elif mode == "duo_key" and key:
            tipo_mine = key.get(numero, "neutral")
            tipo_partner = partner_key.get(numero, "neutral") if partner_key else "neutral"

            if revealed:
                # Verde si fue encontrado como agente, gris si fue un miss
                if tipo == "agente":
                    bg, fg = _PALETTE["revealed_agente"]
                    mark = "check"
                elif tipo == "asesino":
                    bg, fg = _PALETTE["revealed_asesino"]
                else:
                    bg, fg = _PALETTE["revealed_miss"]
                    mark = "miss"
            else:
                if tipo_mine == "agente":
                    bg, fg = _PALETTE["agente"]
                elif tipo_mine == "asesino":
                    bg, fg = _PALETTE["asesino"]
                else:
                    # neutral para mí — ¿es agente del compañero?
                    if tipo_partner == "agente":
                        bg, fg = _PALETTE["partner_agente"]
                        mark = "partner"
                    else:
                        bg, fg = _PALETTE["neutral"]
        else:
            bg, fg = _PALETTE["unrevealed"]

        _draw_cell(draw, x, y, word, numero, bg, fg, mark=mark)

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
