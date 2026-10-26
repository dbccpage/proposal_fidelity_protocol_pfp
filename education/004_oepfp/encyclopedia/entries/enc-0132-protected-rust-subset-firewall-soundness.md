---
id: ENC-0132
kind: theorem
name: "Protected Rust Subset Firewall Soundness"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: []
sources:
  - "symbol_game_math_spine.md trunk Part III §4.4 'Theorem (Protected Rust Subset Firewall Soundness)'"
uses: ["ENC-0131"]
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0132 — Protected Rust Subset Firewall Soundness

## Statement

If
\(V_{\mathrm{PRS}}(x,P)=1\), then the rewrite preserves the checked protected
skeleton invariants in the declared source-level Rust envelope: no macro,
attribute, or cfg mechanism can introduce unchecked unsafe or unchecked public
API mutation inside the protected region.

## Hypotheses

Verbatim setup from the source section:

> Define `ProtectedRustSubset(PR)` for a protected rewrite region \(PR\) as the
> syntactic subset satisfying all of the following:
>
> 1. no macro invocation nodes in the protected region;
> 2. no `macro_rules!`, `include!`, `global_asm!`, `asm!`, or proc-macro
>    expansion point in the protected region;
> 3. no attributes on protected items except a declared inert allowlist whose
>    expansion effect is identity on item presence, signature, visibility, ABI,
>    linkage, and body syntax relevant to the checked invariants;
> 4. no `cfg` or `cfg_attr` on protected items unless the finite configuration
>    model \(K_\Phi\) is declared and the rewrite introduces no new cfg atoms
>    without a config/migration license;
> 5. no new `unsafe` tokens, unsafe blocks, `unsafe fn`, unsafe traits, unsafe
>    impls, or FFI/linkage constructs when `must_not_add_unsafe` is set;
> 6. no hidden carrier mutation: protected span, node id, public signature
>    projection, basis/carrier hash, and rewrite scope remain bound to the
>    parser-produced AST identity.
>
> Let \(V_{\mathrm{PRS}}\) be the pre-expansion verifier that rejects any
> protected rewrite outside `ProtectedRustSubset(PR)` and then runs:
>
> - exact protected span/node binding;
> - `lhs` equality against the parser slice;
> - `rhs` parseability in the expected syntactic category;
> - protected signature and skeleton comparison;
> - unsafe traversal over the protected AST;
> - finite cfg enumeration over \(K_\Phi\) when cfg is admitted.

## Proof

By acceptance, the rewrite lies in `ProtectedRustSubset(PR)`. Items
1 and 2 remove macro expansion points from the protected region, so there is
no post-parse macro output that can introduce unchecked syntax there. Item 3
restricts attributes to a declared inert allowlist whose effect on the checked
protected projections is identity. Item 4 either reduces cfg behavior to the
finite enumeration \(K_\Phi\) or rejects new cfg atoms. Therefore conditional
presence/signature drift is either checked or refused. Item 5 makes the unsafe
scan complete for the admitted source envelope because there is no remaining
post-parse mechanism in the protected region that may synthesize unsafe syntax.
Item 6 prevents checking one AST node while mutating another carrier or span.
The remaining verifier checks compare exactly the protected projections over
the original and rewritten ASTs. Hence every accepted rewrite preserves the
declared protected skeleton invariants inside the protected Rust subset.
\(\square\)

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| acceptance by \(V_{\mathrm{PRS}}\) implies preservation of the checked protected skeleton invariants within `ProtectedRustSubset(PR)` | local | none identified | NOT-STARTED |

## Notes

- The source closes the section with the scope caveat, verbatim: "This is not
  a theorem about unrestricted Rust semantics. If arbitrary macros, proc-macro
  attributes, build-script-generated code, or undeclared cfg atoms are allowed
  in the protected region, the firewall theorem does not apply; the verifier
  must switch to expansion-aware checking or reject."
- `uses` ENC-0131: the verifier's finite cfg enumeration step is the
  decidability result of [[ENC-0131]] (item 4 / final verifier check). Related:
  [[ENC-0129]] (skeleton invariant), [[ENC-0130]] (macro counterexample
  motivating the macro-free subset).

## Provenance

- Extracted 2026-06-09 from `symbol_game_math_spine.md` (trunk; header status
  "DEPENDENT REALIZATION SPINE"), Part III §4.4 "Protected Rust Subset Firewall
  Soundness" (statement and proof copied verbatim). Original header line:
  `**Theorem (Protected Rust Subset Firewall Soundness).** If`

## Changelog

- 2026-06-09: ENC-0132 created (M2 E2 satellite extraction).
