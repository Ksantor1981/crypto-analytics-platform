Param()

$ErrorActionPreference = 'Stop'

$path = Join-Path (Get-Location) 'TASKS2.md'
if (-not (Test-Path $path)) {
    Write-Error 'TASKS2.md not found'
    exit 1
}

$lines = Get-Content $path -Encoding UTF8
$match = $lines | Select-String -Pattern '\(git history snapshot\)' | Select-Object -First 1

if ($null -ne $match) {
    $idx = $match.LineNumber
    # keep everything before the archive header (one blank line above)
    if ($idx -gt 1) {
        $keep = $lines[0..($idx-2)]
    } else {
        $keep = @()
    }
} else {
    # no archive marker found, keep file as is
    $keep = $lines
}

$note = @(
    '## Full TASKS2 archive (git history snapshot)',
    '',
    'See external file: TASKS2_FULL_ARCHIVE_UTF8.md (UTF-8).',
    'Archive was moved out of this file to prevent encoding issues and large diffs.'
)

$final = @()
$final += $keep
$final += $note

Set-Content -Path $path -Value $final -Encoding UTF8
Write-Host 'TASKS2.md cleaned and saved as UTF-8.'


