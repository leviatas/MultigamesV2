# -*- coding: utf-8 -*-
"""Genera una imagen PNG del tablero de Battlestar Galactica con html2image.

Dibuja:
- Las 6 áreas del espacio dispuestas en anillo alrededor de Galactica, con las
  naves de cada área (Raiders, Heavy Raiders, Basestars, Vipers, civiles) y los
  Vipers tripulados (con el nombre del piloto).
- Las ubicaciones de cada nave (Galactica, Colonial One y localizaciones Cylon)
  con los personajes presentes en cada una, marcando averías y bloqueos.

No depende de fuentes de emoji a color: las naves y los roles se dibujan con
formas/etiquetas CSS para que el render sea consistente en headless Chrome.
"""
import os
import tempfile
from io import BytesIO

from BattlestarGalactica.Constants import Locations, Space

# Posibles ejecutables de Chrome/Chromium (el Dockerfile principal instala
# google-chrome-stable; Dockerfile2 usa chromium).
_CHROME_CANDIDATOS = [
    "/usr/bin/google-chrome-stable",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]
_CHROME_FLAGS = ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu",
                 "--hide-scrollbars", "--force-color-profile=srgb"]

# Distribución de las ubicaciones por nave para los paneles inferiores.
_GAL_1 = ["command", "ftl", "weapons", "hangar", "armory"]
_GAL_2 = ["admiral_quarters", "research", "communications", "sickbay", "brig"]
_COLONIAL = ["press_room", "president_office", "administration"]
_CYLON = ["caprica", "cylon_fleet", "human_fleet", "resurrection_ship"]

# Vista de COSTADO de la nave: la proa apunta a la IZQUIERDA y la popa a la
# derecha. Galactica ocupa la franja central (fila 2, columnas 2-3) y las 6 áreas
# del espacio la rodean. Estribor arriba, Babor (con los tubos) abajo.
# Posición en la rejilla 3x4 de cada área (fila, columna), 1-based.
_AREA_GRID = {
    0: (2, 1),  # Proa          (izquierda, frente a la nave)
    1: (1, 2),  # Estribor-proa (arriba-izquierda)
    2: (1, 3),  # Estribor-popa (arriba-derecha)
    3: (2, 4),  # Popa          (derecha, detrás de la nave)
    4: (3, 3),  # Babor-popa    (abajo-derecha, tubo de lanzamiento)
    5: (3, 2),  # Babor-proa    (abajo-izquierda, tubo de lanzamiento)
}


def _chrome_path():
    for p in _CHROME_CANDIDATOS:
        if os.path.exists(p):
            return p
    return None


def _esc(texto):
    return (str(texto).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _naves_html(area):
    """Fichas CSS de las naves Cylon/Vipers/civiles de un área del espacio."""
    piezas = []
    for hits in area["basestars"]:
        dmg = f"<span class='dmg'>{hits}/3</span>" if hits else ""
        piezas.append(f"<span class='ship bs'>BS{dmg}</span>")
    if area["raiders"]:
        piezas.append(f"<span class='ship rd'>R×{area['raiders']}</span>")
    if area.get("heavy_raiders"):
        piezas.append(f"<span class='ship hr'>H×{area['heavy_raiders']}</span>")
    if area["vipers"]:
        piezas.append(f"<span class='ship vp'>V×{area['vipers']}</span>")
    if area["civiles"]:
        piezas.append(f"<span class='ship cv'>C×{len(area['civiles'])}</span>")
    return "".join(piezas)


def _rol_jugador(st, player):
    badges = []
    if st.presidente_uid == player.uid:
        badges.append("<span class='badge pres'>Pres</span>")
    if st.almirante_uid == player.uid:
        badges.append("<span class='badge alm'>Alm</span>")
    if player.revealed:
        badges.append("<span class='badge cylon'>Cylon</span>")
    return "".join(badges)


def _chip_jugador(st, player, activo):
    cls = "pchip" + (" active" if activo else "") + (" rev" if player.revealed else "")
    return (f"<span class='{cls}'>{_esc(player.name)}"
            f"{_rol_jugador(st, player)}</span>")


def render_board_html(game):
    st = game.board.state

    # --- Ocupantes por ubicación y pilotos por área ---
    ocupantes = {}
    for p in game.playerlist.values():
        if getattr(p, "viper_area", None) is not None or not p.ubicacion:
            continue
        ocupantes.setdefault(p.ubicacion, []).append(p)
    pilotos_area = {}
    for p in game.playerlist.values():
        ar = getattr(p, "viper_area", None)
        if ar is not None:
            pilotos_area.setdefault(ar, []).append(p)

    activo_uid = st.active_player.uid if st.active_player else None
    bloqueadas = set(getattr(st, "ubicaciones_bloqueadas", []) or [])
    averiadas = set(st.galactica_damage or [])

    # --- Anillo del espacio ---
    celdas = []
    for meta in Space.AREAS:
        i = meta["id"]
        fila, col = _AREA_GRID[i]
        area = st.areas[i]
        tubo = "<span class='tube'>tubo</span>" if meta["launch"] else ""
        pilotos = "".join(
            f"<span class='pilot'>{_esc(p.name)}</span>" for p in pilotos_area.get(i, [])
        )
        naves = _naves_html(area)
        cuerpo = (naves + pilotos) or "<span class='vacio'>—</span>"
        celdas.append(
            f"<div class='area' style='grid-row:{fila};grid-column:{col};'>"
            f"<div class='area-h'>{_esc(meta['nombre'])} {tubo}</div>"
            f"<div class='area-b'>{cuerpo}</div></div>"
        )

    centro = (
        "<div class='galactica' style='grid-row:2;grid-column:2 / span 2;'>"
        "<div class='gtitle'>◄ GALÁCTICA</div>"
        f"<div class='gsub'>Daño {st.total_danos_galactica()}/{st.galactica_danos_max}</div>"
        f"<div class='gsub'>Abordaje {st.total_centuriones()} · "
        f"Reserva V {st.vipers_reserva} · Dañados {st.vipers_danados}</div>"
        "</div>"
    )
    espacio = f"<div class='ring'>{''.join(celdas)}{centro}</div>"

    # --- Paneles de ubicaciones ---
    def _panel(titulo, claves):
        filas = []
        for key in claves:
            info = Locations.UBICACIONES.get(key)
            if not info:
                continue
            nombre = info["nombre"].split(" (")[0]
            estado = ""
            cls = "loc"
            if key in averiadas:
                cls += " avg"
                estado = "<span class='tag avg'>AVERIADA</span>"
            if key in bloqueadas:
                cls += " blk"
                estado += "<span class='tag blk'>BLOQUEADA</span>"
            chips = "".join(
                _chip_jugador(st, p, p.uid == activo_uid) for p in ocupantes.get(key, [])
            ) or "<span class='vacio'>—</span>"
            filas.append(
                f"<div class='{cls}'><div class='loc-h'>{_esc(nombre)}{estado}</div>"
                f"<div class='loc-b'>{chips}</div></div>"
            )
        return f"<div class='panel'><div class='panel-h'>{titulo}</div>{''.join(filas)}</div>"

    paneles = (
        _panel("GALÁCTICA", _GAL_1)
        + _panel("GALÁCTICA", _GAL_2)
        + _panel("COLONIAL ONE", _COLONIAL)
        + _panel("LOCALIZACIONES CYLON", _CYLON)
    )

    # --- Cabecera de recursos (sin emoji: el Chrome headless no trae fuente de
    # emoji a color; usamos etiquetas de texto para garantizar el render). ---
    def _res(lbl, val, cls=""):
        return f"<span class='res {cls}'><i>{lbl}</i>{val}</span>"

    recursos = (
        _res("COMIDA", st.comida)
        + _res("FUEL", st.combustible)
        + _res("MORAL", st.moral)
        + _res("POBL", st.poblacion)
        + _res("DIST", f"{st.distancia}/{st.objetivo_distancia}")
        + _res("SALTO", f"{st.jump_prep}/{st.jump_prep_max}")
        + _res("OJIVAS", st.nukes)
    )

    # Altura del lienzo: cabecera + anillo (3 filas) + paneles (5 filas máx.) + márgenes.
    canvas_w = 1180
    canvas_h = 150 + 470 + 40 + 5 * 78 + 70

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ width: {canvas_w}px; background: #0b1020; color: #e7ecf5;
       font-family: 'DejaVu Sans', Arial, sans-serif; padding: 16px; }}
.head {{ display: flex; align-items: center; gap: 14px; margin-bottom: 12px; }}
.title {{ font-size: 26px; font-weight: 800; color: #cfe0ff; letter-spacing: 1px; }}
.res {{ background: #16203a; border: 1px solid #2a3a64; border-radius: 8px;
        padding: 5px 10px; font-size: 19px; font-weight: 800; display: inline-flex;
        flex-direction: column; align-items: center; line-height: 1.1; }}
.res i {{ font-style: normal; font-size: 10px; font-weight: 700; color: #7f93c4;
          letter-spacing: .5px; }}
.ring {{ display: grid; grid-template-columns: repeat(4, 1fr);
         grid-template-rows: 150px 150px 150px; gap: 10px; margin-bottom: 16px; }}
.area {{ background: #111a30; border: 1px solid #29365c; border-radius: 12px;
         padding: 8px; display: flex; flex-direction: column; }}
.area-h {{ font-size: 14px; font-weight: 700; color: #9fb6e8; margin-bottom: 6px;
           border-bottom: 1px solid #243154; padding-bottom: 4px; }}
.area-b {{ display: flex; flex-wrap: wrap; gap: 4px; align-content: flex-start; }}
.tube {{ font-size: 11px; background: #1d4ed8; color: #fff; border-radius: 6px;
         padding: 1px 5px; font-weight: 700; }}
.galactica {{ background: linear-gradient(90deg, #1a2b4d 0%, #3a5a92 55%, #22335a 100%);
              clip-path: polygon(0 50%, 13% 0, 100% 0, 100% 100%, 13% 100%);
              display: flex; flex-direction: column; align-items: center;
              justify-content: center; text-align: center; padding: 10px 10px 10px 60px; }}
.gtitle {{ font-size: 30px; font-weight: 900; color: #dfe9ff; letter-spacing: 2px; }}
.gsub {{ font-size: 14px; color: #b9c8ec; margin-top: 4px; }}
.ship {{ font-size: 13px; font-weight: 800; color: #fff; border-radius: 6px;
         padding: 2px 6px; display: inline-block; }}
.ship.bs {{ background: #7c3aed; }} .ship.rd {{ background: #dc2626; }}
.ship.hr {{ background: #991b1b; }} .ship.vp {{ background: #2563eb; }}
.ship.cv {{ background: #6b7280; }}
.dmg {{ font-size: 10px; background: rgba(0,0,0,.35); border-radius: 4px;
        padding: 0 3px; margin-left: 3px; }}
.pilot {{ font-size: 12px; font-weight: 800; color: #fff; background: #15803d;
          border: 1px solid #22c55e; border-radius: 12px; padding: 2px 7px; }}
.vacio {{ color: #586a92; font-size: 13px; }}
.panels {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }}
.panel-h {{ font-size: 16px; font-weight: 800; color: #cfe0ff; margin-bottom: 8px;
            text-align: center; }}
.loc {{ background: #111a30; border: 1px solid #29365c; border-radius: 10px;
        padding: 6px 8px; margin-bottom: 8px; min-height: 60px; }}
.loc.avg {{ background: #2a1320; border-color: #7f1d1d; }}
.loc.blk {{ background: #15151c; border-color: #4b5563; opacity: .85; }}
.loc-h {{ font-size: 13px; font-weight: 700; color: #aebfe6; margin-bottom: 4px; }}
.loc-b {{ display: flex; flex-wrap: wrap; gap: 4px; }}
.tag {{ font-size: 10px; font-weight: 800; border-radius: 5px; padding: 1px 4px;
        margin-left: 5px; color: #fff; }}
.tag.avg {{ background: #b91c1c; }} .tag.blk {{ background: #4b5563; }}
.pchip {{ font-size: 13px; font-weight: 700; background: #1f2b4d; color: #eaf0ff;
          border: 1px solid #3a4d80; border-radius: 12px; padding: 2px 8px; }}
.pchip.active {{ border-color: #facc15; box-shadow: 0 0 0 1px #facc15 inset; }}
.pchip.rev {{ background: #4c1d1d; border-color: #b91c1c; }}
.badge {{ font-size: 10px; font-weight: 800; border-radius: 5px; padding: 0 4px;
          margin-left: 4px; color: #1b2030; }}
.badge.pres {{ background: #fbbf24; }} .badge.alm {{ background: #67e8f9; }}
.badge.cylon {{ background: #ef4444; color: #fff; }}
</style></head><body>
<div class="head"><span class="title">BATTLESTAR GALACTICA</span>{recursos}</div>
{espacio}
<div class="panels">{paneles}</div>
</body></html>"""
    return html, canvas_w, canvas_h


def render_board_image(game):
    """Renderiza el tablero a PNG y devuelve un BytesIO (o None si falla)."""
    from html2image import Html2Image
    html, w, h = render_board_html(game)
    with tempfile.TemporaryDirectory() as tmpdir:
        kwargs = dict(output_path=tmpdir, size=(w, h), custom_flags=_CHROME_FLAGS)
        chrome = _chrome_path()
        if chrome:
            kwargs["browser_executable"] = chrome
        hti = Html2Image(**kwargs)
        paths = hti.screenshot(html_str=html, save_as="bsg_board.png")
        with open(paths[0], "rb") as f:
            buf = BytesIO(f.read())
    buf.seek(0)
    return buf
