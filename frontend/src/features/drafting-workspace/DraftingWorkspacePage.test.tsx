import { describe, it, expect } from "vitest";
import { cleanup, screen, within, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderApp } from "@/test/utils";
import { COPILOT_INTENT_LABELS } from "@/lib/types";
import {
  CLARIFICATION_QUESTIONS,
  DRAFT_SECTIONS,
  LEADING_OPTIONS,
  MENTIONABLE,
  NODE_METADATA,
  RELEASE_REVIEWERS,
  SLASH_COMMANDS,
  WORKSTREAM_CONTEXT,
} from "./copilotV2Data";

const THINKING_WAIT = { timeout: 8000 };
// The scripted brainstorming flow (silent context pull + six clarification
// rounds) runs several seconds of real timers — past vitest's 5s default.
const LONG_FLOW = 25000;

const DRAFT_URL = "/workstreams/opres-v2/tasks/opres-pd-v0-3/draft";
const BCBS_EDGE = "e-opres_v0_3--bcbs_opres_2021";

async function loadWorkspace() {
  renderApp(DRAFT_URL);
  // The editor shell mounts before its queries resolve, so waiting on
  // draft-surface alone races the draft and task fetches. Wait for the saved
  // draft to actually be in the DOM.
  await screen.findByTestId("draft-surface");
  await waitFor(() =>
    expect(screen.getByTestId("draft-surface")).toHaveTextContent(
      /at least annually/,
    ),
  );
  await screen.findByRole("heading", {
    name: "Operational Resilience PD — v0.3",
  });
}

/** Accept a finding the way a drafter does — on the review screen — so the
 *  Reviewed tab is populated by the real path rather than a seeded fixture. */
async function acceptOnReviewScreen(user: ReturnType<typeof userEvent.setup>) {
  renderApp(`/workstreams/opres-v2/edges/${BCBS_EDGE}/review`);
  const card = (await screen.findAllByTestId("finding-card"))[0];
  await user.click(within(card).getByRole("button", { name: "Accept" }));
  await waitFor(() =>
    expect(screen.getByTestId("count-accepted")).toHaveTextContent(
      "1 accepted",
    ),
  );
  // Unmount before the workspace renders: two mounted apps would both answer
  // `screen`. The accepted state survives because the MSW handlers hold it in a
  // module-level map (cleared per-test in setup.ts) — exactly as the real
  // file-backed store survives a page navigation.
  cleanup();
}

describe("DraftingWorkspacePage — landing", () => {
  it("renders the draft surface, the three tabs, and the breadcrumb", async () => {
    await loadWorkspace();

    expect(
      screen.getByRole("heading", { name: "Operational Resilience PD — v0.3" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /Workstream graph/i }),
    ).toBeInTheDocument();
    for (const name of [/Reviewed Findings/, /Recommendations/, /Copilot/]) {
      expect(screen.getByRole("tab", { name })).toBeInTheDocument();
    }
  });

  it("opens on the Reviewed Findings tab", async () => {
    await loadWorkspace();
    expect(
      screen.getByRole("tab", { name: /Reviewed Findings/ }),
    ).toHaveAttribute("aria-selected", "true");
  });

  it("shows the working draft's clause text verbatim in the editor", async () => {
    await loadWorkspace();
    expect(screen.getByTestId("draft-surface")).toHaveTextContent(
      "A financial institution shall conduct scenario testing of its operational resilience arrangements at least annually.",
    );
  });

  it("shows an auto-save indicator", async () => {
    await loadWorkspace();
    expect(screen.getByTestId("autosave-indicator")).toHaveTextContent(
      /Auto-saved \d+s ago/,
    );
  });
});

describe("DraftingWorkspacePage — blank team tabs", () => {
  it("shows a placeholder on the Reviewed Findings tab, pending team data", async () => {
    await loadWorkspace();
    expect(
      screen.getByTestId("reviewed-findings-empty"),
    ).toBeInTheDocument();
  });

  it("shows a placeholder on the Recommendations tab, pending team data", async () => {
    const user = userEvent.setup();
    await loadWorkspace();

    await user.click(screen.getByRole("tab", { name: /Recommendations/ }));

    expect(screen.getByTestId("recommendations-empty")).toBeInTheDocument();
  });
});

describe("DraftingWorkspacePage — editor inline callouts", () => {
  it("renders an inline callout beside the accepted clause, colour-coded", async () => {
    const user = userEvent.setup();
    await acceptOnReviewScreen(user);
    await loadWorkspace();

    const callout = await screen.findByTestId("inline-callout");
    expect(callout).toHaveAttribute("data-label", "aligns-with");
    expect(callout).toHaveAttribute("data-clause", "4.4");
    expect(callout.className).toContain("border-emerald-400");
  });
});

describe("DraftingWorkspacePage — Copilot chat", () => {
  async function openCopilot(user: ReturnType<typeof userEvent.setup>) {
    await loadWorkspace();
    await user.click(screen.getByRole("tab", { name: /Copilot/ }));
    await screen.findByTestId("copilot-chat");
  }

  function commandBlock(command: string) {
    return screen
      .queryAllByTestId("command-step")
      .find((el) => el.getAttribute("data-command") === command);
  }

  /** Click a vertical option button inside the currently-open question card
   *  matching `prompt`. */
  async function answer(
    user: ReturnType<typeof userEvent.setup>,
    prompt: string | RegExp,
    optionText: string,
  ) {
    const promptEl = await screen.findByText(prompt, undefined, THINKING_WAIT);
    const card = promptEl.closest(
      '[data-testid="clarification-card"]',
    ) as HTMLElement;
    await user.click(within(card).getByRole("button", { name: optionText }));
  }

  /** Invoke a command by clicking its suggestion chip. */
  async function runViaChip(
    user: ReturnType<typeof userEvent.setup>,
    label: string,
  ) {
    const chip = await screen.findByRole(
      "button",
      { name: label },
      THINKING_WAIT,
    );
    await user.click(chip);
  }

  /** Answer the opening intent question with the PD preset. */
  async function answerIntent(user: ReturnType<typeof userEvent.setup>) {
    await answer(user, "What are you drafting?", COPILOT_INTENT_LABELS.PD);
  }

  /** From a fresh chat, run brainstorming and walk every clarification round,
   *  leaving the flow with the "Run /draft" chip visible. */
  async function reachBrainstormDone(
    user: ReturnType<typeof userEvent.setup>,
  ) {
    await answerIntent(user);
    await runViaChip(user, "Run /explore-task");
    await runViaChip(user, "Run /brainstorm");
    await answer(user, LEADING_OPTIONS[0], LEADING_OPTIONS[0]);
    for (const q of CLARIFICATION_QUESTIONS) {
      await answer(user, q.prompt, q.options[0]);
    }
    await screen.findByRole("button", { name: "Run /draft" }, THINKING_WAIT);
  }

  async function reachBuildDone(user: ReturnType<typeof userEvent.setup>) {
    await reachBrainstormDone(user);
    await runViaChip(user, "Run /draft");
    await runViaChip(user, "Run /write");
    await screen.findByTestId("draft-summary", undefined, THINKING_WAIT);
  }

  it("opens with a chat stream, an input, and asks the intent as vertical options", async () => {
    const user = userEvent.setup();
    await openCopilot(user);

    expect(screen.getByTestId("copilot-chat")).toBeInTheDocument();
    expect(screen.getByTestId("chat-input")).toBeInTheDocument();

    await screen.findByText("What are you drafting?");
    const options = screen.getByTestId("clarification-options");
    expect(options.className).toContain("flex-col");
    // All seven intents are offered as stacked options, not a dropdown.
    expect(within(options).getAllByRole("button")).toHaveLength(7);
  });

  it("opens a vertical slash menu listing every command, filterable", async () => {
    const user = userEvent.setup();
    await openCopilot(user);

    const input = screen.getByTestId("chat-input");
    await user.click(input);
    await user.type(input, "/");

    const menu = await screen.findByTestId("slash-menu");
    expect(menu.className).toContain("flex-col");
    expect(within(menu).getAllByTestId("autocomplete-item")).toHaveLength(
      SLASH_COMMANDS.length,
    );

    await user.type(input, "bra");
    await waitFor(() =>
      expect(
        within(screen.getByTestId("slash-menu")).getAllByTestId(
          "autocomplete-item",
        ),
      ).toHaveLength(1),
    );
    expect(screen.getByTestId("slash-menu")).toHaveTextContent("/brainstorm");
  });

  it("opens a mention menu of documents when typing @", async () => {
    const user = userEvent.setup();
    await openCopilot(user);

    const input = screen.getByTestId("chat-input");
    await user.click(input);
    await user.type(input, "@");

    const menu = await screen.findByTestId("mention-menu");
    expect(menu).toHaveTextContent(MENTIONABLE[0].label);
  });

  it("reveals the task's regulatory profile — incl. task_type — with honest nulls", async () => {
    const user = userEvent.setup();
    await openCopilot(user);
    await answerIntent(user);
    await runViaChip(user, "Run /explore-task");

    const block = await waitFor(() => {
      const el = commandBlock("/explore-task");
      expect(el).toBeTruthy();
      return el!;
    }, THINKING_WAIT);

    await waitFor(
      () => expect(within(block).getByText("Task type")).toBeInTheDocument(),
      THINKING_WAIT,
    );
    for (const field of NODE_METADATA) {
      expect(within(block).getByText(field.label)).toBeInTheDocument();
    }
    // task_type is the first field, and honest nulls read "Not available".
    expect(NODE_METADATA[0].key).toBe("task_type");
    expect(NODE_METADATA.some((f) => f.value === null)).toBe(true);
    expect(within(block).getAllByText("Not available").length).toBeGreaterThan(0);
  });

  it("walks every clarification round (>=5) to an aligned understanding", async () => {
    const user = userEvent.setup();
    await openCopilot(user);

    expect(CLARIFICATION_QUESTIONS.length).toBeGreaterThanOrEqual(5);
    await answerIntent(user);
    await runViaChip(user, "Run /explore-task");
    await runViaChip(user, "Run /brainstorm");
    await answer(user, LEADING_OPTIONS[0], LEADING_OPTIONS[0]);

    // Options are stacked vertically, Claude-Code style.
    await screen.findByText(CLARIFICATION_QUESTIONS[0].prompt, undefined, THINKING_WAIT);
    expect(screen.getAllByTestId("clarification-options")[0].className).toContain(
      "flex-col",
    );

    for (const q of CLARIFICATION_QUESTIONS) {
      await answer(user, q.prompt, q.options[0]);
    }
    expect(await screen.findByText("Aligned ✓")).toBeInTheDocument();
  }, LONG_FLOW);

  it("reveals commands one at a time via suggestion chips", async () => {
    const user = userEvent.setup();
    await openCopilot(user);

    // Nothing downstream is shown up front.
    expect(commandBlock("/draft")).toBeUndefined();
    expect(commandBlock("/write")).toBeUndefined();

    await reachBrainstormDone(user);

    // The next step is offered as a chip; running it reveals its block.
    expect(commandBlock("/draft")).toBeUndefined();
    await runViaChip(user, "Run /draft");
    await waitFor(() => expect(commandBlock("/draft")).toBeTruthy());
  }, LONG_FLOW);

  it("auto-populates the full draft into the editor on /write, no insert buttons", async () => {
    const user = userEvent.setup();
    await openCopilot(user);
    await reachBuildDone(user);

    const surface = screen.getByTestId("draft-surface");
    const first = DRAFT_SECTIONS[0];
    const last = DRAFT_SECTIONS[DRAFT_SECTIONS.length - 1];
    await waitFor(() => {
      expect(surface).toHaveTextContent(first.title);
      expect(surface).toHaveTextContent(last.title);
    });
    // Provenance mark for text the drafter did not write.
    expect(surface.querySelector(".copilot-snippet")).not.toBeNull();
    // No manual per-section insert affordance anywhere.
    expect(
      screen.queryByRole("button", { name: /Insert into Editor/i }),
    ).not.toBeInTheDocument();
  }, LONG_FLOW);

  it("releases the draft to the task's owner, honestly with no reviewers", async () => {
    const user = userEvent.setup();
    await openCopilot(user);
    await reachBuildDone(user);

    await runViaChip(user, "Run /deliver");

    await screen.findByText(WORKSTREAM_CONTEXT.owner, undefined, THINKING_WAIT);
    expect(RELEASE_REVIEWERS).toHaveLength(0);
    expect(
      screen.getByText("No reviewers on file for this task yet."),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Send for review" }));

    // The confirmation shows both in the command status line and the panel.
    expect(
      (await screen.findAllByText(`Sent to ${WORKSTREAM_CONTEXT.owner}.`)).length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByRole("button", { name: "Send for review" }),
    ).not.toBeInTheDocument();
  }, LONG_FLOW);

  it("nudges toward a command on free-text input", async () => {
    const user = userEvent.setup();
    await openCopilot(user);

    const input = screen.getByTestId("chat-input");
    await user.click(input);
    await user.type(input, "how do i start");
    await user.keyboard("{Enter}");

    expect(await screen.findByText("how do i start")).toBeInTheDocument();
    expect(
      screen.getByText(/Type \/ to see every option/),
    ).toBeInTheDocument();
  });

  it("starts over to a fresh conversation", async () => {
    const user = userEvent.setup();
    await openCopilot(user);
    await answerIntent(user);

    await user.click(screen.getByRole("button", { name: "Start over" }));

    await waitFor(() => {
      // Back to just the greeting + intent question; the ack is gone.
      expect(screen.getByText("What are you drafting?")).toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: "Run /explore-task" }),
      ).not.toBeInTheDocument();
    });
  });
});

describe("DraftingWorkspacePage — tab switching", () => {
  it("does not unmount the editor, so the draft survives a round trip", async () => {
    const user = userEvent.setup();
    await loadWorkspace();
    const before = screen.getByTestId("draft-surface");

    await user.click(screen.getByRole("tab", { name: /Copilot/ }));
    await user.click(screen.getByRole("tab", { name: /Reviewed Findings/ }));

    expect(screen.getByTestId("draft-surface")).toBe(before);
    expect(screen.getByTestId("draft-surface")).toHaveTextContent(
      /at least annually/,
    );
  });

  it("keeps the Copilot conversation across a tab switch", async () => {
    const user = userEvent.setup();
    await loadWorkspace();
    await user.click(screen.getByRole("tab", { name: /Copilot/ }));
    await screen.findByTestId("copilot-chat");

    // Answer the intent so there is real conversation state to preserve.
    const promptEl = await screen.findByText("What are you drafting?");
    const card = promptEl.closest(
      '[data-testid="clarification-card"]',
    ) as HTMLElement;
    await user.click(
      within(card).getByRole("button", { name: COPILOT_INTENT_LABELS.PD }),
    );
    await screen.findByRole("button", { name: "Run /explore-task" });

    await user.click(screen.getByRole("tab", { name: /Reviewed Findings/ }));
    await user.click(screen.getByRole("tab", { name: /Copilot/ }));

    // The conversation is intact — not reset to a fresh greeting.
    expect(
      screen.getByRole("button", { name: "Run /explore-task" }),
    ).toBeInTheDocument();
  });
});

describe("DraftingWorkspacePage — wrong node type", () => {
  it("explains rather than rendering an editor for a non-task node", async () => {
    renderApp("/workstreams/opres-v2/tasks/bcbs-opres-2021/draft");
    expect(await screen.findByText(/is not a task/i)).toBeInTheDocument();
    expect(screen.queryByTestId("draft-surface")).not.toBeInTheDocument();
  });
});
