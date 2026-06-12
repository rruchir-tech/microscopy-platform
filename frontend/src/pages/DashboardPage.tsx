import { Link } from "react-router-dom";
import { JobProgressCard } from "@/components/Jobs/JobProgressCard";
import { PipelineCard } from "@/components/Dashboard/PipelineCard";
import { StorageBar } from "@/components/Dashboard/StorageBar";
import { LoadingSpinner } from "@/components/Shared/LoadingSpinner";
import { useCurrentUser } from "@/hooks/useAuth";
import { useJobs } from "@/hooks/useJobs";
import {
  useInstantiateTemplate,
  usePipelines,
  useTemplates,
} from "@/hooks/usePipelines";

export function DashboardPage() {
  const { data: user } = useCurrentUser();
  const pipelines = usePipelines();
  const jobs = useJobs();
  const templates = useTemplates();
  const instantiate = useInstantiateTemplate();

  const jobList = jobs.data ?? [];
  const completed = jobList.filter((j) => j.status === "completed").length;
  const running = jobList.filter(
    (j) => j.status === "queued" || j.status === "processing",
  ).length;

  return (
    <div className="space-y-8">
      <div className="overflow-hidden rounded-2xl bg-gradient-to-br from-brand-700 to-brand-500 p-6 text-white shadow-lg shadow-brand-600/20 sm:p-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="font-heading text-2xl font-semibold tracking-tight sm:text-3xl">
              Welcome back{user ? `, ${user.username}` : ""}
            </h1>
            <p className="mt-1 max-w-md text-sm text-brand-50/90">
              Upload microscopy images, pick what to measure, and export
              publication-ready results — no code.
            </p>
          </div>
          <div className="flex gap-3">
            <Link
              to="/pipelines/new"
              className="btn border border-white/30 bg-white/10 text-white hover:bg-white/20"
            >
              Advanced builder
            </Link>
            <Link
              to="/analyze"
              className="btn bg-white font-semibold text-brand-700 shadow-sm hover:bg-brand-50"
            >
              + New analysis
            </Link>
          </div>
        </div>
        <div className="mt-6 grid grid-cols-3 gap-3">
          {[
            { label: "Pipelines", value: pipelines.data?.length ?? 0 },
            { label: "Completed", value: completed },
            { label: "Running", value: running },
          ].map((s) => (
            <div
              key={s.label}
              className="rounded-xl bg-white/10 px-4 py-3 backdrop-blur-sm"
            >
              <div className="font-heading text-2xl font-semibold">
                {s.value}
              </div>
              <div className="text-xs text-brand-50/80">{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <h2 className="mb-3 text-lg font-semibold">Your Pipelines</h2>
          {pipelines.isLoading ? (
            <LoadingSpinner />
          ) : pipelines.data && pipelines.data.length > 0 ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {pipelines.data.map((p) => (
                <PipelineCard key={p.id} pipeline={p} />
              ))}
            </div>
          ) : (
            <EmptyPipelines
              onUseTemplate={(id) => instantiate.mutate(id)}
              templates={templates.data ?? []}
            />
          )}
        </div>

        <div className="space-y-6">
          <StorageBar />
          <div>
            <h2 className="mb-3 text-lg font-semibold">Recent Jobs</h2>
            {jobs.isLoading ? (
              <LoadingSpinner />
            ) : jobs.data && jobs.data.length > 0 ? (
              <div className="space-y-3">
                {jobs.data.slice(0, 6).map((j) => (
                  <JobProgressCard key={j.id} job={j} />
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-500">No jobs yet.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function EmptyPipelines({
  templates,
  onUseTemplate,
}: {
  templates: { id: string; name: string; description: string }[];
  onUseTemplate: (id: string) => void;
}) {
  return (
    <div className="card text-center">
      <div className="text-4xl">🧫</div>
      <h3 className="mt-2 font-semibold">No pipelines yet</h3>
      <p className="mt-1 text-sm text-slate-500">
        Start from a template or build one from scratch.
      </p>
      <div className="mt-4 grid gap-3 text-left sm:grid-cols-2">
        {templates.map((t) => (
          <button
            key={t.id}
            onClick={() => onUseTemplate(t.id)}
            className="rounded-lg border border-slate-200 p-3 text-left transition hover:border-brand-300"
          >
            <p className="font-medium">{t.name}</p>
            <p className="text-xs text-slate-500">{t.description}</p>
          </button>
        ))}
      </div>
    </div>
  );
}
