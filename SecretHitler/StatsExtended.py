import logging as log
import os
import re
import urllib.parse

import psycopg2

# DB Connection (mismo patron que MainController.py / Commands.py)
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


def save_extended_game_stats(game, game_endcode):
    # Guarda, ademas de lo que ya se guarda hoy, un registro por jugador vinculado a su uid.
    # No propaga excepciones: un fallo aca nunca debe impedir que end_game() termine su flujo normal.
    if game_endcode == 99:
        return
    try:
        won_liberal = game_endcode in (1, 2)
        won_fascist = game_endcode in (-1, -2)

        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO stats_secret_hitler_games(game_endcode) VALUES (%s) RETURNING id;",
            (game_endcode,)
        )
        game_id = cur.fetchone()[0]

        for uid, player in game.playerlist.items():
            if player.party == "liberal":
                won = won_liberal
            elif player.party == "fascista":
                won = won_fascist
            else:
                won = False
            cur.execute(
                "INSERT INTO stats_secret_hitler_players"
                "(game_id, uid, name, role, party, won, died, killed_by_uid) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
                "ON CONFLICT (game_id, uid) DO NOTHING;",
                (game_id, uid, player.name, player.role, player.party, won,
                 player.is_dead, getattr(player, "killed_by_uid", None))
            )

        conn.commit()
        conn.close()
    except Exception as e:
        log.error("save_extended_game_stats failed: %s" % str(e))


def get_base_stats_by_uid(uid):
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT role, won, died FROM stats_secret_hitler_players WHERE uid = %s;",
        (uid,)
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return None

    def _count(role, won_only=False):
        return sum(1 for r in rows if r[0] == role and (r[1] if won_only else True))

    return {
        "total": len(rows),
        "liberal": _count("Liberal"),
        "liberal_won": _count("Liberal", won_only=True),
        "fascista": _count("Fascista"),
        "fascista_won": _count("Fascista", won_only=True),
        "hitler": _count("Hitler"),
        "hitler_won": _count("Hitler", won_only=True),
        "murio": sum(1 for r in rows if r[2]),
        "gano": sum(1 for r in rows if r[1]),
    }


def get_kill_stats(uid):
    conn = _connect()
    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM stats_secret_hitler_players WHERE killed_by_uid = %s;",
        (uid,)
    )
    kills_count = cur.fetchone()[0]

    cur.execute(
        "SELECT uid, name, COUNT(*) c FROM stats_secret_hitler_players "
        "WHERE killed_by_uid = %s GROUP BY uid, name ORDER BY c DESC, uid LIMIT 1;",
        (uid,)
    )
    most_killed = cur.fetchone()

    cur.execute(
        "SELECT killed_by_uid, COUNT(*) c FROM stats_secret_hitler_players "
        "WHERE uid = %s AND killed_by_uid IS NOT NULL "
        "GROUP BY killed_by_uid ORDER BY c DESC LIMIT 1;",
        (uid,)
    )
    row = cur.fetchone()
    most_frequent_killer = None
    if row is not None:
        killer_uid, killer_count = row
        cur.execute(
            "SELECT name FROM stats_secret_hitler_players WHERE uid = %s "
            "ORDER BY game_id DESC LIMIT 1;",
            (killer_uid,)
        )
        namerow = cur.fetchone()
        killer_name = namerow[0] if namerow else str(killer_uid)
        most_frequent_killer = (killer_name, killer_count)

    conn.close()
    return {
        "kills_count": kills_count,
        "most_killed": most_killed,
        "most_frequent_killer": most_frequent_killer,
    }


def get_teammate_stats(uid):
    conn = _connect()
    cur = conn.cursor()

    def _top_teammates(won_value):
        cur.execute(
            "SELECT b.uid, MAX(b.name), COUNT(*) c "
            "FROM stats_secret_hitler_players a "
            "JOIN stats_secret_hitler_players b "
            "  ON a.game_id = b.game_id AND a.party = b.party AND a.uid != b.uid "
            "WHERE a.uid = %s AND a.won = %s "
            "GROUP BY b.uid ORDER BY c DESC;",
            (uid, won_value)
        )
        rows = cur.fetchall()
        if not rows:
            return []
        top_count = rows[0][2]
        return [(name, c) for (_, name, c) in rows if c == top_count]

    best_teammates = _top_teammates(True)
    worst_teammates = _top_teammates(False)
    conn.close()
    return {
        "best_teammates": best_teammates,
        "worst_teammates": worst_teammates,
    }


def _normalize_role(raw):
    raw = raw.lower()
    if raw.startswith("fasc"):
        return "Fascista"
    if raw.startswith("hitl"):
        return "Hitler"
    if raw.startswith("libe"):
        return "Liberal"
    return None


def _extract_legacy_role(stripped_playerlist, name):
    escaped = re.escape(name)
    patterns = [
        r"%s\s*secret role was\s*(Fasc\w*|Hitl\w*|Libe\w*)" % escaped,
        r"El rol de %s\s*(?:era|sera)\s*(Fasc\w*|Hitl\w*|Libe\w*)" % escaped,
    ]
    for pattern in patterns:
        m = re.search(pattern, stripped_playerlist, re.IGNORECASE)
        if m:
            return _normalize_role(m.group(1))
    return None


def _legacy_player_died(raw_playerlist, name):
    return ("%s (dead)" % name) in raw_playerlist or ("%s (muerto)" % name) in raw_playerlist


def migrate_legacy_stats(uid, name):
    # Busca en stats_detail_secret_hitler (el TEXT que usa /stats <nombre>) las partidas
    # donde aparece `name` y crea filas nuevas vinculadas a `uid`. Idempotente: correrlo
    # de nuevo no duplica partidas ni filas de jugador (ON CONFLICT DO NOTHING).
    # killed_by_uid queda en NULL porque el texto legacy no registra quien mato a quien.
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, playerlist, game_endcode FROM stats_detail_secret_hitler WHERE playerlist LIKE %s;",
        ("%{0}%".format(name),)
    )
    rows = cur.fetchall()

    linked = 0
    for legacy_id, playerlist_text, game_endcode in rows:
        stripped = re.sub(r"\s*\((?:dead|muerto)\)", "", playerlist_text)
        role = _extract_legacy_role(stripped, name)
        if role is None:
            continue
        died = _legacy_player_died(playerlist_text, name)
        party = "fascista" if role in ("Fascista", "Hitler") else "liberal"
        won = (game_endcode in (1, 2)) if party == "liberal" else (game_endcode in (-1, -2))

        cur.execute(
            "SELECT id FROM stats_secret_hitler_games WHERE legacy_detail_id = %s;",
            (legacy_id,)
        )
        existing = cur.fetchone()
        if existing:
            game_id = existing[0]
        else:
            cur.execute(
                "INSERT INTO stats_secret_hitler_games(game_endcode, legacy_detail_id) "
                "VALUES (%s, %s) RETURNING id;",
                (game_endcode, legacy_id)
            )
            game_id = cur.fetchone()[0]

        cur.execute(
            "INSERT INTO stats_secret_hitler_players"
            "(game_id, uid, name, role, party, won, died, killed_by_uid) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, NULL) "
            "ON CONFLICT (game_id, uid) DO NOTHING RETURNING id;",
            (game_id, uid, name, role, party, won, died)
        )
        if cur.fetchone() is not None:
            linked += 1

    conn.commit()
    conn.close()
    return linked
