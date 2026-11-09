"""
Aufgabe 2a + 2b: business.json in die lokale Redis-Instanz schreiben.

Aufruf:
  python load_data.py data/businessS.json --flush      # Test mit 200 Datensätzen
  python load_data.py data/business.json  --flush      # kompletter Import
"""
import argparse
import time

import yelp_redis as yr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?", default="data/business.json")
    ap.add_argument("--flush", action="store_true", help="Datenbank vorher leeren")
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=6379)
    args = ap.parse_args()

    r = yr.connect(args.host, args.port)
    t0 = time.time()
    n = yr.load(r, args.file, flush=args.flush)
    dt = time.time() - t0
    print(f"Dauer: {dt:.1f} s  ({n / max(dt, 1e-9):.0f} Datensätze/s)")
    print(f"Keys in Redis: {r.dbsize()}")
    print(f"Verschiedene Namen im Autocomplete-Index: {r.zcard(yr.AUTOCOMPLETE_KEY)}")


if __name__ == "__main__":
    main()
