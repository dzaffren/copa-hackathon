import { useMemo } from "react";
import { marked } from "marked";
import DOMPurify from "dompurify";

// The Copilot replies in Markdown (bold key terms, bullet lists, short
// headings). We render it as sanitized HTML so `**bold**` and `- lists` show
// formatted instead of as literal characters. marked converts Markdown to
// HTML; DOMPurify then strips anything outside this restricted formatting set,
// so no raw/unsafe HTML from the model can reach the DOM.
const ALLOWED_TAGS = [
  "p",
  "br",
  "strong",
  "em",
  "u",
  "del",
  "code",
  "pre",
  "ul",
  "ol",
  "li",
  "blockquote",
  "h1",
  "h2",
  "h3",
  "h4",
  "a",
  "hr",
];
const ALLOWED_ATTR = ["href", "title", "target", "rel"];

marked.setOptions({ gfm: true, breaks: true });

// Compact prose styling tuned for the narrow chat column, applied via Tailwind
// arbitrary-variant selectors (the same pattern the draft snippet preview uses).
const PROSE_CLASS = [
  "text-sm leading-snug",
  "[&_p]:mb-2 [&_p:last-child]:mb-0",
  "[&_ul]:my-1 [&_ul]:list-disc [&_ul]:pl-5",
  "[&_ol]:my-1 [&_ol]:list-decimal [&_ol]:pl-5",
  "[&_li]:mb-0.5",
  "[&_strong]:font-semibold [&_strong]:text-foreground",
  "[&_h1]:mb-1 [&_h1]:mt-2 [&_h1]:text-sm [&_h1]:font-bold",
  "[&_h2]:mb-1 [&_h2]:mt-2 [&_h2]:text-[13px] [&_h2]:font-bold",
  "[&_h3]:mb-1 [&_h3]:mt-2 [&_h3]:text-[12px] [&_h3]:font-semibold",
  "[&_code]:rounded [&_code]:bg-card/70 [&_code]:px-1 [&_code]:py-0.5 [&_code]:font-mono [&_code]:text-[11px]",
  "[&_blockquote]:border-l-2 [&_blockquote]:border-border [&_blockquote]:pl-2 [&_blockquote]:italic",
  "[&_a]:text-cyan-400 [&_a]:underline",
].join(" ");

interface CopilotMarkdownProps {
  children: string;
  className?: string;
}

/** Render a Copilot reply written in Markdown as sanitized, formatted HTML.
 *  Used for both the streaming partial bubble and committed copilot messages. */
export function CopilotMarkdown({ children, className }: CopilotMarkdownProps) {
  const html = useMemo(() => {
    const raw = marked.parse(children ?? "", { async: false }) as string;
    return DOMPurify.sanitize(raw, { ALLOWED_TAGS, ALLOWED_ATTR });
  }, [children]);

  return (
    <div
      className={[PROSE_CLASS, className].filter(Boolean).join(" ")}
      // Content is Markdown from the model, converted by marked and sanitized
      // by DOMPurify above — never raw HTML rendered directly.
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
