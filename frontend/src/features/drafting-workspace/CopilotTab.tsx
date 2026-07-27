import { useRef, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  FilePlus2,
  FileText,
  Globe,
  PenLine,
  RotateCcw,
  Send,
} from "lucide-react";
import {
  COPILOT_INTENTS,
  COPILOT_INTENT_LABELS,
  type CopilotDraftContext,
  type CopilotIntent,
  type LinkageCard,
} from "@/lib/types";

interface CopilotTabProps {
  workstreamId: string;
  nodeId: string;
  onInsertSnippet: (html: string) => void;
  /** The drafter's already-accepted findings for this task. Retained on the
   *  props contract; unused by this static demo panel. */
  reviewedCards: LinkageCard[];
  /** Reads the drafter's live editor content + current highlighted selection.
   *  Retained on the contract; unused by this static demo panel. */
  getDraftContext: () => CopilotDraftContext;
}

/** A canned Copilot reply. `snippet` is the HTML the drafter can drop into the
 *  editor at their cursor; `followups` are suggested next prompts the Copilot
 *  surfaces under its answer. */
interface Reply {
  title: string;
  body: string;
  snippet?: string;
  followups?: string[];
}

type Turn = { role: "user"; text: string } | { role: "copilot"; reply: Reply };

/** Status badge styling for a benchmark card. */
const BADGE_STYLES: Record<string, string> = {
  Aligned: "bg-emerald-500/15 text-emerald-800 border-emerald-400/30",
  "Gap detected": "bg-amber-400/15 text-amber-800 border-amber-300/30",
  Deviation: "bg-red-500/15 text-red-800 border-red-400/30",
};

/** Finding-label pill styling, reusing the taxonomy's colours. */
const TAG_STYLES: Record<string, string> = {
  "conflicts-with": "bg-red-500/15 text-red-800 border-red-400/30",
  "silent-on": "bg-amber-400/15 text-amber-800 border-amber-300/30",
  "aligns-with": "bg-emerald-500/15 text-emerald-800 border-emerald-400/30",
};

// Reusable drafted clauses, grounded in the workstream's anchor documents.
const GOV_SNIPPET =
  "<h3>Governance &amp; Accountability</h3><p>The board shall approve the operational resilience framework and designate a single accountable officer responsible for its implementation, consistent with BCM PD 8.1–8.3 and Recovery Planning PD 12.3.</p>";
const REPORTING_SNIPPET =
  "<h3>Reporting Requirements</h3><p>A financial institution shall submit a semi-annual operational resilience self-assessment to the Bank, and notify the Bank without delay upon activation of any recovery or continuity plan.</p>";
const CBF_SNIPPET =
  "<h3>Critical Business Functions</h3><p>For the purposes of this policy, a critical business function is (a) an operational function whose disruption would materially impair the institution's delivery of critical operations; and (b) a function whose failure would disrupt the real economy or financial stability.</p>";
const SCENARIO_SNIPPET =
  "<h3>Scenario Testing</h3><p>A financial institution shall conduct scenario testing of its operational resilience arrangements at least annually, covering severe but plausible disruption scenarios.</p>";
const OUTLINE_SNIPPET =
  "<h3>Policy Document — Outline</h3><ul><li>1. Policy Objectives &amp; Legal Basis</li><li>2. Scope of Application</li><li>3. Governance &amp; Accountability</li><li>4. Critical Business Functions &amp; Impact Tolerance</li><li>5. Recovery &amp; Continuity Planning</li><li>6. Reporting &amp; Supervisory Submissions</li><li>7. Enforcement &amp; Supervisory Expectations</li></ul>";
const RTO_SNIPPET =
  "<h3>Recovery Time Objectives</h3><p>A financial institution shall establish recovery time and recovery point objectives for each critical business function, calibrated to its institution tier.</p>";
const ENFORCE_SNIPPET =
  "<h3>Enforcement &amp; Supervisory Expectations</h3><p>The Bank may take supervisory action on a tiered basis — advisory notice, formal direction, and financial penalty — proportionate to the severity of non-compliance.</p>";
const GENERIC_SNIPPET =
  "<h3>Draft clause</h3><p>A financial institution shall [state the obligation] in a manner proportionate to the nature, scale and complexity of its operations. Adapt this scaffold to the requirement you have in mind.</p>";

/** The fake "smart" Copilot: matches the drafter's message against a few
 *  keyword rules and tailors a reply — most carrying a snippet the drafter can
 *  insert. Falls back to a generic drafting scaffold so every message gets a
 *  usable answer. No model call. */
function buildMockReply(input: string): Reply {
  const t = input.toLowerCase();
  const has = (...keys: string[]) => keys.some((k) => t.includes(k));

  if (has("governance", "section 3", "accountab", "board")) {
    return {
      title: "Section 3 — Governance & Accountability",
      body: "This section has the strongest clause coverage in your workstream. Here's a clause grounded in BCM PD 8.1–8.3 and Recovery Planning PD 12.3 — insert it and tailor the officer's title to your mandate.",
      snippet: GOV_SNIPPET,
      followups: ["Draft the scope section next", "Compare with MAS"],
    };
  }
  if (has("report", "section 6", "submission", "notify")) {
    return {
      title: "Section 6 — Reporting Requirements",
      body: "No existing clause covers supervisory reporting. Benchmarking MAS (semi-annual) and FSB (event-triggered) gives a defensible starting point — the drafted clause below combines both.",
      snippet: REPORTING_SNIPPET,
      followups: ["Add an enforcement section", "Summarise gaps"],
    };
  }
  if (has("cbf", "critical business", "section 4", "reconcile", "definition")) {
    return {
      title: "Reconcile the CBF definition",
      body: "BCM PD 9.7 frames CBFs by operational continuity; Recovery Planning PD 11.11 frames them by real-economy impact. UK PRA and MAS both resolved this with a two-tier definition — the clause below adopts the same approach.",
      snippet: CBF_SNIPPET,
      followups: ["Draft impact tolerance next", "Show full outline"],
    };
  }
  if (has("scenario", "testing", "stress")) {
    return {
      title: "Scenario testing (BCBS Principle 5)",
      body: "Neither connected document addresses scenario testing — a deviation from the BCBS baseline. Insert the clause below to close it.",
      snippet: SCENARIO_SNIPPET,
      followups: ["Draft Section 3 — Governance", "Compare with MAS"],
    };
  }
  if (has("outline", "structure", "sections", "skeleton")) {
    return {
      title: "Recommended structure",
      body: "Here's a seven-section structure for the Policy Document. Insert it as headings, then draft into each section.",
      snippet: OUTLINE_SNIPPET,
      followups: ["Draft Section 3 — Governance", "Summarise gaps"],
    };
  }
  if (has("rto", "rpo", "recovery time", "recovery point", "target")) {
    return {
      title: "Recovery time & point objectives",
      body: "Your draft is silent on quantitative recovery targets. MAS prescribes them by institution tier — the clause below follows that model.",
      snippet: RTO_SNIPPET,
      followups: ["Draft the CBF definition", "Compare with MAS"],
    };
  }
  if (has("enforce", "section 7", "penalt", "sanction")) {
    return {
      title: "Section 7 — Enforcement",
      body: "No clause evidence in your workstream. MAS uses a tiered model (advisory → direction → penalty) aligned with FSA 2013 powers — the clause below mirrors it.",
      snippet: ENFORCE_SNIPPET,
      followups: ["Draft the reporting section", "Show full outline"],
    };
  }
  if (has("mas", "singapore")) {
    return {
      title: "Comparison with MAS",
      body: "MAS is more prescriptive than your current draft: it sets RTO/RPO targets by institution tier and requires tiered enforcement. Consider borrowing MAS's quantitative targets for Section 4.",
      followups: ["Draft RTO/RPO targets", "Draft Section 7 — Enforcement"],
    };
  }
  if (has("gap", "missing", "cover")) {
    return {
      title: "Gap summary",
      body: "Open gaps across your workstream:\n• CBF definition conflict (BCM PD 9.7 vs Recovery Planning PD 11.11)\n• Section 6 reporting — no clause evidence\n• Section 7 enforcement — no clause evidence\n• Scenario testing absent (BCBS Principle 5)\n• No RTO/RPO targets (MAS benchmark)",
      followups: ["Draft Section 6 — Reporting", "Draft the CBF definition"],
    };
  }
  return {
    title: "Drafting help",
    body: "I can help you draft that. Here's a clause scaffold grounded in the operational-resilience framework — insert it at your cursor and adapt the obligation to your requirement.",
    snippet: GENERIC_SNIPPET,
    followups: ["Show full outline", "Summarise gaps"],
  };
}

/** How peer jurisdictions handle this policy area. Each is clickable and opens
 *  a canned reply in the conversation. */
const BENCHMARKS: Array<{
  region: string;
  name: string;
  status: keyof typeof BADGE_STYLES;
  desc: string;
  prompt: string;
  reply: Reply;
}> = [
  {
    region: "UK",
    name: "UK PRA — PS6/21",
    status: "Aligned",
    desc: "Board accountability & impact tolerance map to BCM PD 8.1–8.3",
    prompt: "How does UK PRA PS6/21 compare?",
    reply: {
      title: "UK PRA — PS6/21 · Aligned",
      body: "Your draft's board-accountability and impact-tolerance requirements map cleanly to UK PRA PS6/21. BCM PD 8.1–8.3 already covers this — no change needed.",
      followups: ["Draft Section 3 — Governance", "Compare with MAS"],
    },
  },
  {
    region: "SG",
    name: "MAS — BCM Guidelines",
    status: "Gap detected",
    desc: "Prescriptive RTO/RPO targets by tier — not yet in draft",
    prompt: "How does MAS compare?",
    reply: buildMockReply("mas"),
  },
  {
    region: "HK",
    name: "HKMA — SA-2 Module",
    status: "Gap detected",
    desc: "Annual self-certification to the regulator — no equivalent",
    prompt: "How does HKMA SA-2 compare?",
    reply: {
      title: "HKMA — SA-2 Module · Gap detected",
      body: "HKMA mandates an annual self-certification to the regulator. No equivalent obligation exists in your workstream — insert the attestation clause below.",
      snippet:
        "<h3>Annual Certification</h3><p>The accountable officer shall certify to the Bank annually that the institution's operational resilience arrangements remain adequate and effective.</p>",
      followups: ["Draft Section 6 — Reporting", "Summarise gaps"],
    },
  },
  {
    region: "INT",
    name: "BCBS — OpRes Principles 2021",
    status: "Deviation",
    desc: "Scenario testing (Principle 5) not addressed in either doc",
    prompt: "How does BCBS OpRes Principles compare?",
    reply: buildMockReply("scenario testing"),
  },
];

/** Suggested next drafting actions. Each is clickable and opens a canned reply
 *  in the conversation. */
const SUGGESTIONS: Array<{
  id: string;
  Icon: typeof AlertTriangle;
  iconClass: string;
  title: string;
  body: string;
  tag: keyof typeof TAG_STYLES;
  reply: Reply;
}> = [
  {
    id: "cbf",
    Icon: AlertTriangle,
    iconClass: "text-red-600",
    title: "Reconcile CBF definition conflict",
    body: "BCM PD 9.7 and Recovery Planning PD 11.11 define Critical Business Functions differently.",
    tag: "conflicts-with",
    reply: buildMockReply("reconcile cbf"),
  },
  {
    id: "sec6",
    Icon: FileText,
    iconClass: "text-amber-600",
    title: "Draft Section 6 — Reporting Requirements",
    body: "No clause evidence in workstream. Consider the MAS semi-annual reporting model.",
    tag: "silent-on",
    reply: buildMockReply("section 6 reporting"),
  },
  {
    id: "sec3",
    Icon: CheckCircle2,
    iconClass: "text-emerald-600",
    title: "Section 3 ready to draft",
    body: "Governance & Accountability has strong clause coverage from BCM PD 8.1–8.3.",
    tag: "aligns-with",
    reply: buildMockReply("section 3 governance"),
  },
];

/** Quick-prompt chips, always available above the message box. */
const CHIPS = [
  "Summarise gaps",
  "Show full outline",
  "Compare with MAS",
  "Draft Section 3",
];

export function CopilotTab({ onInsertSnippet }: CopilotTabProps) {
  const [intent, setIntent] = useState<CopilotIntent>("PD");
  const [messages, setMessages] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  function ask(prompt: string, reply: Reply) {
    setMessages((prev) => [
      ...prev,
      { role: "user", text: prompt },
      { role: "copilot", reply },
    ]);
    // Jump to the newest turn on the next frame.
    requestAnimationFrame(() => {
      const el = scrollRef.current;
      if (el) el.scrollTop = el.scrollHeight;
    });
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text) return;
    setInput("");
    ask(text, buildMockReply(text));
  }

  const started = messages.length > 0;

  return (
    <div className="flex h-full flex-col" data-testid="copilot-tab">
      <label className="block px-1 pb-2">
        <span className="sr-only">Intent preset</span>
        <select
          aria-label="Intent preset"
          value={intent}
          onChange={(e) => setIntent(e.target.value as CopilotIntent)}
          className="w-full rounded-md border border-border/60 bg-background/60 px-2 py-1.5 text-sm outline-none focus:border-primary/60"
        >
          {COPILOT_INTENTS.map((i) => (
            <option key={i} value={i}>
              {COPILOT_INTENT_LABELS[i]}
            </option>
          ))}
        </select>
      </label>

      <div
        ref={scrollRef}
        className="flex-1 space-y-4 overflow-y-auto px-1 pb-2"
        aria-label="Copilot conversation"
      >
        {!started ? (
          <>
            {/* Header */}
            <div className="space-y-0.5">
              <h3 className="px-1 text-sm font-semibold text-foreground">
                Copilot suggestions based on your workstream
              </h3>
              <p className="px-1 text-xs text-muted-foreground">
                BCM PD (19 Dec 2022) · Recovery Planning PD v0.1 · 2 anchor
                documents
              </p>
            </div>

            {/* Global benchmarks */}
            <section className="space-y-2">
              <h4 className="flex items-center gap-1.5 px-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                <Globe className="h-3.5 w-3.5" />
                Global Benchmarks
              </h4>
              <div className="grid grid-cols-2 gap-2">
                {BENCHMARKS.map((b) => (
                  <button
                    key={b.name}
                    type="button"
                    onClick={() => ask(b.prompt, b.reply)}
                    className="rounded-xl border border-border/60 bg-muted/30 p-2.5 text-left transition hover:border-primary/60 hover:bg-primary/10"
                  >
                    <div className="mb-1 flex items-center gap-1.5">
                      <span className="rounded bg-background/60 px-1 py-0.5 text-[9px] font-bold tracking-wide text-muted-foreground">
                        {b.region}
                      </span>
                      <span className="text-xs font-medium leading-tight text-foreground">
                        {b.name}
                      </span>
                    </div>
                    <span
                      className={[
                        "inline-block rounded-full border px-1.5 py-0.5 text-[9px] font-semibold",
                        BADGE_STYLES[b.status],
                      ].join(" ")}
                    >
                      {b.status}
                    </span>
                    <p className="mt-1.5 text-[11px] leading-snug text-muted-foreground">
                      {b.desc}
                    </p>
                  </button>
                ))}
              </div>
            </section>

            {/* Suggested next actions */}
            <section className="space-y-2">
              <h4 className="flex items-center gap-1.5 px-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                <PenLine className="h-3.5 w-3.5" />
                Suggested next actions
              </h4>
              <div className="space-y-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => ask(s.title, s.reply)}
                    className="block w-full rounded-xl border border-border/60 bg-muted/30 p-2.5 text-left transition hover:border-primary/60 hover:bg-primary/10"
                  >
                    <div className="mb-1 flex items-center justify-between gap-2">
                      <span className="flex items-center gap-1.5 text-sm font-medium text-foreground">
                        <s.Icon
                          className={`h-3.5 w-3.5 shrink-0 ${s.iconClass}`}
                        />
                        {s.title}
                      </span>
                      <span
                        className={[
                          "shrink-0 rounded-full border px-1.5 py-0.5 text-[9px] font-semibold",
                          TAG_STYLES[s.tag],
                        ].join(" ")}
                      >
                        {s.tag}
                      </span>
                    </div>
                    <p className="text-[11px] leading-snug text-muted-foreground">
                      {s.body}
                    </p>
                  </button>
                ))}
              </div>
            </section>
          </>
        ) : (
          <>
            <button
              type="button"
              onClick={() => setMessages([])}
              className="flex items-center gap-1.5 px-1 text-[11px] font-medium text-muted-foreground hover:text-foreground"
            >
              <RotateCcw className="h-3 w-3" />
              New chat
            </button>

            {messages.map((m, i) =>
              m.role === "user" ? (
                <div key={i} data-testid="chat-user" className="flex justify-end">
                  <p className="max-w-[85%] rounded-lg bg-primary px-2.5 py-1.5 text-sm leading-snug text-primary-foreground">
                    {m.text}
                  </p>
                </div>
              ) : (
                <div
                  key={i}
                  data-testid="chat-copilot"
                  className="rounded-xl border border-border/60 bg-muted/30 p-3"
                >
                  <p className="mb-1 text-sm font-semibold text-foreground">
                    {m.reply.title}
                  </p>
                  <p className="whitespace-pre-line text-xs leading-relaxed text-muted-foreground">
                    {m.reply.body}
                  </p>
                  {m.reply.snippet && (
                    <button
                      type="button"
                      onClick={() => onInsertSnippet(m.reply.snippet!)}
                      className="mt-2.5 flex items-center gap-1.5 rounded-md bg-primary px-2.5 py-1 text-xs font-semibold text-primary-foreground hover:bg-primary/90"
                    >
                      <FilePlus2 className="h-3.5 w-3.5" />
                      Insert at cursor
                    </button>
                  )}
                  {m.reply.followups && m.reply.followups.length > 0 && (
                    <div className="mt-2.5 flex flex-wrap gap-1.5">
                      {m.reply.followups.map((f) => (
                        <button
                          key={f}
                          type="button"
                          onClick={() => ask(f, buildMockReply(f))}
                          className="rounded-full border border-border/60 px-2 py-0.5 text-[11px] text-muted-foreground transition hover:border-primary/60 hover:text-primary"
                        >
                          {f}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ),
            )}
          </>
        )}
      </div>

      {/* Footer: quick prompts + message box */}
      <div className="mt-2 space-y-1.5 px-1">
        <div className="flex flex-wrap gap-1.5">
          {CHIPS.map((chip) => (
            <button
              key={chip}
              type="button"
              onClick={() => ask(chip, buildMockReply(chip))}
              className="rounded-full border border-border/60 px-2 py-0.5 text-xs text-muted-foreground transition hover:border-primary/60 hover:text-primary"
            >
              {chip}
            </button>
          ))}
        </div>
        <form className="flex gap-1.5" onSubmit={onSubmit}>
          <input
            aria-label="Message the Copilot"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask the Copilot to draft or compare…"
            className="min-w-0 flex-1 rounded-md border border-border/60 bg-background/60 px-2.5 py-1.5 text-sm outline-none focus:border-primary/60"
          />
          <button
            type="submit"
            aria-label="Send"
            className="flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
          >
            <Send className="h-3.5 w-3.5" />
          </button>
        </form>
      </div>
    </div>
  );
}
