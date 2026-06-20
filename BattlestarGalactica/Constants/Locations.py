# -*- coding: utf-8 -*-
"""
Ubicaciones del juego base — acciones oficiales (hoja Reference del set real).

Códigos de color de los chequeos de ubicación:
  G=Política, P=Liderazgo, Y=Ingeniería, R=Táctica, B=Pilotaje

Algunas ubicaciones tienen una acción que es un *chequeo de habilidad*
(campo "check": {colores, dificultad, efecto}). Otras tienen acción directa.
"""

GALACTICA = "Galactica"
COLONIAL_ONE = "Colonial One"
CYLON = "Cylon"

POLITICA = "Politica"
LIDERAZGO = "Liderazgo"
TACTICA = "Tactica"
PILOTAJE = "Pilotaje"
INGENIERIA = "Ingenieria"

UBICACIONES = {
    # ---------------- GALACTICA ----------------
    "ftl": {
        "nombre": "Control FTL (Galactica)",
        "nave": GALACTICA,
        "accion": "Saltar la flota si el track de salto no está en zona roja (puede perder población).",
    },
    "weapons": {
        "nombre": "Control de Armas (Galactica)",
        "nave": GALACTICA,
        "accion": "Atacar 1 nave Cylon con Galactica. El Almirante puede lanzar una Ojiva Nuclear (limpia un área).",
    },
    "command": {
        "nombre": "Comando (Galactica)",
        "nave": GALACTICA,
        "accion": "Activar hasta 2 Vipers sin tripular (mover/atacar).",
    },
    "communications": {
        "nombre": "Comunicaciones (Galactica)",
        "nave": GALACTICA,
        "accion": "Mirar el reverso de 2 naves civiles; puedes moverlas.",
    },
    "admiral_quarters": {
        "nombre": "Camarote del Almirante (Galactica)",
        "nave": GALACTICA,
        "accion": "Chequeo (dif. 7, Política+Liderazgo): elige un personaje y, si pasa, va al Calabozo.",
        "check": {"colores": [POLITICA, LIDERAZGO], "dificultad": 7, "efecto": "brig"},
    },
    "research": {
        "nombre": "Laboratorio de Investigación (Galactica)",
        "nave": GALACTICA,
        "accion": "Robar 1 carta de Ingeniería o 1 de Táctica.",
    },
    "hangar": {
        "nombre": "Cubierta de Hangar (Galactica)",
        "nave": GALACTICA,
        "accion": "Lanzarte en un Viper (y tomar 1 acción más).",
    },
    "armory": {
        "nombre": "Armería (Galactica)",
        "nave": GALACTICA,
        "accion": "Atacar a un centurión del track de abordaje (destruido con 7-8).",
    },
    "sickbay": {
        "nombre": "Enfermería (Galactica)",
        "nave": GALACTICA,
        "accion": "Solo robas 1 carta de habilidad en tu paso de Recibir Habilidades (sin acción activa).",
    },
    "brig": {
        "nombre": "Calabozo (Galactica)",
        "nave": GALACTICA,
        "accion": "No puedes mover, robar Crisis ni aportar más de 1 carta. "
                  "Acción: chequeo (dif. 7, Ingeniería+Liderazgo) para moverte a cualquier ubicación.",
        "check": {"colores": [INGENIERIA, LIDERAZGO], "dificultad": 7, "efecto": "escape"},
        "es_prision": True,
    },

    # ---------------- COLONIAL ONE ----------------
    "press_room": {
        "nombre": "Sala de Prensa (Colonial One)",
        "nave": COLONIAL_ONE,
        "accion": "Robar 2 cartas de Política.",
    },
    "president_office": {
        "nombre": "Oficina del Presidente (Colonial One)",
        "nave": COLONIAL_ONE,
        "accion": "Si eres Presidente, roba 1 carta de Quórum (y luego roba otra o juega una).",
    },
    "administration": {
        "nombre": "Administración (Colonial One)",
        "nave": COLONIAL_ONE,
        "accion": "Chequeo (dif. 5, Ingeniería+Política): elige un personaje y, si pasa, le das el título de Presidente.",
        "check": {"colores": [INGENIERIA, POLITICA], "dificultad": 5, "efecto": "president"},
    },

    # ---------------- UBICACIONES CYLON ----------------
    "caprica": {
        "nombre": "Caprica",
        "nave": CYLON,
        "accion": "Jugar tu Súper Crisis, o robar 2 Crisis y resolver 1.",
        "es_cylon": True,
    },
    "cylon_fleet": {
        "nombre": "Flota Cylon",
        "nave": CYLON,
        "accion": "Activar todas las naves Cylon de un tipo, o lanzar 2 Raiders y 1 Heavy Raider por Basestar.",
        "es_cylon": True,
    },
    "human_fleet": {
        "nombre": "Flota Humana (Cylon)",
        "nave": CYLON,
        "accion": "Mirar la mano de un jugador y robarle 1 carta; luego tirar dado, 5+ daña Galactica.",
        "es_cylon": True,
    },
    "resurrection_ship": {
        "nombre": "Nave de Resurrección",
        "nave": CYLON,
        "accion": "Descartar tu Súper Crisis para robar otra; si distancia ≤7, dar tu lealtad oculta a otro.",
        "es_cylon": True,
    },
}

AREAS_ESPACIO = ["espacio_1", "espacio_2", "espacio_3", "espacio_4", "espacio_5", "espacio_6"]

# Ubicaciones de Galactica que pueden recibir un token de avería. Al dañarse,
# su acción queda deshabilitada hasta repararla; con las 6 averiadas, Galactica
# es destruida.
GALACTICA_DAMAGEABLE = ["command", "weapons", "ftl", "hangar", "armory", "admiral_quarters"]


def ubicaciones_humanas():
    return {k: v for k, v in UBICACIONES.items() if not v.get("es_cylon")}


def ubicaciones_cylon():
    return {k: v for k, v in UBICACIONES.items() if v.get("es_cylon")}
