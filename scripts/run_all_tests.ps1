$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$env:UV_CACHE_DIR = Join-Path $projectRoot '.uv-cache'

# Make a user-scoped Winget Node installation visible to shells opened earlier.
if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    $nodePackage = Get-ChildItem (Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages') -Directory -Filter 'OpenJS.NodeJS.LTS_*' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($nodePackage) {
        $nodeDirectory = Get-ChildItem $nodePackage.FullName -Directory -Filter 'node-v*-win-x64' -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($nodeDirectory) { $env:PATH = "$($nodeDirectory.FullName);$env:PATH" }
    }
}
$npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $npm) { throw 'Node.js/npm is required. Install the project dependencies first.' }

Push-Location (Join-Path $projectRoot 'frontend')
try {
    & $npm.Source run test:ui
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally { Pop-Location }

uv run --project $projectRoot --group dev python (Join-Path $projectRoot 'scripts/run_coverage.py')
exit $LASTEXITCODE
