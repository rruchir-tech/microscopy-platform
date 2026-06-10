import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";

export function AuthGuard() {
  const isAuthenticated = useAuthStore((s) => Boolean(s.accessToken));
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}
