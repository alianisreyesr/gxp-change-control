import Ajv2020, { type ErrorObject, type ValidateFunction } from "ajv/dist/2020";
import addFormats from "ajv-formats";
import { LOCAL_SCHEMAS, type JsonSchema } from "./localSchemas";

const BASE = import.meta.env.VITE_API_URL ?? "/api";

const ajv = new Ajv2020({
  allErrors: true,
  strict: false, // allow x-* extensions and OpenAPI-ish keywords from Pydantic export
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
    const msg = err.message ?? err.keyword;
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
    // fall through to local
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

/** Normalize payload before Ajv (empty justification → omit for optional). */
export function prepareChangeCreatePayload(form: {
  title: string;
  description: string;
  system_name: string;
  change_type: string;
  priority: string;
  requester: string;
  business_justification: string;
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
  return payload;
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

/** Extra client rules that mirror Pydantic actor policy (not pure JSON Schema). */
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

export function applyActorPolicy(
  result: ValidationResult,
  actorFields: string[] = ["requester", "assessor", "actor"]
): ValidationResult {
  if (!result.ok) {
    // still check actors on the attempted data is not available — only post-ok path needs merge
    return result;
  }
  const fieldErrors: FieldErrors = {};
  for (const f of actorFields) {
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
  fieldErrors: FieldErrors,
  actorFields: string[] = ["requester", "assessor", "actor"]
): FieldErrors {
  const next = { ...fieldErrors };
  for (const f of actorFields) {
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
