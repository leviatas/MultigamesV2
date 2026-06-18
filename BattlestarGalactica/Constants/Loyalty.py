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


def construir_mazo_lealtad(num_jugadores, num_baltar_boomer=0):
    """
    Construye el mazo de lealtad como lista de strings (CYLON/HUMANO/SIMPATIZANTE).

    Total de cartas = 2 * num_jugadores (+ Sympathizer si aplica, que reemplaza
    a una carta humana para mantener el reparto de 2 por jugador).
    """
    total = 2 * num_jugadores
    cylons = CYLON_CARDS_POR_JUGADORES.get(num_jugadores, 2)
    usa_sympathizer = SYMPATHIZER_POR_JUGADORES.get(num_jugadores, False)

    mazo = [CYLON] * cylons
    if usa_sympathizer:
        mazo.append(SIMPATIZANTE)

    # El resto son humanos, hasta completar el total + las "No eres Cylon" extra.
    humanos = total - len(mazo) + num_baltar_boomer
    if humanos < 0:
        humanos = 0
    mazo += [HUMANO] * humanos
    return mazo
