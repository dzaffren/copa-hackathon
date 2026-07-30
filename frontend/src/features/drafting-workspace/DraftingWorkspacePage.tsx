import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  fetchDraft,
  fetchReviewedLinkages,
  fetchTask,
  saveDraft,
} from "@/lib/api";
import { EditorPane, type EditorPaneHandle } from "./EditorPane";
import { CopilotTab } from "./CopilotTab";

type TabKey = "reviewed" | "recommendations" | "copilot";

const SAVE_DEBOUNCE_MS = 2000;

export function DraftingWorkspacePage() {
  const { workstreamId = "", nodeId = "" } = useParams();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<TabKey>("reviewed");
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

  const reviewedCards = reviewed.data?.findings ?? [];

  const tabs: { key: TabKey; label: string }[] = [
    { key: "reviewed", label: "Reviewed Findings" },
    { key: "recommendations", label: "Recommendations" },
    { key: "copilot", label: "Copilot" },
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
            to={`/workstreams/${workstreamId}`}
            className="text-xs font-semibold text-muted-foreground hover:text-foreground"
          >
            ← Workstream graph
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
              </button>
            ))}
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto">
            {tab === "reviewed" && (
              <div
                data-testid="reviewed-findings-empty"
                aria-label="Reviewed findings"
                className="flex h-full items-center justify-center p-6"
              >
                <p className="max-w-xs rounded-lg border border-dashed border-border/60 p-4 text-center text-sm text-muted-foreground">
                  Reviewed findings will appear here once your team's review data
                  is connected.
                </p>
              </div>
            )}

            {tab === "recommendations" && (
              <div
                data-testid="recommendations-empty"
                aria-label="Recommendations"
                className="flex h-full items-center justify-center p-6"
              >
                <p className="max-w-xs rounded-lg border border-dashed border-border/60 p-4 text-center text-sm text-muted-foreground">
                  Recommendations will appear here once your team's data is
                  connected.
                </p>
              </div>
            )}

            {/* Always mounted (like the editor pane) so its command transcript
                survives a tab switch instead of resetting to /pull-node-metadata
                every time the drafter checks another tab. Visibility toggles
                via the hidden class rather than mount/unmount. */}
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
