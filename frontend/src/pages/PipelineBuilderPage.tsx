import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import ReactFlow, {
  addEdge,
  Background,
  Controls,
  MiniMap,
  type Connection,
  type Edge,
  type Node,
  useEdgesState,
  useNodesState,
} from "reactflow";
import "reactflow/dist/style.css";
import { ModuleLibrary } from "@/components/Pipeline/ModuleLibrary";
import { ModuleNode, type ModuleNodeData } from "@/components/Pipeline/ModuleNode";
import { ParameterPanel } from "@/components/Pipeline/ParameterPanel";
import { LoadingSpinner } from "@/components/Shared/LoadingSpinner";
import { useSubmitJob } from "@/hooks/useJobs";
import {
  useCreatePipeline,
  useModules,
  usePipeline,
  useUpdatePipeline,
} from "@/hooks/usePipelines";
import type { ModuleSpec, PipelineConfig } from "@/types";

const nodeTypes = { moduleNode: ModuleNode };
let idSeq = 1;
const nextId = () => `node-${Date.now()}-${idSeq++}`;

export function PipelineBuilderPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isNew = !id;

  const modulesQ = useModules();
  const pipelineQ = usePipeline(id);
  const createMut = useCreatePipeline();
  const updateMut = useUpdatePipeline(id ?? "");
  const submitJob = useSubmitJob();

  const [name, setName] = useState("Untitled Pipeline");
  const [nodes, setNodes, onNodesChange] = useNodesState<ModuleNodeData>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [savedId, setSavedId] = useState<string | undefined>(id);

  const specByType = useMemo(() => {
    const map = new Map<string, ModuleSpec>();
    modulesQ.data?.forEach((s) => map.set(s.type, s));
    return map;
  }, [modulesQ.data]);

  // Hydrate from an existing pipeline.
  useEffect(() => {
    if (!pipelineQ.data) return;
    setName(pipelineQ.data.name);
    const cfg = pipelineQ.data.config;
    setNodes(
      (cfg.nodes ?? []).map((n, i) => ({
        id: n.id,
        type: "moduleNode",
        position: n.position ?? { x: 80 + i * 60, y: 80 + i * 90 },
        data: {
          label: specByType.get(n.type)?.label ?? n.type,
          category: specByType.get(n.type)?.category ?? "analysis",
          type: n.type,
          params: n.params ?? {},
        },
      })),
    );
    setEdges(
      (cfg.edges ?? []).map((e) => ({
        id: `${e.source}-${e.target}`,
        source: e.source,
        target: e.target,
      })),
    );
  }, [pipelineQ.data, specByType, setNodes, setEdges]);

  const addModule = useCallback(
    (spec: ModuleSpec, pos?: { x: number; y: number }) => {
      const defaults: Record<string, unknown> = {};
      spec.params.forEach((p) => (defaults[p.name] = p.default));
      const node: Node<ModuleNodeData> = {
        id: nextId(),
        type: "moduleNode",
        position: pos ?? { x: 120 + Math.random() * 200, y: 80 + Math.random() * 200 },
        data: {
          label: spec.label,
          category: spec.category,
          type: spec.type,
          params: defaults,
        },
      };
      setNodes((nds) => [...nds, node]);
    },
    [setNodes],
  );

  const onConnect = useCallback(
    (conn: Connection) => setEdges((eds) => addEdge(conn, eds)),
    [setEdges],
  );

  const selectedNode =
    nodes.find((n) => n.id === selectedId) ?? null;

  const updateParams = (params: Record<string, unknown>) => {
    setNodes((nds) =>
      nds.map((n) =>
        n.id === selectedId ? { ...n, data: { ...n.data, params } } : n,
      ),
    );
  };

  const deleteSelected = () => {
    setNodes((nds) => nds.filter((n) => n.id !== selectedId));
    setEdges((eds) =>
      eds.filter((e) => e.source !== selectedId && e.target !== selectedId),
    );
    setSelectedId(null);
  };

  const buildConfig = (): PipelineConfig => ({
    nodes: nodes.map((n) => ({
      id: n.id,
      type: n.data.type,
      params: n.data.params,
      position: n.position,
    })),
    edges: (edges as Edge[]).map((e) => ({
      source: e.source,
      target: e.target,
    })),
  });

  const save = async () => {
    const config = buildConfig();
    if (isNew && !savedId) {
      const created = await createMut.mutateAsync({ name, config });
      setSavedId(created.id);
      navigate(`/pipelines/${created.id}`, { replace: true });
    } else {
      await updateMut.mutateAsync({ name, config });
    }
  };

  const run = async () => {
    await save();
    const pid = savedId ?? id;
    if (!pid) return;
    const folder = prompt(
      "Server-side folder of images to process:",
      "./data/uploads",
    );
    if (!folder) return;
    submitJob.mutate(
      { pipeline_id: pid, input_folder_path: folder },
      { onSuccess: (job) => navigate(`/jobs/${job.id}`) },
    );
  };

  if (modulesQ.isLoading) return <LoadingSpinner label="Loading modules…" />;

  return (
    <div className="flex h-[calc(100vh-9rem)] flex-col">
      <div className="mb-3 flex items-center gap-3">
        <input
          className="input max-w-xs"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button
          className="btn-primary"
          onClick={save}
          disabled={createMut.isPending || updateMut.isPending}
        >
          Save
        </button>
        <button
          className="btn-secondary"
          onClick={run}
          disabled={submitJob.isPending || nodes.length === 0}
        >
          Run job
        </button>
        <span className="text-sm text-slate-400">
          {nodes.length} modules · {edges.length} connections
        </span>
      </div>

      <div className="flex flex-1 overflow-hidden rounded-xl border border-slate-200">
        <ModuleLibrary
          modules={modulesQ.data ?? []}
          onAdd={(spec) => addModule(spec)}
        />
        <div
          className="relative flex-1"
          onDrop={(e) => {
            e.preventDefault();
            const type = e.dataTransfer.getData("application/module-type");
            const spec = specByType.get(type);
            if (spec) {
              const bounds = e.currentTarget.getBoundingClientRect();
              addModule(spec, {
                x: e.clientX - bounds.left - 75,
                y: e.clientY - bounds.top - 20,
              });
            }
          }}
          onDragOver={(e) => e.preventDefault()}
        >
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={(_, n) => setSelectedId(n.id)}
            onPaneClick={() => setSelectedId(null)}
            fitView
          >
            <Background />
            <Controls />
            <MiniMap pannable zoomable />
          </ReactFlow>
        </div>
        <ParameterPanel
          node={selectedNode}
          spec={selectedNode ? specByType.get(selectedNode.data.type) : undefined}
          onChange={updateParams}
          onDelete={deleteSelected}
        />
      </div>
    </div>
  );
}
