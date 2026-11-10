# Isolated port collision check; leaves the production port 8501 untouched.
$ErrorActionPreference = 'Stop'
$monitorProject = Split-Path -Parent $PSScriptRoot
$testListener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, 0)
$testListener.Start()
try {
    $testPort = $testListener.LocalEndpoint.Port
    $rejected = $false
    try {
        & (Join-Path $monitorProject 'start_pipeline_monitor.ps1') -Port $testPort
    } catch {
        if ($_.Exception.Message -notlike '*occupied*') { throw }
        $rejected = $true
    }
    if (-not $rejected) { throw 'Occupied monitor port was not rejected.' }
    if (-not $testListener.Server.IsBound) { throw 'Existing listener was interrupted.' }
    Write-Host 'PASS: occupied port rejected; existing listener left running.'
} finally {
    $testListener.Stop()
}
