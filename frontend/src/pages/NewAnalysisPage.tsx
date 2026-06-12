import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAnalyze, useAnalyzeDemo } from "@/hooks/useJobs";

const FEATURES = [
  {
    key: "cell_count",
    label: "Cell count",
    hint: "Detect and count cells in each image",
  },
  {
    key: "intensity",
    label: "Fluorescence intensity",
    hint: "Per-cell mean / max / sum intensity",
  },
  {
    key: "foci",
    label: "Foci / puncta count",
    hint: "Count bright spots (Find Maxima), incl. foci per cell",
  },
];

const THRESHOLD_METHODS = ["otsu", "isodata", "triangle", "mean"];

const IMAGE_EXT = /\.(png|jpe?g|tiff?|bmp)$/i;

export function NewAnalysisPage() {
  const navigate = useNavigate();
  const analyze = useAnalyze();
  const demo = useAnalyzeDemo();

  const [files, setFiles] = useState<File[]>([]);
  const [selected, setSelected] = useState<Set<string>>(
    new Set(["cell_count", "intensity"]),
  );
  const [name, setName] = useState("Untitled Analysis");
  const [thresholdMethod, setThresholdMethod] = useState("otsu");
  const [separateTouching, setSeparateTouching] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const busy = analyze.isPending || demo.isPending;

  // Group selected files by their last-modified date — a preview of the
  // server-side auto-organization.
  const byDate = useMemo(() => {
    const groups: Record<string, number> = {};
    for (const f of files) {
      const d = new Date(f.lastModified).toISOString().slice(0, 10);
      groups[d] = (groups[d] ?? 0) + 1;
    }
    return Object.entries(groups).sort();
  }, [files]);

  const addFiles = (list: FileList | null) => {
    if (!list) return;
    const imgs = Array.from(list).filter((f) => IMAGE_EXT.test(f.name));
    setFiles((prev) => [...prev, ...imgs]);
  };

  const toggle = (key: string) =>
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });

  const handleError = (err: unknown, fallback: string) =>
    setError(
      (err as { response?: { data?: { detail?: string } } })?.response?.data
        ?.detail ?? fallback,
    );

  const runUploaded = async () => {
    setError(null);
    if (files.length === 0) return setError("Add at least one image.");
    if (selected.size === 0) return setError("Pick at least one measurement.");
    try {
      const job = await analyze.mutateAsync({
        files,
        features: [...selected],
        name,
        thresholdMethod,
        separateTouching,
      });
      navigate(`/jobs/${job.id}`);
    } catch (err) {
      handleError(err, "Analysis failed to start");
    }
  };

  const runDemo = async () => {
    setError(null);
    const feats = selected.size > 0 ? [...selected] : ["cell_count"];
    try {
      const job = await demo.mutateAsync({
        features: feats,
        thresholdMethod,
        separateTouching,
      });
      navigate(`/jobs/${job.id}`);
    } catch (err) {
      handleError(err, "Could not start demo analysis");
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Hero header */}
      <div className="overflow-hidden rounded-2xl bg-gradient-to-br from-brand-700 to-brand-500 p-6 text-white shadow-lg shadow-brand-600/20 sm:p-8">
        <p className="text-xs font-medium uppercase tracking-wide text-brand-50/80">
          No-code workflow
        </p>
        <h1 className="mt-1 font-heading text-2xl font-semibold tracking-tight sm:text-3xl">
          New analysis
        </h1>
        <p className="mt-1 max-w-md text-sm text-brand-50/90">
          Upload microscopy images, choose what to measure, and we'll batch
          process them.
        </p>
      </div>

      {/* Analysis name */}
      <div className="card">
        <label className="label" htmlFor="analysis-name">
          Analysis name
        </label>
        <input
          id="analysis-name"
          className="input max-w-sm"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Analysis name"
        />
      </div>

      {/* Step 1: upload */}
      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <span className="badge bg-brand-100 text-brand-700">Step 1</span>
          <h2 className="text-lg font-semibold text-slate-900">Add images</h2>
        </div>
        <div
          className={`card flex flex-col items-center border-2 border-dashed text-center transition ${
            dragOver
              ? "border-brand-500 bg-brand-50 shadow-card-hover"
              : "border-slate-300 hover:border-slate-400"
          }`}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            addFiles(e.dataTransfer.files);
          }}
        >
          <div
            className={`flex h-12 w-12 items-center justify-center rounded-full text-2xl transition-colors ${
              dragOver ? "bg-brand-100 text-brand-700" : "bg-slate-100 text-slate-500"
            }`}
            aria-hidden
          >
            🔬
          </div>
          <p className="mt-3 font-medium text-slate-900">
            Drag &amp; drop your images here
          </p>
          <p className="mb-4 text-sm text-slate-400">PNG, JPG, TIFF, or BMP</p>
          <label className="btn-secondary cursor-pointer">
            Browse files
            <input
              type="file"
              multiple
              accept=".png,.jpg,.jpeg,.tif,.tiff,.bmp"
              className="hidden"
              onChange={(e) => addFiles(e.target.files)}
            />
          </label>

          {files.length > 0 && (
            <div className="mt-5 w-full rounded-lg border border-slate-200 bg-slate-50 p-3 text-left text-sm">
              <div className="flex items-center justify-between">
                <span className="badge bg-brand-100 text-brand-700">
                  {files.length} images ready
                </span>
                <button
                  className="text-xs font-medium text-slate-400 transition-colors hover:text-red-600"
                  onClick={() => setFiles([])}
                >
                  Clear all
                </button>
              </div>
              <div className="mt-3">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                  Auto-organized by date
                </p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {byDate.map(([d, n]) => (
                    <span
                      key={d}
                      className="badge border border-slate-200 bg-white text-slate-600"
                    >
                      {d}
                      <span className="text-slate-400">· {n}</span>
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Step 2: features */}
      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <span className="badge bg-brand-100 text-brand-700">Step 2</span>
          <h2 className="text-lg font-semibold text-slate-900">
            What should we measure?
          </h2>
        </div>
        <div className="card">
          <div className="space-y-2">
            {FEATURES.map((f) => {
              const isOn = selected.has(f.key);
              return (
                <label
                  key={f.key}
                  className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition ${
                    isOn
                      ? "border-brand-200 bg-brand-50"
                      : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50"
                  }`}
                >
                  <input
                    type="checkbox"
                    className="mt-0.5 h-4 w-4 accent-brand-600"
                    checked={isOn}
                    onChange={() => toggle(f.key)}
                  />
                  <span>
                    <span className="font-medium text-slate-900">{f.label}</span>
                    <span className="block text-xs text-slate-500">
                      {f.hint}
                    </span>
                  </span>
                </label>
              );
            })}
          </div>

          {/* Detection options */}
          <div className="mt-5 border-t border-slate-100 pt-5">
            <h3 className="mb-3 text-sm font-semibold text-slate-700">
              Detection options
            </h3>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="label">Threshold method</label>
                <select
                  className="input"
                  value={thresholdMethod}
                  onChange={(e) => setThresholdMethod(e.target.value)}
                >
                  {THRESHOLD_METHODS.map((m) => (
                    <option key={m} value={m}>
                      {m[0].toUpperCase() + m.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
              <label
                className={`flex cursor-pointer items-start gap-3 self-end rounded-lg border p-3 transition ${
                  separateTouching
                    ? "border-brand-200 bg-brand-50"
                    : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50"
                }`}
              >
                <input
                  type="checkbox"
                  className="mt-0.5 h-4 w-4 accent-brand-600"
                  checked={separateTouching}
                  onChange={(e) => setSeparateTouching(e.target.checked)}
                />
                <span>
                  <span className="font-medium text-slate-900">
                    Separate touching cells
                  </span>
                  <span className="block text-xs text-slate-500">
                    Watershed split for clustered cells
                  </span>
                </span>
              </label>
            </div>
          </div>
        </div>
      </section>

      {error && (
        <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm font-medium text-red-600">
          {error}
        </p>
      )}

      <div className="flex flex-col items-stretch gap-3 sm:flex-row sm:items-center">
        <button className="btn-primary" onClick={runUploaded} disabled={busy}>
          {analyze.isPending ? "Starting…" : "Process images"}
        </button>
        <button className="btn-secondary" onClick={runDemo} disabled={busy}>
          {demo.isPending ? "Generating…" : "Try with demo images"}
        </button>
      </div>
    </div>
  );
}
