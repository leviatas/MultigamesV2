# -*- coding: utf-8 -*-
"""
Mazos de habilidad (5 colores) y configuración de chequeos de habilidad.

En el juego base hay 5 colores de habilidad. Cada chequeo de habilidad suma
las cartas aportadas (boca abajo) más 2 cartas del mazo de Destino (Destiny),
y se compara contra la dificultad de la crisis.

Para esta capa modelamos cada carta de habilidad como {color, valor}. Las
cartas con efectos especiales (p. ej. "Reparaciones", "Maniobra de evasión")
se incorporarán como `nombre`/`efecto` en una capa posterior.  # VERIFICAR
"""

POLITICA = "Politica"
LIDERAZGO = "Liderazgo"
TACTICA = "Tactica"
PILOTAJE = "Pilotaje"
INGENIERIA = "Ingenieria"

COLORES = [POLITICA, LIDERAZGO, TACTICA, PILOTAJE, INGENIERIA]

EMOJI_COLOR = {
    POLITICA: "🟢",     # verde
    LIDERAZGO: "🟣",    # morado
    TACTICA: "🔴",      # rojo
    PILOTAJE: "🔵",     # azul
    INGENIERIA: "🟡",   # amarillo
}

# Distribución de valores por color (aproximada del juego base).  # VERIFICAR
# Cada entrada: valor -> cantidad de cartas de ese valor en el mazo del color.
DISTRIBUCION_VALORES = {
    1: 3,
    2: 3,
    3: 4,
    4: 3,
    5: 2,
}


def construir_mazo_color(color):
    """Devuelve la lista de cartas {color, valor} de un color."""
    mazo = []
    for valor, cantidad in DISTRIBUCION_VALORES.items():
        for _ in range(cantidad):
            mazo.append({"color": color, "valor": valor})
    return mazo


def construir_todos_los_mazos():
    """Devuelve un dict color -> lista de cartas barajables."""
    return {color: construir_mazo_color(color) for color in COLORES}


# Colores considerados "positivos" en un chequeo. En BSG, los colores que NO
# están en la lista de habilidades permitidas de la crisis suman en NEGATIVO.
def signo_para_check(color_carta, colores_permitidos):
    return 1 if color_carta in colores_permitidos else -1
