# -*- coding: utf-8 -*-
"""Repetición en video de la última carrera.

Durante la transmisión se guarda una foto liviana de cada cuadro (posiciones, cartas,
titulares...) en el estado de la partida, así sobrevive a un reinicio del bot. Al
terminar la carrera se puede armar un MP4 que vuelve a dibujar cada cuadro con
render.py y agrega cuadros intermedios para que los bichos corran de forma fluida.
"""
import types
from io import BytesIO

from PIL import Image

from CarreraBichos.Boardgamebox.State import Bicho
import CarreraBichos.render as R

FPS = 12
TRANSICION = 6         # cuadros intermedios en los que los bichos se desplazan
PAUSA = 12             # cuadros que se queda quieta cada jugada (1 s)
PAUSA_CUENTA = 10
PAUSA_LLEGADA = 24     # cuando alguien cruza la meta
PAUSA_FINAL = 54       # podio


# ---------------------------------------------------------------------------
# Grabación
# ---------------------------------------------------------------------------

def empezar(st, game):
    """Arranca la grabación de una carrera nueva (las apuestas ya están cerradas)."""
    st.repeticion_actual = {
        "carrera": st.carrera,
        "apuestas": [[p.name, [[a["t"], a["fuerte"]] for a in p.apuestas]] for p in game.player_sequence],
        "cuadros": [],
    }


def grabar(st, cartas=None, previas=None, cuenta=None, final=False, titular_fijo=None, **_):
    rep = getattr(st, "repeticion_actual", None)
    if rep is None:
        return
    rep["cuadros"].append({
        "bichos": [[b.bid, b.pos, b.mareado, b.dormido, b.lugar] for b in st.bichos],
        "podio": list(st.podio),
        "reveladas": st.reveladas,
        "mazo": len(st.mazo),
        "quemadas": len(st.quemadas),
        "desmayos": (st.stats or {}).get("desmayos", 0),
        "cartas": list(cartas or []),
        "previas": {k: list(v) if isinstance(v, tuple) else v for k, v in (previas or {}).items()} or None,
        "cuenta": cuenta,
        "final": final,
        "titular": [titular_fijo[0], list(titular_fijo[1])] if titular_fijo else None,
    })


def cerrar(st):
    """La carrera terminó: la grabación pasa a ser 'la última carrera'."""
    rep = getattr(st, "repeticion_actual", None)
    if rep and rep["cuadros"]:
        st.repeticion = rep
        st.repeticion_file_id = None
        st.repeticion_formato = None
    st.repeticion_actual = None


def disponible(st):
    rep = getattr(st, "repeticion", None)
    return rep if rep and rep.get("cuadros") else None


# ---------------------------------------------------------------------------
# Video
# ---------------------------------------------------------------------------

def _juego(rep, cuadro, pos_visual=None, gestos=None):
    """Partida "de mentira" con lo justo para que render.py dibuje el cuadro."""
    bichos = []
    for bid, pos, mareado, dormido, lugar in cuadro["bichos"]:
        b = Bicho(bid)
        b.pos, b.mareado, b.dormido, b.lugar = pos, mareado, dormido, lugar
        if pos_visual is not None:
            b.pos_visual = pos_visual[bid]
            b.gesto_visual = (gestos or {}).get(bid)
        bichos.append(b)
    st = types.SimpleNamespace(
        carrera=rep["carrera"], bichos=bichos, podio=list(cuadro["podio"]), reveladas=cuadro["reveladas"],
        mazo=[None] * cuadro["mazo"], quemadas=[None] * cuadro["quemadas"],
        stats={"desmayos": cuadro["desmayos"]},
    )
    jugadores = [types.SimpleNamespace(name=n, apuestas=[{"t": t, "fuerte": f} for t, f in aps])
                 for n, aps in rep["apuestas"]]
    return types.SimpleNamespace(board=types.SimpleNamespace(state=st), player_sequence=jugadores)


def _previas(cuadro):
    p = cuadro["previas"]
    return {k: tuple(v) if isinstance(v, list) else v for k, v in p.items()} if p else None


def _suave(t):
    return t * t * (3 - 2 * t)


def cuadros_video(rep):
    """Genera (imagen PIL, cuántas veces se repite) para toda la carrera."""
    anterior = None
    for cuadro in rep["cuadros"]:
        titular = (cuadro["titular"][0], tuple(cuadro["titular"][1])) if cuadro["titular"] else None
        # Transición: los bichos se desplazan desde el cuadro anterior mientras se ven las cartas nuevas.
        if anterior is not None and not cuadro["final"]:
            antes = {b[0]: b[1] for b in anterior["bichos"]}
            ahora = {b[0]: b[1] for b in cuadro["bichos"]}
            if antes != ahora:
                gestos = {}
                aturdidos = {b[0] for b in anterior["bichos"] if b[2] > 0 or b[3]}  # mareados o dormidos
                for bid in ahora:
                    delta = ahora[bid] - antes.get(bid, ahora[bid])
                    if bid not in aturdidos:
                        gestos[bid] = "turbo" if delta >= 2 else ("triste" if delta < 0 else None)
                for k in range(1, TRANSICION + 1):
                    t = _suave(k / (TRANSICION + 1))
                    pos = {bid: antes.get(bid, p) + (p - antes.get(bid, p)) * t for bid, p in ahora.items()}
                    yield R.render_imagen(_juego(rep, anterior, pos, gestos), cartas=cuadro["cartas"]), 1
        img = R.render_imagen(_juego(rep, cuadro), cartas=cuadro["cartas"], previas=_previas(cuadro),
                              cuenta=cuadro["cuenta"], final=cuadro["final"], titular_fijo=titular)
        if cuadro["final"]:
            pausa = PAUSA_FINAL
        elif cuadro["cuenta"] or anterior is None:
            pausa = PAUSA_CUENTA
        elif anterior is not None and len(cuadro["podio"]) > len(anterior["podio"]):
            pausa = PAUSA_LLEGADA
        else:
            pausa = PAUSA
        yield img, pausa
        anterior = cuadro


def armar_mp4(rep):
    """MP4 (H.264) de la carrera. Devuelve los bytes."""
    import av
    buf = BytesIO()
    with av.open(buf, mode="w", format="mp4") as cont:
        stream = cont.add_stream("libx264", rate=FPS)
        stream.width, stream.height = R.W, R.H
        stream.pix_fmt = "yuv420p"
        stream.options = {"crf": "25", "preset": "veryfast", "tune": "animation"}
        n = 0
        for img, veces in cuadros_video(rep):
            frame = av.VideoFrame.from_image(img)
            for _ in range(veces):
                frame.pts = n
                n += 1
                for paquete in stream.encode(frame):
                    cont.mux(paquete)
        for paquete in stream.encode():
            cont.mux(paquete)
    return buf.getvalue()


def armar_gif(rep):
    """Respaldo si no hay H.264: GIF animado más chico (Telegram lo pasa a animación)."""
    imgs, duraciones = [], []
    for img, veces in cuadros_video(rep):
        imgs.append(img.resize((R.W // 2, R.H // 2)).convert("P", palette=Image.Palette.ADAPTIVE, colors=255))
        duraciones.append(int(1000 * veces / FPS))
    buf = BytesIO()
    imgs[0].save(buf, format="GIF", save_all=True, append_images=imgs[1:], duration=duraciones, loop=0,
                 optimize=False)
    return buf.getvalue()


def armar_video(rep):
    """(bytes, 'mp4' | 'gif')."""
    try:
        return armar_mp4(rep), "mp4"
    except Exception:
        return armar_gif(rep), "gif"
