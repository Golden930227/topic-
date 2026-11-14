$ErrorActionPreference = 'Stop'
$env:VITE_WORKER_REMOTE = '1'
try {
    Push-Location $PSScriptRoot
    try { & npm.cmd run build -- --outDir .windmind-remote-dist }
    finally { Pop-Location }
    if ($LASTEXITCODE -ne 0) { throw 'Remote React build failed.' }
} finally { Remove-Item Env:VITE_WORKER_REMOTE -ErrorAction SilentlyContinue }
Write-Host 'Remote React build ready: .windmind-remote-dist'
