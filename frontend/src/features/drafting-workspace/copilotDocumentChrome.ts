// Shared BNM-styled page chrome — the same cover page, header, footer,
// section-heading, and table-of-contents treatment used by both /write's
// full document (copilotFullDocument.ts) and /draft's instructional outline
// (copilotDraftOutline.ts), so the outline previews exactly what the
// finished document will look like: same format, same header, same cover
// and TOC structure — only the body content differs (light instructional
// guidance vs. full prose).

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

function formattedDate(d: Date): string {
  return `${String(d.getDate()).padStart(2, "0")} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
}

export function coverPage(owner: string, workstreamName: string, label: string): string {
  const date = formattedDate(new Date());
  return [
    `<div class="bnm-page bnm-cover">`,
    `<div class="bnm-cover-logo-row"><img class="bnm-seal" src="/bnm-logo.png" alt="Bank Negara Malaysia" /><div class="bnm-logo">Bank Negara Malaysia</div></div>`,
    `<div class="bnm-cover-title-row">`,
    `<div class="bnm-title">Open Finance</div>`,
    `<div class="bnm-draft-label">${label}</div>`,
    `</div>`,
    `<div class="bnm-meta">`,
    `<p>Drafter: ${owner}</p>`,
    `<p>Date: ${date}</p>`,
    `<p>Workstream: ${workstreamName}</p>`,
    `</div>`,
    `<div class="bnm-cover-footer"><span>Issued on: ${date}</span><span>PROJECT SELARAS — DRAFT V1</span></div>`,
    `</div>`,
  ].join("");
}

export function pageChrome(pageNumber: number, totalPages: number, body: string): string {
  return [
    `<div class="bnm-page">`,
    `<div class="bnm-header"><span>Open Finance</span><span>${pageNumber} of ${totalPages}</span></div>`,
    body,
    `<div class="bnm-footer"><span>Bank Negara Malaysia</span><span>Internal Draft — Not for Distribution</span></div>`,
    `</div>`,
  ].join("");
}

/** Inline numbered heading — "7. Governance" on one line, matching the real
 *  document's convention, not a stacked "SECTION N" / title treatment. */
export function sectionHeading(number: string, title: string): string {
  return `<div class="bnm-section-heading">${number}. ${title}</div>`;
}

export function partHeading(letter: string, title: string): string {
  return `<div class="bnm-part-heading">PART ${letter} ${title}</div>`;
}

export interface TocEntry {
  /** Number shown before the title, e.g. "7" or "Appendix 1" — blank for a
   *  PART divider row. */
  number: string;
  title: string;
  /** True for a PART divider row (bold, no dot leader). */
  isPart?: boolean;
}

/** A table-of-contents page: part dividers plus numbered rows with a
 *  dotted leader — the same visual convention the reference document uses,
 *  built from this document's own section list, not copied from any
 *  source's actual entries. */
export function tocPage(entries: TocEntry[], pageNumber: number, totalPages: number): string {
  const rows = entries
    .map((e) =>
      e.isPart
        ? `<div class="bnm-toc-part">${e.number ? `${e.number} ` : ""}${e.title}</div>`
        : `<div class="bnm-toc-row"><span class="bnm-toc-num">${e.number}</span><span class="bnm-toc-title">${e.title}</span></div>`,
    )
    .join("");
  const body = [
    `<div class="bnm-toc-heading">Table of Contents</div>`,
    `<div class="bnm-toc">${rows}</div>`,
  ].join("");
  return pageChrome(pageNumber, totalPages, body);
}
