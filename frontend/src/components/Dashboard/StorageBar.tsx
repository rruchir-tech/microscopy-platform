import { useStorage } from "@/hooks/useJobs";

export function StorageBar() {
  const { data } = useStorage();
  if (!data) return null;
  const pct = Math.min(
    100,
    Math.round((data.storage_used_gb / data.storage_limit_gb) * 100),
  );
  return (
    <div className="card">
      <div className="mb-2 flex items-center justify-between text-sm">
        <span className="font-medium">Storage</span>
        <span className="text-slate-500">
          {data.storage_used_gb.toFixed(2)} / {data.storage_limit_gb} GB
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className={`h-full rounded-full ${pct > 90 ? "bg-red-500" : "bg-brand-600"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="mt-2 text-xs capitalize text-slate-500">{data.tier} tier</p>
    </div>
  );
}
