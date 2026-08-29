import Ajv2020, { type ErrorObject, type ValidateFunction } from "ajv/dist/2020";
import addFormats from "ajv-formats";
import { LOCAL_SCHEMAS, type JsonSchema } from "./localSchemas";

const BASE = import.meta.env.VITE_API_URL ?? "/api";

const ajv = new Ajv2020({
  allErrors: true,
  strict: false,
  validateFormats: true,
});
addFormats(ajv);

const compilerCache = new Map<string, ValidateFunction>();
const schemaCache = new Map<string, JsonSchema>();

export type FieldErrors = Record<string, string[]>;

export type ValidationResult =
  | { ok: true; data: Record<string, unknown> }
  | { ok: false; fieldErrors: FieldErrors; formErrors: string[] };

function pathToField(instancePath: string, missingProperty?: string): string {
  if (missingProperty) return missingProperty;
  if (!instancePath || instancePath === "") return "_form";
  return instancePath.replace(/^\//, "").replace(/\//g, ".");
}

export function errorsToFieldMap(errors: ErrorObject[] | null | undefined): {
  fieldErrors: FieldErrors;
  formErrors: string[];
} {
  const fieldErrors: FieldErrors = {};
  const formErrors: string[] = [];
  if (!errors?.length) return { fieldErrors, formErrors };

  for (const err of errors) {
    const field = pathToField(err.instancePath, err.params?.missingProperty as string | undefined);
    let msg = err.message ?? err.keyword;
    if (err.keyword === "format" && err.params?.format === "date") {
      msg = "must be a valid calendar date (YYYY-MM-DD)";
    }
    if (err.keyword === "format" && err.params?.format === "date-time") {
      msg = "must be ISO 8601 date-time with timezone (e.g. 2026-08-17T12:00:00Z)";
    }
    if (field === "_form") {
      formErrors.push(msg);
    } else {
      if (!fieldErrors[field]) fieldErrors[field] = [];
      fieldErrors[field].push(msg);
    }
  }
  return { fieldErrors, formErrors };
}

async function loadSchema(name: string): Promise<JsonSchema> {
  if (schemaCache.has(name)) return schemaCache.get(name)!;

  try {
    const res = await fetch(`${BASE}/schemas/${name}`);
    if (res.ok) {
      const schema = (await res.json()) as JsonSchema;
      schemaCache.set(name, schema);
      return schema;
    }
  } catch {
    // fall through
  }

  const local = LOCAL_SCHEMAS[name];
  if (!local) throw new Error(`No JSON Schema available for '${name}'`);
  schemaCache.set(name, local);
  return local;
}

async function getValidator(name: string): Promise<ValidateFunction> {
  if (compilerCache.has(name)) return compilerCache.get(name)!;
  const schema = await loadSchema(name);
  const validate = ajv.compile(schema);
  compilerCache.set(name, validate);
  return validate;
}

export function prepareChangeCreatePayload(form: {
  title: string;
  description: string;
  system_name: string;
  change_type: string;
  priority: string;
  requester: string;
  business_justification: string;
  target_implementation_date: string;
}): Record<string, unknown> {
  const payload: Record<string, unknown> = {
    title: form.title.trim(),
    description: form.description.trim(),
    system_name: form.system_name.trim(),
    change_type: form.change_type,
    priority: form.priority,
    requester: form.requester.trim(),
  };
  const j = form.business_justification.trim();
  if (j) payload.business_justification = j;
  const d = form.target_implementation_date.trim();
  if (d) payload.target_implementation_date = d;
  return payload;
}

/** Client mirror of server "not in the past" rule (UTC date). */
export function assertTargetDateNotPast(isoDate: string): string | null {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(isoDate)) return null; // let Ajv format handle shape
  const today = new Date().toISOString().slice(0, 10);
  if (isoDate < today) {
    return `target_implementation_date ${isoDate} is in the past (today UTC ${today})`;
  }
  return null;
}

export async function validateWithSchema(
  schemaName: string,
  data: Record<string, unknown>
): Promise<ValidationResult> {
  const validate = await getValidator(schemaName);
  const ok = validate(data);
  if (ok) return { ok: true, data };
  const { fieldErrors, formErrors } = errorsToFieldMap(validate.errors);
  return { ok: false, fieldErrors, formErrors };
}

const FORBIDDEN_ACTORS = new Set([
  "admin",
  "administrator",
  "user",
  "test",
  "guest",
  "root",
  "system",
  "shared",
  "qa",
  "it",
]);

export function applyActorPolicy(result: ValidationResult): ValidationResult {
  if (!result.ok) return result;
  const fieldErrors: FieldErrors = {};
  for (const f of ["requester", "assessor", "actor"]) {
    const v = result.data[f];
    if (typeof v === "string" && FORBIDDEN_ACTORS.has(v.toLowerCase())) {
      fieldErrors[f] = [
        `'${v}' is not allowed as an attributable actor; use a unique person id (e.g. a.reyes)`,
      ];
    }
  }
  if (Object.keys(fieldErrors).length) {
    return { ok: false, fieldErrors, formErrors: [] };
  }
  return result;
}

export function applyActorPolicyOnErrors(
  data: Record<string, unknown>,
  fieldErrors: FieldErrors
): FieldErrors {
  const next = { ...fieldErrors };
  for (const f of ["requester", "assessor", "actor"]) {
    const v = data[f];
    if (typeof v === "string" && FORBIDDEN_ACTORS.has(v.toLowerCase())) {
      next[f] = [
        ...(next[f] ?? []),
        `'${v}' is not allowed as an attributable actor; use a unique person id (e.g. a.reyes)`,
      ];
    }
  }
  return next;
}

export function applyDatePolicyOnErrors(
  data: Record<string, unknown>,
  fieldErrors: FieldErrors
): FieldErrors {
  const next = { ...fieldErrors };
  const t = data.target_implementation_date;
  if (typeof t === "string" && t) {
    const msg = assertTargetDateNotPast(t);
    if (msg) next.target_implementation_date = [...(next.target_implementation_date ?? []), msg];
  }
  return next;
}

const IMPACT_FLAG_FIELDS = [
  "affects_validated_state",
  "affects_part11_controls",
  "affects_data_integrity",
  "affects_training",
  "affects_sops",
] as const;

/**
 * Client mirror of ImpactAssessmentIn.residual_risk_consistency (app/models.py):
 * when three or more impact flags are true, residual_risk="low" requires a
 * risk_summary of at least 60 characters. The JSON Schema alone can't express
 * "count of true booleans", so this is applied the same way as the actor and
 * date policies above.
 */
export function assertResidualRiskConsistency(
  data: Record<string, unknown>
): string | null {
  const residualRisk = data.residual_risk;
  const riskSummary = data.risk_summary;
  if (residualRisk !== "low" || typeof riskSummary !== "string") return null;
  const hitCount = IMPACT_FLAG_FIELDS.filter((f) => data[f] === true).length;
  if (hitCount >= 3 && riskSummary.trim().length < 60) {
    return (
      "when three or more impact flags are true, residual_risk=low requires " +
      "a detailed risk_summary (min 60 chars) explaining why residual risk remains low"
    );
  }
  return null;
}

export function applyResidualRiskPolicyOnErrors(
  data: Record<string, unknown>,
  fieldErrors: FieldErrors
): FieldErrors {
  const next = { ...fieldErrors };
  const msg = assertResidualRiskConsistency(data);
  if (msg) next.risk_summary = [...(next.risk_summary ?? []), msg];
  return next;
}
