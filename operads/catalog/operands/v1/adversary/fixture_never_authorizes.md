```oewas.operand.v3
operand_id: adversary.fixture_never_authorizes.clause
kind: instruction
body: >-
  3. Ablation runs are experiment arms. They report `ABLATED_WOULD_AUTHORIZE` at most and never authorize. Fixture runs (canned seats) report `FIXTURE_ONLY` at most.
dependencies: []
emitted_observations:
  - experiment_arm_authority_ceiling
```

```oewas.operation.v3
operation_id: adversary.fixture_never_authorizes
declaration: Declared
schema_binding: Unbound
executor_binding: Unbound
validation: Unchecked
admission: Unadmitted
authority_effect: None
authority_ceiling: None
residual_status: unknown
inputs:
  - name: bout_receipt
    colour_id: Receipt
    schema_ref: schema:receipt:v1
    schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
output:
  name: authority_audit
  colour_id: Audit
  schema_ref: schema:audit:v1
  schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
operand_refs:
  - adversary.fixture_never_authorizes.clause
```
