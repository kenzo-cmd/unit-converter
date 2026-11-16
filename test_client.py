"""Test program for the Unit Converter microservice.

It makes real HTTP requests to the running microservice, prints each request and the
data it receives back, and checks the responses.

1. Start the microservice in one terminal:   python app.py
2. Run this program in another terminal:     python test_client.py
"""
import sys

import requests

BASE = "http://localhost:5002"
results = []


def check(label, ok):
    results.append(ok)
    print(f"  -> {'PASS' if ok else 'FAIL'}: {label}")


def convert(title, body):
    print(f"\n{title}\n  request:  POST {BASE}/convert  {body}")
    response = requests.post(f"{BASE}/convert", json=body, timeout=5)
    print(f"  received: status {response.status_code}  {response.json()}")
    return response


try:
    print(f"\nGET {BASE}/units")
    response = requests.get(f"{BASE}/units", timeout=5)
    print(f"  received: status {response.status_code}  {response.json()}")
    check("lists weight, volume, distance and temperature",
          response.status_code == 200 and set(response.json()) == {"weight", "volume", "distance", "temperature"})

    r = convert("Convert 150 lb to kg", {"value": 150, "from": "lb", "to": "kg"})
    check("result is 68.04 kg", r.status_code == 200 and r.json() == {"result": 68.04, "unit": "kg"})

    r = convert("Convert 100 C to F", {"value": 100, "from": "c", "to": "f"})
    check("result is 212.0 f", r.status_code == 200 and r.json() == {"result": 212.0, "unit": "f"})

    r = convert("Error: missing the \"to\" field", {"value": 1, "from": "lb"})
    check("status 400 and the error names \"to\"", r.status_code == 400 and '"to"' in r.json()["error"])

    r = convert("Error: unsupported unit", {"value": 1, "from": "stone", "to": "kg"})
    check("status 400 and the error names the unit", r.status_code == 400 and "stone" in r.json()["error"])

    r = convert("Error: units of different types", {"value": 1, "from": "lb", "to": "ml"})
    check("status 400 and \"not compatible\"", r.status_code == 400 and "not compatible" in r.json()["error"])

    r = convert("Still working after the errors: 10 km to mi", {"value": 10, "from": "km", "to": "mi"})
    check("result is 6.21 mi", r.status_code == 200 and r.json() == {"result": 6.21, "unit": "mi"})
except requests.exceptions.ConnectionError:
    print(f"\nCould not reach {BASE}. Start the microservice first with: python app.py")
    sys.exit(1)

print(f"\n{sum(results)} of {len(results)} checks passed")
sys.exit(0 if all(results) else 1)
