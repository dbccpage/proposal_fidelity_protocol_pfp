---
name: governance-clean-arch
description: "Clean Architecture gate. Enforces inward dependency discipline, pure domain sinks, single-root bounded contexts, and zero-facade imports."
operad_source_colours: ["Code"]
operad_target_colour: "Audit"
operad_arity: 1
operad_residual: "unknown"
families: [governance, clean-architecture, architecture]
---

# governance-clean-arch

AuthorityEffect: None.

Absorbed entrypoint: `clean-arch-inward-audit`.

## Gate

`bounded_contexts.yaml` names `outer_layers`. Every Python package directory named `domain` must not import those layers. A context with `single_root_enforced: true` has one directory root per layer.

A permitted edge in the operations office scanner is an `ArchitectureConfig.dependency_exceptions` record with an owner and a rationale (`operads/domain/python_development_office/architecture_config.py`).

## Check

From the repository root:

```bash
python operads/skills/governance-clean-arch/scripts/check_inward_dependencies.py
python operads/skills/governance-clean-arch/scripts/check_clean_arch.py
```

The first command checks every `domain` package. The second checks the single-root roster, then runs the operations office scanner on `operations`.

## Owned elsewhere

- `operads/rules/architecture/rl_clean_architecture_and_subsystem_governance.md` owns `RULE_CLEAN_ARCH_NO_SHIMS_001`, domain bridges, and duplicate modules.
- `operads/rules/architecture/rl_domain_driven_design_and_package_purity.md` owns the domain module layout.
- `operads/rules/engineering/rl_subsystem_retirement_and_adapter_invariants.md` owns legacy tree retirement.
- `operads/rules/architecture/rl_subsystem_relocation_and_estate_purity.md` owns `RULE_SHADOW_PROTOTYPE_RETIREMENT_001`.
- `operads/rules/engineering/rl_rust_engineering_standards.md` owns `RULE_RUST_CRATES_RS_EXCLUSIVE_001`.
