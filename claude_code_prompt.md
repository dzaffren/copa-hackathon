# Claude Code Prompt — Workstream Brain Full UI Build

> Copy everything below and paste it into Claude Code as your initial prompt.
> Before running, ensure you have applied the CLAUDE.md and CORS updates we discussed (already done!).

---

## The Prompt

```
I need you to build the full Workstream Brain web application — a policy consistency tool for Bank Negara Malaysia (COPA Hackathon 2026). We have a complete HTML Proof-of-Concept (POC) UI that you must convert into a modern Vite + React 18 application.

CRITICAL DIRECTIVE: BUILD THE UI ONLY RIGHT NOW.
I want you to focus 100% on porting the HTML POC to React components (Vite + Tailwind + shadcn) and perfecting the UI/UX.
DO NOT connect to the FastAPI backend yet. DO NOT write `fetch` or `axios` calls or React Query hooks for live data. Hardcode or mock all state directly in the frontend based on the POC designs. We will wire up the backend in a later step.

IMPORTANT: Before writing any code, read the HTML POC files located in `docs/poc/workstream-brain-copy/` to understand the target design, layout, styling, and structure for every screen:
- docs/poc/workstream-brain-copy/index.html (Screen 0: Home/Dashboard)
- docs/poc/workstream-brain-copy/workstream.html (Screen 1: Workstream Graph)
- docs/poc/workstream-brain-copy/task.html (Screen 1a: Task Screen)
- docs/poc/workstream-brain-copy/review.html (Screen 2: Review Linkages)
- docs/poc/workstream-brain-copy/drafting.html (Screen 3: Drafting Workspace)
- docs/poc/workstream-brain-copy/new-workstream.html (Screen 5: New Workstream)

Also read these files to understand the data shapes and system context (but remember, UI comes first!):
- CLAUDE.md (project conventions, do NOT violate)
- README.md (architecture overview)
- engine/api.py (ALL existing API routes — you will eventually consume these)
- engine/workstreams.py (node types, edge types, data shapes)
- engine/connections.py (the finder→critic algorithm, 5-label taxonomy)
- engine/clauses.py (clause index structure)
- engine/ingest.py (PDF ingestion pipeline)
- data/workstreams/opres-v2/graph.json (real graph fixture — understand the shape)
- data/workstreams/opres-v2/workstream.json (workstream metadata shape)
- data/artifacts/connection-trace-opres-v1-2025-draft__open-finance-v1-2025-ed.json (real AI trace — understand findings shape)
- data/artifacts/clause-index.json (first 100 lines — understand clause shape)
- docs/discovery/workstream-brain-mvp1/brief.md (the full product design brief — screen specs, node model, edge layers, taxonomy, institution map analyses)
- frontend/src/App.tsx (existing routes — some features already partially built)
- frontend/package.json (existing dependencies)

Write an implementation plan FIRST. Do not write code until I approve the plan.

## TECH STACK (non-negotiable)
- Frontend: Vite + React 18 + TypeScript + Tailwind CSS + shadcn/ui
- Backend: FastAPI (Python) — already exists at engine/api.py
- Graph visualization: react-force-graph-2d (for the Obsidian-style interactive graph)
- State management: TanStack Query (already installed)
- Routing: react-router-dom v6 (already installed)
- Icons: lucide-react (already installed)

## DATA SHAPES FOR MOCKING (DO NOT CONNECT TO API YET)
Do not write network requests for these! Just use these shapes to create hardcoded mock data for your React components so the UI is fully populated and interactive.

### Workstream CRUD
- GET  /api/workstreams → list all workstreams
- POST /api/workstreams → create a new workstream (body: {name, description, deliverable_type, target_publication, access, reviewer_ids})
- GET  /api/reviewers → list selectable reviewers for the create form

### Graph Screen (Screen 1 — the hero)
- GET  /api/workstreams/{id}/graph → nodes + edges for the primary subgraph
- GET  /api/workstreams/{id}/nodes/{node_id} → node detail (first-order neighbours, concepts, recent activity)
- GET  /api/workstreams/{id}/edges/{edge_id} → edge detail (source/target nodes, findings if analysed)
- POST /api/workstreams/{id}/nodes → add a node + edges to the graph (body: {title, node_type, edges: [{target_node_id, edge_type}]})
- POST /api/workstreams/{id}/edges/{edge_id}/analyze → trigger AI analysis (returns findings or no_matching_source)

### Cross-Workstream
- GET  /api/workstreams/{id}/cross-links → cross-workstream linkages (the demo climax)

### Task Screen (Screen 1a)
- GET  /api/workstreams/{id}/tasks/{node_id} → task details + neighbours + analysed state

### Review Linkages (Screen 2)
- GET  /api/workstreams/{id}/edges/{edge_id}/review → two-pane review data (source_clauses, target_clauses, findings with label/sentiment/summary)
- GET  /api/workstreams/{id}/edges/{edge_id}/findings → raw findings array
- PATCH /api/workstreams/{id}/edges/{edge_id}/findings/{finding_id} → set review_state (accepted/dismissed/pending)

### Drafting Workspace (Screen 3)
- GET  /api/workstreams/{id}/tasks/{node_id}/reviewed-linkages → accepted findings for the side panel
- GET  /api/workstreams/{id}/tasks/{node_id}/related-linkages?hops=1 → 1-hop neighbour findings
- GET  /api/workstreams/{id}/tasks/{node_id}/draft → load the draft HTML
- PUT  /api/workstreams/{id}/tasks/{node_id}/draft → save draft (body: {content_html})
- POST /api/workstreams/{id}/tasks/{node_id}/copilot → scripted copilot (body: {intent, turn})

## THE 6 SCREENS TO BUILD (in priority order)

### Screen 0: Home / Dashboard
- Shows a sidebar listing all workstreams (from GET /api/workstreams)
- Cards for each workstream with name, deliverable type, status
- "+ New Workstream" button → navigates to /workstreams/new
- "Institution Map" entry → navigates to /institution-map
- The sidebar persists across ALL screens (collapsible)

### Screen 1: Workstream Graph (THE HERO — most important screen)
- Route: /workstreams/:workstreamId
- An interactive, zoomable, force-directed graph canvas (use react-force-graph-2d)
- Nodes are colored by node_type (8 types: task, internal-published, international-standard, peer-regulator, act-law, industry-input, supervisory-letter, others)
- The task node is visually distinct (larger, centered, glowing)
- Edges show edge_type label (supersedes, references, contributes-to, parallel-to)
- Edges that are "analysed" show a green badge with findings_count; "not_analysed" show amber
- Clicking a NODE opens a slide-out NODE DETAIL panel on the right with:
  - Node type badge, title, issuer, description
  - ISMP Classification badge (mocked data, e.g., "ISMP: Prudential")
  - "Pursuant to" badge linking to an Act (e.g., "Pursuant to: FSA 2013")
  - First-order neighbours as clickable chips
  - Recent activity
  - Concepts disclosure (Mock the NER concepts: `policy_owner`, `applicability`, `empowerment_framework`, `requirement`, `issuance_date`, `effective_date`, `keywords`)
  - Action button: "Open task" for task nodes → navigate to task screen; "Open source" for others
- Clicking an EDGE opens a slide-out EDGE DETAIL panel with:
  - Edge type badge, status badge (analysed/not analysed)
  - Source ↔ Target title
  - If not analysed: show "Analyze linkages" CTA button (calls POST .../analyze)
  - If analysed: show finding cards with label pill + summary. "Review" button → navigate to review screen
- "Add Node" floating button → modal with: title input, node_type picker (grid of 8 types), edge picker (select existing node + edge_type)
- Cross-workstream section at the bottom: if GET /api/workstreams/{id}/cross-links returns links, show a "Cross-Workstream Linkages" banner with count + "View" button
- Zoom controls: zoom in / zoom out / reset buttons

### Screen 1a: Task Screen
- Route: /workstreams/:workstreamId/tasks/:nodeId
- Header: task title, status badge (Draft | Pending Review | Approved), owner, format
- Source document card
- Neighbours list — each neighbour shows: title, node_type badge, edge_type, analysed state (✓ N linkages / ○ Not analysed)
- Pairwise comparison area: for each analysed neighbour, show a collapsible card with the findings between the task and that neighbour, filterable by label
- Top-right actions: "Assign to Checker" button (Checker-Maker workflow mock — toggles status from Draft to Pending Review), "Open draft" button → navigate to drafting workspace

### Screen 2: Review Linkages (two-pane reader)
- Route: /workstreams/:workstreamId/edges/:edgeId/review
- Left pane: source document clauses (scrollable list of clause cards with clause_number + text)
- Right pane: target document clauses (same format)
- Between the panes (or overlaid): a vertical stack of finding cards, each with:
  - Label pill (color-coded: aligns-with=emerald, differs-on=amber, conflicts-with=red, silent-on=blue, goes-beyond=purple)
  - Sentiment tag on differs-on only (tighten/loosen/neutral)
  - Summary text
  - Source clause numbers (clickable — highlights the clause in the left pane)
  - Target clause numbers (clickable — highlights in right pane)
  - Accept / Dismiss / Pending buttons (PATCH .../findings/{finding_id})
- Summary bar at top: total findings count, accepted/dismissed/pending counts

### Screen 3: Drafting Workspace
- Route: /workstreams/:workstreamId/tasks/:nodeId/draft
- Split view: editor on the right, 3-tab context panel on the left
- Editor: a styled contenteditable div (not a real Word embed). Load from GET .../draft, save to PUT .../draft
- Tab 1: "Reviewed Linkages" — accepted findings from GET .../reviewed-linkages, shown as linkage cards
- Tab 2: "Related · 1 hop" — findings between neighbours from GET .../related-linkages
- Tab 3: "Drafting Copilot" — a 7-intent dropdown (PD, ED, DP, FAQ, Engagement Deck, Feedback Template, Peer Benchmarking) + chat-like UI. On submit, POST .../copilot with {intent, turn}

### Screen 4: Institution Map (demo climax)
- Route: /institution-map
- Filter-pill UI at top: "+ Add workstream" dropdown to select workstreams, selected ones as pills with × to remove
- Main area: a SECOND force-graph (separate from screen 1) showing documents from ALL selected workstreams, with cross-workstream edges highlighted in a distinct color
- For each selected workstream, fetch GET /api/workstreams/{id}/graph and GET /api/workstreams/{id}/cross-links
- Cross-workstream edges (from cross-links) rendered as dashed, bright-colored lines
- Clicking a cross-link shows the finding summary + label
- Below the graph: a "Cross-Workstream Linkages" table listing all cross-links with: source doc, target doc, label tally, "Review" link
- **CRITICAL DEMO REQUIREMENT:** Mock a cross-workstream edge between "BCM" (Business Continuity Management) and "Resolution & Recovery Planning". This directly addresses user feedback about overlapping policies only being discovered post-FPWG. Make sure this overlap is prominent on this screen!

### Screen 5: New Workstream
- Route: /workstreams/new
- Three-card form:
  - Card 1 "Basics": name (required), description, deliverable_type dropdown (Policy Document, Exposure Draft, Discussion Paper), target_publication date picker
  - Card 2 "People": owner (read-only — shows current user), reviewers multi-select (from GET /api/reviewers)
  - Card 3 "Access": team_only / department_wide radio
- "Create Workstream" button → POST /api/workstreams → redirect to the new workstream's graph

## DESIGN REQUIREMENTS (critical — judges score on visual polish)
- Dark mode by default (deep navy/slate background, NOT pure black)
- Glass-morphism cards (backdrop-blur, subtle borders, semi-transparent backgrounds)
- Color palette: emerald for positive/aligns, amber for caution/differs, red for conflicts, blue for silent-on, purple for goes-beyond
- Node type colors on the graph:
  - task: bright cyan (the hero node)
  - internal-published: emerald
  - international-standard: gold
  - peer-regulator: coral
  - act-law: red
  - industry-input: teal
  - supervisory-letter: violet
  - others: gray
- Smooth page transitions
- Loading skeletons (not spinners) for data fetches
- The graph must feel alive: nodes should gently float, edges should have subtle animation
- Typography: use Inter font (already common in Tailwind setups)
- Responsive: must look good on 1920×1080 demo screen

## COLLAPSIBLE SIDEBAR (shared across ALL screens)
- Left sidebar listing:
  - Each workstream the user belongs to (from GET /api/workstreams), with a colored dot for status
  - "+ New workstream" link
  - "Institution Map" link (with a special icon)
- Clicking a workstream navigates to /workstreams/{id}
- Collapse to icon-only rail on toggle
- Current workstream is highlighted

## DATA SHAPES (for TypeScript types)
The API returns these shapes. Define TypeScript interfaces for all of them:

```typescript
// From GET /api/workstreams/{id}/graph
interface GraphResponse {
  workstream_id: string;
  primary_task_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
}
interface GraphNode {
  id: string;
  node_type: "task" | "internal-published" | "international-standard" | "peer-regulator" | "act-law" | "industry-input" | "supervisory-letter" | "others";
  title: string; 
  issuer?: string;
  short_type?: string;
  ismp_classification?: string;
  pursuant_to?: string;
}
interface GraphEdge {
  id: string;
  source: string;
  target: string;
  edge_type: "supersedes" | "references" | "contributes-to" | "parallel-to";
  analysed: boolean;
  findings_count: number;
}

// From GET .../edges/{id}/review
interface ReviewResponse {
  edge: { id: string; edge_type: string; source_node: NodeRef; target_node: NodeRef };
  source_clauses: ClauseCard[];
  target_clauses: ClauseCard[];
  findings: Finding[];
  counts: { total: number; accepted: number; dismissed: number; pending: number };
}
interface Finding {
  id: string;
  summary: string;
  label: "aligns-with" | "differs-on" | "conflicts-with" | "silent-on" | "goes-beyond";
  sentiment?: "tighten" | "loosen" | "neutral" | null;
  review_state: "pending" | "accepted" | "dismissed";
  source_clauses: { clause_number: string; text: string }[];
  target_clauses: { clause_number: string; text: string }[];
  scope_note?: string;
}

// From GET .../cross-links
interface CrossLink {
  id: string;
  edge_type: string;
  near: { node_id: string; title: string; workstream_id: string };
  far: { node_id: string; title: string; workstream_id: string; workstream_name: string };
  findings_count: number;
  labels: Record<string, number>;
}
```

## NEW BACKEND ROUTES TO ADD (engine/api.py)
You WILL need to add these new routes to the FastAPI backend to support full functionality:

### 1. PDF Upload + Ingest route
POST /api/documents/upload
- Accepts a multipart file upload (PDF or DOCX)
- Calls engine.ingest.ingest_document() to convert to markdown
- Calls engine.clauses.segment_clauses() to extract clauses
- Saves the clause index entries to data/artifacts/clause-index.json (merge mode)
- Returns: {document_id, clause_count, status: "indexed"}

### 2. Clause Index query route
GET /api/clauses?document_id={id}
- Returns all clauses for a given document from the clause index
- Shape: {clauses: [{clause_number, text, heading, parent, children}]}

### 3. Live connection finding route (optional — for real demo)
POST /api/connections/find
- Body: {doc_a_id, doc_b_id}
- Calls engine.connections.find_connections() with the real finder/critic
- Returns the FindConnectionsResult
- NOTE: This requires Azure Claude credentials. If not available, fall back to replaying the canned trace files from data/artifacts/connection-trace-*.json

## GRAPH VISUALIZATION DETAILS (react-force-graph-2d)
Install: npm install react-force-graph-2d
The library expects: { nodes: [{id, ...}], links: [{source, target, ...}] }
- Map GraphEdge[] to links (rename "source"/"target" to match)
- Custom node rendering: draw circles with node_type-based colors, label text below
- Task node: larger radius, pulsing glow animation (use Canvas API in nodeCanvasObject)
- Edge rendering: draw edge_type label at midpoint, use dashed line for not-analysed edges
- On node click: emit event to open the node detail panel
- On link click: emit event to open the edge detail panel
- Enable zoom, pan, drag
- d3 force config: charge strength -300, link distance 150, center force enabled

## IMPLEMENTATION ORDER (UI ONLY)
Write your plan and execute in this order. Remember: NO backend connections yet.
1. Set up shared layout (sidebar + main content area) based on `index.html`
2. Create hardcoded mock data fixtures using the TypeScript types
3. Home/Dashboard page UI
4. Workstream Graph UI with react-force-graph-2d (the hero — spend the most time here)
5. Node detail + Edge detail slide-out panels UI
6. Add Node modal UI
7. Review Linkages two-pane screen UI
8. Task Screen UI
9. Drafting Workspace UI (editor + 3 tabs)
10. New Workstream form UI
11. Institution Map (cross-workstream graph) UI
12. Polish: animations, transitions, and making sure the React app looks EXACTLY like the HTML POC.

## CRITICAL RULES
- NEVER modify files in engine/ without asking me first. The engine tests are green and must stay green.
- ALL clause text shown to users MUST come from the API response, never hardcoded or fabricated.
- The 5-label taxonomy is sacred: aligns-with, differs-on, conflicts-with, silent-on, goes-beyond. No other labels exist.
- Sentiment (tighten/loosen/neutral) ONLY appears on differs-on. Never on other labels.
- Run `npm test` in frontend/ after significant changes to make sure existing tests don't break.
- Run `.venv/Scripts/python.exe -m pytest engine/tests -q` if you touch any engine/ file.
- Use CORS middleware in the FastAPI app so the Vite dev server (port 5173) can reach it (port 8000).
- Write UTF-8 everywhere (Windows environment — see CLAUDE.md learnings).

## ENVIRONMENT
- OS: Windows 11
- Python venv: .venv/Scripts/python.exe
- Node: use npm (not yarn/pnpm)
- FastAPI runs on: http://localhost:8000
- Vite dev server: http://localhost:5173
- Set VITE_API_BASE=http://localhost:8000 in frontend/.env

Now write the implementation plan. Group by component, list every file you'll create or modify, and flag any open questions.
```

---

## Appendix A: CLAUDE.md Addition

> Add this block to the bottom of the existing `CLAUDE.md` before running Claude Code, so it picks up the UI conventions automatically:

```markdown
## Frontend conventions (Workstream Brain app)

- **The frontend is `frontend/`** — Vite + React 18 + TypeScript + Tailwind + shadcn/ui.
- **Graph library:** `react-force-graph-2d` for all interactive graph canvases.
- **API base:** set `VITE_API_BASE` in `frontend/.env` (defaults to `http://localhost:8000`).
- **State:** TanStack Query for all server state; no Redux/Zustand.
- **Node types (8):** task, internal-published, international-standard, peer-regulator, act-law, industry-input, supervisory-letter, others.
- **Edge types (4):** supersedes, references, contributes-to, parallel-to.
- **Finding labels (5):** aligns-with, differs-on, conflicts-with, silent-on, goes-beyond.
- **Sentiment (3, differs-on only):** tighten, loosen, neutral.
- **CORS:** FastAPI must include CORS middleware allowing origin `http://localhost:5173`.
- **Dark mode:** default theme. Deep navy/slate, NOT pure black.
```

## Appendix B: Pre-install react-force-graph-2d

> Run this before starting Claude Code so it doesn't have to ask:

```bash
cd frontend
npm install react-force-graph-2d @types/react-force-graph-2d
```

*(If `@types/react-force-graph-2d` doesn't exist as a separate package, Claude Code can create a local `.d.ts` declaration file.)*

## Appendix C: Add CORS to FastAPI (do this manually first)

> Add this to `engine/api.py` inside `create_app()`, right after `app = FastAPI(...)`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Appendix D: Create frontend/.env

```
VITE_API_BASE=http://localhost:8000
```
