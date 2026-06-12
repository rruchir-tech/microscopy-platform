import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "@/store/authStore";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const api = axios.create({ baseURL });

// Attach the access token to every request.
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On 401, try a one-time refresh; if that fails, log out.
let refreshing: Promise<string | null> | null = null;

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & {
      _retried?: boolean;
    };
    const store = useAuthStore.getState();

    if (
      error.response?.status === 401 &&
      original &&
      !original._retried &&
      store.refreshToken &&
      !original.url?.includes("/api/auth/")
    ) {
      original._retried = true;
      refreshing =
        refreshing ??
        api
          .post<{ access_token: string; refresh_token: string }>(
            "/api/auth/refresh",
            { refresh_token: store.refreshToken },
          )
          .then((r) => {
            store.setTokens(r.data.access_token, r.data.refresh_token);
            return r.data.access_token;
          })
          .catch(() => {
            store.logout();
            return null;
          })
          .finally(() => {
            refreshing = null;
          });

      const newToken = await refreshing;
      if (newToken) {
        original.headers.Authorization = `Bearer ${newToken}`;
        return api(original);
      }
    }
    return Promise.reject(error);
  },
);
