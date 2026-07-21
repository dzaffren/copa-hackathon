import { Routes, Route } from "react-router-dom";
import TaskScreenPage from "@/features/task/TaskScreenPage";
import WorkstreamGraphPage from "@/features/workstream-graph/WorkstreamGraphPage";
import { ReviewLinkagesPage } from "@/features/review-linkages/ReviewLinkagesPage";
import { DraftingWorkspacePage } from "@/features/drafting-workspace/DraftingWorkspacePage";
import { NewWorkstreamPage } from "@/features/new-workstream/NewWorkstreamPage";
import { HomePage } from "@/features/home/HomePage";
import { InstitutionMapPage } from "@/features/institution-map/InstitutionMapPage";
import { CrossIntelligencePage } from "@/features/cross-intelligence/CrossIntelligencePage";
import { CompareWorkstreamsPage } from "@/features/cross-intelligence/CompareWorkstreamsPage";
import { ReviewQueuePage } from "@/features/review-queue/ReviewQueuePage";
import { AppShell } from "@/components/AppShell";

function App() {
  return (
    <Routes>
      {/* The sidebar frame wraps every screen; pages render into its outlet. */}
      <Route element={<AppShell />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/workstreams/new" element={<NewWorkstreamPage />} />
        <Route path="/intelligence" element={<CrossIntelligencePage />} />
        <Route path="/intelligence/compare" element={<CompareWorkstreamsPage />} />
        <Route path="/review-queue" element={<ReviewQueuePage />} />
        <Route path="/institution-map" element={<InstitutionMapPage />} />
        <Route
          path="/workstreams/:workstreamId"
          element={<WorkstreamGraphPage />}
        />
        <Route
          path="/workstreams/:workstreamId/tasks/:nodeId"
          element={<TaskScreenPage />}
        />
        <Route
          path="/workstreams/:workstreamId/tasks/:nodeId/draft"
          element={<DraftingWorkspacePage />}
        />
        <Route
          path="/workstreams/:workstreamId/edges/:edgeId/review"
          element={<ReviewLinkagesPage />}
        />
      </Route>
    </Routes>
  );
}

export default App;
