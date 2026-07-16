import "@testing-library/jest-dom/vitest";
import { afterAll, afterEach, beforeAll } from "vitest";
import { cleanup } from "@testing-library/react";
import { server } from "./msw/server";
import {
  resetCreatedWorkstreams,
  resetDraft,
  resetReviewState,
} from "./msw/handlers";

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
});

afterAll(() => server.close());
