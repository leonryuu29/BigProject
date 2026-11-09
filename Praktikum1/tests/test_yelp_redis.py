"""
Automatisierte Tests für Aufgabe 2 (Big Data – 1. Praktikum).

Läuft gegen einen echten Redis-Server auf localhost:6379, benutzt aber eine
eigene Datenbank (db 15), damit die importierten Yelp-Daten in db 0 unberührt bleiben.

Aufruf (im Ordner Praktikum1):
    python -m unittest discover -s tests -v

Die Klasse RealDataTests prüft zusätzlich die Antworten auf echten Daten und wird
automatisch übersprungen, wenn data/business.json fehlt.
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import yelp_redis as yr  # noqa: E402

TEST_DB = 15
REAL_DATA = os.path.join(ROOT, "data", "business.json")
SYNTHETIC = os.path.join(HERE, "sample_synthetic.json")


def _rec(bid, name, **kw):
    d = {"business_id": bid, "name": name, "address": kw.get("address", "1 Main St"),
         "city": kw.get("city", "Phoenix"), "state": kw.get("state", "AZ"),
         "postal_code": kw.get("postal_code", "85000"), "latitude": 33.0, "longitude": -112.0,
         "stars": kw.get("stars", 4.0), "review_count": kw.get("review_count", 10),
         "is_open": kw.get("is_open", 1), "attributes": None, "categories": "Food", "hours": None}
    return json.dumps(d, ensure_ascii=False)


FIXTURE = [
    _rec("id-sb-1", "Starbucks", city="Phoenix", stars=3.5),
    _rec("id-sb-2", "Starbucks", city="Toronto", state="ON", stars=4.0),
    _rec("id-sb-3", "STARBUCKS", city="Las Vegas", state="NV", stars=3.0),
    _rec("id-sbc", "Starbucks Coffee"),
    _rec("id-star", "Star Pizza"),
    _rec("id-still-1", "The Still", address="3400 S Las Vegas Blvd", city="Las Vegas", state="NV",
         stars=3.5, review_count=257),
    _rec("id-still-2", "The Still", address="270 14 Avenue SE", city="Calgary", state="AB",
         stars=2.5, review_count=8),
    _rec("id-stir", "The Stirling Room"),
    _rec("id-cafe", "Café Müller"),
    _rec("id-cjk", "寿司 Sushi Bar"),
    _rec("id-vn", "Pho Ðắc Biệt"),
    _rec("id-zz", "Zzz Last Name"),
]


class FixtureTests(unittest.TestCase):
    """Funktionstests mit einem kleinen, bekannten Datensatz."""

    @classmethod
    def setUpClass(cls):
        cls.r = yr.connect(db=TEST_DB)
        cls.tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        cls.tmp.write("\n".join(FIXTURE) + "\n\n")  # Leerzeile am Ende muss ignoriert werden
        cls.tmp.close()
        cls.n = yr.load(cls.r, cls.tmp.name, flush=True, verbose=False, batch_size=3)

    @classmethod
    def tearDownClass(cls):
        cls.r.flushdb()
        os.unlink(cls.tmp.name)

    # --- Import / 2a ---------------------------------------------------------
    def test_01_import_count(self):
        """Alle Zeilen werden importiert, Leerzeilen ignoriert."""
        self.assertEqual(self.n, len(FIXTURE))

    def test_02_business_key_holds_original_json(self):
        """2a: business:<id> enthält den unveränderten JSON-String."""
        self.assertEqual(self.r.get("business:id-still-1"), FIXTURE[5])
        self.assertEqual(json.loads(self.r.get("business:id-cjk"))["name"], "寿司 Sushi Bar")

    def test_03_key_count(self):
        """Keys = Betriebe + verschiedene Namen + 1 Autocomplete-Index."""
        names = {json.loads(x)["name"].lower() for x in FIXTURE}
        self.assertEqual(self.r.dbsize(), len(FIXTURE) + len(names) + 1)

    # --- 2b -----------------------------------------------------------------
    def test_04_name_set_lowercase_and_merged(self):
        """2b: Name lowercase als Key; Groß-/Kleinschreibung wird zusammengeführt."""
        self.assertEqual(yr.ids_for_name(self.r, "Starbucks"), {"id-sb-1", "id-sb-2", "id-sb-3"})
        self.assertEqual(self.r.scard("starbucks"), 3)
        self.assertEqual(self.r.type("starbucks"), "set")

    def test_05_reimport_is_idempotent(self):
        """Erneuter Import ohne --flush erzeugt keine Duplikate (Set-Semantik)."""
        yr.load(self.r, self.tmp.name, verbose=False)
        self.assertEqual(self.r.scard("starbucks"), 3)
        self.assertEqual(self.r.zcard(yr.AUTOCOMPLETE_KEY), len({json.loads(x)["name"].lower() for x in FIXTURE}))

    # --- 2c -----------------------------------------------------------------
    def test_06_prefix_star(self):
        self.assertEqual(yr.autocomplete(self.r, "Star"),
                         ["star pizza", "starbucks", "starbucks coffee"])

    def test_07_prefix_case_insensitive(self):
        self.assertEqual(yr.autocomplete(self.r, "sTaRbUcKs"), ["starbucks", "starbucks coffee"])

    def test_08_prefix_the_sti(self):
        self.assertEqual(yr.autocomplete(self.r, "The Sti"), ["the still", "the stirling room"])

    def test_09_exact_name_is_included(self):
        self.assertIn("the still", yr.autocomplete(self.r, "the still"))

    def test_10_no_match(self):
        self.assertEqual(yr.autocomplete(self.r, "xyz-gibt-es-nicht"), [])

    def test_11_empty_prefix(self):
        self.assertEqual(yr.autocomplete(self.r, ""), [])

    def test_12_limit(self):
        self.assertEqual(yr.autocomplete(self.r, "s", limit=2), ["star pizza", "starbucks"])

    def test_13_unicode_prefixes(self):
        """Umlaute, CJK und vietnamesische Zeichen werden korrekt gefunden."""
        self.assertEqual(yr.autocomplete(self.r, "Café M"), ["café müller"])
        self.assertEqual(yr.autocomplete(self.r, "寿"), ["寿司 sushi bar"])
        self.assertEqual(yr.autocomplete(self.r, "pho ð"), ["pho ðắc biệt"])

    def test_14_no_false_positive_after_prefix(self):
        """'starbucks' darf nicht 'star pizza' liefern, 'zzz' nur sich selbst."""
        self.assertNotIn("star pizza", yr.autocomplete(self.r, "starbucks"))
        self.assertEqual(yr.autocomplete(self.r, "zzz"), ["zzz last name"])

    # --- 2d -----------------------------------------------------------------
    def test_15_details_the_still(self):
        rows = yr.details(self.r, "The Still")
        self.assertEqual(len(rows), 2)
        by_city = {d["city"]: d for d in rows}
        self.assertEqual(by_city["Las Vegas"]["address"], "3400 S Las Vegas Blvd")
        self.assertEqual(by_city["Las Vegas"]["stars"], 3.5)
        self.assertEqual(by_city["Calgary"]["stars"], 2.5)

    def test_16_details_unknown_name(self):
        self.assertEqual(yr.details(self.r, "gibt es nicht"), [])

    def test_17_format_details(self):
        text = yr.format_details(yr.details(self.r, "The Still"))
        self.assertIn("Calgary", text)
        self.assertIn("3.5 Sterne", text)


@unittest.skipUnless(os.path.exists(SYNTHETIC), "tests/sample_synthetic.json fehlt")
class SyntheticFileTests(unittest.TestCase):
    """Import einer größeren Datei im echten Yelp-Format (200 Datensätze, Unicode)."""

    def test_synthetic_file(self):
        r = yr.connect(db=TEST_DB)
        try:
            n = yr.load(r, SYNTHETIC, flush=True, verbose=False)
            self.assertEqual(n, 200)
            self.assertEqual(r.scard("starbucks"), 5)          # inkl. "STARBUCKS"
            self.assertEqual(yr.autocomplete(r, "the sti"),
                             ["the sticky rice", "the still", "the stillery"])
        finally:
            r.flushdb()


@unittest.skipUnless(os.path.exists(REAL_DATA), "data/business.json fehlt")
class RealDataTests(unittest.TestCase):
    """Prüft die Antworten aus answers.py auf dem echten Datensatz (192.609 Einträge)."""

    @classmethod
    def setUpClass(cls):
        cls.r = yr.connect(db=TEST_DB)
        cls.n = yr.load(cls.r, REAL_DATA, flush=True, verbose=False)

    @classmethod
    def tearDownClass(cls):
        cls.r.flushdb()

    def test_record_count(self):
        self.assertEqual(self.n, 192609)

    def test_distinct_names(self):
        self.assertEqual(self.r.zcard(yr.AUTOCOMPLETE_KEY), 144337)

    def test_starbucks(self):
        self.assertEqual(self.r.scard("starbucks"), 1066)
        total = sum(self.r.scard(n) for n in yr.autocomplete(self.r, "starbucks"))
        self.assertEqual(total, 1073)

    def test_star_prefix(self):
        self.assertEqual(len(yr.autocomplete(self.r, "Star")), 181)

    def test_the_still(self):
        self.assertEqual(self.r.scard("the still"), 2)
        self.assertEqual(yr.autocomplete(self.r, "The Sti"),
                         ["the still", "the stirling club spa", "the stirling room"])
        cities = sorted(d["city"] for d in yr.details(self.r, "The Still"))
        self.assertEqual(cities, ["Calgary", "Las Vegas"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
