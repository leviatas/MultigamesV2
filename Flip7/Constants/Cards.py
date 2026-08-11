# Composición del mazo de Flip 7 y constantes de puntaje.

# Cantidad de copias de cada carta numérica (0 al 12).
NUMBER_CARD_COPIES = {
    0: 1, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6,
    7: 7, 8: 8, 9: 9, 10: 10, 11: 11, 12: 12,
}

# Cartas modificadoras, una copia de cada una.
MODIFIER_CARDS = ["+2", "+4", "+6", "+8", "+10", "X2"]

# Cartas de acción y su cantidad de copias.
ACTION_CARD_COPIES = {
    "FREEZE": 3,
    "FLIP_THREE": 3,
    "SECOND_CHANCE": 3,
}

FLIP7_BONUS = 15
NUMEROS_PARA_FLIP7 = 7
PUNTAJE_OBJETIVO = 200

ACTION_CARD_NAMES = {
    "FREEZE": "❄️ Congelar",
    "FLIP_THREE": "🔄 Flip Three",
    "SECOND_CHANCE": "🍀 Segunda Oportunidad",
}


def build_deck():
    import random
    deck = []
    for numero, copias in NUMBER_CARD_COPIES.items():
        deck += [numero] * copias
    deck += list(MODIFIER_CARDS)
    for accion, copias in ACTION_CARD_COPIES.items():
        deck += [accion] * copias
    random.shuffle(deck)
    return deck


def card_type(carta):
    if isinstance(carta, int):
        return "number"
    if carta in ACTION_CARD_COPIES:
        return "action"
    return "modifier"


def card_display(carta):
    if isinstance(carta, int):
        return str(carta)
    if carta in ACTION_CARD_NAMES:
        return ACTION_CARD_NAMES[carta]
    return carta
