# -*- coding: utf-8 -*-
"""
Mazo de Destino de SALTO del JUEGO BASE (10 cartas, hoja "Destination Cards"
Module=B). No confundir con el mazo de Destino de HABILIDAD (State.destiny_deck):
ese es un mazo secreto de cartas de habilidad usado para chequeos; este es el
que se roba al ejecutar un salto FTL y determina a dónde llega la flota.

Cada carta:
  - "distancia": cuánto avanza la distancia al ejecutar el salto.
  - "combustible": delta de combustible (siempre <= 0, salvo Ragnar Anchorage).
  - "efectos" (opcional): lista de efectos automáticos, resueltos por
    Controller._aplicar_efectos_destino. Tipos soportados: recurso
    (recurso/delta), destruir_civil, raptor (delta sobre raptors_reserva),
    basestar (cantidad), raiders (cantidad), civiles (cantidad).
  - "especial" (opcional): id de una decisión OPCIONAL del Almirante tras
    llegar (reparar en Ragnar, o arriesgar Vipers/un Raptor por una tirada),
    resuelta por Controller.resolver_destino_especial. "especial_texto" es
    el texto que se ofrece con la decisión.

Nota: la carga exacta de "Cylon Ambush" (naves civiles que llegan junto a la
emboscada) no estaba clara en los datos de origen; se usa el valor más
consistente con el resto de la carta (4 civiles), a falta de confirmarlo
contra la carta física.
"""

DESTINATION_DECK = [
    {
        "titulo": "Asteroid Field",
        "distancia": 3,
        "combustible": -2,
        "efectos": [{"tipo": "destruir_civil"}],
    },
    {
        "titulo": "Deep Space",
        "distancia": 2,
        "combustible": -1,
        "efectos": [{"tipo": "recurso", "recurso": "moral", "delta": -1}],
    },
    {
        "titulo": "Ragnar Anchorage",
        "distancia": 1,
        "combustible": 0,
        "especial": "ragnar",
        "especial_texto": "🔧 El Almirante puede reparar hasta 3 Vipers y 1 Raptor.",
    },
    {
        "titulo": "Barren Planet",
        "distancia": 2,
        "combustible": -2,
    },
    {
        "titulo": "Remote Planet",
        "distancia": 2,
        "combustible": -1,
        "efectos": [{"tipo": "raptor", "delta": -1}],
    },
    {
        "titulo": "Desolate Moon",
        "distancia": 3,
        "combustible": -3,
    },
    {
        "titulo": "Cylon Refinery",
        "distancia": 2,
        "combustible": -1,
        "especial": "cylon_refinery",
        "especial_texto": "🎲 El Almirante puede arriesgar 2 Vipers: 1-5 → se dañan; 6-8 → +2 combustible.",
    },
    {
        "titulo": "Icy Moon",
        "distancia": 1,
        "combustible": -1,
        "especial": "icy_moon",
        "especial_texto": "🎲 El Almirante puede arriesgar 1 Raptor: 1-2 → se pierde; 3-8 → +1 comida.",
    },
    {
        "titulo": "Cylon Ambush",
        "distancia": 3,
        "combustible": -1,
        "efectos": [
            {"tipo": "basestar", "cantidad": 1},
            {"tipo": "raiders", "cantidad": 3},
            {"tipo": "civiles", "cantidad": 4},
        ],
    },
    {
        "titulo": "Tylium Planet",
        "distancia": 1,
        "combustible": -1,
        "especial": "tylium_planet",
        "especial_texto": "🎲 El Almirante puede arriesgar 1 Raptor: 1-2 → se pierde; 3-8 → +2 combustible.",
    },
]
