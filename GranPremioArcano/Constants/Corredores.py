# Elenco de corredores de Gran Premio Arcano y constantes de la pista.
#
# Cada corredor tiene un poder que rompe las reglas. La lógica de cada poder vive en
# GranPremioArcano/Motor.py, buscando por el id del poder (que es el id del corredor).
#
# "sigla" es lo que se dibuja en la ficha de la imagen de la pista (sin emojis).
# "nota" (opcional) aclara cómo resuelve el bot las decisiones que se toman solas.

CORREDORES = {
    "transmutador": {"emoji": "⚗️", "sigla": "TR", "nombre": "El Transmutador",
        "poder": "Si obtiene 1 o 2 en su movimiento, puede avanzar 4 espacios."},
    "bruja": {"emoji": "🧙", "sigla": "BT", "nombre": "La Bruja del Tropiezo",
        "poder": "Hace tropezar a cualquier corredor que termine en su casilla o cuando ella termina en la casilla de otro corredor."},
    "cascara": {"emoji": "🍌", "sigla": "CS", "nombre": "La Cáscara",
        "poder": "Hace tropezar a cualquier corredor que lo sobrepase."},
    "dirigible": {"emoji": "🎈", "sigla": "DI", "nombre": "El Dirigible",
        "poder": "Si comienza su turno antes de la segunda curva, suma 3 a su movimiento. Desde esa curva en adelante, resta 1."},
    "centauro": {"emoji": "🏹", "sigla": "CE", "nombre": "El Centauro",
        "poder": "Cuando sobrepasa a otro corredor, ese corredor retrocede 2 espacios."},
    "animadora": {"emoji": "📣", "sigla": "AN", "nombre": "La Animadora",
        "poder": "Antes de moverse, puede hacer avanzar 2 espacios a los últimos corredores. Si lo hace, ella avanza solamente 1."},
    "entrenador": {"emoji": "📋", "sigla": "EN", "nombre": "El Entrenador",
        "poder": "Todos los corredores que estén en su casilla, incluido él, suman 1 a su movimiento."},
    "imitador": {"emoji": "🎭", "sigla": "IM", "nombre": "El Imitador",
        "poder": "Tiene el poder del corredor que esté primero. Si hay empate, elige a quién copiar.",
        "nota": "Con empate copia al primero de ellos en el orden de turnos."},
    "apostador": {"emoji": "🎰", "sigla": "AP", "nombre": "El Apostador",
        "poder": "Todos pueden repetir una vez su tirada por turno. Cada vez que otro lo hace, él avanza 1 espacio."},
    "retador": {"emoji": "🥊", "sigla": "RE", "nombre": "El Retador",
        "poder": "Cuando otro corredor comparte su casilla, puede desafiarlo. Ambos tiran un dado y quien saque el número más alto avanza 2 espacios. Gana los empates.",
        "nota": "Desafía siempre, automáticamente."},
    "cambiante": {"emoji": "🦎", "sigla": "CA", "nombre": "El Cambiante",
        "poder": "Antes de la carrera roba 3 personajes y elige uno. Utiliza sus poderes."},
    "intercambiador": {"emoji": "🔄", "sigla": "IN", "nombre": "El Intercambiador",
        "poder": "Puede no tirar el dado y cambiar de lugar con otro corredor."},
    "adivino": {"emoji": "🔮", "sigla": "AD", "nombre": "El Adivino",
        "poder": "Predice qué número obtendrá en su tirada. Si acierta, juega otro turno inmediatamente."},
    "pegajoso": {"emoji": "🍯", "sigla": "PG", "nombre": "El Pegajoso",
        "poder": "Todos los demás corredores restan 1 a su movimiento."},
    "liebre": {"emoji": "🐇", "sigla": "LI", "nombre": "La Liebre",
        "poder": "Suma 2 a su movimiento. Pero si comienza su turno sola en primer lugar, pierde su movimiento."},
    "burlon": {"emoji": "😜", "sigla": "BU", "nombre": "El Burlón",
        "poder": "Cuando otro corredor termina su turno a 1 espacio o menos de donde empezó, él avanza 2."},
    "gigante": {"emoji": "🗿", "sigla": "GI", "nombre": "El Gigante",
        "poder": "Nadie puede ocupar su casilla, excepto en la salida. Si alguien debería terminar allí, queda en la casilla anterior."},
    "hipnotizador": {"emoji": "🌀", "sigla": "HI", "nombre": "El Hipnotizador",
        "poder": "Antes de moverse, puede teletransportar a otro corredor hasta su casilla."},
    "gusano": {"emoji": "🐛", "sigla": "GU", "nombre": "El Gusano",
        "poder": "Cuando otro corredor saca 1, no puede moverse y él avanza 1."},
    "sirviente": {"emoji": "🤵", "sigla": "SI", "nombre": "El Sirviente",
        "poder": "Cuando otro corredor saca 6, él avanza 2 antes de que ese corredor se mueva."},
    "saltador": {"emoji": "🐸", "sigla": "SA", "nombre": "El Saltador",
        "poder": "Al moverse, salta por encima de las casillas ocupadas por otros corredores."},
    "piernas": {"emoji": "🦵", "sigla": "PA", "nombre": "Piernas de Acero",
        "poder": "Puede no tirar el dado y avanzar directamente 5 espacios."},
    "desafortunado": {"emoji": "😩", "sigla": "DE", "nombre": "El Desafortunado",
        "poder": "Antes de moverse, recibe 1 ficha de punto si está solo en último lugar."},
    "ilusionista": {"emoji": "🎩", "sigla": "IL", "nombre": "El Ilusionista",
        "poder": "Puede repetir su tirada de movimiento hasta 2 veces."},
    "estratega": {"emoji": "♟️", "sigla": "ES", "nombre": "El Estratega",
        "poder": "Al comienzo de su primer turno predice quién ganará. Si acierta, la carrera termina inmediatamente y él queda segundo.",
        "nota": "La predicción se hace en la largada."},
    "devorador": {"emoji": "👹", "sigla": "DV", "nombre": "El Devorador",
        "poder": "Si termina en una casilla con exactamente otro corredor, lo elimina de la carrera."},
    "iman": {"emoji": "🧲", "sigla": "MU", "nombre": "El Imán de Multitudes",
        "poder": "Antes de moverse, todos avanzan 1 espacio hacia él. Cada corredor que termine en su casilla le suma 1 a su movimiento."},
    "cohete": {"emoji": "🚀", "sigla": "CO", "nombre": "El Cohete",
        "poder": "Puede duplicar el resultado de su dado. Si lo hace, termina tropezando después de moverse."},
    "enamorado": {"emoji": "💘", "sigla": "EA", "nombre": "El Enamorado",
        "poder": "Cuando cualquier corredor termina en una casilla compartida con exactamente otro corredor, él avanza 2."},
    "aprovechado": {"emoji": "🦊", "sigla": "AV", "nombre": "El Aprovechado",
        "poder": "Cada vez que se activa el poder de otro corredor, él avanza 1.",
        "nota": "Cuentan los poderes que disparan un efecto, no los que solo suman o restan al movimiento."},
    "condenado": {"emoji": "⛓️", "sigla": "CD", "nombre": "El Condenado",
        "poder": "Comienza con 4 fichas de punto. Si saca 6, en vez de avanzar vuelve a la salida y pierde 1 ficha."},
    "marinero": {"emoji": "⚓", "sigla": "MA", "nombre": "El Marinero",
        "poder": "Cuando alguien saca 1, él pasa a ser el siguiente en el orden de turnos."},
    "perfeccionista": {"emoji": "📏", "sigla": "PF", "nombre": "El Perfeccionista",
        "poder": "Los demás solamente pueden cruzar la meta sacando exactamente la cantidad necesaria. Si se pasan, no avanzan."},
    "pegado": {"emoji": "🐟", "sigla": "PE", "nombre": "El Pegado",
        "poder": "Cuando otro corredor que comparte su casilla se mueve, puede trasladarse a la nueva casilla de ese corredor.",
        "nota": "Se traslada solo si el otro avanzó."},
    "intruso": {"emoji": "🥷", "sigla": "IT", "nombre": "El Intruso",
        "poder": "Antes de moverse, puede teletransportarse a cualquier casilla ocupada por exactamente 2 corredores."},
    "heredero": {"emoji": "👑", "sigla": "HE", "nombre": "El Heredero",
        "poder": "Antes de la carrera, puede elegir un corredor ganador de una carrera anterior y utilizar sus poderes."},
    "bestia": {"emoji": "🐺", "sigla": "BE", "nombre": "La Bestia",
        "poder": "Cuando saca 1 o 2, se transforma en una bestia que elimina a cualquier corredor que sobrepase."},
    "perro": {"emoji": "🐶", "sigla": "PT", "nombre": "El Perro Torpe",
        "poder": "Si está último, triplica el resultado de su dado. Si no está último, se mueve hacia atrás en lugar de avanzar."},
    "tramposo": {"emoji": "🃏", "sigla": "TP", "nombre": "El Tramposo",
        "poder": "En lugar de tirar, elige en secreto un número del 1 al 6. Si el jugador de su derecha adivina el número, no se mueve."},
    "critico": {"emoji": "🧐", "sigla": "CR", "nombre": "El Crítico",
        "poder": "Puede obligar a los corredores que estén delante suyo a repetir su tirada una vez por turno.",
        "nota": "Lo hace solo, cuando sacan 4 o más."},
    "estrella": {"emoji": "⭐", "sigla": "ET", "nombre": "La Estrella",
        "poder": "Si empieza su turno última, intercambia su posición con el primero. Si no, intercambia su posición con el último."},
    "impostor": {"emoji": "🕵️", "sigla": "IP", "nombre": "El Impostor",
        "poder": "El corredor que termina primero queda eliminado. Él obtiene su poder.",
        "nota": "Una vez por carrera: el primero que cruzaría la meta queda eliminado en su lugar."},
    "baboso": {"emoji": "🐌", "sigla": "BB", "nombre": "El Baboso",
        "poder": "Resta 1 a su movimiento. Si termina la carrera sin haber pasado la segunda curva, obtiene 3 puntos."},
    "jinete": {"emoji": "🐗", "sigla": "JJ", "nombre": "El Jinete Jabalí",
        "poder": "Comienza montado en un jabalí que suma 2 al movimiento de quien lo monta. Si otro corredor termina en su casilla, se queda con el jabalí."},
    "reboteador": {"emoji": "🏀", "sigla": "RB", "nombre": "El Reboteador",
        "poder": "Si termina su turno exactamente 1 espacio detrás de otro corredor, obtiene un turno adicional."},
    "cobrador": {"emoji": "💰", "sigla": "CB", "nombre": "El Cobrador",
        "poder": "Cuando otro corredor termina en su casilla, debe pagarle 1 punto. Si no puede, tropieza."},
    "icaro": {"emoji": "🪶", "sigla": "IC", "nombre": "El Ícaro",
        "poder": "Suma 3 a su movimiento. Si saca 6, queda eliminado de la carrera."},
    "rey_tropiezo": {"emoji": "🤴", "sigla": "RT", "nombre": "El Rey del Tropiezo",
        "poder": "Al comienzo de su turno puede hacer tropezar al corredor que esté primero."},
    "leviatan": {"emoji": "🐋", "sigla": "LE", "nombre": "El Leviatán",
        "poder": "Una vez por carrera, al comienzo de su turno, puede teletransportar a todos los demás corredores a su casilla y hacerlos tropezar."},
    "saboteador": {"emoji": "💣", "sigla": "SB", "nombre": "El Saboteador",
        "poder": "Cuando otro corredor saca 3, en lugar de avanzar retrocede 3 espacios."},
    "caotico": {"emoji": "🌪️", "sigla": "CT", "nombre": "El Caótico",
        "poder": "Su dado tiene efectos especiales: 1: avanza 7. 2: el último se teletransporta hasta él. 3: se teletransporta hasta otro corredor y lo hace tropezar. 4: avanza 4 y obtiene otro turno. 5: el primero retrocede 5. 6: avanza 6 y hace tropezar a todos los que sobrepasa.",
        "nota": "Con el 3 va hasta el que esté primero."},
    "excavador": {"emoji": "⛏️", "sigla": "EX", "nombre": "El Excavador",
        "poder": "Si no hay corredores a 1 espacio de distancia, puede evitar tirar y avanzar directamente 6 espacios."},
    "maestro": {"emoji": "🎲", "sigla": "MD", "nombre": "El Maestro de los Dados",
        "poder": "Tira los 6 dados y elige cualquier número que haya salido más de una vez."},
    "mutante": {"emoji": "🧬", "sigla": "MT", "nombre": "El Mutante",
        "poder": "Cuando saca 1 o 2, roba una carta de corredor y obtiene su poder durante el resto de la carrera."},
    "rival": {"emoji": "😤", "sigla": "RI", "nombre": "El Rival",
        "poder": "Cuando otro corredor tira su dado, él también puede tirar. Si obtiene el mismo resultado, avanza esa cantidad."},
    "nino_rico": {"emoji": "💎", "sigla": "NR", "nombre": "El Niño Rico",
        "poder": "Comienza la carrera directamente en la primera curva."},
    "anulador": {"emoji": "🚫", "sigla": "AU", "nombre": "El Anulador",
        "poder": "Los corredores que estén delante suyo restan 1 a su movimiento y no pueden utilizar sus poderes."},
    "adelantador": {"emoji": "🏎️", "sigla": "AL", "nombre": "El Adelantador",
        "poder": "Suma 1 a su movimiento por cada corredor que esté delante suyo."},
    "aguafiestas": {"emoji": "🌧️", "sigla": "AG", "nombre": "El Aguafiestas",
        "poder": "Todos los resultados de 6 deben repetirse. Cada vez que alguien repite un 6, él avanza 1."},
    "pinguino": {"emoji": "🐧", "sigla": "PI", "nombre": "El Pingüino Deslizante",
        "poder": "Cuando alguien lo sobrepasa, tropieza. Mientras está tropezado, duplica su tirada de movimiento en lugar de perder el movimiento."},
    "extra": {"emoji": "➕", "sigla": "XT", "nombre": "El Corredor Extra",
        "poder": "Después de su primera carrera, participa como un corredor adicional de su jugador en todas las carreras restantes."},
    "presumido": {"emoji": "🦚", "sigla": "PR", "nombre": "El Presumido",
        "poder": "Después de tirar, puede seguir tirando y sumar cada resultado a su movimiento. Si alguna tirada es igual o menor que la anterior, no se mueve."},
    "alma_gemela": {"emoji": "💞", "sigla": "AM", "nombre": "El Alma Gemela",
        "poder": "Antes de la carrera elige un corredor rival. Cuando comienza su turno a 5 espacios o menos de él, se teletransporta a su casilla."},
    "demonio": {"emoji": "😈", "sigla": "DM", "nombre": "El Demonio Veloz",
        "poder": "Suma 1 a su movimiento por cada punto que tenga su jugador. Si al comenzar su turno está 4 o más espacios delante de todos, queda eliminado."},
    "cancelador": {"emoji": "❌", "sigla": "CN", "nombre": "El Cancelador",
        "poder": "Si al comenzar su turno todos los demás corredores están al menos 5 espacios delante suyo, cancela la carrera y obtiene 3 puntos."},
    "padrastro": {"emoji": "🧔", "sigla": "PD", "nombre": "El Padrastro",
        "poder": "El corredor sentado a su izquierda suma 2 a su movimiento. Si ese corredor gana, él obtiene 3 puntos.",
        "nota": "A su izquierda = los corredores del jugador que juega después del suyo."},
    "exhibicionista": {"emoji": "🤩", "sigla": "EB", "nombre": "El Exhibicionista",
        "poder": "Cada vez que sobrepasa a otro corredor, obtiene 1 punto."},
    "paralizador": {"emoji": "⚡", "sigla": "PZ", "nombre": "El Paralizador",
        "poder": "Los demás corredores que estén a 1 espacio de él obtienen siempre un resultado de 1 en sus tiradas."},
    "piloto": {"emoji": "🔀", "sigla": "IV", "nombre": "El Intercambiador de Pilotos",
        "poder": "Si termina su turno a 1 espacio o menos de otro corredor, puede intercambiar las cartas de ambos jugadores.",
        "nota": "Intercambia solo si el otro corredor va delante y es de otro jugador."},
    "seguidor": {"emoji": "👣", "sigla": "SG", "nombre": "El Seguidor",
        "poder": "Al comenzar su turno puede teletransportarse a la casilla inmediatamente detrás del siguiente corredor que tenga delante."},
    "manguera": {"emoji": "🚿", "sigla": "MG", "nombre": "La Manguera",
        "poder": "Al terminar su turno tira un dado y hace tropezar a todos los corredores que estén delante suyo dentro de esa distancia."},
    "suplente": {"emoji": "🔁", "sigla": "SU", "nombre": "El Suplente",
        "poder": "Antes de la carrera, copia el poder de cualquier corredor rival."},
}

# Largo de la pista (circuito "Wild Worlds"): se larga en la SALIDA (casilla 0, fuera
# del recorrido), el recorrido tiene las casillas 1 a 29 y la casilla 30 es la
# LLEGADA: el que alcanza LARGO_PISTA cruza la meta.
LARGO_PISTA = 30

# Curvas del circuito: las esquinas de la imagen de la pista (arriba a la derecha y
# abajo a la derecha).
PRIMERA_CURVA = 12
SEGUNDA_CURVA = 15

CANTIDAD_CARRERAS = 4

# Puntos de oro (1°) y plata (2°) por carrera: las últimas valen más.
PUNTOS_ORO = [3, 4, 5, 6]
PUNTOS_PLATA = [1, 2, 2, 3]

# Las carreras 2 y 4 se corren en la Pista Salvaje, con casillas especiales.
PISTA_POR_CARRERA = ["mansa", "salvaje", "mansa", "salvaje"]

# Casillas especiales de la Pista Salvaje: posición -> (tipo, valor).
#   estrella: +valor puntos · tropiezo: el corredor tropieza ·
#   flecha: avanza valor casillas (negativo = retrocede)
CASILLAS_SALVAJES = {
    1: ("estrella", 1),
    5: ("tropiezo", 0),
    7: ("flecha", 3),
    11: ("flecha", 1),
    13: ("estrella", 1),
    16: ("flecha", 4),
    17: ("tropiezo", 0),
    23: ("flecha", 2),
    24: ("flecha", -2),
    26: ("tropiezo", 0),
}


def simbolo_casilla(tipo, valor):
    """Símbolo de una casilla especial en la pista de texto."""
    if tipo == "estrella":
        return "*"
    if tipo == "tropiezo":
        return "x"
    return ">" if valor > 0 else "<"


DESCRIPCION_CASILLA = {
    "estrella": "* Estrella: +1 punto",
    "tropiezo": "x Trip: tropieza",
    "avanza": "> Flecha: avanza 1 a 4",
    "retrocede": "< Flecha roja: retrocede 2",
}

NOMBRE_PISTA = {"mansa": "🌳 Pista Mansa", "salvaje": "🌋 Pista Salvaje"}


def etiqueta(rid):
    c = CORREDORES[rid]
    return "{} {}".format(c["emoji"], c["nombre"])


def ficha(rid):
    c = CORREDORES[rid]
    texto = "{} *{}*: {}".format(c["emoji"], c["nombre"], c["poder"])
    if c.get("nota"):
        texto += " _({})_".format(c["nota"])
    return texto
