Refer to the uploaded PDF file and the local file `docs/pitch/technical-innovation.md` containing all content for Project SELARAS. Create a high-end, single-file HTML presentation slide deck at `docs/pitch/selaras_presentation_deck.html` using the design principles of the `frontend-slides` skill (1920x1080 fixed 16:9 stage scaling, zero external framework dependencies, embedded CSS/JS).

### 🎨 Theme & Aesthetic Requirements
- **Theme:** Clean, modern Light Theme with BNM Royal Blue accents (`#2563eb`), crisp off-white background (`#f7f8fa`), white card panels (`#ffffff`), and slate typography (`#0f172a`), matching the Project SELARAS intro page.
- **Emojis:** Strictly NO emojis anywhere in the presentation.
- **Typography & Polish:** Use modern sans-serif typography, sleek glassmorphism/card shadows, subtle CSS animations/slide transitions, and polished pill badges.

---

### 🚫 NO Generic HTML Tables (Visual Layout Rules)
- **Do NOT render plain, generic HTML tables for content slides.**
- Convert raw table data into modern UI components: structured **Card Grids**, **3-Column Progression Flows**, **Metric Cards**, **Feature Badges**, or **Styled Comparison Boards**.
- Where a table format is strictly necessary (e.g. Cost Estimation, User Feedback), it MUST be rendered as a custom, executive-styled component with rounded card containers, subtle row borders, distinct column widths, and hover states.

---

### 📌 Strict Adherence to Slide "Note:" Directives & Architecture Requirements
Under each slide header in the PDF, follow the explicit `Note:` instructions and reference files:

- **Slide 1 Note (Progression Flow):** Render as a horizontal 3-step visual arrow/flow pipeline: `Situation` → `Problem Statements` → `Impact`.

- **Slide 2 & 3 & 4 (Specialised Agent Architecture & Technical Innovation):** 
  * **Direct Reference:** Read and refer to `docs/pitch/technical-innovation.md` for all technical details, pipeline stages, model tiers, citation integrity mechanisms, and copilot workflows.
  * **Layout:** Render as an executive 4-card technical architecture grid covering:
    1. *Structural Citation Integrity* (Zero Hallucination Guarantee & code-level validators).
    2. *6-Stage Finder Pipeline* (Multi-tier model routing: Haiku → Sonnet → Opus).
    3. *Recommendations Engine* (Evidence floor & drafter requirement dimensions).
    4. *AI Drafting Copilot Workflow* (5-step slash command workflow: `/explore-task` → `/deliver`).

- **Slide 5 Note (Timeline Progression):** Render Phase 1 (Delivered) vs. Phase 2 (Next Steps) as a connected horizontal timeline progression with directional flow arrows.

---

### 💬 Slide 9: Complete User Feedback Instructions (CRITICAL)
- **Zero Truncation / 100% Coverage:** Include ALL user feedback items, recommendations, rationales, BNM action points, and analyst comments from the PDF (pages 6–12). Do NOT skip, summarize, or omit a single row.
- **Highlight Bold Text (`** **`):** Any text enclosed in `** **` in the comments column (e.g., `**The gap is relevant**`, `**The recommendation is good**`, `**it is a valid recommendation**`, `**valid recommendation**`) MUST be visually highlighted using styled status pills/badges (e.g., a green/blue pill badge with bold text).
- **Layout:** Use a clean, scrollable card list or a high-density structured component so all feedback items are legible and organized without overflowing the 16:9 stage layout.

---

### 📑 Comprehensive Slide Deck Content Blueprint
Cover all slides from the PDF and docs/pitch/technical-innovation.md thoroughly:
1. **Slide 1:** About Project SELARAS (Situation → Problem → Impact Flow)
2. **Slide 2:** Specialised Agent Architecture & Technical Innovation - Extraction → Finder Pipeline (Refer directly to `docs/pitch/technical-innovation.md` — 4-card architecture grid) - adapt the mermaid diagrams
3. **Slide 3:** Specialised Agent Architecture & Technical Innovation - Recommendations Engine (Refer directly to `docs/pitch/technical-innovation.md` — 4-card architecture grid) - adapt the mermaid diagrams
4. **Slide 4:** Specialised Agent Architecture & Technical Innovation - Drafting Copilot (Refer directly to `docs/pitch/technical-innovation.md` — 4-card architecture grid) - adapt the mermaid diagrams
5. **Slide 5:** Feasibility & Scalability (Functional & Non-Functional split with evidence metrics)
6. **Slide 6:** Risks & Mitigation (AI accuracy, Confidentiality in/out scope, Maker-Checker accountability)
7. **Slide 7:** Implementation Timeline (Phase 1 Delivered vs. Phase 2 Next Steps with arrow flow)
8. **Slide 8:** Reusability across BNM Departments (FDI, FS, PFP, PPD, JP4, JDM with Power Metrics)
9. **Slide 9:** User Feedback (100% complete table with highlighted `** **` comment badges and 67% validation callout stat)
10. **Slide 10:** Cost Estimation & Production AWS Hosting (Inference costs, Fargate/S3 subtotal, $1,650-$1,800/mo bottom line)
11. **Slide 11:** Limitations & Scope Boundaries (Context limits, non-PDF chunking, scanned docs, topical noise)
11. **Slide 12:** Limitations of this Prototype

Please generate the complete HTML file at `docs/pitch/selaras_presentation_deck.html`.

dont miss any important information.
