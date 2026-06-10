import { useState } from "react";
import { useForm } from "react-hook-form";
import { Navigate, useNavigate } from "react-router-dom";
import { useLogin, useRegister } from "@/hooks/useAuth";
import { useAuthStore } from "@/store/authStore";

interface FormValues {
  email: string;
  username?: string;
  password: string;
}

export function LoginPage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const navigate = useNavigate();
  const isAuthenticated = useAuthStore((s) => Boolean(s.accessToken));
  const login = useLogin();
  const register = useRegister();
  const {
    register: field,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>();

  if (isAuthenticated) return <Navigate to="/" replace />;

  const pending = login.isPending || register.isPending;
  const serverError =
    (login.error as { response?: { data?: { detail?: string } } } | null)
      ?.response?.data?.detail ??
    (register.error as { response?: { data?: { detail?: string } } } | null)
      ?.response?.data?.detail;

  const onSubmit = (values: FormValues) => {
    if (mode === "login") {
      login.mutate(
        { email: values.email, password: values.password },
        { onSuccess: () => navigate("/") },
      );
    } else {
      register.mutate(
        {
          email: values.email,
          username: values.username ?? "",
          password: values.password,
        },
        { onSuccess: () => navigate("/") },
      );
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="card w-full max-w-md">
        <div className="mb-6 text-center">
          <div className="text-3xl">🔬</div>
          <h1 className="mt-2 text-xl font-semibold">Microscopy Pipeline</h1>
          <p className="text-sm text-slate-500">
            {mode === "login" ? "Sign in to your account" : "Create an account"}
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="label">Email</label>
            <input
              className="input"
              type="email"
              {...field("email", { required: "Email is required" })}
            />
            {errors.email && (
              <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>
            )}
          </div>

          {mode === "register" && (
            <div>
              <label className="label">Username</label>
              <input
                className="input"
                {...field("username", {
                  required: "Username is required",
                  minLength: { value: 3, message: "At least 3 characters" },
                })}
              />
              {errors.username && (
                <p className="mt-1 text-xs text-red-600">
                  {errors.username.message}
                </p>
              )}
            </div>
          )}

          <div>
            <label className="label">Password</label>
            <input
              className="input"
              type="password"
              {...field("password", {
                required: "Password is required",
                minLength: { value: 8, message: "At least 8 characters" },
              })}
            />
            {errors.password && (
              <p className="mt-1 text-xs text-red-600">
                {errors.password.message}
              </p>
            )}
          </div>

          {serverError && (
            <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
              {serverError}
            </p>
          )}

          <button
            type="submit"
            className="btn-primary w-full"
            disabled={pending}
          >
            {pending
              ? "Please wait…"
              : mode === "login"
                ? "Sign in"
                : "Create account"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-slate-500">
          {mode === "login" ? "No account yet?" : "Already have an account?"}{" "}
          <button
            className="font-medium text-brand-600 hover:underline"
            onClick={() => setMode(mode === "login" ? "register" : "login")}
          >
            {mode === "login" ? "Register" : "Sign in"}
          </button>
        </p>
      </div>
    </div>
  );
}
