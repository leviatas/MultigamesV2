# Bichos, cartas de carrera, boletos de apuesta y apuestas especiales de Carrera de Bichos.
#
# Las cartas se guardan como strings "TIPO:bicho:valor" para que se serialicen sin
# problemas con jsonpickle.

BICHOS = {
    "gallina": {"emoji": "🐔", "nombre": "Gallina Turbo"},
    "chancho": {"emoji": "🐷", "nombre": "Chancho Rayo"},
    "sapo":    {"emoji": "🐸", "nombre": "Sapo Saltarín"},
    "pato":    {"emoji": "🦆", "nombre": "Pato Bólido"},
}
ORDEN_BICHOS = ["gallina", "chancho", "sapo", "pato"]

# Se larga en 0 y se cruza la meta al llegar a LARGO_PISTA.
LARGO_PISTA = 15

CANTIDAD_CARRERAS = 3
DINERO_INICIAL = 10
# Cartas que se queman (boca abajo) antes de largar y después de cada mezcla.
CARTAS_QUEMADAS = 3
# Cartas al azar que se agregan al mazo base, además de las fijas.
CARTAS_AL_AZAR = 12
# Si el mazo se mezcla más veces que esto, la carrera termina por posiciones.
MAX_MEZCLAS = 3
MANO_INICIAL = 3
# Movimientos que dura el mareo.
TURNOS_MAREO = 2
# La carrera termina cuando cruzan la meta los que definen las apuestas (1° y 2°);
# el resto se ordena por posición.
LLEGADAS_PARA_TERMINAR = 2

# Segundos entre cuadro y cuadro de la transmisión en vivo. Telegram limita a ~20
# mensajes/ediciones por minuto en un grupo: menos de 3 s termina en rate limit.
PAUSA_CARTA = 3.0

# Cartas por bicho en la biblioteca (de donde salen el mazo al azar y las manos).
CARTAS_POR_BICHO = [
    ("MOV", 1, 2), ("MOV", 2, 3), ("MOV", 3, 3), ("MOV", 4, 2), ("MOV", 5, 1),
    ("MOV", -1, 2), ("MOV", -2, 1),
    ("MAREO", 0, 2), ("CAFE", 0, 1), ("CHOQUE", 0, 1), ("PETARDO", 0, 1),
    ("SIESTA", 0, 1), ("CAMBIO", 0, 1),
]
CARTAS_GLOBALES = [("VIENTO", 1, 2), ("VIENTO", -1, 2), ("ESTAMPIDA", 0, 1), ("REVANCHA", 0, 2)]
# Cartas fijas de cada bicho en todas las carreras.
CARTAS_FIJAS_POR_BICHO = [("MOV", 2), ("MOV", 3)]

# Boletos: cuánto pagan, del primero que se toma al último.
PAGOS_GANADOR = [7, 5, 4, 3]
PAGOS_PODIO = [4, 3, 2, 2]  # el bicho termina 1° o 2°
# Apuesta fuerte: si gana cobra el doble, si pierde paga esto.
MULTA_FUERTE = 3
# En la última carrera todo se paga (y se cobra) doble.
MULTIPLICADOR_FINAL = 2

# Umbrales de las apuestas especiales.
UMBRAL_CARTAS_LARGA = 30
UMBRAL_PALIZA = 8
UMBRAL_FOTO = 2
CARTA_REMONTADA = 10

# Apuesta especial de cada carrera: (pregunta, pagos SÍ, pagos NO).
# Pagos calibrados con simulaciones (4000 carreras): entre paréntesis la chance de SÍ.
APUESTAS_ESPECIALES = {
    # (~32%)
    "desmayo":   ("¿Algún bicho se desmaya (lo marean estando mareado)?", [5, 4, 3], [2, 2, 1]),
    # (~49%)
    "cambiazo":  ("¿Sale alguna carta de Cambiazo durante la carrera?", [3, 3, 2], [3, 3, 2]),
    # (~52%)
    "larga":     ("¿La carrera dura más de {} cartas?".format(UMBRAL_CARTAS_LARGA), [3, 3, 2], [3, 3, 2]),
    # (~14%)
    "mareado":   ("¿Algún bicho cruza la meta estando mareado?", [8, 6, 5], [1, 1, 1]),
    # (~17%)
    "foto":      ("¿Foto final: 1° y 2° cruzan con {} cartas o menos de diferencia?".format(UMBRAL_FOTO), [7, 6, 5], [2, 1, 1]),
    # (~49%)
    "paliza":    ("¿Al terminar, el último queda a {} casillas o más de la meta?".format(UMBRAL_PALIZA), [3, 3, 2], [3, 3, 2]),
    # (~24%)
    "remontada": ("¿Gana un bicho que estuvo último solo después de la carta {}?".format(CARTA_REMONTADA), [6, 5, 4], [2, 2, 1]),
}


def bicho_txt(b):
    return "{} {}".format(BICHOS[b]["emoji"], BICHOS[b]["nombre"])


def carta_txt(carta):
    tipo, b, v = carta.split(":")
    v = int(v)
    e = BICHOS[b]["emoji"] if b in BICHOS else ""
    if tipo == "MOV":
        return "{} {}{}".format(e, "+" if v > 0 else "−", abs(v))
    if tipo == "MAREO":
        return "😵 Mareo → {}".format(e)
    if tipo == "CAFE":
        return "☕ Café → {}".format(e)
    if tipo == "CHOQUE":
        return "💥 Embestida → {}".format(e)
    if tipo == "PETARDO":
        return "🧨 Petardo → {}".format(e)
    if tipo == "SIESTA":
        return "💤 Siesta → {}".format(e)
    if tipo == "CAMBIO":
        return "🔀 Cambiazo → {}".format(e)
    if tipo == "VIENTO":
        return "🌬️ Viento a favor: todos +1" if v > 0 else "🌪️ Viento en contra: todos −1"
    if tipo == "ESTAMPIDA":
        return "🐾 Estampida: todos +2"
    if tipo == "REVANCHA":
        return "🔥 Revancha: el último +3"
    return carta


def mano_txt(mano):
    """Cartas de la mano, una por línea."""
    return "\n".join("• {}".format(carta_txt(c)) for c in mano) or "-"


# Recordatorio que va en los mensajes donde se ven cartas.
RECORDATORIO_CARTAS = "ℹ️ ¿No te acordás qué hace cada carta? Usá /cartas"


AYUDA_CARTAS = (
    "• *+N / −N*: ese bicho avanza o retrocede N.\n"
    "• 😵 *Mareo*: sus próximos 2 movimientos son de a 1 casilla. Si ya estaba mareado ¡se desmaya y retrocede 3!\n"
    "• ☕ *Café*: se le pasa el mareo y el sueño, y avanza 2.\n"
    "• 💥 *Embestida*: se lanza contra el bicho de adelante, lo alcanza y lo marea (si no hay nadie, avanza 2).\n"
    "• 🧨 *Petardo*: sale disparado 5 casillas, pero queda mareado.\n"
    "• 💤 *Siesta*: se duerme; su próxima carta de movimiento solo lo despierta.\n"
    "• 🔀 *Cambiazo*: intercambia lugar con el que va primero (si ya es el primero, con el último).\n"
    "• 🌬️/🌪️ *Viento*: todos +1 / −1.  🐾 *Estampida*: todos +2.  🔥 *Revancha*: el último +3.\n"
    "Las cartas que afectan a varios bichos nunca los hacen cruzar la meta."
)
