import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import { EngineConfigError, getGraph } from "./lib/engineApi";

// Mock the engine client so App's WorkspacePage load is deterministic and offline.
vi.mock("./lib/engineApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./lib/engineApi")>();
  return { ...actual, getGraph: vi.fn() };
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("App", () => {
  it("routes the root path to the drafter workspace (its strip renders)", async () => {
    // Fail the load so ClusterGraph (real React Flow) never mounts in jsdom; the
    // workspace strip renders regardless, proving `/` is the WorkspacePage.
    vi.mocked(getGraph).mockRejectedValue(
      new EngineConfigError("test: engine base url not set"),
    );
    render(<App />);

    expect(
      screen.getByRole("link", { name: "Switch to supervisor view" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Aisyah R.")).toBeInTheDocument();

    // The load settles into the error region (never a blank screen); awaiting it
    // also flushes the async state update inside act().
    expect(await screen.findByTestId("workspace-error")).toBeInTheDocument();
  });
});
