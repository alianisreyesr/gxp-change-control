import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import { PriorityBadge, StatusBadge } from "../components/StatusBadge";
import { Loader2 } from "lucide-react";
import { useState } from "react";

export default function ChangeDetail() {
  const { id = "" } = useParams();
  const qc = useQueryClient();
  const [actor, setActor] = useState("a.reyes");

  const changeQ = useQuery({ queryKey: ["change", id], queryFn: () => api.getChange(id), enabled: !!id });
  const activityQ = useQuery({ queryKey: ["activity", id], queryFn: () => api.activity(id), enabled: !!id });

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["change", id] });
    qc.invalidateQueries({ queryKey: ["activity", id] });
    qc.invalidateQueries({ queryKey: ["changes"] });
  };

  const submitM = useMutation({ mutationFn: () => api.submit(id, actor), onSuccess: refresh });
  const impactM = useMutation({
    mutationFn: () =>
      api.impact(id, {
        affects_validated_state: false,
        affects_part11_controls: false,
        affects_data_integrity: false,
        affects_training: false,
        affects_sops: true,
        risk_summary: "Illustrative assessment: documentation/SOP alignment only (synthetic).",
        residual_risk: "low",
        assessor: actor,
      }),
    onSuccess: refresh,
  });
  const approveM = useMutation({
    mutationFn: () =>
      api.approve(id, { role: "Quality", decision: "approve", comment: "Approved for demo workflow", actor }),
    onSuccess: refresh,
  });
  const advanceM = useMutation({ mutationFn: () => api.advance(id, actor), onSuccess: refresh });

  if (changeQ.isLoading) {
    return (
      <div className="flex items-center gap-2 text-slate-600">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading…
      </div>
    );
  }
  if (changeQ.error || !changeQ.data) {
    return <div className="card p-4 text-rose-700">Change not found or API offline.</div>;
  }

  const c = changeQ.data;

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="space-y-4 lg:col-span-2">
        <div className="card p-5">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <span className="font-mono text-sm text-brand-700">{c.id}</span>
            <StatusBadge status={c.status} />
            <PriorityBadge priority={c.priority} />
          </div>
          <h1 className="text-2xl font-semibold text-brand-900">{c.title}</h1>
          <p className="mt-2 text-slate-700">{c.description}</p>
          <dl className="mt-4 grid gap-2 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-slate-500">System</dt>
              <dd className="font-medium">{c.system_name}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Type</dt>
              <dd className="font-medium">{c.change_type}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Requester</dt>
              <dd className="font-medium">{c.requester}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Updated</dt>
              <dd className="font-mono text-xs">{c.updated_at}</dd>
            </div>
          </dl>
        </div>

        <div className="card p-5">
          <h2 className="mb-3 font-semibold text-brand-900">Workflow actions</h2>
          <label className="mb-3 block text-sm">
            <span className="text-slate-600">Actor (attributable)</span>
            <input
              className="mt-1 w-full max-w-xs rounded-lg border border-slate-300 px-3 py-2"
              value={actor}
              onChange={(e) => setActor(e.target.value)}
            />
          </label>
          <div className="flex flex-wrap gap-2">
            {(c.status === "draft" || c.status === "rejected") && (
              <button className="btn-primary" onClick={() => submitM.mutate()} disabled={submitM.isPending}>
                Submit for impact
              </button>
            )}
            {(c.status === "impact_assessment" || c.status === "submitted") && (
              <button className="btn-primary" onClick={() => impactM.mutate()} disabled={impactM.isPending}>
                Record impact (demo)
              </button>
            )}
            {c.status === "pending_approval" && (
              <button className="btn-primary" onClick={() => approveM.mutate()} disabled={approveM.isPending}>
                Approve
              </button>
            )}
            {["approved", "implementing", "verification"].includes(c.status) && (
              <button className="btn-primary" onClick={() => advanceM.mutate()} disabled={advanceM.isPending}>
                Advance stage
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="card p-5">
        <h2 className="mb-3 font-semibold text-brand-900">Activity log</h2>
        <ul className="space-y-3 text-sm">
          {activityQ.data?.map((a) => (
            <li key={a.id} className="border-l-2 border-brand-200 pl-3">
              <div className="font-medium text-slate-900">{a.action}</div>
              <div className="text-xs text-slate-500">
                {a.actor} · {a.created_at}
              </div>
              {a.detail && <p className="mt-1 text-slate-600">{a.detail}</p>}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
