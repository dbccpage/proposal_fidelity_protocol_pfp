---
title: "Q-REAL-001 — Real vs Complex QM as Representation Transport"
author: "Jeremy H. Carroll"
date: "2026-06-22"
status: "RESEARCH PACKET — representation-transport audit for real-number QM formulations"
provenance: "Triggered by PRL 2025 paper (arXiv:2503.17307) showing QM over ℝ with modified composition rule reproduces complex-QM predictions."
---

Thesis
------

Real-number QM that reproduces complex-QM predictions is a representation-transport problem, not a refutation or confirmation of the Core QM spine. The selector question (OB-U1, QM_028) depends on the declared composition rule. A change in the composition postulate may admit a different carrier that is observationally equivalent on all finite prediction packets.

Driving obstruction
-------------------

OB-U1 (the ℂ/U(1) selector from QM_028) was scoped as:

```text
Given: nontrivial invariant phase, abelian phase, continuous reversible pairing-preserving transport
Result: ℂ/U(1) conditionally forced at the two-level core
Residue: continuity import; global field-uniqueness for n>2 (local tomography / Renou et al. 2021)
```

The PRL paper (arXiv:2503.17307) shows: **change the composition postulate** and a real carrier may become observationally equivalent. This means OB-U1 must be re-stated as conditional on the composition rule, not just on the phase/pairing properties.

ODP field mapping
-----------------

| ODP field | Instance |
|-----------|----------|
| Carrier | The space of representation-transport maps between real-doubled and complex QM carriers. |
| C⁰ | Standard complex QM as reference: complex Hilbert space, standard tensor product, U(1) phase, Born pairing. |
| d₀ | Representation transport: map from complex carrier to real-doubled carrier (or vice versa) preserving finite predictions. |
| C¹ | Defects where transport fails: composition rule mismatch, locality failure, fermionic obstruction. |
| ZeroRel | Prediction-equivalence on all declared finite observation packets. |
| B¹ = im(d₀) | Defects removable by carrier redescription (gauge equivalence between formulations). |
| Q¹ = C¹/im(d₀) | Irreducible residuals: composition-rule choice, locality postulate selection, global field-uniqueness. |
| d₁ | Cross-context compatibility: does the transport commute with multipartite composition, tomography, and channel structure? |
| C² | The compatibility layer across bipartite/multipartite/network scenarios. |
| Γ₂ | Closure failures: where real and complex formulations provably disagree on finite packets (if any). |
| Φ₁ | Mass of composition-rule residuals under the declared observer. |
| observer / norm | Finite prediction-equivalence on named experiments. |
| Λ | If composition-rule choice is irreducible: add it as a declared import. |
| DDA op | `C` (context-exposure): mapping the real formulation as a carrier variant. |
| terminal | To be determined by the audit. |

Candidate comparison matrix
---------------------------

| Axis | Complex QM | Real-doubled QM (PRL 2025) | Status |
|------|-----------|---------------------------|--------|
| Single-system predictions | Standard | Equivalent (by construction) | [CONDITIONAL] on doubled-space embedding |
| Bipartite composition | Standard tensor product | Modified real composition rule | [OPEN] — the central claim |
| Multipartite/network composition | Standard | Claimed equivalent (arXiv:2503.17307) | [OPEN] — requires finite-packet verification |
| Local tomography | Holds | May require modified statement | [OPEN] |
| Operational independence | Standard | Modified | [OPEN] |
| Fermionic systems | Standard | Not addressed in PRL paper | [OPEN] |
| Born/effect pairing | Standard | Transported | [CONDITIONAL] |
| CPTP/channel structure | Standard | Transported | [OPEN] |
| Continuum limit | Standard | Not the paper's concern | N/A |
| Finite replayability | Yes | Should be Yes (finite-dimensional) | [OPEN] |

Central residual
----------------

```text
OB-COMP: The composition-rule choice is not a consequence of the carrier selection.
         ℂ/U(1) is forced given standard tensor-product composition.
         ℝ-doubled is admitted given modified composition.
         The composition rule itself is an imported or derived component — which?
```

Claim ledger
------------

| # | Statement | Type | Evidence |
|---|-----------|------|----------|
| 1 | QM_028 conditional forcing remains valid under declared assumptions | [DERIVED] | ForceComplexCarrier.lean, U1Selector.lean |
| 2 | Real-number QM with modified composition reproduces finite predictions | [CONDITIONAL] | arXiv:2503.17307 — conditional on the modified composition postulate |
| 3 | The composition rule is an independent parameter, not derivable from carrier choice | [CONJECTURE] | Not yet mechanized; CODA-OR/CODA-MUR classification needed |
| 4 | Complex QM was shown "essential" under standard postulates (Renou et al. 2021) | [IMPORTED] | Nature 2021 experimental result |
| 5 | The PRL paper identifies one postulate as more restrictive than needed | [IMPORTED] | arXiv:2503.17307 |
| 6 | Representation equivalence on all finite packets implies same GTOC terminal shadow | [STANDARD] | Follows from finite-terminal doctrine |

Support boundary
----------------

* **Supports:** OB-U1 is alive and correctly scoped as conditional. The real-vs-complex question is a representation-transport problem, not a refutation of the ladder.
* **Does not support:** Closing OB-U1 more strongly than QM_028 currently claims. The composition-rule dependency is now exposed.
* **Narrowest defensible claim:** ℂ/U(1) is conditionally selected at the two-level core given the standard composition and named imports. A different composition rule may admit a prediction-equivalent real carrier.
* **Next test needed:** Mechanize the composition-rule parameter as a CODA-OR/CODA-MUR classification: which composition rules are compatible with which carriers, and which pairings are prediction-equivalent on named finite packets?

Q-layer status
--------------

This packet does not enter Q. All components are finite-dimensional. The composition-rule parameter is a finite classification problem, not a continuum limit.

References
----------

* arXiv:2503.17307 — "Quantum mechanics based on real numbers: A consistent description"
* Renou et al., Nature 2021 — "Quantum theory based on real numbers can be experimentally falsified"
* QM_028 (The U(1)-Selector) — engine/research/published/qm/qm_028_the_u1_selector/
* QM_027 (The Finite QM Ingredient Ladder) — engine/research/published/qm/qm_027_the_finite_qm_ingredient_ladder/
