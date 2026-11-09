"""
Big Data – 1. Praktikum (HSBI, WS 2026/27)
Gemeinsame Funktionen für Aufgabe 2: Yelp-Business-Daten in Redis.

Datenmodell in Redis
--------------------
business:<business_id>   STRING  kompletter JSON-String des Betriebs        (Aufgabe 2a)
<name in lowercase>      SET     alle business_ids mit diesem Namen         (Aufgabe 2b)
autocomplete:names       ZSET    alle Namen (lowercase), Score 0             (Aufgabe 2c)
                                 -> Präfixsuche per ZRANGEBYLEX in O(log N + M)
"""
import json
import redis

BUSINESS_PREFIX = "business:"
AUTOCOMPLETE_KEY = "autocomplete:names"


def connect(host="localhost", port=6379, db=0):
    """Verbindung zum Redis-Server im Docker-Container (Port 6379 wird gemappt)."""
    r = redis.Redis(host=host, port=port, db=db, decode_responses=True)
    r.ping()  # wirft eine Exception, falls der Container nicht läuft
    return r


def iter_businesses(path):
    """Liest die Datei Zeile für Zeile (JSON Lines: ein Objekt pro Zeile).

    Gibt (rohe Zeile, geparstes dict) zurück. encoding='utf-8' ist unter
    Windows wichtig, sonst wird cp1252 verwendet und Umlaute/Sonderzeichen brechen.
    """
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield line, json.loads(line)


def load(r, path, batch_size=5000, flush=False, verbose=True):
    """Aufgabe 2a + 2b (+ Index für 2c): schreibt alle Einträge in Redis.

    Pipeline ohne Transaktion bündelt viele Befehle in einem Netzwerk-Roundtrip;
    das macht den Import der ~210k Datensätze um ein Vielfaches schneller.
    """
    if flush:
        r.flushdb()
    pipe = r.pipeline(transaction=False)
    count = 0
    for raw, obj in iter_businesses(path):
        bid = obj["business_id"]
        name = (obj.get("name") or "").lower()
        pipe.set(BUSINESS_PREFIX + bid, raw)          # 2a
        if name:
            pipe.sadd(name, bid)                       # 2b
            pipe.zadd(AUTOCOMPLETE_KEY, {name: 0})     # 2c-Index
        count += 1
        if count % batch_size == 0:
            pipe.execute()
            if verbose:
                print(f"  {count:>7} Datensätze importiert ...", flush=True)
    pipe.execute()
    if verbose:
        print(f"Fertig: {count} Datensätze importiert.")
    return count


def autocomplete(r, prefix, limit=None):
    """Aufgabe 2c: alle Namen, die mit `prefix` beginnen (case-insensitive).

    Alle Elemente des ZSET haben Score 0, daher sortiert Redis sie byteweise
    lexikografisch. '[abc' = inklusive 'abc'; als obere Schranke hängen wir das
    Byte 0xFF an. 0xFF kommt in gültigem UTF-8 nie vor, also ist 'abc'+0xFF größer
    als jeder String, der mit 'abc' beginnt – auch mit Umlauten, CJK oder Emojis.
    """
    p = prefix.lower()
    if not p:
        return []
    lo = ("[" + p).encode("utf-8")
    hi = lo + b"\xff"
    args = {}
    if limit:
        args = {"start": 0, "num": limit}
    return r.zrangebylex(AUTOCOMPLETE_KEY, lo, hi, **args)


def ids_for_name(r, name):
    """Menge der business_ids zu einem Namen (Aufgabe 2b)."""
    return r.smembers(name.lower())


def details(r, name):
    """Aufgabe 2d: Adressen und Sternebewertungen zu einem Namen."""
    result = []
    ids = sorted(ids_for_name(r, name))
    raws = r.mget([BUSINESS_PREFIX + i for i in ids]) if ids else []
    for bid, raw in zip(ids, raws):
        if raw is None:
            continue
        b = json.loads(raw)
        result.append({
            "business_id": bid,
            "name": b.get("name"),
            "address": b.get("address"),
            "city": b.get("city"),
            "state": b.get("state"),
            "postal_code": b.get("postal_code"),
            "stars": b.get("stars"),
            "review_count": b.get("review_count"),
            "is_open": b.get("is_open"),
            "categories": b.get("categories"),
        })
    return result


def format_details(rows):
    lines = []
    for i, d in enumerate(rows, 1):
        addr = ", ".join(x for x in [d["address"], d["postal_code"], d["city"], d["state"]] if x)
        status = "geöffnet" if d["is_open"] == 1 else "geschlossen"
        lines.append(f"  {i:>3}. {d['name']} | {addr or '(keine Adresse)'} | "
                     f"{d['stars']} Sterne ({d['review_count']} Reviews, {status}) | id={d['business_id']}")
    return "\n".join(lines)
