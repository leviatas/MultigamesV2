# -*- coding: utf-8 -*-
"""Imagen de la pista de Gran Premio Arcano (HTML -> PNG con html2image).

Circuito "Wild Worlds": rectángulo horizontal con 29 casillas alrededor de un centro
negro con el título WILD WORLDS. Sentido horario:
  - fila superior (izq. -> der.): SALIDA y casillas 1 a 12
  - lateral derecho (arriba -> abajo): casillas 13 y 14
  - fila inferior (der. -> izq.): casillas 15 a 29
  - lateral izquierdo: la LLEGADA (casilla 30), después de la casilla 29.
Los corredores en la SALIDA están en la posición 0 (fuera del recorrido).

No usa emojis (la imagen Docker no tiene fuente de emoji a color): las casillas
especiales se dibujan con SVG y los corredores son fichas CSS con el color del
jugador y una sigla.
"""
import html as _html
import os
import tempfile
from io import BytesIO

from GranPremioArcano.Constants.Corredores import (
    CORREDORES, LARGO_PISTA, CASILLAS_SALVAJES, CANTIDAD_CARRERAS,
    PRIMERA_CURVA, SEGUNDA_CURVA,
)

COLUMNAS = 15
ANCHO_COL, HUECO, MARGEN = 86, 6, 20
ALTO_FILAS = [112, 150, 150, 112]
# Telegram recorta los costados de la vista previa de fotos muy apaisadas: se agrega
# margen arriba y abajo (con el mismo fondo) para no pasar de esta proporción.
PROPORCION_MAXIMA = 1.9

COLORES_JUGADOR = ["#ef4444", "#3b82f6", "#22c55e", "#f59e0b", "#a855f7", "#ec4899"]

# Colores de las casillas normales (solo decorativos).
COLORES_CASILLA = ["#7c3aed", "#0d9488", "#db2777", "#2563eb", "#ca8a04", "#059669", "#c2410c"]

# --- Ilustraciones SVG de las casillas especiales -------------------------
SVG_ESTRELLA = (
    '<svg viewBox="0 0 100 100" class="ilus"><polygon points="50,4 62,36 96,38 69,59 79,93 50,74 '
    '21,93 31,59 4,38 38,36" fill="#facc15" stroke="#fff7d1" stroke-width="4" stroke-linejoin="round"/>'
    '<text x="50" y="66" text-anchor="middle" font-size="34" font-weight="900" '
    'font-family="DejaVu Sans,Arial,sans-serif" fill="#7c2d12">1</text></svg>')

SVG_ZAPATILLA = (
    '<svg viewBox="0 0 100 100" class="ilus"><g transform="rotate(-18 50 55)">'
    '<path d="M14 62 L20 34 Q30 30 38 38 L48 46 Q62 50 80 52 Q92 55 92 66 L92 70 L14 70 Z" '
    'fill="#f8fafc" stroke="#111827" stroke-width="4" stroke-linejoin="round"/>'
    '<path d="M14 70 L92 70 L92 76 Q60 80 14 76 Z" fill="#ef4444" stroke="#111827" stroke-width="4"/>'
    '<path d="M34 42 L44 36 M40 48 L50 42 M46 52 L56 46" stroke="#ef4444" stroke-width="4" '
    'stroke-linecap="round"/></g>'
    '<path d="M70 18 l6 8 M82 14 l0 10 M90 22 l-7 6" stroke="#fde047" stroke-width="4" '
    'stroke-linecap="round"/></svg>')


def _svg_personaje(color):
    """Personaje tropezando (cae hacia adelante)."""
    return (
        '<svg viewBox="0 0 100 100" class="ilus"><g transform="rotate(38 50 60)">'
        '<circle cx="50" cy="22" r="11" fill="{c}" stroke="#111827" stroke-width="4"/>'
        '<path d="M50 34 L50 62 M50 42 L32 52 M50 42 L70 34 M50 62 L36 84 M50 62 L66 80" '
        'stroke="{c}" stroke-width="9" stroke-linecap="round"/>'
        '<path d="M50 34 L50 62 M50 42 L32 52 M50 42 L70 34 M50 62 L36 84 M50 62 L66 80" '
        'stroke="#111827" stroke-width="2" stroke-linecap="round" opacity=".35"/></g>'
        '<path d="M12 88 Q30 80 40 88" stroke="#fde047" stroke-width="4" fill="none" stroke-linecap="round"/>'
        '<path d="M14 20 l6 6 M10 34 l9 1" stroke="#fde047" stroke-width="4" stroke-linecap="round"/>'
        '</svg>').format(c=color)


SVG_TROPIEZO = {5: SVG_ZAPATILLA, 17: _svg_personaje("#fb923c"), 26: _svg_personaje("#22c55e")}

SVG_FLECHA = (
    '<svg viewBox="0 0 100 60" class="flecha-svg"><path d="M6 22 L58 22 L58 6 L94 30 L58 54 L58 38 L6 38 Z" '
    'fill="{c}" stroke="#fff" stroke-width="4" stroke-linejoin="round"/></svg>')

# Ilustración del centro del tablero (montañas, castillo, luna y estrellas).
SVG_CENTRO = """<svg viewBox="0 0 360 260" class="centro-svg" preserveAspectRatio="xMidYMax slice">
<defs><linearGradient id="cielo" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="#0b0b1e"/><stop offset="1" stop-color="#3b1d5e"/></linearGradient></defs>
<rect width="360" height="260" fill="url(#cielo)"/>
<circle cx="292" cy="58" r="30" fill="#fef3c7"/><circle cx="304" cy="50" r="27" fill="#16123a"/>
<g fill="#fde68a"><circle cx="40" cy="30" r="2"/><circle cx="110" cy="18" r="1.6"/><circle cx="170" cy="44" r="2"/>
<circle cx="230" cy="24" r="1.5"/><circle cx="70" cy="70" r="1.4"/><circle cx="330" cy="110" r="1.6"/>
<circle cx="20" cy="110" r="1.4"/><circle cx="200" cy="90" r="1.3"/></g>
<path d="M0 260 L0 170 L60 100 L110 160 L170 80 L240 170 L290 120 L360 180 L360 260 Z" fill="#2e1065"/>
<path d="M150 104 L170 80 L190 104 L178 98 L170 108 L162 98 Z" fill="#e9d5ff"/>
<path d="M0 260 L0 210 L50 180 L100 215 L160 175 L220 215 L280 190 L360 220 L360 260 Z" fill="#1e1b4b"/>
<g fill="#0a0a14"><rect x="150" y="150" width="60" height="70"/><rect x="138" y="128" width="20" height="92"/>
<rect x="202" y="128" width="20" height="92"/><rect x="170" y="112" width="20" height="40"/>
<path d="M134 128 L148 104 L162 128 Z"/><path d="M198 128 L212 104 L226 128 Z"/><path d="M166 112 L180 84 L194 112 Z"/></g>
<g fill="#facc15"><rect x="174" y="124" width="5" height="8"/><rect x="145" y="150" width="5" height="8"/>
<rect x="209" y="150" width="5" height="8"/><path d="M172 220 L172 196 Q180 184 188 196 L188 220 Z"/></g>
<path d="M0 260 L0 236 Q90 218 180 236 Q270 252 360 230 L360 260 Z" fill="#052e16"/>
</svg>"""
_CHROME_CANDIDATOS = [
    "/usr/bin/google-chrome-stable",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]
_CHROME_FLAGS = ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu",
                 "--hide-scrollbars", "--force-color-profile=srgb"]


def _esc(texto):
    return _html.escape(str(texto), quote=True)


def _chrome_path():
    for p in _CHROME_CANDIDATOS:
        if os.path.exists(p):
            return p
    return None


def posicion_celda(i):
    """(fila, columna) 0-based de la casilla i (1..29) en la grilla del tablero."""
    if 1 <= i <= 12:
        return 0, i + 2
    if i in (13, 14):
        return i - 12, COLUMNAS - 1
    return 3, COLUMNAS - 1 - (i - 15)


def _sentido(i):
    """Sentido de marcha en la casilla i: 1 = hacia la derecha, -1 = hacia la izquierda, 0 = vertical."""
    if i <= 12:
        return 1
    if i <= 14:
        return 0
    return -1


def _colores(game):
    return {p.uid: COLORES_JUGADOR[i % len(COLORES_JUGADOR)] for i, p in enumerate(game.player_sequence)}


def _ficha(c, color, actual, chica=False):
    clases = "ficha"
    if c.tropezado:
        clases += " tropezado"
    if actual:
        clases += " actual"
    if chica:
        clases += " chica"
    sigla = CORREDORES.get(c.rid, {}).get("sigla", "??")
    return '<div class="{}" style="background:{}">{}</div>'.format(clases, color, sigla)


def construir_html(game):
    """Devuelve (html, ancho, alto) de la pista en su estado actual."""
    import GranPremioArcano.Motor as M

    st = game.board.state
    salvaje = M.tipo_pista(st) == "salvaje"
    colores = _colores(game)
    actual = M.corredor_actual(st) if st.subfase in ("Accion", "Objetivo", "PostTirada") else None

    por_casilla = {}
    for c in st.corredores:
        if M.en_carrera(c):
            por_casilla.setdefault(c.pos, []).append(c)

    def bloque_fichas(fichas):
        if not fichas:
            return ""
        chica = len(fichas) > 4
        return '<div class="fichas">{}</div>'.format("".join(
            _ficha(c, colores.get(c.uid, "#888"), c is actual, chica) for c in fichas))

    celdas = []
    for i in range(1, LARGO_PISTA):
        fila, col = posicion_celda(i)
        clases = ["celda"]
        fichas = por_casilla.get(i, [])
        contenido = '<span class="num">{:02d}</span>'.format(i)
        especial = CASILLAS_SALVAJES.get(i) if salvaje else None
        if especial:
            tipo, valor = especial
            if tipo != "flecha":
                clases.append(tipo)
            if tipo == "estrella":
                contenido += SVG_ESTRELLA
            elif tipo == "tropiezo":
                contenido += SVG_TROPIEZO.get(i, SVG_ZAPATILLA)
                contenido += '<span class="etq">TRIP</span>'
            else:
                clases.append("avanza" if valor > 0 else "retrocede")
                gira = _sentido(i) * (1 if valor > 0 else -1) < 0
                contenido += '<div class="flecha{}">{}</div>'.format(
                    " gira" if gira else "", SVG_FLECHA.format(c="#22c55e" if valor > 0 else "#ef4444"))
                contenido += '<span class="valor">{}{}</span>'.format("+" if valor > 0 else "-", abs(valor))
        else:
            fondo = COLORES_CASILLA[i % len(COLORES_CASILLA)]
            clases.append("normal")
            clases_estilo = 'background:linear-gradient(160deg,{0},{0}cc);'.format(fondo)
        if i in (PRIMERA_CURVA, SEGUNDA_CURVA):
            contenido += '<span class="curva-etq">CURVA {}</span>'.format(1 if i == PRIMERA_CURVA else 2)
        if fichas:
            clases.append("ocupada")
        contenido += bloque_fichas(fichas)
        estilo = "grid-row:{};grid-column:{};".format(fila + 1, col + 1)
        if not especial:
            estilo += clases_estilo
        celdas.append('<div class="{}" style="{}">{}</div>'.format(" ".join(clases), estilo, contenido))

    # SALIDA (antes de la casilla 1) y LLEGADA (casilla 30, después de la 29).
    celdas.append('<div class="salida" style="grid-row:1;grid-column:1 / 4">'
                  '<span class="cartel">START</span>{}</div>'.format(bloque_fichas(por_casilla.get(0, []))))
    celdas.append('<div class="meta" style="grid-row:2 / 4;grid-column:1">'
                  '<span class="num">30</span><span class="cartel-v">LLEGADA</span></div>')

    # Tabla de corredores en el orden de turnos (el del turno actual va resaltado).
    orden = [st.corredores[i] for i in st.orden_turnos if i < len(st.corredores)]
    orden += [c for c in st.corredores if not any(c is o for o in orden)]
    filas_tabla = []
    for c in orden:
        jugador = game.playerlist.get(c.uid)
        if c.eliminado:
            estado = '<span class="tag elim">ELIMINADO</span>'
        elif c.lugar is not None:
            estado = '<span class="medalla m{}">{}º</span>'.format(c.lugar, c.lugar)
        else:
            estado = '<span class="casilla">{}</span>'.format(
                "salida" if c.pos == 0 else "casilla {}".format(c.pos))
            if c.tropezado:
                estado += ' <span class="tag">TROPEZÓ</span>'
            if st.jabali is not None and st.corredores[st.jabali] is c:
                estado += ' <span class="tag jabali">JABALÍ</span>'
            if c.bestia:
                estado += ' <span class="tag elim">BESTIA</span>'
        filas_tabla.append(
            '<div class="fila{}">{}<span class="nombre">{}</span><span class="dueno">{}</span>{}</div>'.format(
                " turno" if c is actual else "", _ficha(c, colores.get(c.uid, "#888"), False, True),
                _esc(CORREDORES[c.rid]["nombre"]), _esc(jugador.name if jugador else "?"), estado))

    puntos = "".join(
        '<div class="pto"><span class="punto" style="background:{}"></span>{}<b>{}</b></div>'.format(
            colores.get(p.uid, "#888"), _esc(p.name), p.puntos)
        for p in sorted(game.player_sequence, key=lambda p: -p.puntos))

    pista_txt = "PISTA SALVAJE" if salvaje else "PISTA MANSA"
    ancho = COLUMNAS * ANCHO_COL + (COLUMNAS - 1) * HUECO + 2 * MARGEN
    alto_tablero = sum(ALTO_FILAS) + (len(ALTO_FILAS) - 1) * HUECO + 2 * MARGEN
    alto = max(alto_tablero, -(-ancho * 10 // int(PROPORCION_MAXIMA * 10)))
    margen_sup = MARGEN + (alto - alto_tablero) // 2
    if salvaje:
        leyenda = ('<div class="caja leyenda"><b class="ley estrella">&#9733;</b> Estrella +1 pto '
                   '<b class="ley trip">TRIP</b> tropieza<br><b class="ley verde">&#8594;</b> avanza '
                   '<b class="ley roja">&#8592;</b> retrocede</div>')
    else:
        leyenda = '<div class="caja leyenda">Pista mansa: sin casillas especiales.<br>Sentido horario &#8635;</div>'

    html = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
* {{ box-sizing: border-box; }}
body {{ margin:0; padding:{mt}px {m}px {m}px; width:{w}px; height:{h}px; overflow:hidden;
  font-family:'DejaVu Sans','Liberation Sans',Arial,sans-serif;
  background: linear-gradient(135deg,#3f2a14 0%,#5b3a1a 50%,#3f2a14 100%); }}
.tablero {{ display:grid; grid-template-columns:repeat({cols},{cw}px); grid-template-rows:{filas};
  gap:{g}px; }}
.celda {{ position:relative; border-radius:8px; background:#374151;
  border:3px solid #f8fafc; box-shadow: inset 0 0 0 2px rgba(0,0,0,.25), 0 3px 8px rgba(0,0,0,.5); overflow:hidden; }}
.celda.estrella {{ background:radial-gradient(circle at 50% 45%,#6d28d9,#1e1b4b); }}
.celda.tropiezo {{ background:radial-gradient(circle at 50% 45%,#f97316,#7c2d12); }}
.celda.avanza {{ background:radial-gradient(circle at 50% 45%,#15803d,#052e16); }}
.celda.retrocede {{ background:radial-gradient(circle at 50% 45%,#b91c1c,#450a0a); }}
.num {{ position:absolute; top:3px; left:6px; font-size:14px; font-weight:800; color:#fff;
  text-shadow:0 1px 2px rgba(0,0,0,.8); z-index:2; }}
.etq {{ position:absolute; bottom:3px; right:5px; font-size:11px; font-weight:900; letter-spacing:1px; color:#fff;
  background:rgba(0,0,0,.45); padding:0 4px; border-radius:4px; z-index:2; }}
.ilus {{ position:absolute; left:8%; top:12%; width:84%; height:84%; }}
.flecha {{ position:absolute; left:6%; right:6%; top:26%; }}
.flecha.gira {{ transform:scaleX(-1); }}
.flecha-svg {{ width:100%; display:block; }}
.valor {{ position:absolute; bottom:4px; left:0; right:0; text-align:center; font-size:22px; font-weight:900;
  color:#fff; text-shadow:0 2px 3px rgba(0,0,0,.8); z-index:2; }}
.celda.ocupada .ilus, .celda.ocupada .flecha {{ opacity:.35; }}
.curva-etq {{ position:absolute; top:4px; right:4px; font-size:9px; font-weight:800; color:#fecaca;
  background:rgba(0,0,0,.55); padding:1px 3px; border-radius:4px; z-index:2; }}
.salida {{ position:relative; border-radius:8px; border:3px solid #fff; overflow:hidden;
  background:linear-gradient(90deg,#1f2937 0 82%, transparent 82%),
             repeating-conic-gradient(#111 0 25%, #fff 0 50%) 0 0/18px 18px; }}
.cartel {{ position:absolute; top:4px; left:8px; font-size:20px; font-weight:900; letter-spacing:3px; color:#fde047;
  text-shadow:0 2px 3px #000; z-index:2; }}
.meta .num {{ background:#111; padding:0 4px; border-radius:4px; }}
.meta {{ position:relative; border-radius:8px; border:3px solid #fff;
  background: repeating-conic-gradient(#111 0 25%, #fff 0 50%) 0 0/20px 20px; }}
.cartel-v {{ position:absolute; left:50%; top:50%; transform:translate(-50%,-50%) rotate(-90deg);
  font-size:20px; font-weight:900; letter-spacing:3px; color:#fde047; background:#111; white-space:nowrap; padding:4px 10px;
  border-radius:6px; }}
.fichas {{ position:absolute; left:3px; right:3px; top:22px; bottom:4px; display:flex; flex-wrap:wrap;
  align-content:center; justify-content:center; gap:3px; z-index:3; }}
.ficha {{ width:36px; height:36px; border-radius:50%; border:3px solid #fff; color:#fff; font-weight:900;
  font-size:13px; display:flex; align-items:center; justify-content:center; text-shadow:0 1px 2px rgba(0,0,0,.6);
  box-shadow:0 3px 6px rgba(0,0,0,.6); }}
.ficha.chica {{ width:24px; height:24px; font-size:9px; border-width:2px; }}
.ficha.actual {{ border-color:#fde047; box-shadow:0 0 0 3px rgba(253,224,71,.6), 0 0 14px #fde047; }}
.ficha.tropezado {{ transform:rotate(90deg); filter:grayscale(.55); border-style:dashed; }}
.centro {{ grid-row:2 / 4; grid-column:2 / 15; border-radius:16px; background:#050505; padding:10px;
  box-shadow: inset 0 0 0 3px #a16207, inset 0 0 30px rgba(0,0,0,.8); display:flex; gap:12px; color:#fff;
  overflow:hidden; }}
.arte {{ position:relative; width:330px; border-radius:12px; overflow:hidden; flex:none; }}
.centro-svg {{ position:absolute; inset:0; width:100%; height:100%; }}
.wild {{ position:absolute; left:0; right:0; top:14px; text-align:center; font-size:38px; font-weight:900;
  letter-spacing:3px; line-height:1; color:#fde047;
  text-shadow:0 0 10px #a855f7, 0 3px 0 #7c2d12, 0 4px 6px #000; }}
.sub {{ position:absolute; left:0; right:0; bottom:10px; text-align:center; font-size:13px; font-weight:800;
  letter-spacing:2px; color:#e9d5ff; text-shadow:0 2px 3px #000; }}
.info {{ flex:1; display:flex; flex-direction:column; min-width:0; }}
.titulo {{ display:flex; justify-content:space-between; align-items:baseline; margin-bottom:6px; }}
.titulo .gp {{ font-size:20px; font-weight:900; letter-spacing:2px; color:#fde68a; }}
.titulo .carrera {{ font-size:14px; font-weight:800; background:#3b0764; padding:3px 10px; border-radius:8px; }}
.cuerpo {{ display:flex; gap:12px; flex:1; min-height:0; }}
.tabla {{ flex:1.8; background:rgba(255,255,255,.07); border-radius:12px; padding:6px 8px; overflow:hidden; }}
.fila {{ display:flex; align-items:center; gap:8px; padding:2px 6px; border-radius:8px; font-size:14px; }}
.fila .ficha {{ width:24px; height:24px; font-size:9px; border-width:2px; }}
.fila.turno {{ background:rgba(253,224,71,.22); box-shadow: inset 0 0 0 2px #fde047; }}
.fila .nombre {{ font-weight:800; flex:1.4; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.fila .dueno {{ flex:1; color:#ddd6fe; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.fila .casilla {{ font-size:13px; color:#e5e7eb; white-space:nowrap; }}
.tag {{ font-size:10px; font-weight:800; background:#f59e0b; color:#111; padding:1px 4px; border-radius:5px; }}
.tag.elim {{ background:#b91c1c; color:#fff; }}
.tag.jabali {{ background:#a16207; color:#fff; }}
.medalla {{ font-weight:900; padding:1px 9px; border-radius:999px; color:#111; }}
.medalla.m1 {{ background:linear-gradient(#fde68a,#f59e0b); }}
.medalla.m2 {{ background:linear-gradient(#f3f4f6,#9ca3af); }}
.lado {{ flex:1; display:flex; flex-direction:column; gap:8px; }}
.caja {{ background:rgba(255,255,255,.07); border-radius:12px; padding:6px 10px; }}
.caja h3 {{ margin:0 0 4px 0; font-size:12px; letter-spacing:2px; color:#e9d5ff; }}
.pto {{ display:flex; align-items:center; gap:8px; font-size:14px; padding:1px 0; }}
.pto b {{ margin-left:auto; font-size:16px; }}
.punto {{ width:13px; height:13px; border-radius:50%; border:2px solid #fff; }}
.leyenda {{ font-size:12px; color:#e5e7eb; line-height:1.8; }}
.ley {{ display:inline-block; min-width:18px; text-align:center; border-radius:4px; padding:0 3px; color:#fff; }}
.ley.estrella {{ background:#6d28d9; color:#facc15; }}
.ley.trip {{ background:#ea580c; font-size:10px; }}
.ley.verde {{ background:#15803d; }}
.ley.roja {{ background:#b91c1c; }}
</style></head><body>
<div class="tablero">
{celdas}
<div class="centro">
  <div class="arte">{arte}<div class="wild">WILD<br>WORLDS</div><div class="sub">GRAN PREMIO ARCANO</div></div>
  <div class="info">
    <div class="titulo"><span class="gp">CARRERA {n}/{total}</span>
      <span class="carrera">{pista}</span></div>
    <div class="cuerpo">
      <div class="tabla">{tabla}</div>
      <div class="lado">
        <div class="caja"><h3>PUNTOS</h3>{puntos}</div>
        {leyenda}
      </div>
    </div>
  </div>
</div>
</div>
</body></html>""".format(
        m=MARGEN, mt=margen_sup, w=ancho, h=alto, cols=COLUMNAS, cw=ANCHO_COL, g=HUECO,
        filas=" ".join("{}px".format(a) for a in ALTO_FILAS), arte=SVG_CENTRO,
        celdas="\n".join(celdas), n=st.carrera, total=CANTIDAD_CARRERAS, pista=pista_txt,
        tabla="".join(filas_tabla), puntos=puntos, leyenda=leyenda,
    )
    return html, ancho, alto


def render_pista(game):
    """PNG de la pista en un BytesIO. Lanza excepción si no se puede renderizar."""
    if LARGO_PISTA != 30:
        raise ValueError("el dibujo del circuito asume 29 casillas (LARGO_PISTA = 30)")
    from html2image import Html2Image
    html, w, h = construir_html(game)
    with tempfile.TemporaryDirectory() as tmpdir:
        kwargs = dict(output_path=tmpdir, size=(w, h), custom_flags=_CHROME_FLAGS)
        chrome = _chrome_path()
        if chrome:
            kwargs["browser_executable"] = chrome
        hti = Html2Image(**kwargs)
        paths = hti.screenshot(html_str=html, save_as="gp_pista.png")
        with open(paths[0], "rb") as f:
            buf = BytesIO(f.read())
    buf.seek(0)
    return buf
