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
    <header className="sticky top-0 z-10 border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        <Link to="/" className="flex items-center gap-2 font-semibold">
          <span className="text-xl">🔬</span>
          <span>Microscopy Pipeline</span>
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link to="/" className="text-slate-600 hover:text-slate-900">
            Dashboard
          </Link>
          <Link
            to="/pipelines/new"
            className="text-slate-600 hover:text-slate-900"
          >
            New Pipeline
          </Link>
          {user && (
            <span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700">
              {user.username} · {user.tier}
            </span>
          )}
          <button onClick={handleLogout} className="btn-secondary">
            Log out
          </button>
        </nav>
      </div>
    </header>
  );
}
