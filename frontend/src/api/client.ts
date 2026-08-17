const BASE = import.meta.env.VITE_API_URL ?? "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || res.statusText);
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
};
