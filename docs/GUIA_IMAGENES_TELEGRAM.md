# Guía para IAs: generar imágenes y enviarlas a Telegram (html2image)

> Documento pensado para que otra IA/agente entienda **cómo este repo genera imágenes
> (tableros, cartas, paneles) y las manda a Telegram**, y pueda reutilizar la técnica
> para cualquier otra cosa. Caso de referencia: **Secreto Código** (Codenames),
> `SecretoCodigo/render.py`. Segundo ejemplo más completo: `BattlestarGalactica/render.py`.

---

## 1. Idea general

En vez de dibujar píxel a píxel, **se arma un HTML+CSS en un string de Python** y se le
saca una "captura de pantalla" con Chrome/Chromium headless usando la librería
**`html2image`**. El PNG resultante se carga en un `BytesIO` y se manda con
`bot.send_photo(...)` de `python-telegram-bot`.

```
estado del juego ──► string HTML/CSS ──► html2image (Chrome headless) ──► PNG en disco temporal
                                                                          │
                          bot.send_photo(chat_id, photo=BytesIO) ◄────────┘
```

Ventajas frente a dibujar con Pillow:
- Layout con **CSS grid/flex**: centrado, bordes redondeados, sombras, wrapping gratis.
- Se puede usar **JavaScript** dentro del HTML (ej.: achicar la fuente hasta que la palabra entre).
- Cambiar el diseño es editar CSS, no recalcular coordenadas.

El repo también tiene una versión Pillow (`render_board` en `SecretoCodigo/render.py`),
que hoy solo usan los comandos de demo `/demotablero` y `/demotablero2`. La que usa el juego es
**`render_html_to_bytesio`** (html2image).

---

## 2. Qué instalar

### Python
```txt
# requirements.txt
html2image>=2.0.4
python-telegram-bot[job-queue]==22.6
pillow>=10.2.0        # solo si además querés post-procesar la imagen o usar el fallback Pillow
```
```bash
pip install html2image
```

### Navegador (obligatorio)
`html2image` **no trae navegador**: usa uno instalado en el sistema (Chrome, Chromium o Edge).

- **Docker Debian slim (lo que usa `Dockerfile2`, el de docker-compose):**
  ```dockerfile
  RUN apt-get update \
      && apt-get install -y --no-install-recommends chromium \
      && rm -rf /var/lib/apt/lists/*
  ```
  Ejecutable: `/usr/bin/chromium`.
- **`Dockerfile` (Fly.io):** instala `google-chrome-stable` → `/usr/bin/google-chrome-stable`.
- **Windows/macOS local:** con tener Chrome o Edge instalado, `html2image` lo detecta solo.

### Fuentes
Chromium headless solo usa las fuentes instaladas en el sistema. En imágenes slim puede
no haber casi ninguna. Recomendado:
```dockerfile
RUN apt-get install -y --no-install-recommends fonts-liberation fonts-dejavu-core
# opcional, para emojis a color:
RUN apt-get install -y --no-install-recommends fonts-noto-color-emoji
```
Y en el CSS siempre dar una cadena de respaldo: `font-family: 'Liberation Sans', Arial, sans-serif;`.

---

## 3. Uso correcto de html2image (patrón canónico)

```python
import os
import tempfile
from io import BytesIO

_CHROME_CANDIDATOS = [
    "/usr/bin/google-chrome-stable",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]
_CHROME_FLAGS = [
    "--no-sandbox",               # necesario corriendo como root en Docker
    "--disable-setuid-sandbox",
    "--disable-gpu",              # no hay GPU en el contenedor
    "--hide-scrollbars",          # sin barras de scroll en la captura
    "--force-color-profile=srgb", # colores consistentes
]


def _chrome_path():
    for p in _CHROME_CANDIDATOS:
        if os.path.exists(p):
            return p
    return None  # html2image intentará encontrarlo solo (útil en Windows/macOS)


def html_to_png_bytesio(html: str, width: int, height: int) -> BytesIO:
    from html2image import Html2Image  # import perezoso: el módulo carga aunque falte la lib
    with tempfile.TemporaryDirectory() as tmpdir:
        kwargs = dict(output_path=tmpdir, size=(width, height), custom_flags=_CHROME_FLAGS)
        chrome = _chrome_path()
        if chrome:
            kwargs["browser_executable"] = chrome
        hti = Html2Image(**kwargs)
        paths = hti.screenshot(html_str=html, save_as="render.png")
        with open(paths[0], "rb") as f:
            buf = BytesIO(f.read())
    buf.seek(0)          # ¡importante! si no, Telegram recibe un archivo vacío
    return buf
```

Puntos clave:
1. **`output_path` en un `TemporaryDirectory`**: html2image siempre escribe a disco. Usar un
   directorio temporal evita choques entre partidas simultáneas (mismo `save_as`) y basura
   en el disco. Se lee el archivo **dentro** del `with`, antes de que se borre.
2. **`size=(w, h)`** es el tamaño de la ventana = tamaño exacto del PNG. Lo que quede fuera
   se recorta. Calculá el tamaño a partir del layout (ver §4), no lo adivines.
3. **`screenshot()` devuelve una lista** de rutas → usar `paths[0]`.
4. **`buf.seek(0)`** antes de devolver.
5. En el HTML: `margin:0; padding:0` en `body` y un `background` explícito, o aparecen
   bordes blancos.
6. Es **bloqueante** (lanza un proceso de Chrome, ~0.5–2 s). Ver §6 para no trabar el bot.

---

## 4. Cómo se usa en Secreto Código (Codenames)

Archivo: `SecretoCodigo/render.py`.

### 4.1 Datos de entrada
El tablero es una lista de 25 dicts guardada en `game.board.state.tablero`:
```python
{"word": "GATO", "numero": 13, "revealed": False, "tipo": "rojo"}  # tipo: rojo|azul|neutral|asesino|agente
```

### 4.2 Paleta = diccionario `clave → (fondo, texto)`
```python
_HTML_PALETTE = {
    "unrevealed":       ("#FFE5CC", "#1A1A1A"),
    "rojo":             ("#C0392B", "#FFFFFF"),
    "azul":             ("#1A5276", "#FFFFFF"),
    "revealed_rojo":    ("#F1948A", "#5D0000"),
    # ...
}
```
El **modo** decide qué clave usar por carta (esto es la "lógica de visibilidad"):
- `public`: cartas sin revelar todas iguales; reveladas con el color de su tipo.
- `spymaster`: todos los colores visibles (se manda **por privado** al espía).
- `duo_key`: la clave privada de un jugador en modo Dúo (verde/negro/neutro).
- `duo_public`: tablero público del modo Dúo.

> Regla: **la información secreta se decide al generar la imagen**, no al enviarla.
> Una imagen para el grupo nunca debe contener datos ocultos (ni siquiera en CSS invisible).

### 4.3 Armado del HTML (`render_board_html`)
- Una celda `div` por carta con estilos inline (`background`, `color`, `display:flex`
  centrado, `border-radius`), número chico en la esquina (`position:absolute`), palabra en
  un `span.word`, `text-decoration: line-through` si está revelada.
- Contenedor con `display:grid; grid-template-columns:repeat(5, 200px); gap:10px`.
- Tamaño calculado: `canvas = COLS * CELL + (COLS + 1) * PAD` → 5·200 + 6·10 = **1060 px**.
- **Script de ajuste de texto**: achica la fuente de cada palabra hasta que entra en la celda:
  ```js
  document.querySelectorAll('.cell').forEach(function(cell) {
      var span = cell.querySelector('.word');
      var maxW = 200 - 12, size = parseInt(span.style.fontSize);
      while (span.scrollWidth > maxW && size > 8) { size--; span.style.fontSize = size + 'px'; }
  });
  ```
  ⚠️ Como el HTML está en un f-string de Python, **las llaves de CSS/JS van dobladas** `{{ }}`.

### 4.4 Render y envío
`render_html_to_bytesio(tablero, mode, key, font_size)` → arma el HTML y aplica el patrón del §3.

`SecretoCodigo/Boardgamebox/Board.py` expone helpers para el resto del juego:
```python
def render_board_image(self, game):     return render_html_to_bytesio(self.state.tablero, mode="public")
def render_spymaster_image(self, game): return render_html_to_bytesio(self.state.tablero, mode="spymaster")
```
Y el Controller los envía (`SecretoCodigo/Controller.py`):
```python
await bot.send_photo(
    game.cid,
    photo=game.board.render_board_image(game),
    caption=f"{emoji} Turno del equipo *{team}*...",
    parse_mode=ParseMode.MARKDOWN,
)
# versión secreta, por privado al espía (uid = chat privado)
await bot.send_photo(sm.uid, photo=game.board.render_spymaster_image(game), caption="...")
```

### 4.5 Truco anti-caché (versión Pillow)
Telegram puede deduplicar imágenes idénticas. La versión Pillow cambia un píxel según la hora:
```python
ts = int(time.time() * 1000) % (256 ** 3)
img.putpixel((0, 0), (ts >> 16, (ts >> 8) & 0xFF, ts & 0xFF))
```
Si alguna vez ves que Telegram muestra una imagen vieja, aplicá lo mismo en HTML
(ej.: un `div` de 1×1 px en la esquina con un color derivado del timestamp).

### 4.6 Comandos de demo para probar
- `/demotablero [tamaño_fuente]` → versión Pillow, `send_photo`
- `/demotablero2 [tamaño_fuente]` → versión Pillow, `send_document` (sin compresión)
- `/demotablero3 [tamaño_fuente]` → versión html2image

---

## 5. Enviar a Telegram: detalles importantes

| Método | Cuándo | Notas |
|---|---|---|
| `bot.send_photo(chat_id, photo=buf, caption=...)` | Caso normal | Telegram **recomprime** a JPEG y limita el lado mayor a ~1280 px (se ve en miniatura en el chat). Máx 10 MB. Ancho+alto ≤ 10000 y relación de aspecto ≤ 20. |
| `bot.send_document(chat_id, document=buf, filename="x.png")` | Necesitás nitidez total (texto chico) | Sin compresión, pero se ve como archivo, no como foto. |
| `bot.send_media_group(...)` | Varias imágenes juntas | `InputMediaPhoto(buf)` por cada una (máx 10). |
| `bot.edit_message_media(...)` | Actualizar la misma imagen en lugar de mandar otra | `InputMediaPhoto(nuevo_buf)`. |

- `caption` admite hasta **1024 caracteres**; usar `parse_mode` si tiene markdown y escapar nombres de usuario.
- Un `BytesIO` **se consume** al enviarlo: para mandar la misma imagen a dos chats, generá dos
  veces o hacé `buf.getvalue()` y creá `BytesIO(datos)` para cada envío.
- Para mandar a un jugador por privado usar su `uid` como `chat_id` (el jugador tiene que
  haber iniciado el bot antes, si no da `Forbidden`).

---

## 6. Consejos para usarlo en cualquier otra cosa

**Diseño**
1. **Separá en tres funciones**: `build_html(datos) -> (html, w, h)`, `html_to_png_bytesio(html, w, h)`,
   y el envío. Así podés testear el HTML abriéndolo en un navegador sin Telegram.
2. **Calculá el alto** en base al contenido (filas × alto de fila + cabecera), como hace
   BSG: `canvas_h = 150 + 470 + 40 + 5 * 78 + 70`. Si el contenido es variable, poné
   un tamaño holgado y `overflow:hidden`, o fijá alturas por fila.
3. **Diseñá para móvil**: la mayoría mira Telegram en el celular. Ancho útil 800–1280 px,
   fuentes ≥ 20 px, alto contraste. Con más de 1280 px de ancho Telegram reduce la imagen.
4. Poné el CSS en un bloque `<style>` con clases en vez de todo inline cuando el diseño
   crece (ver `BattlestarGalactica/render.py`).
5. **Emojis**: en headless pueden salir como cuadrados si no hay fuente de emoji. BSG los
   evita a propósito y dibuja las fichas con formas/etiquetas CSS. Hacé lo mismo o instalá
   `fonts-noto-color-emoji`.
6. **Imágenes externas** (cartas, iconos): preferí incrustarlas como `data:image/png;base64,...`
   o rutas `file:///` absolutas. URLs remotas pueden no terminar de cargar antes de la captura.

**Seguridad y robustez**
7. **Escapá todo texto que venga de usuarios** (nombres, pistas) antes de meterlo al HTML:
   ```python
   def _esc(t):
       return (str(t).replace("&", "&amp;").replace("<", "&lt;")
               .replace(">", "&gt;").replace('"', "&quot;"))
   ```
   (o `html.escape(t, quote=True)` de la stdlib). Si no, un nombre con `<script>` se ejecuta en Chrome.
8. **Siempre con fallback**: envolvé el render en `try/except` y, si falla, mandá la versión en texto
   (así hace `command_mapa_img` en BSG):
   ```python
   try:
       buf = render_board_image(game)
       await bot.send_photo(cid, photo=buf, caption="🗺️ Tablero")
   except Exception as e:
       log.error(f"render error: {e}")
       await bot.send_message(cid, game.board.print_map(game), parse_mode=ParseMode.MARKDOWN)
   ```
9. **No bloquees el event loop**: el bot es async y Chrome tarda. Para renders frecuentes:
   ```python
   buf = await asyncio.to_thread(html_to_png_bytesio, html, w, h)
   ```
10. **Detección del ejecutable** con lista de candidatos (§3) en vez de una ruta fija:
    `SecretoCodigo/render.py` tiene `/usr/bin/chromium` fijo y solo funciona con `Dockerfile2`.
11. **No guardes el `BytesIO` en el objeto `Game`**: el juego se serializa con `jsonpickle` a
    PostgreSQL. Guardá los datos y generá la imagen cada vez.
12. Si ves la imagen en blanco o cortada: revisá `size`, `margin:0` del body, y que el
    contenido no dependa de recursos que tardan en cargar.

**Cuándo usar Pillow en vez de html2image**
- Componer imágenes que ya existen (pegar cartas en fila: `Utils/__init__.py`, `LostExpedition`).
- Entornos sin Chrome, o necesitás render muy rápido y muchas veces por segundo.
- Para todo lo que sea "tablero/panel con texto y colores", html2image es más simple de mantener.

---

## 7. Checklist rápido para un render nuevo

- [ ] `html2image` en `requirements.txt` y Chromium/Chrome + fuentes en la imagen Docker
- [ ] `build_html()` devuelve `(html, ancho, alto)` calculados
- [ ] `body { margin:0; background: ... }` y `font-family` con respaldo
- [ ] Llaves `{{ }}` dobladas en CSS/JS dentro de f-strings
- [ ] Texto de usuarios escapado
- [ ] Render en `TemporaryDirectory`, `paths[0]`, `buf.seek(0)`
- [ ] Flags `--no-sandbox --disable-gpu --hide-scrollbars`
- [ ] Info secreta solo en imágenes enviadas por privado
- [ ] `try/except` con fallback a texto
- [ ] Probado abriendo el HTML en un navegador y con un comando de demo en Telegram
