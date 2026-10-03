import logging as log
import os

from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

import TextoToAudio.Commands as Commands
import TextoToAudio.Storage as Storage
from TextoToAudio.version import VERSION


def main(stop_event):
    token = os.environ.get('TOKEN_TTS', None)
    if not token:
        log.warning("TextoToAudio: TOKEN_TTS no definido, el bot no se inicia")
        return

    log.info("Starting TextoToAudio bot v%s", VERSION)
    Storage.init()

    app = Application.builder().token(token).post_init(Commands.al_iniciar).build()

    app.add_handler(CommandHandler("start", Commands.command_start))
    app.add_handler(CommandHandler("help", Commands.command_help))
    app.add_handler(CommandHandler("gender", Commands.command_gender))
    app.add_handler(CommandHandler("version", Commands.command_version))
    app.add_handler(CommandHandler("voz", Commands.command_voz))
    app.add_handler(CommandHandler("switch", Commands.command_switch))
    app.add_handler(CallbackQueryHandler(Commands.callback_voz, pattern=r"^voz\*"))

    # Comandos admin
    app.add_handler(CommandHandler("codigo", Commands.command_codigo))
    app.add_handler(CommandHandler("usuarios", Commands.command_usuarios))
    app.add_handler(CommandHandler("revocar", Commands.command_revocar))

    # Solo chats privados: cualquier texto se convierte en audio
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, Commands.handle_text))
    # Notas de voz, audios y videomensajes se transcriben a texto
    app.add_handler(MessageHandler((filters.VOICE | filters.AUDIO | filters.VIDEO_NOTE) & filters.ChatType.PRIVATE, Commands.handle_audio))

    while not stop_event.is_set():
        app.run_polling(timeout=5, stop_signals=None)


if __name__ == '__main__':
    import threading
    log.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=log.INFO)
    main(threading.Event())
