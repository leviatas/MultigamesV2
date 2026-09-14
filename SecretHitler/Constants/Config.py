ADMIN = 387393551 #your telegram ID

# Version hardcodeada, mostrada por /version. Bumpear en cada cambio que se
# despliegue (ver convencion en CLAUDE.md).
VERSION = "1.27.0"

# --- Voto automatico Ja (/startautoja) ---
# A partir de cuantas politicas promulgadas (de cualquier color) se corta el voto automatico
# de quien haya elegido ese criterio.
POLITICAS_PARA_CORTAR_AUTOJA = 5
# Criterios de corte que puede elegir cada jugador, y como se los describe al explicarlos.
CORTES_AUTOJA = {
    "ambas": "cuando haya 3 políticas fascistas (Zona Hitler) *o* %d políticas promulgadas en total" % POLITICAS_PARA_CORTAR_AUTOJA,
    "fascistas": "solo cuando haya 3 políticas fascistas (Zona Hitler)",
    "politicas": "solo cuando haya %d políticas promulgadas en total" % POLITICAS_PARA_CORTAR_AUTOJA,
}
# Etiquetas cortas para los botones de /startautoja.
CORTES_AUTOJA_BOTONES = {
    "ambas": "Las dos cosas (recomendado)",
    "fascistas": "Solo 3 fascistas",
    "politicas": "Solo %d políticas" % POLITICAS_PARA_CORTAR_AUTOJA,
}
CORTE_AUTOJA_DEFAULT = "ambas"
