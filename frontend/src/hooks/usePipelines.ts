import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { api } from "@/services/api";
import type { ModuleSpec, Pipeline, PipelineConfig, Template } from "@/types";

export function usePipelines() {
  return useQuery({
    queryKey: ["pipelines"],
    queryFn: async () => (await api.get<Pipeline[]>("/api/pipelines")).data,
  });
}

export function usePipeline(id: string | undefined) {
  return useQuery({
    queryKey: ["pipeline", id],
    enabled: Boolean(id),
    queryFn: async () =>
      (await api.get<Pipeline>(`/api/pipelines/${id}`)).data,
  });
}

export function useModules() {
  return useQuery({
    queryKey: ["modules"],
    staleTime: Infinity,
    queryFn: async () =>
      (await api.get<ModuleSpec[]>("/api/pipelines/modules")).data,
  });
}

export function useTemplates() {
  return useQuery({
    queryKey: ["templates"],
    queryFn: async () => (await api.get<Template[]>("/api/templates")).data,
  });
}

interface SavePayload {
  name: string;
  description?: string;
  config: PipelineConfig;
}

export function useCreatePipeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: SavePayload) =>
      (await api.post<Pipeline>("/api/pipelines", payload)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pipelines"] }),
  });
}

export function useUpdatePipeline(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Partial<SavePayload>) =>
      (await api.put<Pipeline>(`/api/pipelines/${id}`, payload)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["pipelines"] });
      qc.invalidateQueries({ queryKey: ["pipeline", id] });
    },
  });
}

export function useDeletePipeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => api.delete(`/api/pipelines/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pipelines"] }),
  });
}

export function useClonePipeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) =>
      (await api.post<Pipeline>(`/api/pipelines/${id}/clone`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pipelines"] }),
  });
}

export function useInstantiateTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (templateId: string) =>
      (await api.post<Pipeline>(`/api/templates/${templateId}/instantiate`))
        .data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pipelines"] }),
  });
}
