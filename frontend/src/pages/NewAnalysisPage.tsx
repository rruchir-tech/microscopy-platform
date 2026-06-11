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
];

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
      const job = await demo.mutateAsync(feats);
      navigate(`/jobs/${job.id}`);
    } catch (err) {
      handleError(err, "Could not start demo analysis");
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">New analysis</h1>
        <p className="text-slate-500">
          Upload microscopy images, choose what to measure, and we'll batch
          process them.
        </p>
      </div>

      <input
        className="input max-w-sm"
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Analysis name"
      />

      {/* Step 1: upload */}
      <div
        className={`card border-2 border-dashed text-center transition ${
          dragOver ? "border-brand-500 bg-brand-50" : "border-slate-300"
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
        <p className="font-medium">Drag &amp; drop your images here</p>
        <p className="mb-3 text-sm text-slate-400">PNG, JPG, TIFF, or BMP</p>
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
          <div className="mt-4 text-left text-sm">
            <div className="flex items-center justify-between">
              <span className="font-medium">{files.length} images ready</span>
              <button
                className="text-xs text-slate-400 hover:text-red-600"
                onClick={() => setFiles([])}
              >
                clear
              </button>
            </div>
            <div className="mt-1 text-xs text-slate-500">
              Auto-organized by date:{" "}
              {byDate.map(([d, n]) => `${d} (${n})`).join(" · ")}
            </div>
          </div>
        )}
      </div>

      {/* Step 2: features */}
      <div className="card">
        <h3 className="mb-3 font-semibold">What should we measure?</h3>
        <div className="space-y-2">
          {FEATURES.map((f) => (
            <label
              key={f.key}
              className="flex cursor-pointer items-start gap-3 rounded-md p-2 hover:bg-slate-50"
            >
              <input
                type="checkbox"
                className="mt-1 h-4 w-4"
                checked={selected.has(f.key)}
                onChange={() => toggle(f.key)}
              />
              <span>
                <span className="font-medium">{f.label}</span>
                <span className="block text-xs text-slate-500">{f.hint}</span>
              </span>
            </label>
          ))}
        </div>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="flex items-center gap-3">
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
