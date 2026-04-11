# Wiki — Frontend

**Stack:** Nuxt 4, Vue 3, TypeScript, Tailwind CSS v4, @nuxt/ui, Pinia, TanStack Query (via `$fetch`)

---

## Directory Structure

```
energy-dashboard/
└── app/
    ├── pages/
    │   └── index.vue              # Single page — the entire app
    ├── components/
    │   ├── features/
    │   │   ├── header/            # Top bar (run controls, solver picker, save)
    │   │   ├── sidebar/           # Asset selection and configuration
    │   │   ├── results/           # KPI cards, charts, summary panels
    │   │   └── scenario/          # Scenario import/export
    │   ├── charts/                # ECharts-based chart components
    │   ├── network-canvas/        # SVG network topology canvas
    │   ├── NetworkCanvas.vue      # Main canvas wrapper
    │   ├── KpiCard.vue            # Reusable KPI card
    │   └── OnboardingTutorial.vue # First-run walkthrough
    ├── composables/
    │   ├── api.ts                 # All typed $fetch wrappers + TypeScript types
    │   ├── useLiveRunner.ts       # Live simulation preview debounce logic
    │   ├── useScenarioIO.ts       # Scenario import/export (JSON files)
    │   ├── useSimulationUrl.ts    # URL-based scenario sharing
    │   ├── useSolverAvailability.ts
    │   ├── useTimeLabels.ts
    │   ├── useAssetColors.ts
    │   └── useEChartsTheme.ts
    ├── stores/
    │   ├── simulation.ts          # Main store — selection, run, overrides
    │   ├── referential.ts         # Available assets from backend
    │   └── history.ts             # Past simulation results
    └── layouts/
```

---

## API Layer (`composables/api.ts`)

All backend calls go through `$fetch` wrappers defined in `api.ts`. No raw `fetch` anywhere else.

### Key types

```typescript
// Assets
Supply, Demand, NetworkComponent, Referential

// Simulation
SimulationRunRequest   // payload sent to POST /api/v1/simulation/run
SimulationResult       // full result with result_json
SimulationListItem     // lightweight list entry (no result_json)
SimulationResultJson   // typed structure of result_json
```

### Key functions

```typescript
fetchReferential()                         // GET /api/v1/referential
fetchSupplies() / createSupply() / ...     // CRUD supplies
fetchDemands() / createDemand() / ...      // CRUD demands

saveSimulation(params)                     // POST /api/v1/simulation/save — runs + persists
previewSimulation(params)                  // POST /api/v1/simulation/preview — runs, no DB write

fetchSimulations()                         // GET /api/v1/simulation (list)
fetchSimulationById(id)                    // GET /api/v1/simulation/:id
renameSimulation(id, name)                 // PATCH /api/v1/simulation/:id/rename
deleteSimulation(id)                       // DELETE /api/v1/simulation/:id
fetchScenarioExport(id)                    // GET /api/v1/simulation/:id/export
fetchSimulationSolvers()                   // GET /api/v1/simulation/solvers
```

### Base URL

Configured via `NUXT_API_BASE_URL` — proxied through Nuxt server routes so the frontend never calls the backend directly from the browser (avoids CORS issues).

---

## Pinia Stores

### `useReferentialStore` (`stores/referential.ts`)

Loads and caches all available assets from the backend.

| State | Type | Description |
|---|---|---|
| `availableSupplies` | `Supply[]` | All supplies from DB |
| `availableDemands` | `Demand[]` | All demands from DB |
| `availableNetwork` | `NetworkComponent[]` | All network components from DB |
| `backendAvailable` | `boolean \| null` | `null` = not checked, `false` = unreachable |

Call `loadReferential()` once on app mount. Also exposes CRUD actions (`addSupply`, `editSupply`, `removeSupply`, etc.).

---

### `useSimulationStore` (`stores/simulation.ts`)

Central store — manages asset selection, simulation parameters, and run state.

#### Selection state

```typescript
selectedSupplyIds   // computed from _supplyEntries
selectedDemandIds
selectedNetworkIds
selectedSupplies    // full Supply objects for selected IDs
selectedDemands
selectedNetwork
```

#### Simulation parameters

| State | Default | Description |
|---|---|---|
| `snapshotHours` | `24` | Auto-updated from date range if set |
| `solver` | `"highs"` | PyPSA solver |
| `startDate` / `endDate` | `""` | ISO date strings; drive `snapshotHours` via `watch` |
| `optimizationObjective` | `"min_cost"` | `min_cost` / `min_emissions` / `max_renewable` |
| `scenarioName` | `""` | Optional name for saved simulation |

#### Asset overrides

Each selected asset can have field-level overrides (e.g. override `capacity_mw` for a run without editing the asset in DB):

```typescript
getOverrides(type, id)              // → Record<string, number>
setOverride(type, id, field, value) // set one field
clearOverrides(type, id)            // reset all overrides
hasOverrides(type, id)              // → boolean
```

Overrides are sent as `asset_overrides` in the simulation payload.

#### Key actions

```typescript
runFullSimulation()    // POST save + updates historyStore
buildPayload()         // builds SimulationRunRequest from current state
clearScenario()        // reset all selection and parameters
loadFromScenario(s)    // restore state from a ScenarioExport object
```

#### Displayed result

```typescript
displayedResult   // computed: currentLiveResult ?? historyStore.currentResult
```

Live preview results take priority over history results.

---

### `useHistoryStore` (`stores/history.ts`)

Manages past simulation results.

| State | Description |
|---|---|
| `simulationHistory` | `SimulationListItem[]` — list of all saved simulations |
| `currentResult` | `SimulationResult \| null` — full result being viewed |
| `selectedSimulationId` | currently selected history entry ID |

Actions: `loadHistory()`, `loadSimulationById(id)`, `deleteEntry(id)`, `renameEntry(id, name)`.

---

## Key Composables

### `useLiveRunner`

Debounced live preview — watches `simulationStore` state and auto-triggers `previewSimulation()` when the selection changes. Writes to `simulationStore.currentLiveResult`.

### `useSimulationUrl`

Encodes/decodes the current scenario into the URL query string, enabling shareable simulation links. Decodes on mount to restore state from URL.

### `useScenarioIO`

Import/export simulation scenarios as JSON files:
- **Export**: calls `fetchScenarioExport(id)` → downloads JSON
- **Import**: reads JSON file → calls `simulationStore.loadFromScenario()`

### `useTimeLabels`

Generates human-readable time axis labels from snapshot index (e.g. `"00:00"`, `"Mon 06:00"`, `"Jan 01"`).

### `useAssetColors`

Returns consistent colors per asset name/carrier — used across all charts.

---

## Component Architecture

### Single page (`pages/index.vue`)

The entire app is a single page. Layout:

```
┌─────────────────────────────────────────────────┐
│  AppHeader (row1: logo/name, row2: run controls) │
├────────────┬────────────────────────────────────┤
│            │                                    │
│ AppSidebar │      NetworkCanvas                 │
│            │   (3-tab: Canvas / Results / ...)  │
│            │                                    │
└────────────┴────────────────────────────────────┘
```

### Header (`features/header/`)

- **`HeaderRow1`** — app title, solver selector, date range picker, snapshot hours
- **`HeaderRow2`** — Run button, Save/Live toggle, scenario name input
- **`HowItWorksModal`** — onboarding explainer
- **`SaveChoiceModal`** — "Run & Save" vs "Live Preview" choice
- **`SolverHelpModal`** — explains available solvers

### Sidebar (`features/sidebar/`)

- **`AppSidebar`** — scrollable panel with 3 asset sections (Supply, Demand, Network)
- **`AssetSection`** — collapsible section per asset type
- **`AssetListItem`** — one row per asset; checkbox to select, expand for overrides
- **`AssetOverridePanel`** — field-level override inputs per asset
- **`AssetCreateForm`** — inline form to create a new asset

### Results (`features/results/`)

Displayed inside the right panel when a result is available:

| Component | Description |
|---|---|
| `KpiCardsGrid` | 4 KPI cards: Status, Balance, Supply, Demand |
| `SimulationSummary` | Detailed panel: IDs, convergence, grid import, curtailment |
| `EnergyFlowPanel` | Animated Sankey-style energy flow diagram |
| `ResultsTab` | Tab wrapper for the results panel |
| `GraphicsTab` | Tab wrapper for charts |
| `ErrorBanner` | Error display when `status === "error"` |
| `EmptyState` | Shown when no result yet |

### Charts (`components/charts/`)

All charts use **ECharts** via `vue-echarts`. Each chart receives `result: SimulationResult` as a prop and derives its data from `result.result_json`.

| Component | Shows |
|---|---|
| `ProductionChart` | Generator dispatch over time (stacked area) |
| `ConsumptionChart` | Load consumption over time |
| `SupplyDemandChart` | Supply vs demand comparison |
| `CapacityFactorChart` | Capacity factors per generator (bar) |
| `BatteryStorageChart` | Battery charge/discharge + state of charge |
| `EnergySummaryChart` | Total energy summary (pie/donut) |
| `ProductionMixChart` | Production mix by carrier |
| `PeakPowerChart` | Peak power per asset |
| `BusVoltageChart` | Bus voltage over time (legacy power flow) |

### Network Canvas (`components/network-canvas/`)

SVG-based topology visualization:
- **`NetworkCanvas.vue`** — main canvas; renders buses, generators, loads with drag support
- **`CableLayer.vue`** — draws cable/transformer connections between buses
- **`AssetIcon.vue`** — renders the correct icon per asset type
- **`MetricTiles.vue`** — floating KPI tiles overlaid on the canvas

---

## Data Flow

```
User selects assets + params
    │
    ▼
simulationStore.buildPayload()
    │
    ├── Live mode → previewSimulation(payload) → currentLiveResult
    │
    └── Save mode → saveSimulation(payload) → historyStore.currentResult
                                            → historyStore.simulationHistory

displayedResult = currentLiveResult ?? historyStore.currentResult
    │
    ▼
KpiCardsGrid, SimulationSummary, Charts, NetworkCanvas
```

---

## Adding a New Chart

1. Create `components/charts/MyChart.vue` — accept `result: SimulationResult` prop
2. Derive data from `result.result_json` (use `useTimeLabels` for x-axis)
3. Use `useEChartsTheme` for consistent dark theme
4. Register in `GraphicsTab.vue`

## Adding a New Asset Type

1. Add the type to the TypeScript union in `api.ts` (`Supply.type` or `Demand.type`)
2. Add an icon mapping in `AssetIcon.vue`
3. Add a color in `useAssetColors.ts`
4. The backend handles the rest (see `wiki-simulation.md`)
