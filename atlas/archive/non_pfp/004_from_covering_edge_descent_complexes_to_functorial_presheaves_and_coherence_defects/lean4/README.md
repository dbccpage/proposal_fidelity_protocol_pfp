<!-- markdownlint-disable MD013 -->

# Lean 4 Proof Kernels — Paper PO-001

This directory contains Lean sources for selected algebraic kernels of Paper PO-001 (*From Covering-Edge Descent Complexes to Functorial Presheaves and Coherence Defects*). Source presence is distinct from a fresh successful kernel build. The 2026-10-02 review did not have Lean/Lake available and did not replay these sources.

Reproduce the focused current replay from this directory with `lake env lean ConcreteIncidence.lean`,
`lake env lean FlatLossAndCurvature.lean` and `lake env lean AllDegreeCurvature.lean`.
For the new roots, first compile the local dependency with
`mkdir -p .lake/build/lib/lean` and
`lake env lean -o .lake/build/lib/lean/ConcreteIncidence.olean ConcreteIncidence.lean`,
then run `lake env lean HeterogeneousIncidence.lean` and
`lake env lean TransportIdentities.lean`.
Use `lake build` only when intentionally auditing every older declared root. The toolchain and Mathlib revision are pinned by the adjacent
project files.

## Architecture & Module Inventory

- `PrimitiveDifference.lean`: Foundational quotient difference kernel `OmegaCore.PrimitiveDifference`.
- `StrictCompletion.lean`: Path A finite algebraic completion of covering edges to functorial presheaf.
- `CurvatureCochain.lean`: Path B coboundary-curvature theorem $d_1 d_0 = K$, flat locus equivalence, and degree-3 boundary formula $d_2 K$.
- `PrimitiveDifferenceLggr.lean`: Primitive difference quotient boundary and Local Green, Global Red (LGGR) certification.
- `CohomologyClass.lean`: Unconditional operator cocycle condition $\delta_2 K \equiv 0$ and a declared coboundary-image relation. It does not construct a generic $H^2$ quotient.
- `CurvedDerivation.lean`: The stated operator derivation identity over its declared carriers.
- `AllDegreeCurvature.lean`: Universal parity-algebra kernel: all-degree covariant Leibniz, curvature square, Bianchi and invertible-endpoint zero preservation. The poset differential laws are explicit assumptions. The supplementary October 14 replay and exact dependencies are recorded in [the derivation review](../docs/derivations_2026_10_14.md); the pinned package has not been replayed.
- `CurvedDerivationStandalone.lean`, `CODAWitnessStandalone.lean`, `PrimeTriadRouterStandalone.lean`, `ReggeBianchiStandalone.lean`, `SheafContextualityStandalone.lean`: Additional standalone finite kernels. Their assumptions and statements must be inspected individually; their names do not prove the broader geometric or contextuality interpretations corrected in the current manuscript.
- `Core.lean`: Unified import hub aggregating all PO-001 proof modules.
- `AxiomAudit.lean`: `#print axioms` report for inspection; it does not enforce an allowlist. The source tree contains no `sorry`/`admit`.
- `Census.lean`, `DualWitnessStandalone.lean`: Additional source records; this supplement does not replay or extend their proof scope.
- `lakefile.lean`, `lean-toolchain`: Reproducible project and dependency pins.

## Axiom Audit Summary

The historical September 27 manifest records a selected, older theorem list and its reported dependencies. It is not a complete inventory or a fresh v2.0 build receipt. The September source inventory had 16 theorem/module sources; the current tree has 20 plus `lakefile.lean`. Receipts record each successive selected replay and its exact source/dependency digests.

`AxiomAudit.lean` prints dependencies; it does not enforce an allowlist. The historical status legend also allows `Classical.choice`. A source scan for `sorry`/`admit` is weaker evidence than a successful kernel replay and a declaration-specific dependency inspection. No blanket axiom whitelist or full-manuscript mechanization claim is made by the current review. The manifest and proof sources are preserved as historical artifacts. None of this constructs a generic cohomology quotient.

## Current concrete replay

The new [derivation review](../docs/loss_incidence_angles_2026_10_14.md) and
[source-bound receipt](../code/loss_incidence_angles_verification.json) supersede
the earlier reproduction limits for the three explicitly replayed roots.
`ConcreteIncidence.lean` constructs intrinsic strict-poset operations over a
common noncommutative ring and proves nilpotence, graded Leibniz and the
curvature square from definitions. Degree zero has a separate endpoint-action
proof. `FlatLossAndCurvature.lean` proves the exact positive normalized flat-loss
example. These add two modules to the older 16-module source inventory.

Current stable Lean 4.34.0 and Mathlib 5ed2965 are deliberate new pins, with all
nine dependency revisions locked in lake-manifest.json. The former rc1/de5ce8
pair and its historical manifest remain historical, unreplayed evidence.
The main word algebra uses propext and Quot.sound; intrinsic poset operations
and the rational matrix controls also use Classical.choice. No sorryAx occurs
in the current accepted declaration outputs. That receipt predates the heterogeneous endpoint-Hom block embedding.
The new five-derivation receipt below updates its scope; graded Jacobi and
every older root remain outside the current replay.

## Heterogeneous and transport replay

`HeterogeneousIncidence.lean` defines the actual varying endpoint-Hom cochains,
coordinate corner injection/extraction, strict-poset zero extension and
restriction, and intrinsic deletion/covariant squares through a faithful map.
Its declaration dependencies are propext, Classical.choice and Quot.sound.
`TransportIdentities.lean` defines comparison labels and finite recursive
path products, proving mixed horizontal composition, interchange, unit and
compositor identities, split descent uniqueness and arbitrary finite
telescoping. Its printed dependencies use propext. No sorryAx is accepted.
These algebraic kernels do not formalize RREF minimality, norm estimates, the
full typed 2-category or metric/transcendental geometry. Graded Jacobi is
written and natively tested, with no new Lean proof claimed.
See [the current supplement](../docs/five_connected_derivations_2026_10_14.md).
