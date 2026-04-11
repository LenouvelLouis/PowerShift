# Wiki — Backend Simulation

## General Architecture

The backend follows a strict layered architecture:

```
     HTTP Request
         │
         ▼
┌─────────────────────┐
│   API (FastAPI)     │  endpoints/, schemas/
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   Application       │  services/, use_cases/
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   Domain            │  entities/, interfaces/
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   Infrastructure    │  db/repositories/, simulation/
└─────────────────────┘
```

Each layer only knows the one below — never the reverse.

---

## Full Simulation Flow

### 1. HTTP Request

```
POST /api/v1/simulation/run
Content-Type: application/json

{
  "snapshot_hours": 24,
  "solver": "highs",
  "start_date": "2025-06-01",
  "end_date": "2025-06-01",
  "supply_ids": ["<uuid>", "<uuid>"],
  "demand_ids": ["<uuid>"],
  "network_ids": [],
  "pypsa_params": {},
  "hourly_load_overrides": {}
}
```

| Field | Description |
|---|---|
| `snapshot_hours` | Simulation duration (1–8760 h). Must match `(end_date - start_date + 1) * 24`. |
| `solver` | PyPSA solver — `"highs"` (default, recommended) |
| `start_date` / `end_date` | Date range for weather profiles. If omitted, auto-derived from today mapped to 2025. |
| `supply_ids` | UUIDs of generators/batteries to include |
| `demand_ids` | UUIDs of loads to include |
| `network_ids` | UUIDs of network components (transformers, cables) |
| `pypsa_params` | Per-asset PyPSA parameter overrides (keyed by asset name) |
| `hourly_load_overrides` | Per-demand hourly profile overrides (keyed by demand UUID, length must equal `snapshot_hours`) |

---

### 2. Endpoint → Service (`simulation.py` → `SimulationService`)

`POST /api/v1/simulation/run` calls `SimulationService.run(body)`.

The service converts the HTTP schema into a `SimulationRunInput` domain object and delegates to the use case.

---

### 3. Use Case (`RunSimulationUseCase.execute`)

All orchestration happens here in 4 sequential steps:

```
1. Persist the request  → generates a request_id in DB (table simulation_requests)
2. Load assets          → fetch supply/demand/network from DB via their IDs
3. Run PyPSA            → execution inside a ThreadPoolExecutor (non-blocking)
4. Persist the result   → saves into simulation_results (linked to request_id)
```

Unknown IDs are silently ignored.

---

### 4. Pre-simulation — Weather & Load Profiles (async)

Before entering the thread executor, `PyPSANetworkBuilder.run()` fetches all profiles asynchronously:

```
PyPSANetworkBuilder.run()  (async)
    │
    ├── load_profile_provider.get_profile("house", 24, start_date)
    │       → [0.82, 0.78, 0.75, ...]  (normalized 0–1)
    │
    ├── pv_profile_repo.get_solar_profile(start_date, end_date)
    │       → [0.0, 0.0, 0.12, 0.45, ...]  (capacity factors from KNMI DB)
    │
    ├── pv_profile_repo.get_wind_profile(start_date, end_date)
    │       → [0.62, 0.58, 0.71, ...] (capacity factors from KNMI DB)
    │
    └── nuclear_repo.get_reactor(supply_id)
            → NuclearConstraintsBuilder.build_pypsa_params(reactor)
```

Profile warnings are appended to `result_json["warnings"]` if solar or wind data is all-zero for the requested date range.

---

### 5. PyPSA — Linear Optimal Power Flow (LOPF)

PyPSA is synchronous and CPU-bound. It runs inside a `ThreadPoolExecutor` (max 2 workers) to avoid blocking the async event loop.

#### Network construction

```
Network (n.optimize = LOPF)
  └── Bus "main_bus" (v_nom=380 kV)
        ├── Generator   "Solar Farm"       (p_nom=200, p_max_pu=[0.0, 0.12, ...], marginal_cost≈0)
        ├── Generator   "Wind Farm"        (p_nom=500, p_max_pu=[0.62, 0.58, ...], marginal_cost≈0)
        ├── Generator   "Gas Plant"        (p_nom=300, p_max_pu=1.0, marginal_cost=80)
        ├── StorageUnit "Battery"          (p_nom=100, max_hours=4, efficiency=0.95)
        ├── Load        "Residential"      (p_set=pd.Series([98.4, 93.6, ...]))
        └── Generator   "__grid_import__"  (p_nom=1e9, marginal_cost=500)  ← backstop
```

#### Dispatch strategy (merit order via marginal costs)

1. **Renewables** (solar/wind) — `p_max_pu` from KNMI weather profiles, `marginal_cost ≈ 0`
2. **Conventional generators** — `p_max_pu = 1.0`, `marginal_cost` by type
3. **Battery StorageUnits** — temporally coupled; absorb surplus, fill deficit; `marginal_cost = 0`
4. **`__grid_import__` backstop** (1 GW, 500 €/MWh) — dispatched only when local resources exhausted, keeps LOPF always feasible

#### Battery StorageUnit parameters

| PyPSA parameter | Value |
|---|---|
| `p_nom` | `capacity_mw` (rated charge/discharge power) |
| `max_hours` | `4.0` default — energy capacity = `capacity_mw × max_hours` |
| `efficiency_store` | `efficiency` field (one-way, e.g. 0.95) |
| `efficiency_dispatch` | same as `efficiency_store` |
| `cyclic_state_of_charge` | `True` — SOC at end of period = SOC at start |
| `marginal_cost` | `0.0` |

#### Curtailment calculation

Curtailment = renewable energy available (from weather profiles) but not dispatched by LOPF.

```python
curtailed_mwh = 0
for gen_name, available_mwh in renewable_available_mwh.items():
    actual_mwh = n.generators_t.p[gen_name].sum()
    curtailed_mwh += max(0, available_mwh - actual_mwh)
```

`renewable_available_mwh` is pre-computed before `n.optimize()` (since `generators_t.p_max_pu` may be empty post-optimization).

Curtailment is stored in `result_json.grid_exchange.total_export_mwh`.

---

### 6. Result

```json
{
  "id": "<simulation_result_id>",
  "request_id": "<simulation_request_id>",
  "status": "optimized",
  "solver": "highs",
  "name": null,
  "start_date": "2025-06-01",
  "end_date": "2025-06-01",
  "total_supply_mwh": 3960.0,
  "total_demand_mwh": 3960.0,
  "balance_mwh": 0.0,
  "objective_value": 3960.0,
  "result_json": {
    "generators_t": {
      "Solar Farm": { "p": [0.0, 0.0, 24.0, 80.0, ...] }
    },
    "storage_units_t": {
      "Battery": {
        "p": [-20.0, -20.0, 40.0, ...],
        "state_of_charge": [80.0, 100.0, 60.0, ...]
      }
    },
    "loads_t": {
      "Residential": { "p": [98.4, 93.6, ...] }
    },
    "capacity_factors": {
      "Solar Farm": 0.23
    },
    "convergence": {
      "all_converged": true,
      "converged_count": 24,
      "total_snapshots": 24,
      "non_converged_snapshots": []
    },
    "grid_exchange": {
      "import_export_mw": [0.0, 0.0, ...],
      "total_import_mwh": 0.0,
      "total_export_mwh": 12.5
    },
    "violations": { "overloads": [], "overvoltages": [] },
    "warnings": []
  },
  "created_at": "2026-04-11T10:00:00.000000"
}
```

#### Top-level fields

| Field | Description |
|---|---|
| `status` | `"optimized"` (LOPF converged), `"converged"` (legacy), `"error"` |
| `total_supply_mwh` | Local generator dispatch only — excludes `__grid_import__` backstop |
| `total_demand_mwh` | Actual load consumption over all snapshots |
| `balance_mwh` | `supply - demand` (near 0 when balanced) |
| `objective_value` | Total cost in €/MWh (`Σ p × marginal_cost`) |

#### `result_json` fields

| Field | Description |
|---|---|
| `generators_t[name].p` | Hourly dispatch per generator (MW) |
| `storage_units_t[name].p` | Hourly charge (negative) / discharge (positive) per battery (MW) |
| `storage_units_t[name].state_of_charge` | Hourly state of charge per battery (MWh) |
| `loads_t[name].p` | Hourly consumption per load (MW) |
| `capacity_factors[name]` | Actual dispatch / (p_nom × hours) |
| `convergence.all_converged` | Always `true` for LOPF |
| `grid_exchange.total_import_mwh` | Energy from backstop grid (0 if local resources sufficient) |
| `grid_exchange.total_export_mwh` | Curtailed renewable energy (MWh available but not dispatched) |
| `warnings` | Profile warnings (e.g. missing solar/wind data for date range) |

---

## Frontend KPI Cards

The results page shows 4 KPI cards:

| Card | Value | Color |
|---|---|---|
| **Status** | `Optimised` / `Converged` / `Non-conv.` / `Error` | Green if optimized/converged, red if error, amber otherwise |
| **Balance** | `balance_mwh` MWh | Green if ≈ 0, blue if positive (surplus), red if negative (deficit) |
| **Supply** | `total_supply_mwh` MWh | Green |
| **Demand** | `total_demand_mwh` MWh | Red |

The **Simulation Summary** panel also shows:
- **Grid Import** (`grid_exchange.total_import_mwh`) — blue — backstop energy used
- **Curtailed** (`grid_exchange.total_export_mwh`) — violet — renewable energy wasted

---

## DB Tables

```
simulation_requests          simulation_results
───────────────────          ──────────────────
id (PK)               ◄──── request_id (FK)
snapshot_hours               id (PK)
solver                       status
name                         total_supply_mwh
start_date                   total_demand_mwh
end_date                     balance_mwh
supply_ids (JSON)            objective_value
demand_ids (JSON)            result_json (JSON)
network_ids (JSON)           created_at
pypsa_params (JSON)
created_at
```

---

## Supply Types

| Type | PyPSA component | `get_carrier()` | Notes |
|---|---|---|---|
| Solar PV | `Generator` | `"solar"` | `p_max_pu` from KNMI irradiance profile |
| Wind | `Generator` | `"wind"` | `p_max_pu` from KNMI wind speed profile |
| Nuclear | `Generator` | `"nuclear"` | Min-stable-power + maintenance constraints applied |
| Gas / conventional | `Generator` | `"gas"` etc. | `p_max_pu = 1.0` |
| Battery storage | `StorageUnit` | `"battery"` | Temporally coupled, cyclic SOC |

---

## Adding a New Supply Type

1. Create the entity in `app/domain/entities/supply/` (inherit from `BaseSupply`)
2. Implement `get_carrier()` and override `to_pypsa_params()` if needed
3. Add the mapping in `supply_repository_impl.py`
4. Add the mapping in `supply.py` `_TYPE_MAP`
5. If it uses a `StorageUnit` (like battery), add an `isinstance` check in `network_builder.py` to call `n.add("StorageUnit", ...)` instead of `n.add("Generator", ...)`

---

## Full curl Example

```bash
BASE="http://localhost:8000/api/v1"

# List available assets
curl -s "$BASE/referential" | python3 -m json.tool

# Run a 24-hour simulation
curl -s -X POST "$BASE/simulation/run" \
  -H "Content-Type: application/json" \
  -d '{
    "snapshot_hours": 24,
    "solver": "highs",
    "start_date": "2025-06-01",
    "end_date": "2025-06-01",
    "supply_ids": ["<supply-uuid>"],
    "demand_ids": ["<demand-uuid>"]
  }' | python3 -m json.tool

# List all simulations
curl -s "$BASE/simulation" | python3 -m json.tool

# Get simulation by ID
curl -s "$BASE/simulation/<id>" | python3 -m json.tool
```
