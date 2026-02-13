# Mission Control — Frontend

Vue 3 + Vite + TypeScript frontend for Mission Control.

## Setup

```bash
npm install
```

## Development

```bash
npm run dev          # dev server at :5173, API proxied to backend at :5055
npm run build        # production build (type-check + vite build)
npm run preview      # serve production build locally
```

## Testing

```bash
npm test             # vitest (single run)
npm run test:watch   # vitest (watch mode)
```

## Type Generation

Regenerate TypeScript types from the backend API (backend must be running):

```bash
npm run generate-types
```

Output: `src/types/api.ts` (git-ignored, generated from `/openapi.json`).

## Stack

- **Vue 3** with `<script setup>` and Composition API
- **TypeScript** for type safety
- **Pinia** for state management
- **PrimeVue** for UI components (dark theme)
- **Apache ECharts** (vue-echarts) for charts
- **vue-router** with auto-discovered module routes
