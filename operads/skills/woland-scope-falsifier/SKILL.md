---
name: woland-scope-falsifier
description: "Detect claim scope exceeding declared evidence scope at PRE_SEAL with a finite executable predicate and benign controls."
metadata:
  omega-arity: "1"
  omega-contract: "omega_engine_operads/catalog/contracts/v1/woland_scope_falsifier.json"
  omega-contracts-digest: "sha256:eeec5a0d727eae41436369698416eabff393a33d0ea7c7eb250036af9296661f"
  omega-generated: "oewas.typed-capability.v1"
  omega-kind: "anti_skill"
  omega-residual: "unknown"
  omega-source-colours: "[\"Contract\"]"
  omega-target-colour: "Audit"
---

# woland-scope-falsifier

Generated from the OEOP typed catalog. Edit the canonical contract and instruction resource.

At PRE_SEAL, compare the typed claim_scope with evidence_scope using the registered
NOT_SUBSET_FIELDS predicate. Emit CLAIM_SCOPE_EXCEEDS_EVIDENCE when a claimed scope
element is absent from the declared evidence. Preserve the subject and emit a finding;
do not repair declarations, infer evidence, grant authority or activate a guard.
Replay positive cases and benign negative controls in both fixture contexts before
using the finite result. Missing or stale implementation and fixture bindings refuse.

Ordered signature: `(subject: Contract) -> findings: Audit`.

## Evidence and execution boundary

Contracts: `sha256:eeec5a0d727eae41436369698416eabff393a33d0ea7c7eb250036af9296661f`

Spec: `sha256:d1ae2b5b9554ebf2661e07a48fc2c5b336c899252afa5e1b6c21b581d4c67d96`

Fixtures: `sha256:e8e0394005f3ba7f15adacd0e7c5722c54d0a5e45f052d92cb390bb9a526b938`

Evaluation: `sha256:6198500cc6cf81335db9b7b323f9cb9ebd1c53a23076467846598397dd2cf3c7`

Implementation: `sha256:8704bc0c8682ca3873930ca807de8f0c4dcb352c0b0f98d450bd3caee615ac88`

Source admission: `Unadmitted`. AuthorityEffect: None.
The finite detector reports findings. It does not activate a production guard.

From the repository root, run the offline audit with:

```text
python -m omega_engine_operads.infrastructure.typed_contract_compiler --repo-root . --audit-subject <subject.json>
```
