```oewas.operand.v3
operand_id: woland.critic_json_only.clause
kind: instruction
body: >-
  2. A critic blocks a candidate only through its fenced `critique` JSON block (`{"blocking": true|false, "counterexample": ...}`). Prose words such as "defect" or "flaw" decide nothing; a reply without a well-typed block is `MALFORMED` and blocks its candidate.
dependencies: []
emitted_observations:
  - critique_evidence_shape
```

```oewas.operation.v3
operation_id: woland.critic_json_only
declaration: Declared
schema_binding: Unbound
executor_binding: Unbound
validation: Unchecked
admission: Unadmitted
authority_effect: None
authority_ceiling: None
residual_status: unknown
inputs:
  - name: critique_contract
    colour_id: Contract
    schema_ref: schema:contract:v1
    schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
  - name: critique_receipt
    colour_id: Receipt
    schema_ref: schema:receipt:v1
    schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
output:
  name: critique_audit
  colour_id: Audit
  schema_ref: schema:audit:v1
  schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
operand_refs:
  - woland.critic_json_only.clause
```
