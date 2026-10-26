# Detailed definition: Clean Architecture & Subsystem Governance (1)

**AuthorityEffect:** None.

Parent: [Clean Architecture & Subsystem Governance](../../../../../rules/architecture/rl_clean_architecture_and_subsystem_governance.md). Load for the matching predicate, not every task.

# Rule: Clean Architecture, Bounded Contexts & Swarm Decoupling

**AuthorityEffect:** None.

This rule codifies pure generic runtime engine decoupling (omega_engine_woland.stage), Woland base swarm specialization, zero-facade direct canonical imports, domain bridge isolation, bounded context standard DDD module layouts, and pure domain sink decoupling.

Detailed operational, relocation, and antibody lifecycle invariants have been factored into modular sub-rules:
- [`.agents/rules/architecture/rl_subsystem_relocation_and_estate_purity.md`](../../../../../rules/architecture/rl_subsystem_relocation_and_estate_purity.md): Bounded context gate and registry relocation closure, documentation `_docs/` isolation, curriculum storage encapsulation, and shadow prototype retirement.
- [`.agents/rules/architecture/rl_immune_antibody_and_verification_hygiene.md`](../../../../../rules/architecture/rl_immune_antibody_and_verification_hygiene.md): Learned failure detector and antibody carrier honesty, catalog atomicity, semantic field filter discipline, and governance skill self-verification script standards.

---

## Swarm Decoupling & Pure Generic Runtime Invariant

> **Base Engine Generality:**
>
> 1. `omega_engine_woland.stage` is a pure generic base framework containing generic scheduling, typed sink protocols (`UtsSink`, `UnsSink`, `DdaSink`, `SgtSink`, `CemeterySink`, `AntibodySink`, `GenealogySink`), and telemetry. It must NEVER contain character lore, dramatic novella rendering, or domain-specific dialectic branching.
> 2. Specific swarms (such as the 7-Act Master & Margarita dialectic) must be isolated in dedicated bounded contexts (e.g. `omega_engine_woland`) with standard Clean Architecture layer boundaries.
> 3. Bounded run executions must emit the five current Woland bundle files (`receipt.json`, `uns.md`, `ddc.jsonl`, `summary.json`, `uts.jsonl`) plus the `mam/` story folder (`mam.md`, `mam.tex`, `mam.pdf`) into isolated run folders under `_ic/<agency>/<swarm>/runs/<task_key>/` (e.g. `_ic/darpa/woland/runs/<task_key>/`). Writers never emit the retired tape copy `dda_actions.jsonl`; readers still accept it in older run folders. Skill-run receipts keep their own older layout.
> 4. **Canonical Stage Dispatch from Tool CLIs**: Tool CLIs and standalone examiners must not create disconnected execution lifecycles or standalone success loops. CLI entry points must dispatch through canonical Woland stage runtime ports (e.g. `WolandSwarmService`), pass local examination findings and minted antibodies in `carrier_context`, map unavailable execution or runtime failures to typed refusals (`EXECUTION_UNAVAILABLE`), and preserve the stage run identity (`receipt_id`) in emitted output.

## Woland Base Swarm Specialization Invariant

> **Swarm Inheritance and Composition Contract:**
>
> 1. **Base Swarm Gateway:** All domain, research, governance, software development, cognitive operations, and developer swarms must subclass `OmegaEngineWolandSwarm` or hold one through `bind_woland`, and declare a `SwarmSpecializationV1` per [`../swarms/rl_woland_base_swarm_specialization.md`](../../../../../rules/swarms/rl_woland_base_swarm_specialization.md).
> 2. **Pure Domain Sink Decoupling:** Domain modules requiring artifact sinks must depend exclusively on abstract domain protocols (`RunArtifactSinkPort`), with concrete implementations injected into domain constructors. Dynamic `importlib` evasion in domain ports is strictly prohibited.

## Zero-Facade & Direct Canonical Import Invariant (`RULE_CLEAN_ARCH_NO_SHIMS_001`)

> **Anti-Shim Clean Architecture Discipline:**
>
> 1. **No Re-Export Shims or Compatibility Facades:** When refactoring or modularizing code into Clean Architecture layers or vertical slices, never retain re-export shims, facade aliases in `domain/__init__.py`, or compatibility facade modules to fake backward compatibility. All call sites, tests, and consumers must import directly from their canonical Clean Architecture layers. Files containing docstrings or comments such as `Canonical forwarder to` or `forwarder stub` are strictly forbidden across all domain roots.
> 2. **Pure Domain Protocol Injection:** Use cases must never instantiate concrete infrastructure classes as inline fallback defaults (e.g. `from infrastructure... import ConcreteService`). Use cases must depend exclusively on Domain Protocols (`ports.py` or `domain/shared_kernel/`) and accept injected implementations defaulting to Null Object patterns (e.g. `NullIntelligenceEmitter`).

## No Duplicate Module Shadowing Invariant (`RULE_NO_DUPLICATE_MODULES_001`)

> **Nested Directory Module Purity:**
>
> 1. **No Shadow Duplicates Across Nested Folders:** No module filename may be duplicated across parent and child directories within the same bounded domain tree (e.g. `domain/foo.py` and `domain/sub/foo.py`).
> 2. **Module-to-Package Separation:** A module file `pkg/name.py` and directory `pkg/name/` must never coexist on disk simultaneously (`RULE_MODULE_TO_PACKAGE_CONFLUENCE_001`).

## Domain Bridge Cross-Context Isolation Invariant

> **Resilient Cross-Context Seam Protocol:**
>
> 1. **Collection-Time Fault Isolation**: Domain bridge modules (`domain/bridge/`) that interface with sister bounded contexts (e.g. `omega_engine_woland.stage`) must never cause unhandled import exceptions that break test collection across the host bounded context.
> 2. **Null-Object & Protocol Fallbacks**: When optional sister packages or external runtime engines are not installed or undergoing refactoring, domain bridges must provide typed Domain Protocol implementations or Null-Object fallbacks rather than unhandled top-level import crashes.

## Bounded Context DDD & Port Protocol Layout Invariant

> **Standard DDD Domain Layout:**
>
> Every bounded context under `omega_engine_operations/domain/<bounded_context>/` must be structured into standard DDD modules:
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
