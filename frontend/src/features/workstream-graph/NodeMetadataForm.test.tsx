import { describe, it, expect, vi } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";

import { renderWithProviders } from "@/test/utils";
import { server } from "@/test/msw/server";
import { METADATA_SAVE_FAILS_NODE_ID } from "@/test/msw/handlers";
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
  issuance_date: null,
  effective_date: null,
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
          issuance_date: null,
          effective_date: null,
          legal_basis: ["FSA 2013", "IFSA 2013"],
          ismp_classification: null,
        }}
        onDone={() => {}}
      />,
    );

    // A recorded value arrives in the field; a list arrives comma-joined so it
    // can be edited as one line.
    expect(screen.getByLabelText("Policy owner")).toHaveValue("Aisyah R.");
    expect(screen.getByLabelText("Legal basis")).toHaveValue(
      "FSA 2013, IFSA 2013",
    );
    // An unset field is empty, never the string "null".
    expect(screen.getByLabelText("Effective date")).toHaveValue("");
    // All seven are editable.
    for (const label of [
      "Policy owner",
      "Applicability",
      "Empowerment framework",
      "Issuance date",
      "Effective date",
      "Legal basis",
      "ISMP classification",
    ]) {
      expect(screen.getByLabelText(label)).toBeEnabled();
    }
  });

  it("splits a comma-separated line into separate Acts on save", async () => {
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
      screen.getByLabelText("Legal basis"),
      "FSA 2013, IFSA 2013 ,, DFIA 2002",
    );
    await userEvent.click(screen.getByRole("button", { name: /^save$/i }));

    await waitFor(() => expect(saved.body()).not.toBeNull());
    // Trimmed, and the stray empty member between the two commas is dropped.
    expect(saved.body()?.legal_basis).toEqual([
      "FSA 2013",
      "IFSA 2013",
      "DFIA 2002",
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
    // All seven keys ride along: the server replaces the profile whole.
    expect(Object.keys(body ?? {}).sort()).toEqual([
      "applicability",
      "effective_date",
      "empowerment_framework",
      "ismp_classification",
      "issuance_date",
      "legal_basis",
      "policy_owner",
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

  it("disables both buttons and reads Saving… while the save is in flight", async () => {
    let release: (() => void) | null = null;
    server.use(
      http.put(
        "*/api/workstreams/:ws/nodes/:nodeId/metadata",
        async ({ params }) => {
          await new Promise<void>((resolve) => {
            release = resolve;
          });
          return HttpResponse.json({
            node_id: params.nodeId as string,
            metadata: EMPTY_PROFILE,
          });
        },
      ),
    );
    renderWithProviders(
      <NodeMetadataForm
        workstreamId="rmit-v2-2025"
        nodeId="rmit-pd-v2"
        initial={EMPTY_PROFILE}
        onDone={() => {}}
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: /^save$/i }));

    // A second click must not fire a second write while the first is unresolved.
    const saving = await screen.findByRole("button", { name: /saving…/i });
    expect(saving).toBeDisabled();
    expect(screen.getByRole("button", { name: /^cancel$/i })).toBeDisabled();

    release?.();
  });

  it("keeps the drafter's values and explains a save that could not be completed", async () => {
    server.use(
      http.put("*/api/workstreams/:ws/nodes/:nodeId/metadata", () =>
        HttpResponse.json(
          {
            code: "METADATA_TOO_LARGE",
            message: "applicability exceeds 2000 characters.",
            field: "applicability",
          },
          { status: 413 },
        ),
      ),
    );
    renderWithProviders(
      <NodeMetadataForm
        workstreamId="rmit-v2-2025"
        nodeId="rmit-pd-v2"
        initial={EMPTY_PROFILE}
        onDone={() => {}}
      />,
    );

    await userEvent.type(
      screen.getByLabelText("Effective date"),
      "28 November 2025",
    );
    await userEvent.click(screen.getByRole("button", { name: /^save$/i }));

    // The refusal is explained in the drafter's terms, not the server's code.
    expect(await screen.findByRole("alert")).toHaveTextContent(
      /too long — shorten it/i,
    );
    // Nothing typed is lost, and Save is live again so she can retry.
    expect(screen.getByLabelText("Effective date")).toHaveValue(
      "28 November 2025",
    );
    expect(screen.getByRole("button", { name: /^save$/i })).toBeEnabled();
  });

  it("reports a refusal it has no copy for using the server's own message", async () => {
    // The shared mock refuses this node id, so the failure path needs no
    // per-test handler override.
    renderWithProviders(
      <NodeMetadataForm
        workstreamId="rmit-v2-2025"
        nodeId={METADATA_SAVE_FAILS_NODE_ID}
        initial={EMPTY_PROFILE}
        onDone={() => {}}
      />,
    );

    await userEvent.type(screen.getByLabelText("Policy owner"), "Priya S.");
    await userEvent.click(screen.getByRole("button", { name: /^save$/i }));

    // No ERROR_COPY entry for SAVE_FAILED, so the server's message is shown
    // rather than a generic apology that hides what happened.
    expect(await screen.findByRole("alert")).toHaveTextContent(
      /could not be saved/i,
    );
    expect(screen.getByLabelText("Policy owner")).toHaveValue("Priya S.");
  });
});

describe("NodeMetadataForm — ISMP classification", () => {
  it("offers the four BNM classifications plus an unset option", async () => {
    renderWithProviders(
      <NodeMetadataForm
        workstreamId="rmit-v2-2025"
        nodeId="rmit-pd-v2"
        initial={EMPTY_PROFILE}
        onDone={() => {}}
      />,
    );

    const select = screen.getByLabelText("ISMP classification");
    expect(select.tagName).toBe("SELECT");
    // Unset stays available: a document nobody has classified must not be
    // forced into a guess, since these categories carry real handling rules.
    expect(
      within(select)
        .getAllByRole("option")
        .map((o) => o.textContent),
    ).toEqual(["Not set", "UMUM", "TERHAD", "SULIT", "RAHSIA"]);
  });

  it("saves the chosen classification", async () => {
    const saved = captureSave();
    renderWithProviders(
      <NodeMetadataForm
        workstreamId="rmit-v2-2025"
        nodeId="rmit-pd-v2"
        initial={EMPTY_PROFILE}
        onDone={() => {}}
      />,
    );

    await userEvent.selectOptions(
      screen.getByLabelText("ISMP classification"),
      "SULIT",
    );
    await userEvent.click(screen.getByRole("button", { name: /^save$/i }));

    await waitFor(() => expect(saved.body()).not.toBeNull());
    expect(saved.body()?.ismp_classification).toBe("SULIT");
  });

  it("sends null when left unset", async () => {
    const saved = captureSave();
    renderWithProviders(
      <NodeMetadataForm
        workstreamId="rmit-v2-2025"
        nodeId="rmit-pd-v2"
        initial={EMPTY_PROFILE}
        onDone={() => {}}
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: /^save$/i }));

    await waitFor(() => expect(saved.body()).not.toBeNull());
    expect(saved.body()?.ismp_classification).toBeNull();
  });
});
