# -*- coding: utf-8 -*-
"""
Configuración del mazo de Lealtad (Loyalty) del juego base.

Datos confirmados contra el reglamento oficial:
- Composición inicial del mazo de lealtad por número de jugadores:
      Jugadores | "Eres un Cylon" | "No eres un Cylon"
          3     |        1        |        5
          4     |        1        |        6
          5     |        2        |        8
          6     |        2        |        9
- El total de cartas repartidas es el doble del número de jugadores
  (1 por jugador al inicio + 1 por jugador en la Fase del Agente Durmiente).
- La carta "Eres un Simpatizante" (Sympathizer) se incluye en partidas de 4 y 6
  jugadores; se añade tras la primera ronda, por lo que aparece en la Fase del
  Agente Durmiente.
- Se añade 1 carta "No eres un Cylon" extra por cada Baltar o Boomer en juego
  (Baltar recibe 2 cartas al inicio; Boomer recibe 2 en la Fase Durmiente).
- La Fase del Agente Durmiente ocurre tras alcanzar la distancia 4 (mitad del
  recorrido hacia la distancia 8).
"""

CYLON = "cylon"
HUMANO = "humano"
SIMPATIZANTE = "simpatizante"

# Número de cartas "Eres un Cylon" en el mazo, por cantidad de jugadores
# (valores oficiales del reglamento del juego base).
CYLON_CARDS_POR_JUGADORES = {
    3: 1,
    4: 1,
    5: 2,
    6: 2,
}

# La Sympathizer se usa en partidas con número par de jugadores (4 y 6).
SYMPATHIZER_POR_JUGADORES = {3: False, 4: True, 5: False, 6: True}

# Distancia a la que se dispara la Fase del Agente Durmiente.
DISTANCIA_SLEEPER = 4

# Zona roja de los diales de recursos (≈ un cuarto del valor inicial). Si algún
# recurso está en rojo cuando aparece el Simpatizante, éste se vuelve Cylon.
ZONA_ROJA = {"comida": 2, "combustible": 2, "moral": 2, "poblacion": 3}


def usa_sympathizer(num_jugadores):
    return SYMPATHIZER_POR_JUGADORES.get(num_jugadores, False)


def construir_mazo_lealtad(num_jugadores, num_baltar_boomer=0, incluir_sympathizer=True):
    """
    Construye el mazo de lealtad como lista de strings (CYLON/HUMANO/SIMPATIZANTE).

    Total de cartas = 2 * num_jugadores (la Sympathizer, si aplica, reemplaza
    a una carta humana para mantener el reparto de 2 por jugador).

    Con incluir_sympathizer=False la carta de Simpatizante se omite del mazo
    (el reparto inicial no debe poder contenerla: según el reglamento se añade
    al mazo restante recién para la Fase del Agente Durmiente).
    """
    total = 2 * num_jugadores
    cylons = CYLON_CARDS_POR_JUGADORES.get(num_jugadores, 2)
    con_sympathizer = usa_sympathizer(num_jugadores)

    mazo = [CYLON] * cylons
    if con_sympathizer and incluir_sympathizer:
        mazo.append(SIMPATIZANTE)

    # El resto son humanos, hasta completar el total + las "No eres Cylon" extra.
    # Si la Sympathizer se añade después, ocupa desde ya su lugar en el total.
    ocupadas = len(mazo) + (1 if con_sympathizer and not incluir_sympathizer else 0)
    humanos = total - ocupadas + num_baltar_boomer
    if humanos < 0:
        humanos = 0
    mazo += [HUMANO] * humanos
    return mazo
