import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  fetchDraft,
  fetchReviewedLinkages,
  fetchTask,
  saveDraft,
  setReviewState,
} from "@/lib/api";
import { bySeverity } from "@/lib/labels";
import type { LinkageCard } from "@/lib/types";
import { EditorPane, type EditorPaneHandle } from "./EditorPane";
import { LinkageRefCard } from "./LinkageRefCard";
import { CopilotTab } from "./CopilotTab";

/** Two tabs. "Related · 1 hop" was retired with the Pairwise Findings epic: the
 *  box on the task page covers the same peer material more completely and with
 *  review state attached, where Related showed unjudged findings beside the draft
 *  as though the drafter had endorsed them. The vacated slot stays EMPTY rather
 *  than holding a disabled placeholder for the future Recommendations tab. */
type TabKey = "reviewed" | "copilot";

const SAVE_DEBOUNCE_MS = 2000;

export function DraftingWorkspacePage() {
  const { workstreamId = "", nodeId = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<TabKey>("reviewed");
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const editorRef = useRef<EditorPaneHandle>(null);

  const task = useQuery({
    queryKey: ["task", workstreamId, nodeId],
    queryFn: () => fetchTask(workstreamId, nodeId),
  });
  const draft = useQuery({
    queryKey: ["draft", workstreamId, nodeId],
    queryFn: () => fetchDraft(workstreamId, nodeId),
  });
  const reviewed = useQuery({
    queryKey: ["reviewed-linkages", workstreamId, nodeId],
    queryFn: () => fetchReviewedLinkages(workstreamId, nodeId),
  });

  const [withdrawErrors, setWithdrawErrors] = useState<Record<string, string>>(
    {},
  );

  // Withdrawal is the tab's ONLY state transition (accepted → pending), so a
  // change of mind mid-draft does not send the drafter back to the task page.
  // Optimistic: the card leaves the list at once and the badge decrements.
  const withdraw = useMutation({
    mutationFn: (card: LinkageCard) =>
      setReviewState(workstreamId, card.edge_id, card.id, "pending"),
    onMutate: async (card) => {
      setWithdrawErrors((prev) => {
        const { [card.id]: _dropped, ...rest } = prev;
        return rest;
      });
      const key = ["reviewed-linkages", workstreamId, nodeId];
      await queryClient.cancelQueries({ queryKey: key });
      const previous = queryClient.getQueryData<{ findings: LinkageCard[] }>(
        key,
      );
      queryClient.setQueryData<{ findings: LinkageCard[] }>(key, (old) =>
        old
          ? { ...old, findings: old.findings.filter((f) => f.id !== card.id) }
          : old,
      );
      return { previous };
    },
    onError: (_err, card, context) => {
      if (context?.previous) {
        queryClient.setQueryData(
          ["reviewed-linkages", workstreamId, nodeId],
          context.previous,
        );
      }
      setWithdrawErrors((prev) => ({
        ...prev,
        [card.id]: "Could not withdraw that decision. Try again.",
      }));
    },
    onSuccess: (_data, card) => {
      // The box and the comparison screen read the same review state — miss one
      // and it shows a decision the drafter has already reversed.
      queryClient.invalidateQueries({
        queryKey: ["pairwise-findings", workstreamId, nodeId],
      });
      queryClient.invalidateQueries({
        queryKey: ["review", workstreamId, card.edge_id],
      });
    },
  });

  // The draft the editor is showing. Seeded from the server once loaded, then
  // owned here so a Copilot insert and a keystroke go through the same path.
  const [html, setHtml] = useState<string | null>(null);
  useEffect(() => {
    if (draft.data && html === null) setHtml(draft.data.content_html);
  }, [draft.data, html]);

  const save = useMutation({
    mutationFn: (content: string) => saveDraft(workstreamId, nodeId, content),
    onSuccess: (saved) =>
      queryClient.setQueryData(["draft", workstreamId, nodeId], saved),
  });

  // Trailing debounce: a policy drafter types in bursts, and a PUT per
  // keystroke would be both wasteful and a great way to lose a race.
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const saveRef = useRef(save);
  saveRef.current = save;
  function edit(next: string) {
    setHtml(next);
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(
      () => saveRef.current.mutate(next),
      SAVE_DEBOUNCE_MS,
    );
  }
  useEffect(
    () => () => void (timer.current && clearTimeout(timer.current)),
    [],
  );

  function insertSnippet(snippetHtml: string) {
    // Lands at the drafter's last cursor position in the editor (falling
    // back to end-of-draft if they've never clicked into it) — the drafter
    // decides where a suggested clause goes, rather than it always appending.
    const wrapped = `<div class="copilot-snippet">${snippetHtml}</div>`;
    const next = editorRef.current?.insertAtCursor(wrapped);
    if (next == null) return;
    setHtml(next);
    save.mutate(next);
  }

  function replaceDraft(documentHtml: string) {
    // /draft and /write each generate the whole document, not a snippet to
    // land beside existing text — running one after the other replaces the
    // page, it doesn't stack the new pages on top of the old ones.
    const wrapped = `<div class="copilot-snippet">${documentHtml}</div>`;
    const next = editorRef.current?.replaceContent(wrapped);
    if (next == null) return;
    setHtml(next);
    save.mutate(next);
  }

  // Attention order (conflicts-with first, aligns-with last), the same order the
  // task page, review screen and edge detail use. Every card here is accepted by
  // construction — the engine filters — so review state is not a sort axis.
  const reviewedCards = bySeverity(reviewed.data?.findings ?? []);

  const tabs: { key: TabKey; label: string; count: number | null }[] = [
    { key: "reviewed", label: "Reviewed", count: reviewedCards.length },
    { key: "copilot", label: "Copilot", count: null },
  ];

  if (task.isError) {
    return (
      <div className="mx-auto max-w-3xl p-8">
        <p className="text-sm text-muted-foreground">
          This draft could not be opened — {nodeId} is not a task in this
          workstream.
        </p>
        <Link
          to={`/workstreams/${workstreamId}`}
          className="text-sm font-semibold text-primary underline-offset-4 hover:underline"
        >
          ← Workstream graph
        </Link>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center justify-between border-b border-border/60 bg-card px-4 py-2.5">
        <div>
          <Link
            to={`/workstreams/${workstreamId}/tasks/${nodeId}`}
            className="text-xs font-semibold text-muted-foreground hover:text-foreground"
          >
            ← Task
          </Link>
          <h1 className="mt-0.5 text-lg font-bold">
            {task.data?.task.title ?? "Working draft"}
          </h1>
        </div>
        <span className="rounded-full border border-emerald-400/30 bg-emerald-500/10 px-2.5 py-1 text-[11px] font-medium text-emerald-700">
          Auto-saved
        </span>
      </header>

      <div className="grid min-h-0 flex-1 grid-cols-12">
        <aside className="col-span-5 flex min-h-0 flex-col border-r border-border/60 p-3">
          <div role="tablist" className="mb-3 flex gap-1">
            {tabs.map((t) => (
              <button
                key={t.key}
                role="tab"
                aria-selected={tab === t.key}
                onClick={() => setTab(t.key)}
                className={[
                  "rounded-md px-2.5 py-1.5 text-xs font-semibold transition",
                  tab === t.key
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent",
                ].join(" ")}
              >
                {t.label}
                {t.count !== null && (
                  <span
                    data-testid={`count-${t.key}`}
                    className={[
                      "ml-1.5 rounded-full px-1.5 py-0.5 text-[10px]",
                      tab === t.key ? "bg-primary-foreground/20" : "bg-accent",
                    ].join(" ")}
                  >
                    {t.count}
                  </span>
                )}
              </button>
            ))}
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto">
            {tab === "reviewed" && (
              <div className="space-y-2" aria-label="Reviewed linkages">
                {reviewedCards.length === 0 ? (
                  <p className="rounded-lg bg-muted/40 p-3 text-sm text-muted-foreground">
                    No findings accepted yet. Accept linkages in the Pairwise
                    findings box on the task page and they appear here, so the
                    decisions you made surveying the landscape sit next to the
                    draft.
                  </p>
                ) : (
                  reviewedCards.map((c: LinkageCard) => (
                    <LinkageRefCard
                      key={c.id}
                      card={c}
                      isActive={activeCardId === c.id}
                      onSelect={() => {
                        setActiveCardId(c.id);
                        // Deep-links to this finding, not the pair's first.
                        navigate(
                          `/workstreams/${workstreamId}/edges/${c.edge_id}/review` +
                            `?finding=${encodeURIComponent(c.id)}`,
                        );
                      }}
                      onWithdraw={() => withdraw.mutate(c)}
                      isWithdrawing={
                        withdraw.isPending && withdraw.variables?.id === c.id
                      }
                      errorMessage={withdrawErrors[c.id]}
                    />
                  ))
                )}
              </div>
            )}

            {/* Always mounted (like the editor pane) so its command transcript
                survives a tab switch instead of resetting every time the
                drafter checks another tab. Visibility toggles via the hidden
                class rather than mount/unmount. */}
            <div className={tab === "copilot" ? "h-full" : "hidden"}>
              <CopilotTab
                workstreamId={workstreamId}
                nodeId={nodeId}
                onInsertSnippet={insertSnippet}
                onReplaceDraft={replaceDraft}
                reviewedCards={reviewedCards}
                getDraftContext={() => ({
                  draftHtml: html ?? "",
                  selectionText: editorRef.current?.getSelectionText() ?? "",
                })}
              />
            </div>
          </div>
        </aside>

        <main className="col-span-7 min-h-0">
          <EditorPane
            ref={editorRef}
            contentHtml={html ?? ""}
            lastSavedAt={draft.data?.last_saved_at ?? null}
            linkages={reviewedCards}
            onChange={edit}
            isSaving={save.isPending}
          />
        </main>
      </div>
    </div>
  );
}
