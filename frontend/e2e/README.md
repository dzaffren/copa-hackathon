# E2E tests (Playwright)

The Workstream Graph happy-path E2E lives in `workstream-graph.spec.ts`. It is a
**deliverable** and is **not** run by `npm run test` (that command runs the
Vitest component/unit suite only). The same happy path is covered automatically
in CI by `src/features/workstream-graph/WorkstreamGraphPage.test.tsx` (Vitest +
MSW), so a green pipeline does not depend on Playwright being installed.

## One-time setup

Playwright is intentionally **not** added to `package.json` (keeps `npm ci`
lockfile-clean). Install it when you want to run the E2E:

```bash
cd frontend
npm install -D @playwright/test
npx playwright install chromium
```

## Running

The E2E drives the real stack, so start both servers first:

```bash
# 1. Backend — FastAPI engine (repo root)
uvicorn engine.api:app --port 8000

# 2. Frontend — point it at the engine, then Playwright starts Vite for you
cd frontend
export VITE_API_BASE=http://localhost:8000
npx playwright test
```

`playwright.config.ts` starts the Vite dev server automatically (`npm run dev`)
and reuses one if already running. The backend must be up separately.

## Selecting a node

The graph is drawn by `react-force-graph-2d` into a single `<canvas>`, so in a
real browser there is **no per-node DOM element to click**. The accessible
one-button-per-node DOM that the Vitest suite uses comes from the test stub
(`src/test/mocks/react-force-graph-2d.tsx`) and does not exist under Playwright.
The only DOM handles on a node are the detail panel's neighbour chips — see the
`openNode` helper in `add-task-node.spec.ts`, which sweeps the canvas for any
node then walks the chips to the one it wants. Specs written against
`getByRole("button", { name: <node title> })` or `svg circle` (`add-edge`,
`add-node-chunking`, `workstream-graph`) predate the canvas renderer and no
longer pass.
