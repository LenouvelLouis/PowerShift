# Energy Dashboard — Frontend

Nuxt 3 dashboard for the Energy Grid Simulation Platform.

---

## Stack

| Technology | Role |
|---|---|
| Nuxt 3 | Vue meta-framework |
| Vue 3 + TypeScript | UI components |
| @nuxt/ui | Component library |
| Pinia | Global state management |
| TanStack Query | Server-state / API calls |

---

## Dev commands

```bash
pnpm install         # install dependencies
pnpm dev             # start dev server at http://localhost:3000
pnpm typecheck       # TypeScript type check
pnpm lint            # lint
pnpm build           # production build
pnpm preview         # locally preview production build
```

---

## Structure

```
app/
├── components/
│   ├── features/       # Feature-level components (header, simulation panels, …)
│   └── ui/             # Generic reusable UI primitives
├── composables/
│   └── api.ts          # All API calls via TanStack Query
├── stores/
│   └── simulation.ts   # Pinia store for simulation state
└── pages/              # Nuxt pages
```

---

## Conventions

- All API calls go through composables in `composables/api.ts` using TanStack Query — no raw `fetch` in components.
- Pinia stores (`stores/`) are for truly global state only.
- Page components contain no business logic — delegate to composables and stores.
- `pnpm typecheck` must pass before committing.

---

## Backend

The dashboard talks to the FastAPI backend running at `http://localhost:8000`.
See the root `README.md` for backend setup instructions.
