# Pre-commit hook para detectar secretos (PowerShell version para Windows)
# Este hook se ejecuta antes de cada commit para validar que no hay secretos

# Obtener la raíz del repositorio git
$repoRoot = (git rev-parse --show-toplevel) -replace '\\', '/'
$validateScript = "$repoRoot/scripts/validate-secrets.py"

if (-not (Test-Path $validateScript)) {
    Write-Error "❌ Error: No se encontró el script de validación en $validateScript"
    exit 1
}

python $validateScript
exit $LASTEXITCODE
