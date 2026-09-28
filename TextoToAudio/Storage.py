"""Persistencia del bot TextoToAudio: código secreto y usuarios autorizados.

Usa PostgreSQL (DATABASE_URL) si está disponible; si no, un archivo JSON local.
"""
import json
import logging as log
import os
import threading
import urllib.parse

import psycopg

CODIGO_POR_DEFECTO = "SnowQuiereUnBot"
JSON_PATH = os.path.join(os.path.dirname(__file__), "tts_data.json")

_lock = threading.Lock()


def _usa_db():
    return bool(os.environ.get("DATABASE_URL"))


def _connect():
    url = urllib.parse.urlparse(os.environ["DATABASE_URL"])
    return psycopg.connect(
        dbname=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )


def init():
    if not _usa_db():
        log.warning("TextoToAudio: DATABASE_URL no definido, usando %s", JSON_PATH)
        return
    with _connect() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS tts_config (key TEXT PRIMARY KEY, value TEXT NOT NULL);")
        conn.execute("CREATE TABLE IF NOT EXISTS tts_users (uid BIGINT PRIMARY KEY, name TEXT);")


# --- JSON fallback ---

def _leer_json():
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"codigo": CODIGO_POR_DEFECTO, "usuarios": {}}


def _escribir_json(data):
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# --- API ---

def get_codigo():
    if _usa_db():
        with _connect() as conn:
            row = conn.execute("SELECT value FROM tts_config WHERE key = 'codigo';").fetchone()
        return row[0] if row else CODIGO_POR_DEFECTO
    with _lock:
        return _leer_json().get("codigo", CODIGO_POR_DEFECTO)


def set_codigo(codigo):
    if _usa_db():
        with _connect() as conn:
            conn.execute(
                "INSERT INTO tts_config (key, value) VALUES ('codigo', %s) "
                "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;", [codigo])
        return
    with _lock:
        data = _leer_json()
        data["codigo"] = codigo
        _escribir_json(data)


def is_autorizado(uid):
    if _usa_db():
        with _connect() as conn:
            row = conn.execute("SELECT 1 FROM tts_users WHERE uid = %s;", [uid]).fetchone()
        return row is not None
    with _lock:
        return str(uid) in _leer_json().get("usuarios", {})


def autorizar(uid, name):
    if _usa_db():
        with _connect() as conn:
            conn.execute(
                "INSERT INTO tts_users (uid, name) VALUES (%s, %s) "
                "ON CONFLICT (uid) DO UPDATE SET name = EXCLUDED.name;", [uid, name])
        return
    with _lock:
        data = _leer_json()
        data.setdefault("usuarios", {})[str(uid)] = name
        _escribir_json(data)


def revocar(uid):
    """Devuelve True si el usuario existía."""
    if _usa_db():
        with _connect() as conn:
            cur = conn.execute("DELETE FROM tts_users WHERE uid = %s;", [uid])
            return cur.rowcount > 0
    with _lock:
        data = _leer_json()
        existia = data.get("usuarios", {}).pop(str(uid), None) is not None
        _escribir_json(data)
        return existia


def listar_usuarios():
    """Lista de tuplas (uid, name)."""
    if _usa_db():
        with _connect() as conn:
            return conn.execute("SELECT uid, name FROM tts_users ORDER BY name;").fetchall()
    with _lock:
        return [(int(uid), name) for uid, name in _leer_json().get("usuarios", {}).items()]
