import { beforeEach, describe, it, expect } from "vitest";
import {
  cleanup,
  fireEvent,
  screen,
  within,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderApp } from "@/test/utils";
import { makeRecommendation, resetRecommendations } from "@/test/msw/handlers";
import { DRAFT_OUTLINE_SECTIONS } from "./copilotDraftOutline";
import {
  CLARIFICATION_QUESTIONS,
  LEADING_OPTIONS,
  MENTIONABLE,
  MISSING_FIELDS,
  NODE_METADATA,
  SLASH_COMMAND_IDS,
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
  it("renders the draft surface, three tabs, and the breadcrumb", async () => {
    await loadWorkspace();

    expect(
      screen.getByRole("heading", { name: "Operational Resilience PD — v0.3" }),
    ).toBeInTheDocument();
    // Back to the task the draft belongs to — where Open draft came from —
    // rather than all the way out to the graph.
    const back = screen.getByRole("link", { name: /← Task/ });
    expect(back).toHaveAttribute(
      "href",
      "/workstreams/opres-v2/tasks/opres-pd-v0-3",
    );
    for (const name of [/Recommendations/, /Playbook/, /Copilot/]) {
      expect(screen.getByRole("tab", { name })).toBeInTheDocument();
    }
    // Order is the point — Recommendations, Playbook, Copilot.
    expect(screen.getAllByRole("tab").map((t) => t.textContent)).toEqual([
      expect.stringContaining("Recommendations"),
      expect.stringContaining("Playbook"),
      expect.stringContaining("Copilot"),
    ]);
  });

  it("offers neither the retired Related nor the retired Reviewed tab", async () => {
    await loadWorkspace();

    expect(screen.getAllByRole("tab")).toHaveLength(3);
    expect(screen.queryByRole("tab", { name: /Related/ })).toBeNull();
    // Reviewed went on 1 Aug 2026: it duplicated the task screen, and accepted
    // findings now reach the draft as quoted evidence on a recommendation.
    expect(screen.queryByRole("tab", { name: /Reviewed/ })).toBeNull();
    expect(screen.queryByTestId("related-empty")).toBeNull();
    expect(
      screen.getAllByRole("tab").filter((t) => t.hasAttribute("disabled")),
    ).toHaveLength(0);
  });

  it("opens on the Recommendations tab", async () => {
    await loadWorkspace();
    expect(
      screen.getByRole("tab", { name: /Recommendations/ }),
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

  it("lets Bold/Italic/Underline be clicked with no selection, not just once text is selected", async () => {
    const user = userEvent.setup();
    await loadWorkspace();

    // Word-style sticky formatting — clicking Bold with the caret merely
    // collapsed (nothing selected) is not a no-op requiring selected text
    // first. execCommand/queryCommandState are real-browser APIs jsdom
    // doesn't implement, so the actual toggle-then-type behaviour is
    // covered by manual verification, not this unit test; what's checked
    // here is that the buttons are enabled and clickable either way.
    const boldButton = screen.getByRole("button", { name: "B" });
    expect(boldButton).not.toBeDisabled();
    await user.click(boldButton);
    expect(boldButton).not.toBeDisabled();
  });
});

describe("DraftingWorkspacePage — Recommendations tab", () => {
  beforeEach(() => resetRecommendations());

  it("points at the task page when nothing has been generated", async () => {
    await loadWorkspace();

    expect(await screen.findByTestId("tab-not-generated")).toHaveTextContent(
      /Generate them in the Recommendations card on the task page/i,
    );
  });

  it("asks for a bookmark when recommendations exist but none is marked", async () => {
    resetRecommendations({
      nextBatch: [makeRecommendation()],
      generatedAt: "2026-08-02T09:14:22Z",
    });
    await loadWorkspace();
    // A generated-but-unbookmarked set is a different state from no set at all,
    // and needs a different instruction — pick, not generate.
    await userEvent.click(screen.getByRole("tab", { name: /Recommendations/ }));

    expect(await screen.findByTestId("tab-none-bookmarked")).toHaveTextContent(
      /Bookmark a recommendation on the task page/i,
    );
  });

  it("shows only the bookmarked recommendations, and counts them", async () => {
    resetRecommendations({
      nextBatch: [
        makeRecommendation({
          id: "kept",
          title: "Taken forward",
          bookmarked: true,
        }),
        makeRecommendation({ id: "passed", title: "Passed over" }),
      ],
      generatedAt: "2026-08-02T09:14:22Z",
    });
    await loadWorkspace();

    const cards = await screen.findAllByTestId("draft-recommendation");
    expect(cards).toHaveLength(1);
    expect(cards[0]).toHaveAttribute("data-rec-id", "kept");
    expect(screen.queryByText("Passed over")).not.toBeInTheDocument();
    // The badge counts what she is carrying forward, not the whole set.
    expect(screen.getByTestId("count-recommendations")).toHaveTextContent("1");
  });

  it("quotes the clause a bookmarked recommendation rests on", async () => {
    resetRecommendations({
      nextBatch: [makeRecommendation({ bookmarked: true })],
      generatedAt: "2026-08-02T09:14:22Z",
    });
    await loadWorkspace();
    const card = await screen.findByTestId("draft-recommendation");

    await userEvent.click(within(card).getByTestId("tab-citations-toggle"));

    expect(within(card).getByTestId("tab-citations")).toHaveTextContent(
      /An AI should publish on its website a list of all TSPs/,
    );
    expect(within(card).getByTestId("tab-citations")).toHaveTextContent("4.2");
  });

  it("offers no way to write to the draft", async () => {
    // The story's defining constraint: everything that reaches the page arrives
    // through the Copilot conversation, where it is reviewed.
    resetRecommendations({
      nextBatch: [makeRecommendation({ bookmarked: true })],
      generatedAt: "2026-08-02T09:14:22Z",
    });
    await loadWorkspace();
    const card = await screen.findByTestId("draft-recommendation");

    expect(
      within(card).queryByRole("button", {
        name: /draft this|insert|add to draft/i,
      }),
    ).not.toBeInTheDocument();
  });

  it("unbookmarks from beside the draft", async () => {
    resetRecommendations({
      nextBatch: [makeRecommendation({ id: "kept", bookmarked: true })],
      generatedAt: "2026-08-02T09:14:22Z",
    });
    await loadWorkspace();
    const card = await screen.findByTestId("draft-recommendation");

    await userEvent.click(within(card).getByTestId("unbookmark"));

    await waitFor(() =>
      expect(screen.getByTestId("tab-none-bookmarked")).toBeInTheDocument(),
    );
  });

  it("reports the accepted findings no recommendation drew on", async () => {
    resetRecommendations({
      nextBatch: [makeRecommendation({ bookmarked: true })],
      generatedAt: "2026-08-02T09:14:22Z",
      acceptedCount: 30,
      unreflected: [
        {
          finding_id: "f-uncited-1",
          edge_id: "e-bis_papers_168--ed_open_finance_2025",
          label: "differs-on",
          sentiment: "tighten",
          summary: "A fixed rollout date where BIS observes flexibility.",
          left: { id: "bis-papers-168", title: "BIS Papers 168" },
          right: { id: "ed-open-finance-2025", title: "ED Open Finance 2025" },
          source_clause_number: "3.1",
          source_clause_text:
            "Jurisdictions may adopt a facilitative approach.",
          target_clause_number: "14.2",
          target_clause_text:
            "Phase one obligations take effect 1 January 2027.",
        },
      ],
    });
    await loadWorkspace();

    const note = await screen.findByTestId("tab-not-yet-reflected");
    // Measured against every generated recommendation, so the figure means the
    // same thing here as on the task screen.
    expect(note).toHaveAttribute("data-count", "1");
    expect(note).toHaveTextContent(/1 of 30 accepted findings/);
  });
});

describe("DraftingWorkspacePage — Playbook tab", () => {
  beforeEach(() => resetRecommendations());

  it("offers one section per Copilot stage, in flow order", async () => {
    await loadWorkspace();
    await userEvent.click(screen.getByRole("tab", { name: /Playbook/ }));

    const sections = await screen.findAllByTestId("playbook-section");
    expect(sections.map((s) => s.getAttribute("data-stage"))).toEqual([
      "/explore-task",
      "/brainstorm",
      "/draft",
      "/write",
      "/deliver",
    ]);
  });

  it("locks the explore-task stage with no editable control at all", async () => {
    await loadWorkspace();
    await userEvent.click(screen.getByRole("tab", { name: /Playbook/ }));
    await screen.findAllByTestId("playbook-section");

    const locked = screen
      .getAllByTestId("playbook-section")
      .find((s) => s.getAttribute("data-stage") === "/explore-task")!;

    // Not a DISABLED textarea — none at all. A disabled field still reads as
    // something that might one day be filled in.
    expect(within(locked).queryByRole("textbox")).not.toBeInTheDocument();
    expect(
      within(locked).getByTestId("explore-task-locked"),
    ).toBeInTheDocument();
    expect(
      within(locked).getByRole("link", { name: /regulatory profile/i }),
    ).toBeInTheDocument();
  });

  it("only enables Save once a section is edited", async () => {
    await loadWorkspace();
    await userEvent.click(screen.getByRole("tab", { name: /Playbook/ }));
    await screen.findAllByTestId("playbook-section");

    expect(screen.getByTestId("playbook-save")).toBeDisabled();

    const write = screen
      .getAllByTestId("playbook-input")
      .find((el) => el.getAttribute("data-section") === "write")!;
    await userEvent.type(write, "Obligations read must.");

    expect(screen.getByTestId("playbook-save")).toBeEnabled();
  });

  it("saves what the drafter typed and keeps it", async () => {
    await loadWorkspace();
    await userEvent.click(screen.getByRole("tab", { name: /Playbook/ }));
    await screen.findAllByTestId("playbook-section");
    const write = screen
      .getAllByTestId("playbook-input")
      .find((el) => el.getAttribute("data-section") === "write")!;

    await userEvent.type(write, "Guidance reads should.");
    await userEvent.click(screen.getByTestId("playbook-save"));

    await waitFor(() =>
      expect(screen.getByTestId("playbook-save")).toBeDisabled(),
    );
    expect(write).toHaveValue("Guidance reads should.");
  });

  it("shows the template picker on /draft and says it does nothing", async () => {
    await loadWorkspace();
    await userEvent.click(screen.getByRole("tab", { name: /Playbook/ }));
    await screen.findAllByTestId("playbook-section");

    const draftSection = screen
      .getAllByTestId("playbook-section")
      .find((s) => s.getAttribute("data-stage") === "/draft")!;
    expect(
      within(draftSection).getByTestId("playbook-upload"),
    ).toBeInTheDocument();

    // Deliberately inert — selecting a file must not upload or store anything.
    const input = within(draftSection).getByTestId("playbook-upload-input");
    await userEvent.upload(
      input as HTMLInputElement,
      new File(["x"], "house-template.docx"),
    );

    expect(
      within(draftSection).getByTestId("playbook-upload-note"),
    ).toHaveTextContent(/not wired up in this build/i);
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

  it(
    "skips stage by stage to the delivered draft, same end state as walking it",
    async () => {
      const user = userEvent.setup();
      await openCopilot(user);

      // The button names the stage it acts on, advancing one per click.
      for (const stage of SLASH_COMMAND_IDS) {
        const skip = await screen.findByTestId("skip-stage");
        expect(skip).toHaveAccessibleName(`Skip ${stage}`);
        await user.click(skip);
      }

      // Every stage completed, so the skip button retires.
      await waitFor(() => {
        expect(screen.queryByTestId("skip-stage")).not.toBeInTheDocument();
      });

      // The full Open Finance PD is in the editor — the same document /write
      // produces, marked as Copilot-written text.
      const surface = screen.getByTestId("draft-surface");
      expect(surface).toHaveTextContent(DRAFT_OUTLINE_SECTIONS[0].title);
      expect(surface).toHaveTextContent(
        DRAFT_OUTLINE_SECTIONS[DRAFT_OUTLINE_SECTIONS.length - 1].title,
      );
      expect(surface.querySelector(".copilot-snippet")).not.toBeNull();

      // Landed on /deliver's send panel, still un-sent with no fabricated
      // recipient — skipping the flow never skips the drafter's own call.
      const block = commandBlock("/deliver")!;
      expect(
        (within(block).getByLabelText("Recipient name") as HTMLInputElement)
          .value,
      ).toBe("");
      expect(
        within(block).getByRole("button", { name: "Send for Review" }),
      ).toBeDisabled();
    },
    LONG_FLOW,
  );

  it("skipping /explore-task leaves unresolvable fields honestly null", async () => {
    const user = userEvent.setup();
    await openCopilot(user);

    await user.click(await screen.findByTestId("skip-stage"));

    // Nothing filled those three fields, so they must read "Not available"
    // rather than a guessed value — the skip unblocks the flow, it never
    // invents metadata the document does not carry.
    const block = await waitFor(() => {
      const el = commandBlock("/explore-task");
      expect(el).toBeTruthy();
      return el!;
    }, THINKING_WAIT);
    expect(within(block).getAllByText("Not available").length).toBe(
      MISSING_FIELDS.length,
    );
    // The form is still offered, so a skipped stage can be completed properly.
    expect(
      within(block).getByTestId("missing-fields-form"),
    ).toBeInTheDocument();
  });

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
    await user.click(screen.getByRole("tab", { name: /Recommendations/ }));

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

    await user.click(screen.getByRole("tab", { name: /Playbook/ }));
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

describe("DraftingWorkspacePage — a configured stage names its section", () => {
  beforeEach(() => resetRecommendations());

  /** Walk the gated flow far enough to unlock /brainstorm: run /explore-task and
   *  submit the missing-fields form it raises. */
  async function reachBrainstorm(user: ReturnType<typeof userEvent.setup>) {
    await user.click(screen.getByRole("tab", { name: /Copilot/ }));
    await screen.findByTestId("copilot-chat");
    await user.click(screen.getByRole("button", { name: "Explore Task" }));

    const form = await screen.findByTestId(
      "missing-fields-form",
      undefined,
      THINKING_WAIT,
    );
    for (const field of MISSING_FIELDS) {
      await user.type(
        within(form).getByLabelText(field.label),
        `Test value for ${field.key}`,
      );
    }
    await user.click(within(form).getByRole("button", { name: "Submit" }));

    const chip = await screen.findByRole(
      "button",
      { name: "Run /brainstorm" },
      THINKING_WAIT,
    );
    await user.click(chip);
  }

  it("names the /brainstorm section when it runs, and only that section", async () => {
    // The five stages are a scripted demo, so a configured stage cannot literally
    // obey the instruction — it names it, which is the honest observable
    // behaviour here. The live path is the engine's system-prompt injection,
    // covered by engine/tests/test_api_playbook.py.
    resetRecommendations({
      playbook: {
        brainstorm: "Should consent expiry differ for business customers?",
        draft: "DRAFT_ONLY_MARKER",
        write: "",
        deliver: "",
      },
    });
    const user = userEvent.setup();
    await loadWorkspace();

    await reachBrainstorm(user);

    expect(
      await screen.findByText(
        /Following your Playbook for \/brainstorm/i,
        undefined,
        THINKING_WAIT,
      ),
    ).toHaveTextContent(/consent expiry differ for business customers/);
    // /draft's section must not leak into /brainstorm.
    expect(screen.queryByText(/DRAFT_ONLY_MARKER/)).not.toBeInTheDocument();
  });

  it("says nothing when the section is empty", async () => {
    const user = userEvent.setup();
    await loadWorkspace();

    await reachBrainstorm(user);

    // An unconfigured stage behaves exactly as it did before playbooks existed —
    // no acknowledgement, no warning.
    expect(
      screen.queryByText(/Following your Playbook/i),
    ).not.toBeInTheDocument();
  });
});
