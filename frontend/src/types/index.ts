export type Tier = "free" | "pro" | "enterprise";

export interface User {
  id: string;
  email: string;
  username: string;
  tier: Tier;
  storage_used_gb: number;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface ModuleParam {
  name: string;
  type: "number" | "select" | "boolean" | "slider" | "text";
  default?: unknown;
  options?: (string | number)[];
  min?: number;
  max?: number;
  step?: number;
}

export interface ModuleSpec {
  type: string;
  label: string;
  category: string;
  params: ModuleParam[];
}

export interface PipelineNode {
  id: string;
  type: string;
  params: Record<string, unknown>;
  position?: { x: number; y: number };
}

export interface PipelineEdge {
  source: string;
  target: string;
}

export interface PipelineConfig {
  nodes: PipelineNode[];
  edges: PipelineEdge[];
}

export interface Pipeline {
  id: string;
  user_id: string;
  name: string;
  description: string;
  config: PipelineConfig;
  version: number;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export type JobStatus =
  | "queued"
  | "processing"
  | "completed"
  | "failed"
  | "cancelled";

export interface Job {
  id: string;
  user_id: string;
  pipeline_id: string | null;
  status: JobStatus;
  input_folder_path: string;
  num_images: number;
  num_processed: number;
  num_failed: number;
  progress_percent: number;
  result_folder_path: string;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface JobResult {
  id: string;
  image_filename: string;
  metrics: {
    aggregate?: Record<string, number>;
    cells?: Record<string, number>[];
  };
  status: "success" | "failed";
  error: string | null;
  processed_at: string;
}

export interface Template {
  id: string;
  name: string;
  description: string;
  config: PipelineConfig;
}

export interface Storage {
  storage_used_gb: number;
  storage_limit_gb: number;
  tier: Tier;
}
