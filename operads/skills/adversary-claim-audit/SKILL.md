---
name: adversary-claim-audit
description: "Audit a typed claim against declared evidence scope with a replayed Adversary falsifier before reporting it."
metadata:
  core-arity: "2"
  core-contract: "operads/catalog/contracts/v1/adversary_claim_audit.json"
  core-contracts-digest: "sha256:eeec5a0d727eae41436369698416eabff393a33d0ea7c7eb250036af9296661f"
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

Contracts: `sha256:eeec5a0d727eae41436369698416eabff393a33d0ea7c7eb250036af9296661f`

Spec: `sha256:d1ae2b5b9554ebf2661e07a48fc2c5b336c899252afa5e1b6c21b581d4c67d96`

Fixtures: `sha256:e8e0394005f3ba7f15adacd0e7c5722c54d0a5e45f052d92cb390bb9a526b938`

Evaluation: `sha256:6198500cc6cf81335db9b7b323f9cb9ebd1c53a23076467846598397dd2cf3c7`

Implementation: `sha256:8704bc0c8682ca3873930ca807de8f0c4dcb352c0b0f98d450bd3caee615ac88`

Source admission: `Unadmitted`. AuthorityEffect: None.
The finite detector reports findings. It does not activate a production guard.

From the repository root, run the offline audit with:

```text
python -m operads.infrastructure.typed_contract_compiler --repo-root . --audit-subject <subject.json>
```
