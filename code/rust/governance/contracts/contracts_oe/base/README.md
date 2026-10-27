# Engine Crate Base Contracts

> Core runtime architectural contracts governing components across the engine crates estate.
> Governed by Techne Council. AuthorityEffect: None.

---

## Overview

This directory (`contracts_crates/base/`) houses the baseline operational and constitutional contracts for the primary architectural roles in Engine crates:

| Contract File | Governed Role | Authority Effect | Primary Responsibilities |
|---|---|---|---|
| [`base.contract.yaml`](base.contract.yaml) | `BaseCrateComponent` | None | Common root archetype establishing fail-closed posture and non-roles. |
| [`engine.contract.yaml`](engine.contract.yaml) | `Engine` | StateTransition | Commits durable state transitions strictly gated by verified `ActionLicense`. |
| [`kernel.contract.yaml`](kernel.contract.yaml) | `SemanticKernelManifest` | None | Declares bounded authority and input/output families for a semantic class. |
| [`pipeline.contract.yaml`](pipeline.contract.yaml) | `Pipeline` | None | Deterministic stage execution and typed refusal forwarding. |
| [`policy.contract.yaml`](policy.contract.yaml) | `Policy` | None | Evaluates invariant conformance and decisions without side-effects. |
| [`solver.contract.yaml`](solver.contract.yaml) | `Solver` | None | Executes deterministic search and exact rational constraint satisfaction. |
| [`validator.contract.yaml`](validator.contract.yaml) | `Validator` | None | Independent receipt verification and structural shape validation. |
| [`packet.contract.yaml`](packet.contract.yaml) | `Packet` | None | Sealed carrier envelope with hash commitments and ancestry links. |
| [`runtime.contract.yaml`](runtime.contract.yaml) | `Runtime` | None | Execution context and resource boundary enforcement. |
| [`trace_artifact.contract.yaml`](trace_artifact.contract.yaml) | `TraceArtifact` | None | Append-only execution trace ledger records. |

---

## Architectural Distinctions: Three "Base" Concepts

To prevent ambiguity, note the three different "base" locations in the contract estate:

1. **System Constitutional Base (`contracts_base/`):**
   Located at [`governance/contracts/contracts_base/`](../../contracts_base/), this contains the root constitutional contracts for the entire system:
   - `base_contract.v1.contract.yaml`: The root `core.contract.v1` abstract contract.
   - `base_math_contract.contract.yaml`: The root mathematical kernel contract.
   - `base_evidence_contract.contract.yaml`, `base_os_contract.contract.yaml`, etc.

2. **Crate Component Base (`contracts_crates/base/`):**
   *This directory*. Holds concrete runtime contracts defining how Rust and Python engine crates instantiate kernels, pipelines, engines, and validators, deriving from `base.contract.yaml`.

3. **Math Contract Template (`contracts_crates/mathematics/`):**
   Located at [`contracts_crates/mathematics/`](../mathematics/), this contains:
   - [`math_contract.template.yaml`](../mathematics/math_contract.template.yaml): The copy-pasteable template for new pure mathematical objects.
   - [`template_usage_guide.md`](../mathematics/template_usage_guide.md): The authoring and validation guide.
