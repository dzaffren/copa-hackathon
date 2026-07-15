import { Routes, Route } from "react-router-dom";
import TaskScreenPage from "@/features/task/TaskScreenPage";
import WorkstreamGraphPage from "@/features/workstream-graph/WorkstreamGraphPage";
import {
  HomePage,
  DraftingWorkspacePage,
  ReviewLinkagesPage,
  NewWorkstreamPage,
  InstitutionMapPage,
} from "@/pages/placeholders";

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/workstreams/new" element={<NewWorkstreamPage />} />
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
    </Routes>
  );
}

export default App;
