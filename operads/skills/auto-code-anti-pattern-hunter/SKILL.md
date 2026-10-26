---
name: auto-code-anti-pattern-hunter
description: "Detect anti-patterns and confirm healthy patterns across Python, Rust, SQL and Lean 4 code."
invocation: entry
operad_source_colours: ["Code", "State"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
families: [meta, techne, quality]
---

# Auto Code Anti-Pattern Hunter

**Status:** canonical-candidate  
**AuthorityEffect:** None

Autonomous orchestrator for detecting anti-patterns across multiple language ecosystems and certifying dual healthy pattern adherence.

## Operadic Foundation & Dual Pattern Architecture

Anti-patterns and healthy patterns are tracked as **colored operads** within [`.agents/patterns/`](../../patterns/README.md).

For every language family, an anti-pattern acts as a defect-witnessing anti-morphism:
$$A: \text{Code} \longrightarrow \text{Witness}$$
And its corresponding healthy pattern acts as a contractive endomorphism:
$$H: \text{Code} \longrightarrow \text{Code}$$
Satisfying exact operadic annihilation:
$$\|A(H(c))\| = 0 \quad \forall c \in \text{Code}$$

### Do We Need a Separate Healthy Pattern Hunter Skill?

Under this operadic duality ($A \dashv H$), detecting an anti-pattern $A(c)$ is structurally dual to verifying whether the healthy pattern $H(c)$ holds.
- **Current Architecture:** `auto-code-anti-pattern-hunter` performs **dual-role hunting**: it detects unmitigated anti-patterns while simultaneously certifying adherence to healthy patterns.
- **Future Factoring:** A dedicated `auto-code-healthy-pattern-hunter` (or positive scaffolding engine) is only necessary if positive architectural synthesis (generating healthy code templates) needs to be decoupled from adversarial auditing. For now, maintaining healthy patterns alongside anti-patterns in `.agents/patterns/` (`anti/` and `helpful/` subfolders) guarantees single-source-of-truth coherence.

## Connected Specialist Skills

`auto-code-anti-pattern-hunter` dispatches targets to 4 language-specific pattern specialists:

1. [**`techne-code-python-anti-patterns`**](../techne-code-python-anti-patterns/SKILL.md):
   - Scope: Blanket `# type: ignore`, dataclass array hashing, bare exception swallowing, unclosed resources.
   - Dual Healthy Patterns: Scoped overrides, canonical immutable arrays, context managers.
2. [**`techne-code-rust-anti-patterns`**](../techne-code-rust-anti-patterns/SKILL.md):
   - Scope: Git worktree cargo target duplication, missing `PartialOrd, Ord` derives on domain enums, non-deterministic `HashMap` keys.
   - Dual Healthy Patterns: Shared `$env:CARGO_TARGET_DIR` cache, deterministic key traits, sovereign crate isolation.
3. [**`techne-code-sql-anti-patterns`**](../techne-code-sql-anti-patterns/SKILL.md):
   - Scope: Unparameterized string query concatenation, unbounded transaction leaks, null totality violations.
   - Dual Healthy Patterns: Parameterized binding, Unit of Work transaction fences, schema null totality.
4. [**`techne-code-lean4-anti-patterns`**](../techne-code-lean4-anti-patterns/SKILL.md):
   - Scope: Unmechanized `sorry` proof claims, unconstrained Mathlib rebuilds, unhedged thermodynamic-limit assertions.
   - Dual Healthy Patterns: Zero-sorry axiom allowlist, scoped target cache builds, finite-difference envelopes.
   - Catalog slots `json`, `markdown`, `html`, `javascript`, `manim`, `svg`, and `autop` have no admitted patterns, so this hunter does not invent signatures for them.

## Automated Execution & CLI Scanner

Execute the integrated pattern hunter scanner:

```bash
# Scan modified diff or specific directories
py -3.12 omega_engine_operads/skills/auto-code-anti-pattern-hunter/scripts/hunt_antipatterns.py <target-paths> --summary

# Generate structured JSON receipt
py -3.12 omega_engine_operads/skills/auto-code-anti-pattern-hunter/scripts/hunt_antipatterns.py . --output runs/anti_pattern_receipt.json
```

## Integration with `auto-oe-autop`

This skill is embedded into [**`auto-oe-autop`**](../auto-oe-autop/SKILL.md) under **Stage 1 (Episode Intake & Anti-Skill Mining)** and as a pre-commit verification gate.

When AutoP executes, it invokes `auto-code-anti-pattern-hunter` to verify that newly generated code does not introduce registered anti-patterns and conforms to healthy architectural baselines.
