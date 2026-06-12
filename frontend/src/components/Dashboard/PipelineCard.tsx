import { Link } from "react-router-dom";
import { useClonePipeline, useDeletePipeline } from "@/hooks/usePipelines";
import type { Pipeline } from "@/types";

export function PipelineCard({ pipeline }: { pipeline: Pipeline }) {
  const del = useDeletePipeline();
  const clone = useClonePipeline();
  const nodeCount = pipeline.config?.nodes?.length ?? 0;

  return (
    <div className="card flex flex-col justify-between">
      <div>
        <div className="flex items-start justify-between">
          <h3 className="font-semibold">{pipeline.name}</h3>
          <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
            v{pipeline.version}
          </span>
        </div>
        <p className="mt-1 line-clamp-2 text-sm text-slate-500">
          {pipeline.description || "No description"}
        </p>
        <p className="mt-2 text-xs text-slate-400">
          {nodeCount} module{nodeCount === 1 ? "" : "s"} · updated{" "}
          {new Date(pipeline.updated_at).toLocaleDateString()}
        </p>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <Link to={`/pipelines/${pipeline.id}`} className="btn-primary">
          Open
        </Link>
        <button
          className="btn-secondary"
          onClick={() => clone.mutate(pipeline.id)}
          disabled={clone.isPending}
        >
          Clone
        </button>
        <button
          className="btn-danger"
          onClick={() => {
            if (confirm(`Delete pipeline "${pipeline.name}"?`))
              del.mutate(pipeline.id);
          }}
          disabled={del.isPending}
        >
          Delete
        </button>
      </div>
    </div>
  );
}
