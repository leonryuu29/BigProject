# Lädt die Yelp-Dateien von Sciebo nach .\data herunter.
# Achtung: in PowerShell ist "curl" ein Alias für Invoke-WebRequest -> curl.exe verwenden.
# "curl -O ...download" aus der Aufgabe würde beide Dateien als "download" speichern
# (die zweite überschreibt die erste), deshalb hier mit eindeutigen Namen und -L.

$root = Split-Path -Parent $PSScriptRoot
$data = Join-Path $root "data"
New-Item -ItemType Directory -Force -Path $data | Out-Null

$urls = @(
  "https://hsbi.sciebo.de/s/REoBXKjpLjViIbJ/download",
  "https://hsbi.sciebo.de/s/KYRLLYOItgJ3Ulp/download"
)
$i = 0
foreach ($u in $urls) {
    $i++
    $tmp = Join-Path $data "download_$i.json"
    Write-Host "Lade $u ..."
    curl.exe -L -o $tmp $u
    # Zuordnung über die Größe: business.json ~135 MB, businessS.json ~143 kB
    $size = (Get-Item $tmp).Length
    if ($size -gt 10MB) { $target = "business.json" } else { $target = "businessS.json" }
    Move-Item -Force $tmp (Join-Path $data $target)
    Write-Host ("  -> data\{0}  ({1:N0} Bytes)" -f $target, $size)
}
