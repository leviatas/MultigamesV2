# -*- coding: utf-8 -*-
"""
Configuración del mazo de Lealtad (Loyalty) del juego base.

Datos confirmados:
- El total de cartas de lealtad repartidas es el doble del número de jugadores
  (1 por jugador al inicio + 1 por jugador en la Fase del Agente Durmiente).
- La Fase del Agente Durmiente ocurre tras alcanzar la distancia 4 (mitad del
  recorrido hacia la distancia 8).
- La carta "Eres un Simpatizante" (Sympathizer) se incluye en partidas de 4 y 6
  jugadores.
- Se añade 1 carta "No eres un Cylon" extra por cada Baltar o Boomer en juego.

PENDIENTE DE VERIFICACIÓN: el número exacto de cartas "Eres un Cylon" por
cantidad de jugadores. Los valores de abajo son los de uso común; ajustar
contra el reglamento oficial si difieren.  # VERIFICAR
"""

CYLON = "cylon"
HUMANO = "humano"
SIMPATIZANTE = "simpatizante"

# Número de cartas "Eres un Cylon" en el mazo, por cantidad de jugadores.
CYLON_CARDS_POR_JUGADORES = {
    3: 1,   # VERIFICAR
    4: 2,   # VERIFICAR
    5: 2,   # VERIFICAR
    6: 3,   # VERIFICAR
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
