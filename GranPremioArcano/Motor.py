# Motor de reglas de Gran Premio Arcano.
#
# Lógica pura (sin Telegram): mueve corredores, resuelve poderes y escribe el relato
# en st.log. El Controller se encarga de los botones, el dado y los mensajes.
#
# Los poderes se consultan siempre con tiene(st, c, "poder"), que tiene en cuenta al
# Anulador (anula a los de adelante) y al Imitador (copia al que va primero). Un
# corredor puede tener varios poderes (Mutante, Impostor) o uno prestado (Cambiante,
# Heredero, Suplente): por eso Corredor.poderes es una lista.
#
# Los efectos se disparan en momentos fijos:
#   - iniciar_turno / efectos_inicio: comienzo del turno
#   - resolver_tirada: al sacar un número (Gusano, Sirviente, Saboteador, ...)
#   - mover -> resolver_adelantamientos: al sobrepasar a alguien
#   - mover / teletransportar -> resolver_detencion: al terminar en una casilla
#   - fin_de_turno: final del turno

import random

from GranPremioArcano.Boardgamebox.State import Corredor
from GranPremioArcano.Constants.Corredores import (
    CORREDORES, LARGO_PISTA, PISTA_POR_CARRERA, CASILLAS_SALVAJES, simbolo_casilla,
    PUNTOS_ORO, PUNTOS_PLATA, NOMBRE_PISTA, CANTIDAD_CARRERAS, PRIMERA_CURVA, SEGUNDA_CURVA,
    etiqueta,
)

# Corta cadenas de efectos (un poder que mueve, que activa otro poder, que mueve...)
PROFUNDIDAD_MAXIMA = 4
PUESTOS_QUE_PUNTUAN = 2
MAX_REPETICIONES_SEIS = 5

# Poderes que piden una elección antes de la largada (en este orden).
PODERES_PREVIOS = ["cambiante", "heredero", "suplente", "estratega", "alma_gemela"]
# Poderes que no se pueden copiar ni robar.
NO_COPIABLES = {"cambiante", "heredero", "suplente", "extra", "imitador"}
# El Mutante roba en plena carrera: nada que necesite una elección previa.
NO_MUTABLES = NO_COPIABLES | set(PODERES_PREVIOS) | {"nino_rico", "condenado", "jinete", "mutante"}

# Acciones del menú de turno que no son "tirar".
TIPO_ACCION = {
    "tramposo": "objetivo", "intercambiador": "objetivo", "hipnotizador": "objetivo",
    "intruso": "objetivo",
    "seguidor": "previa", "rey_tropiezo": "previa", "leviatan": "previa",
    "animadora": "alternativa", "piernas": "alternativa", "excavador": "alternativa",
}


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


def etiqueta_boton(game, c):
    jugador = game.playerlist.get(c.uid)
    return "{} ({}, casilla {})".format(nombre_corto(c), jugador.name if jugador else "?", c.pos)


def en_carrera(c):
    return c.lugar is None and not c.eliminado


def activos(st):
    return [c for c in st.corredores if en_carrera(c)]


def otros_activos(st, c):
    return [o for o in st.corredores if o is not c and en_carrera(o)]


def indice(st, c):
    for i, o in enumerate(st.corredores):
        if o is c:
            return i
    return None


def carrera_terminada(st):
    return st.cancelada or len(st.llegadas) >= PUESTOS_QUE_PUNTUAN or not activos(st)


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


def _por_orden(st, corredores):
    """Ordena corredores según el orden de turnos (para desempatar)."""
    def clave(o):
        i = indice(st, o)
        return st.orden_turnos.index(i) if i in st.orden_turnos else 99
    return sorted(corredores, key=clave)


def primero_de(st, corredores):
    if not corredores:
        return None
    m = max(o.pos for o in corredores)
    return _por_orden(st, [o for o in corredores if o.pos == m])[0]


def ultimo_de(st, corredores):
    if not corredores:
        return None
    m = min(o.pos for o in corredores)
    return _por_orden(st, [o for o in corredores if o.pos == m])[0]


def jugador_de(game, c):
    return game.playerlist.get(c.uid)


def _vecino(game, uid, paso):
    seq = game.player_sequence
    for i, p in enumerate(seq):
        if p.uid == uid:
            return seq[(i + paso) % len(seq)]
    return None


def jugador_izquierda(game, uid):
    """El que juega después (sentido de las agujas del reloj)."""
    return _vecino(game, uid, 1)


def jugador_derecha(game, uid):
    return _vecino(game, uid, -1)


# ---------------------------------------------------------------------------
# Poderes efectivos
# ---------------------------------------------------------------------------

def anulado(st, c):
    """El Anulador anula a los corredores que estén delante suyo."""
    if not en_carrera(c):
        return False
    return any(o is not c and en_carrera(o) and "anulador" in o.poderes and o.pos < c.pos
               for o in st.corredores)


def imitado(st, c):
    """El corredor que copia el Imitador: el que va primero (sin contarlo a él)."""
    otros = otros_activos(st, c)
    if not otros:
        return None
    lider = primero_de(st, otros)
    if c.pos > lider.pos:
        return None
    return lider


def poderes(st, c):
    if anulado(st, c):
        return []
    ps = list(c.poderes)
    if "imitador" in ps:
        o = imitado(st, c)
        if o is not None and not anulado(st, o):
            ps += [p for p in o.poderes if p != "imitador" and p not in ps]
    return ps


def tiene(st, c, poder):
    return poder in poderes(st, c)


def con_poder(st, poder, excluir=None):
    return [o for o in activos(st) if o is not excluir and tiene(st, o, poder)]


def texto_poderes(c):
    texto = CORREDORES[c.rid]["poder"]
    prestados = [p for p in c.poderes if p != c.rid]
    if prestados:
        texto += " — Ahora usa: " + ", ".join(
            "{} ({})".format(CORREDORES[p]["nombre"], CORREDORES[p]["poder"]) for p in prestados)
    return texto


def poderes_mutados(c):
    """Poderes que el Mutante fue robando en esta carrera (además del propio)."""
    if "mutante" not in c.poderes:
        return []
    return [p for p in c.poderes if p not in (c.rid, "mutante")]


def texto_mutaciones(game):
    """Recordatorio público de los poderes que tiene cada Mutante en carrera ("" si no hay)."""
    st = game.board.state
    if st.fase_actual != "Carrera":
        return ""
    lineas = []
    for c in activos(st):
        extra = poderes_mutados(c)
        if not extra:
            continue
        jugador = game.playerlist.get(c.uid)
        lineas.append("🧬 *{}* ({}) también tiene:\n{}".format(
            CORREDORES[c.rid]["nombre"], jugador.name if jugador else "?",
            "\n".join("   {} {}: {}".format(CORREDORES[p]["emoji"], CORREDORES[p]["nombre"],
                                            CORREDORES[p]["poder"]) for p in extra)))
    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Efectos básicos
# ---------------------------------------------------------------------------

def sumar_puntos(game, c, n):
    jugador = jugador_de(game, c)
    if jugador:
        jugador.puntos = max(0, jugador.puntos + n)
    return jugador


def activo(game, fuente, prof=0):
    """Se activó el poder de `fuente`: el Aprovechado avanza 1."""
    st = game.board.state
    if prof >= PROFUNDIDAD_MAXIMA or carrera_terminada(st):
        return
    for a in con_poder(st, "aprovechado", excluir=fuente):
        if en_carrera(a) and not carrera_terminada(st):
            st.log.append("   🦊 {} se aprovecha y avanza 1.".format(nombre_corto(a)))
            mover(game, a, 1, fuente=a, prof=prof + 1)


def tropezar(game, c, motivo=""):
    st = game.board.state
    if not en_carrera(c) or c.tropezado:
        return False
    c.tropezado = True
    st.log.append("   💫 {} tropieza{}.".format(nombre_corto(c), motivo))
    return True


def eliminar(game, c, motivo=""):
    st = game.board.state
    if not en_carrera(c):
        return
    c.eliminado = True
    st.log.append("   ☠️ {} queda eliminado{}.".format(nombre_corto(c), motivo))
    if st.jabali == indice(st, c):
        st.jabali = None
        st.log.append("   🐗 El jabalí sale corriendo solo.")


def _esquivar_gigante(st, c, destino, sentido):
    """Nadie termina en la casilla del Gigante (salvo la salida): queda en la anterior."""
    for _ in range(LARGO_PISTA):
        if destino <= 0 or destino >= LARGO_PISTA:
            return destino
        if not any(g.pos == destino for g in con_poder(st, "gigante", excluir=c)):
            return destino
        destino -= sentido
    return destino


def teletransportar(game, c, destino, prof=0):
    st = game.board.state
    if not en_carrera(c):
        return
    destino = max(0, min(destino, LARGO_PISTA - 1))
    final = _esquivar_gigante(st, c, destino, 1)
    if final != destino:
        st.log.append("   🗿 El Gigante no le deja lugar.")
    c.pos = final
    c.max_pos = max(c.max_pos, final)
    st.log.append("   ✨ {} aparece en la casilla {}.".format(nombre_corto(c), final))
    if prof < PROFUNDIDAD_MAXIMA and not carrera_terminada(st):
        resolver_detencion(game, c, prof + 1)


def intercambiar(game, a, b):
    st = game.board.state
    a.pos, b.pos = b.pos, a.pos
    a.max_pos = max(a.max_pos, a.pos)
    b.max_pos = max(b.max_pos, b.pos)
    st.log.append("   🔄 {} y {} cambian de lugar.".format(nombre_corto(a), nombre_corto(b)))


def intercambiar_cartas(game, c, o):
    """Intercambiador de Pilotos: cada jugador se queda con el corredor del otro."""
    st = game.board.state
    a, b = jugador_de(game, c), jugador_de(game, o)
    if not a or not b or a is b:
        return
    for lista in ("corredores", "elegidos", "usados"):
        la, lb = getattr(a, lista), getattr(b, lista)
        en_a, en_b = c.rid in la, o.rid in lb
        if en_a:
            la.remove(c.rid)
            lb.append(c.rid)
        if en_b:
            lb.remove(o.rid)
            la.append(o.rid)
    c.uid, o.uid = o.uid, c.uid
    st.log.append("   🔀 ¡Cambio de pilotos! {} ahora es de {} y {} es de {}.".format(
        nombre_corto(c), b.name, nombre_corto(o), a.name))


def registrar_llegada(game, c):
    st = game.board.state
    i = indice(st, c)
    if not st.llegadas:
        impostores = [o for o in con_poder(st, "impostor", excluir=c) if "impostor" not in o.usados]
        if impostores:
            imp = impostores[0]
            imp.usados.append("impostor")
            st.log.append("   🕵️ ¡{} desenmascara a {} en la recta final!".format(nombre_corto(imp), nombre_corto(c)))
            eliminar(game, c, " por el Impostor")
            imp.poderes += [p for p in c.poderes if p not in imp.poderes]
            st.log.append("   🕵️ {} se queda con su poder.".format(nombre_corto(imp)))
            activo(game, imp)
            return
    c.pos = LARGO_PISTA
    c.max_pos = LARGO_PISTA
    st.llegadas.append(i)
    c.lugar = len(st.llegadas)
    medalla = "🥇" if c.lugar == 1 else "🥈"
    st.log.append("🏁{} ¡{} cruza la meta en el puesto {}!".format(medalla, nombre(game, c), c.lugar))

    if c.lugar == 1:
        for e in activos(st):
            if tiene(st, e, "estratega") and e.prediccion == i:
                e.pos = LARGO_PISTA
                e.max_pos = LARGO_PISTA
                st.llegadas.append(indice(st, e))
                e.lugar = 2
                st.log.append("♟️🥈 ¡{} lo había predicho! La carrera termina y queda segundo.".format(nombre(game, e)))
                break


def _destino_saltador(st, c, n):
    """El Saltador no cuenta las casillas ocupadas por otros corredores."""
    ocupadas = {o.pos for o in otros_activos(st, c)}
    pos, restantes = c.pos, n
    while restantes > 0:
        pos += 1
        if pos >= LARGO_PISTA:
            return pos + restantes - 1
        if pos in ocupadas:
            continue
        restantes -= 1
    return pos


def mover(game, c, n, fuente=None, prof=0):
    """Mueve `c` n casillas (negativo = hacia atrás). `fuente` es el corredor cuyo
    poder causa el movimiento (None si es la tirada propia o una casilla)."""
    st = game.board.state
    if n == 0 or not en_carrera(c) or carrera_terminada(st):
        return

    inicio = c.pos
    propio = fuente is None or fuente is c
    if n > 0 and propio and tiene(st, c, "saltador"):
        destino = _destino_saltador(st, c, n)
    else:
        destino = max(0, inicio + n)

    if destino > LARGO_PISTA and con_poder(st, "perfeccionista", excluir=c):
        st.log.append("   📏 {} se pasaría de la meta: el Perfeccionista no lo deja avanzar.".format(nombre_corto(c)))
        return

    if destino < LARGO_PISTA:
        final = _esquivar_gigante(st, c, destino, 1 if destino >= inicio else -1)
        if final != destino:
            st.log.append("   🗿 El Gigante ocupa la casilla {}.".format(destino))
            destino = final
    if destino == inicio:
        st.log.append("   {} no se mueve.".format(nombre_corto(c)))
        return

    adelantados, pegados = [], []
    if destino > inicio:
        adelantados = sorted([o for o in otros_activos(st, c) if inicio < o.pos < destino], key=lambda o: o.pos)
        pegados = [p for p in con_poder(st, "pegado", excluir=c) if p.pos == inicio and inicio > 0]

    if destino >= LARGO_PISTA:
        st.log.append("   {} avanza {}.".format(nombre_corto(c), LARGO_PISTA - inicio))
        registrar_llegada(game, c)
    else:
        c.pos = destino
        c.max_pos = max(c.max_pos, destino)
        if destino > inicio:
            st.log.append("   {} avanza {} → casilla {}.".format(nombre_corto(c), destino - inicio, destino))
        else:
            st.log.append("   {} retrocede {} → casilla {}.".format(nombre_corto(c), inicio - destino, destino))

    if adelantados and prof < PROFUNDIDAD_MAXIMA:
        resolver_adelantamientos(game, c, adelantados, prof)

    if en_carrera(c) and prof < PROFUNDIDAD_MAXIMA and not carrera_terminada(st):
        resolver_detencion(game, c, prof)

    for p in pegados:
        if (en_carrera(p) and en_carrera(c) and c.pos > p.pos and prof < PROFUNDIDAD_MAXIMA
                and not carrera_terminada(st)):
            st.log.append("   🐟 {} se va pegado a {}.".format(nombre_corto(p), nombre_corto(c)))
            teletransportar(game, p, c.pos, prof + 1)
            activo(game, p, prof + 1)


def resolver_adelantamientos(game, c, adelantados, prof):
    st = game.board.state
    caos6 = bool(st.pendiente.get("caotico6")) and c is corredor_actual(st)
    bestia = c.bestia and tiene(st, c, "bestia")
    centauro = tiene(st, c, "centauro")

    if tiene(st, c, "exhibicionista"):
        jugador = sumar_puntos(game, c, len(adelantados))
        st.log.append("   🤩 ¡{} se luce! +{} punto(s) para {}.".format(
            nombre_corto(c), len(adelantados), jugador.name if jugador else "?"))
        activo(game, c, prof)

    for o in adelantados:
        if carrera_terminada(st):
            return
        if not en_carrera(o):
            continue
        if bestia:
            st.log.append("   🐺 ¡La Bestia se devora a {}!".format(nombre_corto(o)))
            eliminar(game, o)
            activo(game, c, prof + 1)
            continue
        if caos6:
            tropezar(game, o, " en el torbellino del Caótico")
        if centauro:
            st.log.append("   🏹 El Centauro patea a {}.".format(nombre_corto(o)))
            mover(game, o, -2, fuente=c, prof=prof + 1)
            activo(game, c, prof + 1)
        if tiene(st, o, "cascara") and en_carrera(c):
            st.log.append("   🍌 {} pisa la Cáscara.".format(nombre_corto(c)))
            tropezar(game, c)
            activo(game, o, prof + 1)
        if tiene(st, o, "pinguino") and not o.tropezado:
            st.log.append("   🐧 El Pingüino se tira de panza.")
            tropezar(game, o)
            activo(game, o, prof + 1)


def desafio(game, retador, otro, prof):
    st = game.board.state
    if not (en_carrera(retador) and en_carrera(otro)) or prof >= PROFUNDIDAD_MAXIMA:
        return
    a, b = random.randint(1, 6), random.randint(1, 6)
    ganador = retador if a >= b else otro
    st.log.append("   🥊 {} desafía a {}: {} contra {}. ¡Gana {}!".format(
        nombre_corto(retador), nombre_corto(otro), a, b, nombre_corto(ganador)))
    mover(game, ganador, 2, fuente=retador, prof=prof + 1)
    activo(game, retador, prof + 1)


def resolver_detencion(game, c, prof):
    """Efectos de terminar en una casilla: primero la casilla, después los poderes."""
    st = game.board.state
    pos = c.pos

    if tipo_pista(st) == "salvaje" and pos in CASILLAS_SALVAJES:
        casilla, valor = CASILLAS_SALVAJES[pos]
        if casilla == "flecha" and valor > 0:
            st.log.append("   ➡️ ¡Flecha! Avanza {}.".format(valor))
            mover(game, c, valor, prof=prof + 1)
        elif casilla == "flecha":
            st.log.append("   ⬅️ ¡Flecha roja! Retrocede {}.".format(-valor))
            mover(game, c, valor, prof=prof + 1)
        elif casilla == "tropiezo":
            tropezar(game, c, " en una casilla trampa")
        elif casilla == "estrella":
            jugador = sumar_puntos(game, c, valor)
            st.log.append("   ⭐ ¡{} atrapa una estrella! +{} punto para {}.".format(
                nombre_corto(c), valor, jugador.name if jugador else "?"))

    if not en_carrera(c) or c.pos != pos or carrera_terminada(st) or pos == 0:
        return
    i = indice(st, c)
    otros = [o for o in otros_activos(st, c) if o.pos == pos]

    if otros:
        for b in [o for o in otros if tiene(st, o, "bruja")]:
            st.log.append("   🧙 La Bruja del Tropiezo le hace una zancadilla a {}.".format(nombre_corto(c)))
            tropezar(game, c)
            activo(game, b, prof + 1)
        if tiene(st, c, "bruja"):
            st.log.append("   🧙 La Bruja del Tropiezo cae entre los demás.")
            for o in otros:
                tropezar(game, o)
            activo(game, c, prof + 1)

        if tiene(st, c, "devorador") and len(otros) == 1 and en_carrera(otros[0]):
            st.log.append("   👹 ¡El Devorador se come a {}!".format(nombre_corto(otros[0])))
            eliminar(game, otros[0])
            activo(game, c, prof + 1)

        if st.jabali is not None and st.jabali != i:
            jinete = st.corredores[st.jabali]
            if en_carrera(jinete) and jinete.pos == pos:
                st.jabali = i
                st.log.append("   🐗 ¡{} le roba el jabalí a {}!".format(nombre_corto(c), nombre_corto(jinete)))

        for cb in [o for o in otros if tiene(st, o, "cobrador") and o.uid != c.uid]:
            pagador = jugador_de(game, c)
            if pagador and pagador.puntos >= 1:
                pagador.puntos -= 1
                cobra = sumar_puntos(game, cb, 1)
                st.log.append("   💰 {} le paga 1 punto a {}.".format(pagador.name, cobra.name if cobra else "?"))
            else:
                st.log.append("   💰 {} no tiene con qué pagarle al Cobrador.".format(nombre_corto(c)))
                tropezar(game, c)
            activo(game, cb, prof + 1)

        for r in [o for o in otros if tiene(st, o, "retador")]:
            if en_carrera(c) and en_carrera(r) and r.pos == c.pos:
                desafio(game, r, c, prof)
        if tiene(st, c, "retador") and en_carrera(c):
            rivales = [o for o in otros_activos(st, c) if o.pos == c.pos]
            if rivales:
                desafio(game, c, rivales[0], prof)

    if en_carrera(c) and c.pos == pos and not carrera_terminada(st) and prof < PROFUNDIDAD_MAXIMA:
        if sum(1 for o in activos(st) if o.pos == pos) == 2:
            for e in con_poder(st, "enamorado"):
                if not carrera_terminada(st):
                    st.log.append("   💘 ¡Qué lindos! {} avanza 2.".format(nombre_corto(e)))
                    mover(game, e, 2, fuente=e, prof=prof + 1)


# ---------------------------------------------------------------------------
# Preparación de la carrera
# ---------------------------------------------------------------------------

def aplicar_inicio(game, c, rid):
    """Poderes que actúan en la largada."""
    st = game.board.state
    if rid == "nino_rico":
        c.pos = c.max_pos = PRIMERA_CURVA
        st.log.append("💎 {} larga directamente en la primera curva.".format(nombre_corto(c)))
    elif rid == "condenado":
        jugador = sumar_puntos(game, c, 4)
        st.log.append("⛓️ {} empieza con 4 fichas de punto para {}.".format(
            nombre_corto(c), jugador.name if jugador else "?"))
    elif rid == "jinete" and st.jabali is None:
        st.jabali = indice(st, c)
        st.log.append("🐗 {} larga montado en su jabalí.".format(nombre_corto(c)))


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
    st.jabali = None
    st.cancelada = False
    st.siguiente_forzado = None
    st.reanudar = None
    st.extra_de = None

    inicial = primer_jugador(game)
    secuencia = game.player_sequence
    i0 = secuencia.index(inicial)
    orden_jugadores = secuencia[i0:] + secuencia[:i0]

    for jugador in orden_jugadores:
        rids = list(jugador.elegidos)
        # El Corredor Extra vuelve a correr en todas las carreras después de la suya.
        rids += [r for r in jugador.usados if r == "extra" and r not in rids]
        for rid in rids:
            st.corredores.append(Corredor(rid, jugador.uid))

    for c in st.corredores:
        aplicar_inicio(game, c, c.rid)

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


def robar_cartas(game, n):
    st = game.board.state
    en_uso = set(r for p in game.player_sequence for r in p.corredores)
    en_uso |= set(c.rid for c in st.corredores)
    mazo = [r for r in CORREDORES if r not in NO_COPIABLES and r not in en_uso]
    return random.sample(mazo, min(n, len(mazo)))


def siguiente_previa(game):
    """Busca el próximo corredor que tiene que elegir algo antes de largar. Si hay,
    deja la elección en st.pendiente y devuelve True."""
    st = game.board.state
    vistos = []
    for i in st.orden_turnos:
        if i in vistos:
            continue
        vistos.append(i)
        c = st.corredores[i]
        if not en_carrera(c):
            continue
        for poder in PODERES_PREVIOS:
            marca = "previo_" + poder
            if poder not in c.poderes or marca in c.usados:
                continue
            st.pendiente = {"objetivo": poder, "actor": c.uid, "sujeto": i}
            if poder == "cambiante":
                st.pendiente["cartas"] = robar_cartas(game, 3)
            if not opciones_objetivo(game):
                c.usados.append(marca)
                st.log.append("{} no tiene a quién elegir.".format(nombre_corto(c)))
                continue
            return True
    st.pendiente = {}
    return False


# ---------------------------------------------------------------------------
# Elecciones (objetivos)
# ---------------------------------------------------------------------------

def sujeto(st):
    i = st.pendiente.get("sujeto")
    return st.corredores[i] if i is not None and i < len(st.corredores) else None


def _casillas_intruso(st, c):
    cuenta = {}
    for o in activos(st):
        cuenta[o.pos] = cuenta.get(o.pos, 0) + 1
    return sorted(p for p, n in cuenta.items() if n == 2 and p != c.pos)


def opciones_objetivo(game):
    st = game.board.state
    p = st.pendiente
    tipo = p.get("objetivo")
    c = sujeto(st)
    if c is None:
        return {}
    otros = {str(j): etiqueta_boton(game, o) for j, o in enumerate(st.corredores)
             if o is not c and en_carrera(o)}
    rivales = {str(j): etiqueta_boton(game, o) for j, o in enumerate(st.corredores)
               if o is not c and en_carrera(o) and o.uid != c.uid}

    if tipo == "cambiante":
        return {r: etiqueta(r) for r in p.get("cartas", [])}
    if tipo == "heredero":
        campeones = []
        for r in st.campeones:
            if r not in campeones and r not in NO_COPIABLES:
                campeones.append(r)
        return {r: etiqueta(r) for r in campeones}
    if tipo == "suplente":
        return {k: v for k, v in rivales.items()
                if any(x not in NO_COPIABLES for x in st.corredores[int(k)].poderes)}
    if tipo == "alma_gemela":
        return rivales or otros
    if tipo in ("estratega", "intercambiador"):
        return otros
    if tipo == "hipnotizador":
        return {k: v for k, v in otros.items() if st.corredores[int(k)].pos != c.pos}
    if tipo == "intruso":
        return {"c{}".format(pos): "Casilla {} ({})".format(pos, " y ".join(
            nombre_corto(o) for o in activos(st) if o.pos == pos)) for pos in _casillas_intruso(st, c)}
    if tipo in ("tramposo", "adivinar"):
        return {str(n): str(n) for n in range(1, 7)}
    return {}


def texto_objetivo(game):
    """(texto, privado) del mensaje que pide la elección."""
    st = game.board.state
    p = st.pendiente
    tipo = p.get("objetivo")
    c = sujeto(st)
    quien = nombre(game, c)
    if tipo == "cambiante":
        return ("🦎 {}: robaste estas 3 cartas. ¿Qué poder usás en esta carrera?\n\n{}".format(
            quien, "\n".join("{} *{}*: {}".format(CORREDORES[r]["emoji"], CORREDORES[r]["nombre"],
                                                  CORREDORES[r]["poder"]) for r in p.get("cartas", []))), False)
    if tipo == "heredero":
        return ("👑 {}: elegí a un campeón de una carrera anterior para heredar su poder.".format(quien), False)
    if tipo == "suplente":
        return ("🔁 {}: ¿a qué corredor rival le copiás el poder?".format(quien), False)
    if tipo == "estratega":
        return ("♟️ {}: ¿quién va a ganar esta carrera?".format(quien), False)
    if tipo == "alma_gemela":
        return ("💞 {}: elegí a tu alma gemela.".format(quien), False)
    if tipo == "intercambiador":
        return ("🔄 {}: ¿con quién cambiás de lugar?".format(quien), False)
    if tipo == "hipnotizador":
        return ("🌀 {}: ¿a quién traés hasta tu casilla?".format(quien), False)
    if tipo == "intruso":
        return ("🥷 {}: ¿en qué casilla te colás?".format(quien), False)
    if tipo == "tramposo":
        return ("🃏 {}: elegí *en secreto* el número que vas a mover.".format(quien), True)
    if tipo == "adivinar":
        adivino = game.playerlist.get(p.get("actor"))
        return ("🃏 {}, ¿qué número eligió el Tramposo? Si acertás, no se mueve.".format(
            adivino.name if adivino else "?"), False)
    return ("Elegí una opción.", False)


def preparar_objetivo(game, accion):
    st = game.board.state
    c = corredor_actual(st)
    st.pendiente.update({"objetivo": accion, "actor": c.uid, "sujeto": indice(st, c)})


def _limpiar_objetivo(st):
    for k in ("objetivo", "actor", "sujeto", "cartas"):
        st.pendiente.pop(k, None)


def _copiar(game, c, propio, nuevos):
    """Reemplaza el poder `propio` de c por los poderes `nuevos`."""
    nuevos = [p for p in nuevos if p not in NO_COPIABLES]
    c.poderes = [p for p in c.poderes if p != propio]
    for p in nuevos:
        if p not in c.poderes:
            c.poderes.append(p)
            aplicar_inicio(game, c, p)


def aplicar_objetivo(game, clave):
    """Aplica la elección. Devuelve qué sigue:
    "previa" (otra elección de largada), "accion" (sigue el mismo turno),
    "objetivo" (otra elección) o "fin" (terminó el turno)."""
    st = game.board.state
    p = st.pendiente
    tipo = p.get("objetivo")
    c = sujeto(st)

    if tipo in PODERES_PREVIOS:
        c.usados.append("previo_" + tipo)
        if tipo == "cambiante":
            st.log.append("🦎 {} se transforma: usa el poder de {}.".format(nombre(game, c), etiqueta(clave)))
            _copiar(game, c, "cambiante", [clave])
        elif tipo == "heredero":
            st.log.append("👑 {} hereda el poder de {}.".format(nombre(game, c), etiqueta(clave)))
            _copiar(game, c, "heredero", [clave])
        elif tipo == "suplente":
            o = st.corredores[int(clave)]
            st.log.append("🔁 {} copia el poder de {}.".format(nombre(game, c), nombre_corto(o)))
            _copiar(game, c, "suplente", list(o.poderes))
        elif tipo == "estratega":
            c.prediccion = int(clave)
            st.log.append("♟️ {} predice que gana {}.".format(
                nombre(game, c), nombre_corto(st.corredores[c.prediccion])))
        elif tipo == "alma_gemela":
            c.alma = int(clave)
            st.log.append("💞 {} elige como alma gemela a {}.".format(
                nombre(game, c), nombre_corto(st.corredores[c.alma])))
        st.pendiente = {}
        return "previa"

    _limpiar_objetivo(st)

    if tipo == "intercambiador":
        o = st.corredores[int(clave)]
        st.log.append("⚡ {} cambia de lugar con {}.".format(nombre(game, c), nombre(game, o)))
        intercambiar(game, c, o)
        activo(game, c)
        return "fin"
    if tipo == "hipnotizador":
        o = st.corredores[int(clave)]
        p.setdefault("previas", []).append("hipnotizador")
        st.log.append("🌀 {} hipnotiza a {}.".format(nombre(game, c), nombre(game, o)))
        teletransportar(game, o, c.pos)
        activo(game, c)
        return "accion"
    if tipo == "intruso":
        p.setdefault("previas", []).append("intruso")
        st.log.append("🥷 {} se cuela.".format(nombre(game, c)))
        teletransportar(game, c, int(clave[1:]))
        activo(game, c)
        return "accion"
    if tipo == "tramposo":
        p["secreto"] = int(clave)
        adivina = jugador_derecha(game, c.uid)
        p.update({"objetivo": "adivinar", "actor": adivina.uid, "sujeto": indice(st, c)})
        st.log.append("🃏 {} ya eligió su número en secreto.".format(nombre(game, c)))
        return "objetivo"
    if tipo == "adivinar":
        secreto = p.pop("secreto", 1)
        if int(clave) == secreto:
            st.log.append("🃏 ¡Adivinaron el {}! El Tramposo no se mueve.".format(secreto))
            return "fin"
        st.log.append("🃏 Dijeron {}, pero era el {}.".format(clave, secreto))
        activo(game, c)
        p["dado"] = secreto
        resolver_tirada(game)
        return "fin"
    return "fin"


# ---------------------------------------------------------------------------
# Turno
# ---------------------------------------------------------------------------

def iniciar_turno(game):
    """Prepara el turno del corredor actual. Devuelve False si el corredor no juega
    (estaba tropezado, quedó eliminado o la carrera terminó)."""
    st = game.board.state
    c = corredor_actual(st)
    st.turno_n += 1
    st.pendiente = {
        "inicio_pos": c.pos,
        "ultimo": es_ultimo(st, c),
        "solo_punta": solo_en_punta(st, c),
        "previas": [],
    }
    if c.tropezado:
        c.tropezado = False
        if tiene(st, c, "pinguino"):
            st.pendiente["pinguino"] = True
            st.log.append("🐧 {} se desliza en el piso: duplica su tirada.".format(nombre(game, c)))
            activo(game, c)
        else:
            st.log.append("😵 {} se levanta del piso y pierde el turno.".format(nombre(game, c)))
            return False
    efectos_inicio(game, c)
    return en_carrera(c) and not carrera_terminada(st)


def efectos_inicio(game, c):
    st = game.board.state
    otros = otros_activos(st, c)

    if tiene(st, c, "demonio") and otros and c.pos >= max(o.pos for o in otros) + 4:
        st.log.append("😈 {} se pasa de rosca.".format(nombre(game, c)))
        eliminar(game, c)
        return

    if tiene(st, c, "cancelador"):
        resto = [o for o in st.corredores if o is not c and not o.eliminado]
        if resto and all(o.pos >= c.pos + 5 for o in resto):
            jugador = sumar_puntos(game, c, 3)
            st.log.append("❌ ¡{} cancela la carrera! +3 puntos para {}.".format(
                nombre(game, c), jugador.name if jugador else "?"))
            st.cancelada = True
            return

    if tiene(st, c, "estrella") and otros:
        o = primero_de(st, otros) if st.pendiente.get("ultimo") else ultimo_de(st, otros)
        if o.pos != c.pos:
            st.log.append("⭐ ¡{} roba cámara!".format(nombre(game, c)))
            intercambiar(game, c, o)
            activo(game, c)

    if tiene(st, c, "alma_gemela") and c.alma is not None:
        o = st.corredores[c.alma]
        if en_carrera(o) and o.pos != c.pos and abs(o.pos - c.pos) <= 5:
            st.log.append("💞 {} corre a los brazos de {}.".format(nombre(game, c), nombre_corto(o)))
            teletransportar(game, c, o.pos)
            activo(game, c)

    otros = otros_activos(st, c)
    if tiene(st, c, "desafortunado") and otros and c.pos < min(o.pos for o in otros):
        jugador = sumar_puntos(game, c, 1)
        st.log.append("😩 {} va solo en el fondo: +1 punto para {}.".format(
            nombre(game, c), jugador.name if jugador else "?"))
        activo(game, c)

    if tiene(st, c, "iman") and otros:
        st.log.append("🧲 {} atrae a la multitud.".format(nombre(game, c)))
        for o in otros:
            if carrera_terminada(st) or not en_carrera(c):
                break
            if not en_carrera(o):
                continue
            if o.pos > c.pos:
                mover(game, o, -1, fuente=c, prof=1)
            elif o.pos < c.pos:
                mover(game, o, 1, fuente=c, prof=1)
        activo(game, c)


def _lider_para_rey(st, c):
    otros = otros_activos(st, c)
    lider = primero_de(st, otros)
    if lider is None or lider.pos < c.pos or lider.tropezado:
        return None
    return lider


def _destino_seguidor(st, c):
    adelante = [o for o in otros_activos(st, c) if o.pos > c.pos]
    if not adelante:
        return None
    destino = min(o.pos for o in adelante) - 1
    return destino if destino > c.pos else None


def opciones_turno(game):
    """Botones disponibles para el corredor actual: {clave: etiqueta}."""
    st = game.board.state
    c = corredor_actual(st)
    previas = st.pendiente.get("previas", [])
    otros = otros_activos(st, c)
    op = {}

    if tiene(st, c, "tramposo"):
        op["tramposo"] = "🃏 Elegir número en secreto"
    elif tiene(st, c, "adivino"):
        for n in range(1, 7):
            op["adiv{}".format(n)] = "🔮 Predigo {}".format(n)
    elif tiene(st, c, "maestro"):
        op["tirar"] = "🎲 Tirar los 6 dados"
    else:
        op["tirar"] = "🎲 Tirar"

    if tiene(st, c, "animadora") and otros:
        op["animadora"] = "📣 Animar a los últimos"
    if tiene(st, c, "intercambiador") and otros:
        op["intercambiador"] = "🔄 Cambiar de lugar"
    if tiene(st, c, "piernas"):
        op["piernas"] = "🦵 Avanzar 5"
    if tiene(st, c, "excavador") and not any(abs(o.pos - c.pos) <= 1 for o in otros):
        op["excavador"] = "⛏️ Avanzar 6"
    if "hipnotizador" not in previas and tiene(st, c, "hipnotizador") and any(o.pos != c.pos for o in otros):
        op["hipnotizador"] = "🌀 Hipnotizar"
    if "intruso" not in previas and tiene(st, c, "intruso") and _casillas_intruso(st, c):
        op["intruso"] = "🥷 Colarse"
    if "seguidor" not in previas and tiene(st, c, "seguidor") and _destino_seguidor(st, c) is not None:
        op["seguidor"] = "👣 Seguir al de adelante"
    if "rey_tropiezo" not in previas and tiene(st, c, "rey_tropiezo") and _lider_para_rey(st, c):
        op["rey_tropiezo"] = "🤴 Hacer tropezar al primero"
    if tiene(st, c, "leviatan") and "leviatan" not in c.usados and otros:
        op["leviatan"] = "🐋 Traer a todos"
    return op


def tipo_accion(accion):
    if accion == "tirar" or accion.startswith("adiv"):
        return "tirada"
    return TIPO_ACCION.get(accion)


def accion_previa(game, accion):
    """Poderes de "antes de moverse" que no gastan la tirada."""
    st = game.board.state
    c = corredor_actual(st)
    st.pendiente.setdefault("previas", []).append(accion)
    if accion == "seguidor":
        destino = _destino_seguidor(st, c)
        if destino is not None:
            st.log.append("👣 {} se pone detrás del de adelante.".format(nombre(game, c)))
            teletransportar(game, c, destino)
            activo(game, c)
    elif accion == "rey_tropiezo":
        o = _lider_para_rey(st, c)
        if o is not None:
            st.log.append("🤴 {} hace tropezar a {}.".format(nombre(game, c), nombre(game, o)))
            tropezar(game, o)
            activo(game, c)
    elif accion == "leviatan":
        c.usados.append("leviatan")
        st.log.append("🐋 ¡{} emerge y arrastra a todos a su casilla!".format(nombre(game, c)))
        for o in otros_activos(st, c):
            teletransportar(game, o, c.pos, prof=1)
            tropezar(game, o)
        activo(game, c)


def accion_alternativa(game, accion):
    """Acciones que reemplazan la tirada."""
    st = game.board.state
    c = corredor_actual(st)
    if accion == "animadora":
        st.log.append("📣 ¡{} alienta a los de atrás!".format(nombre(game, c)))
        otros = otros_activos(st, c)
        if otros:
            m = min(o.pos for o in otros)
            for o in [o for o in otros if o.pos == m]:
                mover(game, o, 2, fuente=c, prof=1)
        activo(game, c)
        mover(game, c, 1)
    elif accion == "piernas":
        st.log.append("🦵 {} avanza 5 sin tirar.".format(nombre(game, c)))
        activo(game, c)
        mover(game, c, 5)
    elif accion == "excavador":
        st.log.append("⛏️ {} cava un túnel de 6 casillas.".format(nombre(game, c)))
        activo(game, c)
        mover(game, c, 6)


# ---------------------------------------------------------------------------
# Dados
# ---------------------------------------------------------------------------

def hay_aguafiestas(st):
    return bool(con_poder(st, "aguafiestas"))


def repetir_seis(game):
    """Un 6 que hay que repetir por el Aguafiestas."""
    st = game.board.state
    st.log.append("🌧️ ¡Un 6! El Aguafiestas obliga a repetirlo.")
    for a in con_poder(st, "aguafiestas"):
        mover(game, a, 1, fuente=a, prof=1)
        activo(game, a, 1)


def ajustar_dado(game, valor):
    """El Paralizador deja en 1 la tirada de los que estén a 1 casilla de él."""
    st = game.board.state
    c = corredor_actual(st)
    paralizadores = [o for o in con_poder(st, "paralizador", excluir=c) if abs(o.pos - c.pos) <= 1]
    if paralizadores and valor != 1:
        st.log.append("⚡ El Paralizador congela a {}: su {} vale 1.".format(nombre_corto(c), valor))
        activo(game, paralizadores[0])
        return 1
    return valor


def critico_fuerza(game):
    """El Crítico obliga a repetir (una vez por turno) a los que van delante suyo."""
    st = game.board.state
    c = corredor_actual(st)
    p = st.pendiente
    dado = p.get("dado")
    if p.get("critico") or dado is None or dado < 4:
        return False
    criticos = [o for o in con_poder(st, "critico", excluir=c) if o.pos < c.pos]
    if not criticos:
        return False
    p["critico"] = True
    st.log.append("🧐 El Crítico no está convencido: {} tiene que repetir su {}.".format(nombre_corto(c), dado))
    activo(game, criticos[0])
    return True


def tirar_seis(game):
    """El Maestro de los Dados tira 6 dados (hasta que algún número se repita)."""
    st = game.board.state
    c = corredor_actual(st)
    dados = []
    for _ in range(20):
        dados = [random.randint(1, 6) for _ in range(6)]
        for _ in range(MAX_REPETICIONES_SEIS):
            if 6 not in dados or not hay_aguafiestas(st):
                break
            for k, v in enumerate(dados):
                if v == 6:
                    repetir_seis(game)
                    dados[k] = random.randint(1, 6)
        if any(dados.count(v) > 1 for v in dados):
            break
    st.pendiente["dados6"] = dados
    st.pendiente["dado"] = None
    st.log.append("🎲 {} tira los 6 dados: {}.".format(nombre_corto(c), " ".join(str(d) for d in dados)))
    activo(game, c)


def elegir_maestro(game, valor):
    st = game.board.state
    st.pendiente["dado"] = ajustar_dado(game, valor)


def opciones_post_tirada(game):
    """Decisiones después de ver el dado. Devuelve {clave: etiqueta} o {} si no hay."""
    st = game.board.state
    c = corredor_actual(st)
    p = st.pendiente
    if p.get("dados6") and p.get("dado") is None:
        repetidos = sorted({v for v in p["dados6"] if p["dados6"].count(v) > 1})
        return {"m{}".format(v): "Usar el {}".format(v) for v in repetidos}
    dado = p.get("dado")
    if dado is None:
        return {}
    previos = p.get("previos", [])
    op = {}
    if tiene(st, c, "presumido"):
        op["ok"] = "✅ Plantarse (suma {})".format(sum(previos) + dado)
        op["seguir"] = "🦚 Seguir tirando"
    else:
        op["ok"] = "✅ Quedarse con el {}".format(dado)
    if not previos:
        if con_poder(st, "apostador") and not p.get("apostador"):
            op["rep_apostador"] = "🎰 Repetir (Apostador)"
        if tiene(st, c, "ilusionista") and p.get("ilusionista", 0) < 2:
            op["rep_ilusionista"] = "🎩 Repetir ({} de 2)".format(p.get("ilusionista", 0) + 1)
    if tiene(st, c, "cohete") and not tiene(st, c, "caotico"):
        op["cohete"] = "🚀 Duplicar a {} y tropezar".format(dado * 2)
    if list(op) == ["ok"]:
        return {}
    return op


def registrar_repeticion(game, opcion):
    st = game.board.state
    c = corredor_actual(st)
    p = st.pendiente
    if opcion == "rep_apostador":
        p["apostador"] = True
        st.log.append("🎰 {} repite la tirada.".format(nombre_corto(c)))
        for a in con_poder(st, "apostador", excluir=c):
            st.log.append("   🎰 El Apostador cobra la apuesta: avanza 1.")
            mover(game, a, 1, fuente=a, prof=1)
            activo(game, a, 1)
    elif opcion == "rep_ilusionista":
        p["ilusionista"] = p.get("ilusionista", 0) + 1
        st.log.append("🎩 {} hace desaparecer su {} y vuelve a tirar.".format(nombre_corto(c), p.get("dado")))
        activo(game, c)


def presumido_sigue(game, nuevo):
    """El Presumido tiró otra vez. Devuelve False si se quedó sin moverse."""
    st = game.board.state
    p = st.pendiente
    anterior = p["dado"]
    p.setdefault("previos", []).append(anterior)
    p["dado"] = nuevo
    if nuevo <= anterior:
        p["fallo"] = True
        st.log.append("🦚 ¡Un {} después de un {}! El Presumido se queda en el molde.".format(nuevo, anterior))
        return False
    st.log.append("🦚 El Presumido saca {} y ya suma {}.".format(nuevo, sum(p["previos"]) + nuevo))
    return True


def calcular_movimiento(game, base, explicar=False):
    """Cuántas casillas mueve el corredor actual con una tirada de `base`."""
    st = game.board.state
    c = corredor_actual(st)
    p = st.pendiente
    i = indice(st, c)
    notas = []
    total = base

    def fin(t):
        return (t, notas) if explicar else t

    if tiene(st, c, "transmutador") and base in (1, 2):
        total = 4
        notas.append("⚗️ se transmuta en 4")
    if tiene(st, c, "liebre"):
        if p.get("solo_punta"):
            notas.append("🐇 se duerme sola en la punta")
            return fin(0)
        total += 2
        notas.append("🐇 +2")
    if tiene(st, c, "dirigible"):
        if p.get("inicio_pos", c.pos) < SEGUNDA_CURVA:
            total += 3
            notas.append("🎈 +3")
        else:
            total -= 1
            notas.append("🎈 −1")
    entrenadores = [e for e in con_poder(st, "entrenador") if e.pos == c.pos]
    if entrenadores:
        total += len(entrenadores)
        notas.append("📋 +{}".format(len(entrenadores)))
    pegajosos = con_poder(st, "pegajoso", excluir=c)
    if pegajosos:
        total -= len(pegajosos)
        notas.append("🍯 −{}".format(len(pegajosos)))
    if st.jabali == i:
        total += 2
        notas.append("🐗 +2")
    if tiene(st, c, "iman"):
        n = sum(1 for o in otros_activos(st, c) if o.pos == c.pos)
        if n:
            total += n
            notas.append("🧲 +{}".format(n))
    if tiene(st, c, "baboso"):
        total -= 1
        notas.append("🐌 −1")
    if tiene(st, c, "icaro"):
        total += 3
        notas.append("🪶 +3")
    anuladores = [o for o in otros_activos(st, c) if "anulador" in o.poderes and o.pos < c.pos]
    if anuladores:
        total -= len(anuladores)
        notas.append("🚫 −{}".format(len(anuladores)))
    if tiene(st, c, "adelantador"):
        n = sum(1 for o in otros_activos(st, c) if o.pos > c.pos)
        if n:
            total += n
            notas.append("🏎️ +{}".format(n))
    for pd in con_poder(st, "padrastro", excluir=c):
        izquierda = jugador_izquierda(game, pd.uid)
        if pd.uid != c.uid and izquierda is not None and izquierda.uid == c.uid:
            total += 2
            notas.append("🧔 +2")
    if tiene(st, c, "demonio"):
        jugador = jugador_de(game, c)
        if jugador and jugador.puntos:
            total += jugador.puntos
            notas.append("😈 +{}".format(jugador.puntos))
    if p.get("pinguino"):
        total *= 2
        notas.append("🐧 ×2")
    if tiene(st, c, "perro"):
        if p.get("ultimo"):
            total *= 3
            notas.append("🐶 ×3")
        else:
            notas.append("🐶 corre para atrás")
            return fin(-max(0, total))
    return fin(max(0, total))


def resolver_caotico(game, c, valor):
    st = game.board.state
    otros = otros_activos(st, c)
    activo(game, c)
    if valor == 1:
        st.log.append("🌪️ 1: ¡avanza 7!")
        mover(game, c, 7)
    elif valor == 2:
        o = ultimo_de(st, otros)
        st.log.append("🌪️ 2: el último aparece a su lado.")
        if o is not None:
            teletransportar(game, o, c.pos, prof=1)
    elif valor == 3:
        o = primero_de(st, otros)
        st.log.append("🌪️ 3: aparece junto a otro y lo hace tropezar.")
        if o is not None:
            teletransportar(game, c, o.pos)
            tropezar(game, o)
    elif valor == 4:
        st.log.append("🌪️ 4: avanza 4 y juega otra vez.")
        mover(game, c, 4)
        st.pendiente["extra"] = True
    elif valor == 5:
        o = primero_de(st, otros)
        st.log.append("🌪️ 5: el primero retrocede 5.")
        if o is not None:
            mover(game, o, -5, fuente=c, prof=1)
    else:
        st.log.append("🌪️ 6: avanza 6 y voltea a todos los que pasa.")
        st.pendiente["caotico6"] = True
        mover(game, c, 6)
        st.pendiente.pop("caotico6", None)


def resolver_tirada(game, doble=False):
    """Mueve al corredor actual según su dado ya decidido (st.pendiente["dado"])."""
    st = game.board.state
    c = corredor_actual(st)
    p = st.pendiente
    dado = p["dado"]
    previos = p.get("previos", [])
    valor = previos[0] if previos else dado
    base = sum(previos) + dado
    st.ultima_tirada = valor

    if p.get("fallo"):
        st.log.append("🎲 {} no se mueve.".format(nombre(game, c)))
        return
    if previos:
        st.log.append("🎲 {} suma *{}* en sus tiradas.".format(nombre(game, c), base))
    else:
        st.log.append("🎲 {} saca *{}*.".format(nombre(game, c), valor))

    if tiene(st, c, "caotico"):
        resolver_caotico(game, c, valor)
        return
    if tiene(st, c, "icaro") and valor == 6:
        st.log.append("🪶 ¡Voló demasiado cerca del sol!")
        eliminar(game, c)
        activo(game, c)
        return
    if tiene(st, c, "condenado") and valor == 6:
        jugador = sumar_puntos(game, c, -1)
        st.log.append("⛓️ ¡Condena! Vuelve a la salida y {} pierde 1 punto.".format(jugador.name if jugador else "?"))
        teletransportar(game, c, 0)
        activo(game, c)
        return
    if tiene(st, c, "bestia") and valor in (1, 2) and not c.bestia:
        c.bestia = True
        st.log.append("🐺 ¡{} se transforma en bestia!".format(nombre_corto(c)))
        activo(game, c)
    if tiene(st, c, "mutante") and valor in (1, 2):
        mazo = [r for r in CORREDORES if r not in NO_MUTABLES and r not in c.poderes]
        if mazo:
            nuevo = random.choice(mazo)
            c.poderes.append(nuevo)
            st.log.append("🧬 ¡{} muta! Ahora también tiene el poder de {}.".format(nombre_corto(c), etiqueta(nuevo)))
            activo(game, c)

    bloqueado = False
    if valor == 1:
        gusanos = con_poder(st, "gusano", excluir=c)
        if gusanos:
            bloqueado = True
            st.log.append("   🐛 El Gusano se le enrosca: no puede moverse.")
            for g in gusanos:
                mover(game, g, 1, fuente=g, prof=1)
                activo(game, g, 1)
        marineros = con_poder(st, "marinero", excluir=c)
        if marineros:
            st.siguiente_forzado = indice(st, marineros[0])
            st.log.append("   ⚓ ¡Un 1! {} se cuela: juega a continuación.".format(nombre_corto(marineros[0])))
            activo(game, marineros[0], 1)
    if valor == 6:
        for s in con_poder(st, "sirviente", excluir=c):
            st.log.append("   🤵 El Sirviente se adelanta 2 para abrirle paso.")
            mover(game, s, 2, fuente=s, prof=1)
            activo(game, s, 1)
    saboteadores = con_poder(st, "saboteador", excluir=c) if valor == 3 else []
    for r in con_poder(st, "rival", excluir=c):
        tiro = random.randint(1, 6)
        if tiro == valor:
            st.log.append("   😤 El Rival también saca {}: avanza {}.".format(tiro, valor))
            mover(game, r, valor, fuente=r, prof=1)
            activo(game, r, 1)
    if p.get("prediccion") is not None and tiene(st, c, "adivino"):
        if p["prediccion"] == valor:
            p["extra"] = True
            st.log.append("   🔮 ¡Lo había predicho! Juega otro turno.")
            activo(game, c)
        else:
            st.log.append("   🔮 Había predicho un {}.".format(p["prediccion"]))

    if not en_carrera(c) or carrera_terminada(st):
        return
    if doble:
        base *= 2
    total, notas = calcular_movimiento(game, base, explicar=True)
    if doble:
        notas.insert(0, "🚀 dado duplicado")
    if bloqueado:
        total, notas = 0, []
    elif saboteadores:
        total, notas = -3, ["💣 el Saboteador lo hace retroceder"]
        activo(game, saboteadores[0])
    detalle = " ({})".format(", ".join(notas)) if notas else ""
    st.log.append("   → mueve *{}*{}.".format(total, detalle))
    mover(game, c, total)
    if doble and en_carrera(c):
        st.log.append("   🚀 El Cohete aterriza de cabeza.")
        tropezar(game, c)


def fin_de_turno(game):
    """Poderes de final de turno. Devuelve True si el corredor juega otro turno."""
    st = game.board.state
    c = corredor_actual(st)
    p = st.pendiente
    i = indice(st, c)
    if carrera_terminada(st):
        return False
    extra = False

    if en_carrera(c):
        if tiene(st, c, "manguera"):
            d = random.randint(1, 6)
            mojados = [o for o in otros_activos(st, c) if c.pos < o.pos <= c.pos + d]
            st.log.append("🚿 La Manguera tira {} y moja a {}.".format(
                d, ", ".join(nombre_corto(o) for o in mojados) if mojados else "nadie"))
            for o in mojados:
                tropezar(game, o)
            if mojados:
                activo(game, c)
        if tiene(st, c, "piloto"):
            candidatos = [o for o in otros_activos(st, c)
                          if o.uid != c.uid and 0 < o.pos - c.pos <= 1]
            if candidatos:
                intercambiar_cartas(game, c, primero_de(st, candidatos))
                activo(game, c)
        if tiene(st, c, "reboteador") and any(o.pos == c.pos + 1 for o in otros_activos(st, c)):
            extra = True
            st.log.append("🏀 {} rebota contra el de adelante: turno adicional.".format(nombre_corto(c)))
            activo(game, c)

    if en_carrera(c) and not carrera_terminada(st) and abs(c.pos - p.get("inicio_pos", c.pos)) <= 1:
        for b in con_poder(st, "burlon", excluir=c):
            st.log.append("😜 {} se burla de {} y avanza 2.".format(nombre_corto(b), nombre_corto(c)))
            mover(game, b, 2, fuente=b, prof=1)
            activo(game, b, 1)

    if p.get("extra"):
        extra = True
    if extra and en_carrera(c) and not carrera_terminada(st):
        if st.extra_de == i:
            st.log.append("(ya jugó un turno extra seguido: no encadena otro)")
            return False
        st.extra_de = i
        return True
    return False


def _siguiente_natural(st):
    n = len(st.orden_turnos)
    for k in range(1, n + 1):
        j = (st.turno_idx + k) % n
        if en_carrera(st.corredores[st.orden_turnos[j]]):
            return j
    return None


def avanzar_turno(game):
    """Pasa al próximo corredor que siga en carrera (respetando al Marinero)."""
    st = game.board.state
    st.pendiente = {}
    st.extra_de = None
    forzado = st.siguiente_forzado
    st.siguiente_forzado = None
    if st.reanudar is not None:
        st.turno_idx = st.reanudar
        st.reanudar = None
    natural = _siguiente_natural(st)
    if (forzado is not None and natural is not None and forzado in st.orden_turnos
            and en_carrera(st.corredores[forzado]) and st.orden_turnos[natural] != forzado
            and st.orden_turnos[st.turno_idx] != forzado):
        st.reanudar = st.turno_idx
        st.turno_idx = st.orden_turnos.index(forzado)
        return
    if natural is not None:
        st.turno_idx = natural


# ---------------------------------------------------------------------------
# Fin de carrera
# ---------------------------------------------------------------------------

def puntuar_carrera(game):
    """Reparte puntos de la carrera y devuelve el texto del resultado."""
    st = game.board.state
    i = st.carrera - 1
    lineas = ["🏁 *Resultado de la carrera {}*".format(st.carrera)]
    if st.cancelada:
        lineas.append("❌ La carrera fue cancelada: no hay medallas.")
    else:
        for idx in st.llegadas[:PUESTOS_QUE_PUNTUAN]:
            c = st.corredores[idx]
            puntos = PUNTOS_ORO[i] if c.lugar == 1 else PUNTOS_PLATA[i]
            sumar_puntos(game, c, puntos)
            medalla = "🥇" if c.lugar == 1 else "🥈"
            lineas.append("{} {} → +{} puntos".format(medalla, nombre(game, c), puntos))
            if c.lugar == 1:
                st.campeones.append(c.rid)
                for pd in st.corredores:
                    izquierda = jugador_izquierda(game, pd.uid)
                    if (not pd.eliminado and "padrastro" in pd.poderes and pd.uid != c.uid
                            and izquierda is not None and izquierda.uid == c.uid):
                        jugador = sumar_puntos(game, pd, 3)
                        lineas.append("🧔 El Padrastro festeja: +3 puntos para {}.".format(
                            jugador.name if jugador else "?"))

    for b in st.corredores:
        if (not b.eliminado and b.lugar is None and "baboso" in b.poderes
                and b.max_pos <= SEGUNDA_CURVA):
            jugador = sumar_puntos(game, b, 3)
            lineas.append("🐌 El Baboso ni pasó la segunda curva: +3 puntos para {}.".format(
                jugador.name if jugador else "?"))

    eliminados = [c for c in st.corredores if c.eliminado]
    if eliminados:
        lineas.append("☠️ Eliminados: " + ", ".join(nombre_corto(c) for c in eliminados))

    resto = activos(st)
    if resto:
        minimo = min(c.pos for c in resto)
        st.rezagado_uid = [c for c in resto if c.pos == minimo][0].uid
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
        if salvaje and i in CASILLAS_SALVAJES:
            fondo.append(simbolo_casilla(*CASILLAS_SALVAJES[i]))
        elif i in (PRIMERA_CURVA, SEGUNDA_CURVA):
            fondo.append(":")
        else:
            fondo.append("·")

    lineas = []
    orden = sorted(st.corredores, key=lambda c: (c.eliminado, c.lugar is None, c.lugar or 0, -c.pos))
    for c in orden:
        emoji = CORREDORES[c.rid]["emoji"]
        jugador = game.playerlist.get(c.uid)
        dueno = jugador.name[:10] if jugador else "?"
        if c.eliminado:
            pista = "".join(fondo) + "|☠️"
        elif c.lugar is not None:
            pista = "".join(fondo) + "|" + emoji + ("🥇" if c.lugar == 1 else "🥈")
        else:
            celdas = list(fondo)
            celdas[c.pos] = emoji
            pista = "".join(celdas) + "|🏁"
        marca = " 💫" if c.tropezado and en_carrera(c) else ""
        if st.jabali == indice(st, c):
            marca += " 🐗"
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
    mutaciones = texto_mutaciones(game)
    if mutaciones:
        texto += "\n" + mutaciones + "\n"
    texto += "\n*Puntos:* " + " · ".join(
        "{} {}".format(p.name, p.puntos) for p in sorted(game.player_sequence, key=lambda p: -p.puntos))
    return texto


def repartir_al_azar(game, por_jugador):
    ids = list(CORREDORES.keys())
    random.shuffle(ids)
    for p in game.player_sequence:
        p.corredores = [ids.pop() for _ in range(por_jugador)]
