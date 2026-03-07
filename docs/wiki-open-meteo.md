# Open-Meteo — Integration and Load Profiles

## What is Open-Meteo?

[Open-Meteo](https://open-meteo.com) is a **free, no-API-key** weather API.
It provides hourly weather data (forecasts and historical) for any GPS coordinate.

In this project, it is used to fetch **hourly temperature** and derive
**realistic load profiles** for each electricity demand type.

---

## Raw Request

```
GET https://api.open-meteo.com/v1/forecast
  ?latitude=48.85
  &longitude=2.35
  &hourly=temperature_2m
  &forecast_days=1
  &timezone=Europe/Paris
```

### Parameters

| Parameter | Value | Description |
|---|---|---|
| `latitude` | `48.85` | Paris latitude (configurable) |
| `longitude` | `2.35` | Paris longitude |
| `hourly` | `temperature_2m` | Air temperature at 2m, one value per hour |
| `forecast_days` | `1` to `16` | Number of days to fetch |
| `timezone` | `Europe/Paris` | Timezone for timestamps |

### Response (excerpt)

```json
{
  "latitude": 48.85,
  "longitude": 2.35,
  "timezone": "Europe/Paris",
  "hourly": {
    "time": [
      "2026-03-07T00:00", "2026-03-07T01:00", "2026-03-07T02:00", "..."
    ],
    "temperature_2m": [
      4.2, 3.8, 3.5, 3.2, 3.0, 3.5,
      5.1, 7.3, 9.4, 11.2, 12.5, 13.1,
      13.8, 13.5, 12.9, 12.1, 10.8, 9.2,
      7.6, 6.8, 6.1, 5.5, 5.0, 4.6
    ]
  }
}
```

Only `hourly.temperature_2m` is used — a list of temperatures in degrees Celsius.

---

## How It Works in the Code

### 1. Trigger

On every `POST /api/v1/simulation/run`, `PyPSANetworkBuilder.run()` calls
`OpenMeteoLoadProfileProvider.get_profile()` for **each demand** before running PyPSA:

```
PyPSANetworkBuilder.run()  (async)
    │
    ├── get_profile("house", 24)            → [0.82, 0.78, 0.75, ...]
    ├── get_profile("electric_vehicle", 24) → [0.83, 0.93, 1.00, ...]
    │
    └── _DefaultPyPSASimulation.run_sync()  (thread)
            └── p_set = pd.Series([120*0.82, 120*0.78, ...], index=snapshots)
```

Profiles are fetched **asynchronously** before entering the thread executor,
because `httpx` is async while PyPSA is synchronous.

### 2. Temperature to Profile Conversion

#### House (residential)

```
P(t) = 0.30                          ← base load (appliances, lighting)
      + max(0, 18 - T) / 30          ← heating  (comfort threshold: 18 C)
      + max(0, T - 22) / 20          ← cooling  (AC threshold: 22 C)

Normalized: P(t) / max(P)  → values between 0.0 and 1.0
```

Example at T = 4 C:
```
heating = (18 - 4) / 30 = 0.47
cooling = 0
P = 0.30 + 0.47 = 0.77
```

Example at T = 30 C:
```
heating = 0
cooling = (30 - 22) / 20 = 0.40
P = 0.30 + 0.40 = 0.70
```

#### Electric Vehicle

Based on a **reference hourly profile** (overnight charging priority):

```
Hour:    0h    1h    2h    3h    4h    5h    6h    ...  22h   23h
Profile: 0.80  0.90  1.00  0.95  0.70  0.40  0.20  ...  0.80  0.85
```

Cold weather bonus: if T < 5 C, charging demand increases by up to +20%
(cold degrades battery range, requiring more frequent charging).

```
cold_bonus = max(0, (5 - T) / 20) x 0.20
P(t) = min(1.0, base_profile[hour] + cold_bonus)
```

### 3. Usage in PyPSA

The normalized profile is multiplied by `load_mw` to get the actual hourly power,
then passed to PyPSA as a `pandas.Series` aligned with the network snapshots:

```python
# In network_builder.py
profile = [0.82, 0.78, 0.75, ...]          # normalized (0.0 to 1.0)
p_set   = [120 * 0.82, 120 * 0.78, ...]   # in MW
pd.Series(p_set, index=n.snapshots)        # aligned to PyPSA snapshots
```

PyPSA stores this in `n.loads_t.p_set` (time-series) instead of `n.loads.p_set` (scalar),
which is why `loads_t` is now populated in the simulation result.

---

## Duration Handling (snapshot_hours)

| `snapshot_hours` | Behavior |
|---|---|
| <= 384 h (16 days) | `forecast_days = ceil(hours / 24)` — real forecast data |
| > 384 h | First 384 hours are tiled to fill the required length |

---

## Fallback

If Open-Meteo is unavailable (timeout, network error):

```python
temps = [15.0] * (forecast_days * 24)   # flat 15 C fallback
```

The simulation continues normally with a moderate, slightly shaped profile
based on the demand type models — no real weather data, but no crash.
