import logging as log
import os
import urllib.parse

import psycopg2

from SecretHitler.Constants.Achievements import LOGROS, LOGROS_BY_CODE, CATEGORIAS, CATEGORIA_TITULOS

# DB Connection (mismo patron que StatsExtended.py / MainController.py)
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


class Ctx(dict):
    # dict con los datos de un jugador al final de una partida, mas acceso
    # perezoso a su historial (para no pagar queries extra en logros que
    # solo miran la partida actual).
    def __init__(self, cur, uid, **kwargs):
        super().__init__(uid=uid, **kwargs)
        self._cur = cur
        self._uid = uid
        self._history = None
        self._kills_history = None

    def history(self):
        # Filas (role, party, won, died, killed_by_uid, game_id) de todas las
        # partidas del jugador, en orden. Corre en la misma transaccion que
        # el INSERT de la partida actual, asi que ya la incluye.
        if self._history is None:
            self._cur.execute(
                "SELECT role, party, won, died, killed_by_uid, game_id "
                "FROM stats_secret_hitler_players WHERE uid = %s ORDER BY game_id;",
                (self._uid,)
            )
            self._history = self._cur.fetchall()
        return self._history

    def kills_history(self):
        # Rol de cada jugador que este uid ejecuto, a lo largo de su historial.
        if self._kills_history is None:
            self._cur.execute(
                "SELECT role FROM stats_secret_hitler_players WHERE killed_by_uid = %s;",
                (self._uid,)
            )
            self._kills_history = [row[0] for row in self._cur.fetchall()]
        return self._kills_history


def build_context(cur, game, game_endcode, uid, player):
    won_liberal = game_endcode in (1, 2)
    won_fascist = game_endcode in (-1, -2)
    if player.party == "liberal":
        won = won_liberal
    elif player.party == "fascista":
        won = won_fascist
    else:
        won = False

    killed_roles = [
        getattr(p, "role", None)
        for p in game.playerlist.values()
        if getattr(p, "killed_by_uid", None) == uid
    ]

    hitler_player = game.get_hitler()
    # El ultimo intento de /guess (maximo 2) es el definitivo, el que cuenta para logros.
    guess_history = getattr(game, "guesses", {}).get(uid) or []

    return Ctx(
        cur, uid,
        role=player.role,
        party=player.party,
        won=won,
        died=player.is_dead,
        killed_by_uid=getattr(player, "killed_by_uid", None),
        killed_roles=killed_roles,
        game_endcode=game_endcode,
        num_players=game.board.num_players,
        liberal_track=game.board.state.liberal_track,
        fascist_track=game.board.state.fascist_track,
        dead_count=game.board.state.dead,
        was_investigated=getattr(player, "was_investigated", False),
        auto_ja=getattr(player, "auto_ja", False),
        preference_rol=getattr(player, "preference_rol", ""),
        guess=guess_history[-1] if guess_history else None,
        hitler_uid=hitler_player.uid if hitler_player else None,
        fascist_uids=frozenset(f.uid for f in game.get_fascists()),
    )


def evaluate_and_store(cur, game, game_endcode, game_id):
    # Corre dentro de la transaccion de StatsExtended.save_extended_game_stats,
    # despues de insertar las filas de stats_secret_hitler_players y antes del
    # commit. Nunca propaga excepciones: un logro roto no debe tumbar el guardado
    # de estadisticas ni el fin de partida.
    nuevos_por_uid = {}
    for uid, player in game.playerlist.items():
        try:
            ctx = build_context(cur, game, game_endcode, uid, player)
        except Exception as e:
            log.error("Achievements.build_context failed for uid %s: %s" % (uid, str(e)))
            continue

        nuevos = []
        for logro in LOGROS:
            try:
                if not logro.check(ctx):
                    continue
                cur.execute(
                    "INSERT INTO achievements_secret_hitler_players(uid, achievement_code, game_id) "
                    "VALUES (%s, %s, %s) ON CONFLICT (uid, achievement_code) DO NOTHING RETURNING id;",
                    (uid, logro.code, game_id)
                )
                if cur.fetchone() is not None:
                    nuevos.append(logro)
            except Exception as e:
                log.error("Achievements check '%s' failed for uid %s: %s" % (logro.code, uid, str(e)))

        if nuevos:
            nuevos_por_uid[uid] = nuevos

    return nuevos_por_uid


def get_unlocked_codes(uid):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT achievement_code FROM achievements_secret_hitler_players WHERE uid = %s;",
            (uid,)
        )
        return {row[0] for row in cur.fetchall()}
    finally:
        conn.close()


def format_unlock_announcement(nuevos_por_uid, game, max_lineas=6):
    if not nuevos_por_uid:
        return None

    lineas = []
    total = 0
    for uid, logros in nuevos_por_uid.items():
        player = game.playerlist.get(uid)
        name = (player.name if player is not None else str(uid)).replace("_", " ")
        for logro in logros:
            total += 1
            if len(lineas) < max_lineas:
                lineas.append("%s desbloqueó %s *%s*" % (name, logro.emoji, logro.name))

    texto = "🏆 *¡Nuevos logros!*\n\n" + "\n".join(lineas)
    if total > len(lineas):
        texto += "\n...y %d logro%s más (/logros)" % (total - len(lineas), "" if total - len(lineas) == 1 else "s")
    texto += "\n\nMirá todos los tuyos con /logros"
    return texto


def format_logros_message(uid, name):
    unlocked = get_unlocked_codes(uid)

    texto = "🏆 *Logros de %s* (%d/%d)\n" % (name.replace("_", " "), len(unlocked), len(LOGROS))
    for categoria in CATEGORIAS:
        logros_categoria = [l for l in LOGROS if l.categoria == categoria]
        if not logros_categoria:
            continue
        texto += "\n*%s*\n" % CATEGORIA_TITULOS[categoria]
        for logro in logros_categoria:
            if logro.code in unlocked:
                texto += "✅ %s *%s* — %s\n" % (logro.emoji, logro.name, logro.description)
            elif logro.secreto:
                texto += "🔒 ❓ ??? — Logro secreto\n"
            else:
                texto += "🔒 %s %s — %s\n" % (logro.emoji, logro.name, logro.description)
    return texto
