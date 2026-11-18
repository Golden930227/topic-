param([switch]$GoogleLoginOnly)
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$logs = Join-Path $root '.windmind-logs'
$tunnelArgs = @('tunnel','--url','http://127.0.0.1:18764')
# Keep the existing email gate unless Google-only access is explicitly selected.
if (-not $GoogleLoginOnly) {
    & (Join-Path $root 'prepare_cloudflare_allowlist.ps1') -ShowCount
    $allowlist = ((Get-Content -LiteralPath (Join-Path $root '.env.worker.local') -Raw -Encoding UTF8).Trim() -split '=', 2)[1]
    if (-not $allowlist -or $allowlist -notmatch '^[a-z0-9@.,+_%-]+$') { throw 'Refusing to start an unrestricted Tunnel.' }
    $tunnelArgs += @('--allowed-mail',$allowlist)
} else {
    # Refuse to publish if the application's own login check is unavailable.
    foreach ($apiPath in @('/api/health','/api/cnn','/api/ai','/api/access')) {
        $status = 0
        try { $status = (Invoke-WebRequest -Uri ('http://127.0.0.1:18764' + $apiPath) -UseBasicParsing -TimeoutSec 5).StatusCode }
        catch { if ($_.Exception.Response) { $status = [int]$_.Exception.Response.StatusCode } else { throw } }
        if ($status -ne 401) { throw "Refusing Google-only Tunnel: anonymous $apiPath returned $status instead of 401." }
    }
}
$response = Invoke-WebRequest -Uri 'http://127.0.0.1:18764/healthz' -UseBasicParsing -TimeoutSec 3
if ($response.StatusCode -ne 200) { throw 'Worker proxy is not ready.' }
$cloudflared = (Get-Command cloudflared.exe -ErrorAction Stop).Source
$pidFile = Join-Path $logs 'remote-tunnel-pid.txt'
if (Test-Path -LiteralPath $pidFile) {
    $previous = Get-Content -LiteralPath $pidFile -Raw
    if ($previous -match '^\s*\d+\s*$' -and (Get-Process -Id ([int]$previous) -ErrorAction SilentlyContinue)) { throw 'A worker Tunnel is already running.' }
}
$out = Join-Path $logs 'remote-tunnel.out.log'
$err = Join-Path $logs 'remote-tunnel.err.log'
$process = Start-Process -FilePath $cloudflared -ArgumentList $tunnelArgs `
    -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput $out -RedirectStandardError $err -PassThru
try {
    $url = $null
    for ($attempt = 0; $attempt -lt 40; $attempt++) {
        if ($process.HasExited) { throw "cloudflared exited early. See $err" }
        if (Test-Path -LiteralPath $err) {
            $logContent = Get-Content -LiteralPath $err -Raw
            if ($logContent) {
                $match = [regex]::Match($logContent, 'https://[a-z0-9-]+\.trycloudflare\.com')
                if ($match.Success) { $url = $match.Value; break }
            }
        }
        Start-Sleep -Milliseconds 500
    }
    if (-not $url) { throw "Tunnel URL was not reported. See $err" }
    $process.Id | Set-Content -LiteralPath $pidFile -Encoding ASCII
    $url | Set-Content -LiteralPath (Join-Path $logs 'remote-tunnel-url.txt') -Encoding ASCII
    if ($GoogleLoginOnly) { Write-Host "Google-login website URL: $url/" -ForegroundColor Green }
    else { Write-Host "Email-protected website URL: $url/" -ForegroundColor Green }
    Write-Host 'Quick Tunnel URL changes on each start and has no uptime guarantee.'
} catch {
    Stop-Process -Id $process.Id -ErrorAction SilentlyContinue
    throw
}
