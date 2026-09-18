# -*- coding: utf-8 -*-
"""Capa de internacionalizacion del bot de Secret Hitler.

El idioma es una propiedad del *chat*: se elige con /language y se guarda en la
tabla language_secret_hitler, asi que sobrevive a los reinicios y a las partidas
nuevas. Todos los mensajes de una partida - incluidos los privados a cada
jugador - salen en el idioma del grupo, que se resuelve a partir de game.cid.

Uso:
    from SecretHitler.i18n import t
    t("vote.ask", game, presidente=..., canciller=...)

El segundo parametro es el "contexto de idioma" y puede ser un Game (usa su
cid), un cid, un codigo de idioma ("es"/"en") o None (idioma por defecto).
Nunca lanza: si falta una clave o falla el formateo devuelve el texto en
espanol, y si tampoco esta, la propia clave.
"""
import logging as log
import os
import urllib.parse

import psycopg2

from SecretHitler.Locales import es as _es
from SecretHitler.Locales import en as _en

IDIOMA_DEFAULT = "es"
# Codigo -> nombre del idioma en si mismo (para los botones de /language).
IDIOMAS = {
    "es": u"Español \U0001F1E6\U0001F1F7",
    "en": u"English \U0001F1EC\U0001F1E7",
}
CATALOGOS = {"es": _es.TEXTS, "en": _en.TEXTS}

# Aliases que se aceptan como argumento de /language.
ALIASES = {
    "es": "es", "esp": "es", "español": "es", "espanol": "es", "castellano": "es", "spanish": "es",
    "en": "en", "eng": "en", "ingles": "en", u"inglés": "en", "english": "en",
}

urllib.parse.uses_netloc.append("postgres")
_url = urllib.parse.urlparse(os.environ["DATABASE_URL"])

# cid -> idioma. Se precarga entero en init() para no consultar la base en cada mensaje.
_lang_by_cid = {}


def _connect():
    return psycopg2.connect(
        database=_url.path[1:],
        user=_url.username,
        password=_url.password,
        host=_url.hostname,
        port=_url.port,
    )


def init():
    """Precarga la tabla de idiomas. La llama MainController.main() al arrancar."""
    try:
        conn = _connect()
        cur = conn.cursor()
        cur.execute("SELECT cid, lang FROM language_secret_hitler;")
        for cid, lang in cur.fetchall():
            if lang in CATALOGOS:
                _lang_by_cid[int(cid)] = lang
        conn.close()
        log.info("i18n: %d chats con idioma configurado" % len(_lang_by_cid))
    except Exception as e:
        # Un fallo aca solo significa que todos juegan en el idioma por defecto.
        log.error("i18n.init failed: %s" % str(e))


def normalizar(valor):
    """Devuelve el codigo de idioma para lo que haya escrito el usuario, o None."""
    if not valor:
        return None
    return ALIASES.get(str(valor).strip().lower())


def _cid_de(ctx):
    if ctx is None:
        return None
    if isinstance(ctx, str):
        return None
    if isinstance(ctx, int):
        return ctx
    return getattr(ctx, "cid", None)


def get_lang(ctx=None):
    """Idioma para un Game, un cid, un codigo de idioma o None."""
    if isinstance(ctx, str):
        return ctx if ctx in CATALOGOS else IDIOMA_DEFAULT
    cid = _cid_de(ctx)
    if cid is None:
        return IDIOMA_DEFAULT
    cid = int(cid)
    if cid in _lang_by_cid:
        return _lang_by_cid[cid]
    try:
        conn = _connect()
        cur = conn.cursor()
        cur.execute("SELECT lang FROM language_secret_hitler WHERE cid = %s;", [cid])
        row = cur.fetchone()
        conn.close()
        lang = row[0] if row and row[0] in CATALOGOS else IDIOMA_DEFAULT
    except Exception as e:
        log.error("i18n.get_lang failed for %s: %s" % (cid, str(e)))
        lang = IDIOMA_DEFAULT
    # Cacheo tambien el default: si el chat no tiene fila, no tiene sentido volver a preguntar.
    _lang_by_cid[cid] = lang
    return lang


def set_lang(cid, lang):
    """Guarda el idioma de un chat. Devuelve True si se pudo persistir."""
    if lang not in CATALOGOS:
        return False
    cid = int(cid)
    _lang_by_cid[cid] = lang
    try:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO language_secret_hitler(cid, lang) VALUES (%s, %s) "
            "ON CONFLICT (cid) DO UPDATE SET lang = EXCLUDED.lang, updated_at = now();",
            (cid, lang),
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log.error("i18n.set_lang failed for %s: %s" % (cid, str(e)))
        return False


def t(key, ctx=None, **kwargs):
    """Texto de `key` en el idioma de `ctx`, formateado con kwargs."""
    lang = get_lang(ctx)
    plantilla = CATALOGOS.get(lang, {}).get(key)
    if plantilla is None:
        if lang != IDIOMA_DEFAULT:
            log.error("i18n: falta la clave '%s' en '%s'" % (key, lang))
        plantilla = CATALOGOS[IDIOMA_DEFAULT].get(key)
    if plantilla is None:
        log.error("i18n: clave desconocida '%s'" % key)
        return key
    if not kwargs:
        return plantilla
    try:
        return plantilla.format(**kwargs)
    except Exception as e:
        log.error("i18n: no se pudo formatear '%s' (%s): %s" % (key, lang, str(e)))
        return plantilla


# --- Nombres de juego ---------------------------------------------------------
# role/party/policy se guardan SIEMPRE con su nombre interno en espanol ("Liberal",
# "fascista", ...): son identificadores que viven en el estado de la partida y en la
# base. Estos helpers son solo para mostrarlos.

def role_name(role, ctx=None):
    if role is None:
        return ""
    return t("role.%s" % role.lower(), ctx)


def party_name(party, ctx=None):
    if party is None:
        return ""
    return t("party.%s" % party.lower(), ctx)


def policy_name(policy, ctx=None):
    if policy is None:
        return ""
    return t("policy.%s" % policy.lower(), ctx)

def preference_label(preferencia, ctx=None):
    """Traduce una preferencia de /role ("Liberal_Fascista") para mostrarla."""
    if not preferencia:
        return ""
    partes = [role_name(parte, ctx) for parte in preferencia.split("_") if parte]
    return (" %s " % t("common.or", ctx)).join(partes)
