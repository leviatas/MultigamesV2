# MultigamesV2

Proyecto de Juegos de mesa bot Telegram.

## Configuración Requerida

### Archivos de Ambiente

Para ejecutar este proyecto, necesitas crear dos archivos de configuración en la raíz del proyecto:

#### 1. `.env`

Contiene las credenciales y tokens de los bots.

**Crear desde el ejemplo:**

```bash
cp .envEjemplo .env
```

Variables necesarias:

- `TOKEN_MULTIGAMES`: Token del bot principal de Telegram
- `TOKEN_SPACE_HELPER`: Token del bot Space Helper
- `TOKEN_REPORT`: Token del bot de reportes
- `TOKEN_BLOOD`: Token del bot Blood Clocktower
- `TOKEN_SECRETHITLER`: Token del bot Secret Hitler
- `discord`: Token del bot Discord
- `github_token`: Personal Access Token de GitHub
- `github_token_workflow`: PAT de GitHub para workflows
- `DATABASE_URL`: Conexión a PostgreSQL (para Docker usa `pg-multigames` como hostname)

#### 2. `.envDB`

Contiene la contraseña de la base de datos PostgreSQL.

**Crear desde el ejemplo:**

```bash
cp .envDBEjemplo .envDB
```

Variables necesarias:

- `POSTGRES_PASSWORD`: Contraseña segura para PostgreSQL

> ⚠️ **Importante**: Estos archivos contienen credenciales secretas. **Nunca los commits a Git**. Ya están en `.gitignore`.

## Ejecutar con Docker

### Requisitos

- Docker
- Docker Compose

### Instrucciones

1. **Configurar los archivos de ambiente:**

   ```bash
   cp .envEjemplo .env
   cp .envDBEjemplo .envDB
   # Editar los archivos y agregar tus credenciales reales
   ```

2. **Construir y ejecutar los contenedores:**

   ```bash
   docker compose up --build -d
   ```

3. **Verificar el estado:**

   ```bash
   docker compose ps
   ```

4. **Ver logs:**

   ```bash
   docker compose logs -f multigames-bot
   ```

5. **Detener los servicios:**
   ```bash
   docker compose down
   ```

### Estructura Docker

- **PostgreSQL**: Base de datos que se inicia primero
- **multigames-bot**: Bot principal que espera a que PostgreSQL esté listo
- **Red compartida**: Ambos servicios están en la red `multigames-net` para comunicarse

El bot espera a que PostgreSQL esté completamente operativo antes de iniciar (healthcheck).

## Validación de Secretos

Para evitar que se suban secretos (tokens, contraseñas, credenciales) accidentalmente al repositorio, hemos configurado un pre-commit hook automático.

### ¿Cómo funciona?

Antes de cada commit, se ejecuta automáticamente un script que:

- Busca patrones de tokens de Telegram, Discord, GitHub, AWS, etc.
- Detecta contraseñas en URLs de base de datos
- Identifica claves privadas
- Bloquea el commit si encuentra secretos

### Configuración Automática (Windows + Git Bash + Linux/Mac)

El hook se configura automáticamente cuando haces clone del repositorio. Git detectará:

- `pre-commit.bat` en Windows
- `pre-commit` (shell script) en Linux/Mac/Git Bash

El hook buscará Python en el siguiente orden:

1. `.venv\Scripts\python.exe` (venv del proyecto)
2. `py` (Windows Python launcher)
3. `python3` o `python` (PATH del sistema)

### Ejecutar validador manualmente

Si necesitas validar manualmente antes de un commit:

```bash
python scripts/validate-secrets.py
```

O con PowerShell en Windows:

```powershell
python scripts/validate-secrets.py
# O si tienes activado el venv
& .\.venv\Scripts\Activate.ps1
python scripts/validate-secrets.py
```

### ¿Qué hacer si el validador detecta un secreto?

1. **No intentes hacer commit del secreto**
2. **Elimina el secreto del archivo** (o muévelo a `.env` o `.envDB`)
3. **Si ya subiste un secreto a Git**, considera regenerarlo en el servicio correspondiente (Telegram, Discord, GitHub, etc.)

### Skip validation (último recurso)

Si absolutamente necesitas saltarte la validación:

```bash
git commit --no-verify
```

⚠️ **Usa esto solo como último recurso y asegúrate de que realmente no hay secretos en tu commit.**
