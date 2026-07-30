import type { NodeType, SemanticLabel, Sentiment } from "@/lib/types";

// Curated excerpt of the REAL open-finance-pd-2026 workstream fixture
// (data/workstreams/open-finance-pd-2026/). Every clause_number + text pair
// below is copied verbatim from that workstream's findings JSON — never
// paraphrased — per CLAUDE.md's citation rule. No API call: this is a static
// module, same "no live model" constraint the rest of this demo panel has
// always had, just grounded in the real fixture instead of invented prose.

export const WORKSTREAM_CONTEXT = {
  name: "Open Finance PD . 2026",
  targetPublication: "Q4 2026",
  owner: "Aisyah R.",
};

/** The task's regulatory profile. Nine fields are copied verbatim from the
 *  task's direct anchor "ED Open Finance 2025" —
 *  data/workstreams/open-finance-ed/concepts/of-ed-2025.json — the document
 *  this PD consolidates. A null value is real absence, not omission. The
 *  leading `task_type` is not a concepts field; it is the task node's own
 *  document class ("PD" short_type → "Policy Document"), an honest projection
 *  of existing graph data, not an invented value. */
export interface NodeMetadataField {
  key: string;
  label: string;
  value: string | string[] | null;
}

export const NODE_METADATA: NodeMetadataField[] = [
  { key: "task_type", label: "Task type", value: "Policy Document (PD)" },
  { key: "policy_owner", label: "Policy owner", value: "Jarod N." },
  {
    key: "applicability",
    label: "Applicability",
    value:
      "Licensed banks and eligible data providers participating in the open finance ecosystem",
  },
  { key: "empowerment_framework", label: "Empowerment framework", value: null },
  { key: "requirement", label: "Requirement", value: null },
  { key: "issuance_date", label: "Issuance date", value: "2025-11-18" },
  { key: "effective_date", label: "Effective date", value: null },
  {
    key: "keywords",
    label: "Keywords",
    value: [
      "open finance",
      "data sharing",
      "third-party providers",
      "consent",
      "operational resilience",
      "accountability",
    ],
  },
  { key: "legal_basis", label: "Legal basis", value: ["FSA 2013"] },
  { key: "ismp_classification", label: "ISMP classification", value: null },
];

/** Real reviewers on file for this task, from
 *  data/workstreams/open-finance-pd-2026/workstream.json — genuinely empty in
 *  that fixture today. The owner shown alongside this in the release phase is
 *  WORKSTREAM_CONTEXT.owner, the same real value used throughout this file. */
export const RELEASE_REVIEWERS: string[] = [];

export interface AnchorDoc {
  title: string;
  nodeType: NodeType;
}

export const ANCHOR_DOCS: AnchorDoc[] = [
  { title: "ED Open Finance 2025", nodeType: "internal-published" },
  { title: "HKMA Open API Framework", nodeType: "peer-regulator" },
  { title: "BIS Papers 168", nodeType: "international-standard" },
  { title: "RMiT 2025", nodeType: "internal-published" },
];

export const LEADING_QUESTION =
  "I see you're consolidating the Open Finance PD . 2026 against the 2025 Exposure Draft, benchmarked against the HKMA Open API Framework, BIS Papers 168 and RMiT 2025. To sharpen the draft, tell me — are you most focused on TSP/TPP governance, API security & technology controls, or consumer consent & data portability?";

export const LEADING_OPTIONS = [
  "TSP/TPP governance",
  "API security & technology controls",
  "Consumer consent & data portability",
];

export interface ThinkingStep {
  icon: "search" | "map" | "scale" | "globe" | "link" | "eye" | "chart" | "check";
  text: string;
}

export const THINKING_STEPS: ThinkingStep[] = [
  { icon: "search", text: "Scanning anchor documents — ED Open Finance 2025, HKMA Open API Framework, BIS Papers 168, RMiT 2025..." },
  { icon: "map", text: "Mapping the PD's defined terms against ED Open Finance 2025's scope of prescribed information..." },
  { icon: "scale", text: "Cross-referencing HKMA Open API Framework's TSP governance clauses (9.3, 29–31)..." },
  { icon: "globe", text: "Benchmarking BIS Papers 168 on open banking & cross-border data portability..." },
  { icon: "link", text: "Checking API security control alignment — HKMA's phased categories vs BNM's uniform controls (clause 12)..." },
  { icon: "chart", text: "Comparing implementation timelines — HKMA's voluntary phased rollout vs BNM's mandated 2028 dates..." },
  { icon: "eye", text: "Identifying silent gaps — no HKMA equivalent found for consent dashboards or breach-response plans..." },
  { icon: "check", text: "Synthesising a draft structure grounded in confirmed clause citations..." },
];

export interface ClarificationQuestion {
  id: string;
  prompt: string;
  options: string[];
}

export const CLARIFICATION_QUESTIONS: ClarificationQuestion[] = [
  {
    id: "q1",
    prompt:
      "ED Open Finance 2025 §14 phases mandated-FSP obligations to \"both individual and SME customers\" from 1 Jan 2028. Is this PD's scope individual customers, SME customers, or both?",
    options: ["Individual customers", "SME customers", "Both"],
  },
  {
    id: "q2",
    prompt:
      "For TSP/TPP assessment, should this PD follow HKMA's bilateral-with-common-baseline model (banks may rely on another bank's assessment), or BNM's direct FSP-obligation model in §12.2?",
    options: ["HKMA's shared baseline", "BNM's direct FSP obligation", "Hybrid of both"],
  },
  {
    id: "q3",
    prompt:
      "ED Open Finance 2025 §10.4 requires a real-time consent dashboard — a requirement the HKMA framework has no equivalent for. Should the PD keep this requirement as drafted?",
    options: ["Keep as drafted", "Soften to a periodic status update", "Needs more research"],
  },
  {
    id: "q4",
    prompt:
      "HKMA Open API Framework §12 phases API security by category (product info → transactions), while ED Open Finance 2025 §12.2-12.3 applies uniform API security controls. Which model should this PD's security section follow?",
    options: [
      "Uniform controls (BNM §12.2-12.3)",
      "Phased by API category (HKMA)",
      "Uniform now, phased later",
    ],
  },
  {
    id: "q5",
    prompt:
      "BIS Papers 168 flags cross-border data portability as an open-banking risk area. ED Open Finance 2025 is silent on cross-border sharing. Should this PD add an explicit cross-border data-transfer clause?",
    options: [
      "Add an explicit clause",
      "Defer to a later revision",
      "Reference PDPA and stay silent",
    ],
  },
  {
    id: "q6",
    prompt:
      "ED Open Finance 2025 §11.12 requires a breach handling and response plan with escalation procedures. How prescriptive should this PD be on breach-response timelines?",
    options: [
      "Fixed notification window (e.g. 72h)",
      "Principles-based, no fixed window",
      "Align to existing RMiT incident rules",
    ],
  },
];

export type SectionStatus = "ready" | "drafted" | "gap";

export interface ClauseCitation {
  clauseNumber: string;
  text: string;
}

export interface DraftSection {
  id: string;
  title: string;
  status: SectionStatus;
  label: SemanticLabel;
  sentiment: Sentiment;
  summary: string;
  sourceCitations: ClauseCitation[];
  targetCitations: ClauseCitation[];
}

export const DRAFT_SECTIONS: DraftSection[] = [
  {
    id: "objectives",
    title: "Policy Objectives & Legal Basis",
    status: "ready",
    label: "aligns-with",
    sentiment: null,
    summary:
      "Both documents highlight the benefits of API-driven data sharing frameworks for customers and the financial industry.",
    sourceCitations: [
      {
        clauseNumber: "hkma-open-api-framework 8.1",
        text: "The implementation of Open API would bring many benefits and efficiency gain to the banking industry and to its customers. Feedback from the banking industry indicates that it is desirable to implement Open APIs to provide better services to satisfy the demands of its customers. Banks are therefore expected to implement the Open API framework in the timeline set out in the framework. The HKMA will monitor the implementation closely, and act accordingly to ensure market adoption and encourage use cases.",
      },
    ],
    targetCitations: [
      {
        clauseNumber: "ed-open-finance-2025 1.2",
        text: "Open finance plays a pivotal role in advancing this vision by offering customers a safer and more structured framework for sharing their financial information compared to existing data-sharing arrangements in Malaysia. By enabling consent-driven information sharing, open finance provides customers with greater control over their personal financial information, allowing them to actively determine and manage how their information is shared, accessed and used. Beyond empowering customers, open finance unlocks data-driven innovation that enables customers to make better-informed decisions about their finances, facilitates the delivery of more personalised financial services and promotes greater financial inclusion.",
      },
    ],
  },
  {
    id: "scope",
    title: "Scope of Application — Defined Terms",
    status: "drafted",
    label: "differs-on",
    // No tighten/loosen direction on this difference — a plain scope mismatch.
    sentiment: null,
    summary:
      "HKMA's read-only product and service information sharing corresponds narrowly to BNM's broader defined \"scope of prescribed information\" that a data provider must share with a data consumer, reflecting a difference in scope of what information sharing entails.",
    sourceCitations: [
      {
        clauseNumber: "hkma-open-api-framework 11.1",
        text: "Product and service information - \"Read-only\" information offered by banks on details of their products and services;",
      },
    ],
    targetCitations: [
      {
        clauseNumber: "ed-open-finance-2025 11(a)-(g)",
        text: "\"scope of prescribed information\" refers to the scope of personal financial information relating to a customer that a data provider is obligated to share with a data consumer subject to the customer's consent as specified in Appendix 1; \"open finance\" refers to a framework that enables permissioned sharing of customer information between a data provider and a data consumer in a secure, open, accessible, interoperable, and timely manner;",
      },
    ],
  },
  {
    id: "tsp-governance",
    title: "TSP / TPP Governance & Registration",
    status: "ready",
    label: "aligns-with",
    sentiment: null,
    summary:
      "Both frameworks address TSP/FSP governance and technology operations management for third-party participation in API-based data sharing.",
    sourceCitations: [
      {
        clauseNumber: "hkma-open-api-framework 9.3",
        text: "TSP governance model;",
      },
    ],
    targetCitations: [
      {
        clauseNumber: "ed-open-finance-2025 12.2",
        text: "An FSP shall ensure that its technology operations management practices are appropriately extended to support its open finance activities. This includes, but is not limited to, controls for ensuring effective and safe implementation of IT systems, robust third-party service provider management, and operational resilience measures to ensure the availability, integrity and confidentiality of data exchanged through open finance arrangements.",
      },
    ],
  },
  {
    id: "api-security",
    title: "API Technology & Security Controls",
    status: "drafted",
    label: "differs-on",
    sentiment: "tighten",
    summary:
      "Both specify security/protection requirements (authentication, integrity, confidentiality) for data and API transactions, though HKMA differentiates by API category while BNM applies broader cyber risk and API security controls uniformly.",
    sourceCitations: [
      {
        clauseNumber: "hkma-open-api-framework 12",
        text: "It was further agreed that the types of protection required for each of the four categories of Open API implementation should be in a progressive manner: Product and service information — authentication of bank sites, integrity of data, authentication of TSPs. Subscription and new applications — authentication of bank sites, integrity and confidentiality of data, authentication of TSPs. Account information — authentication of bank sites, integrity and confidentiality of data. Transactions — authentication of TSPs, authorisation of customers.",
      },
    ],
    targetCitations: [
      {
        clauseNumber: "ed-open-finance-2025 12.2-12.3",
        text: "An FSP shall ensure that its cyber risk management capabilities and cybersecurity controls are also appropriately extended to govern, identify, prevent, detect, respond and address cyber risks associated with open finance activities. This includes for the FSP to implement robust API security controls, strengthening digital fraud detection and management, as well as take steps to secure technology networks and internal systems from potential external risks arising from the FSP's participation in an open finance arrangement.",
      },
    ],
  },
  {
    id: "timeline",
    title: "Implementation Timeline & Commencement",
    status: "drafted",
    label: "differs-on",
    sentiment: "loosen",
    summary:
      "HKMA's collaborative, phased, non-mandatory approach to Open API adoption differs from BNM's mandated FSP obligations with fixed commencement timelines for data sharing.",
    sourceCitations: [
      {
        clauseNumber: "hkma-open-api-framework 8.2",
        text: "The HKMA has taken note of the mandatory approach adopted by some jurisdictions such as the EU, the UK and Australia but has decided that a collaborative and phased approach is an appropriate approach for Hong Kong for the time being. The HKMA will monitor the progress of Open API implementation in Hong Kong and further consider the need for new regulatory measures if necessary.",
      },
    ],
    targetCitations: [
      {
        clauseNumber: "ed-open-finance-2025 9",
        text: "S 9.1 The obligations of a mandated FSP as specified under paragraph 8.4 shall commence in accordance with the timeline specified in Appendix 2. S 9.2 A mandated FSP shall commence its obligation under paragraph 8.6 to provide document submission and single account view interfaces by 1 January 2028 or the date on which the FSP's obligations under paragraph 8.4 commence, whichever is later.",
      },
      {
        clauseNumber: "ed-open-finance-2025 14",
        text: "sharing by a mandated FSP whose obligation to commence as a data provider falls on or after 1 January 2028 shall include both individual and SME customers.",
      },
    ],
  },
  {
    id: "consent",
    title: "Consumer Consent & Data Sharing",
    status: "ready",
    label: "aligns-with",
    sentiment: null,
    summary:
      "Both frameworks require explicit customer consent before sharing customer information with third parties.",
    sourceCitations: [
      {
        clauseNumber: "hkma-open-api-framework 34.3.2(i)",
        text: "explicit to their customers that the collection of personal data is neither carried out by banks nor directly related to bank business, and (iii) comply with the applicable laws and guidance on the protection of personal data; and",
      },
    ],
    targetCitations: [
      {
        clauseNumber: "ed-open-finance-2025 6",
        text: "separate and distinct consent must be obtained by the data consumer before disclosing the customer's information to a third party engaged (e.g. data analytics partner) to support the offering of that product or service.",
      },
    ],
  },
  {
    id: "breach-response",
    title: "Consent Dashboard & Breach Response",
    status: "gap",
    label: "silent-on",
    sentiment: null,
    summary:
      "Document B (ED Open Finance 2025) requires FSPs to maintain a breach handling and response plan for theft, loss, misuse or unauthorised access to customer information, including escalation procedures and a clear line of responsibility. The connected HKMA Open API Framework addresses TSP monitoring and scam notification but has no equivalent breach-handling-plan requirement.",
    sourceCitations: [],
    targetCitations: [
      {
        clauseNumber: "ed-open-finance-2025 11.12",
        text: "breach handling and response plan in the event of theft, loss, misuse or unauthorised access, modification or disclosure of customer information associated with an open finance arrangement. The plan must, at a minimum, include escalation procedures and a clear line of responsibility to contain the customer information breach and take remedial actions.",
      },
    ],
  },
];

/** Builds the HTML snippet inserted into the editor for one draft section.
 *  Ready/Drafted sections quote their real citation(s) verbatim; the one Gap
 *  section says so explicitly and marks its scaffold as provisional — never
 *  presented as clause-backed. */
export function buildSectionSnippet(section: DraftSection): string {
  const quote = (c: ClauseCitation) =>
    `<blockquote><strong>${c.clauseNumber}:</strong> "${c.text}"</blockquote>`;

  if (section.status === "gap") {
    return [
      `<h3>${section.title}</h3>`,
      `<p><em>No matching source clause found in the connected anchor documents.</em></p>`,
      ...section.targetCitations.map(quote),
      `<p>Draft language below is provisional — not grounded in a clause citation; review before adopting.</p>`,
      `<p>[Insert drafting language here]</p>`,
    ].join("");
  }

  return [
    `<h3>${section.title}</h3>`,
    `<p>${section.summary}</p>`,
    ...section.sourceCitations.map(quote),
    ...section.targetCitations.map(quote),
  ].join("");
}

/** The full 2–3 page draft /build auto-populates into the editor: every
 *  section's snippet, concatenated. Reuses buildSectionSnippet (never
 *  re-serialises) so each section keeps its verbatim blockquote citation. */
export function buildFullDraft(): string {
  return DRAFT_SECTIONS.map(buildSectionSnippet).join("");
}

// --- Slash command registry ------------------------------------------------
// The five commands the Copilot chatbox understands, in flow order. Typing "/"
// in the chat input opens a vertical, filterable menu of these. Each carries a
// canned assistant intro (there is no live model) and the chip(s) suggested
// once it completes — that suggestion is what reveals the next command.

export type SlashCommandId =
  | "/explore-task"
  | "/brainstorm"
  | "/draft"
  | "/write"
  | "/deliver";

export interface SlashCommandDef {
  id: SlashCommandId;
  label: string;
  description: string;
  /** The assistant's opening line when the command is invoked. */
  intro: string;
}

export const SLASH_COMMANDS: SlashCommandDef[] = [
  {
    id: "/explore-task",
    label: "/explore-task",
    description: "Reveal the task's regulatory profile",
    intro: "Pulling the task's regulatory profile from its connected anchor document…",
  },
  {
    id: "/brainstorm",
    label: "/brainstorm",
    description: "Pull context, then align on focus through Q&A",
    intro: "Let's align on the draft. Pulling context from the anchor documents first…",
  },
  {
    id: "/draft",
    label: "/draft",
    description: "Preview an instructional draft outline",
    intro: "Here's the outline I'd draft, grounded in the confirmed citations.",
  },
  {
    id: "/write",
    label: "/write",
    description: "Write the full draft into the editor",
    intro: "Writing the full draft into your editor now…",
  },
  {
    id: "/deliver",
    label: "/deliver",
    description: "Send the draft for review",
    intro: "Ready to send this draft for review.",
  },
];

export const SLASH_COMMAND_IDS: SlashCommandId[] = SLASH_COMMANDS.map((c) => c.id);

// --- Mentionable documents/nodes -------------------------------------------
// Typing "@" in the chat input references one of the workstream's documents.
// A static demo list (this panel never touches the live graph): the anchor
// documents plus a couple of task-adjacent nodes.

export interface Mentionable {
  id: string;
  label: string;
  kind: "doc" | "node";
}

export const MENTIONABLE: Mentionable[] = [
  ...ANCHOR_DOCS.map((a) => ({
    id: a.title,
    label: a.title,
    kind: "doc" as const,
  })),
  { id: "open-finance-pd-2026", label: "Open Finance PD . 2026 (this task)", kind: "node" },
  { id: "pdpa-2010", label: "PDPA 2010", kind: "node" },
];
