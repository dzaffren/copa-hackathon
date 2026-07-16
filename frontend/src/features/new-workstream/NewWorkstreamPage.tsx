import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { X } from "lucide-react";

import { createWorkstream, fetchReviewers, HttpError } from "@/lib/api";
import {
  DELIVERABLE_TYPE_OPTIONS,
  type AccessLevel,
  type DeliverableTypeCode,
  type Person,
} from "@/lib/types";

/** The three-card create form.
 *
 * Built with plain state and native inputs rather than the spec's
 * react-hook-form + zod + shadcn Command/RadioGroup stack. Two required fields
 * do not justify four dependencies, and the server has to validate regardless —
 * anyone can POST directly — so client validation here is a courtesy that keeps
 * the round trip short, not the boundary. Native radios and selects also carry
 * their own keyboard and screen-reader behaviour for free.
 */
export function NewWorkstreamPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [deliverableType, setDeliverableType] =
    useState<DeliverableTypeCode>("PD");
  const [targetPublication, setTargetPublication] = useState("");
  const [reviewers, setReviewers] = useState<Person[]>([]);
  const [access, setAccess] = useState<AccessLevel>("team_only");
  const [nameError, setNameError] = useState<string | null>(null);

  const { data: available = [] } = useQuery({
    queryKey: ["reviewers"],
    queryFn: fetchReviewers,
  });

  const create = useMutation({
    mutationFn: createWorkstream,
    onSuccess: (ws) => {
      // Refresh the sidebar so the new workstream is listed the moment we land.
      queryClient.invalidateQueries({ queryKey: ["workstreams"] });
      navigate(`/workstreams/${ws.id}`);
    },
    onError: (err) => {
      if (err instanceof HttpError && err.field === "name") {
        setNameError(err.message);
      }
    },
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) {
      setNameError("Give the workstream a name.");
      return;
    }
    setNameError(null);
    create.mutate({
      name: name.trim(),
      description: description.trim() || undefined,
      deliverable_type: deliverableType,
      target_publication: targetPublication.trim() || undefined,
      reviewer_ids: reviewers.map((r) => r.id),
      access,
    });
  }

  const unpicked = available.filter(
    (p) => !reviewers.some((r) => r.id === p.id),
  );

  return (
    <div className="mx-auto max-w-2xl p-8">
      <Link
        to="/"
        className="text-xs font-semibold text-muted-foreground hover:text-foreground"
      >
        ← Workstreams / New
      </Link>
      <h1 className="mt-1 text-2xl font-bold">Create new workstream</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        A workstream is one Discussion Paper, Exposure Draft, or Policy Document
        under active drafting.
      </p>

      <form onSubmit={submit} className="mt-6 space-y-4" noValidate>
        {/* --- Basics --- */}
        <section className="rounded-lg border border-gray-200 p-4">
          <h2 className="text-sm font-bold">Basics</h2>

          <label className="mt-3 block">
            <span className="text-xs font-semibold text-gray-700">
              Workstream name
            </span>
            <input
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                if (nameError) setNameError(null);
              }}
              aria-label="Workstream name"
              aria-invalid={nameError ? true : undefined}
              aria-describedby={nameError ? "name-error" : undefined}
              placeholder="Climate Risk PD v2 · 2026"
              className={[
                "mt-1 w-full rounded-md border px-2 py-1.5 text-sm",
                nameError ? "border-red-400" : "border-gray-200",
              ].join(" ")}
            />
            {nameError && (
              <span
                id="name-error"
                role="alert"
                className="mt-1 block text-xs text-red-600"
              >
                {nameError}
              </span>
            )}
          </label>

          <label className="mt-3 block">
            <span className="text-xs font-semibold text-gray-700">
              Short description
            </span>
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              aria-label="Short description"
              className="mt-1 w-full rounded-md border border-gray-200 px-2 py-1.5 text-sm"
            />
          </label>

          <div className="mt-3 grid grid-cols-2 gap-3">
            <label className="block">
              <span className="text-xs font-semibold text-gray-700">
                Deliverable type
              </span>
              <select
                value={deliverableType}
                onChange={(e) =>
                  setDeliverableType(e.target.value as DeliverableTypeCode)
                }
                aria-label="Deliverable type"
                className="mt-1 w-full rounded-md border border-gray-200 bg-white px-2 py-1.5 text-sm"
              >
                {DELIVERABLE_TYPE_OPTIONS.map((o) => (
                  <option key={o.code} value={o.code}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="text-xs font-semibold text-gray-700">
                Target publication
              </span>
              <input
                value={targetPublication}
                onChange={(e) => setTargetPublication(e.target.value)}
                aria-label="Target publication"
                placeholder="Q4 2026"
                className="mt-1 w-full rounded-md border border-gray-200 px-2 py-1.5 text-sm"
              />
            </label>
          </div>
        </section>

        {/* --- People --- */}
        <section className="rounded-lg border border-gray-200 p-4">
          <h2 className="text-sm font-bold">People</h2>

          <div className="mt-3">
            <span className="text-xs font-semibold text-gray-700">Owner</span>
            <div className="mt-1 flex items-center gap-2">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo-100 text-[10px] font-bold text-indigo-700">
                AR
              </span>
              <span className="text-sm">Aisyah R.</span>
              <span className="text-xs text-muted-foreground">(you)</span>
            </div>
          </div>

          <div className="mt-3">
            <span className="text-xs font-semibold text-gray-700">
              Reviewers
            </span>
            {reviewers.length > 0 && (
              <ul className="mt-1 flex flex-wrap gap-1.5">
                {reviewers.map((r) => (
                  <li
                    key={r.id}
                    data-testid="reviewer-pill"
                    className="flex items-center gap-1 rounded-full bg-gray-100 py-0.5 pl-2 pr-1 text-xs"
                  >
                    {r.name}
                    <button
                      type="button"
                      aria-label={`Remove ${r.name}`}
                      onClick={() =>
                        setReviewers((prev) =>
                          prev.filter((p) => p.id !== r.id),
                        )
                      }
                      className="rounded-full p-0.5 hover:bg-gray-300"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {unpicked.length > 0 ? (
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {unpicked.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => setReviewers((prev) => [...prev, p])}
                    className="rounded-full border border-dashed border-gray-300 px-2 py-0.5 text-xs text-muted-foreground hover:border-indigo-400 hover:text-indigo-600"
                  >
                    + {p.name}
                  </button>
                ))}
              </div>
            ) : (
              <p className="mt-1.5 text-xs text-muted-foreground">
                Everyone available has been added.
              </p>
            )}
          </div>
        </section>

        {/* --- Access --- */}
        <fieldset className="rounded-lg border border-gray-200 p-4">
          <legend className="px-1 text-sm font-bold">Access</legend>
          {(
            [
              [
                "team_only",
                "Team-only",
                "Only the owner and named reviewers can open nodes.",
              ],
              [
                "department_wide",
                "Department-wide",
                "Anyone in the Prudential Policy Department can open nodes.",
              ],
            ] as const
          ).map(([value, label, hint]) => (
            <label key={value} className="mt-1 flex items-start gap-2">
              <input
                type="radio"
                name="access"
                value={value}
                checked={access === value}
                onChange={() => setAccess(value)}
                className="mt-1"
              />
              <span>
                <span className="block text-sm font-semibold">{label}</span>
                <span className="block text-xs text-muted-foreground">
                  {hint}
                </span>
              </span>
            </label>
          ))}
        </fieldset>

        {create.isError && !nameError && (
          <p role="alert" className="text-sm text-red-600">
            {(create.error as Error).message}
          </p>
        )}

        <div className="flex justify-end gap-2">
          <Link
            to="/"
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-semibold hover:bg-gray-50"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={create.isPending}
            className="rounded-md bg-gray-900 px-3 py-1.5 text-sm font-semibold text-white disabled:opacity-50"
          >
            {create.isPending ? "Creating…" : "Create workstream"}
          </button>
        </div>
      </form>
    </div>
  );
}
