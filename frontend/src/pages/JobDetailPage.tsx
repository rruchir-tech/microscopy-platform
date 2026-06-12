import { Link, useParams } from "react-router-dom";
import { LoadingSpinner } from "@/components/Shared/LoadingSpinner";
import { useCancelJob, useJob } from "@/hooks/useJobs";
import { api } from "@/services/api";

const STATUS_STYLES: Record<string, string> = {
  queued: "bg-slate-100 text-slate-600",
  processing: "bg-brand-100 text-brand-700",
  completed: "bg-emerald-100 text-emerald-700",
  failed: "bg-red-100 text-red-700",
  cancelled: "bg-slate-200 text-slate-600",
};

export function JobDetailPage() {
  const { id } = useParams();
  const { data: job, isLoading } = useJob(id);
  const cancel = useCancelJob();

  if (isLoading || !job) return <LoadingSpinner label="Loading job…" />;

  const active = job.status === "queued" || job.status === "processing";
  const downloadUrl = `${api.defaults.baseURL}/api/jobs/${job.id}/download`;

  return (
    <div className="space-y-6">
      <div className="overflow-hidden rounded-xl bg-gradient-to-r from-brand-700 to-brand-500 p-6 text-white shadow-card">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">Batch Job</h1>
            <p className="mt-1 font-mono text-sm text-brand-100">{job.id}</p>
          </div>
          <span
            className={`badge capitalize ${
              STATUS_STYLES[job.status] ?? "bg-slate-100 text-slate-600"
            }`}
          >
            {active && (
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current" />
            )}
            {job.status}
          </span>
        </div>
      </div>

      <div className="card space-y-4">
        <div className="flex items-end justify-between">
          <div>
            <p className="label mb-0">Progress</p>
            <p className="font-heading text-3xl font-bold tabular-nums text-slate-900">
              {job.progress_percent}%
            </p>
          </div>
          <p className="text-sm tabular-nums text-slate-500">
            {job.num_processed}
            <span className="text-slate-400"> / {job.num_images}</span> images
          </p>
        </div>
        <div className="h-3 w-full overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-brand-600 transition-all duration-500 ease-out"
            style={{ width: `${job.progress_percent}%` }}
          />
        </div>
        {job.num_failed > 0 && (
          <p className="text-sm font-medium text-accent-600">
            {job.num_failed} image(s) failed to process.
          </p>
        )}
        {job.error_message && (
          <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {job.error_message}
          </p>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Stat label="Images" value={job.num_images} />
        <Stat label="Processed" value={job.num_processed} />
        <Stat label="Failed" value={job.num_failed} />
      </div>

      <div className="flex flex-wrap gap-3">
        {job.status === "completed" && (
          <>
            <a className="btn-primary" href={downloadUrl}>
              Download ZIP
            </a>
            <Link to={`/jobs/${job.id}/results`} className="btn-secondary">
              View results
            </Link>
          </>
        )}
        {active && (
          <button
            className="btn-danger"
            onClick={() => cancel.mutate(job.id)}
            disabled={cancel.isPending}
          >
            Cancel job
          </button>
        )}
        <Link to="/" className="btn-secondary">
          Back to dashboard
        </Link>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="card text-center">
      <p className="font-heading text-3xl font-bold tabular-nums text-slate-900">
        {value}
      </p>
      <p className="mt-1 text-sm text-slate-500">{label}</p>
    </div>
  );
}
