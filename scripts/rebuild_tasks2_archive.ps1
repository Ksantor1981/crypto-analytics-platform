Param()

$ErrorActionPreference = 'Stop'

$archive = 'TASKS2_FULL_ARCHIVE_UTF8.md'
if (Test-Path $archive) {
    Remove-Item $archive -Force
}

function Get-GitBlobBytes([string]$spec) {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = 'git'
    $psi.Arguments = "show $spec"
    $psi.RedirectStandardOutput = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $p = [System.Diagnostics.Process]::Start($psi)
    $ms = New-Object System.IO.MemoryStream
    $p.StandardOutput.BaseStream.CopyTo($ms)
    $p.WaitForExit()
    return $ms.ToArray()
}

function Convert-ToUtf8Text([byte[]]$bytes) {
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        return [Text.Encoding]::UTF8.GetString($bytes, 3, $bytes.Length - 3)
    }
    if ($bytes.Length -ge 2 -and $bytes[0] -eq 0xFF -and $bytes[1] -eq 0xFE) {
        return [Text.Encoding]::Unicode.GetString($bytes, 2, $bytes.Length - 2)
    }
    if ($bytes.Length -ge 2 -and $bytes[0] -eq 0xFE -and $bytes[1] -eq 0xFF) {
        return [Text.Encoding]::BigEndianUnicode.GetString($bytes, 2, $bytes.Length - 2)
    }
    $sUtf8  = [Text.Encoding]::UTF8.GetString($bytes)
    $s1251  = [Text.Encoding]::GetEncoding(1251).GetString($bytes)
    $badUtf8 = ($sUtf8.ToCharArray()  | Where-Object { $_ -eq [char]0xFFFD }).Count
    $bad1251 = ($s1251.ToCharArray()  | Where-Object { $_ -eq [char]0xFFFD }).Count
    if ($badUtf8 -le $bad1251) { return $sUtf8 } else { return $s1251 }
}

$hashes = @(git log --pretty=format:'%H' --reverse -- TASKS2.md)
if ($hashes.Count -eq 0) {
    Write-Host 'No history for TASKS2.md'
    exit 0
}

$nl = [Environment]::NewLine
foreach ($h in $hashes) {
    [IO.File]::AppendAllText($archive, "$nl----- BEGIN TASKS2.md @ $h -----$nl", [Text.Encoding]::UTF8)
    $bytes = Get-GitBlobBytes "$h`:TASKS2.md"
    $text  = Convert-ToUtf8Text $bytes
    [IO.File]::AppendAllText($archive, $text + $nl, [Text.Encoding]::UTF8)
    [IO.File]::AppendAllText($archive, "----- END TASKS2.md @ $h -----$nl", [Text.Encoding]::UTF8)
}

Write-Host "Archive built: $archive"


