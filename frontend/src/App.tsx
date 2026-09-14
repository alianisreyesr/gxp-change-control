import { FormEvent, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";
import { GitBranch, ShieldAlert } from "lucide-react";
import ChangeList from "./pages/ChangeList";
import ChangeDetail from "./pages/ChangeDetail";
import NewChange from "./pages/NewChange";
import { api, type AuthUser } from "./api/client";

function Login({ onLogin }: { onLogin: (user: AuthUser) => void }) {
  const [username, setUsername] = useState("requester.demo");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      onLogin(await api.login(username, password));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto max-w-md px-4 py-16">
      <form onSubmit={submit} className="card space-y-4 p-6">
        <div><h1 className="text-xl font-semibold text-brand-900">Sign in to the workflow</h1><p className="text-sm text-slate-600">Synthetic demo identity; JWT expires after one hour.</p></div>
        <label className="block text-sm"><span className="font-medium">Username</span><input className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" value={username} onChange={(e) => setUsername(e.target.value)} /></label>
        <label className="block text-sm"><span className="font-medium">Password</span><input type="password" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" value={password} onChange={(e) => setPassword(e.target.value)} /></label>
        {error && <p className="text-sm text-rose-600">{error}</p>}
        <button className="btn-primary" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
        <p className="text-xs text-slate-500">Additional role accounts are documented in the repository README.</p>
      </form>
    </main>
  );
}

export default function App() {
  const [user, setUser] = useState<AuthUser | null>(() => api.sessionUser());
  if (!user) return <Login onLogin={setUser} />;
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white/90 backdrop-blur sticky top-0 z-20">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
          <Link to="/" className="flex items-center gap-2 font-semibold text-brand-700">
            <GitBranch className="h-5 w-5" />
            GxP Change Control
          </Link>
          <nav className="flex items-center gap-2 text-sm">
            <span className="hidden text-slate-600 sm:inline">{user.username} · {user.role}</span>
            <Link className="btn-ghost" to="/">
              Queue
            </Link>
            {(user.role === "requester" || user.role === "admin") && <Link className="btn-primary" to="/new">New change</Link>}
            <button className="btn-ghost" onClick={() => { api.logout(); setUser(null); }}>Sign out</button>
          </nav>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-4 py-3">
        <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-950">
          <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" />
          <p>
            <strong>Portfolio boundary:</strong> synthetic data only. Not validated software. Not for regulated
            decisions.
          </p>
        </div>
      </div>

      <main className="mx-auto max-w-6xl px-4 pb-16">
        <Routes>
          <Route path="/" element={<ChangeList />} />
          <Route path="/new" element={<NewChange />} />
          <Route path="/changes/:id" element={<ChangeDetail />} />
        </Routes>
      </main>
    </div>
  );
}
