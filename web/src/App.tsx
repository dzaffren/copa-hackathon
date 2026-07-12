import { BrowserRouter, Route, Routes } from "react-router-dom";

import WorkspacePage from "./pages/WorkspacePage";

/** Placeholder destination for the "Switch to supervisor view" hand-off (#10). */
function SupervisorPage() {
  return (
    <main className="p-8">
      <h1 className="text-2xl font-semibold">
        Supervisor view — coming in #10
      </h1>
    </main>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<WorkspacePage />} />
        <Route path="/supervisor" element={<SupervisorPage />} />
      </Routes>
    </BrowserRouter>
  );
}
