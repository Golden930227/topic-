$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
& (Join-Path $root 'prepare_cloudflare_allowlist.ps1') -ShowCount
$allowlistPath = Join-Path $root '.env.worker.local'
$line = (Get-Content -LiteralPath $allowlistPath -Raw -Encoding UTF8).Trim()
if ($line -notmatch '^WINDMIND_ALLOWED_EMAILS=([a-z0-9@.,+_%-]+)$') { throw 'Invalid local Cloudflare allowlist.' }
$emails = $Matches[1]
if (-not $emails) { throw 'Refusing to start an unrestricted Tunnel.' }
$cloudflared = (Get-Command cloudflared.exe -ErrorAction Stop).Source
$python = (Get-Command python.exe -ErrorAction Stop).Source
$probe = Join-Path $root '.windmind-logs\cloudflare-probe'
New-Item -ItemType Directory -Path $probe -Force | Out-Null
[System.IO.File]::WriteAllText((Join-Path $probe 'index.html'), '<!doctype html><html lang="en"><meta charset="utf-8"><title>WindMind Tunnel Test</title><body>WindMind Tunnel Test OK</body></html>', [System.Text.UTF8Encoding]::new($false))
$port = 18765
if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) { throw "Probe port $port is already in use." }
$server = Start-Process -FilePath $python -ArgumentList @('-m','http.server',[string]$port,'--bind','127.0.0.1','--directory',('"' + $probe + '"')) -WorkingDirectory $root -WindowStyle Hidden -PassThru
try {
    $ready = $false
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:$port/" -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200 -and $response.Content -like '*WindMind Tunnel Test OK*') { $ready = $true; break }
        } catch { }
        if ($server.HasExited) { break }
        Start-Sleep -Milliseconds 250
    }
    if (-not $ready) { throw 'Local test page failed to start.' }
    Write-Host 'Protected Cloudflare probe starting. Copy the temporary trycloudflare.com URL below.'
    Write-Host 'Test an unauthorized email in a private browser window, then test an allowed email. Press Ctrl+C to stop.'
    & $cloudflared tunnel --url "http://127.0.0.1:$port" --allowed-mail $emails
    if ($LASTEXITCODE -ne 0) { throw "cloudflared exited with code $LASTEXITCODE" }
} finally {
    if (-not $server.HasExited) { Stop-Process -Id $server.Id -ErrorAction SilentlyContinue }
}
