import { Link, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { api, clearToken, getToken, User } from "./api";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import NewClaimPage from "./pages/NewClaimPage";
import ClaimDetailPage from "./pages/ClaimDetailPage";
import ReviewPage from "./pages/ReviewPage";

function Layout({ user, onLogout }: { user: User; onLogout: () => void }) {
  const isReviewer = user.role === "reviewer" || user.role === "admin";
  return (
    <div className="min-h-screen">
      <header className="border-b bg-white shadow-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <Link to="/" className="text-lg font-semibold text-teal-800">
            NRL Medical Claim Engine
          </Link>
          <nav className="flex items-center gap-4 text-sm">
            <Link to="/" className="hover:text-teal-700">
              Claims
            </Link>
            {user.role === "employee" && (
              <Link to="/claims/new" className="hover:text-teal-700">
                New claim
              </Link>
            )}
            {isReviewer && (
              <Link to="/review" className="hover:text-teal-700">
                Review queue
              </Link>
            )}
            <span className="text-slate-500">{user.full_name}</span>
            <button onClick={onLogout} className="rounded bg-slate-200 px-3 py-1 hover:bg-slate-300">
              Logout
            </button>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/claims/new" element={<NewClaimPage />} />
          <Route path="/claims/:id" element={<ClaimDetailPage />} />
          <Route path="/review" element={<ReviewPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (!getToken()) {
      setLoading(false);
      return;
    }
    api<User>("/auth/me")
      .then(setUser)
      .catch(() => clearToken())
      .finally(() => setLoading(false));
  }, []);

  const onLogout = () => {
    clearToken();
    setUser(null);
    navigate("/login");
  };

  if (loading) return <div className="p-8 text-center">Loading…</div>;

  return (
    <Routes>
      <Route
        path="/login"
        element={
          user ? (
            <Navigate to="/" />
          ) : (
            <LoginPage
              onLogin={(u) => {
                setUser(u);
                navigate("/");
              }}
            />
          )
        }
      />
      <Route
        path="/*"
        element={
          user ? (
            <Layout user={user} onLogout={onLogout} />
          ) : (
            <Navigate to="/login" />
          )
        }
      />
    </Routes>
  );
}
