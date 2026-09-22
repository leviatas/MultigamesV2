import logging as log
import os
import urllib.parse

import psycopg2

# Modo en que cada jugador ve /history: "compacto" (una linea por resultado de la
# votacion) o "extendido" (cada jugador con su voto, uno abajo del otro).
# Es una preferencia del jugador, no del grupo ni de la partida: se guarda por uid
# en history_mode_secret_hitler y vale para todas sus partidas, en cualquier grupo.

MODO_COMPACTO = "compacto"
MODO_EXTENDIDO = "extendido"
MODO_DEFAULT = MODO_COMPACTO

# Lo que puede escribir el jugador despues de /history -> modo.
ALIASES = {
    "compacto": MODO_COMPACTO, "compacta": MODO_COMPACTO, "compact": MODO_COMPACTO, "c": MODO_COMPACTO,
    "extendido": MODO_EXTENDIDO, "extendida": MODO_EXTENDIDO, "extended": MODO_EXTENDIDO,
    "full": MODO_EXTENDIDO, "e": MODO_EXTENDIDO,
}

# DB Connection (mismo patron que GroupMembers.py / NextGame.py)
urllib.parse.uses_netloc.append("postgres")
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])

# uid -> modo. Se precarga entero en init() para no consultar la base en cada /history.
_modo_by_uid = {}


def _connect():
    return psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )


def init():
    """Precarga las preferencias. La llama MainController.main() al arrancar."""
    try:
        conn = _connect()
        cur = conn.cursor()
        cur.execute("SELECT uid, modo FROM history_mode_secret_hitler;")
        for uid, modo in cur.fetchall():
            if modo in (MODO_COMPACTO, MODO_EXTENDIDO):
                _modo_by_uid[int(uid)] = modo
        conn.close()
        log.info("HistoryPrefs: %d jugadores con modo de historial configurado" % len(_modo_by_uid))
    except Exception as e:
        # Un fallo aca solo significa que todos ven el historial en el modo por defecto.
        log.error("HistoryPrefs.init failed: %s" % str(e))


def normalizar(valor):
    """Devuelve el modo para lo que haya escrito el jugador, o None si no se reconoce."""
    if not valor:
        return None
    return ALIASES.get(str(valor).strip().lower())


def get_modo(uid):
    # Sin consulta a la base: init() ya cargo todo y set_modo() mantiene el dict al dia.
    return _modo_by_uid.get(int(uid), MODO_DEFAULT)


def set_modo(uid, modo):
    """Guarda el modo de un jugador. Devuelve True si se pudo persistir."""
    if modo not in (MODO_COMPACTO, MODO_EXTENDIDO):
        return False
    uid = int(uid)
    _modo_by_uid[uid] = modo
    conn = None
    try:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO history_mode_secret_hitler (uid, modo) VALUES (%s, %s) "
            "ON CONFLICT (uid) DO UPDATE SET modo = EXCLUDED.modo, updated_at = now();",
            (uid, modo),
        )
        conn.commit()
        return True
    except Exception as e:
        log.error("HistoryPrefs.set_modo failed for %s: %s" % (uid, str(e)))
        return False
    finally:
        if conn:
            conn.close()
