---
id: ENC-0111
kind: theorem
name: "Realization-Arrow Soundness — net-new proof body"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: []
sources:
  - "symbol_game_math_spine.md math_spines_v002 §Realization Functor Boundary 'Theorem (Realization-Arrow Soundness — net-new proof body)'"
  - "proof_obligations.md v1.3.5 §13 'Theorem' (section 'PO-SGRF — Symbol Game Realization Functor Theorem (SG-REP-001)')"
uses: ["ENC-0105"]
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0111 — Realization-Arrow Soundness — net-new proof body

## Statement

\(\eta_{\mathrm{SG}}^\sharp\) is total-or-refusing, grammar-preserving,
schema-preserving, ceiling-preserving, and cannot create authority.

## Hypotheses

The source fixes the setting immediately above the theorem, verbatim:

Fix a finite closed packet grammar \(\Gamma\), a typed seed \(s^\#\), a host
declaration
\[
D=(\mathsf{family},\mathsf{ceiling},\mathsf{terminal\_policy},
\mathsf{verifier\_scope}),
\]
and a registry of family-specific realizers; let \(\eta_{\mathrm{SG}}^\sharp\)
be the canonical arrow of §X.1. The realization procedure parses raw bytes into
the closed grammar, checks that the packet family equals the host declaration,
checks
\[
\mathsf{packet.ceiling}\le D.\mathsf{ceiling}\le s^\#.\mathsf{ceiling},
\]
runs the registered family realizer, and requires typed-pair fidelity before it
seals a `TypedOmegaPacket`.

## Proof

Parsing is a total deterministic finite computation on raw bytes:
it either returns a value of the closed typed grammar or a typed refusal.
Family equality and the two ceiling comparisons are decidable checks on finite
enums. Registry lookup either selects one declared family realizer or refuses.
Each selected realizer either produces a typed normalized artifact or refuses;
an implementation panic is caught at this untrusted boundary and mapped to a
typed refusal. The typed-pair fidelity validator is a finite conjunction and
either supplies its sealed witness or refuses. Thus every input returns exactly
one coproduct arm.

On the success arm, the closed grammar and registered family realizer witness
grammar and schema preservation. The explicit chain
\(\mathsf{packet.ceiling}\le D.\mathsf{ceiling}\le s^\#.\mathsf{ceiling}\)
witnesses ceiling preservation. The successful object carries proposal
evidence and host declarations only: it has no authority field, no
`CertifiedAuthority`, and no deserialization constructor. Omega authority
remains constructible only from terminalized finite descent. Therefore the realization arrow cannot create authority. \(\square\)

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| coproduct totality + grammar/schema/ceiling preservation + no-authority-field for the SG realization arrow | local | none identified | NOT-STARTED |

## Notes

- The arrow itself (`η_SG^♯ : RawLLMOutput → TypedOmegaPacket+𝔽`, Kleisli arrow,
  NOT a functor, PO-10 OPEN) is canonical §X.1 = [[ENC-0105]]; the source's own
  canonical-home blockquote states that "canonical §X.1 declares the arrow but
  does not reproduce this proof body" — only this soundness theorem and its proof
  are net-new here.
- The source follows the proof with a done condition, verbatim:
  "**Done condition.**
  \[
  \eta_{\mathrm{SG}}^\sharp(r)=\mathsf{inl}(P)
  \Rightarrow
  P:\mathsf{TypedOmegaPacket}
  \]
  with declared family, ceiling, terminal policy, and verifier scope. Every
  other input returns \(\mathsf{inr}(\phi)\)."
- Variant statement in proof_obligations.md v1.3.5 §13 "PO-SGRF — Symbol Game
  Realization Functor Theorem (SG-REP-001)": "**Theorem.**
  \(\eta_{\mathrm{SG}}^\sharp\) is total-or-refusing, grammar-preserving,
  schema-preserving, ceiling-preserving, and authority-non-constructing."
  ("authority-non-constructing" for this entry's "cannot create authority" —
  same five-property claim.) The variant's setting fixes the host declaration
  \(D=(f_D,e_D,\tau_D,V_D)\), a finite transform ledger \(\mathrm{TL}\), and a
  realizer registry; its proof tracks an explicit 7-step ordered procedure
  (refuse empty raw output; host/seed family-and-ceiling gates; closed
  `RoutedSeed` schema parse; packet family/ceiling gates; registered
  `PacketFamilyRealizer` dispatch with panic-to-refusal; typed-pair fidelity
  \(F(s^\#,P^\#;\mathrm{TL})\) per PO-PFI; private seal constructor), with the
  ceiling chain \(P^\#.\mathsf{ceiling}\le e_D\le s^\#.\mathsf{ceiling}\) and
  authority non-construction routed through PO-AUTH-NC. NOT merged into the
  Statement.
- Variant status: "PROVED-PROSE and IMPLEMENTED/MACHINE-CHECKED for the
  workspace `omega_representation` boundary" (Rust binding:
  `omega_representation/src/{packet.rs,functor.rs,fidelity.rs}`;
  `RealizationFunctor::realize_raw` implements steps 1–7); "Operational
  rollout remains OPEN for the older standalone `products/symbol_game`
  adapters." The machine check is Rust, not Lean — `lean_status` unchanged.
- The PO id `PO-SGRF` names the variant's section header; this entry is its
  encyclopedia home.

## Provenance

- Extracted 2026-06-09 from `symbol_game_math_spine.md` (math_spines_v002,
  unversioned; status header "DEPENDENT REALIZATION SPINE"), section
  "Realization Functor Boundary" (statement, hypotheses context, and proof
  copied verbatim). Original header line:
  `**Theorem (Realization-Arrow Soundness — net-new proof body).**`

## Changelog

- 2026-06-09: ENC-0111 created (M2 E2 satellite extraction).
- 2026-06-09: variant provenance appended (M2 E3): proof_obligations.md §13
  PO-SGRF theorem recorded as duplicate variant (Notes + sources only;
  Statement untouched).
