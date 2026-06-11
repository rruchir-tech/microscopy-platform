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

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">
            Welcome back{user ? `, ${user.username}` : ""} 👋
          </h1>
          <p className="text-slate-500">
            Build pipelines, run batch jobs, export results.
          </p>
        </div>
        <div className="flex gap-3">
          <Link to="/pipelines/new" className="btn-secondary">
            Advanced builder
          </Link>
          <Link to="/analyze" className="btn-primary">
            + New Analysis
          </Link>
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
