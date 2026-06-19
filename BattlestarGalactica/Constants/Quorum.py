# -*- coding: utf-8 -*-
"""
Mazo de Quórum del JUEGO BASE (hoja "Quorum Cards", Module=B).

Cada carta:
  id, titulo, texto (oficial)
  draw_politics : (opcional) nº de cartas de Política que roba el Presidente al jugarla
  target_efecto : (opcional) "brig" | "pardon" | "mutiny" | "mugshots" |
                  "specialist" | "arbitrator" | "vicepresident" → requiere objetivo
  efectos       : (opcional) lista de efectos inmediatos (soporta "roll", "prophecy")
  keep          : (opcional) True si la carta permanece en juego (efecto continuo
                  descrito en el texto; modelado con estado dedicado en State)

Efecto "roll": {"tipo":"roll","rango":[min,max],"exito":[...],"fracaso":[...]}
  Tira 1d8; aplica 'exito' si cae en [min,max] (inclusive), si no 'fracaso'.
"""

QUORUM_DECK = [
    {
        "id": "inspirational_speech",
        "titulo": "Discurso Inspirador",
        "texto": "Tira 1d8: con 6-8, +1 Moral.",
        "efectos": [{"tipo": "roll", "rango": [6, 8],
                     "exito": [{"tipo": "recurso", "recurso": "moral", "delta": 1}],
                     "fracaso": [{"tipo": "mensaje", "texto": "El discurso no cala."}]}],
    },
    {
        "id": "inspirational_speech_2",
        "titulo": "Discurso Inspirador",
        "texto": "Tira 1d8: con 6-8, +1 Moral.",
        "efectos": [{"tipo": "roll", "rango": [6, 8],
                     "exito": [{"tipo": "recurso", "recurso": "moral", "delta": 1}],
                     "fracaso": [{"tipo": "mensaje", "texto": "El discurso no cala."}]}],
    },
    {
        "id": "food_rationing",
        "titulo": "Racionamiento de Comida",
        "texto": "Tira 1d8: con 6-8, +1 Comida.",
        "efectos": [{"tipo": "roll", "rango": [6, 8],
                     "exito": [{"tipo": "recurso", "recurso": "comida", "delta": 1}],
                     "fracaso": [{"tipo": "mensaje", "texto": "El racionamiento no rinde."}]}],
    },
    {
        "id": "brutal_force",
        "titulo": "Autorización de Fuerza Brutal",
        "texto": "Destruye 3 Raiders (o 1 centurión). Tira 1d8: con 1-2, -1 Población.",
        "efectos": [{"tipo": "raiders", "cantidad": -3},
                    {"tipo": "roll", "rango": [1, 2],
                     "exito": [{"tipo": "recurso", "recurso": "poblacion", "delta": -1}],
                     "fracaso": [{"tipo": "mensaje", "texto": "Sin bajas civiles."}]}],
    },
    {
        "id": "brutal_force_2",
        "titulo": "Autorización de Fuerza Brutal",
        "texto": "Destruye 3 Raiders (o 1 centurión). Tira 1d8: con 1-2, -1 Población.",
        "efectos": [{"tipo": "raiders", "cantidad": -3},
                    {"tipo": "roll", "rango": [1, 2],
                     "exito": [{"tipo": "recurso", "recurso": "poblacion", "delta": -1}],
                     "fracaso": [{"tipo": "mensaje", "texto": "Sin bajas civiles."}]}],
    },
    {
        "id": "arrest_order",
        "titulo": "Orden de Arresto",
        "texto": "Envía a un personaje al Calabozo.",
        "target_efecto": "brig",
    },
    {
        "id": "presidential_pardon",
        "titulo": "Indulto Presidencial",
        "texto": "Saca a otro personaje del Calabozo a una ubicación de Galactica.",
        "target_efecto": "pardon",
    },
    {
        "id": "encourage_mutiny",
        "titulo": "Fomentar Motín",
        "texto": "Elige a un jugador (no Almirante). Tira 1d8: con 1-2, -1 Moral; con 3-8, se vuelve Almirante.",
        "target_efecto": "mutiny",
    },
    {
        "id": "release_mugshots",
        "titulo": "Difundir Fichas Cylon",
        "texto": "Elige un jugador y mira 1 de sus cartas de lealtad al azar. Tira 1d8: con 1-3, -1 Moral.",
        "target_efecto": "mugshots",
    },
    {
        "id": "accept_prophecy",
        "titulo": "Aceptar la Profecía",
        "texto": "Roba 1 carta de Política. (Permanece en juego: el próximo chequeo de "
                 "Administración para nombrar Presidente tiene +2 de dificultad.)",
        "draw_politics": 1,
        "efectos": [{"tipo": "prophecy"}],
    },
    {
        "id": "assign_mission_specialist",
        "titulo": "Asignar Especialista de Misión",
        "texto": "Roba 2 cartas de Política y asigna un Especialista. En el próximo salto, el "
                 "Especialista elige el destino en lugar del Almirante. (Permanece en juego.)",
        "draw_politics": 2,
        "target_efecto": "specialist",
    },
    {
        "id": "assign_arbitrator",
        "titulo": "Asignar Árbitro",
        "texto": "Roba 2 cartas de Política y elige a otro jugador (Árbitro). Cuando alguien active el "
                 "Camarote del Almirante, el Árbitro puede mover la dificultad ±3. (Permanece en juego.)",
        "draw_politics": 2,
        "target_efecto": "arbitrator",
    },
    {
        "id": "assign_vice_president",
        "titulo": "Asignar Vicepresidente",
        "texto": "Roba 2 cartas de Política y nombra un Vicepresidente. Solo el VP puede llegar a "
                 "Presidente vía Administración. (Permanece en juego.)",
        "draw_politics": 2,
        "target_efecto": "vicepresident",
    },
]
