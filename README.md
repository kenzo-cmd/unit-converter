# Unit Converter Microservice

A small REST API that converts a number between units of weight, volume and distance.

**Supported units:** weight `g, kg, oz, lb` · volume `ml, l, tsp, tbsp, cup, fl_oz` (US) · distance `m, km, ft, mi` · temperature `c, f, k` (Celsius, Fahrenheit, Kelvin)

## Run it

```
pip install -r requirements.txt
python app.py
```
It listens on http://localhost:5002 (set the `PORT` environment variable to change this).

## Request data

`POST /convert` with a JSON body (Content-Type: application/json):

| Field | Type | Meaning |
|---|---|---|
| value | number | the number to convert |
| from | string | unit to convert from, e.g. "lb" |
| to | string | unit to convert to, e.g. "kg" |

`GET /units` returns the supported units grouped by type. It needs no parameters.

```python
import requests
response = requests.post("http://localhost:5002/convert", json={"value": 150, "from": "lb", "to": "kg"})
```

## Receive data

- **Success:** status 200 and JSON, e.g. `{"result": 68.04, "unit": "kg"}`. Results are rounded to 2 decimals; converting a unit to itself returns the value unchanged.
- **Failure:** status 400 and JSON `{"error": "..."}` naming the problem field or unit (missing field, non-number value, unsupported unit, incompatible types such as lb to ml, or a temperature below absolute zero).

```python
if response.status_code == 200:
    data = response.json()
    print(data["result"], data["unit"])
else:
    print("Unit converter failure:", response.json()["error"])
```

## Test it

```
python -m unittest -v
```
