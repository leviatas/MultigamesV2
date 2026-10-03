"""Versión del bot TextoToAudio (MAYOR.MINOR.PATCH).

Subir la versión en cada cambio del bot:
- MAYOR: cambios incompatibles (ej. se pierde o migra información guardada).
- MINOR: funcionalidades nuevas.
- PATCH: correcciones sin funcionalidades nuevas.
Agregar también una entrada al principio de CHANGELOG.
"""

VERSION = "1.2.0"

CHANGELOG = {
    "1.2.0": "Aviso al admin con la versión al subir una nueva. Comando /version.",
    "1.1.0": "Comando /gender para elegir voz masculina o femenina. Avisos al admin de cada uso.",
    "1.0.0": "Texto a audio y audio a texto con código secreto.",
}
