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

  if (isLoading) return <LoadingSpinner label="Loading results…" />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Results</h1>
        <div className="flex gap-3">
          <a
            className="btn-secondary"
            href={`${api.defaults.baseURL}/api/jobs/${id}/download`}
          >
            Download ZIP
          </a>
          <Link to={`/jobs/${id}`} className="btn-secondary">
            Back to job
          </Link>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card">
          <h3 className="mb-3 font-semibold">Mean intensity distribution</h3>
          {histogram.length ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={histogram}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="bin" fontSize={11} />
                <YAxis fontSize={11} />
                <Tooltip />
                <Bar dataKey="count" fill="#6366f1" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-slate-400">No numeric metrics to chart.</p>
          )}
        </div>
        <div className="card">
          <h3 className="mb-3 font-semibold">Area vs intensity</h3>
          {scatter.length ? (
            <ResponsiveContainer width="100%" height={220}>
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="area" name="area" fontSize={11} />
                <YAxis dataKey="intensity" name="intensity" fontSize={11} />
                <Tooltip cursor={{ strokeDasharray: "3 3" }} />
                <Scatter data={scatter} fill="#4f46e5" />
              </ScatterChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-slate-400">No per-cell data.</p>
          )}
        </div>
      </div>

      <div className="card overflow-x-auto">
        <h3 className="mb-3 font-semibold">
          Result rows{" "}
          <span className="text-sm font-normal text-slate-400">
            (showing {sorted.length} of {rows.length})
          </span>
        </h3>
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-slate-500">
              {columns.map((c) => (
                <th
                  key={c}
                  className="cursor-pointer px-2 py-2 hover:text-slate-900"
                  onClick={() => {
                    if (sortKey === c) setAsc(!asc);
                    else {
                      setSortKey(c);
                      setAsc(true);
                    }
                  }}
                >
                  {c} {sortKey === c ? (asc ? "▲" : "▼") : ""}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((r, i) => (
              <tr key={i} className="border-b border-slate-100">
                {columns.map((c) => (
                  <td key={c} className="px-2 py-1.5">
                    {typeof r[c] === "number"
                      ? (r[c] as number).toLocaleString(undefined, {
                          maximumFractionDigits: 2,
                        })
                      : String(r[c] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
