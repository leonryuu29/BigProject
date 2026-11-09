"""
Aufgabe 2c + 2d: Autovervollständigung mit einfacher input()-Schleife.

Ablauf:
  1. Präfix eingeben (z. B. "Star")  -> alle passenden Namen mit Anzahl Filialen
  2. Nummer eingeben                  -> Adressen + Sterne der Betriebe (2d)
  Leere Eingabe beendet die jeweilige Ebene.

Aufruf:  python autocomplete.py
"""
import yelp_redis as yr

MAX_SHOW = 50


def main():
    r = yr.connect()
    print("Autovervollständigung (leere Eingabe = Ende)")
    while True:
        prefix = input("\nSuche> ").strip()
        if not prefix:
            break
        names = yr.autocomplete(r, prefix)
        if not names:
            print("  keine Treffer")
            continue
        pipe = r.pipeline(transaction=False)
        for n in names:
            pipe.scard(n)
        counts = pipe.execute()
        print(f"  {len(names)} Namen beginnen mit '{prefix}':")
        for i, (n, c) in enumerate(zip(names[:MAX_SHOW], counts), 1):
            print(f"  {i:>3}. {n}  ({c} Eintrag/Einträge)")
        if len(names) > MAX_SHOW:
            print(f"  ... und {len(names) - MAX_SHOW} weitere (Präfix verfeinern)")

        choice = input("Nummer für Details (Enter = neue Suche)> ").strip()
        if choice.isdigit() and 1 <= int(choice) <= min(len(names), MAX_SHOW):
            name = names[int(choice) - 1]
            rows = yr.details(r, name)
            print(f"\n'{name}': {len(rows)} Betrieb(e)")
            print(yr.format_details(rows))


if __name__ == "__main__":
    main()
