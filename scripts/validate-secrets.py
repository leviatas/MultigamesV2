#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para detectar secretos en archivos antes de hacer commit.
Busca patrones comunes de tokens, contraseñas y credenciales.
"""

import re
import sys
import io
from pathlib import Path

# Configurar stdout para UTF-8 en Windows (evitar UnicodeEncodeError)
if sys.stdout.encoding and sys.stdout.encoding.lower() in ('cp1252', 'ascii', 'utf-8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding and sys.stderr.encoding.lower() in ('cp1252', 'ascii', 'utf-8'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Patrones para detectar secretos
SECRET_PATTERNS = {
    # Tokens de Telegram
    'telegram_token': r'\d{9,10}:AA[A-Za-z0-9_-]{25,}',
    
    # Tokens de Discord
    'discord_token': r'[MN][A-Za-z\d_-]{23,25}\.[A-Za-z\d_-]{6,7}\.[A-Za-z\d_-]{26,38}',
    
    # GitHub Personal Access Tokens
    'github_pat': r'gh[pousr]{1,3}_[A-Za-z0-9_]{36,255}',
    
    # AWS Keys
    'aws_access_key': r'AKIA[0-9A-Z]{16}',
    
    # Contraseñas en DATABASE_URL
    'db_password': r'postgresql://[^:]+:([^@]*?)@',
    'db_password_mysql': r'mysql://[^:]+:([^@]*?)@',
    
    # Variables sospechosas
    'api_key_assignment': r'(api[_-]?key|secret[_-]?key|password|token)["\s:=]+[A-Za-z0-9\-_.+/=]{20,}',
    
    # Credenciales en URLs
    'url_credentials': r'(https?|ftp)://[^:]+:[^@]+@',
    
    # Private Keys
    'private_key': r'-----BEGIN (RSA|OPENSSH|EC|PGP|PRIVATE) KEY-----',
}

EXCLUDED_FILES = {
    '.envEjemplo',
    '.envDBEjemplo',
    '.gitignore',
    'README.md',
    'LICENSE',
    'pyproject.toml',
    'requirements.txt',
    'docker-compose.yml',
    'Dockerfile2',
    '.dockerignore',
    'validate-secrets.py',  # Excluir el validador de su propia validación (contiene patrones regex)
}

EXCLUDED_DIRS = {
    '.git',
    '.venv',
    'venv',
    '__pycache__',
    '.pytest_cache',
    'node_modules',
    '.idea',
    '.vscode',
}


def is_binary_file(filepath):
    """Verifica si un archivo es binario."""
    try:
        with open(filepath, 'rb') as f:
            return b'\x00' in f.read(8192)
    except:
        return True


def should_check_file(filepath):
    """Determina si el archivo debe ser validado."""
    # Ignorar archivos binarios
    if is_binary_file(filepath):
        return False
    
    # Ignorar directorios excluidos
    for excluded_dir in EXCLUDED_DIRS:
        if excluded_dir in filepath.parts:
            return False
    
    # Ignorar archivos de ejemplo
    if filepath.name in EXCLUDED_FILES:
        return False
    
    # Ignorar archivos de ejemplo con terminación
    if filepath.name.startswith('.env') and filepath.name.endswith('Ejemplo'):
        return False
    
    # Ignorar archivos que no sean de texto
    text_extensions = {
        '.py', '.js', '.ts', '.json', '.yaml', '.yml', '.toml', '.txt', '.md',
        '.sh', '.bash', '.sql', '.html', '.css', '.env', '.conf', '.config',
        '.xml', '.jar', '.properties', '.gradle', '.maven', '.lock'
    }
    
    return filepath.suffix in text_extensions or filepath.suffix == ''


def find_secrets(filepath):
    """Busca secretos en un archivo."""
    secrets_found = []
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                # Ignorar líneas de comentarios en archivos de ejemplo
                if line.strip().startswith('#'):
                    continue
                
                for pattern_name, pattern in SECRET_PATTERNS.items():
                    if re.search(pattern, line, re.IGNORECASE):
                        # Mostrar solo parte del secreto (primeros 10 chars)
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            secret_preview = match.group(0)[:10] + '***'
                            secrets_found.append({
                                'line': line_num,
                                'pattern': pattern_name,
                                'preview': secret_preview
                            })
    except Exception as e:
        print(f"Error al leer {filepath}: {e}", file=sys.stderr)
    
    return secrets_found


def validate_staged_files():
    """Valida archivos en el staging area de git."""
    import subprocess
    
    # Obtener lista de archivos staged
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        staged_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
    except Exception as e:
        print(f"Error al obtener archivos staged: {e}", file=sys.stderr)
        return True
    
    secrets_found = False
    
    for filename in staged_files:
        if not filename:
            continue
        
        filepath = Path(filename)
        
        if not should_check_file(filepath):
            continue
        
        if not filepath.exists():
            continue
        
        found = find_secrets(filepath)
        
        if found:
            secrets_found = True
            print(f"\n[!] ALERTA: Se encontraron patrones de secretos en: {filepath}")
            for secret in found:
                print(f"   Línea {secret['line']}: {secret['pattern']} ({secret['preview']})")
    
    return not secrets_found


def main():
    """Función principal."""
    if validate_staged_files():
        print("[OK] No se encontraron secretos en los archivos staged.")
        return 0
    else:
        print("\n[BLOQUEADO] COMMIT BLOQUEADO: Se detectaron posibles secretos.")
        print("   Por favor, revisa los archivos anteriores y remueve los secretos.")
        print("   Si tienes que incluir secretos, usa .env y .envDB (están en .gitignore)")
        return 1


if __name__ == '__main__':
    sys.exit(main())
