# Install Guyline from a local checkout or wheel. No remote product fallback.
param(
    [string]$Source,
    [string]$Wheel,
    [switch]$Dev,
    [switch]$GlobalVenv,
    [switch]$WithChannels
)
$ErrorActionPreference = "Stop"
function Assert-Exit([string]$Action) {
    if ($LASTEXITCODE -ne 0) { throw "$Action failed (exit $LASTEXITCODE)" }
}
if ($Source -and $Wheel) { throw "Choose either -Source or -Wheel" }
if ($Wheel) {
    if (-not (Test-Path -LiteralPath $Wheel -PathType Leaf) -or
        [IO.Path]::GetExtension($Wheel) -ne ".whl") { throw "Local wheel not found: $Wheel" }
    $Target = (Resolve-Path -LiteralPath $Wheel).Path
} else {
    if (-not $Source) { $Source = Join-Path $PSScriptRoot ".." }
    if (-not (Test-Path -LiteralPath (Join-Path $Source "pyproject.toml"))) {
        throw "No local checkout. Supply -Source PATH or -Wheel PATH."
    }
    $Source = (Resolve-Path -LiteralPath $Source).Path
    $Target = $Source
}
$PythonCmd = (Get-Command python -ErrorAction Stop).Source
& $PythonCmd -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10+ is required"'
Assert-Exit "Python version check"
$VenvDir = Join-Path $env:USERPROFILE ".guyline-venv"
if ($Dev -and -not $GlobalVenv -and -not $Wheel) { $VenvDir = Join-Path $Source ".guyline-venv" }
if (-not (Test-Path -LiteralPath $VenvDir)) {
    & $PythonCmd -m venv $VenvDir
    Assert-Exit "Virtual environment creation"
}
$VenvPython = Join-Path $VenvDir "Scripts/python.exe"
if (-not (Test-Path -LiteralPath $VenvPython)) { throw "Incomplete venv: $VenvDir" }
if ($Wheel) { & $VenvPython -m pip install $Target }
else { & $VenvPython -m pip install -e $Target }
Assert-Exit "Local package installation"

& $VenvPython -m guyline --version
Assert-Exit "Module verification"
& $VenvPython -m guyline agent --help
Assert-Exit "Agent verification"
& $VenvPython -m guyline gateway --help
Assert-Exit "Gateway verification"
$FrontendDir = & $VenvPython -c 'from guyline.ui.react_launcher import get_frontend_dir; print(get_frontend_dir())'
Assert-Exit "Frontend discovery"
$FrontendDir = "$FrontendDir".Trim()
if (-not (Test-Path -LiteralPath (Join-Path $FrontendDir "package.json"))) {
    throw "Installed frontend missing: $FrontendDir"
}
if ((Get-Command node -ErrorAction SilentlyContinue) -and (Get-Command npm -ErrorAction SilentlyContinue)) {
    Push-Location -LiteralPath $FrontendDir
    try {
        if (Test-Path -LiteralPath "package-lock.json") { & npm ci --no-fund --no-audit }
        else { & npm install --no-fund --no-audit }
        Assert-Exit "Frontend dependencies"
    } finally { Pop-Location }
} else { Write-Host "Install Node.js 18+ and npm before launching the React terminal." }
$ConfigDir = & $VenvPython -c 'from guyline.config.paths import get_config_dir; print(get_config_dir())'
Assert-Exit "Config discovery"
$ConfigDir = "$ConfigDir".Trim()
New-Item -ItemType Directory -Force -Path (Join-Path $ConfigDir "skills"), (Join-Path $ConfigDir "plugins") | Out-Null

$VenvBinDir = Join-Path $VenvDir "Scripts"
$Launcher = Join-Path $VenvBinDir "guyline.exe"
if (-not (Test-Path -LiteralPath $Launcher)) { throw "Guyline launcher missing: $Launcher" }
& $Launcher --version
Assert-Exit "Launcher verification"
$CurrentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if (($CurrentPath -split ";") -notcontains $VenvBinDir) {
    [Environment]::SetEnvironmentVariable("PATH", "$VenvBinDir;$CurrentPath", "User")
}
Write-Host "Guyline installed from $Target. Restart your terminal to refresh PATH."
Write-Host "Run: guyline, guyline agent, or guyline gateway --help."
