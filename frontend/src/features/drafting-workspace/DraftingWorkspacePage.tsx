import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  fetchDraft,
  fetchRelatedLinkages,
  fetchReviewedLinkages,
  fetchTask,
  saveDraft,
} from "@/lib/api";
import type { LinkageCard } from "@/lib/types";
import { EditorPane } from "./EditorPane";
import { LinkageRefCard } from "./LinkageRefCard";
import { CopilotTab } from "./CopilotTab";

type TabKey = "reviewed" | "related" | "copilot";

const SAVE_DEBOUNCE_MS = 2000;

export function DraftingWorkspacePage() {
  const { workstreamId = "", nodeId = "" } = useParams();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<TabKey>("reviewed");
  const [activeCardId, setActiveCardId] = useState<string | null>(null);

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
  const related = useQuery({
    queryKey: ["related-linkages", workstreamId, nodeId],
    queryFn: () => fetchRelatedLinkages(workstreamId, nodeId),
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
    // Appended at end-of-draft rather than at the caret. The spec leaves this
    // open; end-of-draft is the predictable one, since the caret is usually
    // wherever the drafter last clicked in a *different* pane.
    const wrapped = `<div class="copilot-snippet">${snippetHtml}</div>`;
    const next = `${html ?? ""}${wrapped}`;
    setHtml(next);
    save.mutate(next);
  }

  const reviewedCards = reviewed.data?.findings ?? [];
  const relatedCards = related.data?.findings ?? [];

  const tabs: { key: TabKey; label: string; count: number | null }[] = [
    { key: "reviewed", label: "Reviewed", count: reviewedCards.length },
    { key: "related", label: "Related · 1 hop", count: relatedCards.length },
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
      <header className="flex items-center justify-between border-b border-border/60 bg-card/30 px-4 py-2.5 backdrop-blur">
        <div>
          <Link
            to={`/workstreams/${workstreamId}`}
            className="text-xs font-semibold text-muted-foreground hover:text-foreground"
          >
            ← Workstream graph
          </Link>
          <h1 className="mt-0.5 text-lg font-bold">
            {task.data?.task.title ?? "Working draft"}
          </h1>
        </div>
        <span className="rounded-full border border-emerald-400/30 bg-emerald-500/10 px-2.5 py-1 text-[11px] font-medium text-emerald-300">
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
                    ? "bg-cyan-500 text-slate-950"
                    : "text-muted-foreground hover:bg-accent",
                ].join(" ")}
              >
                {t.label}
                {t.count !== null && (
                  <span
                    data-testid={`count-${t.key}`}
                    className={[
                      "ml-1.5 rounded-full px-1.5 py-0.5 text-[10px]",
                      tab === t.key ? "bg-slate-950/20" : "bg-accent",
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
                    No accepted linkages yet. Findings you accept on the review
                    screen appear here, so the context you built up while
                    reviewing is next to the draft.
                  </p>
                ) : (
                  reviewedCards.map((c: LinkageCard) => (
                    <LinkageRefCard
                      key={c.id}
                      card={c}
                      isActive={activeCardId === c.id}
                      onSelect={() => setActiveCardId(c.id)}
                    />
                  ))
                )}
              </div>
            )}

            {tab === "related" && (
              <div className="space-y-2" aria-label="Related linkages">
                <p className="rounded-lg bg-muted/40 p-2.5 text-[12px] leading-snug text-muted-foreground">
                  Linkages between your task's neighbour documents themselves —
                  useful when your draft is silent on a concept the neighbours
                  have already settled.
                </p>
                {relatedCards.length === 0 ? (
                  <p
                    data-testid="related-empty"
                    className="rounded-lg border border-dashed border-border/60 p-3 text-sm text-muted-foreground"
                  >
                    No linkages between neighbour documents have been analysed
                    yet.
                  </p>
                ) : (
                  relatedCards.map((c: LinkageCard) => (
                    <LinkageRefCard key={c.id} card={c} showBothEndpoints />
                  ))
                )}
              </div>
            )}

            {/* Mounted only when active: the Copilot's chat is deliberately
                ephemeral, so unmounting is the intended reset. The editor pane
                lives outside this switch and never unmounts. */}
            {tab === "copilot" && (
              <CopilotTab
                workstreamId={workstreamId}
                nodeId={nodeId}
                onInsertSnippet={insertSnippet}
                reviewedCards={reviewedCards}
              />
            )}
          </div>
        </aside>

        <main className="col-span-7 min-h-0">
          <EditorPane
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
