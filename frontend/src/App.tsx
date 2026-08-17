import { Link, Route, Routes } from "react-router-dom";
import { GitBranch, ShieldAlert } from "lucide-react";
import ChangeList from "./pages/ChangeList";
import ChangeDetail from "./pages/ChangeDetail";
import NewChange from "./pages/NewChange";

export default function App() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white/90 backdrop-blur sticky top-0 z-20">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
          <Link to="/" className="flex items-center gap-2 font-semibold text-brand-700">
            <GitBranch className="h-5 w-5" />
            GxP Change Control
          </Link>
          <nav className="flex items-center gap-2 text-sm">
            <Link className="btn-ghost" to="/">
              Queue
            </Link>
            <Link className="btn-primary" to="/new">
              New change
            </Link>
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
