import { useMutation } from "@tanstack/react-query";

import { analyzeEdge } from "@/lib/api";
import type { AnalyzeResponse } from "@/lib/types";

/** One mutation, shared by every "Analyze linkages" button in the app
 *  (graph screen's EdgeDetailPanel, task screen's CoverageStrip).
 *  Wrapping `useMutation` here — instead of each caller re-implementing its
 *  own pending/error state — is what gives every caller `isError` for free;
 *  a bare `useState` + `await` silently swallows a rejected call. */
export function useAnalyzeEdge(
  workstreamId: string,
  edgeId: string,
  opts?: { onSuccess?: (res: AnalyzeResponse) => void },
) {
  return useMutation({
    mutationFn: () => analyzeEdge(workstreamId, edgeId),
    onSuccess: opts?.onSuccess,
  });
}
