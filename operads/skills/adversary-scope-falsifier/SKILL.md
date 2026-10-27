---
name: adversary-scope-falsifier
description: "Detect claim scope exceeding declared evidence scope at PRE_SEAL with a finite executable predicate and benign controls."
metadata:
  core-arity: "1"
  core-contract: "operads/catalog/contracts/v1/adversary_scope_falsifier.json"
  core-contracts-digest: "sha256:b001073b031beccde6ad42883e2af5fc4efa04d205c7648b4f029f1c33ce50a3"
  core-generated: "oewas.typed-capability.v1"
  core-kind: "anti_skill"
  core-residual: "unknown"
  core-source-colours: "[\"Contract\"]"
  core-target-colour: "Audit"
---

# adversary-scope-falsifier

Generated from the OEOP typed catalog. Edit the canonical contract and instruction resource.

At PRE_SEAL, compare the typed claim_scope with evidence_scope using the registered
NOT_SUBSET_FIELDS predicate. Emit CLAIM_SCOPE_EXCEEDS_EVIDENCE when a claimed scope
element is absent from the declared evidence. Preserve the subject and emit a finding;
do not repair declarations, infer evidence, grant authority or activate a guard.
Replay positive cases and benign negative controls in both fixture contexts before
using the finite result. Missing or stale implementation and fixture bindings refuse.

Ordered signature: `(subject: Contract) -> findings: Audit`.

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
