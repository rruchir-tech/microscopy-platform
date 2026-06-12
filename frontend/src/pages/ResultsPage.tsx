import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AuthImage } from "@/components/Shared/AuthImage";
import { LoadingSpinner } from "@/components/Shared/LoadingSpinner";
import { useJobResults } from "@/hooks/useJobs";
import { api } from "@/services/api";

interface Row {
  image_name: string;
  cell_id?: number;
  area?: number;
  mean_intensity?: number;
  [key: string]: unknown;
}

export function ResultsPage() {
  const { id } = useParams();
  const { data: results, isLoading } = useJobResults(id);
  const [sortKey, setSortKey] = useState<string>("image_name");
  const [asc, setAsc] = useState(true);

  const rows = useMemo<Row[]>(() => {
    const out: Row[] = [];
    for (const r of results ?? []) {
      const cells = r.metrics?.cells ?? [];
      if (cells.length === 0) {
        out.push({ image_name: r.image_filename, ...(r.metrics?.aggregate ?? {}) });
      } else {
        for (const c of cells) {
          out.push({ image_name: r.image_filename, ...c });
        }
      }
    }
    return out;
  }, [results]);

  const columns = useMemo(() => {
    const cols = new Set<string>();
    rows.forEach((r) => Object.keys(r).forEach((k) => cols.add(k)));
    return Array.from(cols);
  }, [rows]);

  const sorted = useMemo(() => {
    const copy = [...rows];
    copy.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (typeof av === "number" && typeof bv === "number")
        return asc ? av - bv : bv - av;
      return asc
        ? String(av).localeCompare(String(bv))
        : String(bv).localeCompare(String(av));
    });
    return copy.slice(0, 100);
  }, [rows, sortKey, asc]);

  const histogram = useMemo(() => {
    const values = rows
      .map((r) => Number(r.mean_intensity))
      .filter((v) => !isNaN(v));
    if (values.length === 0) return [];
    const min = Math.min(...values);
    const max = Math.max(...values);
    const bins = 10;
    const width = (max - min) / bins || 1;
    const counts = Array.from({ length: bins }, (_, i) => ({
      bin: (min + i * width).toFixed(0),
      count: 0,
    }));
    values.forEach((v) => {
      const idx = Math.min(bins - 1, Math.floor((v - min) / width));
      counts[idx].count += 1;
    });
    return counts;
  }, [rows]);

  const scatter = useMemo(
    () =>
      rows
        .filter((r) => r.area != null && r.mean_intensity != null)
        .slice(0, 500)
        .map((r) => ({ area: r.area, intensity: r.mean_intensity })),
    [rows],
  );

  const gallery = useMemo(
    () => (results ?? []).filter((r) => r.has_image),
    [results],
  );

  // The download endpoint is JWT-protected, so a plain <a href> would 401.
  // Fetch the ZIP with the auth header and save the blob instead.
  const downloadZip = async () => {
    const res = await api.get(`/api/jobs/${id}/download`, {
      responseType: "blob",
    });
    const url = URL.createObjectURL(res.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = `job-${id}-results.zip`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (isLoading) return <LoadingSpinner label="Loading results…" />;

  return (
    <div className="space-y-6">
      <div className="overflow-hidden rounded-xl bg-gradient-to-r from-brand-700 to-brand-500 px-6 py-7 text-white shadow-card">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="font-heading text-2xl font-bold tracking-tight text-white">
              Analysis results
            </h1>
            <p className="mt-1 text-sm text-brand-100">
              Annotated images, distributions, and per-cell measurements for this job.
            </p>
          </div>
          <div className="flex gap-3">
            <button
              className="btn bg-white/15 text-white ring-1 ring-inset ring-white/30 backdrop-blur hover:bg-white/25"
              onClick={downloadZip}
            >
              Download ZIP
            </button>
            <Link
              to={`/jobs/${id}`}
              className="btn bg-white text-brand-700 shadow-sm hover:bg-brand-50"
            >
              Back to job
            </Link>
          </div>
        </div>
      </div>

      {gallery.length > 0 && (
        <div className="card">
          <h3 className="font-heading text-lg font-semibold text-slate-900">
            Annotated images
          </h3>
          <p className="mb-4 text-sm text-slate-500">
            Yellow outlines = detected cells, red dots = centroids.
          </p>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {gallery.map((r) => (
              <figure
                key={r.id}
                className="group overflow-hidden rounded-xl border border-slate-200 bg-slate-50 shadow-card transition-shadow hover:shadow-card-hover"
              >
                <AuthImage
                  path={`/api/jobs/${id}/results/${r.id}/image`}
                  alt={`Annotated ${r.image_filename}`}
                  className="aspect-square w-full bg-white object-cover"
                />
                <figcaption className="space-y-0.5 border-t border-slate-200 px-3 py-2">
                  <span className="block truncate text-xs font-medium text-slate-700">
                    {r.image_filename}
                  </span>
                  {typeof r.metrics?.aggregate?.cell_count === "number" && (
                    <span className="badge bg-brand-50 text-brand-700">
                      {r.metrics.aggregate.cell_count} cells
                    </span>
                  )}
                </figcaption>
              </figure>
            ))}
          </div>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card">
          <h3 className="mb-4 font-heading text-lg font-semibold text-slate-900">
            Mean intensity distribution
          </h3>
          {histogram.length ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={histogram}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="bin" fontSize={11} stroke="#94a3b8" />
                <YAxis fontSize={11} stroke="#94a3b8" />
                <Tooltip />
                <Bar dataKey="count" fill="#2563eb" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-slate-400">No numeric metrics to chart.</p>
          )}
        </div>
        <div className="card">
          <h3 className="mb-4 font-heading text-lg font-semibold text-slate-900">
            Area vs intensity
          </h3>
          {scatter.length ? (
            <ResponsiveContainer width="100%" height={220}>
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="area" name="area" fontSize={11} stroke="#94a3b8" />
                <YAxis
                  dataKey="intensity"
                  name="intensity"
                  fontSize={11}
                  stroke="#94a3b8"
                />
                <Tooltip cursor={{ strokeDasharray: "3 3" }} />
                <Scatter data={scatter} fill="#1d4ed8" />
              </ScatterChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-slate-400">No per-cell data.</p>
          )}
        </div>
      </div>

      <div className="card p-0">
        <div className="flex flex-wrap items-center justify-between gap-2 px-5 py-4">
          <h3 className="font-heading text-lg font-semibold text-slate-900">
            Result rows
          </h3>
          <span className="badge bg-slate-100 text-slate-600">
            showing {sorted.length} of {rows.length}
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-y border-slate-200 bg-slate-50">
                {columns.map((c) => {
                  const active = sortKey === c;
                  return (
                    <th
                      key={c}
                      className="sticky top-0 cursor-pointer select-none whitespace-nowrap bg-slate-50 px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-slate-500 transition-colors hover:text-brand-700"
                      onClick={() => {
                        if (sortKey === c) setAsc(!asc);
                        else {
                          setSortKey(c);
                          setAsc(true);
                        }
                      }}
                    >
                      <span className="inline-flex items-center gap-1">
                        {c}
                        <span
                          className={
                            active ? "text-brand-600" : "text-slate-300"
                          }
                        >
                          {active ? (asc ? "▲" : "▼") : "↕"}
                        </span>
                      </span>
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {sorted.map((r, i) => (
                <tr
                  key={i}
                  className="border-b border-slate-100 odd:bg-white even:bg-slate-50/50 transition-colors hover:bg-brand-50/60"
                >
                  {columns.map((c) => {
                    const active = sortKey === c;
                    const isNum = typeof r[c] === "number";
                    return (
                      <td
                        key={c}
                        className={`whitespace-nowrap px-4 py-2 ${
                          isNum
                            ? "text-right font-mono tabular-nums text-slate-700"
                            : "text-slate-600"
                        } ${active ? "font-medium text-slate-900" : ""}`}
                      >
                        {isNum
                          ? (r[c] as number).toLocaleString(undefined, {
                              maximumFractionDigits: 2,
                            })
                          : String(r[c] ?? "")}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
