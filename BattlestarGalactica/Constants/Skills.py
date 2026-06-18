# -*- coding: utf-8 -*-
"""
Mazos de habilidad (5 colores) del juego base, con la composición y las cartas
nombradas oficiales (hoja "Skill cards", Game=B).

Composición por color: 8×valor1, 6×valor2, 4×valor3, 2×valor4, 1×valor5 (21 cartas).

Cada carta: {color, valor, nombre, texto}. El nombre/efecto depende del color y
de un umbral de valor:
  Política       → Consolidate Power (todos los valores)
  Liderazgo  1-2 → Executive Order      | 3-5 → Declare Emergency
  Táctica    1-2 → Launch Scout         | 3-5 → Strategic Planning
  Pilotaje   1-2 → Evasive Maneuvers    | 3-5 → Maximum Firepower
  Ingeniería 1-2 → Repair               | 3-5 → Scientific Research

Efectos implementados automáticamente al aportarse a un chequeo:
  - Declare Emergency: reduce la dificultad del chequeo en 2 (máx. 1 por chequeo).
  - Scientific Research: todas las cartas de Ingeniería del chequeo cuentan en positivo.
Las demás (acción/intervención) se muestran por su texto (juego interactivo futuro).
"""

POLITICA = "Politica"
LIDERAZGO = "Liderazgo"
TACTICA = "Tactica"
PILOTAJE = "Pilotaje"
INGENIERIA = "Ingenieria"

COLORES = [POLITICA, LIDERAZGO, TACTICA, PILOTAJE, INGENIERIA]

EMOJI_COLOR = {
    POLITICA: "🟢", LIDERAZGO: "🟣", TACTICA: "🔴", PILOTAJE: "🔵", INGENIERIA: "🟡",
}

# Composición oficial por color (valor -> cantidad)
DISTRIBUCION_VALORES = {1: 8, 2: 6, 3: 4, 4: 2, 5: 1}

# Texto de cada habilidad nombrada
TEXTOS = {
    "Consolidate Power": "Acción: roba 2 cartas de habilidad de cualquier tipo (incluso fuera de tu set).",
    "Executive Order": "Acción: elige a otro jugador; puede moverse y tomar 1 acción, o no moverse y tomar 2.",
    "Declare Emergency": "Se juega tras totalizar un chequeo: reduce su dificultad en 2 (máx. 1 por chequeo).",
    "Launch Scout": "Acción: arriesga 1 Raptor y tira un dado para mirar/reordenar el mazo de Crisis o Destino.",
    "Strategic Planning": "Se juega antes de una tirada de dado: súmale 2 (máx. 1 por tirada).",
    "Evasive Maneuvers": "Se juega tras atacar a un Viper: repite la tirada (si está tripulado, -2 al nuevo resultado).",
    "Maximum Firepower": "Acción: estando pilotando un Viper, ataca hasta 4 veces.",
    "Repair": "Acción: repara tu ubicación; en la Cubierta de Hangar, repara hasta 2 Vipers dañados.",
    "Scientific Research": "Se juega antes de añadir cartas a un chequeo: todas las de Ingeniería cuentan en positivo.",
}


def nombre_carta(color, valor):
    if color == POLITICA:
        return "Consolidate Power"
    if color == LIDERAZGO:
        return "Executive Order" if valor <= 2 else "Declare Emergency"
    if color == TACTICA:
        return "Launch Scout" if valor <= 2 else "Strategic Planning"
    if color == PILOTAJE:
        return "Evasive Maneuvers" if valor <= 2 else "Maximum Firepower"
    if color == INGENIERIA:
        return "Repair" if valor <= 2 else "Scientific Research"
    return ""


def construir_mazo_color(color):
    mazo = []
    for valor, cantidad in DISTRIBUCION_VALORES.items():
        nombre = nombre_carta(color, valor)
        for _ in range(cantidad):
            mazo.append({"color": color, "valor": valor, "nombre": nombre,
                         "texto": TEXTOS.get(nombre, "")})
    return mazo


def construir_todos_los_mazos():
    return {color: construir_mazo_color(color) for color in COLORES}


def signo_para_check(color_carta, colores_permitidos):
    return 1 if color_carta in colores_permitidos else -1
