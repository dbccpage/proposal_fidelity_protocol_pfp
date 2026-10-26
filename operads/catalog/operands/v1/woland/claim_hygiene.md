```oewas.operand.v3
operand_id: woland.claim_hygiene.clause
kind: instruction
body: >-
  Separate the requested claim from its evidence and nonclaims. Preserve the
  exact source references. If a required verifier is absent, return an open
  obligation rather than a pass.
dependencies: []
emitted_observations:
  - claim_evidence_separation
```

```oewas.operation.v3
operation_id: woland.claim_hygiene
declaration: Declared
schema_binding: Unbound
executor_binding: Unbound
validation: Unchecked
admission: Unadmitted
authority_effect: None
authority_ceiling: None
residual_status: unknown
inputs:
  - name: source_contract
    colour_id: Contract
    schema_ref: schema:contract:v1
    schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
output:
  name: claim_audit
  colour_id: Audit
  schema_ref: schema:audit:v1
  schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
operand_refs:
  - woland.claim_hygiene.clause
```
