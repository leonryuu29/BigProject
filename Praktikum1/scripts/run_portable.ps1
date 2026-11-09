# Lokale Umgebung OHNE Docker: portables Redis fuer Windows + redis-py, danach Import und Antworten.
# Aufruf: Doppelklick auf deploy.bat (oder: powershell -ExecutionPolicy Bypass -File scripts\run_portable.ps1)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$env:PYTHONIOENCODING = "utf-8"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
New-Item -ItemType Directory -Force -Path results, data | Out-Null

Write-Host "== 1/6 Python pruefen =="
$python = $null
foreach ($c in @("python", "py")) {
    $cmd = Get-Command $c -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source -notlike "*WindowsApps*") { $python = $cmd.Source; break }
}
if (-not $python) {
    throw "Python nicht gefunden. Bitte Downloads\python-3.13.6-amd64.exe ausfuehren und 'Add python.exe to PATH' anhaken, dann deploy.bat erneut starten."
}
& $python --version

Write-Host "== 2/6 Portables Redis fuer Windows (tporadowski/redis 5.0.14.1) =="
$redisDir = Join-Path $root "redis"
$redisExe = Join-Path $redisDir "redis-server.exe"
if (-not (Test-Path $redisExe)) {
    $zip = Join-Path $root "redis.zip"
    $url = "https://github.com/tporadowski/redis/releases/download/v5.0.14.1/Redis-x64-5.0.14.1.zip"
    Write-Host "Lade $url ..."
    Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
    Expand-Archive -Path $zip -DestinationPath $redisDir -Force
    Remove-Item $zip
}
& (Join-Path $redisDir "redis-server.exe") --version

Write-Host "== 3/6 Redis-Server starten (eigenes Fenster, Port 6379) =="
$cli = Join-Path $redisDir "redis-cli.exe"
$ErrorActionPreference = "Continue"
$pong = & $cli ping 2>$null
if ($pong -ne "PONG") {
    Start-Process -FilePath $redisExe -ArgumentList "--port 6379 --save `"`" --appendonly no" -WorkingDirectory $redisDir
    for ($i = 0; $i -lt 20; $i++) { Start-Sleep -Milliseconds 500; $pong = & $cli ping 2>$null; if ($pong -eq "PONG") { break } }
}
if ($pong -ne "PONG") { throw "Redis-Server antwortet nicht." }
Write-Host "Redis laeuft: $pong"

Write-Host "== 4/6 redis-py installieren =="
& $python -m pip install --upgrade -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "pip install fehlgeschlagen (Netzwerk/Proxy pruefen)." }
& $python -c "import redis; print('redis-py', redis.__version__)"

Write-Host "== 5/6 Daten pruefen / herunterladen =="
if (-not (Test-Path "data\business.json") -or -not (Test-Path "data\businessS.json")) {
    & (Join-Path $PSScriptRoot "download_data.ps1")
}
Get-ChildItem data | Format-Table Name, Length

Write-Host "== 6/6 Strukturanalyse + Import + Antworten =="
& $python analyze_structure.py data\businessS.json | Tee-Object -FilePath results\struktur_local.txt
& $python load_data.py data\business.json --flush | Tee-Object -FilePath results\import_local.txt
if ($LASTEXITCODE -ne 0) { throw "Import fehlgeschlagen." }
& $python answers.py | Tee-Object -FilePath results\antworten_local.txt

Write-Host ""
Write-Host "FERTIG. Umgebung laeuft (Redis-Fenster offen lassen)."
Write-Host "  redis-cli:          redis\redis-cli.exe"
Write-Host "  interaktive Suche:  python autocomplete.py   (oder autocomplete.bat)"
