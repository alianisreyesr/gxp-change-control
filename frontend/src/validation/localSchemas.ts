/**
 * Local JSON Schema fallbacks (Draft 2020-12 aligned).
 */

export type JsonSchema = Record<string, unknown>;

export const changeCreateSchema: JsonSchema = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  $id: "change-create-local",
  title: "ChangeCreate",
  type: "object",
  additionalProperties: false,
  properties: {
    title: { type: "string", minLength: 5, maxLength: 200 },
    description: { type: "string", minLength: 20, maxLength: 4000 },
    system_name: { type: "string", minLength: 2, maxLength: 200 },
    change_type: {
      type: "string",
      enum: ["configuration", "code", "process", "infrastructure", "documentation"],
    },
    priority: {
      type: "string",
      enum: ["low", "medium", "high", "critical"],
      default: "medium",
    },
    requester: { type: "string", minLength: 2, maxLength: 80 },
    business_justification: {
      anyOf: [{ type: "string", maxLength: 2000 }, { type: "null" }],
    },
    target_implementation_date: {
      anyOf: [
        { type: "string", format: "date", minLength: 10, maxLength: 10 },
        { type: "null" },
      ],
      description: "YYYY-MM-DD; not in the past (enforced server-side and client extra check)",
    },
  },
  required: ["title", "description", "system_name", "change_type", "requester"],
  allOf: [
    {
      if: {
        properties: { priority: { enum: ["high", "critical"] } },
        required: ["priority"],
      },
      then: {
        properties: {
          business_justification: { type: "string", minLength: 15, maxLength: 2000 },
        },
        required: ["business_justification"],
      },
    },
    {
      // Mirrors ChangeCreate.title_not_placeholder (app/models.py): the server
      // rejects placeholder-looking titles even when the schema-level minLength
      // is satisfied, so surface that here too instead of only via a 422.
      not: {
        properties: {
          title: {
            enum: ["test", "Test", "TEST", "asdf", "xxx", "tbd", "TBD", "n/a", "N/A", "todo", "TODO"],
          },
        },
      },
    },
  ],
};

export const impactAssessmentInSchema: JsonSchema = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  $id: "impact-assessment-in-local",
  title: "ImpactAssessmentIn",
  type: "object",
  additionalProperties: false,
  properties: {
    affects_validated_state: { type: "boolean", default: false },
    affects_part11_controls: { type: "boolean", default: false },
    affects_data_integrity: { type: "boolean", default: false },
    affects_training: { type: "boolean", default: false },
    affects_sops: { type: "boolean", default: false },
    risk_summary: { type: "string", minLength: 20, maxLength: 4000 },
    residual_risk: { type: "string", enum: ["low", "medium", "high"], default: "low" },
    assessor: { type: "string", minLength: 2, maxLength: 80 },
  },
  required: ["risk_summary", "assessor"],
  allOf: [
    {
      if: {
        properties: { residual_risk: { const: "high" } },
        required: ["residual_risk"],
      },
      then: {
        properties: {
          risk_summary: { type: "string", minLength: 40, maxLength: 4000 },
        },
      },
    },
  ],
};

export const approvalInSchema: JsonSchema = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  $id: "approval-in-local",
  title: "ApprovalIn",
  type: "object",
  additionalProperties: false,
  properties: {
    role: { type: "string", minLength: 2, maxLength: 80 },
    decision: { type: "string", enum: ["approve", "reject", "request_info"] },
    comment: {
      anyOf: [{ type: "string", maxLength: 2000 }, { type: "null" }],
    },
    actor: { type: "string", minLength: 2, maxLength: 80 },
  },
  required: ["role", "decision", "actor"],
  allOf: [
    {
      if: {
        properties: { decision: { enum: ["reject", "request_info"] } },
        required: ["decision"],
      },
      then: {
        properties: {
          comment: { type: "string", minLength: 10, maxLength: 2000 },
        },
        required: ["comment"],
      },
    },
  ],
};

export const LOCAL_SCHEMAS: Record<string, JsonSchema> = {
  "change-create": changeCreateSchema,
  "impact-assessment-in": impactAssessmentInSchema,
  "approval-in": approvalInSchema,
};
