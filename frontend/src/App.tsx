import { Outlet, Route, Routes } from "react-router-dom";
import { Navbar } from "@/components/Shared/Navbar";
import { AuthGuard } from "@/components/Shared/AuthGuard";
import { DashboardPage } from "@/pages/DashboardPage";
import { JobDetailPage } from "@/pages/JobDetailPage";
import { LoginPage } from "@/pages/LoginPage";
import { PipelineBuilderPage } from "@/pages/PipelineBuilderPage";
import { ResultsPage } from "@/pages/ResultsPage";

function AppLayout() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto max-w-6xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<AuthGuard />}>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="/pipelines/new" element={<PipelineBuilderPage />} />
          <Route path="/pipelines/:id" element={<PipelineBuilderPage />} />
          <Route path="/jobs/:id" element={<JobDetailPage />} />
          <Route path="/jobs/:id/results" element={<ResultsPage />} />
        </Route>
      </Route>
    </Routes>
  );
}
