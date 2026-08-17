import { FormEvent, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

export default function NewChange() {
  const nav = useNavigate();
  const qc = useQueryClient();
  const [form, setForm] = useState({
    title: "",
    description: "",
    system_name: "",
    change_type: "configuration",
    priority: "medium",
    requester: "a.reyes",
    business_justification: "",
  });

  const mutation = useMutation({
    mutationFn: () => api.createChange(form),
    onSuccess: (c) => {
      qc.invalidateQueries({ queryKey: ["changes"] });
      nav(`/changes/${c.id}`);
    },
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    mutation.mutate();
  }

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <h1 className="text-2xl font-semibold text-brand-900">New change request</h1>
      <form onSubmit={onSubmit} className="card space-y-4 p-5">
        {(["title", "system_name", "requester"] as const).map((k) => (
          <label key={k} className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">{k.replace("_", " ")}</span>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              value={form[k]}
              onChange={(e) => setForm({ ...form, [k]: e.target.value })}
              required
            />
          </label>
        ))}
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-700">description</span>
          <textarea
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
            rows={4}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            required
          />
        </label>
        <div className="grid grid-cols-2 gap-3">
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">change type</span>
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              value={form.change_type}
              onChange={(e) => setForm({ ...form, change_type: e.target.value })}
            >
              {["configuration", "code", "process", "infrastructure", "documentation"].map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">priority</span>
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              value={form.priority}
              onChange={(e) => setForm({ ...form, priority: e.target.value })}
            >
              {["low", "medium", "high", "critical"].map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
        </div>
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-700">business justification</span>
          <textarea
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
            rows={2}
            value={form.business_justification}
            onChange={(e) => setForm({ ...form, business_justification: e.target.value })}
          />
        </label>
        {mutation.isError && <p className="text-sm text-rose-600">{(mutation.error as Error).message}</p>}
        <button className="btn-primary" type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? "Creating…" : "Create draft"}
        </button>
      </form>
    </div>
  );
}
