---
name: adversary-claim-audit
description: "Audit a typed claim against declared evidence scope with a replayed Adversary falsifier before reporting it."
metadata:
  core-arity: "2"
  core-contract: "operads/catalog/contracts/v1/adversary_claim_audit.json"
  core-contracts-digest: "sha256:b001073b031beccde6ad42883e2af5fc4efa04d205c7648b4f029f1c33ce50a3"
  core-generated: "oewas.typed-capability.v1"
  core-kind: "skill"
  core-residual: "unknown"
  core-source-colours: "[\"Audit\", \"Contract\"]"
  core-target-colour: "Receipt"
---

# adversary-claim-audit

Generated from the OEOP typed catalog. Edit the canonical contract and instruction resource.

Review one typed claim subject with the scope falsifier before reporting its audit.
Read claim_scope and evidence_scope from the supplied subject, without inferring
additional evidence from prose or a catalog entry. Report the exact subject ID,
contract binding, fixture evaluation and observed hits in the audit receipt.
A clean scope comparison says only that the declared claim scope is contained in
the declared evidence scope. It does not establish that either declaration is true.
Keep production guard activation at HOLD. Independently signed instruction
consumption remains separate from detector admission and execution permission.

Ordered signature: `(findings: Audit, subject: Contract) -> receipt: Receipt`.

## Evidence and execution boundary

Contracts: `sha256:b001073b031beccde6ad42883e2af5fc4efa04d205c7648b4f029f1c33ce50a3`

Spec: `sha256:ba117ed5180c684520793d18bdc614b102fc6eda2eb8e90d9e6e951ce0f94912`

Fixtures: `sha256:ebdb995f74c857976e38a4b2875c6d5eab2275fe5f6cf9edd4ec9d23e00ffcd7`

Evaluation: `sha256:0443eeb19eaf5a86bb7a408faeba45f2f259762a1de538a42d992d794680313f`

Implementation: `sha256:7f2c2d4117a895d97e54151782589e94a73b1748f5fdca2e2ed29bb2be8cdfcc`

Source admission: `Unadmitted`. AuthorityEffect: None.
The finite detector reports findings. It does not activate a production guard.

From the repository root, run the offline audit with:

```text
python -m operads.infrastructure.typed_contract_compiler --repo-root . --audit-subject <subject.json>
```
