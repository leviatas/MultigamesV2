ADMIN = 387393551 #your telegram ID

# Version hardcodeada, mostrada por /version. Bumpear en cada cambio que se
# despliegue (ver convencion en CLAUDE.md).
VERSION = "1.41.0"

# --- Voto automatico Ja (/startautoja) ---
# A partir de cuantas politicas promulgadas (de cualquier color) se corta el voto automatico
# de quien haya elegido ese criterio.
POLITICAS_PARA_CORTAR_AUTOJA = 5
# Criterios de corte que puede elegir cada jugador. Los textos con que se los describe
# ("autoja.corte.*") y las etiquetas de los botones ("autoja.btn.*") viven en los
# catalogos de idioma, porque dependen del idioma del grupo.
CORTES_AUTOJA = ["ambas", "fascistas", "politicas"]
CORTE_AUTOJA_DEFAULT = "ambas"
