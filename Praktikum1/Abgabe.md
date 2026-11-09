# Big Data – 1. Praktikum (Abgabe)

**Name:** _______________ · **Matrikelnr.:** _______________ · WS 2026/27

## Vorbereitung: Was bewirkt `docker run --name RedisPraktikum2026 -p 6379:6379 -it redis:latest`?

- `docker run` erzeugt aus einem Image einen **neuen Container und startet ihn**. Ist das Image lokal nicht vorhanden, wird es zuvor von Docker Hub geladen (*pull*).
- `redis:latest` – offizielles Redis-Image in der neuesten Version (Tag `latest`).
- `--name RedisPraktikum2026` – fester Containername statt einer zufälligen ID; damit lässt sich der Container später per `docker start/stop/exec RedisPraktikum2026` ansprechen.
- `-p 6379:6379` – Portweiterleitung *Host:Container*. Redis lauscht im Container auf Port 6379; erst durch das Mapping ist der Server vom Host aus (z. B. von Python über `localhost:6379`) erreichbar.
- `-it` – `-i` hält STDIN offen, `-t` weist ein Pseudo-Terminal zu. Der Server läuft im Vordergrund, sein Log erscheint im Terminal, `Ctrl+C` beendet ihn.
- Ohne `--rm` bleibt der Container nach dem Stoppen erhalten (`docker start -ai RedisPraktikum2026`). Ohne Volume (`-v`) liegen die Daten nur im Dateisystem des Containers und gehen mit `docker rm` verloren.

## Aufgabe 1: Fingerübungen

Siehe `aufgabe1_redis_cli.md` (alle Befehle der vier Datentypen mit Ausgaben). Beobachtungen:

- `GETSET`, `RPOPLPUSH`, `BRPOPLPUSH` sind seit Redis 6.2 *deprecated* (Ersatz: `SET … GET`, `LMOVE`, `BLMOVE`).
- Blockierende Befehle (`BLPOP`, `BRPOP`) warten bis zum Timeout, wenn die Liste leer ist, und liefern dann `nil`.
- `BITFIELD … INCRBY u8 0 100` auf 200 ergibt 44: Überlauf mit Standardverhalten `WRAP` (300 mod 256).
- Sets sind ungeordnet; `SMEMBERS`/`SUNION` liefern keine feste Reihenfolge.

## Aufgabe 2: Yelp-Business-Daten

### Struktur der Datei
`business.json` ist **JSON Lines**: ein vollständiges JSON-Objekt pro Zeile, kein JSON-Array. Die Datei wird daher zeilenweise gelesen (`json.loads` je Zeile), was auch den Speicherbedarf klein hält. Felder: `business_id, name, address, city, state, postal_code, latitude, longitude, stars, review_count, is_open, attributes, categories, hours`; `attributes` und `hours` sind verschachtelte Objekte, `categories` ein kommagetrennter String – alle drei können `null` sein. Unter Windows muss die Datei mit `encoding="utf-8"` geöffnet werden.

Die gelieferte `business.json` enthält **192.609** Datensätze (nicht 209.393 wie in der Aufgabenbeschreibung – die Angabe stammt offenbar aus einer anderen Version des Datensatzes). Alle `business_id`s sind eindeutig. 333 Namen enthalten führende/abschließende oder doppelte Leerzeichen.

### a) + b) Import
- `SET business:<business_id> <JSON-String>` (String)
- `SADD <name in lowercase> <business_id>` (Set; gleichnamige Filialen landen automatisch in derselben Menge)
- Import über eine **Pipeline** (`transaction=False`, je 5000 Datensätze), um die Netzwerk-Roundtrips drastisch zu reduzieren.
- Ergebnis: **192.609** Datensätze → **336.947** Keys (192.609 `business:*` + 144.337 Namens-Sets + 1 Sorted Set), **144.337** verschiedene Namen, Speicherbedarf ca. 224 MB, Importdauer ca. 28 s.

### c) Autovervollständigung
Statt `KEYS`/`SCAN` (lineare Suche über alle Keys, `KEYS` blockiert den Server) werden alle Namen zusätzlich in einem Sorted Set `autocomplete:names` mit identischem Score 0 abgelegt. Bei gleichem Score sortiert Redis lexikografisch nach Bytes, sodass eine Präfixsuche einer Bereichsabfrage entspricht:

`ZRANGEBYLEX autocomplete:names "[star" "[star\xff"` → Aufwand O(log N + M).

Als obere Schranke dient das Byte `0xFF`, das in gültigem UTF-8 nie vorkommt; damit werden auch Namen mit Umlauten oder nicht-lateinischen Zeichen korrekt gefunden.

- Beispiel "Star": **181** Namen, u. a. *star anise, star bar, star burger, …, starbucks, starbucks coffee, starbucks reserve, …, starlight nails & spa*.
- **Starbucks-Filialen:** unter dem exakten Namen `starbucks` sind **1.066** Einträge gelistet (davon 982 geöffnet, 84 geschlossen; v. a. AZ 264, ON 262, NV 183). Zählt man die Varianten *Starbucks Coffee* (6) und *Starbucks Reserve* (1) dazu, sind es **1.073**. Durch das Kleinschreiben werden Schreibweisen wie „STARBUCKS“ automatisch zusammengeführt.
- **"The Still":** nur **2** Einträge (`SCARD "the still"` = 2).
- **Teilsuche "The Sti":** 3 Namen – *the still*, *the stirling club spa*, *the stirling room*. „the still“ erscheint dabei **nur einmal**, obwohl zwei Betriebe dahinterstehen, weil die Autovervollständigung Namen und nicht Betriebe liefert.

### d) Details
Name → `SMEMBERS` → `MGET business:<id> …` (ein Roundtrip) → Ausgabe von Adresse und Sternen.

**"The Still":**

| business_id | Adresse | Sterne | Reviews | Kategorien |
|---|---|---|---|---|
| zQmHSe6IOiSNF84m9BVZ8A | 3400 S Las Vegas Blvd, 89109 Las Vegas, NV | 3.5 | 257 | Sports Bar, Diner, American |
| O9qdEZkdcIk5dxC8N00h4A | 270 14 Avenue SE, T2G 0K3 Calgary, AB | 2.5 | 8 | Bar, Lounge, American |

**Bewertung:** Hinter dem Namen „The Still“ stehen zwei völlig verschiedene Betriebe in zwei Ländern (USA und Kanada), die nichts miteinander zu tun haben – keine Kette und keine Dubletten. Die Autovervollständigung zeigt aber nur *einen* Eintrag „the still“, und erst die Detailabfrage offenbart zwei unterschiedliche Adressen mit deutlich abweichenden Bewertungen (3,5 Sterne bei 257 Reviews vs. 2,5 Sterne bei nur 8 Reviews).

Daraus folgt: Der Name ist **kein eindeutiger Identifikator**. Das Datenmodell „Name → Menge von IDs“ unterstellt, dass gleiche Namen zusammengehören. Bei Starbucks stimmt das (Filialen einer Kette), bei „The Still“ werden unabhängige Betriebe zusammengeworfen. Umgekehrt landen leicht abweichende Schreibweisen derselben Kette (z. B. „Starbucks Coffee“) oder Namen mit überzähligen Leerzeichen in getrennten Sets. „Anzahl Filialen = SCARD(name)“ ist daher nur eine Näherung. Für eine verlässliche Suche bräuchte man die Ortsangabe in der Ergebnisliste (z. B. „The Still – Las Vegas, NV“), eine Normalisierung der Namen (trimmen, Satzzeichen) und gegebenenfalls zusätzliche Indizes nach Stadt bzw. Bundesstaat.
