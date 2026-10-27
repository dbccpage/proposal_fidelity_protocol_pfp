---
name: techne-code-rust-anti-patterns
description: "Find Rust failure mechanisms with bounded scans, concrete witnesses and targeted repair checks."
operad_source_colours: ["Code"]
operad_target_colour: "Audit"
operad_arity: 1
operad_residual: "unknown"
families: [techne, quality, rust]
---

# Techne Code Rust Anti-Patterns

**Status:** canonical-candidate. **AuthorityEffect:** None.

Audit `engine/crates_rs/` against the existing Rust pattern catalog.
Static matches are review leads, not compiler findings or certification.

## Existing owners

| Pattern | Failure | Supported alternative |
| --- | --- | --- |
| `AP_RS_001` | Worktree target duplication | [Shared cache](../../patterns/helpful/rust/HP_RS_001_shared_cargo_target_cache.md) |
| `AP_RS_002` | Missing total order on actual ordered keys | [Meaningful ordered keys](../../patterns/helpful/rust/HP_RS_002_deterministic_key_trait_derive.md) |
| `AP_RS_003` | Incremental cache disk exhaustion | [Selective cache hygiene](../../patterns/helpful/rust/HP_RS_003_incremental_cache_pruning.md) |
| `AP_RS_007` | Assumed boundary completion | [Explicit bounded completion](../../patterns/helpful/rust/hp_rs_007_explicit_boundary_completion.md) |

Read [Rust engineering standards](../../rules/engineering/rl_rust_engineering_standards.md)
and [Auto Learn](../auto-learn/SKILL.md) before repair.

## Audit procedure

1. Freeze the candidate revision and enumerate every requested `.rs` path.
   Compare the scanned set with that inventory; crate discovery alone can omit
   root build files and directories without a direct `Cargo.toml`.
2. Run the requested signature checker and retain its exit status and scope:

   ```powershell
   .venv/Scripts/python.exe operads/skills/techne-code-rust-anti-patterns/scripts/rust_anti_pattern_auditor.py --path engine/crates_rs --check
   ```

   This lexical script masks comments/literals and checks exact derive names on
   public enums. Exit 1 means candidates need triage; exit 2 means a root,
   enumeration or read failure. It does not implement the complete pattern
   catalog, type checking, manual trait resolution or data-flow review.
3. Triage matches in actual code. Exclude comments and strings; track test-module
   braces rather than treating every line after `#[cfg(test)]` as test code.
   Report derive-only candidates as unverified review leads, distinguish `Eq`
   from `PartialEq`, and do not classify a checkout by an ancestor named `tests`.
   Inspect `cfg`, macros and unusual syntax separately when the scanner cannot.
4. For ordered collections, inspect the actual key and replay contract. Require
   exact trait tokens `PartialOrd` and `Ord`; a substring match is insufficient.
   An enum deriving only `PartialOrd` is a harmful missing-order scanner control. Derive
   total order only when the type has a meaningful order and its payloads
   support it. Do not bulk-add derives to float/error/JSON result carriers.
   An enum in `BTreeMap<String, Enum>` is a value, not the ordered key; neither
   is the error in `Result<BTreeMap<Key, Value>, Error>`. Inspect manual `Eq`,
   `Hash` and `Ord` together before suggesting a derive.
   Internal hash lookup is acceptable when the consuming output explicitly
   sorts or canonicalizes keys. Sorting console text does not sort JSON fields.
5. For subprocess and exact arithmetic boundaries, use `AP_RS_007`: verify
   restriction-before-execution, successful pipe collection before success,
   extreme valid operands before modular reduction, and final serialized bytes.
6. Demonstrate a failure with a bounded witness and a benign control; connect
   the repair to a tracked test. Label source-only ordering gaps as such.
   Record unavailable checks and residual uncertainty without inventing PASS.

## Ordering witnesses

- Sort semantic names before allocating symbol IDs and traversing neighbors when
  emitted tapes carry names. Compare identical graphs with reversed interning
  histories as well as reversed graph insertion. Sorting allocation IDs alone
  preserves an accidental history, not the semantic replay contract.
- At documented canonical JSON/hash/identity boundaries, recursively sort object
  keys explicitly. Cargo feature unification can enable `serde_json/preserve_order`;
  default-map tests alone can hide a defect. Test the actual bytes, digest or
  duplicate decision with nested opposite insertion orders under that feature.
  Preserve array order and deliberately source-ordered display output.
- Manual trait laws need NaNs, signed zeros, integer extrema and mixed variants.
  Check `cmp == Equal` iff `Eq`, equal hashes and transitivity; use repeated
  ordered-set insertion and lookup. Bulk collection construction masked a real
  mixed-variant comparator defect in the retained RowValue witness.
- Label extracted loose-source harnesses separately from active Cargo package
  tests. No located consumer means unresolved external intent, not dead code.

## Repair and check limits

Use a primary shared Cargo target cache in worktrees, offline dependencies when
available, `-j 1`, and sequential package/test filters. Respect the user's check
budget; this skill does not authorize a full workspace build or CI sweep.
Inspect backward dependencies rather than infer architecture from crate names.
Keep allocation claims within the allocator, input profile and numeric carrier
actually measured; one stack-rational test does not cover arbitrary precision.

Return actionable findings with source locations, commands actually run,
coverage gaps, reproductions, benign controls and remaining obligations.
Use the [Rust reviewer](../techne-code-rust-code-reviewer/SKILL.md) for the
surrounding API, safety and test review. AutoP invokes scoped learning by
default; it does not automatically run this entire audit or maintenance sweep.
