param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$pages = Join-Path $root 'su_data_蘇崇維資料\data_preprocessing\output\pages'
$logs = Join-Path $root '.windmind-logs'
New-Item -ItemType Directory -Path $logs -Force | Out-Null
$python = (Get-Command python.exe -ErrorAction Stop).Source
$node = (Get-Command node.exe -ErrorAction Stop).Source
$env:CORS_ORIGINS = 'http://localhost:5173,http://localhost:5174,http://localhost:5175,http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:5175'
$services = @(
    @{ Name='api'; Dir=$pages; Port=8000; Exe=$python; Args=@('-m','uvicorn','sql_api:app','--host','127.0.0.1','--port','8000'); Path='/openapi.json' },
    @{ Name='main'; Dir=$root; Port=5173 },
    @{ Name='ai'; Dir=(Join-Path $pages 'ai_model\ai_monitor_web'); Port=5174 },
    @{ Name='cnn'; Dir=(Join-Path $pages 'cnn_monitor\cnn_monitor_web'); Port=5175 },
    @{ Name='sql-monitor'; Dir=$root; Port=8502; Exe=$python; Args=@('-m','streamlit','run','streamlist.py','--server.address','127.0.0.1','--server.port','8502','--server.headless','true'); Path='/_stcore/health' }
)
foreach ($service in $services) {
    if ($service.Name -in @('main', 'ai', 'cnn')) {
        $vite = Join-Path $service.Dir 'node_modules\vite\bin\vite.js'
        if (-not (Test-Path -LiteralPath $vite)) { throw "Missing Vite dependencies: $($service.Dir). Run npm install in that folder." }
        $service.Exe = $node
        $service.Args = @(('"' + $vite + '"'),'--host','127.0.0.1','--port',([string]$service.Port),'--strictPort')
        $service.Path = '/'
    }
}
foreach ($service in $services) {
    $url = "http://127.0.0.1:$($service.Port)$($service.Path)"
    $listener = Get-NetTCPConnection -State Listen -LocalPort $service.Port -ErrorAction SilentlyContinue
    if ($listener) {
        $owner = Get-CimInstance Win32_Process -Filter "ProcessId = $($listener[0].OwningProcess)"
        $expected = if ($service.Name -eq 'api') { 'sql_api:app' } elseif ($service.Name -eq 'sql-monitor') { 'streamlist.py' } else { Join-Path $service.Dir 'node_modules\vite\bin\vite.js' }
        if (-not $owner -or $owner.CommandLine -notlike "*$expected*") { throw "Port $($service.Port) is occupied by another process. See PID $($listener[0].OwningProcess)." }
        Write-Host "Reusing $($service.Name): $url"
    } else {
        $process = Start-Process -FilePath $service.Exe -ArgumentList $service.Args -WorkingDirectory $service.Dir -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logs "$($service.Name).out.log") -RedirectStandardError (Join-Path $logs "$($service.Name).err.log") -PassThru
        $service.Process = $process
    }
    $ready = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        try {
            $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) { $ready = $true; break }
        } catch { }
        if ($service.Process -and $service.Process.HasExited) { break }
        Start-Sleep -Milliseconds 500
    }
    if (-not $ready) { throw "Service $($service.Name) failed. Check $logs\$($service.Name).err.log" }
    Write-Host "Ready: $($service.Name) $url" -ForegroundColor Green
}
try {
    $health = Invoke-RestMethod 'http://127.0.0.1:8000/api/health' -TimeoutSec 10
    Write-Host "SQL connected: $($health.database)" -ForegroundColor Green
} catch { Write-Warning 'API is running, but SQL health check failed. Check SQL Server and database settings.' }
try {
    & (Join-Path $root 'start_pipeline_monitor.ps1')
} catch {
    Write-Warning "Pipeline monitor startup failed: $_. Other WindMind services are still running."
}
if (-not $NoBrowser) {
    Start-Process 'http://127.0.0.1:5173/internal'
}
Write-Host "WindMind started. Logs: $logs"
