<# Rebuild/import through the shared Python classifier; no mailbox access here. #>
param(
    [switch]$Push,
    [string]$Python = 'python',
    [string]$ImportJson = ''
)

$ErrorActionPreference = 'Stop'
$syncArgs = @((Join-Path $PSScriptRoot 'sync_emails.py'))
if ($ImportJson) { $syncArgs += @('--import-json', $ImportJson) }
if ($Push) { $syncArgs += '--push' }
& $Python @syncArgs
if ($LASTEXITCODE -ne 0) { throw "Email index rebuild failed (exit $LASTEXITCODE)." }
