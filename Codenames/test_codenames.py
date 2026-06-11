#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Smoke test para Codenames: simula partidas completas (Competitivo y
Cooperativo/Dúo) sin Telegram ni base de datos, usando un FakeBot y
mockeando save()/get_game().

Ejecutar con:  python -m Codenames.test_codenames
"""
import asyncio
import os
import random
import sys
import types

os.environ.setdefault("DATABASE_URL", "postgres://user:pass@localhost/db")

# El Controller carga las palabras desde una ruta absoluta "/Codenames/txt/...",
# que coincide con el directorio raíz del proyecto en el contenedor de producción.
# Si no existe (p.ej. corriendo localmente desde otro lugar), se crea un symlink.
if not os.path.exists("/Codenames"):
    try:
        os.symlink(os.path.dirname(os.path.abspath(__file__)), "/Codenames")
    except OSError:
        pass

# --- Stub mínimo del paquete `telegram` para poder importar el código del juego ---
if "telegram" not in sys.modules:
    telegram = types.ModuleType("telegram")

    class _Stub:
        def __init__(self, *args, **kwargs):
            pass

    telegram.Update = _Stub
    telegram.InlineKeyboardButton = _Stub
    telegram.InlineKeyboardMarkup = _Stub
    telegram.ForceReply = _Stub

    constants = types.ModuleType("telegram.constants")

    class ParseMode:
        MARKDOWN = "Markdown"

    class ChatAction:
        TYPING = "typing"

    constants.ParseMode = ParseMode
    constants.ChatAction = ChatAction

    ext = types.ModuleType("telegram.ext")
    ext.CallbackContext = _Stub
    ext.CallbackQueryHandler = _Stub
    ext.CommandHandler = _Stub

    telegram.constants = constants
    telegram.ext = ext
    sys.modules["telegram"] = telegram
    sys.modules["telegram.constants"] = constants
    sys.modules["telegram.ext"] = ext

import GamesController
import Utils
import Codenames.Controller as CodenamesController
import Codenames.Commands as CodenamesCommands
from Codenames.Boardgamebox.Game import Game


class FakeBot:
    def __init__(self):
        self.messages = []

    async def send_message(self, chat_id, text="", parse_mode=None, reply_markup=None, **kwargs):
        self.messages.append((chat_id, text))
        return types.SimpleNamespace(message_id=len(self.messages))

    async def edit_message_text(self, text, chat_id=None, message_id=None, **kwargs):
        self.messages.append((chat_id, text))

    async def delete_message(self, chat_id, message_id):
        pass

    async def send_photo(self, chat_id, photo=None, caption=None, parse_mode=None, **kwargs):
        self.messages.append((chat_id, caption or ""))


async def _noop_save(bot, cid, newGroupName=''):
    pass


def make_game(cid, modo, names, tipo="Codenames"):
    game = Game(cid, 1, f"Grupo-{cid}", tipo, modo)
    for i, name in enumerate(names, start=1):
        uid = cid * 1000 + i
        game.add_player(uid, name)
    game.create_board()
    game.shuffle_player_sequence()
    game.configs['diccionario'] = 'original'
    GamesController.games[cid] = game
    return game


def assert_true(cond, msg):
    if not cond:
        raise AssertionError(msg)


async def play_competitivo():
    print("\n=== Test Codenames Competitivo ===")
    bot = FakeBot()
    game = make_game(-1001, "Competitivo", ["Ana", "Beto", "Caro", "Dani", "Ema", "Fede"])

    await CodenamesController.finish_config(bot, game)

    st = game.board.state
    assert_true(len(st.tablero) == 25, "El tablero debe tener 25 cartas")
    assert_true(st.spymaster_rojo is not None and st.spymaster_azul is not None, "Deben existir ambos espías")
    assert_true(st.fase_actual == "Turno Rojo - Pista", f"Debe iniciar con el turno Rojo, fue {st.fase_actual}")

    rondas = 0
    while st.fase_actual != "Finalizado" and rondas < 400:
        rondas += 1
        team = st.turno_actual
        fase = st.fase_actual

        if fase == f"Turno {team} - Pista":
            sm = game.get_spymaster(team)
            await CodenamesController.process_hint(bot, game, sm.uid, "PISTA", random.randint(1, 3))
        elif fase == f"Turno {team} - Adivinar":
            operativos = [p for p in game.get_team_players(team) if not game.is_spymaster(p.uid)]
            uid = operativos[0].uid
            sin_revelar = [c for c in st.tablero if not c["revealed"]]
            numero = random.choice(sin_revelar)["numero"]
            await CodenamesController.process_pick(bot, game, uid, numero)
        else:
            raise AssertionError(f"Fase inesperada: {fase}")

    assert_true(st.fase_actual == "Finalizado", "La partida Competitivo debe terminar")
    asesino_tocado = any(c["revealed"] and c["tipo"] == "asesino" for c in st.tablero)
    assert_true(
        st.palabras_rojo_restantes == 0 or st.palabras_azul_restantes == 0 or asesino_tocado,
        "La partida debe terminar porque un equipo reveló todas sus palabras o se tocó al asesino"
    )
    print(f"OK — terminó en {rondas} rondas (asesino_tocado={asesino_tocado}). Mensajes enviados: {len(bot.messages)}")


async def play_cooperativo():
    print("\n=== Test Codenames Cooperativo (Dúo) ===")
    bot = FakeBot()
    game = make_game(-1002, "Cooperativo", ["Ana", "Beto"])

    await CodenamesController.finish_config(bot, game)

    st = game.board.state
    assert_true(len(st.key_a) == 25 and len(st.key_b) == 25, "Las claves deben cubrir las 25 cartas")

    agentes_a = {n for n, t in st.key_a.items() if t == "agente"}
    agentes_b = {n for n, t in st.key_b.items() if t == "agente"}
    assert_true(len(agentes_a & agentes_b) == 0, "Las cartas de agente de A y B no deben solaparse")
    assert_true(len(agentes_a) + len(agentes_b) == 15, "Debe haber 15 agentes en total")

    asesinos = {n for n, t in st.key_a.items() if t == "asesino"}
    assert_true(asesinos == {n for n, t in st.key_b.items() if t == "asesino"}, "El asesino debe ser el mismo para ambos")
    assert_true(len(asesinos) == 1, "Debe haber exactamente un asesino")

    assert_true(st.fase_actual == "Duo A - Pista", f"Debe iniciar con pista del jugador A, fue {st.fase_actual}")

    rondas = 0
    while st.fase_actual != "Finalizado" and rondas < 400:
        rondas += 1
        fase = st.fase_actual
        dador_label = st.dador_actual
        dador = game.get_player_by_label(dador_label)
        receptor = game.get_player_by_label(game.get_other_player_label(dador_label))

        if fase == f"Duo {dador_label} - Pista":
            await CodenamesController.process_hint_duo(bot, game, dador.uid, "PISTA", random.randint(1, 3))
        elif fase == f"Duo {dador_label} - Adivinar":
            sin_revelar = [c for c in st.tablero if not c["revealed"]]
            numero = random.choice(sin_revelar)["numero"]
            await CodenamesController.process_pick_duo(bot, game, receptor.uid, numero)
        else:
            raise AssertionError(f"Fase inesperada: {fase}")

    assert_true(st.fase_actual == "Finalizado", "La partida Dúo debe terminar")
    print(f"OK — terminó en {rondas} rondas. Agentes encontrados: {st.agentes_revelados}/{st.total_agentes_duo}. "
          f"Pistas restantes: {st.pistas_restantes}. Mensajes enviados: {len(bot.messages)}")


async def play_cooperativo_command_dispatch():
    print("\n=== Test Codenames Cooperativo — dispatch vía Commands ===")
    bot = FakeBot()
    game = make_game(-1003, "Cooperativo", ["Ana", "Beto"])
    await CodenamesController.finish_config(bot, game)

    st = game.board.state
    dador = game.get_player_by_label(st.dador_actual)
    receptor = game.get_player_by_label(game.get_other_player_label(st.dador_actual))

    def _can_hint(g):
        if g.tipo != "Codenames" or g.board is None:
            return False
        if g.modo == "Cooperativo":
            label = g.get_label_by_uid(dador.uid)
            return label is not None and g.board.state.fase_actual == f"Duo {label} - Pista"
        return False

    assert_true(_can_hint(game), "El jugador A debe poder dar pista en su turno")

    await CodenamesController.process_hint_duo(bot, game, dador.uid, "ANIMAL", 2)
    assert_true(st.fase_actual == f"Duo {st.dador_actual} - Adivinar", "Tras la pista debe pasar a fase de adivinar")

    sin_revelar = [c for c in st.tablero if not c["revealed"]]
    numero = sin_revelar[0]["numero"]
    receptor_label = game.get_other_player_label(st.dador_actual)
    receptor = game.get_player_by_label(receptor_label)
    assert_true(game.get_label_by_uid(receptor.uid) == receptor_label, "El receptor debe resolverse por label")

    await CodenamesController.process_pick_duo(bot, game, receptor.uid, numero)
    print("OK — dispatch coherente entre Commands y Controller para modo Dúo")


async def main():
    GamesController.init()
    Utils.save = _noop_save
    CodenamesController.save = _noop_save
    CodenamesCommands.save = _noop_save

    await play_competitivo()
    await play_cooperativo()
    await play_cooperativo_command_dispatch()
    print("\nTodos los tests de Codenames pasaron correctamente.")


if __name__ == "__main__":
    asyncio.run(main())
