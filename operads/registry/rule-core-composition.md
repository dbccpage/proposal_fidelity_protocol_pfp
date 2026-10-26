# Core composition rules

- `AGT-CORE-0001` -- `LocalGreen` never implies `GlobalGreen`.
- `AGT-CORE-0002` -- A global-green verdict is a distinct host-verified record,
  not a model assertion or aggregate of local passes.
- `AGT-CORE-0003` -- Proposal, deterministic validation, independent evaluation,
  independent witness, receipt-DAG verification, seam/global checks, and the
  global-boundary check remain separate activities.
- `AGT-CORE-0004` -- The same host-observed invocation identity cannot satisfy
  any two of producer, evaluator, and witness roles (producer != evaluator,
  evaluator != witness, and producer != witness).

