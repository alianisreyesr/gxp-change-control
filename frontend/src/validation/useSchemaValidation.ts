import { useCallback, useState } from "react";
import {
  applyActorPolicy,
  applyActorPolicyOnErrors,
  applyDatePolicyOnErrors,
  applyResidualRiskPolicyOnErrors,
  assertResidualRiskConsistency,
  validateWithSchema,
  type FieldErrors,
  type ValidationResult,
} from "./ajvClient";

export function useSchemaValidation(schemaName: string) {
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [formErrors, setFormErrors] = useState<string[]>([]);
  const [validating, setValidating] = useState(false);

  const clearErrors = useCallback(() => {
    setFieldErrors({});
    setFormErrors([]);
  }, []);

  const validate = useCallback(
    async (data: Record<string, unknown>): Promise<ValidationResult> => {
      setValidating(true);
      try {
        let result = await validateWithSchema(schemaName, data);
        if (result.ok) {
          result = applyActorPolicy(result);
          if (result.ok) {
            const dateErrors = applyDatePolicyOnErrors(result.data, {});
            const riskMsg = assertResidualRiskConsistency(result.data);
            if (riskMsg) dateErrors.risk_summary = [...(dateErrors.risk_summary ?? []), riskMsg];
            if (Object.keys(dateErrors).length) {
              result = { ok: false, fieldErrors: dateErrors, formErrors: [] };
            }
          }
        } else {
          let fe = applyActorPolicyOnErrors(data, result.fieldErrors);
          fe = applyDatePolicyOnErrors(data, fe);
          fe = applyResidualRiskPolicyOnErrors(data, fe);
          result = { ...result, fieldErrors: fe };
        }
        if (result.ok) {
          setFieldErrors({});
          setFormErrors([]);
        } else {
          setFieldErrors(result.fieldErrors);
          setFormErrors(result.formErrors);
        }
        return result;
      } finally {
        setValidating(false);
      }
    },
    [schemaName]
  );

  return { validate, fieldErrors, formErrors, validating, clearErrors, setFieldErrors };
}
