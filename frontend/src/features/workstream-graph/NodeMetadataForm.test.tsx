import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";

import { renderWithProviders } from "@/test/utils";
import { NodeMetadataForm } from "./NodeMetadataForm";

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
});
