# Motor de reglas de Carrera de Bichos (sin Telegram): mazo, resolución de cartas,
# relato de la carrera, dibujo de la pista y pago de apuestas.

import random

from CarreraBichos.Boardgamebox.State import Bicho
from CarreraBichos.Constants.Cartas import (
    BICHOS, ORDEN_BICHOS, LARGO_PISTA, CARTAS_POR_BICHO, CARTAS_GLOBALES, CARTAS_FIJAS_POR_BICHO,
    CARTAS_AL_AZAR, CARTAS_QUEMADAS, MAX_MEZCLAS, TURNOS_MAREO, LLEGADAS_PARA_TERMINAR,
    PAGOS_GANADOR, PAGOS_PODIO, MULTA_FUERTE, MULTIPLICADOR_FINAL, APUESTAS_ESPECIALES,
    UMBRAL_CARTAS_LARGA, UMBRAL_FOTO, UMBRAL_PALIZA, CARTA_REMONTADA, CANTIDAD_CARRERAS,
    bicho_txt, carta_txt,
)

MEDALLAS = {1: "🥇", 2: "🥈", 3: "🥉", 4: "4️⃣"}
MAX_TICKER = 6
# A cuántas casillas de la meta la transmisión pasa a mostrar de a una carta.
DISTANCIA_SUSPENSO = 6
FRASES_AVANCE = [
    "{} avanza {}.",
    "{} trota {} casillas.",
    "{} suma {} y sigue en carrera.",
    "{} acelera: +{}.",
]


# ---------------------------------------------------------------------------
# Mazo
# ---------------------------------------------------------------------------

def biblioteca():
    cartas = []
    for b in ORDEN_BICHOS:
        for tipo, valor, copias in CARTAS_POR_BICHO:
            cartas += ["{}:{}:{}".format(tipo, b, valor)] * copias
    for tipo, valor, copias in CARTAS_GLOBALES:
        cartas += ["{}:-:{}".format(tipo, valor)] * copias
    return cartas


def carta_al_azar():
    return random.choice(biblioteca())


def armar_mazo_base():
    base = []
    for b in ORDEN_BICHOS:
        for tipo, valor in CARTAS_FIJAS_POR_BICHO:
            base.append("{}:{}:{}".format(tipo, b, valor))
    pool = biblioteca()
    random.shuffle(pool)
    base += pool[:CARTAS_AL_AZAR]
    return base


def ordenar_para_mostrar(cartas):
    def clave(c):
        tipo, b, v = c.split(":")
        return (ORDEN_BICHOS.index(b) if b in ORDEN_BICHOS else 9, tipo != "MOV", tipo, -int(v))
    return sorted(cartas, key=clave)


# ---------------------------------------------------------------------------
# Preparación
# ---------------------------------------------------------------------------

def preparar_carrera(st, aportes):
    st.bichos = [Bicho(b) for b in ORDEN_BICHOS]
    st.podio = []
    st.mazo = list(st.mazo_base) + list(aportes)
    random.shuffle(st.mazo)
    st.quemadas = [st.mazo.pop() for _ in range(min(CARTAS_QUEMADAS, len(st.mazo)))]
    st.descarte = []
    st.reveladas = 0
    st.mezclas = 0
    st.ticker = []
    st.stats = {
        "desmayos": 0, "cambiazos": 0, "llegadas": [], "cruzo_mareado": False,
        "dist_ultimo": 0, "ultimos_tarde": [], "lider": None,
    }


def bicho(st, bid):
    for b in st.bichos:
        if b.bid == bid:
            return b
    return None


def en_pista(st):
    return [b for b in st.bichos if b.lugar is None]


def carrera_terminada(st):
    return len(st.podio) >= len(st.bichos)


# ---------------------------------------------------------------------------
# Resolución de cartas
# ---------------------------------------------------------------------------

def robar(st):
    """Saca la próxima carta. Devuelve (carta, aviso_mezcla)."""
    aviso = None
    if not st.mazo:
        st.mezclas += 1
        st.mazo = st.descarte + st.quemadas
        st.descarte, st.quemadas = [], []
        random.shuffle(st.mazo)
        st.quemadas = [st.mazo.pop() for _ in range(min(CARTAS_QUEMADAS, len(st.mazo)))]
        aviso = "🔄 ¡Se acabó el mazo! Se mezcla todo, se queman {} y la carrera sigue.".format(CARTAS_QUEMADAS)
    return st.mazo.pop(), aviso


def _cruzar(st, b, eventos):
    b.pos = LARGO_PISTA
    st.podio.append(b.bid)
    b.lugar = len(st.podio)
    st.stats["llegadas"].append(st.reveladas)
    if b.mareado > 0:
        st.stats["cruzo_mareado"] = True
    frases = {
        1: "🏁🥇 ¡¡¡{} CRUZA LA META PRIMERO!!! ¡¡GANADOR!!",
        2: "🏁🥈 ¡{} entra segundo!",
        3: "🏁🥉 ¡{} completa el podio!",
    }
    eventos.append(frases.get(b.lugar, "🏁 {} llega.").format(bicho_txt(b.bid)))


def _desplazar(st, b, n, eventos, puede_ganar=True):
    """Mueve b n casillas respetando la meta y el piso."""
    if b.lugar is not None or n == 0:
        return
    destino = max(0, b.pos + n)
    if destino >= LARGO_PISTA:
        if puede_ganar:
            _cruzar(st, b, eventos)
            return
        destino = LARGO_PISTA - 1
    b.pos = destino


def _marear(st, b, eventos):
    if b.mareado > 0:
        st.stats["desmayos"] += 1
        eventos.append("😵‍💫 ¡{} ya estaba mareado y SE DESMAYA! Retrocede 3.".format(bicho_txt(b.bid)))
        _desplazar(st, b, -3, eventos)
    else:
        eventos.append("😵 {} queda mareado: sus próximos {} movimientos son de a una casilla.".format(
            bicho_txt(b.bid), TURNOS_MAREO))
    b.mareado = TURNOS_MAREO


def resolver_carta(st, carta):
    """Aplica una carta y devuelve la lista de sucesos para el relato."""
    tipo, bid, valor = carta.split(":")
    valor = int(valor)
    eventos = []
    b = bicho(st, bid) if bid in BICHOS else None
    if b is not None and b.lugar is not None:
        eventos.append("{} ya terminó: la carta no tiene efecto.".format(bicho_txt(bid)))
        return eventos

    if tipo == "MOV":
        if b.dormido:
            b.dormido = False
            eventos.append("⏰ {} se despierta sobresaltado... pero no se mueve.".format(bicho_txt(bid)))
        elif b.mareado > 0:
            b.mareado -= 1
            paso = 1 if valor > 0 else -1
            eventos.append("🥴 {} quería ir {}{}, pero mareado solo da un pasito.".format(
                bicho_txt(bid), "+" if valor > 0 else "−", abs(valor)))
            _desplazar(st, b, paso, eventos)
        else:
            if valor >= 4:
                eventos.append("💨 ¡Qué pique de {}! +{}".format(bicho_txt(bid), valor))
            elif valor < 0:
                eventos.append("↩️ {} se da vuelta y retrocede {}.".format(bicho_txt(bid), -valor))
            else:
                eventos.append(random.choice(FRASES_AVANCE).format(bicho_txt(bid), valor))
            _desplazar(st, b, valor, eventos)
    elif tipo == "MAREO":
        _marear(st, b, eventos)
    elif tipo == "CAFE":
        b.mareado = 0
        b.dormido = False
        eventos.append("☕ {} se toma un cafecito y arranca con todo: +2.".format(bicho_txt(bid)))
        _desplazar(st, b, 2, eventos)
    elif tipo == "CHOQUE":
        adelante = [o for o in en_pista(st) if o is not b and o.pos > b.pos]
        if adelante:
            minimo = min(o.pos for o in adelante)
            victima = [o for o in adelante if o.pos == minimo][0]
            b.pos = victima.pos
            eventos.append("💥 ¡{} embiste a {}!".format(bicho_txt(bid), bicho_txt(victima.bid)))
            _marear(st, victima, eventos)
        else:
            eventos.append("💥 {} embiste... ¡al aire! Avanza 2.".format(bicho_txt(bid)))
            _desplazar(st, b, 2, eventos)
    elif tipo == "PETARDO":
        eventos.append("🧨 ¡BOOM! {} sale disparado 5 casillas...".format(bicho_txt(bid)))
        _desplazar(st, b, 5, eventos)
        if b.lugar is None:
            b.mareado = TURNOS_MAREO
            eventos.append("   ...y queda mareado por la explosión.")
    elif tipo == "SIESTA":
        b.dormido = True
        eventos.append("💤 {} se acuesta a dormir una siesta en plena pista.".format(bicho_txt(bid)))
    elif tipo == "CAMBIO":
        st.stats["cambiazos"] += 1
        otros = [o for o in en_pista(st) if o is not b]
        if otros:
            maximo = max(o.pos for o in en_pista(st))
            if b.pos == maximo:
                minimo = min(o.pos for o in otros)
                otro = [o for o in otros if o.pos == minimo][0]
                eventos.append("🔀 {} se confunde y cambia lugar con el último, {}.".format(
                    bicho_txt(bid), bicho_txt(otro.bid)))
            else:
                otro = [o for o in otros if o.pos == maximo][0]
                eventos.append("🔀 ¡CAMBIAZO! {} aparece en la punta y {} vuelve a su lugar.".format(
                    bicho_txt(bid), bicho_txt(otro.bid)))
            b.pos, otro.pos = otro.pos, b.pos
    elif tipo == "VIENTO":
        eventos.append("🌬️ ¡Viento a favor! Todos +1." if valor > 0 else "🌪️ ¡Viento en contra! Todos −1.")
        for o in en_pista(st):
            _desplazar(st, o, valor, eventos, puede_ganar=False)
    elif tipo == "ESTAMPIDA":
        eventos.append("🐾 ¡ESTAMPIDA! Todos corren +2.")
        for o in en_pista(st):
            _desplazar(st, o, 2, eventos, puede_ganar=False)
    elif tipo == "REVANCHA":
        vivos = en_pista(st)
        if vivos:
            minimo = min(o.pos for o in vivos)
            for o in [o for o in vivos if o.pos == minimo]:
                eventos.append("🔥 ¡Revancha! {} se enciende desde el fondo: +3.".format(bicho_txt(o.bid)))
                _desplazar(st, o, 3, eventos, puede_ganar=False)
    return eventos


def comentarios_de_carrera(st, lider_previo, bid_carta):
    """Comentarios del locutor que dependen de la situación (no de la carta)."""
    eventos = []
    vivos = en_pista(st)
    if not vivos:
        return eventos
    maximo = max(b.pos for b in vivos)
    punteros = [b for b in vivos if b.pos == maximo]
    if len(punteros) == 1 and punteros[0].bid != lider_previo and maximo > 0 and not st.podio:
        eventos.append("📢 ¡{} toma la punta!".format(bicho_txt(punteros[0].bid)))
        st.stats["lider"] = punteros[0].bid
    elif len(punteros) > 1 and lider_previo is not None and not st.podio:
        st.stats["lider"] = None
        eventos.append("📢 ¡Mano a mano en la punta entre {}!".format(
            " y ".join(BICHOS[b.bid]["emoji"] for b in punteros)))
    cerca = [b for b in vivos if b.bid == bid_carta and LARGO_PISTA - b.pos <= 3]
    if cerca:
        b = cerca[0]
        eventos.append("😱 ¡{} está a {} de la meta!".format(bicho_txt(b.bid), LARGO_PISTA - b.pos))

    if st.reveladas > CARTA_REMONTADA and len(vivos) > 1:
        minimo = min(b.pos for b in vivos)
        ultimos = [b for b in vivos if b.pos == minimo]
        if len(ultimos) == 1 and ultimos[0].bid not in st.stats["ultimos_tarde"]:
            st.stats["ultimos_tarde"].append(ultimos[0].bid)
    return eventos


def _es_de_bicho_terminado(st, carta):
    b = bicho(st, carta.split(":")[1])
    return b is not None and b.lugar is not None


def paso_de_carrera(st):
    """Revela una carta y la resuelve. Devuelve (carta, eventos).

    Las cartas de bichos que ya cruzaron la meta se descartan de corrido (no
    tienen efecto) para no llenar la transmisión de tiempo muerto."""
    lider_previo = st.stats.get("lider")
    eventos = []
    salteadas = 0
    while True:
        carta, aviso = robar(st)
        st.reveladas += 1
        if aviso:
            eventos.append(aviso)
        if _es_de_bicho_terminado(st, carta) and st.mezclas <= MAX_MEZCLAS:
            st.descarte.append(carta)
            salteadas += 1
            continue
        break
    if salteadas:
        eventos.append("🗑️ Se descarta{} {} carta{} de bichos que ya llegaron.".format(
            "n" if salteadas > 1 else "", salteadas, "s" if salteadas > 1 else ""))
    eventos += resolver_carta(st, carta)
    st.descarte.append(carta)
    eventos += comentarios_de_carrera(st, lider_previo, carta.split(":")[1])
    _cerrar_si_corresponde(st)
    return carta, eventos


def _cerrar_si_corresponde(st):
    """Cuando cruzan los que definen las apuestas (o el mazo se mezcló demasiado),
    ordena al resto por posición."""
    vivos = en_pista(st)
    if len(st.podio) >= LLEGADAS_PARA_TERMINAR or (st.mezclas > MAX_MEZCLAS and vivos):
        if vivos:
            st.stats["dist_ultimo"] = LARGO_PISTA - min(b.pos for b in vivos)
        for b in sorted(vivos, key=lambda x: -x.pos):
            st.podio.append(b.bid)
            b.lugar = len(st.podio)


# ---------------------------------------------------------------------------
# Apuestas
# ---------------------------------------------------------------------------

def preparar_apuestas(st):
    st.boletos = {}
    for b in ORDEN_BICHOS:
        st.boletos["G_" + b] = list(PAGOS_GANADOR)
        st.boletos["P_" + b] = list(PAGOS_PODIO)
    st.especial = random.choice(list(APUESTAS_ESPECIALES.keys()))
    _, pagos_si, pagos_no = APUESTAS_ESPECIALES[st.especial]
    st.boletos["SI"] = list(pagos_si)
    st.boletos["NO"] = list(pagos_no)


def boleto_txt(game, clave):
    if clave.startswith("G_"):
        return "🏆 Ganador {}".format(bicho_txt(clave[2:]))
    if clave.startswith("P_"):
        return "🥈 Podio {}".format(bicho_txt(clave[2:]))
    st = game.board.state
    pregunta = APUESTAS_ESPECIALES.get(st.especial, ("?",))[0]
    return "❓ {} a «{}»".format("SÍ" if clave == "SI" else "NO", pregunta)


def boleto_boton(clave, pago):
    if clave.startswith("G_"):
        return "🏆 {} ${}".format(BICHOS[clave[2:]]["emoji"], pago)
    if clave.startswith("P_"):
        return "🥈 {} ${}".format(BICHOS[clave[2:]]["emoji"], pago)
    return "❓ {} ${}".format("SÍ" if clave == "SI" else "NO", pago)


def especial_cumplida(st):
    s = st.stats
    e = st.especial
    if e == "desmayo":
        return s["desmayos"] > 0
    if e == "cambiazo":
        return s["cambiazos"] > 0
    if e == "larga":
        return st.reveladas > UMBRAL_CARTAS_LARGA
    if e == "mareado":
        return s["cruzo_mareado"]
    if e == "foto":
        ll = s["llegadas"]
        return len(ll) >= 2 and ll[1] - ll[0] <= UMBRAL_FOTO
    if e == "paliza":
        return s["dist_ultimo"] >= UMBRAL_PALIZA
    if e == "remontada":
        return bool(st.podio) and st.podio[0] in s["ultimos_tarde"]
    return False


def boleto_gana(st, clave):
    if clave.startswith("G_"):
        return st.podio[:1] == [clave[2:]]
    if clave.startswith("P_"):
        return clave[2:] in st.podio[:2]
    cumplida = especial_cumplida(st)
    return cumplida if clave == "SI" else not cumplida


def pagar_apuestas(game):
    """Paga todas las apuestas y devuelve el texto con el detalle."""
    st = game.board.state
    mult = MULTIPLICADOR_FINAL if st.carrera == CANTIDAD_CARRERAS else 1
    lineas = []
    for p in game.player_sequence:
        total = 0
        detalle = []
        for a in p.apuestas:
            if boleto_gana(st, a["t"]):
                monto = a["pago"] * (2 if a["fuerte"] else 1) * mult
                detalle.append("✅ {}{} +${}".format(boleto_boton(a["t"], a["pago"]), "🔥" if a["fuerte"] else "", monto))
            else:
                monto = -MULTA_FUERTE * mult if a["fuerte"] else 0
                detalle.append("❌ {}{} {}".format(boleto_boton(a["t"], a["pago"]), "🔥" if a["fuerte"] else "",
                                                   "−${}".format(-monto) if monto else "$0"))
            total += monto
        p.dinero = max(0, p.dinero + total)
        signo = "+" if total >= 0 else "−"
        lineas.append("*{}*: {} → {}${} = *${}*".format(p.name, " · ".join(detalle) or "sin apuestas",
                                                       signo, abs(total), p.dinero))
        p.apuestas = []
    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Dibujo
# ---------------------------------------------------------------------------

def dibujar_pista(st):
    lineas = []
    for b in st.bichos:
        e = BICHOS[b.bid]["emoji"]
        if b.lugar is not None and b.pos >= LARGO_PISTA:
            linea = "·" * LARGO_PISTA + "│" + e + MEDALLAS.get(b.lugar, "")
        else:
            celdas = ["·"] * LARGO_PISTA
            celdas[min(b.pos, LARGO_PISTA - 1)] = e
            linea = "".join(celdas) + "│🏁"
            if b.lugar is not None:
                linea += MEDALLAS.get(b.lugar, "")
            elif b.mareado > 0:
                linea += "😵"
            elif b.dormido:
                linea += "💤"
        lineas.append(linea)
    return "```\n" + "\n".join(lineas) + "\n```"


def texto_podio(st):
    partes = []
    for i in range(1, 4):
        bid = st.podio[i - 1] if len(st.podio) >= i else None
        partes.append("{} {}".format(MEDALLAS[i], BICHOS[bid]["emoji"] if bid else "—"))
    return "  ".join(partes)


def cartas_por_cuadro(st):
    """Lejos de la meta se muestran 2 cartas por cuadro (ritmo); cerca, de a una (suspenso)."""
    vivos = en_pista(st)
    if st.podio or not vivos or max(b.pos for b in vivos) >= LARGO_PISTA - DISTANCIA_SUSPENSO:
        return 1
    return 2


def cuadro_en_vivo(st, cartas=None, eventos=None, titulo=None, con_pista=True):
    """Un cuadro de la transmisión: las cartas, la pista y lo que pasó con ellas.
    Sin `eventos` se repite lo último relatado (sirve para retomar).
    Con `con_pista=False` es el relato que acompaña a la imagen (la pista ya se ve ahí)."""
    titulo = titulo or "🔴 *EN VIVO* — Carrera {}/{}".format(st.carrera, CANTIDAD_CARRERAS)
    texto = "🏟️ " + titulo + "\n"
    if cartas:
        nombres = " · ".join("*{}*".format(carta_txt(c)) for c in cartas)
        texto += "🃏 Carta{} {}: {}   (quedan {})\n".format(
            "s" if len(cartas) > 1 else "", st.reveladas, nombres, len(st.mazo))
    if con_pista:
        texto += dibujar_pista(st)
    if eventos is not None:
        st.ticker = eventos[-MAX_TICKER:]
    if st.ticker:
        texto += "\n" + "\n".join(st.ticker)
    texto += "\n\n" + texto_podio(st)
    return texto


def texto_tablero(game):
    st = game.board.state
    texto = "🏟️ *Carrera de Bichos* — Carrera {}/{} — {}\n".format(st.carrera, CANTIDAD_CARRERAS, st.fase_actual)
    if st.bichos:
        texto += dibujar_pista(st) + "\n"
    texto += "\n*Plata:*\n" + "\n".join(
        "• {}: ${}{}".format(p.name, p.dinero,
                              " — " + ", ".join(boleto_boton(a["t"], a["pago"]) + ("🔥" if a["fuerte"] else "")
                                                for a in p.apuestas) if p.apuestas else "")
        for p in sorted(game.player_sequence, key=lambda p: -p.dinero))
    return texto
