import { WORKSTREAM_CONTEXT } from "./copilotV2Data";
import { coverPage, pageChrome, sectionHeading, partHeading, tocPage, type TocEntry } from "./copilotDocumentChrome";

export interface DraftOutlineSection {
  id: string;
  /** Display number — "1", "Appendix 1", or "" for the unnumbered executive
   *  summary preface. */
  number: string;
  title: string;
  /** Set on the first section of a new PART — renders a part divider
   *  heading immediately above this section. */
  partStart?: { letter: string; title: string };
  description: string;
  bullets: string[];
  guidanceNote: string;
}

/** The instructional outline /draft renders and inserts into the editor —
 *  same cover, TOC, and page format as /write's full document, one page per
 *  entry, each wrapped in a `.draft-guidance-block`. The 7 ids that also
 *  appear in DRAFT_SECTIONS (scope, tsp-governance, api-security, timeline,
 *  consent, breach-response, plus objectives folded into "introduction"'s
 *  legal-basis framing) reuse those real citations in /write; the rest are
 *  original sections a BNM-style policy document would carry, with no
 *  DRAFT_SECTIONS counterpart. */
export const DRAFT_OUTLINE_SECTIONS: DraftOutlineSection[] = [
  {
    id: "executive-summary",
    number: "",
    title: "Executive Summary",
    description:
      "A prose synthesis of why this PD exists and what it changes, written last but read first.",
    bullets: [
      "State the policy objective in one paragraph: safer, consent-driven data sharing for banking customers.",
      "Name the anchor documents this PD consolidates and benchmarks against — ED Open Finance 2025, HKMA Open API Framework, BIS Papers 168, RMiT 2025.",
      "Flag the two areas where this PD goes further than its anchors: the mandated consent dashboard and the breach-response plan.",
      "Keep it citation-free — this section previews the draft, it does not itself make a clause-backed claim.",
    ],
    guidanceNote:
      "Write this section last, once every body section below is settled — an executive summary that outruns the draft it summarises is a common review-cycle defect.",
  },
  {
    id: "introduction",
    number: "1",
    partStart: { letter: "A", title: "Overview" },
    title: "Introduction",
    description: "Set the scene: why open finance, and why a formal Policy Document now.",
    bullets: [
      "Frame the shift toward digital, consent-driven information sharing as the reason a dedicated open finance framework is needed.",
      "Name the customer and industry benefits this PD is trying to secure, without repeating the Executive Summary verbatim.",
      "Signal that requirements will be phased in — an ecosystem this size is a multi-year adoption, not a single cutover date.",
      "Keep this section short — two to three short paragraphs, not a restatement of every clause that follows.",
    ],
    guidanceNote:
      "This is scene-setting, not obligation — the first `S`-numbered requirement belongs in Applicability, not here.",
  },
  {
    id: "applicability",
    number: "2",
    title: "Applicability",
    description: "State plainly which institutions this Part binds.",
    bullets: [
      "List the FSP categories this PD applies to, drawn from the task's confirmed regulatory profile.",
      "Distinguish 'applies to all FSPs' from 'mandated FSP' — the latter is a narrower, threshold-defined subset covered in Appendix 1.",
      "Cross-reference Appendix 1 rather than repeating the mandated-FSP thresholds here.",
      "One clause is usually enough — resist expanding this into a full definitions section.",
    ],
    guidanceNote:
      "Keep applicability and the mandated-FSP threshold test in two different places — conflating them is a common drafting confusion.",
  },
  {
    id: "legal-provision",
    number: "3",
    title: "Legal Provision",
    description: "Anchor the whole Part in its enabling statutory sections, confirmed via /explore-task.",
    bullets: [
      "Cite the FSA 2013 sections (and IFSA/DFIA equivalents, if this PD binds Islamic or development financial institutions too) once the empowerment framework field is resolved.",
      "Separate binding requirements ('S') from guidance ('G') issued under a different statutory head — the real document keeps these on two different legal footings.",
      "Do not restate the requirement text here — this section cites authority, Policy Objectives (below) states purpose.",
      "If the empowerment framework is still 'Not available' when this is drafted, flag it rather than guessing a section number.",
    ],
    guidanceNote:
      "Legal basis is the one section where an honest 'to be confirmed' beats a plausible-sounding but wrong statutory citation.",
  },
  {
    id: "effective-date",
    number: "4",
    title: "Effective Date",
    description: "State when this Part itself takes effect, distinct from the phased transition dates in Appendix 2.",
    bullets: [
      "Confirm the effective date via /explore-task's regulatory profile rather than inventing one.",
      "Make clear this date governs the Part's coming-into-force, while Appendix 2 governs when each cohort's obligations commence.",
      "Keep this to one line — it is a date, not a policy statement.",
      "Cross-reference Transition Arrangements (below) so a reader isn't left wondering which date actually binds them.",
    ],
    guidanceNote:
      "Confusing 'effective date' with 'commencement date per cohort' is the single most common Part-A drafting error.",
  },
  {
    id: "definitions",
    number: "5",
    title: "Interpretation",
    description: "Define the terms this PD actually uses — no more, no less.",
    bullets: [
      "Define 'data provider', 'data consumer', 'open finance arrangement', 'open finance platform', and 'mandated FSP' before they're used substantively later.",
      "Reuse the applicability/scope language already confirmed elsewhere in this PD rather than drafting a second, slightly different definition.",
      "Alphabetise or group definitions logically — a reader shouldn't have to hunt for one term among fifty.",
      "Only define a term if it's actually used with a specific technical meaning elsewhere in this document.",
    ],
    guidanceNote:
      "A definitions section that doesn't match how a term is actually used three sections later is worse than no definitions section at all.",
  },
  {
    id: "governance",
    number: "6",
    partStart: { letter: "B", title: "Policy Requirements" },
    title: "Governance",
    description: "Set board and senior-management oversight expectations for open finance participation.",
    bullets: [
      "State that the board and senior management must exercise effective oversight of the FSP's open finance arrangements.",
      "Separate board-level responsibilities (risk strategy, appetite) from senior-management responsibilities (day-to-day implementation and controls).",
      "Reference the FSP's existing risk-governance policy document rather than duplicating its content here.",
      "Keep this principles-based — detailed controls belong in API Security and Management of Technology Risk, not here.",
    ],
    guidanceNote:
      "Every substantive section below should trace back to a governance accountability set here — if it doesn't, ask whether it belongs in this PD at all.",
  },
  {
    id: "scope",
    number: "7",
    title: "Scope of Application",
    description:
      "Define \"scope of prescribed information\" precisely — this is the one area where BNM's definition is broader than HKMA's.",
    bullets: [
      "Reproduce ED Open Finance 2025 §11(a)-(g)'s defined-terms list rather than paraphrasing it.",
      "Note explicitly where this differs from HKMA §11.1's narrower \"read-only product and service information\" scope.",
      "Decide, per the drafter's earlier answer, whether scope covers individual customers, SME customers, or both.",
      "Avoid silently narrowing scope to match HKMA — the difference is intentional, not a drafting gap.",
    ],
    guidanceNote:
      "This section differs-on by design — do not soften the wider BNM scope to match HKMA's narrower one without a documented reason.",
  },
  {
    id: "tsp-governance",
    number: "8",
    title: "TSP/TPP Governance and Registration",
    description:
      "Set out technology-operations and third-party governance obligations for participating FSPs.",
    bullets: [
      "Anchor the section on ED Open Finance 2025 §12.2's technology-operations-management language.",
      "Reference HKMA §9.3's TSP governance model as the aligned regional comparator.",
      "Reflect the drafter's brainstorming answer on the shared-baseline vs direct-obligation assessment model.",
      "Cross-reference API Security (below) rather than duplicating its control list here.",
    ],
    guidanceNote:
      "Both anchors agree here (aligns-with) — resist the urge to add net-new obligations that neither document supports.",
  },
  {
    id: "api-security",
    number: "9",
    title: "API Security and Technology Controls",
    description:
      "Set uniform cyber-risk and API security controls, tightened relative to HKMA's phased-by-category model.",
    bullets: [
      "Lead with ED Open Finance 2025 §12.2-12.3's uniform cyber-risk and API security control requirement.",
      "Contrast HKMA §12's four-category phased protection model as the looser comparator being tightened against.",
      "Reflect the drafter's chosen security-control model from the clarification round (uniform, phased, or uniform-now-phased-later).",
      "Call out digital fraud detection and network security explicitly — both named in §12.2-12.3.",
    ],
    guidanceNote:
      "This section tightens relative to its anchor (differs-on / tighten) — state plainly that uniform controls apply from commencement, not phased in by category.",
  },
  {
    id: "timeline",
    number: "10",
    title: "Transition Arrangements",
    description:
      "Fix commencement dates against Appendix 2 — a deliberate move from HKMA's voluntary phasing to a mandated timeline.",
    bullets: [
      "State the 1 January 2028 commencement date for document submission and single-account-view interfaces per ED Open Finance 2025 §9.1-9.2.",
      "Note HKMA §8.2's collaborative, non-mandatory phasing as the comparator this PD deliberately moves away from.",
      "Confirm from §14 whether the 2028 cohort covers individual customers, SME customers, or both, per the drafter's scope decision.",
      "Point to Appendix 2 for the full phase-by-phase table rather than repeating every date here.",
    ],
    guidanceNote:
      "This section loosens relative to HKMA's non-mandatory comparator (differs-on / loosen) even as it tightens BNM's own commencement certainty — flag both directions for the reviewing manager.",
  },
  {
    id: "consent",
    number: "11",
    title: "Consent Management — Obtaining Consent",
    description: "Require explicit, separate consent before any third-party disclosure — an area both anchors already agree on.",
    bullets: [
      "Anchor on ED Open Finance 2025 §6's separate-and-distinct consent requirement for third-party disclosure.",
      "Cite HKMA §34.3.2(i) as the aligned comparator on explicit customer-facing consent language.",
      "Reflect the drafter's chosen approach to the mandated real-time consent dashboard (§10.4) here, or defer detail to the next section.",
      "Keep consent language customer-facing and plain — this clause is read by compliance officers, not just lawyers.",
    ],
    guidanceNote:
      "Both anchors agree here (aligns-with) — this is a section to keep tight and uncontroversial, not to expand.",
  },
  {
    id: "consent-monitoring",
    number: "12",
    title: "Consent Management — Monitoring, Renewal and Revocation",
    description: "Cover the consent lifecycle after it's granted: the dashboard, expiry, renewal, and revocation.",
    bullets: [
      "State the real-time consent dashboard requirement from ED Open Finance 2025 §10.4 in full, per the drafter's decision to keep, soften, or research it further.",
      "Set validity periods for one-time vs recurring data access, and what happens on expiry (cease access, or require renewal).",
      "Set out the customer's right to revoke consent at any time, and the data provider/consumer's obligations once revoked.",
      "Require an auditable record of every consent action — granted, renewed, revoked — retained for a defined minimum period.",
    ],
    guidanceNote:
      "This is the section most likely to grow beyond one page — split validity/renewal and revocation into two sub-headings if it does.",
  },
  {
    id: "data-privacy-security",
    number: "13",
    title: "Customer Protection — Data Privacy and Security",
    description: "Set data governance, confidentiality, and technical-safeguard expectations for customer information.",
    bullets: [
      "Require data governance and privacy policies limiting access to a need-to-know basis and prohibiting use beyond consented purpose.",
      "Set retention limits and secure-disposal requirements once information is no longer needed for its consented purpose.",
      "Require technical and operational safeguards against theft, loss, misuse, or unauthorised access.",
      "Require a data consumer to treat information received from another FSP at least as protectively as its own customers' information.",
    ],
    guidanceNote:
      "This section has no direct HKMA citation in the confirmed anchors — mark it as this PD's own synthesis, not a comparator citation.",
  },
  {
    id: "third-party-arrangements",
    number: "14",
    title: "Customer Protection — Third-Party Arrangements",
    description: "Extend the same protections to any third-party service provider handling customer information.",
    bullets: [
      "Require the FSP to ensure any third-party service provider handling customer information meets the same privacy, confidentiality, and security requirements.",
      "Require customer information not be shared with a third party without the customer's explicit consent, cross-referencing Consent Management above.",
      "Require the obligation to safeguard customer information to be reflected in the service-level agreement with the third party.",
      "Cross-reference the FSP's existing outsourcing policy document rather than restating it.",
    ],
    guidanceNote:
      "Keep this section about third parties specifically — general data-privacy obligations belong in the section above.",
  },
  {
    id: "breach-response",
    number: "15",
    title: "Customer Protection — Breach Handling and Response",
    description:
      "The one section with no HKMA equivalent — write it as new obligation, not as a gap to be quietly filled.",
    bullets: [
      "Draft the breach handling and response plan required by §11.12 — theft, loss, misuse, or unauthorised access — with explicit escalation procedures and a named line of responsibility.",
      "Set the notification timeline the drafter chose in the clarification round (a fixed window, principles-based, or aligned to RMiT incident rules).",
      "Require prompt escalation of material breaches to the board, cross-referencing the Governance section.",
      "State explicitly that no equivalent clause exists in HKMA Open API Framework — this is silent-on, not a citation to invent.",
    ],
    guidanceNote:
      "No matching source clause exists for this section (silent-on) — draft it as considered new policy, and say so, rather than implying HKMA precedent that isn't there.",
  },
  {
    id: "complaints-handling",
    number: "16",
    title: "Complaints Handling and Redress",
    description: "Set clear accountability and a fair, timely complaints process for open finance disputes.",
    bullets: [
      "Require clear delineation of responsibility between FSPs when a dispute or complaint involves more than one party.",
      "Require complaints handling policies compliant with the FSP's existing complaints-handling policy document.",
      "Where no protocol exists for a multi-FSP dispute, assign the FSP that first receives the complaint to lead resolution, absent agreement otherwise.",
      "Encourage — not mandate — customer-centric, accessible complaint channels, including a human-assisted option.",
    ],
    guidanceNote:
      "Keep the mandatory 'S' requirements and the encouraged 'G' guidance visually distinct — this section naturally has both.",
  },
  {
    id: "tech-risk",
    number: "17",
    title: "Management of Technology Risk",
    description: "Cross-reference the FSP's existing technology risk framework rather than duplicating it.",
    bullets: [
      "Require existing technology-risk-management and payment-technology requirements to extend to open finance activities.",
      "Require operational resilience measures — availability, integrity, confidentiality of exchanged data — sized to open finance's specific risk profile.",
      "Require compliance with the open finance platform operator's own technology and operational requirements (API specs, uptime, independent review).",
      "Do not restate API Security's controls here — this section is about the FSP's broader technology-risk framework, not API-specific controls.",
    ],
    guidanceNote:
      "If this section starts repeating API Security almost verbatim, that's a sign the two sections need a clearer division of content.",
  },
  {
    id: "appendix-definitions",
    number: "Appendix 1",
    partStart: { letter: "C", title: "Appendices" },
    title: "Definition of Mandated FSP and Scope of Prescribed Information",
    description: "The threshold test for who is a 'mandated FSP', and exactly what information they must share.",
    bullets: [
      "Set the customer-count (or active-user, for e-money) threshold that makes an FSP 'mandated', per category of institution.",
      "Confirm whether the threshold is measured at entity level, banking-group level, or both.",
      "List the specific information fields in scope (e.g. transaction history, outstanding balance) rather than a general description.",
      "Keep this appendix purely definitional — no new substantive obligations should first appear here.",
    ],
    guidanceNote:
      "This is a reference appendix — every number here should already be foreshadowed by Applicability and Scope of Application above.",
  },
  {
    id: "appendix-timeline",
    number: "Appendix 2",
    title: "Transition Timeline",
    description: "The full phase-by-phase commencement schedule, rendered as a table.",
    bullets: [
      "Render the commencement date per FSP category as a table, not prose — this is the one section that should be almost entirely tabular.",
      "State which categories of customer information are mandated for sharing at each phase.",
      "Confirm the final cohort's scope (individual and/or SME customers) matches the decision recorded in the clarification round.",
      "Cross-reference Transition Arrangements (Part B) rather than repeating its narrative framing here.",
    ],
    guidanceNote:
      "If a reviewer can find every commencement date without reading anything except this table, the appendix is doing its job.",
  },
];

const PART_TITLES: Record<string, string> = { A: "Overview", B: "Policy Requirements", C: "Appendices" };

/** The TOC entries for this document — this PD's own section list, in the
 *  same dotted-leader / part-divider visual convention as the reference,
 *  not copied from any source's actual table of contents. */
export function buildTocEntries(): TocEntry[] {
  const entries: TocEntry[] = [];
  for (const s of DRAFT_OUTLINE_SECTIONS) {
    if (s.id === "executive-summary") continue;
    if (s.partStart) {
      entries.push({ number: s.partStart.letter, title: PART_TITLES[s.partStart.letter], isPart: true });
    }
    entries.push({ number: s.number, title: s.title });
  }
  return entries;
}

/** One section's page body: the same numbered-heading treatment /write uses
 *  (sectionHeading/partHeading), wrapping the lighter instructional content
 *  — description, "what to write" bullets, guidance note — in the
 *  `.draft-guidance-block` light-blue tint so it still reads as guidance to
 *  replace, not finished prose. */
function guidanceBody(section: DraftOutlineSection): string {
  const bullets = section.bullets.map((b) => `<li class="bnm-clause">${b}</li>`).join("");
  const heading =
    section.id === "executive-summary"
      ? `<div class="bnm-section-heading">${section.title}</div>`
      : sectionHeading(section.number, section.title);
  const part = section.partStart ? partHeading(section.partStart.letter, section.partStart.title) : "";
  return [
    part,
    heading,
    `<div class="draft-guidance-block">`,
    `<p class="bnm-clause">${section.description}</p>`,
    `<ul>${bullets}</ul>`,
    `<p class="bnm-clause"><em>${section.guidanceNote}</em></p>`,
    `</div>`,
  ].join("");
}

/** The instructional outline /draft inserts into the editor — same cover,
 *  TOC, BNM page format, header, and footer as /write's full document
 *  (Task 5's copilotFullDocument.ts, via the shared copilotDocumentChrome
 *  module), one page per DRAFT_OUTLINE_SECTIONS entry. Only the body
 *  content differs: a light-blue guidance block instead of full prose +
 *  citations. Real editable content the drafter overwrites by clicking and
 *  typing, never an HTML `placeholder` attribute. Uses only
 *  div/p/span/ul/li/strong/em, all already allowed by both the client
 *  (DOMPurify) and server (bleach, engine/drafts.py) sanitizers. */
export function buildDraftOutline(): string {
  const totalPages = 2 + DRAFT_OUTLINE_SECTIONS.length; // cover + TOC + sections
  const cover = coverPage(WORKSTREAM_CONTEXT.owner, WORKSTREAM_CONTEXT.name, "Instructional Outline — Draft");
  const toc = tocPage(buildTocEntries(), 2, totalPages);
  const pages = DRAFT_OUTLINE_SECTIONS.map((section, i) =>
    pageChrome(i + 3, totalPages, guidanceBody(section)),
  );
  return `<div class="bnm-doc">${cover}${toc}${pages.join("")}</div>`;
}
