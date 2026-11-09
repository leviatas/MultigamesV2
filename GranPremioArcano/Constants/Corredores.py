# Elenco de corredores de Gran Premio Arcano y constantes de la pista.
#
# Cada corredor tiene un poder que rompe las reglas. La lógica de cada poder vive en
# GranPremioArcano/Motor.py, buscando por el id del corredor.

CORREDORES = {
    "caracol":    {"emoji": "🐌", "nombre": "Caracol Turbo",
                   "poder": "Si saca 1, 2 o 3 en su tirada, suma +2."},
    "liebre":     {"emoji": "🐇", "nombre": "Liebre Fanfarrona",
                   "poder": "+2 a su tirada, salvo que empiece su turno sola en la punta: ahí se confía y no suma nada."},
    "dino":       {"emoji": "🦖", "nombre": "Dino Torpe",
                   "poder": "Cada corredor que adelanta tropieza."},
    "iman":       {"emoji": "🧲", "nombre": "Imán Andante",
                   "poder": "Al terminar su turno, el corredor más cercano delante suyo retrocede 1 y el más cercano detrás avanza 1."},
    "torbellino": {"emoji": "🌪️", "nombre": "Torbellino",
                   "poder": "En vez de tirar, puede intercambiar lugar con el corredor que tiene inmediatamente delante."},
    "mago":       {"emoji": "🎩", "nombre": "Mago Despistado",
                   "poder": "Puede volver a tirar una vez por turno (se queda con la nueva tirada)."},
    "yeti":       {"emoji": "🧊", "nombre": "Yeti Friolento",
                   "poder": "Los demás corredores que tiran estando a 1 casilla o menos de él mueven −2."},
    "pulpo":      {"emoji": "🐙", "nombre": "Pulpo Pegajoso",
                   "poder": "Cuando otro corredor lo adelanta, se le pega y avanza 2."},
    "duende":     {"emoji": "🍀", "nombre": "Duende Suertudo",
                   "poder": "Si saca un 6, juega otro turno enseguida (una vez por turno)."},
    "fenix":      {"emoji": "🔥", "nombre": "Fénix",
                   "poder": "Si empieza su turno en último lugar, suma +3 a su tirada."},
    "dinamitero": {"emoji": "🧨", "nombre": "Dinamitero",
                   "poder": "Después de tirar puede mover el doble. Si lo hace, explota al llegar: tropiezan él y todos los de su casilla."},
    "fantasma":   {"emoji": "👻", "nombre": "Fantasma",
                   "poder": "Nunca tropieza y atraviesa a los demás (sus adelantamientos no activan poderes). +1 si tira compartiendo casilla."},
    "zorro":      {"emoji": "🦊", "nombre": "Zorro Apostador",
                   "poder": "Antes de tirar apuesta par o impar: si acierta suma +3, si falla −1."},
    "abeja":      {"emoji": "🐝", "nombre": "Abeja Celosa",
                   "poder": "Cuando otro corredor saca un 6, lo pica: ese corredor mueve solo 3."},
    "rey":        {"emoji": "👑", "nombre": "Rey Mimado",
                   "poder": "Al terminar su turno, todos los que estén en su casilla retroceden 2. ¡Fuera de mi camino!"},
    "payaso":     {"emoji": "🤡", "nombre": "Payaso Bromista",
                   "poder": "Una vez por carrera, antes de tirar, puede hacer tropezar a un corredor que esté a 3 casillas o menos."},
    "bruja":      {"emoji": "🧙", "nombre": "Bruja del Pantano",
                   "poder": "Una vez por carrera, en vez de tirar, trae al corredor que va primero a su casilla."},
    "canguro":    {"emoji": "🦘", "nombre": "Canguro",
                   "poder": "En vez de tirar, puede saltar exactamente 4."},
    "dragon":     {"emoji": "🐉", "nombre": "Dragoncito",
                   "poder": "Al terminar su turno escupe fuego: los corredores en las 2 casillas delante suyo retroceden 1."},
    "perezoso":   {"emoji": "🦥", "nombre": "Perezoso",
                   "poder": "Mueve −1 (mínimo 1). Si la carrera termina y él quedó último, su jugador gana 2 puntos."},
    "espejo":     {"emoji": "🪞", "nombre": "Espejo",
                   "poder": "En vez de tirar, puede copiar la última tirada que sacó otro corredor en esta carrera."},
    "mono":       {"emoji": "🐒", "nombre": "Mono Ladrón",
                   "poder": "Cada vez que adelanta a alguien le roba: el adelantado retrocede 1 y el mono avanza 1."},
    "oso":        {"emoji": "🐻", "nombre": "Oso Dormilón",
                   "poder": "Empieza la carrera 4 casillas adelante, pero dormido (tropezado)."},
    "unicornio":  {"emoji": "🦄", "nombre": "Unicornio",
                   "poder": "Si saca 5 o 6 suma +2. Si saca 1 se queda brillando y no se mueve."},
    "arana":      {"emoji": "🕷️", "nombre": "Araña Tejedora",
                   "poder": "Al terminar su turno deja una telaraña en la casilla de la que salió: el próximo que se detenga ahí tropieza."},
    "ardilla":    {"emoji": "🐿️", "nombre": "Ardilla Nerviosa",
                   "poder": "Tira dos dados y elige cuál usar."},
    "robot":      {"emoji": "🤖", "nombre": "Robot Constante",
                   "poder": "No tira: siempre avanza exactamente 3. Nunca tropieza."},
    "tortuga":    {"emoji": "🐢", "nombre": "Tortuga Blindada",
                   "poder": "Los poderes de los demás corredores no pueden moverla, hacerla tropezar ni teletransportarla."},
    "pavo":       {"emoji": "🦚", "nombre": "Pavo Presumido",
                   "poder": "Si adelanta a 2 o más corredores en un mismo movimiento, su jugador gana 1 punto."},
    "hongo":      {"emoji": "🍄", "nombre": "Hongo Saltarín",
                   "poder": "Cuando otro corredor se detiene en su casilla, lo hace rebotar 2 casillas para atrás."},
}

# Largo de la pista: se larga en la casilla 0 y se llega a la meta al alcanzar LARGO_PISTA.
LARGO_PISTA = 24

CANTIDAD_CARRERAS = 4

# Puntos de oro (1°) y plata (2°) por carrera: las últimas valen más.
PUNTOS_ORO = [3, 4, 5, 6]
PUNTOS_PLATA = [1, 2, 2, 3]

# Las carreras 2 y 4 se corren en la Pista Salvaje, con casillas especiales.
PISTA_POR_CARRERA = ["mansa", "salvaje", "mansa", "salvaje"]

CASILLAS_SALVAJES = {
    4: "turbo", 6: "gema", 8: "pozo", 11: "remolino", 13: "turbo",
    15: "gema", 17: "pozo", 20: "remolino", 22: "gema",
}

SIMBOLO_CASILLA = {"turbo": "»", "remolino": "«", "pozo": "o", "gema": "$", "telarana": "#"}

DESCRIPCION_CASILLA = {
    "turbo": "» Turbo: avanza 3",
    "remolino": "« Remolino: retrocede 3",
    "pozo": "o Pozo: tropieza",
    "gema": "$ Gema: +1 punto",
}

NOMBRE_PISTA = {"mansa": "🌳 Pista Mansa", "salvaje": "🌋 Pista Salvaje"}


def etiqueta(rid):
    c = CORREDORES[rid]
    return "{} {}".format(c["emoji"], c["nombre"])


def ficha(rid):
    c = CORREDORES[rid]
    return "{} *{}*: {}".format(c["emoji"], c["nombre"], c["poder"])
