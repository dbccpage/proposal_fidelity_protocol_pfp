```oewas.operand.v3
operand_id: adversary.checker_receipt_required.clause
kind: instruction
body: >-
  1. Never persist `PASS_TO_MASTER` without the checker receipt file that accepted the answer. `persist-run` refuses it with `CHECKER_RECEIPT_REQUIRED`, a receipt it cannot parse with `CHECKER_RECEIPT_MALFORMED`, and a receipt stating the other verdict with `CHECKER_RECEIPT_VERDICT_MISMATCH`.
dependencies: []
emitted_observations:
  - checker_receipt_binding
```

```oewas.operation.v3
operation_id: adversary.checker_receipt_required
declaration: Declared
schema_binding: Unbound
executor_binding: Unbound
validation: Unchecked
admission: Unadmitted
authority_effect: None
authority_ceiling: None
residual_status: unknown
inputs:
  - name: candidate
    colour_id: Code
    schema_ref: schema:code:v1
    schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
  - name: checker_receipt
    colour_id: Receipt
    schema_ref: schema:receipt:v1
    schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
output:
  name: verdict_audit
  colour_id: Audit
  schema_ref: schema:audit:v1
  schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
operand_refs:
  - adversary.checker_receipt_required.clause
```
