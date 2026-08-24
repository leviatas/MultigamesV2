import logging as log
import os
import urllib.parse

import psycopg2

# DB Connection (mismo patron que StatsExtended.py / Commands.py)
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


def upsert_member(cid, uid, name, is_bot=False, active=True):
    # Registra o actualiza un miembro conocido de un grupo. Se llama desde los
    # handlers de entrada/salida al grupo y desde /join, para que /all tambien
    # alcance a quienes ya estaban en el grupo antes de que este tracking existiera.
    # No propaga excepciones: nunca debe romper el flujo que la esta llamando.
    conn = None
    try:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO group_members_secret_hitler (cid, uid, name, is_bot, active, updated_at)
            VALUES (%s, %s, %s, %s, %s, now())
            ON CONFLICT (cid, uid) DO UPDATE SET
                name = EXCLUDED.name,
                is_bot = EXCLUDED.is_bot,
                active = EXCLUDED.active,
                updated_at = now()
            """,
            (cid, uid, name, is_bot, active)
        )
        conn.commit()
    except Exception as e:
        log.error("No se pudo actualizar group_members_secret_hitler (cid=%s, uid=%s): %s" % (cid, uid, str(e)))
    finally:
        if conn:
            conn.close()


def get_active_members(cid):
    conn = None
    try:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT uid, name FROM group_members_secret_hitler WHERE cid = %s AND active = TRUE AND is_bot = FALSE ORDER BY name",
            (cid,)
        )
        return cur.fetchall()
    except Exception as e:
        log.error("No se pudo leer group_members_secret_hitler (cid=%s): %s" % (cid, str(e)))
        return []
    finally:
        if conn:
            conn.close()
