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
# Voces en español que se pueden elegir con /voz: (país, femenina, masculina)
VOCES_DISPONIBLES = [
    ("🇦🇷 Argentina", "es-AR-ElenaNeural", "es-AR-TomasNeural"),
    ("🇺🇾 Uruguay", "es-UY-ValentinaNeural", "es-UY-MateoNeural"),
    ("🇨🇱 Chile", "es-CL-CatalinaNeural", "es-CL-LorenzoNeural"),
    ("🇲🇽 México", "es-MX-DaliaNeural", "es-MX-JorgeNeural"),
    ("🇪🇸 España", "es-ES-ElviraNeural", "es-ES-AlvaroNeural"),
    ("🇨🇴 Colombia", "es-CO-SalomeNeural", "es-CO-GonzaloNeural"),
    ("🇺🇸 EE.UU.", "es-US-PalomaNeural", "es-US-AlonsoNeural"),
]
_VOCES_VALIDAS = {
    "femenino": {f for _, f, _ in VOCES_DISPONIBLES},
    "masculino": {m for _, _, m in VOCES_DISPONIBLES},
}
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
    return voz if voz in _VOCES_VALIDAS[gender] else VOCES[gender]


def _nombre_voz(voz):
    """'es-AR-ElenaNeural' -> 'Elena'"""
    return voz.split("-")[-1].replace("Neural", "")


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


def _teclado_voces(uid):
    fem = _voz_usuario(uid, "femenino")
    masc = _voz_usuario(uid, "masculino")
    filas = []
    for pais, f, m in VOCES_DISPONIBLES:
        filas.append([InlineKeyboardButton(pais, callback_data="voz*nada")])
        filas.append([
            InlineKeyboardButton(f"{'✅ ' if f == fem else ''}♀ {_nombre_voz(f)}", callback_data=f"voz*femenino*{f}"),
            InlineKeyboardButton(f"{'✅ ' if m == masc else ''}♂ {_nombre_voz(m)}", callback_data=f"voz*masculino*{m}"),
        ])
    return InlineKeyboardMarkup(filas)


def _texto_voces(uid):
    return (
        "🎙️ Elegí qué voz usar para cada género (✅ = la actual).\n"
        f"Femenina: {_nombre_voz(_voz_usuario(uid, 'femenino'))} · "
        f"Masculina: {_nombre_voz(_voz_usuario(uid, 'masculino'))}\n"
        f"Ahora estás usando la voz {_ADJETIVO[Storage.get_gender(uid)]} (cambiala con /gender)."
    )


async def command_voz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not _esta_autorizado(uid):
        await update.message.reply_text("🔒 Bot no activado. Usá /start y enviá el código secreto.")
        return
    await update.message.reply_text(_texto_voces(uid), reply_markup=_teclado_voces(uid))


async def callback_voz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    partes = query.data.split("*")
    if not _esta_autorizado(uid):
        await query.answer("🔒 Bot no activado.")
        return
    if len(partes) != 3 or partes[2] not in _VOCES_VALIDAS.get(partes[1], ()):
        await query.answer()
        return
    _, gender, voz = partes
    Storage.set_pref(uid, f"voz_{gender}", voz)
    await query.answer(f"Voz {_ADJETIVO[gender]}: {_nombre_voz(voz)}")
    try:
        await query.edit_message_text(_texto_voces(uid), reply_markup=_teclado_voces(uid))
    except Exception:
        # Telegram rechaza la edición si no cambió nada (misma voz elegida de nuevo)
        pass


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


async def _generar_audio(texto, voz, proveedor):
    if proveedor == "gtts":
        return await asyncio.to_thread(_generar_audio_gtts, texto)
    try:
        buffer = io.BytesIO()
        async for chunk in edge_tts.Communicate(texto, voz).stream():
            if chunk["type"] == "audio":
                buffer.write(chunk["data"])
        if buffer.tell():
            buffer.seek(0)
            return buffer
        log.warning("TextoToAudio: edge-tts no devolvió audio, uso gTTS")
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
