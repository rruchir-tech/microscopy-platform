import type { ModuleSpec } from "@/types";

export function ModuleLibrary({
  modules,
  onAdd,
}: {
  modules: ModuleSpec[];
  onAdd: (spec: ModuleSpec) => void;
}) {
  return (
    <aside className="w-56 shrink-0 space-y-2 overflow-y-auto border-r border-slate-200 bg-white p-3">
      <h3 className="px-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
        Module Library
      </h3>
      {modules.map((spec) => (
        <button
          key={spec.type}
          onClick={() => onAdd(spec)}
          draggable
          onDragStart={(e) =>
            e.dataTransfer.setData("application/module-type", spec.type)
          }
          className="flex w-full items-center justify-between rounded-md border border-slate-200 px-3 py-2 text-left text-sm transition hover:border-brand-300 hover:bg-brand-50"
        >
          <span>{spec.label}</span>
          <span className="text-xs text-slate-400">+</span>
        </button>
      ))}
      <p className="px-1 pt-2 text-[11px] text-slate-400">
        Click or drag a module onto the canvas, then connect the nodes.
      </p>
    </aside>
  );
}
