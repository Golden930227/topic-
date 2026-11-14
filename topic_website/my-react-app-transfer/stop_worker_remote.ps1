$ErrorActionPreference = 'Stop'
$tunnelFile = Join-Path $PSScriptRoot '.windmind-logs\remote-tunnel-pid.txt'
if (Test-Path -LiteralPath $tunnelFile) {
    $tunnelId = (Get-Content -LiteralPath $tunnelFile -Raw).Trim()
    if ($tunnelId -match '^\d+$') { Stop-Process -Id ([int]$tunnelId) -ErrorAction SilentlyContinue }
    Remove-Item -LiteralPath $tunnelFile -Force
}
$urlFile = Join-Path $PSScriptRoot '.windmind-logs\remote-tunnel-url.txt'
if (Test-Path -LiteralPath $urlFile) { Remove-Item -LiteralPath $urlFile -Force }
$file = Join-Path $PSScriptRoot '.windmind-logs\remote-pids.txt'
if (-not (Test-Path -LiteralPath $file)) { Write-Host 'No remote services recorded.'; return }
foreach ($processId in (Get-Content -LiteralPath $file)) {
    if ($processId -match '^\d+$') { Stop-Process -Id ([int]$processId) -ErrorAction SilentlyContinue }
}
Remove-Item -LiteralPath $file -Force
Write-Host 'WindMind remote services stopped.'
