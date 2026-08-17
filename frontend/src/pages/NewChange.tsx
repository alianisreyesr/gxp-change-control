import { FormEvent, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { ApiError, api, map422ToFields } from "../api/client";
import { FieldError } from "../components/FieldError";
import { prepareChangeCreatePayload } from "../validation/ajvClient";
import { useSchemaValidation } from "../validation/useSchemaValidation";

export default function NewChange() {
  const nav = useNavigate();
  const qc = useQueryClient();
  const { validate, fieldErrors, formErrors, validating, setFieldErrors } =
    useSchemaValidation("change-create");

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
    mutationFn: (payload: Record<string, unknown>) => api.createChange(payload),
    onSuccess: (c) => {
      qc.invalidateQueries({ queryKey: ["changes"] });
      nav(`/changes/${c.id}`);
    },
    onError: (err: unknown) => {
      if (err instanceof ApiError && err.status === 422) {
        setFieldErrors(map422ToFields(err.body));
      }
    },
  });

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const payload = prepareChangeCreatePayload(form);
    const result = await validate(payload);
    if (!result.ok) return;
    mutation.mutate(result.data);
  }

  function set<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  const inputCls = (field: string) =>
    `w-full rounded-lg border px-3 py-2 ${
      fieldErrors[field] ? "border-rose-400 ring-1 ring-rose-200" : "border-slate-300"
    }`;

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div>
        <h1 className="text-2xl font-semibold text-brand-900">New change request</h1>
        <p className="text-sm text-slate-600">
          Client-side validation via <strong>Ajv</strong> + JSON Schema (<code className="text-xs">change-create</code>
          ), then server-side Pydantic.
        </p>
      </div>

      <form onSubmit={onSubmit} className="card space-y-4 p-5" noValidate>
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-700">title</span>
          <input className={inputCls("title")} value={form.title} onChange={(e) => set("title", e.target.value)} />
          <FieldError messages={fieldErrors.title} />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-700">system name</span>
          <input
            className={inputCls("system_name")}
            value={form.system_name}
            onChange={(e) => set("system_name", e.target.value)}
          />
          <FieldError messages={fieldErrors.system_name} />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-700">requester</span>
          <input
            className={inputCls("requester")}
            value={form.requester}
            onChange={(e) => set("requester", e.target.value)}
          />
          <FieldError messages={fieldErrors.requester} />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-700">description</span>
          <textarea
            className={inputCls("description")}
            rows={4}
            value={form.description}
            onChange={(e) => set("description", e.target.value)}
          />
          <FieldError messages={fieldErrors.description} />
        </label>

        <div className="grid grid-cols-2 gap-3">
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">change type</span>
            <select
              className={inputCls("change_type")}
              value={form.change_type}
              onChange={(e) => set("change_type", e.target.value)}
            >
              {["configuration", "code", "process", "infrastructure", "documentation"].map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
            <FieldError messages={fieldErrors.change_type} />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">priority</span>
            <select
              className={inputCls("priority")}
              value={form.priority}
              onChange={(e) => set("priority", e.target.value)}
            >
              {["low", "medium", "high", "critical"].map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
            <FieldError messages={fieldErrors.priority} />
          </label>
        </div>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-700">
            business justification{" "}
            {(form.priority === "high" || form.priority === "critical") && (
              <span className="text-rose-600">(required for high/critical)</span>
            )}
          </span>
          <textarea
            className={inputCls("business_justification")}
            rows={2}
            value={form.business_justification}
            onChange={(e) => set("business_justification", e.target.value)}
          />
          <FieldError messages={fieldErrors.business_justification} />
        </label>

        {formErrors.length > 0 && (
          <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800">
            {formErrors.join(" · ")}
          </div>
        )}

        {mutation.isError && !(mutation.error instanceof ApiError && mutation.error.status === 422) && (
          <p className="text-sm text-rose-600">{(mutation.error as Error).message}</p>
        )}

        <button className="btn-primary" type="submit" disabled={mutation.isPending || validating}>
          {validating ? "Validating…" : mutation.isPending ? "Creating…" : "Create draft"}
        </button>
      </form>
    </div>
  );
}
