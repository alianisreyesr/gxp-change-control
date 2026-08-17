import { useCallback, useState } from "react";
import {
  applyActorPolicy,
  applyActorPolicyOnErrors,
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
        } else {
          result = {
            ...result,
            fieldErrors: applyActorPolicyOnErrors(data, result.fieldErrors),
          };
          // if actor policy added errors, ok stays false
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
