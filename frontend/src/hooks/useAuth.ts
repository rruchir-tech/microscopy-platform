import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import type { TokenPair, User } from "@/types";

interface Credentials {
  email: string;
  password: string;
}
interface RegisterData extends Credentials {
  username: string;
}

export function useLogin() {
  const setTokens = useAuthStore((s) => s.setTokens);
  return useMutation({
    mutationFn: async (creds: Credentials) => {
      const { data } = await api.post<TokenPair>("/api/auth/login", creds);
      return data;
    },
    onSuccess: (data) => setTokens(data.access_token, data.refresh_token),
  });
}

export function useRegister() {
  const setTokens = useAuthStore((s) => s.setTokens);
  return useMutation({
    mutationFn: async (payload: RegisterData) => {
      const { data } = await api.post<TokenPair>("/api/auth/register", payload);
      return data;
    },
    onSuccess: (data) => setTokens(data.access_token, data.refresh_token),
  });
}

export function useCurrentUser() {
  const token = useAuthStore((s) => s.accessToken);
  const setUser = useAuthStore((s) => s.setUser);
  return useQuery({
    queryKey: ["me"],
    enabled: Boolean(token),
    queryFn: async () => {
      const { data } = await api.get<User>("/api/auth/me");
      setUser(data);
      return data;
    },
  });
}
