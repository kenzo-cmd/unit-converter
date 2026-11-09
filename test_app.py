import unittest

from app import app

# 28 hand-calculated conversions: (value, from, to, expected)
CASES = [
    (150, "lb", "kg", 68.04), (100, "kg", "lb", 220.46), (1, "lb", "oz", 16.0),
    (1, "oz", "g", 28.35), (2500, "g", "kg", 2.5), (1.5, "kg", "g", 1500),
    (1, "cup", "ml", 236.59), (500, "ml", "cup", 2.11), (1, "tbsp", "tsp", 3.0),
    (1, "tsp", "ml", 4.93), (2, "l", "ml", 2000), (750, "ml", "l", 0.75),
    (8, "fl_oz", "ml", 236.59), (1, "cup", "fl_oz", 8.0), (1, "mi", "km", 1.61),
    (10, "km", "mi", 6.21), (10, "ft", "m", 3.05), (100, "m", "ft", 328.08),
    (5.5, "km", "m", 5500), (1, "mi", "ft", 5280),
    # temperature
    (100, "c", "f", 212.0), (32, "f", "c", 0.0), (0, "c", "k", 273.15),
    (300, "k", "c", 26.85), (98.6, "f", "c", 37.0), (-40, "c", "f", -40.0),
    (212, "f", "k", 373.15), (0, "k", "c", -273.15),
]


class ConverterTests(unittest.TestCase):
    def setUp(self):
        self.c = app.test_client()

    def post(self, body):
        return self.c.post("/convert", json=body)

    def test_hand_calculated_conversions(self):
        for value, src, dst, expected in CASES:
            r = self.post({"value": value, "from": src, "to": dst})
            self.assertEqual(r.status_code, 200, (value, src, dst))
            self.assertEqual(r.get_json(), {"result": expected, "unit": dst}, (value, src, dst))

    def test_same_unit_unchanged(self):
        self.assertEqual(self.post({"value": 1.234, "from": "kg", "to": "kg"}).get_json()["result"], 1.234)

    def test_units_endpoint(self):
        r = self.c.get("/units")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(sorted(r.get_json()), ["distance", "temperature", "volume", "weight"])

    def test_every_listed_unit_is_accepted(self):
        for units in self.c.get("/units").get_json().values():
            for u in units:
                self.assertEqual(self.post({"value": 1, "from": u, "to": u}).status_code, 200)

    def test_missing_fields_name_the_field(self):
        full = {"value": 1, "from": "lb", "to": "kg"}
        for field in full:
            body = {k: v for k, v in full.items() if k != field}
            r = self.post(body)
            self.assertEqual(r.status_code, 400)
            self.assertIn(f'"{field}"', r.get_json()["error"])

    def test_value_must_be_number(self):
        for bad in ("abc", "10", None, True, [1]):
            r = self.post({"value": bad, "from": "lb", "to": "kg"})
            self.assertEqual(r.status_code, 400)
            self.assertIn('"value"', r.get_json()["error"])

    def test_unsupported_unit_names_unit_and_lists_supported(self):
        r = self.post({"value": 1, "from": "stone", "to": "kg"})
        self.assertEqual(r.status_code, 400)
        msg = r.get_json()["error"]
        self.assertIn("stone", msg)
        self.assertIn("lb", msg)

    def test_incompatible_types(self):
        r = self.post({"value": 1, "from": "lb", "to": "ml"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("not compatible", r.get_json()["error"])

    def test_temperature_below_absolute_zero(self):
        for value, unit in ((-274, "c"), (-460, "f"), (-1, "k")):
            r = self.post({"value": value, "from": unit, "to": "c"})
            self.assertEqual(r.status_code, 400)
            self.assertIn("absolute zero", r.get_json()["error"])

    def test_temperature_not_compatible_with_other_types(self):
        r = self.post({"value": 20, "from": "c", "to": "kg"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("not compatible", r.get_json()["error"])

    def test_unit_names_not_case_sensitive(self):
        self.assertEqual(self.post({"value": 100, "from": "C", "to": "F"}).get_json()["result"], 212.0)

    def test_invalid_json_and_same_error_every_time(self):
        first = self.c.post("/convert", data="not json", content_type="application/json")
        second = self.c.post("/convert", data="not json", content_type="application/json")
        self.assertEqual(first.status_code, 400)
        self.assertEqual(first.get_json(), second.get_json())

    def test_keeps_working_after_errors(self):
        self.post({"value": "x"})
        self.c.get("/nope")
        r = self.post({"value": 150, "from": "lb", "to": "kg"})
        self.assertEqual(r.get_json(), {"result": 68.04, "unit": "kg"})

    def test_unknown_route_returns_json(self):
        r = self.c.get("/nope")
        self.assertEqual(r.status_code, 404)
        self.assertIn("error", r.get_json())


if __name__ == "__main__":
    unittest.main()