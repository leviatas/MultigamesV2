# -*- coding: utf-8 -*-
"""
Mazo de Quórum (juego base) — SET INICIAL representativo.

Las cartas de Quórum las roba/juega el Presidente. Aquí se modelan con
efectos globales que el motor ya entiende (recursos, naves, centuriones).
El roster completo y los efectos dirigidos a jugadores se completarán en
una capa posterior.  # VERIFICAR / COMPLETAR

Esquema:
  id      : identificador
  titulo  : nombre
  texto   : descripción
  efectos : lista de efectos (ver aplicar_efectos en el Controller)
"""

QUORUM_DECK = [
    {
        "id": "voto_confianza",
        "titulo": "Voto de Confianza",
        "texto": "El Quórum respalda al gobierno.",
        "efectos": [{"tipo": "recurso", "recurso": "moral", "delta": 1}],
    },
    {
        "id": "racionamiento",
        "titulo": "Racionamiento Eficiente",
        "texto": "Se optimizan las reservas de comida.",
        "efectos": [{"tipo": "recurso", "recurso": "comida", "delta": 1}],
    },
    {
        "id": "reabastecimiento",
        "titulo": "Reabastecimiento de Tylium",
        "texto": "Una operación minera recupera combustible.",
        "efectos": [{"tipo": "recurso", "recurso": "combustible", "delta": 1}],
    },
    {
        "id": "contraataque",
        "titulo": "Orden de Contraataque",
        "texto": "La flota repele a los cazas Cylon.",
        "efectos": [{"tipo": "raiders", "cantidad": -2}],
    },
    {
        "id": "refuerzo_vipers",
        "titulo": "Refuerzo de Vipers",
        "texto": "Llegan Vipers de reserva.",
        "efectos": [{"tipo": "vipers", "cantidad": 2}],
    },
    {
        "id": "ley_marcial",
        "titulo": "Ley Marcial",
        "texto": "Se refuerza la seguridad interna de Galactica.",
        "efectos": [{"tipo": "centuriones", "delta": -1}],
    },
    {
        "id": "asignacion_recursos",
        "titulo": "Asignación de Recursos",
        "texto": "El gobierno coordina la moral de la flota.",
        "efectos": [{"tipo": "recurso", "recurso": "moral", "delta": 1},
                    {"tipo": "recurso", "recurso": "poblacion", "delta": 1}],
    },
]
