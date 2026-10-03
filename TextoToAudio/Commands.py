import asyncio
import html
import io
import logging as log

import av
import edge_tts
import speech_recognition as sr
from gtts import gTTS
from telegram import BotCommand, BotCommandScopeChat, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from Constants.Config import ADMIN
import TextoToAudio.Storage as Storage
from TextoToAudio.version import CHANGELOG, VERSION

MAX_CARACTERES = 3000
IDIOMA = "es"
# Acento de gTTS: "com.ar" (Argentina), "es" (España), "com.mx" (México)
TLD = "com.ar"
# Voces neuronales (edge-tts) por defecto para cada género; gTTS queda como respaldo si fallan
VOCES = {
    "masculino": "es-AR-TomasNeural",
    "femenino": "es-AR-ElenaNeural",
}
# Voces en español de edge-tts que se pueden elegir con /voz, por país:
# código -> (nombre del país, [(voz, género, nombre a mostrar), ...])
VOCES_DISPONIBLES = {
    "AR": ("🇦🇷 Argentina", [("es-AR-ElenaNeural", "femenino", "Elena"), ("es-AR-TomasNeural", "masculino", "Tomás")]),
    "BO": ("🇧🇴 Bolivia", [("es-BO-SofiaNeural", "femenino", "Sofía"), ("es-BO-MarceloNeural", "masculino", "Marcelo")]),
    "CL": ("🇨🇱 Chile", [("es-CL-CatalinaNeural", "femenino", "Catalina"), ("es-CL-LorenzoNeural", "masculino", "Lorenzo")]),
    "CO": ("🇨🇴 Colombia", [("es-CO-SalomeNeural", "femenino", "Salomé"), ("es-CO-GonzaloNeural", "masculino", "Gonzalo")]),
    "CR": ("🇨🇷 Costa Rica", [("es-CR-MariaNeural", "femenino", "María"), ("es-CR-JuanNeural", "masculino", "Juan")]),
    "CU": ("🇨🇺 Cuba", [("es-CU-BelkysNeural", "femenino", "Belkys"), ("es-CU-ManuelNeural", "masculino", "Manuel")]),
    "DO": ("🇩🇴 Rep. Dominicana", [("es-DO-RamonaNeural", "femenino", "Ramona"), ("es-DO-EmilioNeural", "masculino", "Emilio")]),
    "EC": ("🇪🇨 Ecuador", [("es-EC-AndreaNeural", "femenino", "Andrea"), ("es-EC-LuisNeural", "masculino", "Luis")]),
    "ES": ("🇪🇸 España", [("es-ES-ElviraNeural", "femenino", "Elvira"), ("es-ES-XimenaNeural", "femenino", "Ximena"),
                         ("es-ES-AlvaroNeural", "masculino", "Álvaro")]),
    "GQ": ("🇬🇶 Guinea Ecuatorial", [("es-GQ-TeresaNeural", "femenino", "Teresa"), ("es-GQ-JavierNeural", "masculino", "Javier")]),
    "GT": ("🇬🇹 Guatemala", [("es-GT-MartaNeural", "femenino", "Marta"), ("es-GT-AndresNeural", "masculino", "Andrés")]),
    "HN": ("🇭🇳 Honduras", [("es-HN-KarlaNeural", "femenino", "Karla"), ("es-HN-CarlosNeural", "masculino", "Carlos")]),
    "MX": ("🇲🇽 México", [("es-MX-DaliaNeural", "femenino", "Dalia"), ("es-MX-JorgeNeural", "masculino", "Jorge")]),
    "NI": ("🇳🇮 Nicaragua", [("es-NI-YolandaNeural", "femenino", "Yolanda"), ("es-NI-FedericoNeural", "masculino", "Federico")]),
    "PA": ("🇵🇦 Panamá", [("es-PA-MargaritaNeural", "femenino", "Margarita"), ("es-PA-RobertoNeural", "masculino", "Roberto")]),
    "PE": ("🇵🇪 Perú", [("es-PE-CamilaNeural", "femenino", "Camila"), ("es-PE-AlexNeural", "masculino", "Alex")]),
    "PR": ("🇵🇷 Puerto Rico", [("es-PR-KarinaNeural", "femenino", "Karina"), ("es-PR-VictorNeural", "masculino", "Víctor")]),
    "PY": ("🇵🇾 Paraguay", [("es-PY-TaniaNeural", "femenino", "Tania"), ("es-PY-MarioNeural", "masculino", "Mario")]),
    "SV": ("🇸🇻 El Salvador", [("es-SV-LorenaNeural", "femenino", "Lorena"), ("es-SV-RodrigoNeural", "masculino", "Rodrigo")]),
    "US": ("🇺🇸 EE.UU.", [("es-US-PalomaNeural", "femenino", "Paloma"), ("es-US-AlonsoNeural", "masculino", "Alonso")]),
    "UY": ("🇺🇾 Uruguay", [("es-UY-ValentinaNeural", "femenino", "Valentina"), ("es-UY-MateoNeural", "masculino", "Mateo")]),
    "VE": ("🇻🇪 Venezuela", [("es-VE-PaolaNeural", "femenino", "Paola"), ("es-VE-SebastianNeural", "masculino", "Sebastián")]),
}
# voz -> (género, nombre a mostrar, código de país)
_INFO_VOZ = {voz: (g, nombre, cod) for cod, (_, voces) in VOCES_DISPONIBLES.items() for voz, g, nombre in voces}
TEXTO_PRUEBA = "¿Querés practicar? Elegí una letra para seguir su recorrido"
_ADJETIVO = {"femenino": "femenina", "masculino": "masculina"}
# Proveedores de texto a voz que se alternan con /switch
PROVEEDORES = {"edge": "Edge (voces neuronales de Microsoft)", "gtts": "gTTS (Google Translate)"}
PROVEEDOR_POR_DEFECTO = "edge"
ALIAS_PROVEEDOR = {"edge": "edge", "microsoft": "edge", "gtts": "gtts", "google": "gtts"}

COMANDOS = [
    BotCommand("start", "Activar el bot"),
    BotCommand("help", "Ayuda"),
    BotCommand("voz", "Elegir la voz femenina y masculina"),
    BotCommand("gender", "Alternar entre voz masculina y femenina"),
    BotCommand("switch", "Alternar el proveedor de voz (Edge / gTTS)"),
    BotCommand("version", "Ver la versión del bot"),
]
COMANDOS_ADMIN = COMANDOS + [
    BotCommand("codigo", "Ver o cambiar el código secreto"),
    BotCommand("usuarios", "Listar usuarios activados"),
    BotCommand("revocar", "Quitar acceso a un usuario"),
]
ALIAS_GENERO = {
    "m": "masculino", "masculino": "masculino", "hombre": "masculino", "male": "masculino",
    "f": "femenino", "femenino": "femenino", "mujer": "femenino", "female": "femenino",
}
# Límite de un mensaje de Telegram (con margen para el encabezado)
MAX_AVISO = 3500

# Audio a texto
IDIOMA_STT = "es-AR"
SAMPLE_RATE = 16000
SEGUNDOS_POR_PARTE = 50
MAX_SEGUNDOS_AUDIO = 10 * 60


def _es_admin(uid):
    return uid == ADMIN[0]


def _esta_autorizado(uid):
    return _es_admin(uid) or Storage.is_autorizado(uid)


def _nombre_usuario(user):
    if user.username:
        return html.escape(f"@{user.username}")
    return f'<a href="tg://user?id={user.id}">{html.escape(user.full_name)}</a> ({user.id})'


async def _avisar_admin(context: ContextTypes.DEFAULT_TYPE, user, accion, texto):
    """Le avisa al admin qué texto mandó o generó un usuario."""
    if _es_admin(user.id):
        return
    if len(texto) > MAX_AVISO:
        texto = texto[:MAX_AVISO] + "…"
    try:
        await context.bot.send_message(
            ADMIN[0],
            f"El usuario {_nombre_usuario(user)} {accion} \"{html.escape(texto)}\"",
            parse_mode="HTML")
    except Exception:
        log.exception("TextoToAudio: no pude avisar al admin")


async def _intentar_codigo(update: Update, context: ContextTypes.DEFAULT_TYPE, codigo):
    user = update.effective_user
    if codigo.strip() == Storage.get_codigo():
        Storage.autorizar(user.id, user.full_name)
        context.user_data.pop("esperando_codigo", None)
        await update.message.reply_text(
            "✅ Código correcto. ¡Bot activado!\n"
            "Mandame un texto y te lo devuelvo como audio, "
            "o mandame un audio y te lo paso a texto.")
        log.info("TextoToAudio: usuario %s (%s) activado", user.id, user.full_name)
    else:
        context.user_data["esperando_codigo"] = True
        await update.message.reply_text("❌ Código incorrecto. Probá de nuevo.")


async def command_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if _esta_autorizado(uid):
        await update.message.reply_text(
            "¡Hola! Ya tenés el bot activado. Mandame un texto y te lo convierto en audio, "
            "o un audio y te lo paso a texto.")
        return
    # Permite "/start CODIGO" directamente
    if context.args:
        await _intentar_codigo(update, context, " ".join(context.args))
        return
    context.user_data["esperando_codigo"] = True
    await update.message.reply_text("🔒 Para activar el bot, enviame el código secreto.")


async def command_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "🗣️ *Texto a Audio / Audio a Texto*\n"
        "/start — activar el bot (pide el código secreto)\n"
        "/voz — elegir qué voz femenina y masculina usar\n"
        "/gender — cambiar la voz entre masculina y femenina\n"
        "/switch — cambiar el proveedor de voz (Edge / gTTS)\n"
        "/version — ver la versión del bot\n"
        f"• Mandá un texto y te llega como audio (máx. {MAX_CARACTERES} caracteres).\n"
        f"• Mandá una nota de voz, audio o videomensaje y te llega el texto (máx. {MAX_SEGUNDOS_AUDIO // 60} minutos)."
    )
    if _es_admin(update.effective_user.id):
        texto += (
            "\n\n*Admin*\n"
            "/codigo — ver el código actual\n"
            "/codigo NUEVO — cambiar el código secreto\n"
            "/usuarios — listar usuarios activados\n"
            "/revocar UID — quitar acceso a un usuario"
        )
    await update.message.reply_text(texto, parse_mode="Markdown")


async def command_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not _esta_autorizado(uid):
        await update.message.reply_text("🔒 Bot no activado. Usá /start y enviá el código secreto.")
        return
    if context.args:
        nuevo = ALIAS_GENERO.get(context.args[0].strip().lower())
        if not nuevo:
            await update.message.reply_text("Uso: /gender (alterna), /gender masculino o /gender femenino")
            return
    else:
        nuevo = "femenino" if Storage.get_gender(uid) == "masculino" else "masculino"
    Storage.set_gender(uid, nuevo)
    texto = f"🗣️ Voz cambiada a {nuevo} ({_nombre_voz(_voz_usuario(uid, nuevo))})."
    if _proveedor_usuario(uid) == "gtts":
        texto += "\nOjo: con gTTS la voz es siempre la misma. Usá /switch para volver a Edge."
    await update.message.reply_text(texto)


def _proveedor_usuario(uid):
    return Storage.get_pref(uid, "proveedor", PROVEEDOR_POR_DEFECTO)


def _voz_usuario(uid, gender):
    voz = Storage.get_pref(uid, f"voz_{gender}")
    return voz if _INFO_VOZ.get(voz, (None,))[0] == gender else VOCES[gender]


def _nombre_voz(voz):
    """'es-AR-ElenaNeural' -> 'Elena (🇦🇷 Argentina)'"""
    if voz not in _INFO_VOZ:
        return voz
    _, nombre, cod = _INFO_VOZ[voz]
    return f"{nombre} ({VOCES_DISPONIBLES[cod][0]})"


async def command_switch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not _esta_autorizado(uid):
        await update.message.reply_text("🔒 Bot no activado. Usá /start y enviá el código secreto.")
        return
    if context.args:
        nuevo = ALIAS_PROVEEDOR.get(context.args[0].strip().lower())
        if not nuevo:
            await update.message.reply_text("Uso: /switch (alterna), /switch edge o /switch gtts")
            return
    else:
        nuevo = "gtts" if _proveedor_usuario(uid) == "edge" else "edge"
    Storage.set_pref(uid, "proveedor", nuevo)
    await update.message.reply_text(f"🔀 Proveedor de voz: {PROVEEDORES[nuevo]}.")


def _teclado_paises(uid):
    elegidas = {_INFO_VOZ[_voz_usuario(uid, g)][2] for g in ("femenino", "masculino")}
    botones = [
        InlineKeyboardButton(f"{'✅ ' if cod in elegidas else ''}{pais}", callback_data=f"voz*pais*{cod}")
        for cod, (pais, _) in VOCES_DISPONIBLES.items()
    ]
    return InlineKeyboardMarkup([botones[i:i + 2] for i in range(0, len(botones), 2)])


def _texto_paises(uid):
    return (
        "🎙️ Elegí un país para ver y probar sus voces (✅ = el de tus voces actuales).\n"
        f"Femenina: {_nombre_voz(_voz_usuario(uid, 'femenino'))}\n"
        f"Masculina: {_nombre_voz(_voz_usuario(uid, 'masculino'))}\n"
        f"Ahora estás usando la voz {_ADJETIVO[Storage.get_gender(uid)]} (cambiala con /gender)."
    )


def _teclado_pais(uid, cod):
    actuales = {_voz_usuario(uid, "femenino"), _voz_usuario(uid, "masculino")}
    filas = []
    for voz, gender, nombre in VOCES_DISPONIBLES[cod][1]:
        simbolo = "♀" if gender == "femenino" else "♂"
        filas.append([
            InlineKeyboardButton(f"{'✅ ' if voz in actuales else ''}{simbolo} {nombre}", callback_data=f"voz*{gender}*{voz}"),
            InlineKeyboardButton("▶️ Probar", callback_data=f"voz*probar*{voz}"),
        ])
    filas.append([InlineKeyboardButton("⬅️ Volver a los países", callback_data="voz*volver")])
    return InlineKeyboardMarkup(filas)


def _texto_pais(uid, cod):
    return (
        f"{VOCES_DISPONIBLES[cod][0]}\n"
        "Tocá una voz para elegirla o ▶️ para escucharla.\n"
        f"Femenina actual: {_nombre_voz(_voz_usuario(uid, 'femenino'))}\n"
        f"Masculina actual: {_nombre_voz(_voz_usuario(uid, 'masculino'))}"
    )


async def command_voz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not _esta_autorizado(uid):
        await update.message.reply_text("🔒 Bot no activado. Usá /start y enviá el código secreto.")
        return
    await update.message.reply_text(_texto_paises(uid), reply_markup=_teclado_paises(uid))


async def _editar(query, texto, teclado):
    try:
        await query.edit_message_text(texto, reply_markup=teclado)
    except Exception:
        # Telegram rechaza la edición si no cambió nada (misma voz elegida de nuevo)
        pass


# file_id de Telegram de cada audio de prueba ya enviado, para no volver a generarlo
_audios_prueba = {}


async def _probar_voz(query, context, voz):
    nombre = _nombre_voz(voz)
    chat_id = query.message.chat.id
    if voz in _audios_prueba:
        await query.answer()
        await context.bot.send_voice(chat_id, _audios_prueba[voz], caption=f"▶️ {nombre}")
        return
    await query.answer(f"Generando la voz de {nombre}…")
    await context.bot.send_chat_action(chat_id, "record_voice")
    try:
        audio = await _generar_audio_edge(TEXTO_PRUEBA, voz)
    except Exception:
        log.exception("TextoToAudio: falló la prueba de la voz %s", voz)
        await context.bot.send_message(chat_id, f"⚠️ No pude generar la voz de {nombre}. Probá de nuevo en un rato.")
        return
    mensaje = await context.bot.send_voice(chat_id, audio, filename="prueba.mp3", caption=f"▶️ {nombre}")
    if mensaje.voice:
        _audios_prueba[voz] = mensaje.voice.file_id


async def callback_voz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    partes = query.data.split("*")
    if not _esta_autorizado(uid):
        await query.answer("🔒 Bot no activado.")
        return
    accion = partes[1] if len(partes) > 1 else ""
    valor = partes[2] if len(partes) > 2 else ""

    if accion == "volver":
        await query.answer()
        await _editar(query, _texto_paises(uid), _teclado_paises(uid))
    elif accion == "pais" and valor in VOCES_DISPONIBLES:
        await query.answer()
        await _editar(query, _texto_pais(uid, valor), _teclado_pais(uid, valor))
    elif accion == "probar" and valor in _INFO_VOZ:
        await _probar_voz(query, context, valor)
    elif accion in ("femenino", "masculino") and _INFO_VOZ.get(valor, (None,))[0] == accion:
        Storage.set_pref(uid, f"voz_{accion}", valor)
        await query.answer(f"Voz {_ADJETIVO[accion]}: {_nombre_voz(valor)}")
        cod = _INFO_VOZ[valor][2]
        await _editar(query, _texto_pais(uid, cod), _teclado_pais(uid, cod))
    else:
        await query.answer()


async def command_version(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = f"🤖 Versión {VERSION}"
    if VERSION in CHANGELOG:
        texto += f"\n{CHANGELOG[VERSION]}"
    await update.message.reply_text(texto)


async def al_iniciar(app):
    await configurar_comandos(app)
    await avisar_version(app)


async def configurar_comandos(app):
    """Registra los comandos para que aparezcan al escribir / en Telegram."""
    try:
        await app.bot.set_my_commands(COMANDOS)
        await app.bot.set_my_commands(COMANDOS_ADMIN, scope=BotCommandScopeChat(ADMIN[0]))
    except Exception:
        log.exception("TextoToAudio: no pude registrar los comandos")


async def avisar_version(app):
    """Al iniciar, si la versión cambió desde el último aviso, se lo informa al admin."""
    try:
        anterior = await asyncio.to_thread(Storage.get_ultima_version)
        if anterior == VERSION:
            return
        texto = f"🚀 Bot de TTS actualizado a la versión {VERSION}"
        if anterior:
            texto += f" (antes {anterior})"
        if VERSION in CHANGELOG:
            texto += f"\n\nCambios: {CHANGELOG[VERSION]}"
        await app.bot.send_message(ADMIN[0], texto)
        await asyncio.to_thread(Storage.set_ultima_version, VERSION)
        log.info("TextoToAudio: avisada la versión %s al admin", VERSION)
    except Exception:
        log.exception("TextoToAudio: no pude avisar la versión al admin")


async def command_codigo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _es_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text(f"Código actual: `{Storage.get_codigo()}`", parse_mode="Markdown")
        return
    nuevo = " ".join(context.args).strip()
    Storage.set_codigo(nuevo)
    await update.message.reply_text(f"✅ Nuevo código secreto: `{nuevo}`", parse_mode="Markdown")


async def command_usuarios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _es_admin(update.effective_user.id):
        return
    usuarios = Storage.listar_usuarios()
    if not usuarios:
        await update.message.reply_text("No hay usuarios activados.")
        return
    lineas = [f"• {name} — {uid}" for uid, name in usuarios]
    await update.message.reply_text("Usuarios activados:\n" + "\n".join(lineas))


async def command_revocar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _es_admin(update.effective_user.id):
        return
    if not context.args or not context.args[0].lstrip("-").isdigit():
        await update.message.reply_text("Uso: /revocar UID")
        return
    uid = int(context.args[0])
    if Storage.revocar(uid):
        await update.message.reply_text(f"🚫 Acceso revocado para {uid}.")
    else:
        await update.message.reply_text(f"El usuario {uid} no estaba activado.")


def _generar_audio_gtts(texto):
    buffer = io.BytesIO()
    gTTS(text=texto, lang=IDIOMA, tld=TLD).write_to_fp(buffer)
    buffer.seek(0)
    return buffer


async def _generar_audio_edge(texto, voz):
    buffer = io.BytesIO()
    async for chunk in edge_tts.Communicate(texto, voz).stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])
    if not buffer.tell():
        raise RuntimeError("edge-tts no devolvió audio")
    buffer.seek(0)
    return buffer


async def _generar_audio(texto, voz, proveedor):
    if proveedor == "gtts":
        return await asyncio.to_thread(_generar_audio_gtts, texto)
    try:
        return await _generar_audio_edge(texto, voz)
    except Exception:
        log.exception("TextoToAudio: falló edge-tts, uso gTTS")
    return await asyncio.to_thread(_generar_audio_gtts, texto)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    texto = update.message.text

    if not _esta_autorizado(uid):
        if context.user_data.get("esperando_codigo"):
            await _intentar_codigo(update, context, texto)
        else:
            await update.message.reply_text("🔒 Bot no activado. Usá /start y enviá el código secreto.")
        return

    if len(texto) > MAX_CARACTERES:
        await update.message.reply_text(
            f"El texto es muy largo ({len(texto)} caracteres). Máximo: {MAX_CARACTERES}.")
        return

    await _avisar_admin(context, update.effective_user, "puso el texto", texto)
    await context.bot.send_chat_action(update.effective_chat.id, "record_voice")
    try:
        voz = _voz_usuario(uid, Storage.get_gender(uid))
        audio = await _generar_audio(texto, voz, _proveedor_usuario(uid))
    except Exception:
        log.exception("TextoToAudio: error generando audio")
        await update.message.reply_text("⚠️ No pude generar el audio. Probá de nuevo en un rato.")
        return
    await update.message.reply_voice(voice=audio, filename="audio.mp3")


def _decodificar_pcm(data):
    """Decodifica cualquier audio/video a PCM 16-bit mono a SAMPLE_RATE."""
    pcm = bytearray()
    with av.open(io.BytesIO(data)) as container:
        resampler = av.AudioResampler(format="s16", layout="mono", rate=SAMPLE_RATE)
        for frame in container.decode(audio=0):
            for f in resampler.resample(frame):
                pcm += f.to_ndarray().tobytes()
        for f in resampler.resample(None):
            pcm += f.to_ndarray().tobytes()
    return bytes(pcm)


def _transcribir(data):
    pcm = _decodificar_pcm(data)
    recognizer = sr.Recognizer()
    # Google corta los audios largos, así que se transcribe por partes
    bytes_por_parte = SEGUNDOS_POR_PARTE * SAMPLE_RATE * 2
    partes = []
    for i in range(0, len(pcm), bytes_por_parte):
        audio = sr.AudioData(pcm[i:i + bytes_por_parte], SAMPLE_RATE, 2)
        try:
            partes.append(recognizer.recognize_google(audio, language=IDIOMA_STT))
        except sr.UnknownValueError:
            continue
    return " ".join(partes).strip()


async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not _esta_autorizado(uid):
        await update.message.reply_text("🔒 Bot no activado. Usá /start y enviá el código secreto.")
        return

    media = update.message.voice or update.message.audio or update.message.video_note
    if media.duration and media.duration > MAX_SEGUNDOS_AUDIO:
        await update.message.reply_text(
            f"El audio es muy largo ({media.duration}s). Máximo: {MAX_SEGUNDOS_AUDIO // 60} minutos.")
        return

    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    try:
        archivo = await media.get_file()
        data = bytes(await archivo.download_as_bytearray())
        texto = await asyncio.to_thread(_transcribir, data)
    except sr.RequestError:
        log.exception("TextoToAudio: error del servicio de reconocimiento")
        await update.message.reply_text("⚠️ El servicio de reconocimiento no respondió. Probá de nuevo en un rato.")
        return
    except Exception as e:
        log.exception("TextoToAudio: error transcribiendo audio")
        await update.message.reply_text(f"⚠️ No pude procesar el audio ({type(e).__name__}: {e}).")
        return

    if not texto:
        await update.message.reply_text("🤷 No entendí nada en el audio.")
        return
    await update.message.reply_text(f"📝 {texto}")
    await _avisar_admin(context, update.effective_user, "convirtió el audio a este texto", texto)
