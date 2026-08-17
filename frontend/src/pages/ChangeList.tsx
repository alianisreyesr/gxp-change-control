import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { PriorityBadge, StatusBadge } from "../components/StatusBadge";
import { Loader2 } from "lucide-react";

export default function ChangeList() {
  const { data, isLoading, error } = useQuery({ queryKey: ["changes"], queryFn: () => api.listChanges() });

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-slate-600">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading change queue…
      </div>
    );
  }

  if (error) {
    return (
      <div className="card p-4 text-rose-700">
        Failed to load changes. Start the API with <code className="font-mono text-sm">uvicorn app.main:app --reload</code>
        .
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-brand-900">Change queue</h1>
        <p className="text-sm text-slate-600">Illustrative GxP change control workflow — synthetic records only.</p>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Title</th>
              <th className="px-4 py-3">System</th>
              <th className="px-4 py-3">Priority</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {data?.map((c) => (
              <tr key={c.id} className="hover:bg-slate-50/80">
                <td className="px-4 py-3 font-mono text-xs text-brand-700">
                  <Link to={`/changes/${c.id}`}>{c.id}</Link>
                </td>
                <td className="px-4 py-3">
                  <Link className="font-medium text-slate-900 hover:text-brand-700" to={`/changes/${c.id}`}>
                    {c.title}
                  </Link>
                </td>
                <td className="px-4 py-3 text-slate-600">{c.system_name}</td>
                <td className="px-4 py-3">
                  <PriorityBadge priority={c.priority} />
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={c.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
