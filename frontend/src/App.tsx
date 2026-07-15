import { Routes, Route } from "react-router-dom";
import TaskScreenPage from "@/features/task/TaskScreenPage";
import {
  HomePage,
  WorkstreamGraphPage,
  DraftingWorkspacePage,
  ReviewLinkagesPage,
} from "@/pages/placeholders";

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
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
