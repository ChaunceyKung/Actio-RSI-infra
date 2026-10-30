param([string]$Config = (Join-Path (Split-Path $PSScriptRoot -Parent) 'actio.toml'))
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$settingsFile = (Resolve-Path -LiteralPath $Config).Path
$settingsBase = Split-Path $settingsFile -Parent
# Bootstrap has no Python yet. Read only the documented single-line TOML path
# strings; the installed Python loader validates the complete TOML at the end.
$pathSettings = @{}
$inPaths = $false
foreach ($line in Get-Content -LiteralPath $settingsFile) {
    $value = $line.Trim()
    if ($value -match '^\[([^\]]+)\]') { $inPaths = $Matches[1] -eq 'paths'; continue }
    if (!$inPaths -or !$value -or $value.StartsWith('#')) { continue }
    if ($value -notmatch '^([a-z_]+)\s*=\s*("(?:[^"\\]|\\.)*"|''[^'']*'')\s*(?:#.*)?$') {
        throw 'Bootstrap [paths] requires single-line quoted TOML strings; use forward slashes or literal single quotes.'
    }
    $name = $Matches[1]; $literal = $Matches[2]
    if ($pathSettings.ContainsKey($name)) { throw "Duplicate TOML path: $name" }
    $pathSettings[$name] = if ($literal.StartsWith('"')) { ConvertFrom-Json $literal } else { $literal.Substring(1, $literal.Length - 2) }
}
function Get-ConfiguredPath([string]$Name) {
    if (!$pathSettings.ContainsKey($Name) -or !$pathSettings[$Name]) { throw "Missing TOML path: $Name" }
    $configuredPath = $pathSettings[$Name]
    if (![IO.Path]::IsPathRooted($configuredPath)) { $configuredPath = Join-Path $settingsBase $configuredPath }
    return [IO.Path]::GetFullPath($configuredPath)
}
Set-Location $projectRoot
$env:UV_CACHE_DIR = Get-ConfiguredPath 'uv_cache'
$env:UV_PYTHON_INSTALL_DIR = Get-ConfiguredPath 'python_install'
$env:UV_PYTHON_INSTALL_BIN = '0'
$env:TEMP = Get-ConfiguredPath 'temp'
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Force $env:TEMP | Out-Null
function Invoke-Uv {
    & uv @args
    if ($LASTEXITCODE -ne 0) { throw "uv failed with exit $LASTEXITCODE" }
}
Invoke-Uv python install 3.12.13
$environmentRoot = Get-ConfiguredPath 'venv'
if (!(Test-Path (Join-Path $environmentRoot 'pyvenv.cfg'))) {
    Invoke-Uv venv --python 3.12.13 $environmentRoot
}
$python = Join-Path $environmentRoot 'Scripts/python.exe'
Invoke-Uv pip install --python $python --require-hashes -r requirements.lock
Invoke-Uv pip install --python $python --require-hashes -r requirements-eval.lock -r requirements-eval-test.lock
Invoke-Uv pip install --python $python --no-build-isolation --reinstall-package actio-rsi '.[environments]' gin-config==0.5.0
Invoke-Uv run --no-project --python $python python scripts/bootstrap_concordia.py
Invoke-Uv pip check --python $python
Invoke-Uv run --no-project --python $python python -m actio config show --settings $settingsFile
