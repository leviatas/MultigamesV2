# Helpers compartidos para juegos con animaciones en vivo (carreras, tiradas de dado).
#
# El bot procesa los updates de Telegram de a uno (sin concurrent_updates), así que
# cualquier animación larga (editar un mensaje carta por carta, esperar la animación
# de un dado) tiene que correr como tarea en segundo plano. Si no, el bot entero
# queda congelado para todos los demás grupos mientras dura la animación.

import asyncio
import logging as log

from telegram.error import RetryAfter, BadRequest, TimedOut, NetworkError

logger = log.getLogger(__name__)

# clave -> asyncio.Task. Guardar la referencia evita que el recolector de basura
# cancele la tarea antes de terminar.
_tareas = {}


def lanzar(clave, coro):
    """Ejecuta `coro` en segundo plano, registrada bajo `clave` (ej: "CB-<cid>")."""
    tarea = asyncio.get_running_loop().create_task(coro)
    _tareas[clave] = tarea

    def _limpiar(t):
        if _tareas.get(clave) is t:
            _tareas.pop(clave, None)
        if not t.cancelled() and t.exception() is not None:
            logger.error("Tarea %s terminó con error: %s", clave, t.exception())

    tarea.add_done_callback(_limpiar)
    return tarea


def en_curso(clave):
    tarea = _tareas.get(clave)
    return tarea is not None and not tarea.done()


def _segundos(retry_after):
    if hasattr(retry_after, "total_seconds"):
        return retry_after.total_seconds()
    try:
        return float(retry_after)
    except (TypeError, ValueError):
        return 3.0


async def editar(bot, chat_id, message_id, texto, reply_markup=None, parse_mode="Markdown", reintentos=3):
    """Edita un mensaje tolerando el rate limit de Telegram.

    Devuelve True si el mensaje quedó con el texto pedido (o ya lo tenía).
    """
    for _ in range(reintentos):
        try:
            await bot.edit_message_text(
                texto, chat_id=chat_id, message_id=message_id,
                parse_mode=parse_mode, reply_markup=reply_markup
            )
            return True
        except RetryAfter as e:
            await asyncio.sleep(_segundos(e.retry_after) + 0.5)
        except BadRequest as e:
            if "not modified" in str(e).lower():
                return True
            logger.warning("editar(): BadRequest %s", e)
            return False
        except (TimedOut, NetworkError) as e:
            logger.warning("editar(): red %s", e)
            await asyncio.sleep(1.5)
    return False


async def enviar(bot, chat_id, texto, reply_markup=None, parse_mode="Markdown", reintentos=3):
    """send_message tolerante al rate limit. Devuelve el Message o None."""
    for _ in range(reintentos):
        try:
            return await bot.send_message(chat_id, texto, parse_mode=parse_mode, reply_markup=reply_markup)
        except RetryAfter as e:
            await asyncio.sleep(_segundos(e.retry_after) + 0.5)
        except (TimedOut, NetworkError) as e:
            logger.warning("enviar(): red %s", e)
            await asyncio.sleep(1.5)
    return None


async def enviar_foto(bot, chat_id, foto_bytes, caption=None, reply_markup=None, parse_mode="Markdown", reintentos=3):
    """send_photo tolerante al rate limit. `foto_bytes` son los bytes del PNG (se arma
    un BytesIO nuevo en cada intento, porque Telegram lo consume). Devuelve el Message o None."""
    from io import BytesIO
    for _ in range(reintentos):
        try:
            return await bot.send_photo(chat_id, photo=BytesIO(foto_bytes), caption=caption,
                                        parse_mode=parse_mode, reply_markup=reply_markup)
        except RetryAfter as e:
            await asyncio.sleep(_segundos(e.retry_after) + 0.5)
        except (TimedOut, NetworkError) as e:
            logger.warning("enviar_foto(): red %s", e)
            await asyncio.sleep(1.5)
    return None


async def tirar_dado(bot, chat_id, espera=3.6):
    """Tira el dado animado de Telegram y espera a que termine la animación.

    Devuelve el valor (1-6). Si Telegram falla, cae a un dado local.
    """
    import random
    for _ in range(3):
        try:
            msg = await bot.send_dice(chat_id, emoji="🎲")
            await asyncio.sleep(espera)
            return msg.dice.value
        except RetryAfter as e:
            await asyncio.sleep(_segundos(e.retry_after) + 0.5)
        except (TimedOut, NetworkError):
            await asyncio.sleep(1.5)
    return random.randint(1, 6)
