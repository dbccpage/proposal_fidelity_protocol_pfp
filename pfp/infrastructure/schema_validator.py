"""Schema validation adapter for PFP artifacts, receipts, and packets.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..domain.contracts.schemas import SchemaValidationResult


class PfpSchemaValidatorAdapter:
    """Validates payloads against Draft202012 JSON schemas and closed-object constraints."""

    @staticmethod
    def validate_payload(schema_dict: Dict[str, Any], payload: Dict[str, Any], schema_id: str = "") -> SchemaValidationResult:
        errors: List[str] = []
        try:
            # Core pilot execution does not require the optional schema engine.
            # A missing engine still rejects any requested schema validation.
            import jsonschema

            validator = jsonschema.Draft202012Validator(schema_dict)
            for err in validator.iter_errors(payload):
                errors.append(f"{err.json_path}: {err.message}")
        except Exception as exc:
            errors.append(f"ValidatorException: {str(exc)}")

        return SchemaValidationResult(
            schema_id=schema_id or str(schema_dict.get("$id", "unnamed_schema")),
            is_valid=(len(errors) == 0),
            errors=errors,
            authority_effect="None",
        )
