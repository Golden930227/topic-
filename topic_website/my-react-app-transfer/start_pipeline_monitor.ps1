param([int]$Port = 8501)
$ErrorActionPreference = 'Stop'
if ($Port -lt 1024 -or $Port -gt 65535) { throw 'Invalid monitor port.' }
$monitorRoot = $PSScriptRoot
$monitorApp = Join-Path $monitorRoot 'pipeline_monitor\app.py'
$monitorLogs = Join-Path $monitorRoot '.windmind-logs'
New-Item -ItemType Directory -Path $monitorLogs -Force | Out-Null
$monitorUrl = "http://127.0.0.1:$Port"
$listener = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)
if ($listener.Count -gt 0) {
    foreach ($entry in $listener) {
        $owner = Get-CimInstance Win32_Process -Filter "ProcessId = $($entry.OwningProcess)"
        if ($entry.LocalAddress -ne '127.0.0.1' -or -not $owner -or $owner.CommandLine -notlike "*$monitorApp*") {
            throw "Monitor port $Port is occupied (PID $($entry.OwningProcess)); existing service was left untouched."
        }
    }
    $response = Invoke-WebRequest -Uri "$monitorUrl/_stcore/health" -UseBasicParsing -TimeoutSec 3
    if ($response.StatusCode -ne 200) { throw 'Existing monitor failed health check.' }
    Write-Host "Reusing Pipeline Monitoring Center: $monitorUrl"
    return
}
$monitorPython = (Get-Command python.exe -ErrorAction Stop).Source
& $monitorPython -c 'import streamlit, plotly, pandas, pyodbc'
if ($LASTEXITCODE -ne 0) { throw 'Missing monitor dependencies. Run python -m pip install -r requirements-monitor.txt' }
$codeFile = Join-Path $monitorLogs 'monitor-access.txt'
if (-not (Test-Path -LiteralPath $codeFile)) {
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $bytes = New-Object byte[] 32
        $rng.GetBytes($bytes)
        [Convert]::ToBase64String($bytes) | Set-Content -LiteralPath $codeFile -Encoding ASCII
    } finally { $rng.Dispose() }
}
$env:WINDMIND_MONITOR_ACCESS_CODE = (Get-Content -LiteralPath $codeFile -Raw).Trim()
if ($env:WINDMIND_MONITOR_ACCESS_CODE.Length -lt 32) { throw 'Invalid local access code; rotate monitor-access.txt before starting.' }
try {
    $arguments = @('-m', 'streamlit', 'run', ('"' + $monitorApp + '"'),
        '--server.address', '127.0.0.1', '--server.port', [string]$Port,
        '--server.headless', 'true', '--browser.gatherUsageStats', 'false',
        '--theme.base', 'dark')
    $monitorProcess = Start-Process -FilePath $monitorPython -ArgumentList $arguments -WorkingDirectory $monitorRoot -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $monitorLogs 'monitor.out.log') `
        -RedirectStandardError (Join-Path $monitorLogs 'monitor.err.log')
} finally { Remove-Item Env:WINDMIND_MONITOR_ACCESS_CODE -ErrorAction SilentlyContinue }
$monitorReady = $false
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    try {
        $response = Invoke-WebRequest -Uri "$monitorUrl/_stcore/health" -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -eq 200) { $monitorReady = $true; break }
    } catch { }
    if ($monitorProcess.HasExited) { break }
    Start-Sleep -Milliseconds 500
}
if (-not $monitorReady) { throw 'Monitor did not become ready. Check .windmind-logs/monitor.err.log. Other services are unaffected.' }
Write-Host "Pipeline Monitoring Center ready: $monitorUrl (LOCAL DEVELOPMENT ONLY)" -ForegroundColor Green
Write-Host "Local access code file: $codeFile"
