# -*- coding: utf-8 -*-
"""
Roster oficial de personajes del JUEGO BASE de Battlestar Galactica.
Datos transcritos del set oficial (hoja "Characters"):
- tipo (subtype), conjunto de habilidades, ubicación inicial, lealtades y
  el texto completo de las tres habilidades de cada personaje.

NOTA: el motor implementa la habilidad de "Acción una vez por juego" de forma
aproximada en algunos casos (ver Controller.usar_habilidad). El texto mostrado
es el oficial. Las ubicaciones iniciales que no existen aún como ubicación
jugable propia se mapean a la más cercana (marcado con  # map).

Formato de "skill_set": lista de *slots*; cada turno (paso "Recibir Habilidades")
se roba el set completo, un slot = una carta.
  - Un color (str) → slot FIJO: siempre se roba ese color (p. ej. Adama: 3
    Liderazgo + 2 Táctica).
  - Una lista de colores → slot de ELECCIÓN: el jugador elige uno de esos colores
    (p. ej. Apolo: 2 slots [Liderazgo/Política]).
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
        "ubicacion": "research",
        "titulo": None,
        "skill_set": [POLITICA, POLITICA, LIDERAZGO, INGENIERIA],
        "abilities": (
            "Intuición Delirante: tras robar una carta de Crisis, roba 1 carta de habilidad "
            "de tu elección (puede ser de fuera de tu set).\n"
            "Detector de Cylons (Acción, 1/juego): mira todas las cartas de lealtad de otro jugador.\n"
            "Cobarde: empiezas con 2 cartas de lealtad (en vez de 1)."
        ),
        "desventaja": "Cobarde: 2 cartas de lealtad iniciales (más chance de ser Cylon).",
        "loyalty_extra": 1,
    },
    "roslin": {
        "nombre": "Laura Roslin",
        "tipo": "Politico",
        "ubicacion": "president_office",
        "titulo": "Presidente",
        "skill_set": [POLITICA, POLITICA, POLITICA, LIDERAZGO, LIDERAZGO],
        "abilities": (
            "Visiones Religiosas: al robar cartas de Crisis, roba 2 y elige 1 para resolver; la otra al fondo.\n"
            "Política Habilidosa (Acción, 1/juego): roba 4 cartas de Quórum, juega 1 y el resto al fondo. "
            "No necesitas ser Presidenta.\n"
            "Enfermedad Terminal: para activar una ubicación debes descartar antes 2 cartas de habilidad."
        ),
        "desventaja": "Enfermedad Terminal: activar ubicaciones cuesta 2 cartas de habilidad.",
    },
    "zarek": {
        "nombre": "Tom Zarek",
        "tipo": "Politico",
        "ubicacion": "press_room",  # map: Administración (Colonial One)
        "titulo": None,
        "skill_set": [POLITICA, POLITICA, LIDERAZGO, LIDERAZGO, TACTICA],
        "abilities": (
            "Amigos en las Sombras: cuando alguien activa 'Administración' o el 'Calabozo', "
            "puedes reducir o aumentar la dificultad en 2.\n"
            "Tácticas Heterodoxas (Acción, 1/juego): pierde 1 población para ganar 1 de cualquier otro recurso.\n"
            "Criminal Convicto: no puedes activar ubicaciones ocupadas por otros personajes (excepto el Calabozo)."
        ),
        "desventaja": "Criminal Convicto: no activa ubicaciones ocupadas por otros.",
    },

    # ---------------- LÍDERES MILITARES ----------------
    "adama": {
        "nombre": "William Adama",
        "tipo": "Militar",
        "ubicacion": "admiral_quarters",
        "titulo": "Almirante",
        "skill_set": [LIDERAZGO, LIDERAZGO, LIDERAZGO, TACTICA, TACTICA],
        "abilities": (
            "Líder Inspirador: al robar una carta de Crisis, todas las cartas de habilidad de fuerza 1 "
            "cuentan en positivo en el chequeo.\n"
            "Autoridad de Mando (1/juego): tras resolver un chequeo, en vez de descartar las cartas "
            "usadas, róbalas a tu mano.\n"
            "Apego Emocional: no puedes activar la ubicación 'Camarote del Almirante'."
        ),
        "desventaja": "Apego Emocional: no puede activar el Camarote del Almirante.",
    },
    "tigh": {
        "nombre": "Saul Tigh",
        "tipo": "Militar",
        "ubicacion": "command",
        "titulo": None,
        "skill_set": [LIDERAZGO, LIDERAZGO, TACTICA, TACTICA, TACTICA],
        "abilities": (
            "Odio a los Cylons: cuando alguien activa el 'Camarote del Almirante', puedes reducir la dificultad en 3.\n"
            "Declarar Ley Marcial (Acción, 1/juego): entrega el título de Presidente al Almirante.\n"
            "Alcohólico: al inicio del turno de cualquier jugador, si tienes exactamente 1 carta de habilidad, descártala."
        ),
        "desventaja": "Alcohólico: descarta si te queda exactamente 1 carta de habilidad.",
    },
    "helo": {
        "nombre": "Karl \"Helo\" Agathon",
        "tipo": "Militar",
        "ubicacion": "hangar",  # Varado: no empieza en el tablero; entra al Hangar en su 2º turno
        "titulo": None,
        "skill_set": [LIDERAZGO, LIDERAZGO, TACTICA, TACTICA, PILOTAJE],
        "abilities": (
            "Oficial ECO: en tu turno puedes repetir una tirada de dado recién hecha (1/turno); usas el nuevo resultado.\n"
            "Brújula Moral (1/juego): tras una elección de una carta de Crisis, puedes cambiarla.\n"
            "Varado: no empiezas en el tablero; al inicio de tu 2º turno te colocas en la Cubierta de Hangar."
        ),
        "desventaja": "Varado: entra al tablero recién en su 2º turno.",
    },

    # ---------------- PILOTOS ----------------
    "apollo": {
        "nombre": "Lee \"Apollo\" Adama",
        "tipo": "Piloto",
        "ubicacion": "hangar",  # map: Sector 5/6 (empieza pilotando un Viper)
        "titulo": None,
        # 1 Táctica + 2 Pilotaje (fijos) + 2 cartas a elegir Liderazgo/Política.
        "skill_set": [TACTICA, PILOTAJE, PILOTAJE, [LIDERAZGO, POLITICA], [LIDERAZGO, POLITICA]],
        "abilities": (
            "Piloto de Viper Alerta: cuando se coloca un Viper desde la reserva, puedes pilotarlo y tomar 1 acción "
            "(estando en una ubicación de Galactica, salvo el calabozo).\n"
            "CAG (Acción, 1/juego): activa hasta 6 Vipers sin tripular.\n"
            "Cabezadura: cuando te obligan a descartar cartas de habilidad, descartas al azar."
        ),
        "desventaja": "Cabezadura: descartes forzados son al azar.",
    },
    "starbuck": {
        "nombre": "Kara \"Starbuck\" Thrace",
        "tipo": "Piloto",
        "ubicacion": "hangar",
        "titulo": None,
        "skill_set": [PILOTAJE, PILOTAJE, TACTICA, TACTICA, LIDERAZGO, INGENIERIA],
        "abilities": (
            "Piloto Experta: si empiezas tu turno pilotando un Viper, tomas 2 acciones en tu paso de Acción.\n"
            "Destino Secreto (1/juego): justo tras revelar una carta de Crisis, descártala y roba otra.\n"
            "Insubordinada: cuando te eligen con el 'Camarote del Almirante', reduce la dificultad en 3."
        ),
        "desventaja": "Insubordinada: -3 dificultad al chequeo del Camarote del Almirante sobre ella.",
    },
    "boomer": {
        "nombre": "Sharon \"Boomer\" Valerii",
        "tipo": "Piloto",
        "ubicacion": "hangar",  # map: Armería
        "titulo": None,
        "skill_set": [PILOTAJE, PILOTAJE, TACTICA, TACTICA, INGENIERIA],
        "abilities": (
            "Reconocimiento: al final de tu turno, mira la carta superior del mazo de Crisis y déjala arriba o abajo.\n"
            "Intuición Misteriosa (1/juego): antes de resolver un chequeo de una Crisis, elige el resultado "
            "(Éxito o Fracaso) en vez de resolverlo normalmente.\n"
            "Agente Durmiente: en la Fase del Agente Durmiente recibes 2 cartas de lealtad (en vez de 1) y "
            "te trasladan al Calabozo."
        ),
        "desventaja": "Agente Durmiente: 2 cartas de lealtad en la fase durmiente y va al Calabozo.",
        "sleeper_extra": 1,
        "sleeper_to_brig": True,
    },

    # ---------------- APOYO ----------------
    "tyrol": {
        "nombre": "Galen \"Chief\" Tyrol",
        "tipo": "Apoyo",
        "ubicacion": "hangar",
        "titulo": None,
        "skill_set": [POLITICA, LIDERAZGO, LIDERAZGO, INGENIERIA, INGENIERIA],
        "abilities": (
            "Ingeniero de Mantenimiento: en tu turno, tras usar una carta de habilidad 'Reparación', "
            "puedes tomar otra acción (1/turno).\n"
            "Devoción Ciega (1/juego): tras añadir las cartas a un chequeo (antes de revelarlas), "
            "elige un tipo de habilidad; todas las cartas de ese tipo cuentan fuerza 0.\n"
            "Imprudente: tu límite de mano es 8 (en vez de 10)."
        ),
        "desventaja": "Imprudente: límite de mano de 8 cartas.",
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
