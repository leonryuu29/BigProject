# Testbericht – Big Data, 1. Praktikum (Redis + Yelp)

| | |
|---|---|
| Datum | 09.11.2026 |
| Testobjekt | `yelp_redis.py`, `load_data.py`, `autocomplete.py`, `answers.py` (Aufgabe 2a–2d) |
| Testdatei | `tests/test_yelp_redis.py` (Python `unittest`, keine Zusatzpakete nötig) |
| Ergebnis | **23 / 23 bestanden**, 0 Fehler, 0 übersprungen (Laufzeit 25,8 s inkl. Vollimport) |
| Rohausgabe | `results/test_output.txt` |

## 1. Testumgebungen

| | Umgebung A (Testlauf dieses Berichts) | Umgebung B (lokaler Rechner) |
|---|---|---|
| Betriebssystem | Linux (Cloud-Container) | Windows 11 (10.0.22631) |
| Redis-Server | 7.0.15 | 5.0.14.1 (tporadowski, portabel) |
| Python | 3.13 | 3.10.11 |
| Redis-Client | minimaler RESP-Client mit derselben API (redis-py war offline nicht installierbar) | redis-py 8.1.0 |
| Daten | `business.json` (192.609 Zeilen), `tests/sample_synthetic.json` | dieselben Dateien unter `data\` |

In Umgebung B wurden Installation, Serverstart (`PONG`) und Installation von redis-py über `deploy.bat` erfolgreich durchgeführt. Die Tests lassen sich dort mit **`run_tests.bat`** ausführen; die Ausgabe landet in `results\test_output_local.txt`.

## 2. Teststrategie

Die Tests laufen gegen einen **echten Redis-Server**, aber in **Datenbank 15**, damit die importierten Daten in Datenbank 0 nicht verändert werden. Jede Testklasse leert db 15 am Ende wieder.

1. **Fixture-Tests** – 12 handverlesene Datensätze mit bekannten Sonderfällen: drei Starbucks-Filialen in unterschiedlicher Schreibweise (`Starbucks`/`STARBUCKS`), eine Namensvariante (`Starbucks Coffee`), zwei verschiedene „The Still“, ähnliche Präfixe (`The Stirling Room`, `Star Pizza`) sowie Namen mit Umlauten, CJK- und vietnamesischen Zeichen. Eine Leerzeile am Dateiende prüft robustes Einlesen; `batch_size=3` erzwingt mehrere Pipeline-Flushes.
2. **Synthetische Datei** – 200 Datensätze im Yelp-Format (`tests/sample_synthetic.json`).
3. **Echte Daten** – Vollimport von `business.json` und Abgleich mit den Antworten der Abgabe. Wird automatisch übersprungen, wenn `data/business.json` fehlt.

## 3. Testfälle und Ergebnisse

### 3.1 Import (Aufgabe 2a)

| ID | Testfall | Erwartet | Ergebnis |
|---|---|---|---|
| T01 | Anzahl importierter Datensätze, Leerzeilen ignorieren | 12 | ✅ |
| T02 | `business:<id>` enthält den **unveränderten** JSON-String (inkl. Unicode) | identisch mit Quellzeile | ✅ |
| T03 | Gesamtzahl der Keys | Betriebe + verschiedene Namen + 1 Index | ✅ |

### 3.2 Namens-Sets (Aufgabe 2b)

| ID | Testfall | Erwartet | Ergebnis |
|---|---|---|---|
| T04 | Key ist Name in Kleinbuchstaben, Typ `set`; `Starbucks` und `STARBUCKS` werden zusammengeführt | `{sb-1, sb-2, sb-3}` | ✅ |
| T05 | Zweiter Import ohne `--flush` erzeugt keine Duplikate | `SCARD` und `ZCARD` unverändert | ✅ |

### 3.3 Autovervollständigung (Aufgabe 2c)

| ID | Eingabe | Erwartet | Ergebnis |
|---|---|---|---|
| T06 | `Star` | star pizza, starbucks, starbucks coffee | ✅ |
| T07 | `sTaRbUcKs` (Groß-/Kleinschreibung egal) | starbucks, starbucks coffee | ✅ |
| T08 | `The Sti` | the still, the stirling room | ✅ |
| T09 | vollständiger Name `the still` | ist selbst enthalten | ✅ |
| T10 | nicht vorhandener Präfix | leere Liste | ✅ |
| T11 | leere Eingabe | leere Liste | ✅ |
| T12 | `s` mit `limit=2` | genau 2 Treffer, sortiert | ✅ |
| T13 | `Café M`, `寿`, `pho ð` (Unicode) | jeweils der passende Name | ✅ |
| T14 | `starbucks` liefert nicht `star pizza`; `zzz` (Ende des Index) | keine falschen Treffer | ✅ |

### 3.4 Details (Aufgabe 2d)

| ID | Testfall | Erwartet | Ergebnis |
|---|---|---|---|
| T15 | Details zu `The Still` | 2 Betriebe: Las Vegas 3,5★ (3400 S Las Vegas Blvd), Calgary 2,5★ | ✅ |
| T16 | unbekannter Name | leere Liste | ✅ |
| T17 | Textausgabe enthält Stadt und Sterne | „Calgary“, „3.5 Sterne“ | ✅ |

### 3.5 Synthetische Datei

| ID | Testfall | Erwartet | Ergebnis |
|---|---|---|---|
| T18 | Import von 200 Datensätzen, `starbucks` inkl. `STARBUCKS`, Präfix `the sti` | 200 / 5 / 3 Namen | ✅ |

### 3.6 Echte Daten (`business.json`)

| ID | Testfall | Erwartet | Ergebnis |
|---|---|---|---|
| T19 | Anzahl Datensätze | 192.609 | ✅ |
| T20 | verschiedene Namen | 144.337 | ✅ |
| T21 | Starbucks: exakter Name / alle mit Präfix | 1.066 / 1.073 | ✅ |
| T22 | Präfix `Star` | 181 Namen | ✅ |
| T23 | `The Still`: Anzahl, Präfix `The Sti`, Städte | 2; the still, the stirling club spa, the stirling room; Calgary + Las Vegas | ✅ |

## 4. Während der Entwicklung gefundene und behobene Fehler

| Problem | Ursache | Lösung |
|---|---|---|
| Präfixsuche hätte Namen übersehen, bei denen nach dem Präfix ein Zeichen jenseits von U+00FF folgt | Obergrenze ursprünglich als Zeichen `'\xff'` (UTF-8: `C3 BF`) | Obergrenze als **Byte** `0xFF` angehängt; kommt in gültigem UTF-8 nie vor (abgesichert durch T13) |
| `deploy.bat` brach unter Windows sofort ab („`﻿#` is not recognized“) | PowerShell-Skript hatte eine doppelte UTF-8-BOM | BOM normalisiert |
| Deployment stoppte beim ersten `redis-cli ping` | Unter `ErrorActionPreference = Stop` wertet PowerShell 5.1 stderr-Ausgaben nativer Programme als Fehler; vor dem Serverstart schlägt `ping` aber erwartungsgemäß fehl | Fehlerbehandlung für native Befehle gelockert, Prüfung über `$LASTEXITCODE` |
| Datensatzzahl weicht von der Aufgabenstellung ab (192.609 statt 209.393) | Gelieferte Datei stammt aus einer anderen Version des Yelp-Datensatzes | kein Codefehler; in der Abgabe dokumentiert |

## 5. Grenzen der Tests

- Der Testlauf dieses Berichts nutzt Redis 7.0.15 und einen minimalen RESP-Client statt redis-py. Die verwendeten Befehle (`SET`, `SADD`, `ZADD`, `ZRANGEBYLEX`, `MGET`, Pipelines) existieren unverändert seit Redis 2.8 und in redis-py; zur Bestätigung in Umgebung B `run_tests.bat` ausführen.
- `autocomplete.py` (die `input()`-Schleife) wird nicht automatisch getestet; ihre Logik steckt in `autocomplete()` und `details()`, die vollständig abgedeckt sind. Ein manueller Durchlauf auf echten Daten liegt in `results/autocomplete_demo.txt`.
- Aufgabe 1 (redis-cli) ist eine manuelle Übung; Befehle und Ausgaben stehen in `aufgabe1_redis_cli.md`.

## 6. Continuous Integration

Die Workflow-Datei `.github/workflows/praktikum1-tests.yml` führt bei jedem Push oder Pull Request auf `Praktikum1/**` die Testsuite automatisch aus:

- Matrix: Python 3.10 / 3.13 × Redis 5 / 7 (offizielle Docker-Images als Service-Container), also 4 Jobs
- Schritte: redis-py installieren → Syntaxprüfung → `unittest` → Smoke-Test (Strukturanalyse, Import, Autocomplete auf synthetischen Daten)
- Die Testausgabe jedes Jobs wird als Artefakt gespeichert
- `RealDataTests` werden dort übersprungen (`business.json` ist nicht eingecheckt); erwartet: 18 bestanden, 5 übersprungen

Damit wird auch die Lücke aus Abschnitt 5 geschlossen: In CI laufen die Tests mit dem echten redis-py und zusätzlich gegen Redis 5, also dieselbe Hauptversion wie das portable Redis unter Windows.

## 7. Tests ausführen

```bat
:: Windows (im Ordner Praktikum1, Redis wird bei Bedarf gestartet)
run_tests.bat
```

```bash
# beliebiges System mit laufendem Redis auf localhost:6379
python -m unittest discover -s tests -v
```
