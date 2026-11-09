# Ein-Klick-Ablauf: Redis starten -> redis-py installieren -> Daten laden -> importieren -> Antworten speichern
# Aufruf (im Ordner Praktikum1):  powershell -ExecutionPolicy Bypass -File scripts\run_all.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$env:PYTHONIOENCODING = "utf-8"
New-Item -ItemType Directory -Force -Path results | Out-Null

Write-Host "== 1/6 Python pruefen =="
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
if (-not $py) { throw "Python nicht gefunden. Bitte Python 3 installieren (Haken bei 'Add python.exe to PATH')." }
$python = $py.Source
& $python --version

Write-Host "== 2/6 Docker pruefen (Docker Desktop wird ggf. gestartet) =="
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker nicht gefunden. Bitte Docker Desktop installieren: https://www.docker.com/products/docker-desktop/"
}
$ErrorActionPreference = "Continue"
docker info *> $null
if ($LASTEXITCODE -ne 0) {
    $dd = Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dd) { Write-Host "Starte Docker Desktop ..."; Start-Process $dd }
    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Seconds 3
        docker info *> $null
        if ($LASTEXITCODE -eq 0) { break }
    }
    if ($LASTEXITCODE -ne 0) { throw "Docker Engine laeuft nicht (nach 3 Minuten). Docker Desktop oeffnen und Status pruefen." }
}
$ErrorActionPreference = "Stop"
docker --version

Write-Host "== 3/6 Redis-Container starten =="
& (Join-Path $PSScriptRoot "start_redis.ps1")

Write-Host "== 4/6 redis-py installieren =="
& $python -m pip install -r requirements.txt
& $python -c "import redis; print('redis-py', redis.__version__)"

Write-Host "== 5/6 Daten pruefen / herunterladen =="
if (-not (Test-Path "data\business.json") -or -not (Test-Path "data\businessS.json")) {
    & (Join-Path $PSScriptRoot "download_data.ps1")
}
Get-ChildItem data | Format-Table Name, Length

Write-Host "== 6/6 Strukturanalyse + Import + Antworten (dauert einige Minuten) =="
& $python analyze_structure.py data\businessS.json | Tee-Object -FilePath results\struktur_local.txt
& $python load_data.py data\business.json --flush | Tee-Object -FilePath results\import_local.txt
& $python answers.py | Tee-Object -FilePath results\antworten_local.txt

Write-Host "`nFERTIG. Umgebung laeuft. Interaktive Suche:  python autocomplete.py"
