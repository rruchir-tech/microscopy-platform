import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { api } from "@/services/api";
import type { Job, JobResult, Storage } from "@/types";

export function useJobs() {
  return useQuery({
    queryKey: ["jobs"],
    queryFn: async () => (await api.get<Job[]>("/api/jobs")).data,
    refetchInterval: (query) => {
      const jobs = query.state.data as Job[] | undefined;
      const active = jobs?.some(
        (j) => j.status === "queued" || j.status === "processing",
      );
      return active ? 2000 : false;
    },
  });
}

export function useJob(id: string | undefined) {
  return useQuery({
    queryKey: ["job", id],
    enabled: Boolean(id),
    queryFn: async () => (await api.get<Job>(`/api/jobs/${id}`)).data,
    refetchInterval: (query) => {
      const job = query.state.data as Job | undefined;
      return job && (job.status === "queued" || job.status === "processing")
        ? 1500
        : false;
    },
  });
}

export function useJobResults(id: string | undefined) {
  return useQuery({
    queryKey: ["job-results", id],
    enabled: Boolean(id),
    queryFn: async () =>
      (await api.get<JobResult[]>(`/api/jobs/${id}/results`)).data,
  });
}

export function useSubmitJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      pipeline_id: string;
      input_folder_path: string;
    }) => (await api.post<Job>("/api/jobs", payload)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["jobs"] }),
  });
}

export function useCancelJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) =>
      (await api.post<Job>(`/api/jobs/${id}/cancel`)).data,
    onSuccess: (_data, id) => {
      qc.invalidateQueries({ queryKey: ["jobs"] });
      qc.invalidateQueries({ queryKey: ["job", id] });
    },
  });
}

export function useStorage() {
  return useQuery({
    queryKey: ["storage"],
    queryFn: async () => (await api.get<Storage>("/api/user/storage")).data,
  });
}
