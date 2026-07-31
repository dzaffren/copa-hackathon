import {
  DRAFT_SECTIONS,
  WORKSTREAM_CONTEXT,
  type ClauseCitation,
  type DraftSection,
} from "./copilotV2Data";
import {
  DRAFT_OUTLINE_SECTIONS,
  buildTocEntries,
  type DraftOutlineSection,
} from "./copilotDraftOutline";
import {
  coverPage,
  pageChrome,
  sectionHeading,
  partHeading,
  tocPage,
} from "./copilotDocumentChrome";

function clause(num: string, text: string): string {
  return `<p class="bnm-clause"><span class="bnm-clause-num">${num}</span> ${text}</p>`;
}

function citation(c: ClauseCitation): string {
  return `<div class="bnm-blockquote"><strong>${c.clauseNumber}:</strong> &quot;${c.text}&quot;</div>`;
}

function timelineTable(): string {
  const rows = [
    ["Milestone", "Date", "Cohort"],
    [
      "Document submission & single account view interfaces live",
      "1 January 2028",
      "Mandated FSPs under §8.4",
    ],
    [
      "Data-sharing obligation commencement",
      "Per Appendix 2 schedule",
      "Mandated FSPs, phased by category",
    ],
    [
      "Individual and SME customer coverage complete",
      "On or after 1 January 2028",
      "All mandated data providers",
    ],
  ];
  const [header, ...body] = rows;
  return [
    `<div class="bnm-table">`,
    `<div class="bnm-table-header-row">${header.map((h) => `<div class="bnm-table-cell">${h}</div>`).join("")}</div>`,
    ...body.map(
      (r) =>
        `<div class="bnm-table-row">${r.map((c) => `<div class="bnm-table-cell">${c}</div>`).join("")}</div>`,
    ),
    `</div>`,
  ].join("");
}

function heading(outline: DraftOutlineSection): string {
  const part = outline.partStart
    ? partHeading(outline.partStart.letter, outline.partStart.title)
    : "";
  return part + sectionHeading(outline.number, outline.title);
}

function executiveSummaryBody(): string {
  return [
    `<div class="bnm-section-heading">Executive Summary</div>`,
    `<p class="bnm-clause">This Policy Document sets out Bank Negara Malaysia's requirements for open finance participation by licensed banks and eligible data providers. It consolidates the Exposure Draft on Open Finance 2025, benchmarked against the Hong Kong Monetary Authority's Open API Framework, BIS Papers 168 on open banking, and RMiT 2025, to produce a single set of consent-driven data-sharing obligations for the industry.</p>`,
    `<p class="bnm-clause">The draft affirms the objectives already shared across these documents — safer, consent-driven information sharing that gives customers control over how their financial data is used — while setting Malaysia-specific commencement dates, scope, and security controls. Two areas depart materially from the reviewed comparators: this PD mandates a real-time consent dashboard and a formal breach handling and response plan, neither of which has an equivalent in the HKMA framework.</p>`,
    `<p class="bnm-clause">Where this draft aligns with, differs from, or extends its anchor documents, each section below states so plainly against a verbatim clause citation, or states that no matching clause was found. No claim in this document is made without a citable source.</p>`,
  ].join("");
}

function introductionBody(o: DraftOutlineSection): string {
  return [
    heading(o),
    clause(
      "S 1.1",
      "As financial services continue to move onto digital platforms, the volume of customer information processed across the industry has grown substantially. This Part sets out a framework for the secure, permissioned sharing of that information between financial service providers.",
    ),
    clause(
      "S 1.2",
      "Open finance gives customers a structured, consent-driven means of sharing their financial information, replacing ad hoc bilateral arrangements with a common set of obligations that apply across the industry.",
    ),
    clause(
      "G 1.3",
      "Given the scale of this undertaking, the requirements in this Part are phased in over several years, allowing the industry and its customers to build familiarity and confidence in open finance before the full framework applies.",
    ),
  ].join("");
}

function applicabilityBody(o: DraftOutlineSection): string {
  return [
    heading(o),
    clause(
      "S 2.1",
      "This Part applies to all financial service providers as defined in the Interpretation section below.",
    ),
    clause(
      "S 2.2",
      "A narrower subset of financial service providers — those meeting the thresholds set out in Appendix 1 — are additionally subject to the mandated participation obligations in Transition Arrangements and the sections that follow it.",
    ),
  ].join("");
}

function legalProvisionBody(o: DraftOutlineSection): string {
  return [
    heading(o),
    clause(
      "S 3.1",
      "The requirements in this Part are issued pursuant to the legal provision confirmed for this task via /explore-task.",
    ),
    clause(
      "G 3.2",
      "The guidance in this Part is issued under the corresponding guidance-issuing provisions of the same enabling statutes.",
    ),
  ].join("");
}

function effectiveDateBody(o: DraftOutlineSection): string {
  return [
    heading(o),
    clause(
      "S 4.1",
      "This Part comes into effect on the confirmed effective date for this task, subject to the transition arrangements set out in Appendix 2.",
    ),
  ].join("");
}

function definitionsBody(o: DraftOutlineSection): string {
  return [
    heading(o),
    `<p class="bnm-clause">For the purpose of this Part —</p>`,
    clause(
      "",
      "“data provider” refers to a financial service provider that holds customer information and makes it available to a data consumer upon the customer's consent, in relation to an open finance arrangement;",
    ),
    clause(
      "",
      "“data consumer” refers to a financial service provider authorised by the customer to access their information from a data provider, upon obtaining the customer's consent;",
    ),
    clause(
      "",
      "“open finance arrangement” refers to the contractual relationship between a data provider and a data consumer that enables the permissioned sharing of customer information through an open finance platform;",
    ),
    clause(
      "",
      "“mandated financial service provider” or “mandated FSP” refers to a financial service provider that meets the thresholds specified in Appendix 1.",
    ),
  ].join("");
}

function governanceBody(o: DraftOutlineSection): string {
  return [
    heading(o),
    clause(
      "S 6.1",
      "The board and senior management shall exercise effective oversight of this Part's implementation, so that the financial service provider's participation in open finance is efficient, resilient, and secure.",
    ),
    clause(
      "S 6.2",
      "The board shall ensure a sound risk strategy and risk management framework is in place for open finance activities, consistent with the financial service provider's overall risk appetite.",
    ),
    clause(
      "S 6.3",
      "Senior management shall be responsible for developing and implementing the controls, policies, and procedures that give effect to the board's risk strategy for open finance.",
    ),
  ].join("");
}

function objectivesBody(section: DraftSection, o: DraftOutlineSection): string {
  return [
    heading(o),
    clause(
      "S 2.1",
      "This Part is issued under the Financial Services Act 2013 and sets out the objectives underpinning the open finance framework for licensed banks and eligible data providers.",
    ),
    clause("S 2.2", section.summary),
    clause(
      "S 2.3",
      "A financial service provider shall read this Part alongside the legal provision and policy requirement confirmed for this task, and shall not commence open finance activities in advance of the confirmed effective date.",
    ),
    citation(section.sourceCitations[0]),
    citation(section.targetCitations[0]),
  ].join("");
}

function scopeBody(section: DraftSection, o: DraftOutlineSection): string {
  return [
    heading(o),
    clause(
      "S 7.1",
      "This Part applies to licensed banks and eligible data providers participating in the open finance ecosystem, in respect of the scope of prescribed information defined below.",
    ),
    clause("S 7.2", section.summary),
    clause(
      "S 7.3",
      "Where a term used in this Part is not separately defined, it takes the meaning given to it in the Exposure Draft on Open Finance 2025.",
    ),
    citation(section.sourceCitations[0]),
    citation(section.targetCitations[0]),
  ].join("");
}

function tspGovernanceBody(
  section: DraftSection,
  o: DraftOutlineSection,
): string {
  return [
    heading(o),
    clause(
      "S 8.1",
      "A financial service provider shall ensure that its technology operations management practices are appropriately extended to support its open finance activities, including third-party service provider governance.",
    ),
    clause("S 8.2", section.summary),
    clause(
      "S 8.3",
      "A financial service provider shall maintain a register of third-party service providers engaged in its open finance arrangements and shall review that register at least annually.",
    ),
    citation(section.sourceCitations[0]),
    citation(section.targetCitations[0]),
  ].join("");
}

function apiSecurityBody(
  section: DraftSection,
  o: DraftOutlineSection,
): string {
  return [
    heading(o),
    clause(
      "S 9.1",
      "A financial service provider shall ensure that its cyber risk management capabilities and cybersecurity controls are appropriately extended to govern, identify, prevent, detect, respond to, and address cyber risks associated with open finance activities.",
    ),
    clause("S 9.2", section.summary),
    clause(
      "S 9.3",
      "These controls apply uniformly from the effective date of this Part; a financial service provider shall not implement a phased or category-differentiated level of protection in place of the uniform controls required here.",
    ),
    citation(section.sourceCitations[0]),
    citation(section.targetCitations[0]),
  ].join("");
}

function timelineBody(section: DraftSection, o: DraftOutlineSection): string {
  return [
    heading(o),
    clause(
      "S 10.1",
      "The obligations of a mandated financial service provider under this Part shall commence in accordance with the timeline specified in Appendix 2.",
    ),
    clause("S 10.2", section.summary),
    clause(
      "S 10.3",
      "A mandated financial service provider shall commence its obligation to provide document submission and single account view interfaces by 1 January 2028, or the date on which its obligations under this Part otherwise commence, whichever is later.",
    ),
    timelineTable(),
    citation(section.sourceCitations[0]),
    ...section.targetCitations.map(citation),
  ].join("");
}

function consentBody(section: DraftSection, o: DraftOutlineSection): string {
  return [
    heading(o),
    clause(
      "S 11.1",
      "A data provider shall not disclose a customer's information to a data consumer, or a third party engaged by a data consumer, without the customer's explicit and informed consent.",
    ),
    clause("S 11.2", section.summary),
    clause(
      "S 11.3",
      "Separate and distinct consent must be obtained before a customer's information is disclosed to any third party engaged to support the offering of a product or service, distinct from the consent given for the underlying open finance arrangement itself.",
    ),
    citation(section.sourceCitations[0]),
    citation(section.targetCitations[0]),
  ].join("");
}

function consentMonitoringBody(o: DraftOutlineSection): string {
  return [
    heading(o),
    clause(
      "S 12.1",
      "A financial service provider shall maintain a consent dashboard through which a customer may view, manage, and revoke consents given under an open finance arrangement, updated in real time.",
    ),
    clause(
      "S 12.2",
      "Consent granted for one-time data access expires immediately once the consented information has been retrieved. Consent granted for recurring access remains valid for no longer than six months from the date it was granted, unless revoked earlier.",
    ),
    clause(
      "S 12.3",
      "Upon a customer's request to revoke consent, a data consumer shall immediately cease any further access to the customer's information and notify the corresponding data provider without undue delay.",
    ),
    clause(
      "S 12.4",
      "A financial service provider shall log every consent action — granted, renewed, revoked — in an auditable format, retained for a period consistent with the FSP's records-management policy.",
    ),
  ].join("");
}

function dataPrivacySecurityBody(o: DraftOutlineSection): string {
  return [
    heading(o),
    clause(
      "S 13.1",
      "A financial service provider shall establish data governance and privacy policies that limit access to customer information to a need-to-know basis and prohibit its use beyond the purpose for which consent was granted.",
    ),
    clause(
      "S 13.2",
      "Retention schedules shall ensure customer information is not kept longer than necessary, with secure disposal required once its consented purpose has been fulfilled.",
    ),
    clause(
      "S 13.3",
      "A financial service provider shall implement technical and operational safeguards to prevent theft, loss, misuse, or unauthorised access to customer information exchanged under an open finance arrangement.",
    ),
    `<p class="bnm-clause"><em>No matching citation was found among the confirmed anchor documents for this section — it is drafted as this PD's own synthesis, not a benchmarked comparison.</em></p>`,
  ].join("");
}

function thirdPartyArrangementsBody(o: DraftOutlineSection): string {
  return [
    heading(o),
    clause(
      "S 14.1",
      "A financial service provider shall ensure that any third-party service provider handling customer information in connection with an open finance arrangement is subject to privacy, confidentiality, and security requirements at least equivalent to those set out in this Part.",
    ),
    clause(
      "S 14.2",
      "Customer information shall not be shared with a third-party service provider without the customer's explicit consent, obtained in accordance with Consent Management above.",
    ),
    clause(
      "S 14.3",
      "The obligation to safeguard customer information shall be reflected in the service-level agreement between the financial service provider and the third-party service provider.",
    ),
    `<p class="bnm-clause"><em>No matching citation was found among the confirmed anchor documents for this section — it is drafted as this PD's own synthesis, not a benchmarked comparison.</em></p>`,
  ].join("");
}

function breachResponseBody(
  section: DraftSection,
  o: DraftOutlineSection,
): string {
  return [
    heading(o),
    clause(
      "S 15.1",
      "A financial service provider shall provide customers with a real-time consent dashboard through which a customer may view, manage, and withdraw consents given in respect of open finance arrangements.",
    ),
    clause("S 15.2", section.summary),
    clause(
      "S 15.3",
      "A financial service provider shall maintain a breach handling and response plan for theft, loss, misuse, or unauthorised access, modification, or disclosure of customer information associated with an open finance arrangement. The plan shall, at a minimum, include escalation procedures and a clear line of responsibility to contain the breach and take remedial action.",
    ),
    `<p class="bnm-clause"><em>No matching source clause was found in the connected anchor documents for the consent dashboard or breach-response requirements above — the HKMA Open API Framework addresses TSP monitoring and scam notification but has no equivalent breach-handling-plan requirement. These clauses are drafted as considered new policy, not as a citation to an anchor document.</em></p>`,
    ...section.targetCitations.map(citation),
  ].join("");
}

function complaintsHandlingBody(o: DraftOutlineSection): string {
  return [
    heading(o),
    clause(
      "S 16.1",
      "Where a dispute involves more than one financial service provider, the parties shall collaborate to ensure a coordinated and timely resolution. Absent an applicable protocol, the financial service provider that first receives the complaint shall lead the resolution process, unless the parties agree otherwise.",
    ),
    clause(
      "S 16.2",
      "A financial service provider's complaints handling procedures for open finance activities shall be consistent with its existing complaints handling policy document.",
    ),
    clause(
      "G 16.3",
      "A financial service provider may endeavour to make complaint channels accessible and inclusive, including the option to interact with a human representative where needed.",
    ),
    `<p class="bnm-clause"><em>No matching citation was found among the confirmed anchor documents for this section — it is drafted as this PD's own synthesis, not a benchmarked comparison.</em></p>`,
  ].join("");
}

function techRiskBody(o: DraftOutlineSection): string {
  return [
    heading(o),
    clause(
      "S 17.1",
      "A financial service provider shall ensure that its existing technology risk management requirements are extended to govern its open finance activities.",
    ),
    clause(
      "S 17.2",
      "A financial service provider shall comply with the technology and operational requirements of the open finance platform for which it is a member, including requirements relating to API specifications, uptime, and independent review.",
    ),
    `<p class="bnm-clause"><em>No matching citation was found among the confirmed anchor documents for this section — it is drafted as this PD's own synthesis, not a benchmarked comparison.</em></p>`,
  ].join("");
}

function appendixDefinitionsBody(o: DraftOutlineSection): string {
  return [
    heading(o),
    clause(
      "1",
      "A mandated FSP is a financial service provider that meets the applicable customer-count or active-user threshold for its category, measured at entity level or banking-group level, whichever the drafter confirms is applicable.",
    ),
    clause(
      "2",
      "The scope of prescribed information comprises transaction information for the most recent 12 months (date, description, and value) and the current outstanding balance of the relevant account.",
    ),
  ].join("");
}

function appendixTimelineBody(o: DraftOutlineSection): string {
  return [
    heading(o),
    `<p class="bnm-clause">The obligations of a mandated financial service provider commence as follows:</p>`,
    timelineTable(),
  ].join("");
}

const SECTION_BUILDERS: Record<string, (o: DraftOutlineSection) => string> = {
  introduction: introductionBody,
  applicability: applicabilityBody,
  "legal-provision": legalProvisionBody,
  "effective-date": effectiveDateBody,
  definitions: definitionsBody,
  governance: governanceBody,
  "consent-monitoring": consentMonitoringBody,
  "data-privacy-security": dataPrivacySecurityBody,
  "third-party-arrangements": thirdPartyArrangementsBody,
  "complaints-handling": complaintsHandlingBody,
  "tech-risk": techRiskBody,
  "appendix-definitions": appendixDefinitionsBody,
  "appendix-timeline": appendixTimelineBody,
};

const CITED_SECTION_BUILDERS: Record<
  string,
  (s: DraftSection, o: DraftOutlineSection) => string
> = {
  objectives: objectivesBody,
  scope: scopeBody,
  "tsp-governance": tspGovernanceBody,
  "api-security": apiSecurityBody,
  timeline: timelineBody,
  consent: consentBody,
  "breach-response": breachResponseBody,
};

/** The full document /write auto-populates into the editor: a cover page, a
 *  table of contents, and one page per DRAFT_OUTLINE_SECTIONS entry. The 7
 *  sections that map onto DRAFT_SECTIONS quote their citation(s) verbatim —
 *  never re-paraphrased; the rest are this PD's own original policy
 *  synthesis, honestly marked as uncited where no anchor-document match
 *  exists. Page shell, header, footer, and typography are styled (via the
 *  .bnm-* classes in index.css) to match the real BNM Exposure Draft's
 *  visual presentation. */
export function buildFullDraft(): string {
  const totalPages = 2 + DRAFT_OUTLINE_SECTIONS.length; // cover + TOC + sections
  const toc = tocPage(buildTocEntries(), 2, totalPages);
  const bodyPages = DRAFT_OUTLINE_SECTIONS.map((outline, i) => {
    const pageNumber = i + 3;
    let body: string;
    if (outline.id === "executive-summary") {
      body = executiveSummaryBody();
    } else if (CITED_SECTION_BUILDERS[outline.id]) {
      const section = DRAFT_SECTIONS.find(
        (s) => s.id === outline.id,
      ) as DraftSection;
      body = CITED_SECTION_BUILDERS[outline.id](section, outline);
    } else {
      body = SECTION_BUILDERS[outline.id](outline);
    }
    return pageChrome(pageNumber, totalPages, body);
  });
  const cover = coverPage(
    WORKSTREAM_CONTEXT.owner,
    WORKSTREAM_CONTEXT.name,
    "Policy Document — Draft",
  );
  return `<div class="bnm-doc">${cover}${toc}${bodyPages.join("")}</div>`;
}
