# -*- coding: utf-8 -*-
"""Imágenes de la transmisión en vivo de Carrera de Bichos, dibujadas con Pillow.

Se usa Pillow (y no HTML + Chrome como en Gran Premio Arcano) porque durante la
carrera se genera un cuadro cada ~3 segundos: dibujar tarda unas decenas de
milisegundos y no lanza procesos.

No usa emojis (la imagen Docker no tiene fuente de emoji a color): los bichos,
las tribunas y las cartas están dibujados con figuras. Se dibuja al doble de
tamaño y se achica al final para que los bordes queden suaves.
"""
import random
from functools import lru_cache
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from CarreraBichos.Constants.Cartas import (
    BICHOS, ORDEN_BICHOS, LARGO_PISTA, CANTIDAD_CARRERAS, MULTIPLICADOR_FINAL,
)

W, H = 1280, 720
S = 2  # supersampling

HEADER_H = 56
TRIBUNA_Y0, TRIBUNA_Y1 = 56, 146
PISTA_Y0 = 154
CARRIL_H = 104
PISTA_Y1 = PISTA_Y0 + CARRIL_H * len(ORDEN_BICHOS)
ETIQ_X1 = 214
LARGADA_X = 262
META_X = 1060
CASILLA = (META_X - LARGADA_X) / LARGO_PISTA
COLUMNA_X0 = 1086
PIE_Y0 = PISTA_Y1 + 8
TAM_BICHO = 86
# A cuántas casillas de la meta se considera "recta final" (igual que el motor).
RECTA_FINAL = 6

COLOR = {
    "gallina": {"acento": (249, 115, 22), "claro": (255, 237, 213)},
    "chancho": {"acento": (236, 72, 153), "claro": (252, 231, 243)},
    "sapo":    {"acento": (34, 197, 94), "claro": (220, 252, 231)},
    "pato":    {"acento": (14, 165, 233), "claro": (224, 242, 254)},
}
ORO, PLATA, BRONCE = (250, 204, 21), (209, 213, 219), (217, 119, 6)
MEDALLA_COLOR = {1: ORO, 2: PLATA, 3: BRONCE, 4: (120, 113, 108)}
BLANCO, NEGRO = (255, 255, 255), (17, 17, 17)

_FUENTES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "DejaVuSans-Bold.ttf",
    "arialbd.ttf",
]


@lru_cache(maxsize=64)
def fuente(px):
    for ruta in _FUENTES:
        try:
            return ImageFont.truetype(ruta, int(px * S))
        except OSError:
            continue
    return ImageFont.load_default(size=int(px * S))


def _p(v):
    return int(round(v * S))


def _caja(x0, y0, x1, y1):
    return [_p(x0), _p(y0), _p(x1), _p(y1)]


def _texto(d, xy, texto, px, fill=BLANCO, anchor="la", stroke=0, stroke_fill=NEGRO):
    d.text((_p(xy[0]), _p(xy[1])), texto, font=fuente(px), fill=fill, anchor=anchor,
           stroke_width=_p(stroke), stroke_fill=stroke_fill)


def _ajustar(d, texto, max_ancho, px, minimo=12):
    while px > minimo and d.textlength(texto, font=fuente(px)) > _p(max_ancho):
        px -= 2
    return px


# ---------------------------------------------------------------------------
# Bichos (mirando a la derecha, en una caja de 100x100)
# ---------------------------------------------------------------------------

class _Sprite(object):
    def __init__(self, d, cx, cy, tam):
        self.d = d
        self.x0, self.y0, self.u = cx - tam / 2, cy - tam / 2, tam / 100.0

    def pt(self, x, y):
        return (_p(self.x0 + x * self.u), _p(self.y0 + y * self.u))

    def caja(self, x0, y0, x1, y1):
        a, b = self.pt(x0, y0), self.pt(x1, y1)
        return [a[0], a[1], b[0], b[1]]

    def w(self, v):
        return max(1, _p(v * self.u))

    def elipse(self, x0, y0, x1, y1, fill, outline=None, ancho=2):
        self.d.ellipse(self.caja(x0, y0, x1, y1), fill=fill, outline=outline, width=self.w(ancho))

    def poligono(self, puntos, fill, outline=None, ancho=2):
        self.d.polygon([self.pt(x, y) for x, y in puntos], fill=fill, outline=outline, width=self.w(ancho))

    def linea(self, puntos, fill, ancho):
        self.d.line([self.pt(x, y) for x, y in puntos], fill=fill, width=self.w(ancho), joint="curve")

    def ojo(self, x, y, r=4):
        self.elipse(x - r, y - r, x + r, y + r, NEGRO, ancho=0)
        self.elipse(x - r * 0.2, y - r * 0.7, x + r * 0.5, y, BLANCO, ancho=0)


def _gallina(s, mareado):
    naranja, borde = (245, 158, 11), (156, 163, 175)
    s.linea([(42, 72), (38, 93)], naranja, 4)
    s.linea([(58, 72), (62, 93)], naranja, 4)
    s.linea([(30, 93), (46, 93)], naranja, 4)
    s.linea([(54, 93), (70, 93)], naranja, 4)
    s.poligono([(16, 46), (2, 20), (20, 36), (12, 10), (30, 34)], BLANCO, borde)
    s.elipse(12, 30, 76, 80, BLANCO, borde, 2.5)
    s.elipse(28, 44, 62, 68, (229, 231, 235), borde)
    s.elipse(56, 12, 88, 44, BLANCO, borde, 2.5)
    rojo = (220, 38, 38)
    s.elipse(60, 4, 70, 16, rojo, ancho=0)
    s.elipse(67, 0, 78, 14, rojo, ancho=0)
    s.elipse(75, 4, 85, 16, rojo, ancho=0)
    s.poligono([(86, 23), (99, 28), (86, 33)], naranja, (180, 83, 9), 1.5)
    s.elipse(80, 32, 88, 46, rojo, ancho=0)
    _ojos(s, 74, 23, mareado)


def _chancho(s, mareado):
    rosa, oscuro, borde = (249, 168, 212), (244, 114, 182), (190, 24, 93)
    for x0 in (24, 40, 58, 72):
        s.d.rounded_rectangle(s.caja(x0, 64, x0 + 9, 92), radius=s.w(3), fill=oscuro, outline=borde, width=s.w(1.5))
    s.d.arc(s.caja(0, 28, 16, 44), 90, 400, fill=borde, width=s.w(3))
    s.elipse(8, 24, 86, 76, rosa, borde, 2.5)
    s.elipse(58, 16, 94, 58, rosa, borde, 2.5)
    s.poligono([(64, 20), (70, 4), (80, 20)], oscuro, borde)
    s.elipse(84, 30, 99, 50, oscuro, borde, 2)
    s.elipse(88, 36, 91, 42, borde, ancho=0)
    s.elipse(93, 36, 96, 42, borde, ancho=0)
    _ojos(s, 75, 29, mareado)


def _sapo(s, mareado):
    verde, oscuro, borde = (74, 222, 128), (22, 163, 74), (20, 83, 45)
    s.elipse(4, 54, 46, 86, oscuro, borde, 2)
    s.linea([(10, 86), (0, 94), (22, 94)], oscuro, 4)
    s.elipse(12, 32, 82, 84, verde, borde, 2.5)
    s.elipse(40, 58, 80, 84, (217, 249, 157), ancho=0)
    s.linea([(68, 72), (78, 92), (90, 92)], oscuro, 5)
    for x, y in ((24, 46), (34, 40), (28, 58)):
        s.elipse(x - 3, y - 3, x + 3, y + 3, oscuro, ancho=0)
    s.elipse(48, 14, 70, 38, verde, borde, 2.5)
    s.elipse(66, 12, 88, 36, verde, borde, 2.5)
    s.elipse(52, 18, 66, 32, BLANCO, ancho=0)
    s.elipse(70, 16, 84, 30, BLANCO, ancho=0)
    s.d.arc(s.caja(58, 36, 94, 58), 10, 120, fill=borde, width=s.w(2.5))
    if mareado:
        _espiral(s, 59, 25)
        _espiral(s, 77, 23)
    else:
        s.ojo(61, 25, 3.5)
        s.ojo(79, 23, 3.5)


def _pato(s, mareado):
    amarillo, borde, naranja = (250, 204, 21), (161, 98, 7), (249, 115, 22)
    s.linea([(44, 76), (42, 92)], naranja, 4)
    s.linea([(58, 76), (60, 92)], naranja, 4)
    s.poligono([(32, 94), (42, 88), (50, 94)], naranja, ancho=0)
    s.poligono([(52, 94), (60, 88), (70, 94)], naranja, ancho=0)
    s.poligono([(12, 56), (0, 40), (22, 50)], amarillo, borde)
    s.elipse(6, 40, 80, 84, amarillo, borde, 2.5)
    s.elipse(22, 52, 58, 74, (234, 179, 8), borde, 1.5)
    s.elipse(52, 10, 86, 46, amarillo, borde, 2.5)
    s.d.rounded_rectangle(s.caja(78, 26, 100, 38), radius=s.w(5), fill=naranja, outline=(194, 65, 12),
                          width=s.w(1.5))
    _ojos(s, 70, 22, mareado)


def _espiral(s, x, y):
    for r in (6, 3.5):
        s.d.arc(s.caja(x - r, y - r, x + r, y + r), 0, 300, fill=(124, 58, 237), width=s.w(1.6))


def _ojos(s, x, y, mareado):
    if mareado:
        _espiral(s, x, y)
    else:
        s.ojo(x, y)


DIBUJO = {"gallina": _gallina, "chancho": _chancho, "sapo": _sapo, "pato": _pato}


def dibujar_bicho(d, bid, cx, cy, tam, mareado=False):
    DIBUJO[bid](_Sprite(d, cx, cy, tam), mareado)


# ---------------------------------------------------------------------------
# Fondo fijo (tribuna, pista, meta): se dibuja una sola vez
# ---------------------------------------------------------------------------

def _gradiente(d, x0, y0, x1, y1, c0, c1):
    alto = _p(y1) - _p(y0)
    for i in range(alto):
        t = i / max(1, alto - 1)
        c = tuple(int(c0[k] + (c1[k] - c0[k]) * t) for k in range(3))
        d.line([(_p(x0), _p(y0) + i), (_p(x1), _p(y0) + i)], fill=c)


def carril_y(i):
    return PISTA_Y0 + i * CARRIL_H


def casilla_x(pos):
    return LARGADA_X + pos * CASILLA


@lru_cache(maxsize=1)
def _fondo():
    img = Image.new("RGB", (_p(W), _p(H)), (15, 23, 42))
    d = ImageDraw.Draw(img, "RGBA")
    _gradiente(d, 0, 0, W, PIE_Y0, (30, 41, 59), (15, 23, 42))

    # Tribuna con público
    _gradiente(d, 0, TRIBUNA_Y0, W, TRIBUNA_Y1, (51, 65, 85), (30, 41, 59))
    rnd = random.Random(7)
    remeras = [(239, 68, 68), (59, 130, 246), (34, 197, 94), (234, 179, 8), (168, 85, 247),
               (236, 72, 153), (20, 184, 166), (249, 115, 22), (226, 232, 240)]
    pieles = [(253, 224, 196), (234, 192, 134), (198, 134, 66), (141, 85, 36), (255, 205, 178)]
    for fila, y in enumerate((TRIBUNA_Y0 + 24, TRIBUNA_Y0 + 50, TRIBUNA_Y0 + 76)):
        d.rectangle(_caja(0, y + 6, W, y + 9), fill=(71, 85, 105))
        x = -6 + fila * 9
        while x < W + 10:
            r = rnd.uniform(7, 9.5)
            dy = rnd.uniform(-3, 2)
            d.ellipse(_caja(x - r * 1.3, y + dy + r * 0.6, x + r * 1.3, y + dy + r * 2.6), fill=rnd.choice(remeras))
            d.ellipse(_caja(x - r, y + dy - r, x + r, y + dy + r), fill=rnd.choice(pieles))
            if rnd.random() < 0.18:  # brazos arriba
                d.line([(_p(x + r), _p(y + dy + r)), (_p(x + r * 2), _p(y + dy - r * 1.6))],
                       fill=rnd.choice(pieles), width=_p(3))
            x += r * 2.2 + rnd.uniform(1, 4)
    # Banderines
    cols = [(239, 68, 68), (250, 204, 21), (59, 130, 246), (34, 197, 94)]
    for i, x in enumerate(range(0, W, 32)):
        d.polygon([(_p(x), _p(TRIBUNA_Y1)), (_p(x + 32), _p(TRIBUNA_Y1)), (_p(x + 16), _p(TRIBUNA_Y1 + 12))],
                  fill=cols[i % 4])
    d.rectangle(_caja(0, TRIBUNA_Y1 - 2, W, TRIBUNA_Y1 + 1), fill=BLANCO)

    # Carriles
    for i, bid in enumerate(ORDEN_BICHOS):
        y0, y1 = carril_y(i), carril_y(i) + CARRIL_H
        base = (161, 98, 7) if i % 2 == 0 else (146, 88, 10)
        _gradiente(d, ETIQ_X1, y0, COLUMNA_X0, y1, tuple(min(255, c + 18) for c in base), base)
        for _ in range(140):  # textura de tierra
            x, y = rnd.uniform(ETIQ_X1, COLUMNA_X0), rnd.uniform(y0, y1)
            r = rnd.uniform(0.8, 2.2)
            d.ellipse(_caja(x - r, y - r, x + r, y + r), fill=(120, 72, 6, 120))
        d.line([(_p(ETIQ_X1), _p(y1)), (_p(COLUMNA_X0), _p(y1))], fill=(255, 255, 255, 140), width=_p(2))
        # Etiqueta del carril
        acento = COLOR[bid]["acento"]
        d.rectangle(_caja(0, y0, ETIQ_X1, y1), fill=(15, 23, 42))
        d.rectangle(_caja(0, y0, 7, y1), fill=acento)
        d.line([(0, _p(y1)), (_p(ETIQ_X1), _p(y1))], fill=(51, 65, 85), width=_p(2))
        dibujar_bicho(d, bid, 40, y0 + 30, 50)
        nombre = BICHOS[bid]["nombre"].upper()
        _texto(d, (70, y0 + 30), nombre, _ajustar(d, nombre, ETIQ_X1 - 76, 17), fill=acento, anchor="lm")
        # Columna de estado
        d.rectangle(_caja(COLUMNA_X0, y0, W, y1), fill=(15, 23, 42, 235))
        d.line([(_p(COLUMNA_X0), _p(y1)), (_p(W), _p(y1))], fill=(51, 65, 85), width=_p(2))

    # Marcas de distancia
    for k in range(1, LARGO_PISTA):
        x = casilla_x(k)
        for i in range(len(ORDEN_BICHOS)):
            y0 = carril_y(i)
            d.line([(_p(x), _p(y0 + CARRIL_H - 12)), (_p(x), _p(y0 + CARRIL_H - 2))],
                   fill=(255, 255, 255, 90), width=_p(2))
    # Largada y meta
    d.rectangle(_caja(LARGADA_X - 3, PISTA_Y0, LARGADA_X + 3, PISTA_Y1), fill=(255, 255, 255, 220))
    lado = 13
    for fila, y in enumerate(range(PISTA_Y0, PISTA_Y1, lado)):
        for col in range(2):
            negro = (fila + col) % 2 == 0
            d.rectangle(_caja(META_X + col * lado, y, META_X + (col + 1) * lado, min(PISTA_Y1, y + lado)),
                        fill=NEGRO if negro else BLANCO)
    return img


# ---------------------------------------------------------------------------
# Análisis del cuadro: qué se movió, a quién le pegaron, titular
# ---------------------------------------------------------------------------

def instantanea(st):
    """Estado de los bichos antes de revelar cartas, para comparar después."""
    foto = {b.bid: (b.pos, b.lugar, b.mareado, b.dormido) for b in st.bichos}
    foto["_desmayos"] = (st.stats or {}).get("desmayos", 0)
    return foto


def _lider(posiciones):
    if not posiciones:
        return None
    maximo = max(posiciones.values())
    punteros = [b for b, p in posiciones.items() if p == maximo]
    return punteros[0] if len(punteros) == 1 and maximo > 0 else None


def _lider_actual(st):
    if st.podio:
        return None
    return _lider({b.bid: b.pos for b in st.bichos if b.lugar is None})


def _lider_previo(previas):
    return _lider({bid: v[0] for bid, v in previas.items() if not bid.startswith("_") and v[1] is None})


def _golpes(st, cartas, previas):
    """bid -> texto del golpe (BOOM!, PAF!, ...) para dibujar un estallido."""
    golpes = {}
    if not previas:
        return golpes
    for carta in cartas or []:
        tipo, bid, _ = carta.split(":")
        if tipo == "PETARDO":
            golpes[bid] = "BOOM!"
        elif tipo == "CHOQUE":
            for b in st.bichos:
                antes = previas.get(b.bid)
                if b.bid != bid and antes and b.mareado > 0 and (antes[2] == 0 or b.pos < antes[0]):
                    golpes[b.bid] = "PAF!"
        elif tipo == "MAREO" and bid in previas:
            golpes.setdefault(bid, "PLOP!")
    return golpes


def titular(st, cartas, previas):
    """(texto, color) del gran titular del cuadro, o None."""
    if not previas:
        return None
    nombre = lambda bid: BICHOS[bid]["nombre"].upper()
    nuevos = {b.lugar: b.bid for b in st.bichos if b.lugar is not None and previas.get(b.bid, (0, None))[1] is None}
    if 1 in nuevos:
        return "¡¡{} GANA!!".format(nombre(nuevos[1])), ORO
    if 2 in nuevos:
        return "¡{} ENTRA SEGUNDO!".format(nombre(nuevos[2])), PLATA
    tipos = [c.split(":")[0] for c in cartas or []]
    if (st.stats or {}).get("desmayos", 0) > previas.get("_desmayos", 0):
        return "¡SE DESMAYÓ!", (196, 181, 253)
    especiales = [
        ("PETARDO", "¡BOOM!", (251, 146, 60)), ("CAMBIO", "¡CAMBIAZO!", (192, 132, 252)),
        ("CHOQUE", "¡EMBESTIDA!", (248, 113, 113)), ("ESTAMPIDA", "¡ESTAMPIDA!", (253, 186, 116)),
        ("REVANCHA", "¡REVANCHA!", (252, 165, 165)),
    ]
    for tipo, texto, color in especiales:
        if tipo in tipos:
            return texto, color
    if "VIENTO" in tipos:
        viento = [c for c in cartas if c.startswith("VIENTO")][-1]
        return ("¡VIENTO A FAVOR!", (125, 211, 252)) if int(viento.split(":")[2]) > 0 else \
            ("¡VIENTO EN CONTRA!", (148, 163, 184))
    antes, ahora = _lider_previo(previas), _lider_actual(st)
    if ahora and ahora != antes:
        return "¡{} TOMA LA PUNTA!".format(nombre(ahora)), COLOR[ahora]["acento"]
    vivos = [b for b in st.bichos if b.lugar is None]
    if vivos:
        cerca = max(vivos, key=lambda b: b.pos)
        falta = LARGO_PISTA - cerca.pos
        if falta <= 3 and cerca.pos > previas.get(cerca.bid, (0,))[0]:
            return "¡{} A {} DE LA META!".format(nombre(cerca.bid), falta), (254, 202, 202)
    for carta in cartas or []:
        tipo, bid, v = carta.split(":")
        if tipo == "MOV" and int(v) >= 4:
            return "¡QUÉ PIQUE!", (134, 239, 172)
    for tipo, texto, color in (("MAREO", "¡MAREADO!", (196, 181, 253)), ("SIESTA", "¡A DORMIR LA SIESTA!", (147, 197, 253)),
                               ("CAFE", "¡CAFECITO!", (253, 230, 138))):
        if tipo in tipos:
            return texto, color
    return None


# ---------------------------------------------------------------------------
# Partes dinámicas
# ---------------------------------------------------------------------------

def _encabezado(d, st, en_vivo, recta_final):
    _gradiente(d, 0, 0, W, HEADER_H, (2, 6, 23), (15, 23, 42))
    d.line([(0, _p(HEADER_H)), (_p(W), _p(HEADER_H))], fill=(250, 204, 21), width=_p(3))
    _texto(d, (22, HEADER_H / 2), "CARRERA DE BICHOS", 26, fill=(250, 204, 21), anchor="lm", stroke=1)
    if st.carrera >= CANTIDAD_CARRERAS:
        centro, color = "CARRERA FINAL · TODO PAGA x{}".format(MULTIPLICADOR_FINAL), (251, 191, 36)
    else:
        centro, color = "CARRERA {}/{}".format(st.carrera, CANTIDAD_CARRERAS), BLANCO
    _texto(d, (W / 2 + 40, HEADER_H / 2), centro, 22, fill=color, anchor="mm")
    x = W - 22
    if en_vivo:
        ancho = 128
        d.rounded_rectangle(_caja(x - ancho, 12, x, HEADER_H - 12), radius=_p(16), fill=(220, 38, 38))
        d.ellipse(_caja(x - ancho + 12, HEADER_H / 2 - 6, x - ancho + 24, HEADER_H / 2 + 6), fill=BLANCO)
        _texto(d, (x - ancho + 34, HEADER_H / 2), "EN VIVO", 18, anchor="lm")
        x -= ancho + 12
    if recta_final:
        ancho = 150
        d.rounded_rectangle(_caja(x - ancho, 12, x, HEADER_H - 12), radius=_p(16), fill=(250, 204, 21))
        _texto(d, (x - ancho / 2, HEADER_H / 2), "RECTA FINAL", 18, fill=NEGRO, anchor="mm")


def _apostadores(game):
    """bid -> [(nombre, 'G'|'P', fuerte)]"""
    res = {b: [] for b in ORDEN_BICHOS}
    for p in game.player_sequence:
        for a in p.apuestas:
            t = a["t"]
            if t[:2] in ("G_", "P_") and t[2:] in res:
                res[t[2:]].append((p.name, t[0], a["fuerte"]))
    return res


def _etiquetas_apuestas(d, game):
    apuestas = _apostadores(game)
    for i, bid in enumerate(ORDEN_BICHOS):
        x, y = 14, carril_y(i) + 62
        for nombre, tipo, fuerte in apuestas[bid]:
            nombre = nombre if len(nombre) <= 9 else nombre[:8] + "."
            ancho = 24 + d.textlength(nombre, font=fuente(13)) / S + 10
            if x + ancho > ETIQ_X1 - 4:
                x, y = 14, y + 20
                if y > carril_y(i) + CARRIL_H - 12:
                    break
            d.rounded_rectangle(_caja(x, y - 8, x + ancho, y + 9), radius=_p(8), fill=(30, 41, 59),
                                outline=(239, 68, 68) if fuerte else (71, 85, 105), width=_p(2 if fuerte else 1))
            d.ellipse(_caja(x + 3, y - 6, x + 17, y + 7), fill=ORO if tipo == "G" else PLATA)
            _texto(d, (x + 10, y + 0.5), "1" if tipo == "G" else "2", 10, fill=NEGRO, anchor="mm")
            _texto(d, (x + 21, y + 0.5), nombre, 13, fill=BLANCO, anchor="lm")
            x += ancho + 5


def _estrella(cx, cy, r_ext, r_int, puntas, giro=0.0):
    import math
    pts = []
    for k in range(puntas * 2):
        r = r_ext if k % 2 == 0 else r_int
        a = giro + k * math.pi / puntas
        pts.append((_p(cx + r * math.cos(a)), _p(cy + r * math.sin(a))))
    return pts


def _corona(d, cx, y):
    pts = [(cx - 17, y + 12), (cx - 19, y - 6), (cx - 9, y + 3), (cx, y - 10), (cx + 9, y + 3),
           (cx + 19, y - 6), (cx + 17, y + 12)]
    d.polygon([(_p(a), _p(b)) for a, b in pts], fill=ORO, outline=(161, 98, 7), width=_p(2))
    for a in (-19, 0, 19):
        d.ellipse(_caja(cx + a - 3, y - (10 if a == 0 else 6) - 3, cx + a + 3, y - (10 if a == 0 else 6) + 3),
                  fill=(239, 68, 68))


def _pildora(d, x, y, texto, fondo, color=BLANCO, px=13):
    ancho = d.textlength(texto, font=fuente(px)) / S + 16
    d.rounded_rectangle(_caja(x - ancho / 2, y - 10, x + ancho / 2, y + 10), radius=_p(10), fill=fondo)
    _texto(d, (x, y + 0.5), texto, px, fill=color, anchor="mm")


def _carril(d, st, i, b, previas, golpes, lider, rnd, final=False):
    y0 = carril_y(i)
    cy = y0 + CARRIL_H / 2 + 2
    acento = COLOR[b.bid]["acento"]
    antes = previas.get(b.bid) if previas else None
    terminado = b.lugar is not None and b.pos >= LARGO_PISTA

    if terminado:
        cx = COLUMNA_X0 + 52
    else:
        cx = max(ETIQ_X1 + TAM_BICHO / 2 + 4, casilla_x(min(b.pos, LARGO_PISTA - 1)) - TAM_BICHO * 0.32)
    delta = (b.pos - antes[0]) if antes else 0

    # Estela de velocidad
    if delta:
        x_antes = max(ETIQ_X1 + TAM_BICHO / 2 + 4, casilla_x(min(antes[0], LARGO_PISTA)) - TAM_BICHO * 0.32)
        cola = cx - TAM_BICHO * 0.42 if delta > 0 else cx + TAM_BICHO * 0.42
        color = acento if delta > 0 else (239, 68, 68)
        for k, dy in enumerate((-22, -6, 10, 24)):
            largo = 1.0 - k * 0.12
            x_ini = cola + (x_antes - cola) * largo
            d.line([(_p(x_ini), _p(cy + dy)), (_p(cola), _p(cy + dy))], fill=color + (150 - k * 25,),
                   width=_p(5 - k))
        if not terminado:
            d.ellipse(_caja(x_antes - 26, cy + 26, x_antes - 4, cy + 38), fill=(255, 255, 255, 60))

    # Estallido de golpe
    golpe = golpes.get(b.bid)
    if golpe:
        d.polygon(_estrella(cx, cy, 58, 30, 12, rnd.uniform(0, 1)), fill=(250, 204, 21, 230))
        d.polygon(_estrella(cx, cy, 40, 22, 12, rnd.uniform(0, 1)), fill=(249, 115, 22, 230))

    if final and not terminado:
        cx = -1000  # en el podio final no se dibujan los que no cruzaron la meta
    sombra_y = cy + TAM_BICHO * 0.45
    d.ellipse(_caja(cx - 30, sombra_y - 5, cx + 30, sombra_y + 5), fill=(0, 0, 0, 70))
    dibujar_bicho(d, b.bid, cx, cy, TAM_BICHO, mareado=b.mareado > 0 and not terminado)

    if golpe:
        _texto(d, (cx + 4, y0 + 14), golpe, 26, fill=(254, 240, 138), anchor="mm", stroke=3,
               stroke_fill=(127, 29, 29))
    if b.bid == lider:
        _corona(d, cx + 28, y0 + 12)
    if b.mareado > 0 and not terminado:
        for k in range(3):
            ang = rnd.uniform(0, 6.28)
            d.polygon(_estrella(cx + 8 + (k - 1) * 18, y0 + 13 + (k % 2) * 6, 7, 3, 5, ang), fill=(250, 204, 21))
    if b.dormido and not terminado:
        for k, px in enumerate((14, 18, 22)):
            _texto(d, (cx + 26 + k * 12, y0 + 30 - k * 10), "z", px, fill=(191, 219, 254), anchor="mm", stroke=2,
                   stroke_fill=(30, 58, 138))
    if delta and not golpe:
        txt = "+{}".format(delta) if delta > 0 else "−{}".format(-delta)
        _texto(d, (cx - 16, y0 + 12), txt, 24, fill=(134, 239, 172) if delta > 0 else (252, 165, 165), anchor="mm",
               stroke=3, stroke_fill=NEGRO)

    # Columna derecha
    cx_col = (COLUMNA_X0 + W) / 2
    if b.lugar is not None:
        mx, my = W - 40, cy - 4
        d.ellipse(_caja(mx - 24, my - 24, mx + 24, my + 24), fill=MEDALLA_COLOR.get(b.lugar, PLATA),
                  outline=BLANCO, width=_p(3))
        _texto(d, (mx, my + 1), "{}º".format(b.lugar), 22, fill=NEGRO, anchor="mm")
    else:
        falta = LARGO_PISTA - b.pos
        _texto(d, (cx_col, y0 + 22), "FALTAN", 13, fill=(148, 163, 184), anchor="mm")
        _texto(d, (cx_col, y0 + 54), str(falta), 40 if falta > 3 else 46,
               fill=(248, 113, 113) if falta <= 3 else acento, anchor="mm", stroke=1)
        if b.mareado > 0:
            _pildora(d, cx_col, y0 + 88, "MAREADO", (124, 58, 237))
        elif b.dormido:
            _pildora(d, cx_col, y0 + 88, "DORMIDO", (37, 99, 235))


def _flashes(d, rnd, cantidad):
    for _ in range(cantidad):
        x = rnd.uniform(20, W - 20)
        y = rnd.uniform(TRIBUNA_Y0 + 10, TRIBUNA_Y1 - 14)
        d.polygon(_estrella(x, y, 13, 3, 4, 0.0), fill=(255, 255, 255, 235))
        d.ellipse(_caja(x - 5, y - 5, x + 5, y + 5), fill=(255, 255, 255, 255))


INFO_CARTA = {
    "MAREO": ("MAREO", "a pasitos"), "CAFE": ("CAFÉ", "+2 y despierta"), "CHOQUE": ("EMBESTIDA", "al de adelante"),
    "PETARDO": ("PETARDO", "+5 y mareado"), "SIESTA": ("SIESTA", "se duerme"), "CAMBIO": ("CAMBIAZO", "con el 1º"),
    "ESTAMPIDA": ("ESTAMPIDA", "todos +2"), "REVANCHA": ("REVANCHA", "el último +3"),
}


def _carta(d, x, y, carta):
    ancho, alto = 196, 96
    tipo, bid, v = carta.split(":")
    v = int(v)
    acento = COLOR[bid]["acento"] if bid in COLOR else (147, 51, 234)
    d.rounded_rectangle(_caja(x + 4, y + 5, x + ancho + 4, y + alto + 5), radius=_p(12), fill=(0, 0, 0, 110))
    d.rounded_rectangle(_caja(x, y, x + ancho, y + alto), radius=_p(12), fill=(250, 250, 249), outline=acento,
                        width=_p(4))
    d.rounded_rectangle(_caja(x, y, x + 72, y + alto), radius=_p(12), fill=acento)
    d.rectangle(_caja(x + 60, y, x + 72, y + alto), fill=acento)
    if bid in BICHOS:
        d.ellipse(_caja(x + 6, y + 18, x + 66, y + 78), fill=COLOR[bid]["claro"])
        dibujar_bicho(d, bid, x + 36, y + 48, 54)
    else:
        _texto(d, (x + 36, y + alto / 2), "TODOS", 15, fill=BLANCO, anchor="mm")
    if tipo == "MOV":
        grande, chico = ("+{}".format(v), "AVANZA") if v > 0 else ("−{}".format(-v), "RETROCEDE")
        color = (21, 128, 61) if v > 0 else (185, 28, 28)
    elif tipo == "VIENTO":
        grande, chico = "VIENTO", "todos +1" if v > 0 else "todos −1"
        color = NEGRO
    else:
        grande, chico = INFO_CARTA.get(tipo, (tipo, ""))
        color = NEGRO
    centro = x + 72 + (ancho - 72) / 2
    _texto(d, (centro, y + 42), grande, _ajustar(d, grande, ancho - 84, 40 if tipo == "MOV" else 24), fill=color,
           anchor="mm")
    _texto(d, (centro, y + 76), chico, _ajustar(d, chico, ancho - 84, 14), fill=(87, 83, 78), anchor="mm")


def _pie(d, st, cartas, tit, rnd, final=False):
    _gradiente(d, 0, PIE_Y0, W, H, (15, 23, 42), (2, 6, 23))
    d.line([(0, _p(PIE_Y0)), (_p(W), _p(PIE_Y0))], fill=(250, 204, 21), width=_p(3))
    x = 20
    for carta in (cartas or [])[-2:]:
        _carta(d, x, PIE_Y0 + 16, carta)
        x += 212
    if final:
        x = 0
    elif not cartas:
        d.rounded_rectangle(_caja(20, PIE_Y0 + 16, 216, PIE_Y0 + 112), radius=_p(12), fill=(30, 58, 138),
                            outline=(147, 197, 253), width=_p(3))
        for k in range(4):
            d.rounded_rectangle(_caja(44 + k * 6, PIE_Y0 + 30 - k * 3, 108 + k * 6, PIE_Y0 + 100 - k * 3),
                                radius=_p(8), fill=(29, 78, 216), outline=BLANCO, width=_p(2))
        _texto(d, (176, PIE_Y0 + 56), str(len(st.mazo)), 30, anchor="mm")
        _texto(d, (176, PIE_Y0 + 84), "cartas", 13, fill=(191, 219, 254), anchor="mm")
        x = 232
    zona0, zona1 = (24 if final else max(x + 10, 460)), W - 24
    cx = (zona0 + zona1) / 2
    if tit:
        texto, color = tit
        px = _ajustar(d, texto, zona1 - zona0 - 20, 52, 20)
        d.polygon([(_p(zona0), _p(PIE_Y0 + 22)), (_p(zona1), _p(PIE_Y0 + 14)), (_p(zona1 - 14), _p(PIE_Y0 + 86)),
                   (_p(zona0 + 10), _p(PIE_Y0 + 92))], fill=(185, 28, 28))
        _texto(d, (cx, PIE_Y0 + 53), texto, px, fill=color, anchor="mm", stroke=4)
    if final:
        sub = "La carrera duró {} cartas".format(st.reveladas)
    elif cartas:
        sub = "Carta #{} · quedan {} en el mazo".format(st.reveladas, len(st.mazo))
    else:
        sub = "{} cartas en el mazo · se queman {} boca abajo".format(len(st.mazo), len(st.quemadas))
    _texto(d, (cx, H - 18), sub, 15, fill=(148, 163, 184), anchor="mm")


def _sombra(d, alfa=150):
    d.rectangle(_caja(0, TRIBUNA_Y0, W, PIE_Y0), fill=(2, 6, 23, alfa))


def _cuenta(d, cuenta):
    _sombra(d, 120)
    cy = (PISTA_Y0 + PISTA_Y1) / 2
    if len(cuenta) <= 2:
        d.ellipse(_caja(W / 2 - 120, cy - 120, W / 2 + 120, cy + 120), fill=(220, 38, 38, 230), outline=BLANCO,
                  width=_p(8))
        _texto(d, (W / 2, cy + 6), cuenta, 170, anchor="mm", stroke=6)
    else:
        px = _ajustar(d, cuenta, W - 160, 110, 30)
        _texto(d, (W / 2, cy), cuenta, px, fill=(250, 204, 21), anchor="mm", stroke=8)


def _podio(d, st, rnd):
    _sombra(d, 185)
    for _ in range(140):  # papelitos
        x, y = rnd.uniform(0, W), rnd.uniform(TRIBUNA_Y0, PIE_Y0)
        c = rnd.choice([(239, 68, 68), (250, 204, 21), (59, 130, 246), (34, 197, 94), (236, 72, 153), BLANCO])
        d.polygon(_estrella(x, y, rnd.uniform(4, 8), rnd.uniform(1.5, 3), 2, rnd.uniform(0, 3)), fill=c)
    base = PIE_Y0 - 14
    bloques = [(2, W / 2 - 230, 120), (1, W / 2, 175), (3, W / 2 + 230, 85)]
    for lugar, cx, alto in bloques:
        if len(st.podio) < lugar:
            continue
        bid = st.podio[lugar - 1]
        color = MEDALLA_COLOR[lugar]
        d.rectangle(_caja(cx - 100, base - alto, cx + 100, base), fill=color, outline=BLANCO, width=_p(4))
        _texto(d, (cx, base - alto / 2), "{}º".format(lugar), 56, fill=NEGRO, anchor="mm")
        tam = 150 if lugar == 1 else 120
        dibujar_bicho(d, bid, cx, base - alto - tam * 0.46, tam)
        _texto(d, (cx, base - alto - tam - 4), BICHOS[bid]["nombre"].upper(), 20, fill=COLOR[bid]["acento"],
               anchor="mm", stroke=3)
        if lugar == 1:
            _corona(d, cx + 22, base - alto - tam - 30)


def render_cuadro(game, cartas=None, previas=None, cuenta=None, final=False, titular_fijo=None):
    """JPEG (bytes) de un cuadro de la transmisión."""
    st = game.board.state
    img = _fondo().copy()
    d = ImageDraw.Draw(img, "RGBA")
    rnd = random.Random()

    golpes = _golpes(st, cartas, previas)
    lider = _lider_actual(st)
    vivos = [b for b in st.bichos if b.lugar is None]
    recta_final = bool(vivos) and not final and max(b.pos for b in vivos) >= LARGO_PISTA - RECTA_FINAL
    tit = titular_fijo or (None if final else titular(st, cartas, previas))
    if final and st.podio:
        tit = ("¡¡GANÓ {}!!".format(BICHOS[st.podio[0]]["nombre"].upper()), ORO)

    _encabezado(d, st, en_vivo=not final, recta_final=recta_final)
    if tit or final:
        _flashes(d, rnd, 10 if final else 5)
    _etiquetas_apuestas(d, game)
    for i, bid in enumerate(ORDEN_BICHOS):
        b = next((x for x in st.bichos if x.bid == bid), None)
        if b is not None:
            _carril(d, st, i, b, previas, golpes, lider, rnd, final)
    if recta_final:
        d.rectangle(_caja(META_X - 6, PISTA_Y0, META_X + 32, PISTA_Y1), outline=(250, 204, 21, 200), width=_p(4))
    _pie(d, st, cartas, tit, rnd, final)
    if cuenta:
        _cuenta(d, cuenta)
    if final:
        _podio(d, st, rnd)

    img = img.resize((W, H), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=88, optimize=True)
    return buf.getvalue()
