# -*- coding: utf-8 -*-
"""
Ubicaciones del tablero (juego base).

NOTA: los textos de acción son descriptivos y deben verificarse contra el
reglamento oficial. Las claves estructurales (a qué nave pertenece cada
ubicación, cuáles son ubicaciones Cylon) son fiables.
"""

# Naves / zonas
GALACTICA = "Galactica"
COLONIAL_ONE = "Colonial One"
CYLON = "Cylon"

UBICACIONES = {
    # ---------------- GALACTICA ----------------
    "command": {
        "nombre": "Comando (Galactica)",
        "nave": GALACTICA,
        "accion": "Activar un punto de salto / mover naves. Acción de mando.",  # VERIFICAR
    },
    "weapons": {
        "nombre": "Control de Armas (Galactica)",
        "nave": GALACTICA,
        "accion": "Disparar a un Raider o Basestar adyacente a Galactica.",  # VERIFICAR
    },
    "ftl": {
        "nombre": "Control FTL (Galactica)",
        "nave": GALACTICA,
        "accion": "Avanzar la preparación de salto (Jump Prep).",  # VERIFICAR
    },
    "admiral_quarters": {
        "nombre": "Camarote del Almirante (Galactica)",
        "nave": GALACTICA,
        "accion": "El Almirante puede ejecutar un salto si el track está listo.",  # VERIFICAR
    },
    "hangar": {
        "nombre": "Cubierta de Hangar (Galactica)",
        "nave": GALACTICA,
        "accion": "Lanzar un Viper (subirse a un Viper en un área de espacio).",  # VERIFICAR
    },
    "research": {
        "nombre": "Laboratorio de Investigación (Galactica)",
        "nave": GALACTICA,
        "accion": "Robar 2 cartas de habilidad de los colores indicados.",  # VERIFICAR
    },
    "sickbay": {
        "nombre": "Enfermería (Galactica)",
        "nave": GALACTICA,
        "accion": "Curarse / acción de enfermería.",  # VERIFICAR
    },
    "brig": {
        "nombre": "Calabozo (Galactica)",
        "nave": GALACTICA,
        "accion": "Ubicación de prisión: los jugadores enviados aquí no pueden actuar normalmente.",
        "es_prision": True,
    },

    # ---------------- COLONIAL ONE ----------------
    "president_office": {
        "nombre": "Oficina del Presidente (Colonial One)",
        "nave": COLONIAL_ONE,
        "accion": "El Presidente puede jugar/usar cartas de Quórum.",  # VERIFICAR
    },
    "press_room": {
        "nombre": "Sala de Prensa (Colonial One)",
        "nave": COLONIAL_ONE,
        "accion": "Robar 1 carta de habilidad y consultar cartas de Crisis.",  # VERIFICAR
    },

    # ---------------- UBICACIONES CYLON ----------------
    # (donde van los jugadores Cylon revelados)
    "caprica": {
        "nombre": "Caprica",
        "nave": CYLON,
        "accion": "Ubicación Cylon: el Cylon revelado puede actuar contra la flota.",  # VERIFICAR
        "es_cylon": True,
    },
    "cylon_fleet": {
        "nombre": "Flota Cylon",
        "nave": CYLON,
        "accion": "Ubicación Cylon: activar/lanzar naves Cylon.",  # VERIFICAR
        "es_cylon": True,
    },
    "resurrection_ship": {
        "nombre": "Nave de Resurrección",
        "nave": CYLON,
        "accion": "Ubicación Cylon.",  # VERIFICAR
        "es_cylon": True,
    },
    "human_fleet": {
        "nombre": "Flota Humana (Cylon)",
        "nave": CYLON,
        "accion": "Ubicación Cylon.",  # VERIFICAR
        "es_cylon": True,
    },
}

# Áreas de espacio alrededor de Galactica (para naves: vipers, raiders, civiles)
AREAS_ESPACIO = ["espacio_1", "espacio_2", "espacio_3", "espacio_4", "espacio_5", "espacio_6"]


def ubicaciones_humanas():
    return {k: v for k, v in UBICACIONES.items() if not v.get("es_cylon")}


def ubicaciones_cylon():
    return {k: v for k, v in UBICACIONES.items() if v.get("es_cylon")}
