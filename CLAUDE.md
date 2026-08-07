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

`Constants/Config.py` has a hardcoded `VERSION` string (starting at `1.0.0`), shown by `/version`. Bump it (semver) on every change committed to this bot — patch for fixes, minor for new commands/features, major for breaking changes.

#### Achievements system

- **Catalog**: `SecretHitler/Constants/Achievements.py` — a flat `LOGROS` list of `Logro` namedtuples (`code, name, description, emoji, categoria, secreto, check`). `code` is the stable key persisted in `achievements_secret_hitler_players.achievement_code`; **never rename it** once shipped, or you orphan everyone's unlocks for it. `secreto=True` hides `name`/`description` in `/logros` until unlocked. `check(ctx)` is a pure predicate over an `Achievements.Ctx`.
- **Evaluation**: `SecretHitler/Achievements.py` — `build_context(cur, game, game_endcode, uid, player)` builds a `Ctx` (dict subclass) per (game, uid) with derived fields (`role`, `party`, `won`, `killed_roles`, guess data, MVP data, etc.) plus lazy DB-backed methods (`history()`, `kills_history()`, `mvp_count()`) for cumulative achievements. `evaluate_and_store(cur, game, game_endcode, game_id)` loops every player × every `Logro`, inserting with `ON CONFLICT (uid, achievement_code) DO NOTHING RETURNING id` so it can atomically tell which unlocks are *new*; it never propagates exceptions (a broken check must not break game-end). It runs twice per game: once inside `StatsExtended.save_extended_game_stats()` right after the game ends, and again inside `StatsExtended.finalize_mvp_stats()` once the post-game MVP vote closes (the second pass only picks up MVP-count achievements, since `mvp` is the only column that changes between the two passes — see below).
- **Persistence**: `SecretHitler/StatsExtended.py` — `stats_secret_hitler_games` (one row per game, holds `game_endcode`) and `stats_secret_hitler_players` (one row per player per game: `role`, `party`, `won`, `died`, `killed_by_uid`, `mvp`) back `Ctx.history()` / `kills_history()` / `mvp_count()`.
- **Adding an achievement**: write a `_check_*(ctx)` predicate, add a `Logro(...)` to `LOGROS`. If it needs data not already on `Ctx`, add a field in `Achievements.build_context()` (and a helper method on `Ctx`/`Game` if it needs its own query or cross-player computation — see `Game.compute_mvp()` / `Game.compute_best_guessers()`, shared between the end-game reveal text and achievement checks so they can't disagree).
- **Retroactive grants**: achievements only evaluate at game-end time, so fixing a `check()` predicate does *not* retroactively grant it to players who were already eligible — they only get it on their *next* completed game (see the `Primera vez` fix: `==1` only ever fires once, at the exact moment a player's history hits length 1; changed to `>=1` to match `Veterano`/`Leyenda`'s pattern). For a one-shot backfill, write a dedicated `INSERT ... SELECT DISTINCT ... ON CONFLICT DO NOTHING` (see `Achievements.backfill_primera_partida()`) with `game_id = NULL` — the schema supports that for grants not tied to a specific game — and wire it behind `/admin` (see below).

#### Post-game commands (`/guess`, `/mvp`, `/end`)

- **`/guess`** — private, role-aware, offered any time during the match (up to 2 attempts, second is definitive; both saved in `Game.guesses[uid]` as a list). What a player is asked depends on their role, since Fascista/Hitler already know the "answer" from their private role reveal and a naive guess would be trivial: **Liberal** guesses the fascist team + Hitler (the original/default flow); **Hitler** only guesses fascist teammates (guessing "who is Hitler" would be pointless — it's themselves); **Fascista** instead predicts which *Liberal* will score best at guessing (a genuinely uncertain question even for a player who knows the truth). Revealed at game end via `Commands.format_guesses_reveal()`, in three separate sections matching those three roles.
- **`/mvp`** — private, one vote per player (no self-votes), usable **only after the match has ended**, changeable while votes are still outstanding. Unlike every other post-game action, `end_game()` does **not** delete the game the instant it ends — the game stays alive (in memory and DB) specifically so `/mvp` has something to operate on, until either every player has voted or `/end` force-closes it early (any player in the game can do this, for when someone won't participate). Whichever closes it calls `Commands._finalize_mvp()`, which reveals the tally, updates the `mvp` column via `StatsExtended.finalize_mvp_stats()`, and re-runs achievement evaluation before finally deleting the game.
- **`/calltovote`** pings players who haven't voted Ja/Nein (mid-game) — or, once the match has ended, whoever hasn't voted `/mvp` yet.
- **Gotcha**: every win path in `MainController.py` must set `game.board.state.game_endcode` *before* calling `end_game()` — `/mvp`, `/end`, and `/calltovote`'s post-game branch all gate on that field to know the match is over. A past bug in the kill-Hitler win path (`choose_kill()`) called `end_game(bot, game, 2)` without setting the field, silently leaving affected games stuck looking "still in progress" forever. `Commands._game_has_ended(game)` self-heals this class of bug: if the field reads `0` but `game.stats_game_id` is already set (meaning `end_game()` genuinely ran and stats were saved using the correct code, since that path uses the function parameter, not the field), it looks up the real `game_endcode` from `stats_secret_hitler_games` and repairs the field in place.

#### Admin tooling (`/fix*`, `/admin`)

ADMIN-only commands (`if uid != ADMIN: return`, silent no-op otherwise) are deliberately excluded from the public `commands` help list and the Telegram `/`-menu (`set_my_commands`). `/fix`, `/fix2`–`/fix5` patch a specific in-progress game's state (deck contents, chancellor, drawn-policy count, etc.), following a shared shape: `command_fixN` resolves the target game (direct in a group, a game-picker in DM), delegates to `_apply_fixN(bot, game, ...)`, with a matching `callback_fixN_game` for the DM picker. `/admin` is a small, growing button-driven panel (`callback_data="admin_<action>"`, no `cid`/`uid` needed since it's never game-scoped) for operations that don't belong to one game — e.g. its `first` button runs the `Primera vez` backfill above.

### Config (`Constants/Config.py`)

- `TOKEN`: main bot token (or set via DB)
- `ADMIN`: list of admin Telegram user IDs; `ADMIN[0]` is the primary admin
- `JUEGOS_DISPONIBLES`: registry of all games with commands, `restriccion` (admin-only flag), and `permitir_ingreso_tardio` (late-join allowed)
- `MODULOS_DISPONIBES`: per-game modes with `min_jugadores` / `max_jugadores`
- `HOJAS_AYUDA`: in-game help text per game

### Constants/Cards.py

Large file (~93KB) containing all game card definitions (`cartas_aventura`), player role sets (`playerSets`), action sequences (`actions`), button configurations (`comandos`), and other game data referenced by multiple controllers.
