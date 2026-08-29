import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { Loader2 } from "lucide-react";

import { ApiError, api, map422ToFields } from "../api/client";
import { FieldError } from "../components/FieldError";
import { PriorityBadge, StatusBadge } from "../components/StatusBadge";
import { useSchemaValidation } from "../validation/useSchemaValidation";

const IMPACT_FLAGS = [
  ["affects_validated_state", "Validated state"],
  ["affects_part11_controls", "Part 11 controls"],
  ["affects_data_integrity", "Data integrity"],
  ["affects_training", "Training"],
  ["affects_sops", "SOPs"],
] as const;

const IMPACT_RECORD_STATUSES = new Set([
  "pending_approval",
  "approved",
  "rejected",
  "implementing",
  "verification",
  "closed",
]);

const ADVANCE_LABELS: Record<string, string> = {
  approved: "Start implementation",
  implementing: "Send to verification",
  verification: "Close change",
};

type ImpactFormState = {
  affects_validated_state: boolean;
  affects_part11_controls: boolean;
  affects_data_integrity: boolean;
  affects_training: boolean;
  affects_sops: boolean;
  risk_summary: string;
  residual_risk: "low" | "medium" | "high";
};

type ApprovalFormState = {
  role: string;
  decision: "approve" | "reject" | "request_info";
  comment: string;
};

function errorMessage(error: unknown): string {
  if (error instanceof Error && error.message) return error.message;
  return "Workflow action failed";
}

export default function ChangeDetail() {
  const { id = "" } = useParams();
  const qc = useQueryClient();

  const [actor, setActor] = useState("a.reyes");
  const [actorErrors, setActorErrors] = useState<string[]>([]);
  const [actionError, setActionError] = useState<string | null>(null);
  const [impactForm, setImpactForm] = useState<ImpactFormState>({
    affects_validated_state: false,
    affects_part11_controls: false,
    affects_data_integrity: false,
    affects_training: false,
    affects_sops: false,
    risk_summary: "",
    residual_risk: "low",
  });
  const [approvalForm, setApprovalForm] = useState<ApprovalFormState>({
    role: "Quality",
    decision: "approve",
    comment: "",
  });

  const impactValidation = useSchemaValidation("impact-assessment-in");
  const approvalValidation = useSchemaValidation("approval-in");

  const changeQ = useQuery({
    queryKey: ["change", id],
    queryFn: () => api.getChange(id),
    enabled: !!id,
  });
  const activityQ = useQuery({
    queryKey: ["activity", id],
    queryFn: () => api.activity(id),
    enabled: !!id,
  });
  const impactQ = useQuery({
    queryKey: ["impact", id],
    queryFn: () => api.getImpact(id),
    enabled: !!id && IMPACT_RECORD_STATUSES.has(changeQ.data?.status ?? ""),
    retry: false,
  });

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["change", id] });
    qc.invalidateQueries({ queryKey: ["activity", id] });
    qc.invalidateQueries({ queryKey: ["impact", id] });
    qc.invalidateQueries({ queryKey: ["changes"] });
  };

  function handleActorActionError(error: unknown) {
    if (error instanceof ApiError && error.status === 422) {
      const fields = map422ToFields(error.body);
      setActorErrors(fields.actor ?? fields._form ?? [error.message]);
      return;
    }
    setActionError(errorMessage(error));
  }

  const submitM = useMutation({
    mutationFn: () => api.submit(id, actor.trim()),
    onSuccess: () => {
      setActorErrors([]);
      setActionError(null);
      refresh();
    },
    onError: handleActorActionError,
  });

  const impactM = useMutation({
    mutationFn: (payload: Record<string, unknown>) => api.impact(id, payload),
    onSuccess: () => {
      impactValidation.clearErrors();
      setActionError(null);
      refresh();
    },
    onError: (error: unknown) => {
      if (error instanceof ApiError && error.status === 422) {
        impactValidation.setFieldErrors(map422ToFields(error.body));
        return;
      }
      setActionError(errorMessage(error));
    },
  });

  const approveM = useMutation({
    mutationFn: (payload: Record<string, unknown>) => api.approve(id, payload),
    onSuccess: () => {
      approvalValidation.clearErrors();
      setActionError(null);
      refresh();
    },
    onError: (error: unknown) => {
      if (error instanceof ApiError && error.status === 422) {
        approvalValidation.setFieldErrors(map422ToFields(error.body));
        return;
      }
      setActionError(errorMessage(error));
    },
  });

  const advanceM = useMutation({
    mutationFn: () => api.advance(id, actor.trim()),
    onSuccess: () => {
      setActorErrors([]);
      setActionError(null);
      refresh();
    },
    onError: handleActorActionError,
  });

  async function onImpactSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setActionError(null);
    const payload: Record<string, unknown> = {
      ...impactForm,
      risk_summary: impactForm.risk_summary.trim(),
      assessor: actor.trim(),
    };
    const result = await impactValidation.validate(payload);
    if (!result.ok) return;
    impactM.mutate(result.data);
  }

  async function onApprovalSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setActionError(null);
    const payload: Record<string, unknown> = {
      role: approvalForm.role.trim(),
      decision: approvalForm.decision,
      actor: actor.trim(),
    };
    const comment = approvalForm.comment.trim();
    if (comment) payload.comment = comment;
    const result = await approvalValidation.validate(payload);
    if (!result.ok) return;
    approveM.mutate(result.data);
  }

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
  const combinedActorErrors = [
    ...actorErrors,
    ...(impactValidation.fieldErrors.assessor ?? []),
    ...(approvalValidation.fieldErrors.actor ?? []),
  ];
  const activeImpactFlags = impactQ.data
    ? IMPACT_FLAGS.filter(([key]) => impactQ.data?.[key]).map(([, label]) => label)
    : [];
  const approvalButtonLabel =
    approvalForm.decision === "approve"
      ? "Approve change"
      : approvalForm.decision === "reject"
        ? "Reject change"
        : "Request more information";

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
            {c.target_implementation_date && (
              <div>
                <dt className="text-slate-500">Target date</dt>
                <dd className="font-medium">{c.target_implementation_date}</dd>
              </div>
            )}
          </dl>
          {c.business_justification && (
            <div className="mt-4 rounded-lg bg-slate-50 p-3 text-sm">
              <div className="font-medium text-slate-700">Business justification</div>
              <p className="mt-1 text-slate-600">{c.business_justification}</p>
            </div>
          )}
        </div>

        <div className="card p-5">
          <h2 className="font-semibold text-brand-900">Workflow actions</h2>
          <p className="mt-1 text-sm text-slate-600">
            Every transition requires an attributable individual identifier and is written to the activity log.
          </p>

          <label className="mt-4 block text-sm">
            <span className="font-medium text-slate-700">Actor</span>
            <input
              className={`mt-1 w-full max-w-sm rounded-lg border px-3 py-2 ${
                combinedActorErrors.length ? "border-rose-400 ring-1 ring-rose-200" : "border-slate-300"
              }`}
              value={actor}
              onChange={(event) => {
                setActor(event.target.value);
                setActorErrors([]);
              }}
            />
            <FieldError messages={combinedActorErrors} />
          </label>

          {(c.status === "draft" || c.status === "rejected") && (
            <button
              className="btn-primary mt-4"
              onClick={() => submitM.mutate()}
              disabled={submitM.isPending}
            >
              {submitM.isPending ? "Submitting…" : "Submit for impact assessment"}
            </button>
          )}

          {c.status === "impact_assessment" && (
            <form onSubmit={onImpactSubmit} className="mt-5 space-y-4 border-t border-slate-200 pt-5" noValidate>
              <div>
                <h3 className="font-medium text-brand-900">Impact assessment</h3>
                <p className="text-sm text-slate-600">Select every area that could be affected by the change.</p>
              </div>

              <div className="grid gap-2 sm:grid-cols-2">
                {IMPACT_FLAGS.map(([key, label]) => (
                  <label key={key} className="flex items-center gap-2 rounded-lg border border-slate-200 p-3 text-sm">
                    <input
                      type="checkbox"
                      checked={impactForm[key]}
                      onChange={(event) =>
                        setImpactForm((current) => ({ ...current, [key]: event.target.checked }))
                      }
                    />
                    {label}
                  </label>
                ))}
              </div>

              <label className="block text-sm">
                <span className="font-medium text-slate-700">Residual risk</span>
                <select
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
                  value={impactForm.residual_risk}
                  onChange={(event) =>
                    setImpactForm((current) => ({
                      ...current,
                      residual_risk: event.target.value as ImpactFormState["residual_risk"],
                    }))
                  }
                >
                  <option value="low">low</option>
                  <option value="medium">medium</option>
                  <option value="high">high</option>
                </select>
                <FieldError messages={impactValidation.fieldErrors.residual_risk} />
              </label>

              <label className="block text-sm">
                <span className="font-medium text-slate-700">Risk summary</span>
                <textarea
                  className={`mt-1 w-full rounded-lg border px-3 py-2 ${
                    impactValidation.fieldErrors.risk_summary
                      ? "border-rose-400 ring-1 ring-rose-200"
                      : "border-slate-300"
                  }`}
                  rows={4}
                  value={impactForm.risk_summary}
                  onChange={(event) =>
                    setImpactForm((current) => ({ ...current, risk_summary: event.target.value }))
                  }
                />
                <FieldError messages={impactValidation.fieldErrors.risk_summary} />
              </label>

              <FieldError messages={impactValidation.fieldErrors._form} />
              {impactValidation.formErrors.length > 0 && (
                <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800">
                  {impactValidation.formErrors.join(" · ")}
                </div>
              )}

              <button
                className="btn-primary"
                type="submit"
                disabled={impactM.isPending || impactValidation.validating}
              >
                {impactValidation.validating
                  ? "Validating…"
                  : impactM.isPending
                    ? "Recording…"
                    : "Record impact assessment"}
              </button>
            </form>
          )}

          {c.status === "pending_approval" && (
            <form onSubmit={onApprovalSubmit} className="mt-5 space-y-4 border-t border-slate-200 pt-5" noValidate>
              <div>
                <h3 className="font-medium text-brand-900">Approval decision</h3>
                <p className="text-sm text-slate-600">
                  Approve, reject, or return the assessment for additional information.
                </p>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <label className="block text-sm">
                  <span className="font-medium text-slate-700">Role</span>
                  <input
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
                    value={approvalForm.role}
                    onChange={(event) =>
                      setApprovalForm((current) => ({ ...current, role: event.target.value }))
                    }
                  />
                  <FieldError messages={approvalValidation.fieldErrors.role} />
                </label>
                <label className="block text-sm">
                  <span className="font-medium text-slate-700">Decision</span>
                  <select
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
                    value={approvalForm.decision}
                    onChange={(event) =>
                      setApprovalForm((current) => ({
                        ...current,
                        decision: event.target.value as ApprovalFormState["decision"],
                      }))
                    }
                  >
                    <option value="approve">approve</option>
                    <option value="reject">reject</option>
                    <option value="request_info">request information</option>
                  </select>
                  <FieldError messages={approvalValidation.fieldErrors.decision} />
                </label>
              </div>

              <label className="block text-sm">
                <span className="font-medium text-slate-700">
                  Comment
                  {approvalForm.decision !== "approve" && (
                    <span className="ml-1 font-normal text-rose-600">(required)</span>
                  )}
                </span>
                <textarea
                  className={`mt-1 w-full rounded-lg border px-3 py-2 ${
                    approvalValidation.fieldErrors.comment
                      ? "border-rose-400 ring-1 ring-rose-200"
                      : "border-slate-300"
                  }`}
                  rows={3}
                  value={approvalForm.comment}
                  onChange={(event) =>
                    setApprovalForm((current) => ({ ...current, comment: event.target.value }))
                  }
                />
                <FieldError messages={approvalValidation.fieldErrors.comment} />
              </label>

              <FieldError messages={approvalValidation.fieldErrors._form} />
              {approvalValidation.formErrors.length > 0 && (
                <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800">
                  {approvalValidation.formErrors.join(" · ")}
                </div>
              )}

              <button
                className="btn-primary"
                type="submit"
                disabled={approveM.isPending || approvalValidation.validating}
              >
                {approvalValidation.validating
                  ? "Validating…"
                  : approveM.isPending
                    ? "Saving decision…"
                    : approvalButtonLabel}
              </button>
            </form>
          )}

          {["approved", "implementing", "verification"].includes(c.status) && (
            <button
              className="btn-primary mt-4"
              onClick={() => advanceM.mutate()}
              disabled={advanceM.isPending}
            >
              {advanceM.isPending ? "Advancing…" : ADVANCE_LABELS[c.status]}
            </button>
          )}

          {actionError && (
            <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800">
              {actionError}
            </div>
          )}
        </div>

        {impactQ.data && (
          <div className="card p-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="font-semibold text-brand-900">Recorded impact assessment</h2>
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
                residual risk: {impactQ.data.residual_risk}
              </span>
            </div>
            <p className="mt-3 text-sm text-slate-700">{impactQ.data.risk_summary}</p>
            <dl className="mt-4 grid gap-2 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-slate-500">Assessor</dt>
                <dd className="font-medium">{impactQ.data.assessor}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Affected areas</dt>
                <dd className="font-medium">
                  {activeImpactFlags.length ? activeImpactFlags.join(", ") : "No impact flags selected"}
                </dd>
              </div>
            </dl>
          </div>
        )}
      </div>

      <div className="card p-5">
        <h2 className="mb-3 font-semibold text-brand-900">Activity log</h2>
        {activityQ.isLoading && (
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading activity…
          </div>
        )}
        <ul className="space-y-3 text-sm">
          {activityQ.data?.map((activity) => (
            <li key={activity.id} className="border-l-2 border-brand-200 pl-3">
              <div className="font-medium text-slate-900">{activity.action}</div>
              <div className="text-xs text-slate-500">
                {activity.actor} · {activity.created_at}
              </div>
              {activity.detail && <p className="mt-1 text-slate-600">{activity.detail}</p>}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
