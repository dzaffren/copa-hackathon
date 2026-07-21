import { Outlet, useParams } from "react-router-dom";
import { Sidebar } from "@/features/workstream-graph/Sidebar";
import { DemoController } from "@/components/DemoController";

/**
 * The persistent frame every screen renders inside: the collapsible workstream
 * sidebar on the left, the routed page on the right. A layout route in App.tsx
 * mounts this once, so the sidebar survives navigation instead of remounting per
 * page.
 *
 * The content column is a flex column with `min-h-0` (not `overflow-*`): pages
 * own their own scrolling — the graph and drafting screens fill the height and
 * scroll internal panels; the task, home and form screens scroll their body via
 * `h-full overflow-y-auto`.
 */
export function AppShell() {
  const { workstreamId } = useParams();
  return (
    <div className="flex h-screen w-full overflow-hidden bg-background text-foreground">
      <Sidebar activeWorkstreamId={workstreamId} />
      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <Outlet />
      </div>
      <DemoController />
    </div>
  );
}

export default AppShell;
