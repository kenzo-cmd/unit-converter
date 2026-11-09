"""Unit Converter microservice (REST API, JSON in / JSON out).

POST /convert  {"value": 150, "from": "lb", "to": "kg"} -> {"result": 68.04, "unit": "kg"}
GET  /units    -> {"weight": [...], "volume": [...], "distance": [...], "temperature": [...]}
Errors         -> status 400 and {"error": "..."}
"""
import math
import os

from flask import Flask, jsonify, request

app = Flask(__name__)

# Each unit is stored as its size in the base unit of its type (g, ml, m).
UNITS = {
    "weight": {"g": 1, "kg": 1000, "oz": 28.349523125, "lb": 453.59237},
    "volume": {"ml": 1, "l": 1000, "tsp": 4.92892159375, "tbsp": 14.78676478125,
               "cup": 236.5882365, "fl_oz": 29.5735295625},
    "distance": {"m": 1, "km": 1000, "ft": 0.3048, "mi": 1609.344},
}
# Temperature is not a simple ratio (offsets), so each unit has (to_celsius, from_celsius).
TEMPERATURE = {
    "c": (lambda x: x, lambda c: c),
    "f": (lambda x: (x - 32) * 5 / 9, lambda c: c * 9 / 5 + 32),
    "k": (lambda x: x - 273.15, lambda c: c + 273.15),
}
ALL_UNITS = {**UNITS, "temperature": TEMPERATURE}
UNIT_TYPE = {u: t for t, units in ALL_UNITS.items() for u in units}
SUPPORTED = ", ".join(UNIT_TYPE)


def error(message, status=400):
    return jsonify({"error": message}), status


def read_request():
    """Return (value, from_unit, to_unit) or raise ValueError with a clear message."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError('Request body must be a JSON object with "value", "from" and "to".')
    for field in ("value", "from", "to"):
        if field not in data:
            raise ValueError(f'Missing required field "{field}".')
    value = data["value"]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('Field "value" must be a number.')
    units = []
    for field in ("from", "to"):
        unit = str(data[field]).strip().lower()
        if unit not in UNIT_TYPE:
            raise ValueError(f'Unsupported unit "{data[field]}" in field "{field}". Supported units: {SUPPORTED}.')
        units.append(unit)
    return value, units[0], units[1]


@app.post("/convert")
def convert():
    try:
        value, src, dst = read_request()
    except ValueError as e:
        return error(str(e))
    if UNIT_TYPE[src] != UNIT_TYPE[dst]:
        return error(f'Units are not compatible: "{src}" is {UNIT_TYPE[src]} but "{dst}" is {UNIT_TYPE[dst]}.')
    kind = UNIT_TYPE[src]
    if kind == "temperature":
        celsius = TEMPERATURE[src][0](value)
        if celsius < -273.15 - 1e-9:
            return error(f'Temperature {value} {src} is below absolute zero.')
        result = TEMPERATURE[dst][1](celsius)
    else:
        table = UNITS[kind]
        result = value * table[src] / table[dst]
    if src == dst:
        return jsonify({"result": value, "unit": dst})
    return jsonify({"result": round(result, 2), "unit": dst})


@app.get("/units")
def units():
    return jsonify({t: list(u) for t, u in ALL_UNITS.items()})


@app.after_request
def allow_browser_calls(resp):
    # Lets a web page (such as LiftLog) call this service from the browser.
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


@app.errorhandler(404)
def not_found(_):
    return error("Not found. Use POST /convert or GET /units.", 404)


@app.errorhandler(405)
def bad_method(_):
    return error("Method not allowed for this endpoint.", 405)


@app.errorhandler(Exception)
def unexpected(_):
    return error("Unexpected server error.", 500)


if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 5002)))