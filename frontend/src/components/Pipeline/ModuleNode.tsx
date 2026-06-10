import { Handle, Position, type NodeProps } from "reactflow";

const CATEGORY_COLORS: Record<string, string> = {
  input: "border-emerald-400",
  transform: "border-sky-400",
  analysis: "border-violet-400",
  output: "border-amber-400",
};

export interface ModuleNodeData {
  label: string;
  category: string;
  type: string;
  params: Record<string, unknown>;
}

export function ModuleNode({ data, selected }: NodeProps<ModuleNodeData>) {
  const border = CATEGORY_COLORS[data.category] ?? "border-slate-300";
  return (
    <div
      className={`min-w-[150px] rounded-lg border-2 bg-white px-3 py-2 shadow-sm ${border} ${
        selected ? "ring-2 ring-brand-400" : ""
      }`}
    >
      {data.category !== "input" && (
        <Handle type="target" position={Position.Left} className="!bg-slate-400" />
      )}
      <p className="text-sm font-semibold">{data.label}</p>
      <p className="text-[10px] uppercase tracking-wide text-slate-400">
        {data.category}
      </p>
      {data.category !== "output" && (
        <Handle
          type="source"
          position={Position.Right}
          className="!bg-slate-400"
        />
      )}
    </div>
  );
}
