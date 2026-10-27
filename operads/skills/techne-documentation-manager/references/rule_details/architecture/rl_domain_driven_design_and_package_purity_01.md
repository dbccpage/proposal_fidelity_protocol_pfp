# Detailed definition: Domain-Driven Design & Package Standards (1)

**AuthorityEffect:** None.

Parent: [Domain-Driven Design & Package Standards](../../../../../rules/architecture/rl_domain_driven_design_and_package_purity.md). Load for the matching predicate, not every task.

# Rule: Domain-Driven Design & Package Purity

**AuthorityEffect:** None.

This rule codifies bounded context standard Domain-Driven Design (DDD) module layouts, strict sub-package partitioning, anti-primitive-obsession, professional DDD entity/aggregate/value-object standards, Proposal Fidelity Protocol (PFP) educational engine architecture, and module-to-package confluence preservation.

For generic swarm runtime decoupling, anti-shim facades, and domain bridges, see [`.agents/rules/architecture/rl_clean_architecture_and_subsystem_governance.md`](../../../../../rules/architecture/rl_clean_architecture_and_subsystem_governance.md).
For operational relocation and antibody lifecycle invariants, see:
- [`.agents/rules/architecture/rl_subsystem_relocation_and_estate_purity.md`](../../../../../rules/architecture/rl_subsystem_relocation_and_estate_purity.md)
- [`.agents/rules/architecture/rl_immune_antibody_and_verification_hygiene.md`](../../../../../rules/architecture/rl_immune_antibody_and_verification_hygiene.md)

---

## Bounded Context DDD & Port Protocol Layout Invariant

> **Standard DDD Domain Layout:**
>
> Every bounded context under `operations/domain/<bounded_context>/` must be structured into standard DDD modules:
>
> 1. `enums.py`: Domain enumerations (`str, Enum`).
> 2. `value_objects.py`: Strongly-typed Value Objects (`@dataclass(frozen=True)`) enforcing exact-type equality via explicit runtime checks (`if type(self) is not type(other): return False`) paired with explicit static narrowing (`if not isinstance(other, <Class>): return False`) to prevent Pitfall 037 (`assert` optimization stripping), and composite `hash((type(self), ...))`.
> 3. `entities.py` / `aggregates.py`: Domain entities and aggregate roots with identity and lifecycle invariants.
> 4. `errors.py`: Typed domain error hierarchy rooted in a BC-specific base exception.
> 5. `protocols.py`: Domain ports and interfaces (`typing.Protocol`) for use-case and infrastructure inversion.
> 6. `constants.py`: Static domain configurations, regexes, and policy matrices.
> 7. `__init__.py`: Clean re-export of all public domain types with explicit `__all__`.
> 8. **Zero Outer Framework Imports:** Domain modules must have zero imports from `use_cases/`, `infrastructure/`, outer frameworks (e.g. `fastapi`, `requests`), or fallback try/except crate shims.

## Domain Package Layout & Anti-Primitive-Obsession Invariant (`RULE_DOMAIN_AGGREGATE_AND_VO_PACKAGING_001`)

> **Strict Domain Sub-Package Partitioning & Typed Port Signatures:**
>
> 1. **Zero Loose Domain Files in Package Roots:** Bounded context `domain/` directories must not leave loose domain entity or type files directly in the `domain/` root. All models must be partitioned into cohesive sub-packages: `aggregates/`, `value_objects/`, `entities/`, `contracts/`, `fixtures/`, etc. Only `__init__.py` may reside directly under `domain/`, acting as a deep interface facade.
> 2. **Anti-Primitive Obsession in Use Cases:** Use case services and application ports (`use_cases/`) must accept and return typed `Aggregate` and `ValueObject` instances directly. Decomposing domain objects into primitive Python dictionaries, strings, or untyped tuples across use-case boundaries is strictly prohibited.
> 3. **Entity & Value Object Contracts:** Value Objects must be immutable (`@dataclass(frozen=True)` or frozen models) with exact-type equality; entities must encapsulate internal state; wire DTOs (`contracts/`) must remain segregated from pure domain entities.
> 4. **AST Conformance:** AST linting suites must verify that `domain/` package roots contain zero standalone `.py` model modules aside from `__init__.py`.

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
> 1. **Zero Ad-Hoc Harness Rebuilding:** Autonomous agents running PFP demos, stage pipelines, or Adversary tribunal gates must invoke the canonical Clean Architecture entrypoints under `education` (`pfp.entrypoints.cli.pfp` or `education.scripts.run_pfp_demos`). Agents must NEVER author throwaway runner scripts in `documentation/` or temporary workspaces.
> 2. **Pure Domain AST Isolation:** `education/domain/` and `pfp/domain/` must maintain zero inward dependency violations, enforced by static AST analysis in `test_pfp_clean_arch.py`.
> 3. **Exact Machine Receipts:** All demo executions, stage pipeline runs, and gate evaluations must emit typed `Receipt` objects bearing `authority_effect: "None"` and exact verification status.

## Module-to-Package Confluence Preservation Invariant (`RULE_MODULE_TO_PACKAGE_CONFLUENCE_001`)

> **Atomic Promotion and Namespace Integrity:**
>
> 1. When promoting a single-file module (`pkg/name.py`) into a package directory (`pkg/name/`):
>    - The existing module code must be relocated to a coherent submodule (e.g. `pkg/name/contracts.py` or `pkg/name/models.py`).
>    - The new package `pkg/name/__init__.py` must re-export all symbols declared in the original module's `__all__`.
>    - All newly grouped submodules in the package must be cleanly imported and declared in `__all__`.
>    - The single-file module `pkg/name.py` and the directory `pkg/name/` must never coexist on disk simultaneously.
