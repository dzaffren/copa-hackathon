import "@testing-library/jest-dom/vitest";
import { afterAll, afterEach, beforeAll } from "vitest";
import { cleanup } from "@testing-library/react";
import { server } from "./msw/server";

// react-force-graph-2d is swapped for an accessible DOM stub via a test-time
// alias in vite.config.ts (jsdom has no real canvas). See src/test/mocks.
import {
  resetAnalysedEdges,
  resetCreatedWorkstreams,
  resetDraft,
  resetLinkageReview,
  resetReviewState,
  resetSavedMetadata,
  resetTaskWorkflow,
} from "./msw/handlers";

// jsdom ships no ResizeObserver; the graph canvases observe their container to
// size the (mocked) force graph. A no-op stub is enough — layout is not asserted
// in jsdom.
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver =
  globalThis.ResizeObserver ??
  (ResizeObserverStub as unknown as typeof ResizeObserver);

// jsdom implements no layout engine, so Element.scrollIntoView does not exist.
// The review screen's clause panes call it to bring a cited clause into view;
// without this stub any test that renders them throws. Not a behaviour we can
// assert in jsdom — scroll position is covered by the E2E suite instead.
beforeAll(() => {
  Element.prototype.scrollIntoView = () => {};
});

// jsdom ships no PointerEvent, so `fireEvent.pointerDown(el, {button: 0,
// pointerId: 1})` silently dispatches a plain Event whose `button` and
// `pointerId` are BOTH undefined — a pointer handler that guards on either
// (as the demo bar's drag does) then bails and the interaction looks broken
// in tests while working fine in a browser. Subclassing MouseEvent keeps the
// clientX/clientY plumbing jsdom already implements and adds the pointer
// fields on top.
class PointerEventStub extends MouseEvent {
  pointerId: number;
  pointerType: string;
  isPrimary: boolean;

  constructor(type: string, params: PointerEventInit = {}) {
    super(type, params);
    this.pointerId = params.pointerId ?? 0;
    this.pointerType = params.pointerType ?? "mouse";
    this.isPrimary = params.isPrimary ?? true;
  }
}
globalThis.PointerEvent =
  globalThis.PointerEvent ??
  (PointerEventStub as unknown as typeof PointerEvent);

// Pointer capture is a no-op here: jsdom has no real pointer, and the drag
// handler calls it unconditionally on pointerdown.
beforeAll(() => {
  Element.prototype.setPointerCapture ??= () => {};
  Element.prototype.releasePointerCapture ??= () => {};
});

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));

afterEach(() => {
  cleanup();
  server.resetHandlers();
  // The review and draft handlers hold state in module-level variables so
  // PATCH/PUT round-trips persist within a test; clear both so tests stay
  // independent.
  resetReviewState();
  resetAnalysedEdges();
  resetDraft();
  resetCreatedWorkstreams();
  resetTaskWorkflow();
  resetLinkageReview();
  resetSavedMetadata();
});

afterAll(() => server.close());
