param([string]$Python)
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$logs = Join-Path $root '.windmind-logs'
$dist = Join-Path $root '.windmind-remote-dist'
$dataFolder = @(Get-ChildItem -LiteralPath $root -Directory | Where-Object { $_.Name -like 'su_data_*' })
if ($dataFolder.Count -ne 1) { throw 'Could not identify the data pages folder.' }
$pages = Join-Path $dataFolder[0].FullName 'data_preprocessing\output\pages'
$defaultPython = Join-Path $root '.windmind-venv\Scripts\python.exe'
if (-not $Python) { $Python = $defaultPython }
New-Item -ItemType Directory -Path $logs -Force | Out-Null
if (-not (Test-Path -LiteralPath $Python)) { throw "Python not found: $Python" }
if (-not (Test-Path -LiteralPath (Join-Path $dist 'index.html'))) { throw 'Remote site is not built. Run build_worker_remote.ps1 first.' }
& $Python -c 'import fastapi, uvicorn, streamlit, plotly, pandas, pyodbc'
if ($LASTEXITCODE -ne 0) { throw "Missing Python dependencies. Run: & '$Python' -m pip install -r requirements-worker-remote.txt" }
$node = (Get-Command node.exe -ErrorAction Stop).Source
$services = @(
    @{ Name='api'; Port=18000; Dir=$pages; Exe=$Python; Args=@('-m','uvicorn','sql_api:app','--host','127.0.0.1','--port','18000'); Path='/openapi.json' },
    @{ Name='pipeline'; Port=18501; Dir=$root; Exe=$Python; Args=@('-m','streamlit','run',(Join-Path $root 'pipeline_monitor\app.py'),'--server.address','127.0.0.1','--server.port','18501','--server.baseUrlPath','pipeline','--server.headless','true','--server.enableCORS','false','--server.enableXsrfProtection','false'); Path='/pipeline/_stcore/health' },
    @{ Name='sql-monitor'; Port=18502; Dir=$root; Exe=$Python; Args=@('-m','streamlit','run',(Join-Path $root 'streamlist.py'),'--server.address','127.0.0.1','--server.port','18502','--server.baseUrlPath','sql-monitor','--server.headless','true','--server.enableCORS','false','--server.enableXsrfProtection','false'); Path='/sql-monitor/_stcore/health' },
    @{ Name='proxy'; Port=18764; Dir=$root; Exe=$node; Args=@((Join-Path $root 'windmind_remote_proxy.cjs')); Path='/healthz' }
)
$owned = @()
$codeFile = Join-Path $logs 'monitor-access.txt'
if (-not (Test-Path -LiteralPath $codeFile)) {
    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    [Convert]::ToBase64String($bytes) | Set-Content -LiteralPath $codeFile -Encoding ASCII
}
try {
    foreach ($service in $services) {
        $listener = @(Get-NetTCPConnection -State Listen -LocalPort $service.Port -ErrorAction SilentlyContinue)
        if ($listener.Count) { throw "Port $($service.Port) is already occupied. Stop the other process first." }
        if ($service.Name -eq 'pipeline') { $env:WINDMIND_MONITOR_ACCESS_CODE = (Get-Content -LiteralPath $codeFile -Raw).Trim() }
        try {
            $process = Start-Process -FilePath $service.Exe -ArgumentList $service.Args -WorkingDirectory $service.Dir -WindowStyle Hidden -PassThru `
                -RedirectStandardOutput (Join-Path $logs "remote-$($service.Name).out.log") `
                -RedirectStandardError (Join-Path $logs "remote-$($service.Name).err.log")
        } finally { Remove-Item Env:WINDMIND_MONITOR_ACCESS_CODE -ErrorAction SilentlyContinue }
        $owned += $process.Id
        $url = "http://127.0.0.1:$($service.Port)$($service.Path)"
        $ready = $false
        for ($attempt = 0; $attempt -lt 40; $attempt++) {
            try { if ((Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200) { $ready = $true; break } } catch { }
            if ($process.HasExited) { break }
            Start-Sleep -Milliseconds 500
        }
        if (-not $ready) { throw "$($service.Name) failed. See $logs\remote-$($service.Name).err.log" }
        Write-Host "Ready: $($service.Name) $url" -ForegroundColor Green
    }
    $owned | Set-Content -LiteralPath (Join-Path $logs 'remote-pids.txt') -Encoding ASCII
    Write-Host 'Local worker entry: http://127.0.0.1:18764/worker'
    Write-Host 'Start a protected Cloudflare Tunnel only after unauthorized-email rejection has been verified.'
} catch {
    foreach ($id in $owned) { Stop-Process -Id $id -ErrorAction SilentlyContinue }
    throw
}
