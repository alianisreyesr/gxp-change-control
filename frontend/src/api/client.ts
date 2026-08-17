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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    let parsed: unknown = null;
    const text = await res.text();
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = text;
    }
    const msg =
      typeof parsed === "object" &&
      parsed &&
      "message" in parsed &&
      typeof (parsed as { message: unknown }).message === "string"
        ? (parsed as { message: string }).message
        : text || res.statusText;
    throw new ApiError(res.status, parsed, msg);
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
    request(`/changes/${id}/impact`, { method: "POST", body: JSON.stringify(body) }),
  approve: (id: string, body: Record<string, unknown>) =>
    request(`/changes/${id}/approve`, { method: "POST", body: JSON.stringify(body) }),
  advance: (id: string, actor: string) =>
    request<Change>(`/changes/${id}/advance?actor=${encodeURIComponent(actor)}`, { method: "POST" }),
  activity: (id: string) => request<Activity[]>(`/changes/${id}/activity`),
  getSchema: (name: string) => request<Record<string, unknown>>(`/schemas/${name}`),
};
