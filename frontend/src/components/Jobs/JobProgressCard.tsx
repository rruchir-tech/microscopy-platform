import { Link } from "react-router-dom";
import type { Job } from "@/types";

const STATUS_STYLES: Record<string, string> = {
  queued: "bg-amber-100 text-amber-700",
  processing: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
  cancelled: "bg-slate-200 text-slate-600",
};

export function JobProgressCard({ job }: { job: Job }) {
  return (
    <Link
      to={`/jobs/${job.id}`}
      className="block rounded-lg border border-slate-200 bg-white p-4 transition hover:border-brand-300"
    >
      <div className="flex items-center justify-between">
        <span className="font-mono text-xs text-slate-400">
          {job.id.slice(0, 8)}
        </span>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${
            STATUS_STYLES[job.status] ?? "bg-slate-100"
          }`}
        >
          {job.status}
        </span>
      </div>
      <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-brand-600 transition-all"
          style={{ width: `${job.progress_percent}%` }}
        />
      </div>
      <p className="mt-2 text-xs text-slate-500">
        {job.num_processed}/{job.num_images} images · {job.progress_percent}%
        {job.num_failed > 0 && ` · ${job.num_failed} failed`}
      </p>
    </Link>
  );
}
