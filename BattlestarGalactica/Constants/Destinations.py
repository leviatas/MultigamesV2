# -*- coding: utf-8 -*-
"""
Mazo de Destino de SALTO del JUEGO BASE (10 títulos, 21 cartas en total con
sus repeticiones, hoja "Destination Cards" Module=B). No confundir con el
mazo de Destino de HABILIDAD (State.destiny_deck): ese es un mazo secreto de
cartas de habilidad usado para chequeos; este es el que se roba al ejecutar
un salto FTL y determina a dónde llega la flota.

Cada carta en DESTINATION_CARDS:
  - "count": cuántas copias de esta carta hay en el mazo de 21.
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

construir_mazo_destino() arma el mazo real de 21 cartas (una entrada
independiente por copia) listo para barajar.
"""

DESTINATION_CARDS = [
    {
        "titulo": "Asteroid Field",
        "count": 2,
        "distancia": 3,
        "combustible": -2,
        "efectos": [{"tipo": "destruir_civil"}],
    },
    {
        "titulo": "Deep Space",
        "count": 3,
        "distancia": 2,
        "combustible": -1,
        "efectos": [{"tipo": "recurso", "recurso": "moral", "delta": -1}],
    },
    {
        "titulo": "Ragnar Anchorage",
        "count": 1,
        "distancia": 1,
        "combustible": 0,
        "especial": "ragnar",
        "especial_texto": "🔧 El Almirante puede reparar hasta 3 Vipers y 1 Raptor.",
    },
    {
        "titulo": "Barren Planet",
        "count": 4,
        "distancia": 2,
        "combustible": -2,
    },
    {
        "titulo": "Remote Planet",
        "count": 3,
        "distancia": 2,
        "combustible": -1,
        "efectos": [{"tipo": "raptor", "delta": -1}],
    },
    {
        "titulo": "Desolate Moon",
        "count": 1,
        "distancia": 3,
        "combustible": -3,
    },
    {
        "titulo": "Cylon Refinery",
        "count": 1,
        "distancia": 2,
        "combustible": -1,
        "especial": "cylon_refinery",
        "especial_texto": "🎲 El Almirante puede arriesgar 2 Vipers: 1-5 → se dañan; 6-8 → +2 combustible.",
    },
    {
        "titulo": "Icy Moon",
        "count": 1,
        "distancia": 1,
        "combustible": -1,
        "especial": "icy_moon",
        "especial_texto": "🎲 El Almirante puede arriesgar 1 Raptor: 1-2 → se pierde; 3-8 → +1 comida.",
    },
    {
        "titulo": "Cylon Ambush",
        "count": 1,
        "distancia": 3,
        "combustible": -1,
        "efectos": [
            {"tipo": "basestar", "cantidad": 1},
            {"tipo": "raiders", "cantidad": 3},
            {"tipo": "civiles", "cantidad": 3},
        ],
    },
    {
        "titulo": "Tylium Planet",
        "count": 4,
        "distancia": 1,
        "combustible": -1,
        "especial": "tylium_planet",
        "especial_texto": "🎲 El Almirante puede arriesgar 1 Raptor: 1-2 → se pierde; 3-8 → +2 combustible.",
    },
]


def construir_mazo_destino():
    """Arma el mazo de 21 cartas de Destino de Salto (una copia independiente
    por cada repetición), sin barajar."""
    mazo = []
    for carta in DESTINATION_CARDS:
        copia = {k: v for k, v in carta.items() if k != "count"}
        for _ in range(carta["count"]):
            mazo.append(dict(copia))
    return mazo
