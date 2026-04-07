# Simulation URL Sharing — Design

**Goal:** Sync the current simulation ID into the URL query param (`?sim=<uuid>`) so the page can be shared and bookmarked.

## Architecture

New composable `useSimulationUrl` (one file, ~20 lines). Called once in `index.vue`. No store changes.

## Behaviour

- **On save or history load:** `historyStore.selectedSimulationId` changes → `router.replace({ query: { sim: id } })`
- **On new scenario (clear):** `selectedSimulationId` → `null` → `router.replace({ query: {} })`
- **On page load with `?sim=<uuid>`:** `onMounted` reads `route.query.sim`, calls `historyStore.loadSimulationById(id)` to restore the simulation result

## File

| File | Change |
|------|--------|
| `energy-dashboard/app/composables/useSimulationUrl.ts` | Create |
| `energy-dashboard/app/pages/index.vue` | Add `useSimulationUrl()` call |
