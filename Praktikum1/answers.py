"""
Beantwortet die konkreten Fragen aus Aufgabe 2c/2d automatisch
(nach dem Import mit load_data.py ausführen).

Aufruf:  python answers.py
"""
import yelp_redis as yr


def section(title):
    print("\n" + "=" * 70 + f"\n{title}\n" + "=" * 70)


def main():
    r = yr.connect()
    print(f"Keys in Redis: {r.dbsize()}, Namen im Index: {r.zcard(yr.AUTOCOMPLETE_KEY)}")

    section('2c) Präfix "Star" (erste 20 Treffer)')
    star = yr.autocomplete(r, "Star")
    print(f"{len(star)} Namen beginnen mit 'star':")
    for n in star[:20]:
        print("  ", n)

    section("2c) Wie viele Starbucks-Filialen?")
    exact = r.scard("starbucks")
    print(f"Exakter Name 'starbucks': {exact} Einträge")
    variants = yr.autocomplete(r, "starbucks")
    total = 0
    for n in variants:
        c = r.scard(n)
        total += c
        print(f"   {c:>5}  {n}")
    print(f"Alle Namen, die mit 'starbucks' beginnen: {total} Einträge")

    section('2c) "The Still" und Teilsuche "The Sti"')
    print(f"Exakter Name 'the still': {r.scard('the still')} Eintrag/Einträge")
    sti = yr.autocomplete(r, "The Sti")
    print(f"Teilsuche 'The Sti' liefert {len(sti)} Namen:")
    for n in sti:
        print(f"   {r.scard(n):>3}  {n}")

    section('2d) Details zu "The Still"')
    rows = yr.details(r, "The Still")
    print(yr.format_details(rows) or "  (keine Einträge)")


if __name__ == "__main__":
    main()
