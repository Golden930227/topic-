$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$logs = Join-Path $root '.windmind-logs'
$pidFile = Join-Path $logs 'remote-tunnel-pid.txt'
if (-not (Test-Path -LiteralPath $pidFile)) { throw 'Protected Tunnel is not running.' }
$tunnelId = (Get-Content -LiteralPath $pidFile -Raw).Trim()
if ($tunnelId -notmatch '^\d+$' -or -not (Get-Process -Id ([int]$tunnelId) -ErrorAction SilentlyContinue)) { throw 'Protected Tunnel process is not running.' }
$urlFile = Join-Path $logs 'remote-tunnel-url.txt'
if (Test-Path -LiteralPath $urlFile) {
    $url = (Get-Content -LiteralPath $urlFile -Raw).Trim()
} else {
    $url = [regex]::Match((Get-Content -LiteralPath (Join-Path $logs 'remote-tunnel.err.log') -Raw), 'https://[a-z0-9-]+\.trycloudflare\.com').Value
    if ($url) { $url | Set-Content -LiteralPath $urlFile -Encoding ASCII }
}
if ($url -notmatch '^https://[a-z0-9-]+\.trycloudflare\.com$') { throw 'Invalid temporary Tunnel URL.' }
$env:VITE_WORKER_TUNNEL_URL = $url
try {
    Push-Location $root
    try { & npm.cmd run build }
    finally { Pop-Location }
    if ($LASTEXITCODE -ne 0) { throw 'Vercel public site build failed.' }
} finally { Remove-Item Env:VITE_WORKER_TUNNEL_URL -ErrorAction SilentlyContinue }
$stage = Join-Path $logs ('vercel-stage-' + (Get-Date -Format 'yyyyMMddHHmmss'))
$static = Join-Path $stage '.vercel\output\static'
New-Item -ItemType Directory -Path $static -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $root '.vercel\project.json') -Destination (Join-Path $stage '.vercel\project.json') -Force
[System.IO.File]::WriteAllText((Join-Path $stage '.vercel\output\config.json'), '{"version":3,"routes":[{"handle":"filesystem"},{"src":"/.*","dest":"/index.html"}]}', [System.Text.UTF8Encoding]::new($false))
Get-ChildItem -LiteralPath (Join-Path $root 'dist') -Force | Where-Object { $_.Name -ne 'internal.html' } | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $static -Recurse -Force
}
$npx = (Get-Command npx.cmd -ErrorAction Stop).Source
& $npx --yes vercel deploy --prebuilt --prod --yes --cwd $stage
if ($LASTEXITCODE -ne 0) { throw 'Vercel production deployment failed.' }
Write-Host "Public employee login now forwards to: $url/internal" -ForegroundColor Green
