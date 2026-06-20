import logging as log
import os
import urllib.parse

import psycopg
import SecretoCodigo.Controller as SecretoCodigoController
from SecretoCodigo.Controller import format_numero_pista
from Utils import get_game, save, player_call, simple_choose_buttons

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext
import GamesController
from Constants.Config import ADMIN

import re

log.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s SecretoCodigo',
    level=log.INFO)
logger = log.getLogger(__name__)

urllib.parse.uses_netloc.append("postgres")
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])


async def command_hint(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args

    try:
        uid = update.message.from_user.id
        cid = update.message.chat_id
    except Exception:
        return

    # /hint must be used in private chat
    if update.effective_message.chat.type in ['group', 'supergroup']:
        try:
            await bot.delete_message(cid, update.message.message_id)
        except Exception:
            pass
        await bot.send_message(uid, "Debes usar /hint en privado, no en el grupo.")
        return

    if len(args) < 2:
        await bot.send_message(uid, "Uso: /hint PALABRA NUMERO  (ej: /hint ANIMAL 3)")
        return

    word = " ".join(args[:-1])
    if word.lstrip('-').isdigit():
        await bot.send_message(uid, "La pista debe ser una palabra, no un número. Uso: `/hint PALABRA NUMERO`", parse_mode=ParseMode.MARKDOWN)
        return
    try:
        number = int(args[-1])
    except ValueError:
        await bot.send_message(uid, "El último argumento debe ser un número entero.")
        return

    if not (-1 <= number <= 9):
        await bot.send_message(uid, "El número debe ser entre -1 y 9. Usa -1 para pista infinita.")
        return

    # Load all SecretoCodigo games from DB to memory
    try:
        conn = psycopg.connect(
            dbname=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port,
        )
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM games g WHERE g.tipojuego = 'SecretoCodigo'")
        for table in cursor.fetchall():
            if table[0] not in GamesController.games:
                get_game(table[0])
        conn.close()
    except Exception as e:
        log.error(f'DB error in command_hint: {e}')

    def _can_hint(g):
        if g.tipo != "SecretoCodigo" or uid not in g.playerlist or g.board is None:
            return False
        if g.modo == "Cooperativo":
            label = g.get_label_by_uid(uid)
            return label is not None and g.board.state.fase_actual == f"Duo {label} - Pista"
        return g.is_spymaster(uid) and g.board.state.fase_actual in ("Turno Rojo - Pista", "Turno Azul - Pista")

    valid_games = [g for g in GamesController.games.values() if _can_hint(g)]

    if len(valid_games) == 0:
        await bot.send_message(uid, "No hay partida donde puedas dar pista ahora.")
        return

    if len(valid_games) == 1:
        g = valid_games[0]
        if g.modo == "Cooperativo":
            await SecretoCodigoController.process_hint_duo(bot, g, uid, word, number)
        else:
            await SecretoCodigoController.process_hint(bot, g, uid, word, number)
        return

    # Multiple eligible games — show selection buttons
    btns = []
    for g in valid_games:
        datos = f"{g.cid}*choosegamehintCN*{word}_{number}*{uid}"
        btns.append([InlineKeyboardButton(g.groupName, callback_data=datos)])
    datos = f"-1*choosegamehintCN*cancel*{uid}"
    btns.append([InlineKeyboardButton("Cancelar", callback_data=datos)])
    await bot.send_message(uid, "¿En qué grupo quieres dar la pista?", reply_markup=InlineKeyboardMarkup(btns))


async def callback_choose_game_hint_cn(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    try:
        regex = re.search(r"(-?[0-9]*)\*choosegamehintCN\*(.*)\*([0-9]*)", callback.data)
        cid_str, opcion, uid = regex.group(1), regex.group(2), int(regex.group(3))

        if cid_str == "-1":
            await bot.edit_message_text("Cancelado.", uid, callback.message.message_id)
            return

        game = get_game(int(cid_str))
        await bot.edit_message_text(f"Grupo elegido: {game.groupName}", uid, callback.message.message_id)

        parts = opcion.rsplit("_", 1)
        word = parts[0]
        number = int(parts[1])
        if game.modo == "Cooperativo":
            await SecretoCodigoController.process_hint_duo(bot, game, uid, word, number)
        else:
            await SecretoCodigoController.process_hint(bot, game, uid, word, number)
    except Exception as e:
        await bot.send_message(ADMIN[0], f'callback_choose_game_hint_cn error: {e}')


async def command_pick(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    cid = update.message.chat_id
    uid = update.message.from_user.id

    game = get_game(cid)
    if not game or game.tipo != "SecretoCodigo" or not game.board:
        return

    if len(args) < 1:
        await bot.send_message(cid, "Uso: /pick NUMERO  (ej: /pick 7)")
        return

    try:
        numero = int(args[0])
    except ValueError:
        await bot.send_message(cid, "El argumento debe ser un número entre 1 y 25.")
        return

    if numero < 1 or numero > 25:
        await bot.send_message(cid, "El número debe ser entre 1 y 25.")
        return

    fase = game.board.state.fase_actual

    if game.modo == "Cooperativo":
        st = game.board.state
        receptor_label = game.get_other_player_label(st.dador_actual)
        receptor = game.get_player_by_label(receptor_label)

        if fase != f"Duo {st.dador_actual} - Adivinar":
            await bot.send_message(cid, "No es el momento de adivinar.")
            return
        if not receptor or receptor.uid != uid:
            await bot.send_message(cid, "No eres quien debe adivinar ahora.")
            return

        card = next((c for c in game.board.state.tablero if c["numero"] == numero), None)
        if card is None or card["revealed"]:
            await bot.send_message(cid, "Carta inválida o ya revelada.")
            return

        await SecretoCodigoController.process_pick_duo(bot, game, uid, numero)
        return

    team = game.board.state.turno_actual

    if fase != f"Turno {team} - Adivinar":
        await bot.send_message(cid, "No es el momento de adivinar.")
        return

    if not game.is_field_operative(uid, team):
        await bot.send_message(cid, "No eres un agente de campo del equipo activo.")
        return

    card = next((c for c in game.board.state.tablero if c["numero"] == numero), None)
    if card is None or card["revealed"]:
        await bot.send_message(cid, "Carta inválida o ya revelada.")
        return

    await SecretoCodigoController.process_pick(bot, game, uid, numero)


async def command_pickb(update: Update, context: CallbackContext):
    bot = context.bot
    cid = update.message.chat_id
    uid = update.message.from_user.id

    game = get_game(cid)
    if not game or game.tipo != "SecretoCodigo" or not game.board:
        return

    tablero = game.board.state.tablero
    strcid = str(cid)

    buttons = []
    row = []
    for card in tablero:
        numero = card["numero"]
        word = card["word"].upper()
        label = f"✓" if card["revealed"] else word
        cb = f"{strcid}*pickb*{numero}*{uid}"
        row.append(InlineKeyboardButton(label, callback_data=cb))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    markup = InlineKeyboardMarkup(buttons)
    await bot.send_message(cid, "🗺 Elegí una carta:", reply_markup=markup)


async def callback_pickb(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    import re
    regex = re.search(r"(-?[0-9]*)\*pickb\*([0-9]*)\*([0-9]*)", callback.data)
    cid = int(regex.group(1))
    numero = int(regex.group(2))
    uid = callback.from_user.id

    game = get_game(cid)
    if not game or game.tipo != "SecretoCodigo" or not game.board:
        await callback.answer("No hay partida activa.")
        return

    card = next((c for c in game.board.state.tablero if c["numero"] == numero), None)
    if card is None or card["revealed"]:
        await callback.answer("Carta ya revelada o inválida.")
        return

    fase = game.board.state.fase_actual

    if game.modo == "Cooperativo":
        st = game.board.state
        receptor_label = game.get_other_player_label(st.dador_actual)
        receptor = game.get_player_by_label(receptor_label)
        if fase != f"Duo {st.dador_actual} - Adivinar":
            await callback.answer("No es el momento de adivinar.")
            return
        if not receptor or receptor.uid != uid:
            await callback.answer("No eres quien debe adivinar ahora.")
            return
        await callback.answer()
        await callback.message.delete()
        await SecretoCodigoController.process_pick_duo(bot, game, uid, numero)
        return

    team = game.board.state.turno_actual
    if fase != f"Turno {team} - Adivinar":
        await callback.answer("No es el momento de adivinar.")
        return
    if not game.is_field_operative(uid, team):
        await callback.answer("No eres un agente de campo del equipo activo.")
        return

    await callback.answer()
    await callback.message.delete()
    await SecretoCodigoController.process_pick(bot, game, uid, numero)


async def command_endturn(update: Update, context: CallbackContext):
    bot = context.bot
    cid = update.message.chat_id
    uid = update.message.from_user.id

    game = get_game(cid)
    if not game or game.tipo != "SecretoCodigo" or not game.board:
        return

    fase = game.board.state.fase_actual

    if game.modo == "Cooperativo":
        st = game.board.state
        receptor_label = game.get_other_player_label(st.dador_actual)
        receptor = game.get_player_by_label(receptor_label)

        if fase != f"Duo {st.dador_actual} - Adivinar":
            await bot.send_message(cid, "No estás en fase de adivinar.")
            return
        if not receptor or receptor.uid != uid:
            await bot.send_message(cid, "Solo quien debe adivinar puede terminar el turno.")
            return

        await bot.send_message(cid, f"*{receptor.name}* termina el turno voluntariamente.", parse_mode=ParseMode.MARKDOWN)
        await SecretoCodigoController.end_turn_duo(bot, game)
        return

    team = game.board.state.turno_actual

    if fase != f"Turno {team} - Adivinar":
        await bot.send_message(cid, "No estás en fase de adivinar.")
        return

    if not game.is_field_operative(uid, team):
        await bot.send_message(cid, "Solo los agentes de campo pueden terminar el turno.")
        return

    await bot.send_message(
        cid,
        f"El equipo *{team}* termina su turno voluntariamente.",
        parse_mode=ParseMode.MARKDOWN,
    )
    await SecretoCodigoController.end_turn(bot, game)


async def command_demotablero(update: Update, context: CallbackContext):
    bot = context.bot
    cid = update.message.chat_id
    import SecretoCodigo.render as render_mod
    args = context.args
    font_size = int(args[0]) if args and args[0].isdigit() else None
    sample_words = [
        "GRANADA", "UNICORNIO", "MONTAÑA", "LANZA", "MOTOR",
        "RIO", "LEONA", "INTERNET", "POLO", "CEREBRO",
        "ARMA", "ROBOT", "GATO", "TIGRE", "HORMIGA",
        "PAPA", "ESTADO", "LINCE", "SATELITE", "MERCADO",
        "FALCON", "LATIGO", "CHOCOLATE", "DIETA", "SENADO",
    ]
    tipos = ["rojo"] * 9 + ["azul"] * 8 + ["neutral"] * 7 + ["asesino"] * 1
    import random as _random
    _random.shuffle(tipos)
    tablero = [
        {"word": w, "tipo": tipos[i], "revealed": i in (0, 5, 10, 17, 24), "numero": i + 1}
        for i, w in enumerate(sample_words)
    ]
    effective_size = font_size if font_size is not None else render_mod.FONT_SIZE
    buf = render_mod.render_board(tablero, mode="public", font_size=font_size)
    await bot.send_photo(cid, photo=buf, caption=f"🎲 Tablero de demo — send_photo | font: {effective_size}px")


async def command_demotablero2(update: Update, context: CallbackContext):
    bot = context.bot
    cid = update.message.chat_id
    import SecretoCodigo.render as render_mod
    args = context.args
    font_size = int(args[0]) if args and args[0].isdigit() else None
    sample_words = [
        "GRANADA", "UNICORNIO", "MONTAÑA", "LANZA", "MOTOR",
        "RIO", "LEONA", "INTERNET", "POLO", "CEREBRO",
        "ARMA", "ROBOT", "GATO", "TIGRE", "HORMIGA",
        "PAPA", "ESTADO", "LINCE", "SATELITE", "MERCADO",
        "FALCON", "LATIGO", "CHOCOLATE", "DIETA", "SENADO",
    ]
    tipos = ["rojo"] * 9 + ["azul"] * 8 + ["neutral"] * 7 + ["asesino"] * 1
    import random as _random
    _random.shuffle(tipos)
    tablero = [
        {"word": w, "tipo": tipos[i], "revealed": i in (0, 5, 10, 17, 24), "numero": i + 1}
        for i, w in enumerate(sample_words)
    ]
    effective_size = font_size if font_size is not None else render_mod.FONT_SIZE
    buf = render_mod.render_board(tablero, mode="public", font_size=font_size)
    await bot.send_document(cid, document=buf, filename="tablero.png", caption=f"🎲 Tablero de demo — send_document | font: {effective_size}px")


async def command_demotablero3(update: Update, context: CallbackContext):
    bot = context.bot
    cid = update.message.chat_id
    import SecretoCodigo.render as render_mod
    args = context.args
    font_size = int(args[0]) if args and args[0].isdigit() else None
    sample_words = [
        "GRANADA", "UNICORNIO", "MONTAÑA", "LANZA", "MOTOR",
        "RIO", "LEONA", "INTERNET", "POLO", "CEREBRO",
        "ARMA", "ROBOT", "GATO", "TIGRE", "HORMIGA",
        "PAPA", "ESTADO", "LINCE", "SATELITE", "MERCADO",
        "FALCON", "LATIGO", "CHOCOLATE", "DIETA", "SENADO",
    ]
    tipos = ["rojo"] * 9 + ["azul"] * 8 + ["neutral"] * 7 + ["asesino"] * 1
    import random as _random
    _random.shuffle(tipos)
    tablero = [
        {"word": w, "tipo": tipos[i], "revealed": i in (0, 5, 10, 17, 24), "numero": i + 1}
        for i, w in enumerate(sample_words)
    ]
    effective_size = font_size if font_size is not None else render_mod.FONT_SIZE
    buf = render_mod.render_html_to_bytesio(tablero, mode="public", font_size=font_size)
    await bot.send_photo(cid, photo=buf, caption=f"🎲 Tablero de demo — html2image | font: {effective_size}px")


async def command_history(update: Update, context: CallbackContext):
    bot = context.bot
    cid = update.message.chat_id
    uid = update.message.from_user.id
    game = get_game(cid)
    if not game or game.tipo != "SecretoCodigo" or not game.board:
        return
    historial = getattr(game.board.state, 'historial', [])
    if not historial:
        await bot.send_message(uid, "No hay pistas registradas aún.", parse_mode=ParseMode.MARKDOWN)
        return

    if game.modo == "Cooperativo":
        emoji_resultado = {"agente": "✅", "neutral": "⬜", "asesino": "💀"}
        desc_resultado = {"agente": "agente", "neutral": "neutral pisado", "asesino": "asesino"}
    else:
        emoji_resultado = {"correcto": "✅", "gris": "⬜", "contrario": "❌", "asesino": "💀"}
        desc_resultado = {"correcto": "correcto", "gris": "neutral", "contrario": "equipo contrario", "asesino": "asesino"}

    lines = [f"📋 *Historial de pistas — {game.groupName}:*\n"]
    for entrada in historial:
        turno = entrada["turno"]
        dador = entrada["dador"]
        pista = entrada["pista"]
        numero = entrada["numero"]
        numero_str = format_numero_pista(numero)

        if game.modo == "Cooperativo":
            lines.append(f"👤 *{dador}* (Jugador {turno}) — *{pista}* ({numero_str})")
        else:
            emoji_eq = "🔴" if turno == "Rojo" else "🔵"
            lines.append(f"{emoji_eq} *{dador}* ({turno}) — *{pista}* ({numero_str})")

        for pick in entrada["picks"]:
            r = pick["resultado"]
            lines.append(f"  {emoji_resultado.get(r, '?')} *{pick['word']}* — {desc_resultado.get(r, r)}")

        if not entrada["picks"]:
            lines.append("  _(sin intentos)_")
        elif numero not in (0, -1):
            exito_key = "agente" if game.modo == "Cooperativo" else "correcto"
            encontrados = sum(1 for p in entrada["picks"] if p["resultado"] == exito_key)
            if encontrados < numero:
                lines.append(f"  ⚠️ _Solo {encontrados}/{numero} encontrados — quedaron intentos sin usar_")
        lines.append("")

    await bot.send_message(uid, "\n".join(lines), parse_mode=ParseMode.MARKDOWN)


async def command_call(bot, game):
    fase = game.board.state.fase_actual
    if not fase:
        return

    if game.modo == "Cooperativo":
        st = game.board.state
        if not st.dador_actual:
            return
        dador = game.get_player_by_label(st.dador_actual)
        receptor = game.get_player_by_label(game.get_other_player_label(st.dador_actual))

        if "Pista" in fase:
            await bot.send_message(
                game.cid,
                f"{player_call(dador)} es tu turno de dar la pista.\nUsa `/hint PALABRA NUMERO` en privado.",
                parse_mode=ParseMode.MARKDOWN,
            )
            await bot.send_photo(
                dador.uid,
                photo=game.board.render_key_image(game, st.dador_actual),
                caption=(
                    f"[{game.groupName}] Es tu turno de dar pista. Usa `/hint PALABRA NUMERO` aquí.\n"
                    "• `0` → adivina sin límite\n"
                    "• `-1` → pista infinita (también sin límite)"
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
        elif "Adivinar" in fase:
            intentos_display = "∞" if st.intentos_restantes >= 999 else st.intentos_restantes
            numero_display = format_numero_pista(st.numero_pista)
            await bot.send_photo(
                game.cid,
                photo=game.board.render_duo_board_image(game),
                caption=(
                    f"{player_call(receptor)}: pista *{st.pista_actual}* — {numero_display}. "
                    f"Intentos restantes: {intentos_display}.\nUsa `/pick NUMERO` o `/endturn`."
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
            await bot.send_message(
                receptor.uid,
                f"[{game.groupName}] 🔍 Toca adivinar. Pista: *{st.pista_actual}* — {numero_display}. "
                f"Intentos restantes: {intentos_display}.\nUsa `/pick NUMERO` o `/endturn`.",
                parse_mode=ParseMode.MARKDOWN,
            )
        return

    if "Pista" in fase:
        team = game.board.state.turno_actual
        sm = game.get_spymaster(team)
        await bot.send_message(
            game.cid,
            f"{player_call(sm)} es tu turno de dar la pista del equipo *{team}*.\nUsa `/hint PALABRA NUMERO` en privado.",
            parse_mode=ParseMode.MARKDOWN,
        )
        await bot.send_photo(
            sm.uid,
            photo=game.board.render_spymaster_image(game),
            caption=(
                f"Es tu turno ({team}). Usa `/hint PALABRA NUMERO` aquí.\n"
                "• `0` → adivina sin límite\n"
                "• `-1` → pista infinita (también sin límite)"
            ),
            parse_mode=ParseMode.MARKDOWN,
        )

    elif "Adivinar" in fase:
        team = game.board.state.turno_actual
        pista = game.board.state.pista_actual
        numero = game.board.state.numero_pista
        intentos = game.board.state.intentos_restantes
        intentos_display = "∞" if intentos >= 999 else intentos
        numero_display = format_numero_pista(numero)
        await bot.send_photo(
            game.cid,
            photo=game.board.render_board_image(game),
            caption=(
                f"Equipo *{team}*: pista *{pista}* — {numero_display}. "
                f"Intentos restantes: {intentos_display}.\nUsa `/pick NUMERO` o `/endturn`."
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
        sm = game.get_spymaster(team)
        equipo = game.board.state.equipo_rojo if team == "Rojo" else game.board.state.equipo_azul
        for jugador in equipo:
            if jugador.uid != sm.uid:
                await bot.send_message(
                    jugador.uid,
                    f"[{game.groupName}] 🔍 Toca adivinar, equipo *{team}*. Pista: *{pista}* — {numero_display}. "
                    f"Intentos restantes: {intentos_display}.\nUsa `/pick NUMERO` o `/endturn`.",
                    parse_mode=ParseMode.MARKDOWN,
                )
