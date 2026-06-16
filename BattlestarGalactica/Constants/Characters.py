# -*- coding: utf-8 -*-
"""
Roster oficial de personajes del juego base de Battlestar Galactica.

NOTA DE FIDELIDAD: los textos de habilidades y los conjuntos de habilidades
iniciales (`skill_set`) están transcritos lo más fielmente posible, pero
DEBEN verificarse contra el reglamento oficial de FFG antes de considerarse
definitivos. Las claves estructurales (tipo, título, ubicación inicial) sí
son fiables. Marcado con  # VERIFICAR  donde aplica.

Cada personaje:
  key          : identificador interno
  nombre       : nombre mostrado
  tipo         : "Politico" | "Militar" | "Piloto" | "Apoyo"
  ubicacion    : ubicación inicial (clave de Locations)
  titulo       : "Presidente" | "Almirante" | None  (título inicial preferente)
  skill_set    : lista de colores que roba cada turno (Receive Skills)
  habilidad    : texto de la habilidad de una vez por partida / pasiva
  desventaja   : texto de la desventaja (drawback)
"""

# Colores de habilidad
POLITICA = "Politica"
LIDERAZGO = "Liderazgo"
TACTICA = "Tactica"
PILOTAJE = "Pilotaje"
INGENIERIA = "Ingenieria"

PERSONAJES = {
    # ---------------- LÍDERES POLÍTICOS ----------------
    "baltar": {
        "nombre": "Gaius Baltar",
        "tipo": "Politico",
        "ubicacion": "sickbay",
        "titulo": None,
        "skill_set": [POLITICA, POLITICA, LIDERAZGO, INGENIERIA],  # VERIFICAR
        "habilidad": "Recibe una carta de lealtad adicional al inicio. Una vez por juego "
                     "puede mirar una de sus cartas de lealtad y, si quiere, barajarla de nuevo "
                     "en el mazo de lealtad.",  # VERIFICAR
        "desventaja": "Su carta de lealtad extra aumenta su probabilidad de ser Cylon.",
        "loyalty_extra": 1,
    },
    "roslin": {
        "nombre": "Laura Roslin",
        "tipo": "Politico",
        "ubicacion": "president_office",
        "titulo": "Presidente",
        "skill_set": [POLITICA, POLITICA, LIDERAZGO, LIDERAZGO],  # VERIFICAR
        "habilidad": "Al inicio del juego roba 2 cartas de Quórum adicionales (Mandato Ejecutivo).",  # VERIFICAR
        "desventaja": "Enferma: no puede mover salvo por habilidades especiales (Diagnóstico Terminal).",  # VERIFICAR
    },
    "zarek": {
        "nombre": "Tom Zarek",
        "tipo": "Politico",
        "ubicacion": "president_office",
        "titulo": None,
        "skill_set": [POLITICA, POLITICA, LIDERAZGO, TACTICA],  # VERIFICAR
        "habilidad": "Una vez por juego puede provocar una votación para destituir al Presidente "
                     "actual (Filibustero / Agenda política).",  # VERIFICAR
        "desventaja": "Genera desconfianza: penalización al ser elegido para títulos.",
    },

    # ---------------- LÍDERES MILITARES ----------------
    "adama": {
        "nombre": "William Adama",
        "tipo": "Militar",
        "ubicacion": "command",
        "titulo": "Almirante",
        "skill_set": [LIDERAZGO, LIDERAZGO, TACTICA, POLITICA],  # VERIFICAR
        "habilidad": "Una vez por juego puede mover a cualquier jugador a una ubicación adyacente "
                     "y +1 a una tirada de habilidad militar (Cadena de Mando).",  # VERIFICAR
        "desventaja": "Cylon Hatred: tendencia a enviar sospechosos al calabozo.",
    },
    "tigh": {
        "nombre": "Saul Tigh",
        "tipo": "Militar",
        "ubicacion": "command",
        "titulo": None,
        "skill_set": [LIDERAZGO, TACTICA, TACTICA, INGENIERIA],  # VERIFICAR
        "habilidad": "Una vez por juego, todos los jugadores deben descartar una carta de habilidad "
                     "(Declarar Emergencia).",  # VERIFICAR
        "desventaja": "Cylon Hatred: -1 a chequeos políticos.",  # VERIFICAR
    },

    # ---------------- PILOTOS ----------------
    "apollo": {
        "nombre": "Lee \"Apollo\" Adama",
        "tipo": "Piloto",
        "ubicacion": "hangar",
        "titulo": None,
        "skill_set": [PILOTAJE, PILOTAJE, TACTICA, LIDERAZGO],  # VERIFICAR
        "habilidad": "Una vez por juego puede lanzarse en un Viper y +1 a un chequeo de pilotaje "
                     "(A la altura de la leyenda).",  # VERIFICAR
        "desventaja": "Ninguna relevante.",
    },
    "starbuck": {
        "nombre": "Kara \"Starbuck\" Thrace",
        "tipo": "Piloto",
        "ubicacion": "hangar",
        "titulo": None,
        "skill_set": [PILOTAJE, PILOTAJE, TACTICA, TACTICA],  # VERIFICAR
        "habilidad": "Top Gun: una vez por juego puede relanzar su Viper tras ser destruido "
                     "y +1 al ataque desde un Viper.",  # VERIFICAR
        "desventaja": "Imprudente (Reckless): a veces obligada a actuar agresivamente.",
    },
    "boomer": {
        "nombre": "Sharon \"Boomer\" Valerii",
        "tipo": "Piloto",
        "ubicacion": "hangar",
        "titulo": None,
        "skill_set": [PILOTAJE, PILOTAJE, INGENIERIA, TACTICA],  # VERIFICAR
        "habilidad": "Piloto Natural: una vez por juego puede mover su Viper hasta 2 áreas "
                     "y atacar.",  # VERIFICAR
        "desventaja": "Aumenta su probabilidad de ser Cylon (se añade 1 carta 'No eres Cylon' por ella).",
        "loyalty_not_cylon_extra": 1,
    },

    # ---------------- APOYO ----------------
    "tyrol": {
        "nombre": "Galen Tyrol",
        "tipo": "Apoyo",
        "ubicacion": "hangar",
        "titulo": None,
        "skill_set": [INGENIERIA, INGENIERIA, LIDERAZGO, PILOTAJE],  # VERIFICAR
        "habilidad": "Jefe de Cubierta: una vez por juego puede reparar todos los Vipers dañados "
                     "(moverlos de dañado a la reserva).",  # VERIFICAR
        "desventaja": "Cabeza caliente (Hothead): puede iniciar peleas en su ubicación.",  # VERIFICAR
    },
    "helo": {
        "nombre": "Karl \"Helo\" Agathon",
        "tipo": "Apoyo",
        "ubicacion": "command",
        "titulo": None,
        "skill_set": [TACTICA, LIDERAZGO, INGENIERIA, POLITICA],  # VERIFICAR
        "habilidad": "Brújula Moral: una vez por juego puede impedir que un jugador sea enviado "
                     "al calabozo, o sacar a alguien del calabozo.",  # VERIFICAR
        "desventaja": "Demasiado confiado: penalización al sospechar de otros.",
    },
}

# Agrupación por tipo (para la selección de personajes)
TIPOS = ["Politico", "Militar", "Piloto", "Apoyo"]

EMOJI_TIPO = {
    "Politico": "🏛️",
    "Militar": "🎖️",
    "Piloto": "✈️",
    "Apoyo": "🔧",
}


def personajes_por_tipo(tipo):
    return {k: v for k, v in PERSONAJES.items() if v["tipo"] == tipo}
