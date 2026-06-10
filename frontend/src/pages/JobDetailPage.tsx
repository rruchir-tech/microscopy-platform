import { Link, useParams } from "react-router-dom";
import { LoadingSpinner } from "@/components/Shared/LoadingSpinner";
import { useCancelJob, useJob } from "@/hooks/useJobs";
import { api } from "@/services/api";

export function JobDetailPage() {
  const { id } = useParams();
  const { data: job, isLoading } = useJob(id);
  const cancel = useCancelJob();

  if (isLoading || !job) return <LoadingSpinner label="Loading job…" />;

  const active = job.status === "queued" || job.status === "processing";
  const downloadUrl = `${api.defaults.baseURL}/api/jobs/${job.id}/download`;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Batch Job</h1>
          <p className="font-mono text-sm text-slate-400">{job.id}</p>
        </div>
        <span
          className={`rounded-full px-3 py-1 text-sm font-medium ${
            job.status === "completed"
              ? "bg-green-100 text-green-700"
              : job.status === "failed"
                ? "bg-red-100 text-red-700"
                : "bg-blue-100 text-blue-700"
          }`}
        >
          {job.status}
        </span>
      </div>

      <div className="card">
        <div className="mb-2 flex justify-between text-sm">
          <span>Progress</span>
          <span>
            {job.num_processed}/{job.num_images} images · {job.progress_percent}%
          </span>
        </div>
        <div className="h-3 w-full overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-brand-600 transition-all"
            style={{ width: `${job.progress_percent}%` }}
          />
        </div>
        {job.num_failed > 0 && (
          <p className="mt-2 text-sm text-amber-600">
            {job.num_failed} image(s) failed to process.
          </p>
        )}
        {job.error_message && (
          <p className="mt-2 rounded bg-red-50 px-3 py-2 text-sm text-red-700">
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
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-sm text-slate-500">{label}</p>
    </div>
  );
}
