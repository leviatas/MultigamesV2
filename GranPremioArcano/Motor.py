# Motor de reglas de Gran Premio Arcano.
#
# Lógica pura (sin Telegram): mueve corredores, resuelve poderes y escribe el relato
# en st.log. El Controller se encarga de los botones, el dado y los mensajes.

import random

from GranPremioArcano.Boardgamebox.State import Corredor
from GranPremioArcano.Constants.Corredores import (
    CORREDORES, LARGO_PISTA, PISTA_POR_CARRERA, CASILLAS_SALVAJES, SIMBOLO_CASILLA,
    PUNTOS_ORO, PUNTOS_PLATA, NOMBRE_PISTA, CANTIDAD_CARRERAS,
)

# Corta cadenas de efectos (un poder que mueve, que activa otro poder, que mueve...)
PROFUNDIDAD_MAXIMA = 4
PUESTOS_QUE_PUNTUAN = 2


# ---------------------------------------------------------------------------
# Consultas
# ---------------------------------------------------------------------------

def nombre(game, c):
    info = CORREDORES[c.rid]
    jugador = game.playerlist.get(c.uid)
    dueno = jugador.name if jugador else "?"
    return "{} *{}* ({})".format(info["emoji"], info["nombre"], dueno)


def nombre_corto(c):
    info = CORREDORES[c.rid]
    return "{} {}".format(info["emoji"], info["nombre"])


def activos(st):
    return [c for c in st.corredores if c.lugar is None]


def carrera_terminada(st):
    return len(st.llegadas) >= PUESTOS_QUE_PUNTUAN or not activos(st)


def tipo_pista(st):
    return PISTA_POR_CARRERA[(st.carrera - 1) % len(PISTA_POR_CARRERA)]


def corredor_actual(st):
    if not st.orden_turnos:
        return None
    return st.corredores[st.orden_turnos[st.turno_idx]]


def es_ultimo(st, c):
    vivos = activos(st)
    return bool(vivos) and c.pos == min(o.pos for o in vivos)


def solo_en_punta(st, c):
    vivos = activos(st)
    maximo = max(o.pos for o in vivos)
    return c.pos == maximo and sum(1 for o in vivos if o.pos == maximo) == 1


def lideres(st, excluir=None):
    vivos = [c for c in activos(st) if c is not excluir]
    if not vivos:
        return []
    maximo = max(c.pos for c in vivos)
    return [c for c in vivos if c.pos == maximo]


def puede_afectar(fuente, objetivo):
    """La Tortuga Blindada ignora los poderes de otros corredores."""
    if fuente is None or fuente is objetivo:
        return True
    return objetivo.rid != "tortuga"


def _hay(st, rid):
    return [c for c in activos(st) if c.rid == rid]


# ---------------------------------------------------------------------------
# Efectos básicos
# ---------------------------------------------------------------------------

def tropezar(game, c, fuente=None, motivo=""):
    st = game.board.state
    if c.lugar is not None:
        return
    if c.rid in ("fantasma", "robot"):
        st.log.append("   {} es inmune a los tropiezos.".format(nombre_corto(c)))
        return
    if not puede_afectar(fuente, c):
        st.log.append("   🛡️ {} ni se inmuta.".format(nombre_corto(c)))
        return
    if c.tropezado:
        return
    c.tropezado = True
    st.log.append("   💫 {} tropieza{}.".format(nombre_corto(c), motivo))


def teletransportar(game, c, destino, fuente=None):
    st = game.board.state
    if c.lugar is not None:
        return
    if not puede_afectar(fuente, c):
        st.log.append("   🛡️ {} no se deja teletransportar.".format(nombre_corto(c)))
        return
    destino = max(0, min(destino, LARGO_PISTA - 1))
    c.pos = destino
    st.log.append("   ✨ {} aparece en la casilla {}.".format(nombre_corto(c), destino))


def registrar_llegada(game, c):
    st = game.board.state
    c.pos = LARGO_PISTA
    st.llegadas.append(st.corredores.index(c))
    c.lugar = len(st.llegadas)
    medalla = "🥇" if c.lugar == 1 else "🥈"
    st.log.append("🏁{} ¡{} cruza la meta en el puesto {}!".format(medalla, nombre(game, c), c.lugar))


def mover(game, c, n, fuente=None, prof=0):
    """Mueve `c` n casillas (negativo = hacia atrás). `fuente` es el corredor cuyo
    poder causa el movimiento (None si es la tirada propia o una casilla)."""
    st = game.board.state
    if n == 0 or c.lugar is not None or carrera_terminada(st):
        return
    if fuente is not None and fuente is not c and not puede_afectar(fuente, c):
        st.log.append("   🛡️ {} no se mueve.".format(nombre_corto(c)))
        return

    inicio = c.pos
    destino = max(0, inicio + n)

    adelantados = []
    if n > 0:
        adelantados = [o for o in activos(st) if o is not c and inicio < o.pos < destino]
        adelantados.sort(key=lambda o: o.pos)

    if destino >= LARGO_PISTA:
        if prof == 0:
            st.log.append("   {} avanza {}.".format(nombre_corto(c), n))
        registrar_llegada(game, c)
    else:
        c.pos = destino
        if n > 0:
            st.log.append("   {} avanza {} → casilla {}.".format(nombre_corto(c), n, destino))
        else:
            st.log.append("   {} retrocede {} → casilla {}.".format(nombre_corto(c), -n, destino))

    if adelantados and prof < PROFUNDIDAD_MAXIMA:
        resolver_adelantamientos(game, c, adelantados, prof)

    if c.lugar is None and prof < PROFUNDIDAD_MAXIMA and not carrera_terminada(st):
        resolver_detencion(game, c, prof)


def resolver_adelantamientos(game, c, adelantados, prof):
    st = game.board.state
    if c.rid == "fantasma":
        return
    adelantados = [o for o in adelantados if o.rid != "fantasma"]
    if not adelantados:
        return

    if c.rid == "pavo" and len(adelantados) >= 2:
        jugador = game.playerlist.get(c.uid)
        if jugador:
            jugador.puntos += 1
        st.log.append("   🦚 ¡{} adelanta a {} de una! Su jugador gana 1 punto.".format(
            nombre_corto(c), len(adelantados)))

    for o in adelantados:
        if carrera_terminada(st):
            return
        if c.rid == "dino":
            tropezar(game, o, fuente=c, motivo=" con la cola del Dino")
        if c.rid == "mono" and puede_afectar(c, o):
            st.log.append("   🐒 ¡El Mono le roba a {}!".format(nombre_corto(o)))
            mover(game, o, -1, fuente=c, prof=prof + 1)
            mover(game, c, 1, fuente=c, prof=prof + 1)
        if o.rid == "pulpo" and o.lugar is None:
            st.log.append("   🐙 El Pulpo se pega a {}.".format(nombre_corto(c)))
            mover(game, o, 2, fuente=o, prof=prof + 1)


def resolver_detencion(game, c, prof):
    """Efectos de detenerse en una casilla: primero la casilla, después los poderes."""
    st = game.board.state
    pos = c.pos

    if tipo_pista(st) == "salvaje" and pos in CASILLAS_SALVAJES:
        casilla = CASILLAS_SALVAJES[pos]
        if casilla == "turbo":
            st.log.append("   » ¡Casilla turbo!")
            mover(game, c, 3, prof=prof + 1)
        elif casilla == "remolino":
            st.log.append("   « ¡Un remolino lo arrastra!")
            mover(game, c, -3, prof=prof + 1)
        elif casilla == "pozo":
            tropezar(game, c, motivo=" en un pozo")
        elif casilla == "gema":
            jugador = game.playerlist.get(c.uid)
            if jugador:
                jugador.puntos += 1
            st.log.append("   💎 ¡{} junta una gema! +1 punto para {}.".format(
                nombre_corto(c), jugador.name if jugador else "?"))

    if c.lugar is not None or c.pos != pos or carrera_terminada(st):
        return

    if pos in st.trampas and c.rid != "arana":
        arana = (_hay(st, "arana") or [None])[0]
        st.trampas.remove(pos)
        st.log.append("   🕸️ ¡{} cae en una telaraña!".format(nombre_corto(c)))
        tropezar(game, c, fuente=arana)

    for h in _hay(st, "hongo"):
        if h is not c and h.pos == pos and c.pos == pos and c.lugar is None:
            if puede_afectar(h, c):
                st.log.append("   🍄 ¡Boing! El Hongo hace rebotar a {}.".format(nombre_corto(c)))
                mover(game, c, -2, fuente=h, prof=prof + 1)
            break


# ---------------------------------------------------------------------------
# Preparación de la carrera
# ---------------------------------------------------------------------------

def preparar_carrera(game):
    """Arma la pista con los corredores elegidos y define el orden de turnos."""
    st = game.board.state
    st.corredores = []
    st.trampas = []
    st.llegadas = []
    st.ultima_tirada = None
    st.log = []
    st.turno_idx = 0
    st.pendiente = {}

    inicial = primer_jugador(game)
    secuencia = game.player_sequence
    i0 = secuencia.index(inicial)
    orden_jugadores = secuencia[i0:] + secuencia[:i0]

    for jugador in orden_jugadores:
        for rid in jugador.elegidos:
            c = Corredor(rid, jugador.uid)
            if rid == "oso":
                c.pos = 4
                c.tropezado = True
            st.corredores.append(c)

    # Orden de turnos: ronda por jugador; con 2 corredores por jugador se intercalan.
    por_jugador = [[i for i, c in enumerate(st.corredores) if c.uid == j.uid] for j in orden_jugadores]
    st.orden_turnos = []
    for k in range(max(len(l) for l in por_jugador)):
        for l in por_jugador:
            if k < len(l):
                st.orden_turnos.append(l[k])

    st.ultimo_primer_jugador = inicial.uid


def primer_jugador(game):
    """Carrera 1: el primero de la secuencia. Después: el dueño del corredor que
    terminó más atrás en la carrera anterior."""
    st = game.board.state
    rezagado = getattr(st, "rezagado_uid", None)
    if rezagado is not None and rezagado in game.playerlist:
        return game.playerlist[rezagado]
    return game.player_sequence[0]


# ---------------------------------------------------------------------------
# Turno
# ---------------------------------------------------------------------------

def iniciar_turno(game):
    """Prepara el turno del corredor actual. Devuelve False si el corredor pierde el
    turno (estaba tropezado)."""
    st = game.board.state
    c = corredor_actual(st)
    st.turno_n += 1
    st.pendiente = {
        "inicio_pos": c.pos,
        "ultimo": es_ultimo(st, c),
        "solo_punta": solo_en_punta(st, c),
        "extra_usado": st.pendiente.get("extra_usado", False) if st.pendiente.get("extra_de") == c.rid else False,
        "rerolled": False,
    }
    c.pos_inicio_turno = c.pos
    if c.tropezado:
        c.tropezado = False
        st.log.append("😵 {} se levanta del piso y pierde el turno.".format(nombre(game, c)))
        return False
    return True


def opciones_turno(game):
    """Botones disponibles para el corredor actual: {clave: etiqueta}."""
    st = game.board.state
    c = corredor_actual(st)
    rid = c.rid
    op = {}

    if rid == "robot":
        op["robot"] = "🤖 Avanzar 3"
    elif rid == "zorro":
        op["par"] = "🎲 Apostar PAR"
        op["impar"] = "🎲 Apostar IMPAR"
    elif rid == "ardilla":
        op["tirar"] = "🎲🎲 Tirar dos dados"
    else:
        op["tirar"] = "🎲 Tirar"

    if rid == "canguro":
        op["canguro"] = "🦘 Saltar 4"
    if rid == "torbellino" and _inmediato_adelante(st, c):
        op["torbellino"] = "🌪️ Intercambiar con el de adelante"
    if rid == "bruja" and "bruja" not in c.usados:
        lider = lideres(st, excluir=c)
        if lider and lider[0].pos > c.pos:
            op["bruja"] = "🧙 Traer al líder"
    if rid == "espejo" and st.ultima_tirada:
        op["espejo"] = "🪞 Copiar el {}".format(st.ultima_tirada)
    if rid == "payaso" and "payaso" not in c.usados and objetivos_payaso(st, c):
        op["payaso"] = "🤡 Hacer tropezar a alguien"
    return op


def _inmediato_adelante(st, c):
    adelante = [o for o in activos(st) if o is not c and o.pos > c.pos]
    if not adelante:
        return None
    minimo = min(o.pos for o in adelante)
    return [o for o in adelante if o.pos == minimo][0]


def objetivos_payaso(st, c):
    return [o for o in activos(st) if o is not c and abs(o.pos - c.pos) <= 3 and not o.tropezado]


def usar_payaso(game, objetivo_idx):
    st = game.board.state
    c = corredor_actual(st)
    o = st.corredores[objetivo_idx]
    c.usados.append("payaso")
    st.log.append("⚡ {} le hace una zancadilla a {}.".format(nombre(game, c), nombre(game, o)))
    tropezar(game, o, fuente=c)


def accion_alternativa(game, accion):
    """Acciones que reemplazan la tirada. Devuelve True si el turno ya movió."""
    st = game.board.state
    c = corredor_actual(st)
    if accion == "robot":
        st.log.append("⚡ {} avanza sus 3 casillas de siempre.".format(nombre(game, c)))
        mover(game, c, 3)
    elif accion == "canguro":
        st.log.append("⚡ ¡{} pega un salto de 4!".format(nombre(game, c)))
        mover(game, c, 4)
    elif accion == "torbellino":
        o = _inmediato_adelante(st, c)
        if o is None:
            return False
        if not puede_afectar(c, o):
            st.log.append("⚡ {} intenta un intercambio, pero {} no se deja.".format(nombre(game, c), nombre_corto(o)))
        else:
            st.log.append("⚡ ¡{} intercambia lugar con {}!".format(nombre(game, c), nombre(game, o)))
            c.pos, o.pos = o.pos, c.pos
    elif accion == "bruja":
        lider = lideres(st, excluir=c)
        c.usados.append("bruja")
        if lider:
            st.log.append("⚡ {} lanza un hechizo y arrastra a {} hasta su charco.".format(nombre(game, c), nombre(game, lider[0])))
            teletransportar(game, lider[0], c.pos, fuente=c)
    elif accion == "espejo":
        valor = st.ultima_tirada
        st.log.append("⚡ {} copia la tirada: *{}*.".format(nombre(game, c), valor))
        total = valor + _aura_yeti(game, c)
        mover(game, c, max(0, total))
    else:
        return False
    return True


def opciones_post_tirada(game, dados):
    """Decisiones después de ver el dado. Devuelve {clave: etiqueta} o {} si no hay."""
    st = game.board.state
    c = corredor_actual(st)
    op = {}
    if c.rid == "ardilla" and len(dados) == 2:
        op["d0"] = "Usar el {}".format(dados[0])
        op["d1"] = "Usar el {}".format(dados[1])
        return op
    valor = dados[0]
    if c.rid == "mago" and not st.pendiente.get("rerolled"):
        op["aceptar"] = "✅ Quedarse con el {}".format(valor)
        op["retirar"] = "🎩 Volver a tirar"
    if c.rid == "dinamitero":
        base = calcular_movimiento(game, valor)
        op["normal"] = "Mover {}".format(base)
        op["doble"] = "🧨 Mover {} y explotar".format(base * 2)
    return op


def _aura_yeti(game, c):
    st = game.board.state
    for y in _hay(st, "yeti"):
        if y is not c and abs(y.pos - c.pos) <= 1 and puede_afectar(y, c):
            return -2
    return 0


def calcular_movimiento(game, valor, apuesta=None, explicar=False):
    """Cuántas casillas mueve el corredor actual con el dado `valor`."""
    st = game.board.state
    c = corredor_actual(st)
    rid = c.rid
    notas = []

    base = valor
    picadura = [a for a in _hay(st, "abeja") if a is not c]
    if valor == 6 and picadura and puede_afectar(picadura[0], c):
        base = 3
        notas.append("🐝 ¡la Abeja lo pica! mueve solo 3")

    extra = 0
    if rid == "caracol" and valor <= 3:
        extra += 2
        notas.append("🐌 +2")
    if rid == "liebre":
        if st.pendiente.get("solo_punta"):
            notas.append("🐇 se confía en la punta, sin bonus")
        else:
            extra += 2
            notas.append("🐇 +2")
    if rid == "fenix" and st.pendiente.get("ultimo"):
        extra += 3
        notas.append("🔥 renace desde el fondo: +3")
    if rid == "unicornio":
        if valor >= 5:
            extra += 2
            notas.append("🦄 +2")
        elif valor == 1:
            base, extra = 0, 0
            notas.append("🦄 se queda brillando")
    if rid == "perezoso":
        extra -= 1
        notas.append("🦥 −1")
    if rid == "fantasma" and any(o is not c and o.pos == c.pos for o in activos(st)):
        extra += 1
        notas.append("👻 +1")
    if rid == "zorro" and apuesta in ("par", "impar"):
        acierto = (valor % 2 == 0) == (apuesta == "par")
        if acierto:
            extra += 3
            notas.append("🦊 ¡acertó {}! +3".format(apuesta))
        else:
            extra -= 1
            notas.append("🦊 falló la apuesta, −1")
    yeti = _aura_yeti(game, c)
    if yeti:
        extra += yeti
        notas.append("🧊 el Yeti lo congela, −2")

    total = base + extra
    if rid == "perezoso" and base > 0:
        total = max(1, total)
    total = max(0, total)
    if explicar:
        return total, notas
    return total


def aplicar_tirada(game, valor, apuesta=None, doble=False):
    """Mueve al corredor actual según su dado ya decidido."""
    st = game.board.state
    c = corredor_actual(st)
    total, notas = calcular_movimiento(game, valor, apuesta, explicar=True)
    if doble:
        total *= 2
        notas.append("🧨 ¡doble!")
    detalle = " ({})".format(", ".join(notas)) if notas else ""
    st.log.append("🎲 {} saca *{}*{} → mueve *{}*.".format(nombre(game, c), valor, detalle, total))
    st.ultima_tirada = valor
    st.pendiente["dado_final"] = valor
    mover(game, c, total)

    if doble and c.lugar is None and not carrera_terminada(st):
        st.log.append("   💥 ¡KABOOM! El Dinamitero explota.")
        for o in [o for o in activos(st) if o.pos == c.pos]:
            tropezar(game, o, fuente=c if o is not c else None)


def fin_de_turno(game):
    """Poderes de final de turno. Devuelve True si el corredor juega otro turno."""
    st = game.board.state
    c = corredor_actual(st)
    if carrera_terminada(st):
        return False

    if c.lugar is None:
        if c.rid == "iman":
            adelante = [o for o in activos(st) if o is not c and o.pos > c.pos]
            atras = [o for o in activos(st) if o is not c and o.pos < c.pos]
            if adelante or atras:
                st.log.append("🧲 El Imán atrae a sus vecinos.")
            if adelante:
                m = min(o.pos for o in adelante)
                for o in [o for o in adelante if o.pos == m]:
                    mover(game, o, -1, fuente=c, prof=1)
            if atras:
                m = max(o.pos for o in atras)
                for o in [o for o in atras if o.pos == m]:
                    mover(game, o, 1, fuente=c, prof=1)
        elif c.rid == "rey":
            vecinos = [o for o in activos(st) if o is not c and o.pos == c.pos]
            if vecinos:
                st.log.append("👑 «¡Fuera de mi camino!» grita el Rey.")
                for o in vecinos:
                    mover(game, o, -2, fuente=c, prof=1)
        elif c.rid == "dragon":
            quemados = [o for o in activos(st) if o is not c and c.pos < o.pos <= c.pos + 2]
            if quemados:
                st.log.append("🐉 ¡El Dragoncito escupe fuego!")
                for o in quemados:
                    mover(game, o, -1, fuente=c, prof=1)

    if c.rid == "arana":
        origen = c.pos_inicio_turno
        if origen > 0 and origen != c.pos and origen not in st.trampas:
            st.trampas.append(origen)
            st.log.append("🕸️ La Araña deja una telaraña en la casilla {}.".format(origen))

    if (c.rid == "duende" and c.lugar is None and st.pendiente.get("dado_final") == 6
            and not st.pendiente.get("extra_usado") and not carrera_terminada(st)):
        st.log.append("🍀 ¡Seis! El Duende Suertudo juega otra vez.")
        st.pendiente["extra_usado"] = True
        st.pendiente["extra_de"] = c.rid
        return True
    return False


def avanzar_turno(game):
    """Pasa al próximo corredor que siga en carrera."""
    st = game.board.state
    st.pendiente = {}
    n = len(st.orden_turnos)
    for _ in range(n):
        st.turno_idx = (st.turno_idx + 1) % n
        if corredor_actual(st).lugar is None:
            return


# ---------------------------------------------------------------------------
# Fin de carrera
# ---------------------------------------------------------------------------

def puntuar_carrera(game):
    """Reparte puntos de la carrera y devuelve el texto del resultado."""
    st = game.board.state
    i = st.carrera - 1
    lineas = ["🏁 *Resultado de la carrera {}*".format(st.carrera)]
    for idx in st.llegadas[:PUESTOS_QUE_PUNTUAN]:
        c = st.corredores[idx]
        puntos = PUNTOS_ORO[i] if c.lugar == 1 else PUNTOS_PLATA[i]
        jugador = game.playerlist.get(c.uid)
        if jugador:
            jugador.puntos += puntos
        medalla = "🥇" if c.lugar == 1 else "🥈"
        lineas.append("{} {} → +{} puntos".format(medalla, nombre(game, c), puntos))

    resto = activos(st)
    if resto:
        minimo = min(c.pos for c in resto)
        rezagados = [c for c in resto if c.pos == minimo]
        for c in rezagados:
            if c.rid == "perezoso":
                jugador = game.playerlist.get(c.uid)
                if jugador:
                    jugador.puntos += 2
                lineas.append("🦥 El Perezoso llegó último y su jugador gana 2 puntos.")
        st.rezagado_uid = rezagados[0].uid
    return "\n".join(lineas)


def ganadores(game):
    maximo = max(p.puntos for p in game.player_sequence)
    return [p for p in game.player_sequence if p.puntos == maximo]


# ---------------------------------------------------------------------------
# Dibujo
# ---------------------------------------------------------------------------

def dibujar_pista(game):
    st = game.board.state
    salvaje = tipo_pista(st) == "salvaje"
    fondo = []
    for i in range(LARGO_PISTA):
        if i in st.trampas:
            fondo.append(SIMBOLO_CASILLA["telarana"])
        elif salvaje and i in CASILLAS_SALVAJES:
            fondo.append(SIMBOLO_CASILLA[CASILLAS_SALVAJES[i]])
        else:
            fondo.append("·")

    lineas = []
    orden = sorted(st.corredores, key=lambda c: (c.lugar is None, c.lugar or 0, -c.pos))
    for c in orden:
        emoji = CORREDORES[c.rid]["emoji"]
        jugador = game.playerlist.get(c.uid)
        dueno = jugador.name[:10] if jugador else "?"
        if c.lugar is not None:
            pista = "".join(fondo) + "|" + emoji + ("🥇" if c.lugar == 1 else "🥈")
        else:
            celdas = list(fondo)
            celdas[c.pos] = emoji
            pista = "".join(celdas) + "|🏁"
        marca = " 💫" if c.tropezado else ""
        lineas.append("{} {}{}".format(pista, dueno, marca))
    return "```\n" + "\n".join(lineas) + "\n```"


def texto_tablero(game):
    st = game.board.state
    texto = "🏆 *Gran Premio Arcano* — Carrera {}/{}".format(st.carrera, CANTIDAD_CARRERAS)
    if st.fase_actual == "Carrera" and st.corredores:
        texto += " — {}\n".format(NOMBRE_PISTA[tipo_pista(st)])
        texto += dibujar_pista(game) + "\n"
    else:
        texto += "\nFase: {}\n".format(st.fase_actual)
    texto += "\n*Puntos:* " + " · ".join(
        "{} {}".format(p.name, p.puntos) for p in sorted(game.player_sequence, key=lambda p: -p.puntos))
    return texto


def repartir_al_azar(game, por_jugador):
    ids = list(CORREDORES.keys())
    random.shuffle(ids)
    for p in game.player_sequence:
        p.corredores = [ids.pop() for _ in range(por_jugador)]
