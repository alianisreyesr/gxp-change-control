const BASE = import.meta.env.VITE_API_URL ?? "/api";

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown, message: string) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

function responseMessage(parsed: unknown, fallback: string): string {
  if (typeof parsed === "object" && parsed) {
    const body = parsed as { message?: unknown; detail?: unknown };
    if (typeof body.message === "string") return body.message;
    if (typeof body.detail === "string") return body.detail;
  }
  if (typeof parsed === "string" && parsed.trim()) return parsed;
  return fallback;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (init?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    let parsed: unknown = null;
    const text = await res.text();
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = text;
    }
    throw new ApiError(res.status, parsed, responseMessage(parsed, res.statusText));
  }
  return res.json() as Promise<T>;
}

export type Change = {
  id: string;
  title: string;
  description: string;
  system_name: string;
  change_type: string;
  priority: string;
  status: string;
  requester: string;
  business_justification?: string | null;
  target_implementation_date?: string | null;
  created_at: string;
  updated_at: string;
};

export type Activity = {
  id: number;
  change_id: string;
  actor: string;
  action: string;
  detail?: string | null;
  created_at: string;
};

export type ImpactAssessment = {
  id: string;
  change_id: string;
  affects_validated_state: boolean;
  affects_part11_controls: boolean;
  affects_data_integrity: boolean;
  affects_training: boolean;
  affects_sops: boolean;
  risk_summary: string;
  residual_risk: "low" | "medium" | "high";
  assessor: string;
  assessed_at?: string | null;
};

export type Approval = {
  id: string;
  change_id: string;
  role: string;
  decision: "approve" | "reject" | "request_info";
  comment?: string | null;
  actor: string;
  decided_at: string;
};

/** Map server 422 details → field errors for forms. */
export function map422ToFields(body: unknown): Record<string, string[]> {
  const out: Record<string, string[]> = {};
  if (!body || typeof body !== "object") return out;
  const details = (body as { details?: { loc?: (string | number)[]; msg?: string }[] }).details;
  if (!Array.isArray(details)) return out;
  for (const d of details) {
    const loc = (d.loc ?? []).filter((x) => x !== "body" && x !== "query" && x !== "path");
    const key = loc.length ? String(loc[loc.length - 1]) : "_form";
    if (!out[key]) out[key] = [];
    out[key].push(d.msg ?? "Invalid value");
  }
  return out;
}

export const api = {
  health: () => request<{ status: string; data_classification: string }>("/health"),
  listChanges: (status?: string) =>
    request<Change[]>(status ? `/changes?status=${encodeURIComponent(status)}` : "/changes"),
  getChange: (id: string) => request<Change>(`/changes/${id}`),
  createChange: (body: Record<string, unknown>) =>
    request<Change>("/changes", { method: "POST", body: JSON.stringify(body) }),
  submit: (id: string, actor: string) =>
    request<Change>(`/changes/${id}/submit?actor=${encodeURIComponent(actor)}`, { method: "POST" }),
  impact: (id: string, body: Record<string, unknown>) =>
    request<ImpactAssessment>(`/changes/${id}/impact`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getImpact: (id: string) => request<ImpactAssessment>(`/changes/${id}/impact`),
  approve: (id: string, body: Record<string, unknown>) =>
    request<Approval>(`/changes/${id}/approve`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  advance: (id: string, actor: string) =>
    request<Change>(`/changes/${id}/advance?actor=${encodeURIComponent(actor)}`, { method: "POST" }),
  activity: (id: string) => request<Activity[]>(`/changes/${id}/activity`),
  getSchema: (name: string) => request<Record<string, unknown>>(`/schemas/${name}`),
};
