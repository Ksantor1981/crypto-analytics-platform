# Generate requirements-pinned.txt for reproducible installs
# Run from project root: .\scripts\generate_requirements_pinned.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Push-Location $root
foreach ($svc in @("backend", "ml-service", "workers")) {
    $req = Join-Path $svc "requirements.txt"
    if (Test-Path $req) {
        Write-Host "Generating $svc/requirements-pinned.txt..."
        Push-Location $svc
        pip install -r requirements.txt -q
        pip freeze | Out-File -FilePath "requirements-pinned.txt" -Encoding utf8
        Pop-Location
        Write-Host "  -> $svc/requirements-pinned.txt"
    }
}
Pop-Location
Write-Host "Done. Commit requirements-pinned.txt for reproducible builds."
