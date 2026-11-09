# Startet den Redis-Container (benötigt Docker Desktop).
# Original-Befehl aus der Aufgabe (blockiert das Terminal, Ctrl+C beendet den Server):
#   docker run --name RedisPraktikum2026 -p 6379:6379 -it redis:latest
# Hier im Hintergrund (-d), damit dasselbe Terminal für Python frei bleibt.

$name = "RedisPraktikum2026"
$exists = docker ps -a --filter "name=^$name$" --format "{{.Names}}"
if ($exists -eq $name) {
    Write-Host "Container $name existiert bereits -> starte ihn."
    docker start $name | Out-Null
} else {
    docker run --name $name -p 6379:6379 -d redis:latest | Out-Null
}
Start-Sleep -Seconds 2
docker exec $name redis-cli ping
Write-Host "redis-cli öffnen mit:  docker exec -it $name redis-cli"
