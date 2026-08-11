#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging as log
import re

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from Utils import get_game, save, simple_choose_buttons, player_call
from Constants.Config import ADMIN
from Flip7.Boardgamebox.Game import Game
from Flip7.Constants.Cards import card_type, card_display, NUMEROS_PARA_FLIP7, FLIP7_BONUS, PUNTAJE_OBJETIVO

import GamesController

log.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=log.INFO)
logger = log.getLogger(__name__)


async def init_game(bot, game):
    try:
        log.info("Flip7 init_game called")
        game.shuffle_player_sequence()
        await bot.send_message(
            game.cid,
            "🎴 *¡Flip 7 ha comenzado!*\n\n"
            "En tu turno elegí *Pedir carta* o *Plantarte*. Si repetís un número, ¡revientas "
            "y perdés los puntos de la ronda! Juntá *{}* números distintos para lograr "
            "*¡Flip 7!* y ganar un bonus de *{}* puntos.\n"
            "Gana quien primero llegue a *{}* puntos al final de una ronda.".format(
                NUMEROS_PARA_FLIP7, FLIP7_BONUS, PUNTAJE_OBJETIVO
            ),
            parse_mode=ParseMode.MARKDOWN
        )
        await start_round(bot, game)
    except Exception as e:
        logger.error(f"Flip7 init_game error: {e}")
        await bot.send_message(ADMIN[0], f"Flip7 init_game error: {e}")
        raise


async def start_round(bot, game):
    st = game.board.state
    st.fase_actual = "Jugando"
    st.forzado_uid = None
    st.forzado_restantes = 0
    st.cola_flip_three = []
    st.accion_pendiente = None

    for player in game.player_sequence:
        if player.tiene_segunda_oportunidad:
            game.board.discards.append("SECOND_CHANCE")
        game.board.discards += player.numeros
        game.board.discards += player.modificadores
        player.reset_ronda()

    st.player_counter = st.player_counter % len(game.player_sequence)
    st.active_player = game.player_sequence[st.player_counter]

    await bot.send_message(
        game.cid,
        "🎴 *Ronda {}* — Empieza {}.".format(st.ronda, player_call(st.active_player)),
        parse_mode=ParseMode.MARKDOWN
    )
    await bot.send_message(game.cid, game.board.print_board(game), parse_mode=ParseMode.MARKDOWN)
    await save(bot, game.cid)
    await prompt_turn(bot, game)


async def prompt_turn(bot, game):
    st = game.board.state
    player = st.active_player
    if player is None or player.estado_ronda != "jugando":
        await avanzar_turno(bot, game)
        return
    opciones = {"hit": "🃏 Pedir carta", "stay": "✋ Plantarse"}
    await simple_choose_buttons(
        bot, game.cid, player.uid, game.cid, "chooseturnF7",
        "{}, ¿pedís carta o te plantás?".format(player_call(player)),
        opciones
    )


def siguiente_jugador_activo(game):
    st = game.board.state
    n = len(game.player_sequence)
    for i in range(1, n + 1):
        idx = (st.player_counter + i) % n
        candidato = game.player_sequence[idx]
        if candidato.estado_ronda == "jugando":
            return candidato
    return None


def iniciar_o_encolar_flip_three(game, target_uid):
    st = game.board.state
    if st.forzado_uid == target_uid:
        st.forzado_restantes += 3
    elif st.forzado_uid is not None:
        st.cola_flip_three.append(target_uid)
    else:
        st.forzado_uid = target_uid
        st.forzado_restantes = 3


async def hit(bot, game, player):
    st = game.board.state
    carta = game.board.robar_carta()
    if st.forzado_uid == player.uid:
        st.forzado_restantes -= 1

    await bot.send_message(
        game.cid,
        "{} vuelve la carta: *{}*".format(player_call(player), card_display(carta)),
        parse_mode=ParseMode.MARKDOWN
    )

    tipo = card_type(carta)
    if tipo == "number":
        await resolver_numero(bot, game, player, carta)
    elif tipo == "modifier":
        player.modificadores.append(carta)
        await bot.send_message(
            game.cid,
            "{} suma el modificador *{}*. Puntaje de ronda: *{}*.".format(
                player.name, card_display(carta), player.puntaje_ronda()
            ),
            parse_mode=ParseMode.MARKDOWN
        )
        await continuar_tras_carta(bot, game, player)
    elif carta == "SECOND_CHANCE":
        await resolver_segunda_oportunidad(bot, game, player)
    elif carta == "FREEZE":
        game.board.discards.append(carta)
        await pedir_objetivo_accion(bot, game, player, "FREEZE")
    elif carta == "FLIP_THREE":
        game.board.discards.append(carta)
        await pedir_objetivo_accion(bot, game, player, "FLIP_THREE")


async def resolver_numero(bot, game, player, carta):
    if carta in player.numeros:
        if player.tiene_segunda_oportunidad:
            player.tiene_segunda_oportunidad = False
            game.board.discards.append("SECOND_CHANCE")
            game.board.discards.append(carta)
            await bot.send_message(
                game.cid,
                "🍀 {} repitió el {} pero se salva gracias a su *Segunda Oportunidad* "
                "(se descartan ambas cartas).".format(player.name, carta),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            game.board.discards.append(carta)
            player.estado_ronda = "reventado"
            await bot.send_message(
                game.cid,
                "💥 {} repitió el {} y *revienta*. Pierde los puntos de la ronda.".format(player.name, carta),
                parse_mode=ParseMode.MARKDOWN
            )
    else:
        player.numeros.append(carta)
        if len(player.numeros) >= NUMEROS_PARA_FLIP7:
            player.estado_ronda = "flip7"
            await bot.send_message(
                game.cid,
                "🎉 *¡FLIP 7!* {} consiguió {} números distintos y gana un bonus de *{}* "
                "puntos. ¡La ronda termina!".format(player.name, NUMEROS_PARA_FLIP7, FLIP7_BONUS),
                parse_mode=ParseMode.MARKDOWN
            )
    await continuar_tras_carta(bot, game, player)


async def resolver_segunda_oportunidad(bot, game, player):
    st = game.board.state
    if not player.tiene_segunda_oportunidad:
        player.tiene_segunda_oportunidad = True
        await bot.send_message(
            game.cid,
            "🍀 {} se queda con una *Segunda Oportunidad*.".format(player.name),
            parse_mode=ParseMode.MARKDOWN
        )
        await continuar_tras_carta(bot, game, player)
        return

    candidatos = [
        p for p in game.player_sequence
        if p.uid != player.uid and p.estado_ronda == "jugando" and not p.tiene_segunda_oportunidad
    ]
    if not candidatos:
        game.board.discards.append("SECOND_CHANCE")
        await bot.send_message(
            game.cid,
            "🍀 {} ya tenía una Segunda Oportunidad y no hay a quién dársela: se descarta.".format(player.name),
            parse_mode=ParseMode.MARKDOWN
        )
        await continuar_tras_carta(bot, game, player)
        return

    st.accion_pendiente = {"tipo": "SECOND_CHANCE_GIVE", "drawer_uid": player.uid}
    opciones = {str(p.uid): p.name for p in candidatos}
    await save(bot, game.cid)
    await simple_choose_buttons(
        bot, game.cid, player.uid, game.cid, "choosescgiveF7",
        "{}, ya tenés una Segunda Oportunidad. ¿A quién se la das?".format(player_call(player)),
        opciones
    )


async def pedir_objetivo_accion(bot, game, player, tipo_accion):
    st = game.board.state
    st.accion_pendiente = {"tipo": tipo_accion, "drawer_uid": player.uid}
    candidatos = [p for p in game.player_sequence if p.estado_ronda == "jugando"]
    opciones = {str(p.uid): ("Vos mismo" if p.uid == player.uid else p.name) for p in candidatos}
    if tipo_accion == "FREEZE":
        etiqueta, comando = "❄️ Congelar", "choosefreezeF7"
    else:
        etiqueta, comando = "🔄 Flip Three", "choosef3F7"
    await save(bot, game.cid)
    await simple_choose_buttons(
        bot, game.cid, player.uid, game.cid, comando,
        "{}, elegí a quién aplicarle *{}*:".format(player_call(player), etiqueta),
        opciones
    )


async def continuar_tras_carta(bot, game, player):
    st = game.board.state
    await save(bot, game.cid)

    if st.fase_actual != "Jugando":
        return

    if any(p.estado_ronda == "flip7" for p in game.player_sequence):
        await finalizar_ronda(bot, game)
        return

    if st.forzado_uid == player.uid and player.estado_ronda == "jugando" and st.forzado_restantes > 0:
        await ejecutar_una_carta_forzada(bot, game)
        return

    if st.forzado_uid == player.uid:
        st.forzado_uid = None
        st.forzado_restantes = 0

    await avanzar_turno(bot, game)


async def ejecutar_una_carta_forzada(bot, game):
    st = game.board.state
    player = game.playerlist[st.forzado_uid]
    await hit(bot, game, player)


async def avanzar_turno(bot, game):
    st = game.board.state

    if st.forzado_uid is not None:
        forzado = game.playerlist.get(st.forzado_uid)
        if forzado and forzado.estado_ronda == "jugando" and st.forzado_restantes > 0:
            await ejecutar_una_carta_forzada(bot, game)
            return
        st.forzado_uid = None
        st.forzado_restantes = 0

    if st.cola_flip_three:
        target_uid = st.cola_flip_three.pop(0)
        target = game.playerlist.get(target_uid)
        if target and target.estado_ronda == "jugando":
            st.forzado_uid = target_uid
            st.forzado_restantes = 3
            await bot.send_message(
                game.cid,
                "🔄 Le toca resolver un *Flip Three* pendiente a {}.".format(player_call(target)),
                parse_mode=ParseMode.MARKDOWN
            )
            await save(bot, game.cid)
            await ejecutar_una_carta_forzada(bot, game)
            return
        else:
            await avanzar_turno(bot, game)
            return

    siguiente = siguiente_jugador_activo(game)
    if siguiente is None:
        await finalizar_ronda(bot, game)
        return

    st.active_player = siguiente
    st.player_counter = game.player_sequence.index(siguiente)
    await save(bot, game.cid)
    await prompt_turn(bot, game)


async def finalizar_ronda(bot, game):
    st = game.board.state
    if st.fase_actual != "Jugando":
        return
    st.fase_actual = "RondaFinalizada"

    for p in game.player_sequence:
        if p.estado_ronda == "jugando":
            p.estado_ronda = "plantado"

    resumen = ["🏁 *Fin de la ronda {}*".format(st.ronda)]
    for p in game.player_sequence:
        puntos = p.puntaje_ronda()
        p.puntaje_total += puntos
        resumen.append("• {}: +{} → *{}*".format(p.name, puntos, p.puntaje_total))
    await bot.send_message(game.cid, "\n".join(resumen), parse_mode=ParseMode.MARKDOWN)
    await save(bot, game.cid)

    ganadores = [p for p in game.player_sequence if p.puntaje_total >= PUNTAJE_OBJETIVO]
    if ganadores:
        await finalizar_juego(bot, game, ganadores)
        return

    st.ronda += 1
    st.player_counter = (st.player_counter + 1) % len(game.player_sequence)
    await start_round(bot, game)


async def finalizar_juego(bot, game, ganadores):
    st = game.board.state
    st.fase_actual = "Finalizado"
    mejor_puntaje = max(p.puntaje_total for p in ganadores)
    empatados = [p for p in ganadores if p.puntaje_total == mejor_puntaje]
    st.ganadores_uids = [p.uid for p in empatados]
    await save(bot, game.cid)

    nombres = " y ".join(p.name for p in empatados)
    resumen = "\n".join(
        "• {}: {}".format(p.name, p.puntaje_total)
        for p in sorted(game.player_sequence, key=lambda x: -x.puntaje_total)
    )
    await bot.send_message(
        game.cid,
        "🏆 *¡{} gana Flip 7!*\n\n*Resultado final:*\n{}".format(nombres, resumen),
        parse_mode=ParseMode.MARKDOWN
    )
    await continue_playing(bot, game)


async def continue_playing(bot, game):
    opciones_botones = {
        "Nuevo": "Nueva partida con nuevos jugadores",
        "Mismos": "Misma partida, mismos jugadores",
    }
    await simple_choose_buttons(
        bot, game.cid, 1, game.cid,
        "chooseendF7",
        "¿Quieren seguir jugando?",
        opciones_botones,
    )


async def callback_finish_game_buttons_f7(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    try:
        regex = re.search(r"(-[0-9]*)\*chooseendF7\*(.*)\*([0-9]*)", callback.data)
        cid, opcion, uid = int(regex.group(1)), regex.group(2), int(regex.group(3))
        mensaje_edit = f"Has elegido: {opcion}"
        try:
            await bot.edit_message_text(mensaje_edit, cid, callback.message.message_id)
        except Exception:
            await bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)

        game = get_game(cid)
        groupName, tipo, modo = game.groupName, game.tipo, game.modo
        players = game.playerlist.copy()

        new_game = Game(cid, uid, groupName, tipo, modo)
        GamesController.games[cid] = new_game

        if opcion == "Nuevo":
            await bot.send_message(
                cid,
                "Cada jugador puede unirse con /join. El iniciador puede escribir /startgame cuando todos estén listos.",
            )
            return

        for player in players.values():
            player.puntaje_total = 0
            player.reset_ronda()
        new_game.playerlist = players
        new_game.create_board()
        await init_game(bot, new_game)
    except Exception as e:
        await bot.send_message(ADMIN[0], f'callback_finish_game_buttons_f7 error: {e}')
        await bot.send_message(ADMIN[0], callback.data)


async def callback_choose_turn(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    try:
        regex = re.search(r"(-[0-9]*)\*chooseturnF7\*(hit|stay)\*([0-9]*)", callback.data)
        cid, opcion, uid = int(regex.group(1)), regex.group(2), int(regex.group(3))
        actor_uid = callback.from_user.id

        game = get_game(cid)
        if not game or game.tipo != "Flip7" or not game.board:
            return
        st = game.board.state
        if actor_uid != uid or st.active_player is None or st.active_player.uid != actor_uid:
            return
        player = game.playerlist.get(actor_uid)
        if not player or player.estado_ronda != "jugando":
            return

        try:
            await bot.edit_message_text(
                "{} eligió: {}".format(player.name, "Pedir carta" if opcion == "hit" else "Plantarse"),
                cid, callback.message.message_id
            )
        except Exception:
            pass

        if opcion == "stay":
            player.estado_ronda = "plantado"
            await bot.send_message(
                game.cid,
                "✋ {} se planta con *{}* puntos.".format(player.name, player.puntaje_ronda()),
                parse_mode=ParseMode.MARKDOWN
            )
            await continuar_tras_carta(bot, game, player)
        else:
            await hit(bot, game, player)
    except Exception as e:
        await bot.send_message(ADMIN[0], f'callback_choose_turn (Flip7) error: {e}')
        await bot.send_message(ADMIN[0], callback.data)


async def callback_choose_freeze_target(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    try:
        regex = re.search(r"(-[0-9]*)\*choosefreezeF7\*([0-9]*)\*([0-9]*)", callback.data)
        cid, target_uid, uid = int(regex.group(1)), int(regex.group(2)), int(regex.group(3))
        actor_uid = callback.from_user.id

        game = get_game(cid)
        if not game or game.tipo != "Flip7" or not game.board:
            return
        st = game.board.state
        if actor_uid != uid or not st.accion_pendiente or st.accion_pendiente.get("drawer_uid") != actor_uid:
            return

        target = game.playerlist.get(target_uid)
        drawer = game.playerlist.get(actor_uid)
        if not target or not drawer:
            return
        st.accion_pendiente = None

        try:
            await bot.edit_message_text("❄️ Elegiste congelar a {}".format(target.name), cid, callback.message.message_id)
        except Exception:
            pass

        if target.uid == st.forzado_uid:
            st.forzado_restantes = 0
        target.estado_ronda = "congelado"
        await bot.send_message(
            game.cid,
            "❄️ {} queda *congelado* con *{}* puntos de ronda.".format(player_call(target), target.puntaje_ronda()),
            parse_mode=ParseMode.MARKDOWN
        )
        await continuar_tras_carta(bot, game, drawer)
    except Exception as e:
        await bot.send_message(ADMIN[0], f'callback_choose_freeze_target error: {e}')
        await bot.send_message(ADMIN[0], callback.data)


async def callback_choose_flip_three_target(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    try:
        regex = re.search(r"(-[0-9]*)\*choosef3F7\*([0-9]*)\*([0-9]*)", callback.data)
        cid, target_uid, uid = int(regex.group(1)), int(regex.group(2)), int(regex.group(3))
        actor_uid = callback.from_user.id

        game = get_game(cid)
        if not game or game.tipo != "Flip7" or not game.board:
            return
        st = game.board.state
        if actor_uid != uid or not st.accion_pendiente or st.accion_pendiente.get("drawer_uid") != actor_uid:
            return

        target = game.playerlist.get(target_uid)
        drawer = game.playerlist.get(actor_uid)
        if not target or not drawer:
            return
        st.accion_pendiente = None

        try:
            await bot.edit_message_text("🔄 Elegiste Flip Three para {}".format(target.name), cid, callback.message.message_id)
        except Exception:
            pass

        iniciar_o_encolar_flip_three(game, target.uid)
        if target.uid == drawer.uid:
            msg = "🔄 {} se aplica *Flip Three* a sí mismo.".format(drawer.name)
        else:
            msg = "🔄 {} le aplica *Flip Three* a {}.".format(drawer.name, player_call(target))
        await bot.send_message(game.cid, msg, parse_mode=ParseMode.MARKDOWN)
        await continuar_tras_carta(bot, game, drawer)
    except Exception as e:
        await bot.send_message(ADMIN[0], f'callback_choose_flip_three_target error: {e}')
        await bot.send_message(ADMIN[0], callback.data)


async def callback_choose_sc_give(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    try:
        regex = re.search(r"(-[0-9]*)\*choosescgiveF7\*([0-9]*)\*([0-9]*)", callback.data)
        cid, target_uid, uid = int(regex.group(1)), int(regex.group(2)), int(regex.group(3))
        actor_uid = callback.from_user.id

        game = get_game(cid)
        if not game or game.tipo != "Flip7" or not game.board:
            return
        st = game.board.state
        if actor_uid != uid or not st.accion_pendiente or st.accion_pendiente.get("drawer_uid") != actor_uid:
            return

        target = game.playerlist.get(target_uid)
        drawer = game.playerlist.get(actor_uid)
        if not target or not drawer:
            return
        st.accion_pendiente = None

        try:
            await bot.edit_message_text("🍀 Se la diste a {}".format(target.name), cid, callback.message.message_id)
        except Exception:
            pass

        target.tiene_segunda_oportunidad = True
        await bot.send_message(
            game.cid,
            "🍀 {} le da su Segunda Oportunidad extra a {}.".format(drawer.name, player_call(target)),
            parse_mode=ParseMode.MARKDOWN
        )
        await continuar_tras_carta(bot, game, drawer)
    except Exception as e:
        await bot.send_message(ADMIN[0], f'callback_choose_sc_give error: {e}')
        await bot.send_message(ADMIN[0], callback.data)
