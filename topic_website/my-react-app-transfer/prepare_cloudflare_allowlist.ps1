param(
    [string]$ProjectRoot = $PSScriptRoot,
    [switch]$ShowCount
)
$ErrorActionPreference = 'Stop'
$source = Join-Path $ProjectRoot 'src\App.jsx'
$gitignore = Join-Path $ProjectRoot '.gitignore'
if (-not (Test-Path -LiteralPath $source)) { throw "Missing employee source: $source" }
if (-not (Select-String -LiteralPath $gitignore -Pattern '^\.env\*\s*$' -Quiet)) { throw 'Project must ignore .env* before writing employee addresses.' }
$content = Get-Content -LiteralPath $source -Raw -Encoding UTF8
$match = [regex]::Match($content, '(?s)const\s+allowedEmails\s*=\s*\[(.*?)\]')
if (-not $match.Success) { throw 'Could not locate App.jsx employee allowlist.' }
$withoutComments = [regex]::Replace($match.Groups[1].Value, '(?m)//.*$', '')
$addresses = @([regex]::Matches($withoutComments, '["'']([^"'']+@[^"'']+)["'']') | ForEach-Object { $_.Groups[1].Value.Trim().ToLowerInvariant() } | Sort-Object -Unique)
if ($addresses.Count -eq 0) { throw 'Employee allowlist is empty.' }
foreach ($address in $addresses) {
    if ($address -notmatch '^[a-z0-9.!#$%&''*+/=?^_`{|}~-]+@[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\.[a-z]{2,}$') { throw 'Invalid email in App.jsx allowlist.' }
}
$destination = Join-Path $ProjectRoot '.env.worker.local'
$value = 'WINDMIND_ALLOWED_EMAILS=' + ($addresses -join ',')
[System.IO.File]::WriteAllText($destination, $value + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
if ($ShowCount) { Write-Host "Prepared $($addresses.Count) employee addresses in $destination" }
