import { describe, it, expect, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";

import { renderWithProviders } from "@/test/utils";
import { server } from "@/test/msw/server";
import type { NodeMetadataRequest } from "@/lib/types";
import { NodeMetadataForm } from "./NodeMetadataForm";

/** Capture the body the form actually PUTs — the comma-splitting and the
 *  blank→null rule are wire-level claims, so they are asserted on the payload
 *  rather than on the rendering. */
function captureSave(): { body: () => NodeMetadataRequest | null } {
  let seen: NodeMetadataRequest | null = null;
  server.use(
    http.put(
      "*/api/workstreams/:workstreamId/nodes/:nodeId/metadata",
      async ({ request, params }) => {
        seen = (await request.json()) as NodeMetadataRequest;
        return HttpResponse.json({
          node_id: params.nodeId as string,
          metadata: { status: "available", ...seen },
        });
      },
    ),
  );
  return { body: () => seen };
}

const EMPTY_PROFILE = {
  status: "available" as const,
  policy_owner: null,
  applicability: null,
  empowerment_framework: null,
  requirement: null,
  issuance_date: null,
  effective_date: null,
  keywords: null,
  legal_basis: null,
  ismp_classification: null,
};

describe("NodeMetadataForm", () => {
  it("offers an input for every profile field, pre-filled from the current values", async () => {
    renderWithProviders(
      <NodeMetadataForm
        workstreamId="rmit-v2-2025"
        nodeId="rmit-pd-v2"
        initial={{
          status: "available",
          policy_owner: "Aisyah R.",
          applicability: null,
          empowerment_framework: null,
          requirement: null,
          issuance_date: null,
          effective_date: null,
          keywords: ["technology risk", "cloud"],
          legal_basis: null,
          ismp_classification: null,
        }}
        onDone={() => {}}
      />,
    );

    // A recorded value arrives in the field; a list arrives comma-joined so it
    // can be edited as one line.
    expect(screen.getByLabelText("Policy owner")).toHaveValue("Aisyah R.");
    expect(screen.getByLabelText("Keywords")).toHaveValue(
      "technology risk, cloud",
    );
    // An unset field is empty, never the string "null".
    expect(screen.getByLabelText("Effective date")).toHaveValue("");
    // All nine are editable.
    for (const label of [
      "Policy owner",
      "Applicability",
      "Empowerment framework",
      "Requirement",
      "Issuance date",
      "Effective date",
      "Keywords",
      "Legal basis",
      "ISMP classification",
    ]) {
      expect(screen.getByLabelText(label)).toBeEnabled();
    }
  });

  it("tells the drafter the empowerment framework must be quoted verbatim", () => {
    renderWithProviders(
      <NodeMetadataForm
        workstreamId="rmit-v2-2025"
        nodeId="rmit-pd-v2"
        initial={null}
        onDone={() => {}}
      />,
    );

    // The tool cannot verify the quote, so it says so on screen rather than
    // implying a check it does not perform.
    expect(
      screen.getByText(/quote this word-for-word from the document/i),
    ).toBeInTheDocument();
  });

  it("splits a comma-separated line into separate keywords on save", async () => {
    const saved = captureSave();
    renderWithProviders(
      <NodeMetadataForm
        workstreamId="rmit-v2-2025"
        nodeId="rmit-pd-v2"
        initial={EMPTY_PROFILE}
        onDone={() => {}}
      />,
    );

    await userEvent.type(
      screen.getByLabelText("Keywords"),
      "technology risk, cloud ,, outsourcing",
    );
    await userEvent.click(screen.getByRole("button", { name: /^save$/i }));

    await waitFor(() => expect(saved.body()).not.toBeNull());
    // Trimmed, and the stray empty member between the two commas is dropped.
    expect(saved.body()?.keywords).toEqual([
      "technology risk",
      "cloud",
      "outsourcing",
    ]);
  });

  it("sends a cleared field as null so it reads as not set again", async () => {
    const saved = captureSave();
    renderWithProviders(
      <NodeMetadataForm
        workstreamId="rmit-v2-2025"
        nodeId="rmit-pd-v2"
        initial={{
          ...EMPTY_PROFILE,
          policy_owner: "Aisyah R.",
          legal_basis: ["FSA 2013"],
        }}
        onDone={() => {}}
      />,
    );

    await userEvent.clear(screen.getByLabelText("Policy owner"));
    await userEvent.clear(screen.getByLabelText("Legal basis"));
    // Whitespace is not a value either.
    await userEvent.type(screen.getByLabelText("Applicability"), "   ");
    await userEvent.click(screen.getByRole("button", { name: /^save$/i }));

    await waitFor(() => expect(saved.body()).not.toBeNull());
    const body = saved.body();
    expect(body?.policy_owner).toBeNull();
    expect(body?.applicability).toBeNull();
    // An emptied list is null, not [] — "cleared" and "never set" are one state.
    expect(body?.legal_basis).toBeNull();
    // All nine keys ride along: the server replaces the profile whole.
    expect(Object.keys(body ?? {}).sort()).toEqual([
      "applicability",
      "effective_date",
      "empowerment_framework",
      "ismp_classification",
      "issuance_date",
      "keywords",
      "legal_basis",
      "policy_owner",
      "requirement",
    ]);
  });

  it("closes on a successful save without the caller doing anything", async () => {
    captureSave();
    const onDone = vi.fn();
    renderWithProviders(
      <NodeMetadataForm
        workstreamId="rmit-v2-2025"
        nodeId="rmit-pd-v2"
        initial={EMPTY_PROFILE}
        onDone={onDone}
      />,
    );

    await userEvent.type(screen.getByLabelText("Policy owner"), "Priya S.");
    await userEvent.click(screen.getByRole("button", { name: /^save$/i }));

    await waitFor(() => expect(onDone).toHaveBeenCalled());
  });

  it("cancels without saving anything", async () => {
    let putCalled = false;
    server.use(
      http.put("*/api/workstreams/:ws/nodes/:nodeId/metadata", () => {
        putCalled = true;
        return HttpResponse.json({ node_id: "x", metadata: EMPTY_PROFILE });
      }),
    );
    const onDone = vi.fn();
    renderWithProviders(
      <NodeMetadataForm
        workstreamId="rmit-v2-2025"
        nodeId="rmit-pd-v2"
        initial={{ ...EMPTY_PROFILE, policy_owner: "Aisyah R." }}
        onDone={onDone}
      />,
    );

    await userEvent.clear(screen.getByLabelText("Policy owner"));
    await userEvent.type(screen.getByLabelText("Policy owner"), "Farid M.");
    await userEvent.click(screen.getByRole("button", { name: /^cancel$/i }));

    expect(onDone).toHaveBeenCalled();
    expect(putCalled).toBe(false);
  });
});
