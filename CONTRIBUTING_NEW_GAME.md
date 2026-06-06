# Cómo crear un nuevo juego para MultigamesV2

Este documento describe el proceso estándar para agregar un nuevo juego de mesa al bot de Telegram.

---

## 1. Estructura de carpetas

Crear la siguiente estructura dentro del directorio raíz del proyecto:

```
NombreJuego/
├── Controller.py              # Lógica del juego y callbacks de botones
├── Commands.py                # Handlers de comandos de Telegram
├── Boardgamebox/
│   ├── __init__.py            # Vacío
│   ├── Game.py                # Extiende Boardgamebox.Game.Game
│   ├── Player.py              # Extiende Boardgamebox.Player.Player
│   ├── Board.py               # Extiende Boardgamebox.Board.Board
│   └── State.py               # Extiende Boardgamebox.State.State
├── Constants/
│   └── Config.py              # Constantes del juego (dificultad, configuraciones)
└── txt/
    └── spanish-original.txt   # Listas de palabras/cartas (si aplica, una por línea)
```

---

## 2. State.py

Extiende `Boardgamebox.State.State`. El atributo `fase_actual` (heredado) es la única fuente de verdad para la fase del juego.

```python
from Boardgamebox.State import State as BaseState

class State(BaseState):
    def __init__(self):
        BaseState.__init__(self)
        # Agregar acá solo los atributos específicos del juego
        self.mi_variable_de_juego = None
```

---

## 3. Board.py

Extiende `Boardgamebox.Board.Board`. Sobreescribir `self.state` con la clase State propia.

```python
from Boardgamebox.Board import Board as BaseBoard
from NombreJuego.Boardgamebox.State import State

class Board(BaseBoard):
    def __init__(self, playercount, game):
        BaseBoard.__init__(self, playercount, game)
        self.state = State()

    def print_board(self, game) -> str:
        # Retorna un string Markdown con el estado visual del tablero
        board = ""
        # ... construir el mensaje
        return board
```

---

## 4. Player.py

Extiende `Boardgamebox.Player.Player`. Sobreescribir `get_private_info` para soportar el comando `/info`.

```python
from Boardgamebox.Player import Player as BasePlayer

class Player(BasePlayer):
    def __init__(self, name, uid):
        BasePlayer.__init__(self, name, uid)
        self.mi_atributo = None

    def get_private_info(self, game) -> str:
        return f"--- Info de {self.name} ---\n..."
```

---

## 5. Game.py

Extiende `Boardgamebox.Game.Game`. Métodos obligatorios:

```python
from Boardgamebox.Game import Game as BaseGame
from NombreJuego.Boardgamebox.Player import Player
from NombreJuego.Boardgamebox.Board import Board

class Game(BaseGame):
    def __init__(self, cid, initiator, groupName, tipo=None, modo=None):
        BaseGame.__init__(self, cid, initiator, groupName, tipo, modo)

    def add_player(self, uid, name):
        # Usar la clase Player propia del juego
        self.playerlist[uid] = Player(name, uid)

    def create_board(self):
        self.board = Board(len(self.playerlist), self)

    def call(self, context):
        # Importar dentro del método para evitar imports circulares
        import NombreJuego.Commands as MiJuegoCommands
        if self.board is not None:
            MiJuegoCommands.command_call(context.bot, self)

    def get_rules(self):
        return ["Descripción de las reglas del juego."]
```

---

## 6. Controller.py

Punto de entrada y lógica principal del juego.

### Patrones obligatorios

**Función de inicio:**
```python
async def init_game(bot, game):
    game.shuffle_player_sequence()
    game.board.state.fase_actual = "Configurando"
    await call_dicc_buttons(bot, game)  # o iniciar directamente
    await save(bot, game.cid)
```

**Botones de configuración** (usar sufijo de 2 letras para evitar colisiones):
```python
async def call_dicc_buttons(bot, game):
    opciones = {"opcion1": "Descripción 1", "opcion2": "Descripción 2"}
    await simple_choose_buttons(bot, game.cid, 1234, game.cid, "choosediccXX", "¿Elige?", opciones)

async def callback_finish_config_xx(update: Update, context: CallbackContext):
    regex = re.search(r"(-[0-9]*)\*choosediccXX\*(.*)\*([0-9]*)", callback.data)
    cid, opcion, uid = int(regex.group(1)), regex.group(2), int(regex.group(3))
    # ...
```

**Reglas generales del Controller:**
- Siempre llamar `await save(bot, game.cid)` después de cada cambio de estado.
- Usar `await bot.send_message(game.cid, texto, ParseMode.MARKDOWN)` para mensajes al grupo.
- Usar `await bot.send_message(player.uid, texto, ParseMode.MARKDOWN)` para mensajes privados.
- Los strings de `fase_actual` deben ser descriptivos en español (ej: `"Turno Rojo - Pista"`).

**Todos los action codes de callbacks deben terminar con el sufijo del juego** (2-3 letras), por ejemplo `choosediccCN`, `chooseendCN`, `pickCN`. Esto evita colisiones entre juegos.

---

## 7. Commands.py

Handlers de los comandos de Telegram.

```python
import NombreJuego.Controller as MiJuegoController
from Utils import get_game, save, player_call

async def command_micomando(update: Update, context: CallbackContext):
    bot = context.bot
    cid = update.message.chat_id
    uid = update.message.from_user.id
    game = get_game(cid)
    # validar y delegar a Controller

async def command_call(bot, game):
    # Recuerda el estado actual según fase_actual
    fase = game.board.state.fase_actual
    if "MiFase" in fase:
        await bot.send_message(game.cid, "Recordatorio de qué hacer...", parse_mode=ParseMode.MARKDOWN)
```

**Para comandos que requieren privacidad** (como dar pistas secretas):
```python
if update.effective_message.chat.type in ['group', 'supergroup']:
    await bot.delete_message(cid, update.message.message_id)
    await bot.send_message(uid, "Este comando solo se puede usar en privado.")
    return
```

---

## 8. Registrar en Constants/Config.py

Agregar en `JUEGOS_DISPONIBLES`:
```python
"NombreJuego" : {
    "comandos" : {
        "NombreJuego" : "Nombre Legible del Juego"
    },
    # "restriccion" : "admin",       # si solo admins pueden crear
    # "permitir_ingreso_tardio": True # si jugadores pueden unirse después de empezar
},
```

Agregar en `MODULOS_DISPONIBES`:
```python
"NombreJuego" : {
    "Cooperativo" : {
        "comandos" : {
            "Cooperativo" : "Cooperativo"
        },
        "min_jugadores" : 4,
        "max_jugadores" : 8
    }
},
```

---

## 9. Registrar en Commands.py (raíz)

Agregar el import de la clase Game propia:
```python
from NombreJuego.Boardgamebox.Game import Game as GameNombreJuego
```

Agregar en la función `CreateGame()`:
```python
elif tipo == 'NombreJuego':
    GamesController.games[cid] = GameNombreJuego(cid, uid, groupName, tipo)
```

Si el juego comparte un comando con otro juego (ej: `/pick`, `/guess`, `/pass`), agregar el caso al dispatcher correspondiente en `Commands.py`.

---

## 10. Registrar en MainController.py

Agregar los imports:
```python
import NombreJuego.Controller as NombreJuegoController
import NombreJuego.Commands as NombreJuegoCommands
```

Agregar en `init_game()`:
```python
elif game.tipo == "NombreJuego":
    game.create_board()
    await NombreJuegoController.init_game(bot, game)
```

Agregar los handlers en `main()`:
```python
# Handlers de NombreJuego
app.add_handler(CommandHandler("micomando", NombreJuegoCommands.command_micomando))
app.add_handler(CallbackQueryHandler(
    pattern=r"(-[0-9]*)\*choosediccXX\*(.*)\*([0-9]*)",
    callback=NombreJuegoController.callback_finish_config_xx
))
app.add_handler(CallbackQueryHandler(
    pattern=r"(-[0-9]*)\*chooseendXX\*(.*)\*([0-9]*)",
    callback=NombreJuegoController.callback_finish_game_buttons_xx
))
```

---

## Convenciones de nomenclatura

| Elemento | Convención | Ejemplo |
|---|---|---|
| Sufijo de callbacks | 2 letras mayúsculas | `CN` (Codenames), `JO` (JustOne) |
| Action codes | camelCase + sufijo | `choosediccCN`, `chooseendCN` |
| Fases (`fase_actual`) | Español descriptivo | `"Turno Rojo - Pista"` |
| Rutas a archivos txt | Absolutas desde raíz | `/NombreJuego/txt/spanish-original.txt` |
| `save()` | Siempre async/await | `await save(bot, game.cid)` |

---

## Juegos de referencia

| Juego | Complejidad | Buen ejemplo de... |
|---|---|---|
| JustOne | Media | Comandos privados, múltiples partidas activas |
| Arcana | Alta | Teams, cartas con acciones, Boardgamebox custom |
| Codenames | Media | 2 equipos, roles distintos, fases alternadas |
| Unanimo | Baja | Estructura mínima, juego cooperativo simple |
