import "@testing-library/jest-dom/vitest";
import { afterAll, afterEach, beforeAll } from "vitest";
import { cleanup } from "@testing-library/react";
import { server } from "./msw/server";

// react-force-graph-2d is swapped for an accessible DOM stub via a test-time
// alias in vite.config.ts (jsdom has no real canvas). See src/test/mocks.
import {
  resetCreatedWorkstreams,
  resetDraft,
  resetLinkageReview,
  resetReviewState,
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
  globalThis.ResizeObserver ?? (ResizeObserverStub as unknown as typeof ResizeObserver);

// jsdom implements no layout engine, so Element.scrollIntoView does not exist.
// The review screen's clause panes call it to bring a cited clause into view;
// without this stub any test that renders them throws. Not a behaviour we can
// assert in jsdom — scroll position is covered by the E2E suite instead.
beforeAll(() => {
  Element.prototype.scrollIntoView = () => {};
});

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));

afterEach(() => {
  cleanup();
  server.resetHandlers();
  // The review and draft handlers hold state in module-level variables so
  // PATCH/PUT round-trips persist within a test; clear both so tests stay
  // independent.
  resetReviewState();
  resetDraft();
  resetCreatedWorkstreams();
  resetTaskWorkflow();
  resetLinkageReview();
});

afterAll(() => server.close());
