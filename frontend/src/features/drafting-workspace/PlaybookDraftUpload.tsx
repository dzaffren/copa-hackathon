import { useRef, useState } from "react";
import { Upload } from "lucide-react";

/** A template picker on the `/draft` section that is **deliberately inert**.
 *
 *  NOTHING IS STORED, PARSED, OR SENT. Selecting a file shows its name and says
 *  so plainly. What actually configures the stage is the text in the textarea
 *  above.
 *
 *  This is recorded here, in the component itself, so a future reader finds it
 *  documented as a decision rather than filing it as a bug — and does not
 *  "finish" it by wiring an upload nobody asked for. The precedent is
 *  `EditorPane.tsx`'s formatting buttons, which carry
 *  `title="Formatting is not wired up in this build"` for the same reason.
 *
 *  A working upload needs parsing, storage, size limits and failure states; it is
 *  a follow-on, deferred in the spec's Open Questions.
 */
export function PlaybookDraftUpload() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [filename, setFilename] = useState<string | null>(null);

  return (
    <div className="mt-2">
      <input
        ref={inputRef}
        type="file"
        data-testid="playbook-upload-input"
        className="hidden"
        onChange={(event) => {
          setFilename(event.target.files?.[0]?.name ?? null);
          // Deliberately no read, no upload, no state beyond the name.
        }}
      />
      <button
        type="button"
        data-testid="playbook-upload"
        onClick={() => inputRef.current?.click()}
        className="inline-flex items-center gap-1.5 rounded-md border border-border/60 px-2 py-1 text-[11px] font-semibold text-muted-foreground transition hover:bg-accent hover:text-foreground"
      >
        <Upload className="h-3 w-3" />
        Attach a template
      </button>

      {filename && (
        <p
          data-testid="playbook-upload-note"
          className="mt-1 text-[11px] text-amber-800"
        >
          {filename} — template upload is not wired up in this build. Describe
          your template in the text above instead.
        </p>
      )}
    </div>
  );
}
