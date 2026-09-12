# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Autoría de los commits

Todo lo que se sube a este repo va a nombre del dueño del repo, no de Claude. Antes de commitear, corré:

```bash
git config --local user.name "Eduardo Peluffo"
git config --local user.email "leviatas@gmail.com"
git config --local commit.gpgsign false
```

`commit.gpgsign false` es a propósito: la clave de firma del entorno del agente no es la del dueño del repo, así que un commit firmado con ella queda "Unverified" en GitHub y con identidad mezclada. Esto se aplica solo localmente (no toca la config global) y se re-aplica automáticamente al arrancar una sesión de Claude Code gracias al hook `SessionStart` en `.claude/settings.json`.

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

#### Expansión Socialista (`Game.modo`)

A game is either `modo = "clasico"` (the default, unchanged) or `modo = "socialista"`, chosen once at creation with `/newgame socialista` and never switched afterwards. The mode is the single switch every other rule branches off: `Game.es_socialista()` / `Board.es_socialista()` (both `getattr`-based, so games saved before the expansion load as classic), and `Commands.limites_jugadores(game)` for the player range (5-10 classic, **6-13** socialist).

- **Data** (`Constants/Cards.py`): `socialistSets` mirrors `playerSets` but is keyed 6-13 and built from small helpers instead of literal lists. Per player count it holds `roles` (adds the `Socialista` role), `track`, `socialist_track`, `liberal_track` (how many liberal policies win — **6 only at 8 players**, which also swap a fascist policy for a liberal one: 6/9/8 instead of 5/10/8), and `policies`. The fascist track is a **single** track for the whole expansion (`PISTA_FASCISTA_SOCIALISTA`: empty, inspect, policy peek, kill, kill, win) — it does *not* vary by player count and is not any of the classic ones. The socialist track comes in three printed variants: `PISTA_SOCIALISTA_CORTA` (6-8, five policies to win), `PISTA_SOCIALISTA_CONGRESO` (9-10, the only one with Confesión), `PISTA_SOCIALISTA_DOBLE_RECLUTAMIENTO` (11+, two Recruitments, no Escucha/Congreso, first slot empty). All of these come from the expansion's printed boards — don't "fix" them to look symmetric.
- **Third party**: `party` now has a third value, `"socialista"`. **Affiliation, not role, decides who wins** — that's the whole point of Recruitment — with one exception: Hitler wins with the fascists "regardless of your Party Membership card", even after being recruited. That exception lives in exactly one place, **`Player.party_efectiva()`** (`"fascista"` when `role == "Hitler"`, otherwise `party`), and everything that asks "what team is this player really on" goes through it: `Game.get_socialist_team()`, `action_congreso()`'s new-socialist list, `StatsExtended.save_extended_game_stats` (which also *stores* the effective party, so `won` and `party` in the DB can't contradict each other) and `Achievements.build_context`. Raw `player.party` is only for what other players *see* — investigations, Escucha, Confesión, the `/info` header. New end code: **`3` = socialists enacted their whole track**. Socialists lose every Hitler-related ending by construction, since those set `-2`/`2`.
- **Chairman** (`state.chairman`): after a successful vote the chancellor picks a Presidente de la Cámara, who privately peeks the top policy before the president draws. `voting_aftermath` goes through `start_legislative_session()`, which only inserts that step for socialist games without censorship. The peek runs `shuffle_policy_pile()` *first*, so the card shown is really the one the president will draw. Reset to `None` in `start_round`; the last Chairman is **not** term-limited, so chancellor eligibility is untouched.
- **Censorship** is not a track slot: it's derived (`Board.hay_censura()`, `socialist_track >= CENSURA_DESDE`, i.e. 3) and works like the Hitler zone — once on, no more Chairman for the rest of the game.
- **Socialist powers** run from `socialist_action()` and belong to the *party*, not the president, with two consequences: they fire **even when the policy came from anarchy** (explicit in the rules, unlike presidential powers), and every target-picking power (Escucha, Reclutamiento, Confesión) is decided by the **whole party, unanimously**. The picker goes to every living socialist; whoever clicks first only *proposes* (`_claim_socialist_power` lets exactly one proposal exist at a time), which opens `state.socialist_proposal` — `{"power", "target", "proposer", "approvals": [uid, ...]}`, plain string keys and uids in a **list** so jsonpickle leaves them as ints. The other living socialists get Sí/No (`_socvoto_` → `handle_socialist_vote`); one **No** drops the proposal and re-opens the picker for everyone (`_ofrecer_poder_socialista`), while the last **Sí** applies it through `_aplicar_poder_socialista` → `_aplicar_escucha` / `_aplicar_reclutamiento` / `_aplicar_confesion`. With a single living socialist there is nobody to consult, so it applies straight away — which is every 6-8 player game until they recruit someone. `start_round()` clears any proposal so one can't outlive its round. Escucha, Reclutamiento and Congreso are night actions and therefore **secret**: the group is told the power was used but never who was targeted — that goes to `hiddenhistory` (revealed at game end), never to `history`. Confesión is public and does get announced. Recruitment **does** flip Hitler's `party` to `"socialista"` — the socialists physically swap his card, so from then on investigating/bugging/confessing him shows *socialista*, which is real camouflage — but `party_efectiva()` keeps him fascist for everything that matters: he never gets the powers' buttons, doesn't wake for Congreso, and still wins with the fascists. The socialists only find out it failed at Congreso, which reports "no new socialist ⇒ you recruited Hitler". `state.recruited_uids` is deliberately a **list**, not a dict, so jsonpickle doesn't stringify the uids.
- **`/role`** offers `opciones_choose_posible_role_socialista` instead of the classic set when the game is socialist — the same options plus `Socialista` and its pairs. `Commands.choose_posible_role()` resolves the game by `cid` to pick the set, so it also covers the call made from `command_join()`. Each option key is what lands in `Player.preference_rol` and `inform_players()` splits it on `_`, so every segment of a key must be a literal role name. Note the preference has always been best-effort, in both modes: players are served in shuffled order and one without a preference can take a role someone else asked for, so asking for `Socialista` in a 10-player game gets it ~70% of the time rather than always.
- **`/explainsocialista`** (`Commands.command_explainsocialista`) is the in-chat explanation of the mode and everything it changes vs. the classic game. It's static text sent in two `send_chunked_message` calls (it doesn't fit in Telegram's 4096-char limit), and it's the one place that describes the tracks in prose — if you ever change `socialistSets`, the powers, or `CENSURA_DESDE`, update that text too or it starts lying.
- **Gotcha**: any code reading `playerSets[len(playerlist)]` must pick the set by mode instead — see `MainController.get_role_set()` and `Commands._guess_num_fascists()`. `/guess` is unchanged otherwise: a Socialista plays the same "full" flow as a liberal, which is why `Game.compute_best_guessers()` excludes by role `Hitler`/`Fascista` rather than requiring `Liberal`.

#### Achievements system

- **Catalog**: `SecretHitler/Constants/Achievements.py` — a flat `LOGROS` list of `Logro` namedtuples (`code, name, description, emoji, categoria, secreto, check`). `code` is the stable key persisted in `achievements_secret_hitler_players.achievement_code`; **never rename it** once shipped, or you orphan everyone's unlocks for it. `secreto=True` hides `name`/`description` in `/logros` until unlocked. `check(ctx)` is a pure predicate over an `Achievements.Ctx`. `categoria` must be one of `CATEGORIAS` (that list is also the display order in `/logros`), which includes `socialista` ("Expansión Socialista") for everything the expansion added. The full catalog no longer fits in one Telegram message, so `/logros` goes out through `send_chunked_message`.
- **Socialist achievements**: they all read *affiliation*, never role, so a recruited player counts as a socialist and Hitler never does — that is `Ctx["party"]`, which `build_context` fills from `Player.party_efectiva()`. The expansion-specific `Ctx` fields are `es_modo_socialista`, `was_recruited`, `recruited_uids` and `hitler_reclutado`; the last two come from `state.recruited_uids` / the Hitler player and are what `revolucion_pura` ("won without recruiting anyone", hence only reachable by socialists of origin) and `reclutamos_a_hitler` ("the party burned its Recruitment on Hitler", awarded to the socialists and never to Hitler himself) hang off. Counting *socialists of origin* over a history (`camarada_de_hierro`, `ideologo_completo`) goes by `role == "Socialista"` instead, since a recruited player keeps their original role. The `/guess`-based achievements that used to require `role == "Liberal"` now go through `_hace_guess_completo(ctx)` (`Liberal` or `Socialista`), because a Socialista answers the exact same "full" guess flow — the same reason `Game.compute_best_guessers()` excludes by role `Hitler`/`Fascista` rather than requiring `Liberal`.
- **Evaluation**: `SecretHitler/Achievements.py` — `build_context(cur, game, game_endcode, uid, player)` builds a `Ctx` (dict subclass) per (game, uid) with derived fields (`role`, `party`, `won`, `killed_roles`, guess data, MVP data, etc.) plus lazy DB-backed methods (`history()`, `kills_history()`, `mvp_count()`) for cumulative achievements. `evaluate_and_store(cur, game, game_endcode, game_id)` loops every player × every `Logro`, inserting with `ON CONFLICT (uid, achievement_code) DO NOTHING RETURNING id` so it can atomically tell which unlocks are *new*; it never propagates exceptions (a broken check must not break game-end). It runs twice per game: once inside `StatsExtended.save_extended_game_stats()` right after the game ends, and again inside `StatsExtended.finalize_mvp_stats()` once the post-game MVP vote closes (the second pass only picks up MVP-count achievements, since `mvp` is the only column that changes between the two passes — see below).
- **Persistence**: `SecretHitler/StatsExtended.py` — `stats_secret_hitler_games` (one row per game, holds `game_endcode`) and `stats_secret_hitler_players` (one row per player per game: `role`, `party`, `won`, `died`, `killed_by_uid`, `mvp`) back `Ctx.history()` / `kills_history()` / `mvp_count()`. `stats_secret_hitler_formulas` (one row per *enacted* formula: `round`, `president_uid`, `chancellor_uid`, `policy`) is collected during play in `Game.formula_history` (appended in `MainController.enact_policy()`, skipped for anarchy enactments since those weren't voted on) and flushed to the table in the same transaction as `save_extended_game_stats()`. Not wired into any achievement yet — captured for future stats/achievements use.
- **Adding an achievement**: write a `_check_*(ctx)` predicate, add a `Logro(...)` to `LOGROS`. If it needs data not already on `Ctx`, add a field in `Achievements.build_context()` (and a helper method on `Ctx`/`Game` if it needs its own query or cross-player computation — see `Game.compute_mvps()` / `Game.compute_best_guessers()`, shared between the end-game reveal text and achievement checks so they can't disagree).
- **Retroactive grants**: achievements only evaluate at game-end time, so fixing a `check()` predicate does *not* retroactively grant it to players who were already eligible — they only get it on their *next* completed game (see the `Primera vez` fix: `==1` only ever fires once, at the exact moment a player's history hits length 1; changed to `>=1` to match `Veterano`/`Leyenda`'s pattern). For a one-shot backfill, write a dedicated `INSERT ... SELECT DISTINCT ... ON CONFLICT DO NOTHING` (see `Achievements.backfill_primera_partida()`) with `game_id = NULL` — the schema supports that for grants not tied to a specific game — and wire it behind `/admin` (see below).

#### Post-game commands (`/guess`, `/mvp`, `/end`) and test games (`/prueba`)

- **`/guess`** — private, role-aware, offered any time during the match (up to 2 attempts, second is definitive; both saved in `Game.guesses[uid]` as a list). What a player is asked depends on their role, since Fascista/Hitler already know the "answer" from their private role reveal and a naive guess would be trivial: **Liberal** guesses the fascist team + Hitler (the original/default flow); **Hitler** only guesses fascist teammates (guessing "who is Hitler" would be pointless — it's themselves); **Fascista** instead predicts which *Liberal* will score best at guessing (a genuinely uncertain question even for a player who knows the truth). Revealed at game end via `Commands.format_guesses_reveal()`, in three separate sections matching those three roles. Guesses can be **partial**: every person-picking step in all three flows offers a "🤷 No sé" button (`_guessskip_<etapa>` → `callback_guess_skip`, where `etapa` is `f` fascists / `h` Hitler / `p` the Fascista prediction) that leaves that part blank — an unfinished fascist list, no Hitler pick, or no prediction — so a player can record what they actually suspect instead of padding it with noise. A blank slot is stored as a short list / a `None` or missing key, which `compute_guess_score()` already handles (it simply scores fewer points) and which every guess-related achievement predicate already guards against, and the reveal text distinguishes "no arriesgó" from having guessed wrong. Nothing is refused for being blank, including a guess left *entirely* blank: "No sé" is a valid answer in its own right, and in two of the flows it is the only way to express "no idea" at all — the Fascista prediction is a single field, and Hitler has only one fascist teammate to name in games of 6 players or fewer.
- **`/mvp`** — private, one vote per player (no self-votes), usable **only after the match has ended**, changeable while votes are still outstanding. Unlike every other post-game action, `end_game()` does **not** delete the game the instant it ends — the game stays alive (in memory and DB) specifically so `/mvp` has something to operate on, until either every player has voted or `/end` force-closes it early (any player in the game can do this, for when someone won't participate). Whichever closes it calls `Commands._finalize_mvp()`, which reveals the tally, updates the `mvp` column via `StatsExtended.finalize_mvp_stats()`, and re-runs achievement evaluation before finally deleting the game. A game can have **more than one MVP**: `Game.compute_mvps()` returns a list — the single most-voted player wins; if the top spot is *tied*, the tied players share the MVP only when they reach `VOTOS_MVP_COMPARTIDO` (4) votes each (i.e. 4-4 or 5-5; with the 10-player cap three players can never all tie at 4), and a tie below that threshold means no MVP. A player with strictly more votes than everyone else always wins alone, even when the runner-up also reached 4. Both the reveal text and the `mvp = TRUE` write go through that one method, and the MVP-count achievements read the column, so co-MVPs each get credit automatically.
- **`/calltovote`** pings players who haven't voted Ja/Nein (mid-game) — or, once the match has ended, whoever hasn't voted `/mvp` yet.
- **`/prueba`** — toggles whether the group's current game counts. A test game (`Game.es_partida_de_prueba`, read through the `getattr`-based `Game.es_prueba()` so pre-existing saved games load as real) is played exactly like any other — roles, powers, `/guess`, the end-of-game reveal and the hidden history all behave normally — but `end_game()` skips `save_game_details()` and `StatsExtended.save_extended_game_stats()` (so no `stats_*` rows, no formula history and, since achievements are evaluated inside that call, no unlocks), routes every `set_stats()` through a local `contar_stat()` that no-ops, and offers no MVP vote. With nothing left to wait for, a test game is deleted the moment it ends, on the same branch as a cancelled one — which also means `/guessresults` and `/miguess` can't be used afterwards, unlike a real game. The command is group-only, allowed to any player in the game (or the initiator/ADMIN before anyone joined), refuses to switch once the match has ended (stats are already written or already discarded by then), and always answers with which mode the game is now in. `/mvp` and `/end` answer with that same notice instead of a vote, and `print_board()` prepends a reminder to `/board` so nobody forgets mid-match that the game doesn't count. The flag lives on the game, so it resets with every `/newgame`.
- **Gotcha**: every win path in `MainController.py` must set `game.board.state.game_endcode` *before* calling `end_game()` — `/mvp`, `/end`, and `/calltovote`'s post-game branch all gate on that field to know the match is over. A past bug in the kill-Hitler win path (`choose_kill()`) called `end_game(bot, game, 2)` without setting the field, silently leaving affected games stuck looking "still in progress" forever. `Commands._game_has_ended(game)` self-heals this class of bug: if the field reads `0` but `game.stats_game_id` is already set (meaning `end_game()` genuinely ran and stats were saved using the correct code, since that path uses the function parameter, not the field), it looks up the real `game_endcode` from `stats_secret_hitler_games` and repairs the field in place.

#### Group membership & next-game notifications (`/all`, `/nextgame`)

Telegram gives bots no API to enumerate a group's membership, so both features work by having the bot passively record who it sees and act on that later.

- **`/all`** — mentions every known active, non-bot member of the group (`[Name](tg://user?id=X)`, sent via `Commands.send_chunked_message` since a big group can exceed Telegram's message-length limit). Membership is tracked in `group_members_secret_hitler` (`cid, uid, name, is_bot, active`, PK `(cid, uid)`) via `SecretHitler/GroupMembers.py` (`upsert_member()` / `get_active_members()`). Kept in sync by two `MessageHandler`s in `MainController.main()` for Telegram's `new_chat_members` (`active=True`) and `left_chat_member` (`active=False`) status updates, plus a call from `command_join()` (so a member who joined a game before this tracking existed still gets backfilled into the table the next time they `/join`).
- **`/nextgame`** — a player asks to be notified the next time someone creates a game in this group. It doesn't send anything immediately: it stores `(cid, uid, name)` in `nextgame_secret_hitler_waitlist` via `SecretHitler/NextGame.py` (`add_waiting()`), persisted (rather than in-memory) because an arbitrary amount of time — and possibly a bot restart — can pass between `/nextgame` and the `/newgame` that triggers it. On `/newgame`'s success path (a game didn't already exist, so a new `Game` was actually created), `Commands.command_newgame()` calls `NextGame.pop_waiting(cid)`, which atomically returns and deletes that group's waitlist rows, and DMs each of them that a new game just started. The wait is one-shot: it's cleared the moment it fires, so a player who wants to be notified again has to `/nextgame` again.

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
