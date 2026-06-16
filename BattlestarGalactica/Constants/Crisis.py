# -*- coding: utf-8 -*-
"""
Mazo de Crisis (juego base) — SET INICIAL representativo.

NOTA DE FIDELIDAD: el juego base tiene ~50 cartas de crisis. Aquí se incluye un
subconjunto representativo con sus mecánicas modeladas para que el motor sea
jugable de punta a punta. Se irán completando todas las cartas oficiales en
capas posteriores.  # VERIFICAR / COMPLETAR

Esquema de cada carta:
  id          : identificador único
  titulo      : nombre de la crisis
  texto       : descripción breve
  tipo        : "chequeo" | "evento"
  colores     : (chequeo) colores que suman en positivo
  dificultad  : (chequeo) valor a igualar o superar
  exito       : lista de efectos si se pasa el chequeo
  fracaso     : lista de efectos si se falla
  efectos     : (evento) lista de efectos inmediatos
  jump        : iconos de avance de preparación de salto (0/1/2)
  activar_cylons : si activa naves Cylon tras resolverse

Esquema de un EFECTO:
  {"tipo": "recurso", "recurso": "comida|combustible|moral|poblacion", "delta": int}
  {"tipo": "raiders", "cantidad": int}
  {"tipo": "mensaje", "texto": str}
"""

CRISIS_DECK = [
    {
        "id": "water_shortage",
        "titulo": "Escasez de Agua",
        "texto": "Los tanques de agua están contaminados.",
        "tipo": "chequeo",
        "colores": ["Politica", "Liderazgo"],
        "dificultad": 7,
        "exito": [{"tipo": "mensaje", "texto": "Se raciona el agua sin pérdidas."}],
        "fracaso": [{"tipo": "recurso", "recurso": "poblacion", "delta": -1},
                    {"tipo": "recurso", "recurso": "comida", "delta": -1}],
        "jump": 1,
        "activar_cylons": True,
    },
    {
        "id": "food_shortage",
        "titulo": "Escasez de Comida",
        "texto": "Las reservas de comida menguan.",
        "tipo": "chequeo",
        "colores": ["Liderazgo", "Politica"],
        "dificultad": 8,
        "exito": [{"tipo": "mensaje", "texto": "Se distribuye la comida con orden."}],
        "fracaso": [{"tipo": "recurso", "recurso": "comida", "delta": -2}],
        "jump": 0,
        "activar_cylons": True,
    },
    {
        "id": "fuel_leak",
        "titulo": "Fuga de Combustible",
        "texto": "Una fuga amenaza las reservas de tylium.",
        "tipo": "chequeo",
        "colores": ["Ingenieria", "Tactica"],
        "dificultad": 8,
        "exito": [{"tipo": "mensaje", "texto": "Sellan la fuga a tiempo."}],
        "fracaso": [{"tipo": "recurso", "recurso": "combustible", "delta": -1}],
        "jump": 1,
        "activar_cylons": False,
    },
    {
        "id": "cylon_raiders",
        "titulo": "Ataque de Raiders Cylon",
        "texto": "Una escuadra de Raiders salta sobre la flota.",
        "tipo": "evento",
        "efectos": [{"tipo": "raiders", "cantidad": 3},
                    {"tipo": "mensaje", "texto": "¡3 Raiders aparecen en el espacio!"}],
        "jump": 0,
        "activar_cylons": True,
    },
    {
        "id": "boarding_party",
        "titulo": "Partida de Abordaje",
        "texto": "Centuriones intentan abordar Galactica.",
        "tipo": "chequeo",
        "colores": ["Tactica", "Liderazgo"],
        "dificultad": 9,
        "exito": [{"tipo": "mensaje", "texto": "Repelen el abordaje."}],
        "fracaso": [{"tipo": "recurso", "recurso": "moral", "delta": -2}],
        "jump": 0,
        "activar_cylons": True,
    },
    {
        "id": "political_crisis",
        "titulo": "Crisis Política",
        "texto": "El Quórum exige respuestas.",
        "tipo": "chequeo",
        "colores": ["Politica"],
        "dificultad": 7,
        "exito": [{"tipo": "mensaje", "texto": "El gobierno mantiene la calma."}],
        "fracaso": [{"tipo": "recurso", "recurso": "moral", "delta": -1}],
        "jump": 1,
        "activar_cylons": False,
    },
    {
        "id": "low_morale",
        "titulo": "Moral por los Suelos",
        "texto": "La desesperanza se extiende por la flota.",
        "tipo": "evento",
        "efectos": [{"tipo": "recurso", "recurso": "moral", "delta": -1},
                    {"tipo": "mensaje", "texto": "La moral cae."}],
        "jump": 1,
        "activar_cylons": True,
    },
    {
        "id": "scout_jump",
        "titulo": "Salto de Reconocimiento",
        "texto": "Una oportunidad para preparar el salto.",
        "tipo": "evento",
        "efectos": [{"tipo": "mensaje", "texto": "Se aprovecha para preparar el salto."}],
        "jump": 2,
        "activar_cylons": False,
    },
    {
        "id": "engine_malfunction",
        "titulo": "Fallo en los Motores",
        "texto": "Los motores FTL fallan.",
        "tipo": "chequeo",
        "colores": ["Ingenieria"],
        "dificultad": 9,
        "exito": [{"tipo": "mensaje", "texto": "Reparan los motores."}],
        "fracaso": [{"tipo": "recurso", "recurso": "combustible", "delta": -1},
                    {"tipo": "raiders", "cantidad": 1}],
        "jump": 0,
        "activar_cylons": True,
    },
    {
        "id": "riots",
        "titulo": "Disturbios en la Flota",
        "texto": "Estallan disturbios entre los civiles.",
        "tipo": "chequeo",
        "colores": ["Liderazgo", "Tactica"],
        "dificultad": 8,
        "exito": [{"tipo": "mensaje", "texto": "Restauran el orden."}],
        "fracaso": [{"tipo": "recurso", "recurso": "moral", "delta": -1},
                    {"tipo": "recurso", "recurso": "poblacion", "delta": -1}],
        "jump": 1,
        "activar_cylons": False,
    },
    {
        "id": "basestar_detected",
        "titulo": "Basestar Detectada",
        "texto": "Una Basestar Cylon aparece en los sensores.",
        "tipo": "evento",
        "efectos": [{"tipo": "raiders", "cantidad": 2},
                    {"tipo": "mensaje", "texto": "Una Basestar lanza Raiders."}],
        "jump": 0,
        "activar_cylons": True,
    },
    {
        "id": "tough_decision",
        "titulo": "Decisión Difícil",
        "texto": "El Almirante debe tomar una decisión impopular.",
        "tipo": "chequeo",
        "colores": ["Liderazgo", "Politica"],
        "dificultad": 10,
        "exito": [{"tipo": "mensaje", "texto": "La decisión sale bien."}],
        "fracaso": [{"tipo": "recurso", "recurso": "moral", "delta": -2}],
        "jump": 1,
        "activar_cylons": True,
    },
]
