Param()

$ErrorActionPreference = 'Stop'

$path = Join-Path (Get-Location) 'TASKS2.md'
if (-not (Test-Path $path)) {
    Write-Error "TASKS2.md not found"
    exit 1
}

$lines = Get-Content $path -Encoding UTF8
$marker = '## Полный архив TASKS2 (git history snapshot)'
$idx = $lines.IndexOf($marker)

if ($idx -lt 0) {
    Write-Host 'Marker not found; no changes'
    exit 0
}

# Keep content before the marker (one line above header spacing)
$keepUntil = [Math]::Max(0, $idx - 1)
$kept = @()
if ($keepUntil -gt 0) {
    $kept = $lines[0..($keepUntil-1)]
}

$note = @(
    '## Полный архив TASKS2 (git history snapshot)',
    '',
    'См. внешний архив: TASKS2_FULL_ARCHIVE_UTF8.md (UTF-8).',
    'Архив вынесен из этого файла для корректного отображения и размера репозитория.'
)

$out = @()
$out += $kept
$out += $note

Set-Content -Path $path -Value $out -Encoding UTF8
Write-Host 'Inline archive removed. Note inserted.'


