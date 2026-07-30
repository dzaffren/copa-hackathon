export interface AutocompleteItem {
  id: string;
  label: string;
  description?: string;
}

/** A vertical, stacked, full-width filterable menu — the Claude-Code slash /
 *  mention affordance. Anchored above the chat input (`bottom-full`). Purely
 *  presentational: the parent owns filtering, the highlighted index, and
 *  keyboard handling; this renders and reports clicks/hovers.
 *
 *  `testId` distinguishes the slash menu from the mention menu; each row also
 *  carries `data-testid="autocomplete-item"` and `role="option"`. */
export function AutocompleteMenu({
  items,
  highlight,
  onPick,
  onHover,
  testId,
  emptyLabel,
}: {
  items: AutocompleteItem[];
  highlight: number;
  onPick: (item: AutocompleteItem) => void;
  onHover: (index: number) => void;
  testId: string;
  emptyLabel?: string;
}) {
  return (
    <div
      data-testid={testId}
      role="listbox"
      className="absolute bottom-full left-0 right-0 z-20 mb-1.5 flex max-h-60 flex-col overflow-y-auto rounded-lg border border-border/70 bg-popover p-1 shadow-lg"
      style={{ animation: "fadeSlideUp 0.16s var(--ease-out-expo) both" }}
    >
      {items.length === 0 ? (
        <p className="px-2.5 py-2 text-xs text-muted-foreground">
          {emptyLabel ?? "No matches"}
        </p>
      ) : (
        items.map((item, i) => (
          <button
            key={item.id}
            type="button"
            role="option"
            aria-selected={i === highlight}
            data-testid="autocomplete-item"
            // Use onMouseDown (not onClick) so the pick fires before the input's
            // blur — clicking a row must not first blur-close the menu.
            onMouseDown={(e) => {
              e.preventDefault();
              onPick(item);
            }}
            onMouseEnter={() => onHover(i)}
            className={`flex w-full items-baseline gap-2 rounded-md px-2.5 py-1.5 text-left transition-colors ${
              i === highlight
                ? "border border-primary/40 bg-primary/10"
                : "border border-transparent hover:bg-accent"
            }`}
          >
            <span className="shrink-0 font-mono text-[12px] font-semibold text-primary">
              {item.label}
            </span>
            {item.description && (
              <span className="min-w-0 flex-1 truncate text-[11px] text-muted-foreground">
                {item.description}
              </span>
            )}
          </button>
        ))
      )}
    </div>
  );
}
