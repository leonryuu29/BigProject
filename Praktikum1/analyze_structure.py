"""
Aufgabe 2 (Vorarbeit): Struktur der Datei business.json / businessS.json analysieren.

Aufruf:  python analyze_structure.py data/businessS.json
"""
import json
import sys
from collections import Counter, defaultdict


def type_name(v):
    return "null" if v is None else type(v).__name__


def main(path):
    n = 0
    field_types = defaultdict(Counter)
    attr_keys = Counter()
    name_counts = Counter()
    first = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            first = first or obj
            n += 1
            for k, v in obj.items():
                field_types[k][type_name(v)] += 1
            if isinstance(obj.get("attributes"), dict):
                attr_keys.update(obj["attributes"].keys())
            name_counts[(obj.get("name") or "").lower()] += 1

    print(f"Datei: {path}")
    print("Format: JSON Lines (ein JSON-Objekt pro Zeile, KEIN JSON-Array)")
    print(f"Anzahl Datensätze: {n}\n")
    print("Felder und Typen:")
    for k, c in field_types.items():
        print(f"  {k:<14} {dict(c)}")
    print("\nHäufigste Attribut-Schlüssel (verschachteltes Objekt 'attributes'):")
    for k, c in attr_keys.most_common(10):
        print(f"  {k:<28} {c}")
    print(f"\nVerschiedene Namen (lowercase): {len(name_counts)}")
    print("Häufigste Namen:")
    for k, c in name_counts.most_common(10):
        print(f"  {c:>5}  {k}")
    print("\nErster Datensatz:")
    print(json.dumps(first, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/businessS.json")
