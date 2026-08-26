import logging as log
import os
import urllib.parse

import psycopg2

# DB Connection (mismo patron que GroupMembers.py / StatsExtended.py)
urllib.parse.uses_netloc.append("postgres")
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])


def _connect():
    return psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )


def add_waiting(cid, uid, name):
    # Registra que un jugador quiere que se le avise cuando se cree la proxima partida
    # (via /newgame) en este grupo. Se persiste porque puede pasar bastante tiempo, y
    # posibles reinicios del bot, entre /nextgame y el /newgame que lo dispara.
    conn = None
    try:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO nextgame_secret_hitler_waitlist (cid, uid, name)
            VALUES (%s, %s, %s)
            ON CONFLICT (cid, uid) DO UPDATE SET name = EXCLUDED.name
            """,
            (cid, uid, name)
        )
        conn.commit()
    except Exception as e:
        log.error("No se pudo guardar en nextgame_secret_hitler_waitlist (cid=%s, uid=%s): %s" % (cid, uid, str(e)))
    finally:
        if conn:
            conn.close()


def pop_waiting(cid):
    # Devuelve [(uid, name), ...] de quienes esperaban la proxima partida en este grupo
    # y borra esos registros: el aviso es de una sola vez por cada /nextgame.
    conn = None
    try:
        conn = _connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM nextgame_secret_hitler_waitlist WHERE cid = %s RETURNING uid, name", (cid,))
        rows = cur.fetchall()
        conn.commit()
        return rows
    except Exception as e:
        log.error("No se pudo leer/borrar nextgame_secret_hitler_waitlist (cid=%s): %s" % (cid, str(e)))
        return []
    finally:
        if conn:
            conn.close()
