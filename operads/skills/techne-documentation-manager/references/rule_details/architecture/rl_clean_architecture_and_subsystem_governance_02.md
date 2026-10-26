# Detailed definition: Clean Architecture & Subsystem Governance (2)

**AuthorityEffect:** None.

Parent: [Clean Architecture & Subsystem Governance](../../../../../rules/architecture/rl_clean_architecture_and_subsystem_governance.md). Load for the matching predicate, not every task.

## Professional Domain-Driven Design (DDD) Architecture Invariant (`RULE_DDD_PROFESSIONAL_STANDARDS_001`)

> **Genuine DDD Abstractions Over Shallow Taxonomies:**
>
> 1. **Prohibition of Shallow Taxonomies:** Creating folder structures (`aggregates/`, `entities/`, `value_objects/`) that hold raw dictionaries, loose strings, or unencapsulated data containers without genuine domain invariants is strictly forbidden.
> 2. **Base Entity & Identity:** Domain entities must inherit from an explicit `Entity` base class where equality and hashing are strictly defined by identity and exact type (`(type(self), self.id)`). Entities must encapsulate internal state and validate structural invariants at initialization.
> 3. **Value Object Discipline:** Value Objects must be immutable (`@dataclass(frozen=True)` or frozen Pydantic), possess zero identity, enforce exact-type equality (`type(self) is type(other)`), and validate domain bounds in `__post_init__`. Floating-point representations in discrete/exact domains are strictly prohibited.
> 4. **Aggregate Root Authority:** Aggregate roots must encapsulate all child entities and value objects (not bare unlinked IDs). Aggregate roots are the sole consistency boundary: all state transitions and cross-entity invariant verifications (such as cryptographic digest chains `INV_*`) must execute through aggregate methods returning fail-closed ROP `Result[T, DomainError]` monads.
> 5. **Interface & Wire DTO Segregation:** Wire serialization models (e.g. Pydantic v2 `BaseModel` with `strict=True`) reside at the interface/wire boundary (`contracts/`, `homology/`, `infrastructure/`), segregated from pure domain entities. Bidirectional mapping between wire DTOs and domain entities must be explicitly implemented via `to_domain()` and `from_domain()`.
> 6. **Zero Host I/O in Domain:** Domain layers must have zero imports of `subprocess`, OS handles, or unmanaged filesystem/network I/O (`AP_PY_008`).

## Proposal Fidelity Protocol (PFP) Educational Engine Invariant

> **Canonical PFP Application Architecture:**
>
> 1. **Zero Ad-Hoc Harness Rebuilding:** Autonomous agents running PFP demos, stage pipelines, or Woland tribunal gates must invoke the canonical Clean Architecture entrypoints under `omega_engine_education` (`omega_engine_pfp.entrypoints.cli.pfp` or `omega_engine_education.scripts.run_pfp_demos`). Agents must NEVER author throwaway runner scripts in `documentation/` or temporary workspaces.
> 2. **Pure Domain AST Isolation:** `omega_engine_education/domain/` and `omega_engine_pfp/domain/` must maintain zero inward dependency violations, enforced by static AST analysis in `test_pfp_clean_arch.py`.
> 3. **Exact Machine Receipts:** All demo executions, stage pipeline runs, and gate evaluations must emit typed `Receipt` objects bearing `authority_effect: "None"` and exact verification status.

## Module-to-Package Confluence Preservation Invariant (`RULE_MODULE_TO_PACKAGE_CONFLUENCE_001`)

> **Atomic Promotion and Namespace Integrity:**
>
> 1. When promoting a single-file module (`pkg/name.py`) into a package directory (`pkg/name/`):
>    - The existing module code must be relocated to a coherent submodule (e.g. `pkg/name/contracts.py` or `pkg/name/models.py`).
>    - The new package `pkg/name/__init__.py` must re-export all symbols declared in the original module's `__all__`.
>    - All newly grouped submodules in the package must be cleanly imported and declared in `__all__`.
>    - The single-file module `pkg/name.py` and the directory `pkg/name/` must never coexist on disk simultaneously.
