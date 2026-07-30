import { describe, it, expect } from "vitest";
import {
  cleanup,
  fireEvent,
  screen,
  within,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderApp } from "@/test/utils";
import { DRAFT_OUTLINE_SECTIONS } from "./copilotDraftOutline";
import {
  CLARIFICATION_QUESTIONS,
  LEADING_OPTIONS,
  MENTIONABLE,
  MISSING_FIELDS,
  NODE_METADATA,
  SLASH_COMMANDS,
} from "./copilotV2Data";

const THINKING_WAIT = { timeout: 8000 };
// The scripted brainstorming flow (silent context pull + six clarification
// rounds) runs several seconds of real timers — past vitest's 5s default.
const LONG_FLOW = 25000;

const DRAFT_URL = "/workstreams/opres-v2/tasks/opres-pd-v0-3/draft";
const BCBS_EDGE = "e-opres_v0_3--bcbs_opres_2021";
const HKMA_EDGE = "e-opres_v0_3--hkma_spm_or2";

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
  // By label, not position: the review screen orders cards by attention
  // (conflicts-with → … → aligns-with), so index 0 is not the aligns-with
  // finding on OpRes PD 4.4 that the assertions below are about.
  await screen.findAllByTestId("finding-card");
  const card = screen
    .getAllByTestId("finding-card")
    .find((c) => c.getAttribute("data-label") === "aligns-with")!;
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
  it("renders the draft surface, two tabs, and the breadcrumb", async () => {
    await loadWorkspace();

    expect(
      screen.getByRole("heading", { name: "Operational Resilience PD — v0.3" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /Workstream graph/i }),
    ).toBeInTheDocument();
    for (const name of [/Reviewed/, /Copilot/]) {
      expect(screen.getByRole("tab", { name })).toBeInTheDocument();
    }
  });

  it("no longer offers the Related · 1 hop tab, and leaves no placeholder", async () => {
    await loadWorkspace();

    expect(screen.getAllByRole("tab")).toHaveLength(2);
    expect(screen.queryByRole("tab", { name: /Related/ })).toBeNull();
    expect(screen.queryByTestId("related-empty")).toBeNull();
    // No disabled stand-in for the future Recommendations tab either.
    expect(
      screen.getAllByRole("tab").filter((t) => t.hasAttribute("disabled")),
    ).toHaveLength(0);
  });

  it("opens on the Reviewed tab", async () => {
    await loadWorkspace();
    expect(screen.getByRole("tab", { name: /Reviewed/ })).toHaveAttribute(
      "aria-selected",
      "true",
    );
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

  it("enables Bold/Italic/Underline once text is selected in the editor", async () => {
    const user = userEvent.setup();
    await loadWorkspace();

    const surface = screen.getByTestId("draft-surface");
    const boldButton = screen.getByRole("button", { name: "B" });
    expect(boldButton).toBeDisabled();

    // Select the clause text already rendered in the surface.
    const range = document.createRange();
    range.selectNodeContents(surface);
    const selection = window.getSelection();
    selection?.removeAllRanges();
    selection?.addRange(range);
    await user.pointer([{ target: surface }]); // fires mouseup on the surface
    fireEvent.mouseUp(surface);

    await waitFor(() => expect(boldButton).not.toBeDisabled());
  });
});

describe("DraftingWorkspacePage — Reviewed tab", () => {
  it("is empty until something is accepted, and points at the box", async () => {
    await loadWorkspace();
    expect(screen.getByTestId("count-reviewed")).toHaveTextContent("0");
    expect(screen.getByText(/No findings accepted yet/i)).toBeInTheDocument();
    // Names where acceptance now happens, not just "the review screen".
    expect(
      screen.getByText(/Pairwise findings box on the task page/i),
    ).toBeInTheDocument();
  });

  it("shows a linkage accepted on the review screen, and counts it", async () => {
    const user = userEvent.setup();
    await acceptOnReviewScreen(user);

    await loadWorkspace();

    const cards = await screen.findAllByTestId("linkage-ref-card");
    expect(cards).toHaveLength(1);
    expect(cards[0]).toHaveAttribute("data-label", "aligns-with");
    expect(cards[0]).toHaveTextContent("BCBS OpRes 2021");
    expect(screen.getByTestId("count-reviewed")).toHaveTextContent("1");
  });

  it("does not show a dismissed finding", async () => {
    const user = userEvent.setup();
    renderApp(`/workstreams/opres-v2/edges/${BCBS_EDGE}/review`);
    const card = (await screen.findAllByTestId("finding-card"))[0];
    await user.click(within(card).getByRole("button", { name: "Dismiss" }));
    await waitFor(() =>
      expect(screen.getByTestId("count-dismissed")).toHaveTextContent(
        "1 dismissed",
      ),
    );
    cleanup();

    await loadWorkspace();

    expect(screen.queryByTestId("linkage-ref-card")).not.toBeInTheDocument();
    expect(screen.getByTestId("count-reviewed")).toHaveTextContent("0");
  });

  it("opens the comparison on the clicked finding", async () => {
    const user = userEvent.setup();
    await acceptOnReviewScreen(user);
    await loadWorkspace();

    const card = (await screen.findAllByTestId("linkage-ref-card"))[0];
    await user.click(within(card).getByText(/Dependency mapping/));

    // Lands on the comparison for that pair, with the clicked finding selected
    // rather than the pair's first.
    expect(
      await screen.findByRole("heading", {
        name: /Operational Resilience PD — v0.3 ↔ BCBS OpRes 2021/,
      }),
    ).toBeInTheDocument();
    const active = screen
      .getAllByTestId("finding-card")
      .find((c) => c.getAttribute("data-active") === "true");
    expect(active).toHaveTextContent(/Dependency mapping/);
  });

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

describe("DraftingWorkspacePage — the neighbourhood widening", () => {
  /** Accept a finding on an edge that does NOT touch the task node. Before the
   *  widening this acceptance was recorded and then invisible in the workspace —
   *  the defect the epic exists to fix. `opres-v2` has no anchor↔anchor edges, so
   *  the second task node's edge is the available second-order case. */
  async function acceptOnASecondOrderEdge(
    user: ReturnType<typeof userEvent.setup>,
  ) {
    renderApp(`/workstreams/opres-v2/edges/${HKMA_EDGE}/review`);
    const card = (await screen.findAllByTestId("finding-card"))[0];
    await user.click(within(card).getByRole("button", { name: "Accept" }));
    await waitFor(() =>
      expect(screen.getByTestId("count-accepted")).toHaveTextContent(
        "1 accepted",
      ),
    );
    cleanup();
  }

  it("lists an acceptance made on a pair the draft is not part of", async () => {
    const user = userEvent.setup();
    await acceptOnASecondOrderEdge(user);
    await loadWorkspace();

    const cards = await screen.findAllByTestId("linkage-ref-card");
    expect(cards).toHaveLength(1);
    expect(cards[0]).toHaveAttribute("data-edge-id", HKMA_EDGE);
    expect(screen.getByTestId("count-reviewed")).toHaveTextContent("1");
  });

  it("names both documents on every card", async () => {
    const user = userEvent.setup();
    await acceptOnASecondOrderEdge(user);
    await loadWorkspace();

    const card = (await screen.findAllByTestId("linkage-ref-card"))[0];
    // Cards now arrive from across the neighbourhood, so a single title would
    // leave the drafter unable to tell one pair's finding from another's.
    expect(card).toHaveTextContent("Operational Resilience PD — v0.3");
    expect(card).toHaveTextContent("HKMA SPM OR-2");
  });
});

describe("DraftingWorkspacePage — withdrawing an acceptance", () => {
  it("removes the card, decrements the badge, and returns it to the box", async () => {
    const user = userEvent.setup();
    await acceptOnReviewScreen(user);
    await loadWorkspace();

    const card = (await screen.findAllByTestId("linkage-ref-card"))[0];
    expect(screen.getByTestId("count-reviewed")).toHaveTextContent("1");

    await user.click(within(card).getByRole("button", { name: /Withdraw/ }));

    await waitFor(() =>
      expect(screen.queryByTestId("linkage-ref-card")).not.toBeInTheDocument(),
    );
    expect(screen.getByTestId("count-reviewed")).toHaveTextContent("0");

    // Back to pending on the task page — one decision, everywhere.
    cleanup();
    renderApp("/workstreams/opres-v2/tasks/opres-pd-v0-3");
    await screen.findAllByTestId("finding-group");
    const onTaskPage = screen
      .getAllByTestId("finding-card")
      .find((c) => c.dataset.edgeId === BCBS_EDGE);
    expect(onTaskPage).toHaveAttribute("data-review-state", "pending");
  });

  it("offers no accept or dismiss control — withdrawal only", async () => {
    const user = userEvent.setup();
    await acceptOnReviewScreen(user);
    await loadWorkspace();

    const panel = screen.getByLabelText("Reviewed linkages");
    expect(
      within(panel).getByRole("button", { name: /Withdraw/ }),
    ).toBeInTheDocument();
    expect(within(panel).queryByRole("button", { name: /^Accept/ })).toBeNull();
    expect(
      within(panel).queryByRole("button", { name: /^Dismiss/ }),
    ).toBeNull();
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

  /** Fill and submit the /explore-task missing-fields form — a prerequisite
   *  for the /brainstorm suggestion chip to appear. */
  async function fillMissingFields(user: ReturnType<typeof userEvent.setup>) {
    const form = await screen.findByTestId(
      "missing-fields-form",
      undefined,
      THINKING_WAIT,
    );
    for (const f of MISSING_FIELDS) {
      await user.type(
        within(form).getByLabelText(f.label),
        `Test value for ${f.key}`,
      );
    }
    await user.click(within(form).getByRole("button", { name: "Submit" }));
  }

  /** From a fresh chat, run brainstorming and walk every clarification round,
   *  leaving the flow with the "Run /draft" chip visible. */
  async function reachBrainstormDone(user: ReturnType<typeof userEvent.setup>) {
    await user.click(screen.getByRole("button", { name: "Explore Task" }));
    await fillMissingFields(user);
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
    await screen.findByTestId("write-banner", undefined, THINKING_WAIT);
  }

  it("opens on a welcome screen with a five-step flow, no intent question", async () => {
    const user = userEvent.setup();
    await openCopilot(user);

    expect(screen.getByTestId("copilot-chat")).toBeInTheDocument();
    expect(screen.getByTestId("chat-input")).toBeInTheDocument();
    expect(screen.getByTestId("copilot-welcome")).toBeInTheDocument();

    const actions = screen.getAllByTestId("welcome-quick-action");
    expect(actions).toHaveLength(5);
    expect(actions[0]).toHaveTextContent("Explore Task");
    expect(actions[1]).toHaveTextContent("Brainstorm");
    expect(actions[2]).toHaveTextContent("Draft Outline");
    expect(actions[3]).toHaveTextContent("Write Document");
    expect(actions[4]).toHaveTextContent("Deliver");
    expect(
      screen.queryByText("What are you drafting?"),
    ).not.toBeInTheDocument();
  });

  it("running a quick action starts the conversation and hides the welcome screen", async () => {
    const user = userEvent.setup();
    await openCopilot(user);

    await user.click(screen.getByRole("button", { name: "Explore Task" }));

    expect(screen.queryByTestId("copilot-welcome")).not.toBeInTheDocument();
    await screen.findByTestId("command-step", undefined, THINKING_WAIT);
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

  it("does nothing when a locked command is picked or typed out of order", async () => {
    const user = userEvent.setup();
    await openCopilot(user);

    const input = screen.getByTestId("chat-input");
    await user.click(input);
    await user.type(input, "/write");
    await user.keyboard("{Enter}");

    // The command is listed and typeable, but running it before its
    // prerequisites are met simply does nothing — no command starts, the
    // welcome screen is still showing, nothing was echoed.
    expect(screen.getByTestId("copilot-welcome")).toBeInTheDocument();
    expect(screen.queryByTestId("command-step")).not.toBeInTheDocument();
    expect(screen.queryByTestId("user-msg")).not.toBeInTheDocument();
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
    await user.click(screen.getByRole("button", { name: "Explore Task" }));

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
      // getAllByText: the missing-fields form (rendered alongside, before
      // submission) repeats the same label text for each null field.
      expect(within(block).getAllByText(field.label).length).toBeGreaterThan(0);
    }
    // task_type is the first field, and honest nulls read "Not available".
    expect(NODE_METADATA[0].key).toBe("task_type");
    expect(NODE_METADATA.some((f) => f.value === null)).toBe(true);
    expect(within(block).getAllByText("Not available").length).toBeGreaterThan(
      0,
    );
  });

  it("shows a missing-fields form after /explore-task, and resolves nulls on submit", async () => {
    const user = userEvent.setup();
    await openCopilot(user);
    await user.click(screen.getByRole("button", { name: "Explore Task" }));

    const block = await waitFor(() => {
      const el = commandBlock("/explore-task");
      expect(el).toBeTruthy();
      return el!;
    }, THINKING_WAIT);
    // Wait past the metadata-reveal timer before inspecting field content.
    await waitFor(
      () => expect(within(block).getByText("Task type")).toBeInTheDocument(),
      THINKING_WAIT,
    );
    const nullFieldLabels = NODE_METADATA.filter((f) => f.value === null).map(
      (f) => f.label,
    );
    expect(nullFieldLabels.length).toBeGreaterThan(0);
    for (const label of nullFieldLabels) {
      expect(
        within(block).getAllByText("Not available").length,
      ).toBeGreaterThan(0);
    }

    await fillMissingFields(user);

    await waitFor(() => {
      expect(
        screen.queryByTestId("missing-fields-form"),
      ).not.toBeInTheDocument();
    });
    expect(within(block).queryAllByText("Not available")).toHaveLength(0);
    await screen.findByRole(
      "button",
      { name: "Run /brainstorm" },
      THINKING_WAIT,
    );
  }, 15000);

  it(
    "walks every clarification round (>=5) to an aligned understanding",
    async () => {
      const user = userEvent.setup();
      await openCopilot(user);

      expect(CLARIFICATION_QUESTIONS.length).toBeGreaterThanOrEqual(5);
      await user.click(screen.getByRole("button", { name: "Explore Task" }));
      await fillMissingFields(user);
      await runViaChip(user, "Run /brainstorm");
      await answer(user, LEADING_OPTIONS[0], LEADING_OPTIONS[0]);

      // Options are stacked vertically, Claude-Code style.
      await screen.findByText(
        CLARIFICATION_QUESTIONS[0].prompt,
        undefined,
        THINKING_WAIT,
      );
      expect(
        screen.getAllByTestId("clarification-options")[0].className,
      ).toContain("flex-col");

      for (const q of CLARIFICATION_QUESTIONS) {
        await answer(user, q.prompt, q.options[0]);
      }
      expect(await screen.findByText("Aligned ✓")).toBeInTheDocument();
    },
    LONG_FLOW,
  );

  it(
    "reveals commands one at a time via suggestion chips",
    async () => {
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
    },
    LONG_FLOW,
  );

  it("renders and inserts the instructional draft outline on /draft", async () => {
    const user = userEvent.setup();
    await openCopilot(user);
    await reachBrainstormDone(user);
    await runViaChip(user, "Run /draft");

    const cards = await screen.findAllByTestId(
      "draft-instruction-card",
      undefined,
      THINKING_WAIT,
    );
    expect(cards).toHaveLength(DRAFT_OUTLINE_SECTIONS.length);
    expect(cards[0]).toHaveTextContent("Executive Summary");

    const surface = screen.getByTestId("draft-surface");
    await waitFor(() => {
      expect(surface.querySelectorAll(".draft-guidance-block").length).toBe(
        DRAFT_OUTLINE_SECTIONS.length,
      );
    });
  }, 25000);

  it(
    "writes the full document into the editor on /write, no insert buttons",
    async () => {
      const user = userEvent.setup();
      await openCopilot(user);
      await reachBuildDone(user);

      const surface = screen.getByTestId("draft-surface");
      const first = DRAFT_OUTLINE_SECTIONS[0];
      const last = DRAFT_OUTLINE_SECTIONS[DRAFT_OUTLINE_SECTIONS.length - 1];
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

      const banner = await screen.findByTestId("write-banner");
      expect(banner).toHaveTextContent(
        "This draft has been inserted into the editor. You may edit it directly.",
      );
      await user.click(within(banner).getByRole("button", { name: "Dismiss" }));
      expect(screen.queryByTestId("write-banner")).not.toBeInTheDocument();
    },
    LONG_FLOW,
  );

  it(
    "delivers the draft to a recipient the drafter names themselves",
    async () => {
      const user = userEvent.setup();
      await openCopilot(user);
      await reachBuildDone(user);

      await runViaChip(user, "Run /deliver");

      const block = await waitFor(() => {
        const el = commandBlock("/deliver");
        expect(el).toBeTruthy();
        return el!;
      }, THINKING_WAIT);

      // No fabricated default recipient — every field starts empty and "Send
      // for Review" is disabled until the drafter names someone.
      const nameInput = within(block).getByLabelText(
        "Recipient name",
      ) as HTMLInputElement;
      const emailInput = within(block).getByLabelText(
        "Recipient email",
      ) as HTMLInputElement;
      expect(nameInput.value).toBe("");
      expect(emailInput.value).toBe("");
      expect(
        within(block).getByRole("button", { name: "Send for Review" }),
      ).toBeDisabled();

      await user.type(nameInput, "Jarod N.");
      await user.type(
        within(block).getByLabelText("Recipient role"),
        "Policy Owner, Open Finance Division",
      );
      await user.type(emailInput, "jarod.ng@bnm.gov.my");
      await user.click(
        within(block).getByRole("button", { name: "Send for Review" }),
      );

      expect(
        (
          await screen.findAllByText(
            "Draft submitted to Jarod N. (jarod.ng@bnm.gov.my) for review.",
          )
        ).length,
      ).toBeGreaterThan(0);
      expect(
        (await screen.findAllByText("Sent to Jarod N. (jarod.ng@bnm.gov.my)."))
          .length,
      ).toBeGreaterThan(0);
      expect(
        screen.queryByRole("button", { name: "Send for Review" }),
      ).not.toBeInTheDocument();
    },
    LONG_FLOW,
  );

  it("nudges toward a command on free-text input", async () => {
    const user = userEvent.setup();
    await openCopilot(user);

    const input = screen.getByTestId("chat-input");
    await user.click(input);
    await user.type(input, "how do i start");
    await user.keyboard("{Enter}");

    expect(await screen.findByText("how do i start")).toBeInTheDocument();
    expect(screen.getByText(/Type \/ to see every option/)).toBeInTheDocument();
  });

  it("starts over to a fresh conversation", async () => {
    const user = userEvent.setup();
    await openCopilot(user);
    await user.click(screen.getByRole("button", { name: "Explore Task" }));
    await screen.findByTestId("command-step", undefined, THINKING_WAIT);

    await user.click(screen.getByRole("button", { name: "Start over" }));

    await waitFor(() => {
      expect(screen.getByTestId("copilot-welcome")).toBeInTheDocument();
      expect(screen.queryByTestId("command-step")).not.toBeInTheDocument();
    });
  });
});

describe("DraftingWorkspacePage — tab switching", () => {
  it("does not unmount the editor, so the draft survives a round trip", async () => {
    const user = userEvent.setup();
    await loadWorkspace();
    const before = screen.getByTestId("draft-surface");

    await user.click(screen.getByRole("tab", { name: /Copilot/ }));
    await user.click(screen.getByRole("tab", { name: /Reviewed/ }));

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

    await user.click(screen.getByRole("button", { name: "Explore Task" }));
    await screen.findByTestId("command-step", undefined, THINKING_WAIT);

    await user.click(screen.getByRole("tab", { name: /Reviewed/ }));
    await user.click(screen.getByRole("tab", { name: /Copilot/ }));

    // The conversation is intact — not reset to the welcome screen.
    expect(screen.queryByTestId("copilot-welcome")).not.toBeInTheDocument();
    expect(screen.getByTestId("command-step")).toBeInTheDocument();
  });
});

describe("DraftingWorkspacePage — wrong node type", () => {
  it("explains rather than rendering an editor for a non-task node", async () => {
    renderApp("/workstreams/opres-v2/tasks/bcbs-opres-2021/draft");
    expect(await screen.findByText(/is not a task/i)).toBeInTheDocument();
    expect(screen.queryByTestId("draft-surface")).not.toBeInTheDocument();
  });
});
