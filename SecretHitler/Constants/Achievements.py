from collections import namedtuple

# Catalogo de logros. `code` es el identificador estable que se persiste en
# achievements_secret_hitler_players.achievement_code: una vez desplegado un
# logro, nunca renombrar su `code` (perderia el vinculo con lo ya desbloqueado).
# El nombre y la descripcion de cada logro viven en los catalogos de idioma, con las
# claves logro.<code>.name y logro.<code>.desc; el emoji se puede editar libremente.
# `secreto` = True oculta nombre y descripcion en /logros mientras esta bloqueado.
# `check(ctx)` recibe un Achievements.Ctx y devuelve True/False.
Logro = namedtuple("Logro", "code emoji categoria secreto check")

CATEGORIAS = ["roles", "socialista", "muerte", "hitos", "social"]
# El titulo visible de cada categoria sale del catalogo de idioma (logro.cat.<nombre>).

MISION_IMPOSIBLE_UID = 863684947


def _roles_ganados(ctx):
    # row = (role, party, won, died, killed_by_uid, game_id)
    return {row[0] for row in ctx.history() if row[2]}


def _hace_guess_completo(ctx):
    # Quienes juegan el flujo "completo" de /guess (fascistas comunes + Hitler): los
    # liberales y, en el modo socialista, tambien los socialistas, que responden lo mismo.
    # Hitler y los fascistas ya conocen la respuesta por su rol y tienen otro flujo.
    # Mismo criterio que Game.compute_best_guessers(), que excluye por rol Hitler/Fascista.
    return ctx["role"] in ("Liberal", "Socialista")


def _check_hitler_ganador(ctx):
    return ctx["role"] == "Hitler" and ctx["won"]


def _check_hitler_incognito(ctx):
    return ctx["role"] == "Hitler" and ctx["won"] and not ctx["was_investigated"]


def _check_democracia_impecable(ctx):
    return ctx["party"] == "liberal" and ctx["won"] and ctx["game_endcode"] == 1 and ctx["dead_count"] == 0


def _check_regimen_consolidado(ctx):
    return ctx["party"] == "fascista" and ctx["won"] and ctx["game_endcode"] == -1


def _check_actor_completo(ctx):
    return {"Liberal", "Fascista", "Hitler"}.issubset(_roles_ganados(ctx))


def _check_bala_certera(ctx):
    return ctx["game_endcode"] == 2 and "Hitler" in ctx["killed_roles"]


def _check_martir(ctx):
    return ctx["died"] and ctx["party"] == "liberal" and ctx["won"]


def _check_martir_fascista(ctx):
    # Espejo fascista de "martir": lo ejecutaron y su equipo gano igual. En la practica
    # siempre es un fascista comun: si ejecutan a Hitler la partida la ganan los liberales,
    # asi que Hitler nunca puede estar muerto en una partida ganada por los fascistas.
    return ctx["died"] and ctx["party"] == "fascista" and ctx["won"]


def _check_error_de_calculo(ctx):
    return ctx["party"] == "liberal" and "Liberal" in ctx["killed_roles"]


def _check_verdugo(ctx):
    return len(ctx.kills_history()) >= 3


def _check_intocable(ctx):
    hist = ctx.history()
    return len(hist) >= 10 and all(not row[3] for row in hist)  # row[3] = died


def _check_cazador_de_hitler(ctx):
    return sum(1 for role in ctx.kills_history() if role == "Hitler") >= 2


def _check_gafe(ctx):
    return sum(1 for row in ctx.history() if row[3]) >= 3  # row[3] = died


def _check_carne_de_canon(ctx):
    return sum(1 for row in ctx.history() if row[3]) >= 5


def _check_alma_en_pena(ctx):
    return sum(1 for row in ctx.history() if row[3]) >= 10


def _check_mas_muerto_que_alee(ctx):
    return sum(1 for row in ctx.history() if row[3]) > 10  # row[3] = died


def _check_primera_partida(ctx):
    # >=1 (no ==1): si el primer registro de un jugador vino de una migracion
    # legacy (/vincularstats) o de antes de que existiera este logro, el
    # momento exacto en que history() valia 1 nunca se evaluo, y con ==1
    # el logro quedaba inalcanzable para siempre.
    return len(ctx.history()) >= 1


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


def _check_premio_consuelo(ctx):
    hist = ctx.history()
    if len(hist) < 5:
        return False
    return all(not row[2] for row in hist[-5:])  # row[2] = won


def _check_piloto_automatico(ctx):
    return ctx["won"] and ctx["auto_ja"]


def _check_me_toco_lo_que_pedi(ctx):
    return ctx["won"] and ctx["preference_rol"] != "" and ctx["preference_rol"] == ctx["role"]


def _check_lo_sabia(ctx):
    if not _hace_guess_completo(ctx):
        return False
    guess = ctx["guess"]
    return guess is not None and ctx["hitler_uid"] is not None and guess.get("hitler") == ctx["hitler_uid"]


def _check_detective(ctx):
    if not _hace_guess_completo(ctx):
        return False
    guess = ctx["guess"]
    if guess is None:
        return False
    return guess.get("hitler") == ctx["hitler_uid"] and set(guess.get("fascists", [])) == ctx["fascist_uids"]


def _check_no_debi_dudar(ctx):
    if not _hace_guess_completo(ctx):
        return False
    history = ctx["guess_history"]
    hitler_uid = ctx["hitler_uid"]
    if hitler_uid is None or len(history) < 2:
        return False
    primer_intento, segundo_intento = history[0], history[1]
    return primer_intento.get("hitler") == hitler_uid and segundo_intento.get("hitler") != hitler_uid


def _check_companeros_de_ideologia(ctx):
    # Solo Hitler: el /guess de Hitler solo pide adivinar a los compañeros fascistas.
    if ctx["role"] != "Hitler":
        return False
    guess = ctx["guess"]
    if guess is None:
        return False
    return set(guess.get("fascists", [])) == ctx["fascist_uids"]


def _check_dude_de_los_mios(ctx):
    # Solo Hitler: en el primer /guess acerto a todos sus companeros fascistas,
    # pero lo cambio por un segundo intento que ya no los tiene a todos.
    if ctx["role"] != "Hitler":
        return False
    history = ctx["guess_history"]
    if len(history) < 2:
        return False
    fascist_uids = ctx["fascist_uids"]
    primer_intento, segundo_intento = history[0], history[1]
    return (set(primer_intento.get("fascists", [])) == fascist_uids
            and set(segundo_intento.get("fascists", [])) != fascist_uids)


def _check_prediccion_certera(ctx):
    # Solo Fascista: el /guess de Fascista predice quien sera el mejor adivinando (los liberales).
    if ctx["role"] != "Fascista":
        return False
    guess = ctx["guess"]
    if guess is None:
        return False
    predicted = guess.get("predicted")
    if predicted is None:
        return False
    return predicted in ctx["best_guessers"]


DEADLINE_PRESIDENCIA = 7  # currentround es 0-indexed: 7 == arranco la 8va presidencia


def _check_detective_precoz(ctx):
    # Como detective, pero el /guess definitivo tiene que haber quedado
    # registrado antes de que arranque la 8va presidencia (currentround < 7).
    if not _hace_guess_completo(ctx):
        return False
    guess = ctx["guess"]
    if guess is None:
        return False
    guess_round = guess.get("round")
    if guess_round is None or guess_round >= DEADLINE_PRESIDENCIA:
        return False
    return guess.get("hitler") == ctx["hitler_uid"] and set(guess.get("fascists", [])) == ctx["fascist_uids"]


def _check_companeros_de_ideologia_precoz(ctx):
    if ctx["role"] != "Hitler":
        return False
    guess = ctx["guess"]
    if guess is None:
        return False
    guess_round = guess.get("round")
    if guess_round is None or guess_round >= DEADLINE_PRESIDENCIA:
        return False
    return set(guess.get("fascists", [])) == ctx["fascist_uids"]


def _check_prediccion_certera_precoz(ctx):
    if ctx["role"] != "Fascista":
        return False
    guess = ctx["guess"]
    if guess is None:
        return False
    guess_round = guess.get("round")
    if guess_round is None or guess_round >= DEADLINE_PRESIDENCIA:
        return False
    predicted = guess.get("predicted")
    if predicted is None:
        return False
    return predicted in ctx["best_guessers"]


def _check_mision_imposible(ctx):
    # ctx["mision_imposible_party"] es None si MISION_IMPOSIBLE_UID no jugo
    # esta partida, o si el jugador evaluado es el mismo MISION_IMPOSIBLE_UID.
    return ctx["won"] and ctx["mision_imposible_party"] is not None and ctx["mision_imposible_party"] == ctx["party"]


# --- Expansion Socialista (ver Game.modo) ---

PARTIDAS_CAMARADA = 5  # partidas como Socialista que pide "Camarada de hierro"


def _check_jugo_socialista(ctx):
    return ctx["es_modo_socialista"]


def _check_socialista_ganador(ctx):
    # party es party_efectiva(): incluye a los reclutados y deja afuera a Hitler,
    # que gana con los fascistas aunque tenga la carta socialista.
    return ctx["party"] == "socialista" and ctx["won"]


def _check_converso_ganador(ctx):
    return ctx["was_recruited"] and ctx["party"] == "socialista" and ctx["won"]


def _check_revolucion_pura(ctx):
    # Ganaron sin usar el Reclutamiento sobre nadie (ni siquiera fallido sobre Hitler),
    # asi que solo lo pueden conseguir los socialistas de origen.
    return ctx["party"] == "socialista" and ctx["won"] and not ctx["recruited_uids"]


def _check_socialista_martir(ctx):
    return ctx["died"] and ctx["party"] == "socialista" and ctx["won"]


def _check_reclutamos_a_hitler(ctx):
    # Para el equipo socialista de esa partida: gastaron un Reclutamiento en Hitler, que
    # sigue siendo fascista. Hitler mismo queda afuera (su party efectiva es fascista).
    return ctx["party"] == "socialista" and ctx["hitler_reclutado"]


def _check_hitler_reclutado_ganador(ctx):
    return ctx["role"] == "Hitler" and ctx["was_recruited"] and ctx["won"]


def _check_tres_frentes(ctx):
    return ctx["es_modo_socialista"] and ctx["won"] and ctx["party"] != "socialista"


def _check_ideologo_completo(ctx):
    return {"Liberal", "Fascista", "Hitler", "Socialista"}.issubset(_roles_ganados(ctx))


def _check_camarada_de_hierro(ctx):
    # row[0] = role: cuenta los socialistas de origen, no los reclutados (que conservan su rol).
    return sum(1 for row in ctx.history() if row[0] == "Socialista") >= PARTIDAS_CAMARADA


def _check_purga_roja(ctx):
    return "Socialista" in ctx["killed_roles"]


def _check_mvp_una_vez(ctx):
    return ctx.mvp_count() >= 1


def _check_mvp_cinco_veces(ctx):
    return ctx.mvp_count() >= 5


def _check_mvp_mas_de_diez(ctx):
    return ctx.mvp_count() > 10


LOGROS = [
    # Roles y victorias
    Logro("hitler_ganador", "🎩", "roles", False, _check_hitler_ganador),
    Logro("hitler_incognito", "🕵️", "roles", False, _check_hitler_incognito),
    Logro("democracia_impecable", "🕊", "roles", False, _check_democracia_impecable),
    Logro("regimen_consolidado", "🔥", "roles", False, _check_regimen_consolidado),
    Logro("actor_completo", "🎭", "roles", False, _check_actor_completo),
    Logro("lo_sabia", "🔮", "roles", False, _check_lo_sabia),
    Logro("detective", "🔍", "roles", False, _check_detective),
    Logro("no_debi_dudar", "😩", "roles", False, _check_no_debi_dudar),
    Logro("companeros_de_ideologia", "🥸", "roles", False, _check_companeros_de_ideologia),
    Logro("dude_de_los_mios", "😬", "roles", False, _check_dude_de_los_mios),
    Logro("prediccion_certera", "👁️", "roles", False, _check_prediccion_certera),
    Logro("detective_precoz", "⏱️", "roles", False, _check_detective_precoz),
    Logro("companeros_de_ideologia_precoz", "⏱️", "roles", False, _check_companeros_de_ideologia_precoz),
    Logro("prediccion_certera_precoz", "⏱️", "roles", False, _check_prediccion_certera_precoz),

    # Expansion Socialista
    Logro("jugo_socialista", "☭", "socialista", False, _check_jugo_socialista),
    Logro("socialista_ganador", "🚩", "socialista", False, _check_socialista_ganador),
    Logro("converso_ganador", "✊", "socialista", False, _check_converso_ganador),
    Logro("revolucion_pura", "🌹", "socialista", False, _check_revolucion_pura),
    Logro("socialista_martir", "⚒", "socialista", False, _check_socialista_martir),
    Logro("tres_frentes", "🔺", "socialista", False, _check_tres_frentes),
    Logro("ideologo_completo", "📚", "socialista", False, _check_ideologo_completo),
    Logro("camarada_de_hierro", "⭐", "socialista", False, _check_camarada_de_hierro),
    Logro("purga_roja", "🧹", "socialista", False, _check_purga_roja),
    Logro("reclutamos_a_hitler", "🤝", "socialista", True, _check_reclutamos_a_hitler),
    Logro("hitler_reclutado_ganador", "🕳", "socialista", True, _check_hitler_reclutado_ganador),

    # Muerte y ejecuciones
    Logro("bala_certera", "🗡", "muerte", False, _check_bala_certera),
    Logro("martir", "☠", "muerte", False, _check_martir),
    Logro("martir_fascista", "⚱️", "muerte", False, _check_martir_fascista),
    Logro("error_de_calculo", "🤦", "muerte", True, _check_error_de_calculo),
    Logro("verdugo", "🔪", "muerte", False, _check_verdugo),
    Logro("intocable", "🛡", "muerte", False, _check_intocable),
    Logro("cazador_de_hitler", "🎯", "muerte", False, _check_cazador_de_hitler),
    Logro("gafe", "💀", "muerte", False, _check_gafe),
    Logro("carne_de_canon", "⚰️", "muerte", False, _check_carne_de_canon),
    Logro("alma_en_pena", "👻", "muerte", False, _check_alma_en_pena),
    Logro("mas_muerto_que_alee", "🪦", "muerte", False, _check_mas_muerto_que_alee),

    # Hitos
    Logro("primera_partida", "🎬", "hitos", False, _check_primera_partida),
    Logro("veterano", "🏅", "hitos", False, _check_veterano),
    Logro("leyenda", "👑", "hitos", False, _check_leyenda),
    Logro("en_racha", "🔥", "hitos", False, _check_en_racha),
    Logro("imparable", "⚡", "hitos", False, _check_imparable),
    Logro("premio_consuelo", "🍦", "hitos", True, _check_premio_consuelo),

    # Social / comportamiento
    Logro("piloto_automatico", "🤖", "social", False, _check_piloto_automatico),
    Logro("me_toco_lo_que_pedi", "🎲", "social", False, _check_me_toco_lo_que_pedi),
    Logro("mvp_una_vez", "🌟", "social", False, _check_mvp_una_vez),
    Logro("mvp_cinco_veces", "🏆", "social", False, _check_mvp_cinco_veces),
    Logro("mvp_mas_de_diez", "💫", "social", False, _check_mvp_mas_de_diez),
    Logro("mision_imposible", "🕶️", "social", True, _check_mision_imposible),
]

LOGROS_BY_CODE = {logro.code: logro for logro in LOGROS}
