from collections import namedtuple

# Catalogo de logros. `code` es el identificador estable que se persiste en
# achievements_secret_hitler_players.achievement_code: una vez desplegado un
# logro, nunca renombrar su `code` (perderia el vinculo con lo ya desbloqueado).
# `name`/`description`/`emoji` se pueden editar libremente.
# `secreto` = True oculta nombre y descripcion en /logros mientras esta bloqueado.
# `check(ctx)` recibe un Achievements.Ctx y devuelve True/False.
Logro = namedtuple("Logro", "code name description emoji categoria secreto check")

CATEGORIAS = ["roles", "muerte", "hitos", "social"]
CATEGORIA_TITULOS = {
    "roles": "Roles y victorias",
    "muerte": "Muerte y ejecuciones",
    "hitos": "Hitos",
    "social": "Social",
}


def _check_hitler_ganador(ctx):
    return ctx["role"] == "Hitler" and ctx["won"]


def _check_hitler_incognito(ctx):
    return ctx["role"] == "Hitler" and ctx["won"] and not ctx["was_investigated"]


def _check_democracia_impecable(ctx):
    return ctx["party"] == "liberal" and ctx["won"] and ctx["game_endcode"] == 1 and ctx["dead_count"] == 0


def _check_regimen_consolidado(ctx):
    return ctx["party"] == "fascista" and ctx["won"] and ctx["game_endcode"] == -1


def _check_actor_completo(ctx):
    roles_ganados = {row[0] for row in ctx.history() if row[2]}  # row = (role, party, won, died, killed_by_uid, game_id)
    return {"Liberal", "Fascista", "Hitler"}.issubset(roles_ganados)


def _check_bala_certera(ctx):
    return ctx["game_endcode"] == 2 and "Hitler" in ctx["killed_roles"]


def _check_martir(ctx):
    return ctx["died"] and ctx["party"] == "liberal" and ctx["won"]


def _check_error_de_calculo(ctx):
    return ctx["party"] == "liberal" and "Liberal" in ctx["killed_roles"]


def _check_verdugo(ctx):
    return len(ctx.kills_history()) >= 3


def _check_intocable(ctx):
    hist = ctx.history()
    return len(hist) >= 10 and all(not row[3] for row in hist)  # row[3] = died


def _check_cazador_de_hitler(ctx):
    return sum(1 for role in ctx.kills_history() if role == "Hitler") >= 2


def _check_primera_partida(ctx):
    return len(ctx.history()) == 1


def _check_veterano(ctx):
    return len(ctx.history()) >= 25


def _check_leyenda(ctx):
    return len(ctx.history()) >= 100


def _check_en_racha(ctx):
    hist = ctx.history()
    if len(hist) < 3:
        return False
    return all(row[2] for row in hist[-3:])  # row[2] = won


def _check_imparable(ctx):
    hist = ctx.history()
    if len(hist) < 5:
        return False
    return all(row[2] for row in hist[-5:])


def _check_piloto_automatico(ctx):
    return ctx["won"] and ctx["auto_ja"]


def _check_me_toco_lo_que_pedi(ctx):
    return ctx["won"] and ctx["preference_rol"] != "" and ctx["preference_rol"] == ctx["role"]


def _check_lo_sabia(ctx):
    guess = ctx["guess"]
    return guess is not None and ctx["hitler_uid"] is not None and guess.get("hitler") == ctx["hitler_uid"]


def _check_detective(ctx):
    guess = ctx["guess"]
    if guess is None:
        return False
    return guess.get("hitler") == ctx["hitler_uid"] and set(guess.get("fascists", [])) == ctx["fascist_uids"]


def _check_no_debi_dudar(ctx):
    history = ctx["guess_history"]
    hitler_uid = ctx["hitler_uid"]
    if hitler_uid is None or len(history) < 2:
        return False
    primer_intento, segundo_intento = history[0], history[1]
    return primer_intento.get("hitler") == hitler_uid and segundo_intento.get("hitler") != hitler_uid


def _check_mvp_una_vez(ctx):
    return ctx.mvp_count() >= 1


def _check_mvp_cinco_veces(ctx):
    return ctx.mvp_count() >= 5


def _check_mvp_mas_de_diez(ctx):
    return ctx.mvp_count() > 10


LOGROS = [
    # Roles y victorias
    Logro("hitler_ganador", "Canciller Supremo", "Ganaste una partida siendo Hitler.",
          "🎩", "roles", False, _check_hitler_ganador),
    Logro("hitler_incognito", "Escondido a plena vista", "Ganaste como Hitler sin ser investigado nunca.",
          "🕵️", "roles", False, _check_hitler_incognito),
    Logro("democracia_impecable", "Democracia impecable", "Ganaste como liberal con 5 políticas liberales y nadie ejecutado.",
          "🕊", "roles", False, _check_democracia_impecable),
    Logro("regimen_consolidado", "Régimen consolidado", "Ganaste como fascista promulgando 6 políticas fascistas.",
          "🔥", "roles", False, _check_regimen_consolidado),
    Logro("actor_completo", "Actor completo", "Ganaste al menos una vez como Liberal, Fascista y Hitler.",
          "🎭", "roles", False, _check_actor_completo),
    Logro("lo_sabia", "¡Lo sabía!", "Adivinaste correctamente quién era Hitler con /guess.",
          "🔮", "roles", False, _check_lo_sabia),
    Logro("detective", "Detective", "Adivinaste correctamente a todos los fascistas y a Hitler con /guess.",
          "🔍", "roles", False, _check_detective),
    Logro("no_debi_dudar", "No debí dudar", "En tu primer /guess acertaste quién era Hitler, pero en el segundo te equivocaste.",
          "😩", "roles", False, _check_no_debi_dudar),

    # Muerte y ejecuciones
    Logro("bala_certera", "Bala certera", "Ejecutaste a Hitler y los liberales ganaron.",
          "🗡", "muerte", False, _check_bala_certera),
    Logro("martir", "Mártir de la República", "Te ejecutaron siendo liberal y tu equipo ganó igual.",
          "☠", "muerte", False, _check_martir),
    Logro("error_de_calculo", "Error de cálculo", "Siendo liberal, ejecutaste a otro liberal.",
          "🤦", "muerte", True, _check_error_de_calculo),
    Logro("verdugo", "Verdugo", "Ejecutaste a 3 jugadores en total.",
          "🔪", "muerte", False, _check_verdugo),
    Logro("intocable", "Intocable", "Jugaste 10 partidas sin que te ejecuten nunca.",
          "🛡", "muerte", False, _check_intocable),
    Logro("cazador_de_hitler", "Cazador de Hitler", "Ejecutaste a Hitler en 2 partidas distintas.",
          "🎯", "muerte", False, _check_cazador_de_hitler),

    # Hitos
    Logro("primera_partida", "Primera vez", "Jugaste tu primera partida.",
          "🎬", "hitos", False, _check_primera_partida),
    Logro("veterano", "Veterano", "Jugaste 25 partidas.",
          "🏅", "hitos", False, _check_veterano),
    Logro("leyenda", "Leyenda", "Jugaste 100 partidas.",
          "👑", "hitos", False, _check_leyenda),
    Logro("en_racha", "En racha", "Ganaste 3 partidas seguidas.",
          "🔥", "hitos", False, _check_en_racha),
    Logro("imparable", "Imparable", "Ganaste 5 partidas seguidas.",
          "⚡", "hitos", False, _check_imparable),

    # Social / comportamiento
    Logro("piloto_automatico", "Piloto automático", "Ganaste una partida con el voto automático Ja activado.",
          "🤖", "social", False, _check_piloto_automatico),
    Logro("me_toco_lo_que_pedi", "Me tocó lo que pedí", "Te tocó el rol que pediste y ganaste.",
          "🎲", "social", False, _check_me_toco_lo_que_pedi),
    Logro("mvp_una_vez", "MVP", "Te votaron como MVP de la partida.",
          "🌟", "social", False, _check_mvp_una_vez),
    Logro("mvp_cinco_veces", "MVP Recurrente", "Te votaron como MVP en 5 partidas.",
          "🏆", "social", False, _check_mvp_cinco_veces),
    Logro("mvp_mas_de_diez", "El MVP de Siempre", "Te votaron como MVP en más de 10 partidas.",
          "💫", "social", False, _check_mvp_mas_de_diez),
]

LOGROS_BY_CODE = {logro.code: logro for logro in LOGROS}
