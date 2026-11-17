---
name: techne-code-rust-code-reviewer
description: "Review Rust APIs, safety boundaries and deterministic outputs with concrete findings and scoped checks."
operad_source_colours: ["Code"]
operad_target_colour: "Audit"
operad_arity: 1
operad_residual: neutral
families: [techne, quality, rust]
---

# Techne Code Rust Code Reviewer

**AuthorityEffect:** None.

Use for Rust changes and bounded estate reviews. Read the candidate diff, caller
contracts and [Rust engineering standards](../../rules/engineering/rl_rust_engineering_standards.md).
The [code quality checklist](../_shared/checklists/code_quality_checklist.md)
supplies the broader rubric; the procedure below supplies Rust-specific checks.

## Bound the review

Identify the revision, requested paths, public APIs, supported platforms/features,
external inputs and replay contract. Enumerate `.rs` files independently. The
script below discovers direct Cargo crates and includes loose files in its
`<non-crate>` report group. Compare reported file paths to the inventory and
review any gap explicitly; cache directories are deliberately excluded.

```powershell
.venv/Scripts/python.exe operads/skills/techne-code-rust-code-reviewer/scripts/rust_crate_reviewer.py --base-dir engine/crates_rs --check
```

The automated reviewer uses regex/source heuristics, not a compiler AST. Read
its present implementation before assigning meaning to match counts. Comments,
string literals, test scopes, conditional compilation and macros can create
false positives or omissions. The scanner masks nested comments and literals,
compares exact derive names, and scopes simple `#[cfg(test)]` / `#[test]` items.
It does not resolve manual trait implementations or conditional features.
Its ordering rows are unverified, derive-only review leads; `PartialEq` is not
`Eq`. A report severity label must not imply a demonstrated compiler defect.
Exit 1 means ordering/local-cache candidates; exit 2 means an invalid root or
enumeration/read failure. Record check exits; a zero exit is not a general
Rust correctness or safety verdict. When changing a detector, plant a harmful
case and a benign control through its actual command, not a parallel regex.

## Inspect the actual boundary

- **Safety and lifetime:** trace each active `unsafe` block to pointer ownership,
  handle lifetime and the OS/API preconditions. Commented-out transmute text is
  not a live unsafe operation. Test-only sites need their own scope label.
- **Subprocess confinement:** prove restrictions apply before untrusted code
  executes. On Windows, create suspended, assign the Job Object successfully,
  then resume; terminate and close handles on every setup failure. A later
  parent assignment cannot establish membership for earlier descendants.
- **Output and refusal:** child exit does not imply inherited pipe EOF. A reader
  timeout, disconnection, I/O failure or output overflow must not become a
  successful empty capture. Bind elapsed collection to the declared deadline;
  preserve ordinary empty output, nonzero exit codes and bounded output.
- **Exact arithmetic:** inspect intermediate operations before modular reduction.
  Reduce inputs first or widen safely; check negative values and integer extrema
  in overflow-checked and unchecked configurations. Do not weaken assertions
  or replace exact arithmetic with tolerances to make a regression pass.
- **Determinism:** inspect final bytes, not console formatting. Use ordered keys
  or canonicalization at serialized report/receipt boundaries. Internal hash
  lookup with a sorted consuming boundary can be valid. A supported total-order
  key needs exact `Eq`, `PartialOrd`, `Ord` traits; error and payload carriers do
  not automatically have a meaningful total order.
- **Ordering semantics:** distinguish map keys from values and `Result` errors.
  Check manual `Eq`/`Hash`/`Ord` laws, including custom equality that ignores
  display fields. For floats, exercise NaNs and signed zeros; test repeated set
  insertion/lookup and mixed variants, not just bulk collection.
  If wire tapes contain names, compare different symbol allocation histories
  and neighbor insertion orders. Sorting interned IDs is not sorting names.
- **Canonical JSON:** Cargo feature unification can enable
  `serde_json/preserve_order`. At promised canonical bytes/hash/identity
  boundaries explicitly sort nested objects, then exercise the public entry
  point under that feature with opposite insertion orders and a pinned digest.
  Changed array order must remain distinguishable. Do not sort intentionally
  source-ordered presentation output or rely on default-map tests alone.
- **API and architecture:** preserve existing outcome roots and field meanings,
  inspect dependency directions, and keep refusal paths typed. Do not add a
  framework when a local repair preserves the contract.

The concrete witnesses and deciding controls are in
[AP_RS_007](../../patterns/anti/rust/ap_rs_007_assumed_boundary_completion.md)
and [HP_RS_007](../../patterns/helpful/rust/hp_rs_007_explicit_boundary_completion.md).

## Recheck and report

Run only checks justified by the changes and user budget. Use the primary shared
Cargo target cache in worktrees, `-j 1`, offline dependencies when available and
sequential package/test filters. No full canonical CI is implied by this skill.
Use actual production paths in regression tests, with hostile and benign inputs;
allocation claims retain their tested carrier and finite input scope.

Report severity, path/line, failed assumption, concrete consequence, repair and
actual check. Separate reproduced failures from source-only gaps and hypotheses.
Report implementation completion separately from broader proof or certification.
An extracted retained-source harness does not verify an installed Cargo package;
no located consumer does not prove that external consumers cannot exist.
Do not count every enum/hash/unwrap match as a defect or bulk-repair raw results.

## Formatting and encoding

Lint created or modified Markdown with the available Markdown linter; lint other
changed languages with their scoped tools. Keep UTF-8 without BOM, check local
links and report unavailable linting. Preserve Rustdoc and formal Unicode.
