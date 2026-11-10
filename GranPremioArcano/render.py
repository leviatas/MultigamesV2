# -*- coding: utf-8 -*-
"""Imagen de la pista de Gran Premio Arcano (HTML -> PNG con html2image).

La pista es un circuito cerrado de 24 casillas alrededor de un infield de pasto:
9 casillas arriba, 3 a la derecha, 9 abajo y 3 a la izquierda (sentido horario).
La salida es la casilla 0 (arriba a la izquierda) y la meta es la línea a cuadros
entre la casilla 23 y la 0.

No usa emojis (la imagen Docker no tiene fuente de emoji a color): los corredores
son fichas CSS con el color del jugador y una sigla.
"""
import html as _html
import os
import tempfile
from io import BytesIO

from GranPremioArcano.Constants.Corredores import (
    CORREDORES, LARGO_PISTA, CASILLAS_SALVAJES, CANTIDAD_CARRERAS, NOMBRE_PISTA,
    PRIMERA_CURVA, SEGUNDA_CURVA,
)

COLUMNAS, FILAS = 9, 5
CELDA, HUECO, MARGEN = 116, 6, 22

COLORES_JUGADOR = ["#ef4444", "#3b82f6", "#22c55e", "#f59e0b", "#a855f7", "#ec4899"]


ESTILO_CASILLA = {
    "turbo": ("TURBO", "»", "+3"),
    "remolino": ("REMOLINO", "«", "-3"),
    "pozo": ("POZO", "", "tropieza"),
    "gema": ("GEMA", "◆", "+1 pto"),
}

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
    """(fila, columna) 0-based de la casilla i en el circuito, sentido horario."""
    if i <= 8:
        return 0, i
    if i <= 11:
        return i - 8, 8
    if i <= 20:
        return 4, 8 - (i - 12)
    return 4 - (i - 20), 0


def _flecha(i):
    """Sentido de marcha en la casilla i (horario)."""
    if i < 8:
        return "&#8594;"
    if i < 12:
        return "&#8595;"
    if i < 20:
        return "&#8592;"
    return "&#8593;"


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

    celdas = []
    for i in range(LARGO_PISTA):
        fila, col = posicion_celda(i)
        clases = ["celda"]
        etiqueta, simbolo, efecto = "", "", ""
        if salvaje and i in CASILLAS_SALVAJES:
            tipo = CASILLAS_SALVAJES[i]
            clases.append(tipo)
            etiqueta, simbolo, efecto = ESTILO_CASILLA[tipo]
        if i in (0, 8, 12, 20):
            clases.append("curva")
        if i == 0:
            clases.append("salida")
        contenido = '<span class="num">{}</span><span class="dir">{}</span>'.format(i, _flecha(i))
        if i == 0:
            contenido += '<span class="etq">SALIDA</span>'
        elif etiqueta:
            contenido += '<span class="etq">{}</span>'.format(etiqueta)
        if simbolo:
            contenido += '<span class="simbolo">{}</span>'.format(simbolo)
        if "pozo" in clases:
            contenido += '<span class="hoyo"></span>'
        if efecto:
            contenido += '<span class="efecto">{}</span>'.format(efecto)
        if i == PRIMERA_CURVA:
            contenido += '<span class="curva-etq">CURVA 1</span>'
        elif i == SEGUNDA_CURVA:
            contenido += '<span class="curva-etq">CURVA 2</span>'
        fichas = por_casilla.get(i, [])
        if fichas:
            chica = len(fichas) > 4
            contenido += '<div class="fichas">{}</div>'.format("".join(
                _ficha(c, colores.get(c.uid, "#888"), c is actual, chica) for c in fichas))
        celdas.append('<div class="{}" style="grid-row:{};grid-column:{}">{}</div>'.format(
            " ".join(clases), fila + 1, col + 1, contenido))

    # Tabla de corredores: primero los que llegaron, después por posición.
    orden = sorted(st.corredores, key=lambda c: (c.eliminado, c.lugar is None, c.lugar or 0, -c.pos))
    filas_tabla = []
    for c in orden:
        jugador = game.playerlist.get(c.uid)
        if c.eliminado:
            estado = '<span class="tag elim">ELIMINADO</span>'
        elif c.lugar is not None:
            estado = '<span class="medalla m{}">{}º</span>'.format(c.lugar, c.lugar)
        else:
            estado = '<span class="casilla">casilla {}</span>'.format(c.pos)
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
    ancho = COLUMNAS * CELDA + (COLUMNAS - 1) * HUECO + 2 * MARGEN
    alto = FILAS * CELDA + (FILAS - 1) * HUECO + 2 * MARGEN

    html = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
* {{ box-sizing: border-box; }}
body {{ margin:0; padding:{m}px; width:{w}px; height:{h}px; overflow:hidden;
  font-family:'DejaVu Sans','Liberation Sans',Arial,sans-serif;
  background: radial-gradient(circle at 50% 40%, #1e3a2a 0%, #0f1f17 70%); }}
.circuito {{ display:grid; grid-template-columns:repeat({cols},{c}px); grid-template-rows:repeat({filas},{c}px);
  gap:{g}px; }}
.celda {{ position:relative; border-radius:14px; background:linear-gradient(160deg,#4b5563,#374151);
  border:3px solid #e5e7eb; box-shadow: inset 0 0 0 2px rgba(0,0,0,.25), 0 4px 10px rgba(0,0,0,.45); overflow:hidden; }}
.celda.curva {{ border-color:#fca5a5; border-style:dashed; }}
.celda.salida {{ border-color:#fff; border-style:solid; }}
.celda.salida::after {{ content:''; position:absolute; left:0; right:0; bottom:0; height:16px;
  background: repeating-conic-gradient(#111 0 25%, #fff 0 50%) 0 0/16px 16px; }}
.celda.turbo {{ background:linear-gradient(160deg,#16a34a,#14532d); }}
.celda.remolino {{ background:linear-gradient(160deg,#0284c7,#0c4a6e); }}
.celda.pozo {{ background:linear-gradient(160deg,#92400e,#451a03); }}
.celda.gema {{ background:linear-gradient(160deg,#9333ea,#4c1d95); }}
.num {{ position:absolute; top:5px; left:8px; font-size:15px; font-weight:700; color:rgba(255,255,255,.75); }}
.etq {{ position:absolute; top:6px; right:8px; font-size:11px; font-weight:800; letter-spacing:1px; color:rgba(255,255,255,.9); }}
.simbolo {{ position:absolute; left:0; right:0; top:22px; text-align:center; font-size:46px; font-weight:900;
  color:rgba(255,255,255,.28); line-height:1; }}
.dir {{ position:absolute; bottom:4px; left:8px; font-size:18px; font-weight:900; color:rgba(255,255,255,.30); }}
.efecto {{ position:absolute; bottom:6px; right:8px; font-size:12px; font-weight:700; color:rgba(255,255,255,.85); }}
.hoyo {{ position:absolute; left:33px; top:36px; width:48px; height:34px; border-radius:50%;
  background:radial-gradient(#000 40%, #3f1d0b 100%); opacity:.7; }}
.red {{ position:absolute; inset:0; opacity:.55;
  background: repeating-radial-gradient(circle at 50% 50%, transparent 0 10px, #e5e7eb 10px 11px),
              repeating-conic-gradient(from 0deg, transparent 0 40deg, #e5e7eb 40deg 41deg); }}
.etq-red {{ position:absolute; bottom:5px; left:8px; font-size:10px; font-weight:800; color:#f3f4f6;
  background:rgba(0,0,0,.55); padding:1px 4px; border-radius:4px; }}
.fichas {{ position:absolute; left:6px; right:6px; top:26px; bottom:8px; display:flex; flex-wrap:wrap;
  align-content:center; justify-content:center; gap:5px; }}
.ficha {{ width:44px; height:44px; border-radius:50%; border:3px solid #fff; color:#fff; font-weight:900;
  font-size:16px; display:flex; align-items:center; justify-content:center; text-shadow:0 1px 2px rgba(0,0,0,.6);
  box-shadow:0 3px 6px rgba(0,0,0,.6); }}
.ficha.chica {{ width:32px; height:32px; font-size:12px; border-width:2px; }}
.ficha.actual {{ border-color:#fde047; box-shadow:0 0 0 4px rgba(253,224,71,.55), 0 0 18px #fde047; }}
.ficha.tropezado {{ transform:rotate(90deg); filter:grayscale(.55); border-style:dashed; }}
.infield {{ grid-row:2 / 5; grid-column:2 / 9; border-radius:22px; padding:14px 20px;
  background: repeating-linear-gradient(90deg,#2f7d32 0 56px,#2b7330 56px 112px);
  box-shadow: inset 0 0 0 4px rgba(255,255,255,.25), inset 0 0 40px rgba(0,0,0,.35);
  display:flex; flex-direction:column; color:#fff; }}
.titulo {{ display:flex; justify-content:space-between; align-items:baseline; margin-bottom:10px; }}
.titulo .gp {{ font-size:26px; font-weight:900; letter-spacing:2px; text-shadow:0 2px 4px rgba(0,0,0,.5); }}
.titulo .carrera {{ font-size:16px; font-weight:800; background:rgba(0,0,0,.35); padding:4px 10px; border-radius:8px; }}
.cuerpo {{ display:flex; gap:18px; flex:1; min-height:0; }}
.tabla {{ flex:1.7; background:rgba(0,0,0,.35); border-radius:14px; padding:8px 10px; }}
.fila {{ display:flex; align-items:center; gap:10px; padding:4px 6px; border-radius:8px; font-size:16px; }}
.fila.turno {{ background:rgba(253,224,71,.25); box-shadow: inset 0 0 0 2px #fde047; }}
.fila .nombre {{ font-weight:800; flex:1.4; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.fila .dueno {{ flex:1; color:#d1fae5; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.fila .casilla {{ font-size:14px; color:#e5e7eb; white-space:nowrap; }}
.tag {{ font-size:11px; font-weight:800; background:#f59e0b; color:#111; padding:2px 5px; border-radius:5px; }}
.tag.elim {{ background:#b91c1c; color:#fff; }}
.tag.jabali {{ background:#a16207; color:#fff; }}
.curva-etq {{ position:absolute; bottom:5px; left:30px; font-size:10px; font-weight:800; color:#fecaca;
  background:rgba(0,0,0,.55); padding:1px 4px; border-radius:4px; }}
.medalla {{ font-weight:900; padding:2px 10px; border-radius:999px; color:#111; }}
.medalla.m1 {{ background:linear-gradient(#fde68a,#f59e0b); }}
.medalla.m2 {{ background:linear-gradient(#f3f4f6,#9ca3af); }}
.lado {{ flex:1; display:flex; flex-direction:column; gap:10px; }}
.caja {{ background:rgba(0,0,0,.35); border-radius:14px; padding:8px 12px; }}
.caja h3 {{ margin:0 0 6px 0; font-size:13px; letter-spacing:2px; color:#bbf7d0; }}
.pto {{ display:flex; align-items:center; gap:8px; font-size:15px; padding:2px 0; }}
.pto b {{ margin-left:auto; font-size:17px; }}
.punto {{ width:14px; height:14px; border-radius:50%; border:2px solid #fff; }}
.leyenda {{ font-size:12px; color:#e5e7eb; line-height:1.6; }}
.leyenda span {{ display:inline-block; width:12px; height:12px; border-radius:3px; vertical-align:middle; margin-right:4px; }}
</style></head><body>
<div class="circuito">
{celdas}
<div class="infield">
  <div class="titulo"><span class="gp">GRAN PREMIO ARCANO</span>
    <span class="carrera">CARRERA {n}/{total} · {pista}</span></div>
  <div class="cuerpo">
    <div class="tabla">{tabla}</div>
    <div class="lado">
      <div class="caja"><h3>PUNTOS</h3>{puntos}</div>
      {leyenda}
    </div>
  </div>
</div>
</div>
</body></html>""".format(
        m=MARGEN, w=ancho, h=alto, cols=COLUMNAS, filas=FILAS, c=CELDA, g=HUECO,
        celdas="\n".join(celdas), n=st.carrera, total=CANTIDAD_CARRERAS, pista=pista_txt,
        tabla="".join(filas_tabla), puntos=puntos,
        leyenda=(
            '<div class="caja leyenda"><span style="background:#16a34a"></span>Turbo +3 '
            '<span style="background:#0284c7"></span>Remolino -3<br>'
            '<span style="background:#92400e"></span>Pozo: tropieza '
            '<span style="background:#9333ea"></span>Gema +1 pto</div>' if salvaje else
            '<div class="caja leyenda">Sentido horario &#8594; · la meta es la línea a cuadros de la SALIDA</div>'),
    )
    return html, ancho, alto


def render_pista(game):
    """PNG de la pista en un BytesIO. Lanza excepción si no se puede renderizar."""
    if LARGO_PISTA != 24:
        raise ValueError("el dibujo del circuito asume 24 casillas")
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
