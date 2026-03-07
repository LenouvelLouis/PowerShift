# Wiki — Backend simulation

## Architecture générale

Le backend suit une architecture en couches stricte :

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

Chaque couche ne connaît que celle du dessous — jamais l'inverse.

---

## Flux complet d'une simulation

### 1. Requête HTTP

```
POST /api/v1/simulation/run
Content-Type: application/json

{
  "snapshot_hours": 24,
  "solver": "highs",
  "supply_ids": ["00000000-0000-0000-0000-000000000001",
                 "00000000-0000-0000-0000-000000000002"],
  "demand_ids": ["00000000-0000-0000-0000-000000000003",
                 "00000000-0000-0000-0000-000000000004"],
  "network_ids": ["00000000-0000-0000-0000-000000000005"]
}
```

| Champ | Description |
|---|---|
| `snapshot_hours` | Durée de la simulation (1–8760h) |
| `solver` | Solveur PyPSA (`"highs"` par défaut) |
| `supply_ids` | UUIDs des générateurs à inclure |
| `demand_ids` | UUIDs des charges à inclure |
| `network_ids` | UUIDs des composants réseau (transformateurs, câbles) |

---

### 2. Endpoint → Service (`simulation.py` → `SimulationService`)

`POST /api/v1/simulation/run` appelle `SimulationService.run(body)`.

Le service convertit le schéma HTTP en `SimulationRunInput` (objet domaine) et délègue au use case.

---

### 3. Use Case (`RunSimulationUseCase.execute`)

C'est ici que toute l'orchestration se passe, en 4 étapes séquentielles :

```
1. Persister la requête → génère un request_id en DB (table simulation_requests)
2. Charger les assets   → fetch supply/demand/network depuis la DB via leurs IDs
3. Lancer PyPSA         → exécution dans un ThreadPoolExecutor (non-bloquant)
4. Persister le résultat → sauvegarde dans simulation_results (lié au request_id)
```

Les assets manquants (IDs inconnus) sont ignorés silencieusement.

---

### 4. PyPSA (`PyPSANetworkBuilder` → `_DefaultPyPSASimulation`)

PyPSA est synchrone et CPU-bound. Il tourne dans un `ThreadPoolExecutor` pour ne pas bloquer la boucle asyncio.

Construction du réseau :

```
Network
  └── Bus "main_bus" (v_nom=380 kV)
        ├── Generator "North Sea Wind Farm"   (p_nom=500, marginal_cost=1.0)
        ├── Generator "Provence Solar Park"   (p_nom=200, marginal_cost=1.0)
        ├── Load      "Paris Residential"     (p_set=120)
        ├── Load      "EV Fleet"              (p_set=45)
        └── Transformer "MV/LV Transformer"
```

Chaque entité domaine expose `to_pypsa_params()` qui retourne les paramètres PyPSA.
PyPSA appelle ensuite `n.optimize(solver_name="highs")` pour minimiser le coût total.

---

### 5. Résultat

```json
{
  "id": "<simulation_result_id>",
  "request_id": "<simulation_request_id>",
  "status": "optimal",
  "total_supply_mwh": 3960.0,
  "total_demand_mwh": 3960.0,
  "balance_mwh": 0.0,
  "objective_value": 3960.0,
  "result_json": {
    "generators_t": {
      "North Sea Wind Farm": { "p": [0, 0, ..., 0] },
      "Provence Solar Park": { "p": [165, 165, ..., 165] }
    },
    "loads_t": {},
    "capacity_factors": {
      "North Sea Wind Farm": 0.0,
      "Provence Solar Park": 0.825
    },
    "violations": { "overloads": [], "overvoltages": [] },
    "objective_value": 3960.0
  },
  "created_at": "2026-03-07T10:00:00.000000"
}
```

| Champ | Description |
|---|---|
| `status` | `"optimal"` ou `"error"` |
| `total_supply_mwh` | Production réelle dispatché (somme post-optimisation) |
| `total_demand_mwh` | Consommation réelle (charges statiques × snapshot_hours) |
| `balance_mwh` | `supply - demand` (0 si réseau équilibré) |
| `objective_value` | Coût total en €/MWh (somme `p × marginal_cost`) |
| `generators_t` | Dispatch horaire de chaque générateur |
| `capacity_factors` | Taux d'utilisation par rapport à `p_nom` |

---

## Tables DB impliquées

```
simulation_requests        simulation_results
───────────────────        ──────────────────
id (PK)             ◄──── request_id (FK)
snapshot_hours             id (PK)
solver                     status
supply_ids (JSON)          total_supply_mwh
demand_ids (JSON)          total_demand_mwh
network_ids (JSON)         balance_mwh
pypsa_params (JSON)        objective_value
created_at                 result_json (JSON)
                           created_at
```

---

## Préparer la DB (seed)

```bash
# Depuis la racine du projet
python scripts/seed.py
```

Crée (de façon idempotente) :
- 2 supplies : `North Sea Wind Farm` (UUID ...001), `Provence Solar Park` (UUID ...002)
- 2 demands  : `Paris Residential Zone A` (UUID ...003), `EV Fleet` (UUID ...004)
- 2 network  : `MV/LV Transformer` (UUID ...005), `LV Cable` (UUID ...006)

---

## Curl complet

```bash
BASE="http://localhost:8000/api/v1"

# 1. Vérifier les assets disponibles
curl -s "$BASE/referential" | python3 -m json.tool

# 2. Lancer une simulation (avec les UUIDs du seed)
curl -s -X POST "$BASE/simulation/run" \
  -H "Content-Type: application/json" \
  -d '{
    "snapshot_hours": 24,
    "solver": "highs",
    "supply_ids": [
      "00000000-0000-0000-0000-000000000001",
      "00000000-0000-0000-0000-000000000002"
    ],
    "demand_ids": [
      "00000000-0000-0000-0000-000000000003",
      "00000000-0000-0000-0000-000000000004"
    ],
    "network_ids": [
      "00000000-0000-0000-0000-000000000005"
    ]
  }' | python3 -m json.tool

# 3. Lister toutes les simulations
curl -s "$BASE/simulation" | python3 -m json.tool

# 4. Récupérer une simulation par ID
curl -s "$BASE/simulation/<id>" | python3 -m json.tool
```

---

## Ajouter un nouveau type de supply/demand

1. Créer l'entité dans `app/domain/entities/supply/` (hériter de `BaseSupply`)
2. Implémenter `get_carrier()` et optionnellement surcharger `to_pypsa_params()`
3. Ajouter le mapping dans le repository (`supply_repository_impl.py`)
4. Mettre à jour le seed si nécessaire
