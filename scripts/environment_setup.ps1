$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:UV_CACHE_DIR = "$PWD/.local/uv-cache"
$env:UV_PYTHON_INSTALL_DIR = "$PWD/.local/python"
$env:UV_PYTHON_INSTALL_BIN = '0'
$env:TEMP = "$PWD/.local/tmp"
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Force $env:TEMP | Out-Null
function Invoke-Uv {
    & uv @args
    if ($LASTEXITCODE -ne 0) { throw "uv failed with exit $LASTEXITCODE" }
}
Invoke-Uv python install 3.12.13
if (!(Test-Path .local/phase1-env/pyvenv.cfg)) {
    Invoke-Uv venv --python 3.12.13 .local/phase1-env
}
$python = '.local/phase1-env/Scripts/python.exe'
Invoke-Uv pip install --python $python --require-hashes -r requirements.lock
Invoke-Uv pip install --python $python --require-hashes -r requirements-eval.lock -r requirements-eval-test.lock
Invoke-Uv pip install --python $python --no-build-isolation --reinstall-package actio-rsi '.[environments]' gin-config==0.5.0
Invoke-Uv run --no-project --python $python python scripts/bootstrap_concordia.py
Invoke-Uv pip check --python $python
