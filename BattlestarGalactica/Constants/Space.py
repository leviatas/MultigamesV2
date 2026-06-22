# -*- coding: utf-8 -*-
"""
Áreas del espacio alrededor de Galactica (combate posicional).

El espacio se modela como un anillo de 6 áreas. Dos de ellas tienen tubo de
lanzamiento de Vipers (junto a Galactica). La amenaza Cylon aparece en la proa,
los Vipers se lanzan por los tubos y las naves civiles viajan en la popa.

Cada área es un dict:
    {
      "vipers":   int,            # Vipers (sin tripular) en el área
      "raiders":  int,            # Raiders Cylon
      "heavy_raiders": int,       # Heavy Raiders (transportan centuriones al hangar)
      "basestars": [int, ...],    # una entrada por Basestar = tokens de daño
      "civiles":  [carga, ...],   # naves civiles (carga oculta) en el área
    }
"""

N_AREAS = 6

AREAS = [
    {"id": 0, "nombre": "Proa",          "emoji": "🔴", "launch": False},
    {"id": 1, "nombre": "Estribor-proa", "emoji": "▫️", "launch": False},
    {"id": 2, "nombre": "Estribor-popa", "emoji": "▫️", "launch": False},
    {"id": 3, "nombre": "Popa",          "emoji": "🛰️", "launch": False},
    {"id": 4, "nombre": "Babor-popa",    "emoji": "🚀", "launch": True},
    {"id": 5, "nombre": "Babor-proa",    "emoji": "🚀", "launch": True},
]

LAUNCH_AREAS = [5, 4]   # tubos de lanzamiento de Vipers: Babor-proa y Babor-popa
AREA_PROA = 0           # amenaza Cylon inicial
AREA_POPA = 3           # naves civiles iniciales


def nueva_area():
    return {"vipers": 0, "raiders": 0, "heavy_raiders": 0, "basestars": [], "civiles": []}


def distancia(i, j):
    """Distancia en el anillo (mínimo en sentido horario/antihorario)."""
    d = abs(i - j)
    return min(d, N_AREAS - d)


def vecinos(i):
    """Áreas adyacentes (antihoraria, horaria)."""
    return [(i - 1) % N_AREAS, (i + 1) % N_AREAS]


def nombre(i):
    return AREAS[i]["nombre"]


def emoji(i):
    return AREAS[i]["emoji"]
