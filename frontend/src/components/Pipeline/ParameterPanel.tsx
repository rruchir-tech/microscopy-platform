import type { Node } from "reactflow";
import type { ModuleNodeData } from "./ModuleNode";
import type { ModuleSpec } from "@/types";

export function ParameterPanel({
  node,
  spec,
  onChange,
  onDelete,
}: {
  node: Node<ModuleNodeData> | null;
  spec: ModuleSpec | undefined;
  onChange: (params: Record<string, unknown>) => void;
  onDelete: () => void;
}) {
  if (!node) {
    return (
      <aside className="w-64 shrink-0 border-l border-slate-200 bg-white p-4 text-sm text-slate-400">
        Select a module to edit its parameters.
      </aside>
    );
  }

  const params = node.data.params ?? {};

  const update = (name: string, value: unknown) =>
    onChange({ ...params, [name]: value });

  return (
    <aside className="w-64 shrink-0 space-y-4 overflow-y-auto border-l border-slate-200 bg-white p-4">
      <div>
        <h3 className="font-semibold">{node.data.label}</h3>
        <p className="text-xs text-slate-400">{node.data.type}</p>
      </div>

      {spec?.params.map((p) => (
        <div key={p.name}>
          <label className="label capitalize">{p.name.replace(/_/g, " ")}</label>
          {p.type === "boolean" ? (
            <input
              type="checkbox"
              checked={Boolean(params[p.name] ?? p.default)}
              onChange={(e) => update(p.name, e.target.checked)}
              className="h-4 w-4"
            />
          ) : p.type === "select" ? (
            <select
              className="input"
              value={String(params[p.name] ?? p.default ?? "")}
              onChange={(e) => {
                const raw = e.target.value;
                const num = Number(raw);
                update(p.name, !isNaN(num) && raw !== "" ? num : raw);
              }}
            >
              {p.options?.map((o) => (
                <option key={String(o)} value={String(o)}>
                  {String(o)}
                </option>
              ))}
            </select>
          ) : p.type === "slider" ? (
            <div>
              <input
                type="range"
                min={p.min}
                max={p.max}
                step={p.step}
                value={Number(params[p.name] ?? p.default ?? 0)}
                onChange={(e) => update(p.name, Number(e.target.value))}
                className="w-full"
              />
              <span className="text-xs text-slate-500">
                {String(params[p.name] ?? p.default)}
              </span>
            </div>
          ) : (
            <input
              type="number"
              className="input"
              value={Number(params[p.name] ?? p.default ?? 0)}
              min={p.min}
              max={p.max}
              onChange={(e) => update(p.name, Number(e.target.value))}
            />
          )}
        </div>
      ))}

      <button className="btn-danger w-full" onClick={onDelete}>
        Remove module
      </button>
    </aside>
  );
}
