---
id: ENC-0113
kind: corollary
name: "Compiler Does Not Supply Fidelity Authority"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: []
sources:
  - "symbol_game_math_spine.md math_spines_v002 §1.4 'Corollary (Compiler Does Not Supply Fidelity Authority)'"
  - "proof_obligations.md v1.3.5 §13 PO-PFI 'Corollary (Compiler Does Not Supply Fidelity Authority; restated from §1.4)' (variant)"
uses: ["ENC-0112"]
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0113 — Compiler Does Not Supply Fidelity Authority

## Statement

If \(V_{fid}\)
reconstructs and checks all fidelity clauses from the bundle, then the
seed-to-packet compiler is not trusted for fidelity merely because it emitted
the packet.

## Proof

Acceptance depends on replayed parser, normalizer, field-binding,
and transform-ledger checks, not on the compiler's assertion that the packet is
faithful. A compiler lie is rejected unless it also satisfies every clause of
\(V_{fid}\), which by the theorem implies \(F(s^\#,P^\#)=1\). \(\square\)

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| compiler-assertion independence: acceptance derivable only from replayed bundle checks | local | none identified | NOT-STARTED |

## Notes

- "the theorem" in the proof is the Implementation-Bound Packet Fidelity
  theorem, [[ENC-0112]]; "the bundle" is its fidelity bundle \(\mathcal{B}_{fid}\).
- The source's KEEP note marks this compiler-non-trust corollary as net-new
  (not reproduced in canonical; cf. [[ENC-0100]] for the abstract §VII.4 home).

- Variant provenance (E3, 2026-06-09): `proof_obligations.md` v1.3.5 §13
  PO-PFI carries a self-declared restatement — its name literally reads
  "restated from §1.4". The restated text differs in wording (acceptance
  depends on "the replayed normalizer prefix (parser folded in), schema,
  \(\mathrm{FBT}\), \(\mathrm{TL}\), \(\mathrm{SFM}\), and \(\mathrm{AM}\)
  checks") and adds: "The dropped `compiler_id` field is therefore not a
  trust regression; it is the corollary's enforcement." Variant recorded only
  here; the §1.4 text above remains controlling.

## Provenance

- Extracted 2026-06-09 from `symbol_game_math_spine.md` (math_spines_v002,
  unversioned; status header "DEPENDENT REALIZATION SPINE"), §1.4 "Packet
  Fidelity Theorem" / "Packet Fidelity Implementation Binding Rule" (statement
  and proof copied verbatim). Original header line:
  `**Corollary (Compiler Does Not Supply Fidelity Authority).** If \(V_{fid}\)`

## Changelog

- 2026-06-09: ENC-0113 created (M2 E2 satellite extraction).
- 2026-06-09: variant provenance appended (E3 proof_obligations.md v1.3.5 §13 PO-PFI restatement); Statement unchanged.
