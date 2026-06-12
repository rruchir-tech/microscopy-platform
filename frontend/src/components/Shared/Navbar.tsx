import { Link, useNavigate } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";

export function Navbar() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        <Link to="/" className="flex items-center gap-2.5">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-600 text-base text-white shadow-sm">
            🔬
          </span>
          <span className="font-heading text-lg font-semibold tracking-tight text-slate-900">
            Micro<span className="text-brand-600">Count</span>
          </span>
        </Link>
        <nav className="flex items-center gap-1 text-sm">
          <Link
            to="/"
            className="rounded-md px-3 py-1.5 font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900"
          >
            Dashboard
          </Link>
          <Link
            to="/analyze"
            className="rounded-md px-3 py-1.5 font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900"
          >
            New analysis
          </Link>
          {user && (
            <span className="badge ml-2 bg-brand-50 text-brand-700">
              {user.username} · {user.tier}
            </span>
          )}
          <button onClick={handleLogout} className="btn-secondary ml-2">
            Log out
          </button>
        </nav>
      </div>
    </header>
  );
}
