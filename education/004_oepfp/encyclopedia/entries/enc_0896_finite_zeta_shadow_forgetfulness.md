---
id: ENC-0896
kind: theorem
name: "Finite Zeta Shadow Forgetfulness"
status: MECHANIZED
conditional_on:
  - "Finite zeta shadows are modeled as finite evidence shapes"
  - "Continuum-source status is modeled separately from finite shadow shape"
layer: symbol-game
tower_level: null
primitive: null
aliases: ["paper:sn-packets:finite-zeta-shadow-forgetfulness", "paper:sn-packets:zeta-shadow-not-continuum-source"]
sources:
  - "s_n_packets_and_the_symbol_game.md §10 'Theorem 15: Finite Zeta Shadows Do Not Determine Source or Delta'"
uses: ["ENC-0888", "ENC-0889", "ENC-0895"]
lean_status: MECHANIZED
lean_refs:
  - "engine/lean4/research_programs/008_engine_runtime/007_er007_tower_zeta.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0896 - Finite Zeta Shadow Forgetfulness

## Statement

Finite zeta-shadow shape alone does not determine continuum-source status or
the tower-delta law. There is a two-world witness in which the same finite zeta
shadow is compatible with one world that names RH as the continuum source and
another world that does not. There is also a two-world witness in which the
same finite tower-zeta shape is compatible with the Symbol Game `delta = 2`
tower and a non-`delta = 2` tower.

## Proof Pointer

Mechanized in `engine/lean4/research_programs/008_engine_runtime/007_er007_tower_zeta.lean`.

The Lean theorem name is:

- `SnSymbolGameAndPackets.finite_zeta_shadow_forgets_continuum_source`
- `SnSymbolGameAndPackets.finite_zeta_shadow_forgets_delta_two_status`

`lake build SnSymbolGameAndPackets` succeeds and reports these two theorems as
axiom-free.

## Notes

- This is the zeta/tower analogue of [[ENC-0888]] packet-shape forgetfulness and
  [[ENC-0889]] local-dashboard quotient failure.
- The theorem does not deny that an RH continuum-source bridge may exist. It
  says that finite shadow shape does not recover that bridge without additional
  declared and certified structure.
- The theorem likewise does not deny that a tower has a declared delta. It says
  the delta law is not reconstructed from finite zeta-shadow shape alone.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass, in response to the tower/zeta/RH-source conjecture.

## Changelog

- 2026-06-13: ENC-0896 created with Lean mechanization.
