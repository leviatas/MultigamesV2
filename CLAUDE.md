# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

MultigamesV2 is a **Python Telegram bot ecosystem** for playing board games in group chats. It runs multiple bots concurrently in threads: a main Multigames bot (10+ games) and a dedicated Secret Hitler bot. The user-facing language is Spanish.

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Required environment variable
export DATABASE_URL="postgres://user:pass@host:port/dbname"

# Run only Secret Hitler (current __main__ default — see Main.py line 84)
python Main.py

# Run the full multi-bot setup (edit Main.py to call main() instead)
# main() starts Bot1 (MainController) and Bot2 (SecretHitler) as daemon threads
```

There is no test suite. `MainTest.py` is a standalone runner for isolated manual testing of SecretHitler.

## Deployment

- **CI/CD**: Push to `main` triggers `.github/workflows/fly.yml`, which deploys to Fly.io (`flyctl deploy --remote-only`).
- **Docker**: `CMD ["python", "Main.py"]` — includes Google Chrome (used by `html2image` for rendering).
- **Database**: PostgreSQL, schema in `DBCreate.sql`. Key table: `games` (id, groupName, tipojuego, data TEXT — JSON-serialized game object via `jsonpickle`).

## Architecture

### Multi-Bot Threading (`Main.py`)

`main()` launches each bot as a `daemon=True` thread. Currently active: `MainController.main()` (Multigames) and `SecretHitler.MainController.main()`. Other bots (`reportBot`, `BloodClocktower`, `discordBot`) exist as modules but are commented out.

### Game Module Pattern

Each game lives in its own directory and follows this structure:
```
GameName/
  Controller.py   # Game initialization and phase-transition logic
  Commands.py     # Telegram command handlers and callback handlers
  Boardgamebox/
    Game.py       # Extends root Boardgamebox/Game.py with game-specific fields
  Constants/      # (optional) game-specific card/rule data
  txt/            # (optional) word lists
```

Adding a new game requires:
1. Creating the module directory with the pattern above
2. Registering it in `Constants/Config.py` under `JUEGOS_DISPONIBLES` and `MODULOS_DISPONIBES`
3. Importing its `Controller` and `Commands` in `MainController.py`
4. Wiring its command/callback handlers in `MainController.main()`

### Core Data Flow

```
Telegram update → MainController (dispatcher) → Commands.py handler
                                                    ↓
                                              Utils.get_game(cid)
                                                    ↓
                                         GamesController.games dict (in-memory)
                                         or load_game() from PostgreSQL
                                                    ↓
                                           Game object mutation
                                                    ↓
                                            Utils.save() → PostgreSQL
```

**`GamesController`** is a module-level singleton with a `games` dict keyed by `cid` (Telegram chat ID). `GamesController.init()` must be called at startup to initialize the dict.

**Game state** is persisted as `jsonpickle`-encoded objects. After decoding, player IDs in `playerlist`, `board.state.last_votes`, and `board.state.enesperadeaccion` must be cast back to `int` (jsonpickle converts dict keys to strings — see `Utils.load_game()`). Any new dict keyed by `uid` added to persisted state needs the same treatment.

### Root Boardgamebox Classes

- **`Game`** (`Boardgamebox/Game.py`): Base class holding `playerlist` (dict uid→Player), `player_sequence` (list, shuffled order), `board`, `initiator`, `history`, `tipo` (game name), `modo` (game mode), `configs` dict, `is_debugging` flag.
- **`Board`** (`Boardgamebox/Board.py`): Holds `state`, card deck (`cartas`), `discards`, `previous`.
- **`State`** (`Boardgamebox/State.py`): All mutable game state — `fase_actual`, `active_player`, `reviewer_player`, `player_counter`, `last_votes`, action indices for card execution sequences.
- **`Player`** (`Boardgamebox/Player.py`): `name` and `uid`.
- **`Team`** (`Boardgamebox/Team.py`): Named group of players (e.g. liberal/fascist); used by team-based games to check membership and broadcast messages to teammates only.

Each game typically subclasses `Game` (in its own `Boardgamebox/Game.py`) to add game-specific fields.

### Callback Data Format

Inline keyboard buttons encode data as a `*`-delimited string:
```
"{cid}*{comando_callback}*{key}*{uid}"
```
Handlers split on `*` to extract these four fields. This is the universal pattern across all games.

Destructive actions (e.g. `/delete`, `/cancelgame`) don't act immediately — they send a Sí/No inline keyboard (`confirmDelete`/`confirmCancel` in the callback data) and require the confirming callback's `from_user.id` to match the `uid` embedded in the data before proceeding. Follow this two-step pattern for any new command that deletes or ends a game.

### Utility Functions (`Utils/__init__.py`)

Key helpers used everywhere:
- `get_game(cid)` — returns game from memory or DB
- `save(bot, cid)` / `save_game(...)` / `load_game(cid)` / `delete_game(cid)` — DB CRUD
- `simple_choose_buttons(...)` — renders inline keyboard to a chat; redirects to admin if `game.is_debugging` is True
- `player_call(player)` — formats a Telegram mention link
- `basic_validation(game, uid)` — checks board exists and player is in game
- `@restricted` — limits command to `ADMIN[0]` only
- `remove_same_elements_dict(last_votes)` — deduplicates clues (used in JustOne)

### SecretHitler Sub-Ecosystem

`SecretHitler/` is a **self-contained** bot with its own `MainController`, `Commands`, `GamesController`, `Boardgamebox/`, `Constants/`, and DB connection. It shares only `Utils.command_status` from the root. It has its own `DBCreate.sql`, `requirements.txt`, and formerly its own Heroku/Jenkins deployment (`Procfile`, `Jenkinsfile`, `app.json`). It also has its own player stats layer: `PlayerStats.py` (per-user, per-game-type stats/achievements dict, persisted separately from game state) and `EstadisticsCalculator.py` (hypergeometric-distribution helpers for role-probability stats). At startup `main()` registers the bot's `/`-menu via `set_my_commands` — keep that list in sync when adding/removing commands.

### Config (`Constants/Config.py`)

- `TOKEN`: main bot token (or set via DB)
- `ADMIN`: list of admin Telegram user IDs; `ADMIN[0]` is the primary admin
- `JUEGOS_DISPONIBLES`: registry of all games with commands, `restriccion` (admin-only flag), and `permitir_ingreso_tardio` (late-join allowed)
- `MODULOS_DISPONIBES`: per-game modes with `min_jugadores` / `max_jugadores`
- `HOJAS_AYUDA`: in-game help text per game

### Constants/Cards.py

Large file (~93KB) containing all game card definitions (`cartas_aventura`), player role sets (`playerSets`), action sequences (`actions`), button configurations (`comandos`), and other game data referenced by multiple controllers.
