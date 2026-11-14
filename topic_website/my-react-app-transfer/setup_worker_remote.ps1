$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$python = Join-Path $root '.windmind-venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    & py -3.11 -m venv --system-site-packages (Join-Path $root '.windmind-venv')
    if ($LASTEXITCODE -ne 0) { throw 'Could not create Python 3.11 environment.' }
}
& $python -m pip install -r (Join-Path $root 'requirements-worker-remote.txt')
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
& $python -c 'import fastapi, uvicorn, streamlit, plotly, pandas, pyodbc'
if ($LASTEXITCODE -ne 0) { throw 'Python dependency verification failed.' }
Write-Host 'Worker dependencies ready.'
