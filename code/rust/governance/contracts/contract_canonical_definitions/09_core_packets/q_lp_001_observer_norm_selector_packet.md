---
title: "Q-LP-001 — Lp Observer/Norm Selector and Finite Descent"
author: "Jeremy H. Carroll"
date: "2026-06-22"
status: "RESEARCH PACKET — Lp norm selection as observer-choice obstruction"
provenance: "Triggered by representation-transport audit (Q-REAL-001). The Lp family is the observer/norm axis of the same representation-transport question."
---

Thesis
------

The choice of Lp norm in the QM series is an observer-selection problem, not a physical law. Different norms see different residuals. The correct question is not "which p is true?" but "for which declared carrier and observer axioms is an Lp norm selected, and what does it preserve and fail to see?"

Driving obstruction
-------------------

The QM spine uses three norms at different layers:

| Norm | Layer | Role | Paper |
|------|-------|------|-------|
| L¹ | Residual mass / probability | Diagonal bookkeeping: $\Phi_1$ is an L¹ quotient mass over the defect space. | QM_000, QM_017 |
| L² | Amplitude geometry | Phase fiber, interference, inner-product structure. | QM_025, QM_026 |
| Schatten-1 (trace norm) | Operational distinguishability | CPTP channel metric after the quantum interface is declared. | QM_006, QM_023 |

The open question is: **are these three norms independently selected, or does one force the others given the carrier and composition rule?**

ODP field mapping
-----------------

| ODP field | Instance |
|-----------|----------|
| Carrier | The space of candidate observer norms over a declared finite carrier. |
| C⁰ | A candidate Lp norm $\|\cdot\|_p$ on the declared carrier's state/effect space. |
| d₀ | The norm-selection derivation: given carrier + composition + pairing axioms, which norms are forced? |
| C¹ | Defects where a candidate norm fails: non-monotonicity under allowed operations, failure to commute with composition, failure to descend to finite terminal evidence. |
| ZeroRel | Norm-equivalence on the declared finite carrier (all norms agree on finite-dimensional spaces up to constants; the question is which one is *canonical* under the declared operations). |
| B¹ = im(d₀) | Norm-choice defects removable by rescaling or carrier-dimension finiteness. |
| Q¹ = C¹/im(d₀) | Irreducible norm-selection residuals: which properties force which p? |
| d₁ | Cross-context compatibility: does the norm selection commute with composition, transport, and channel structure? |
| C² | The compatibility layer across subsystem composition. |
| Γ₂ | Closure failures: where different norm choices lead to different terminal classifications on the same finite packet. |
| Φ₁ | Mass of norm-selection residuals. |
| observer / norm | Meta-level: the observer that evaluates observer-selection (the GTOC diagnostic itself). |
| Λ | If norm selection is irreducible: declare the norm as an imported axiom with named source. |
| DDA op | `C` (context-exposure): mapping the Lp family as observer candidates. |
| terminal | To be determined by the audit. |

Norm comparison matrix
----------------------

| Property | L¹ | L² | Schatten-1 | Lp (general) |
|----------|----|----|-----------|-------------|
| Probability conservation | Preserves | Does not directly | Preserves for density operators | p=1 only |
| Interference visibility | Does not see phase | Sees phase and amplitude | Sees channel-level phase effects | Depends on p |
| Composition (tensor) | Multiplicative | Multiplicative | Multiplicative | Only p=1,2,∞ are multiplicative |
| Monotonicity under CPTP | Contractivity | No general contractivity | Contractivity | p=1 contractivity; general p not |
| Finite descent | Yes (finite sums) | Yes (finite sums) | Yes (finite matrices) | Yes (all finite) |
| Uniqueness given axioms | Selected by $\ell^1$ additivity (QM_004) | Selected by inner-product structure | Selected by CPTP transport | Open for general p |

Central residual
----------------

```text
OB-LP: The Lp norm hierarchy is currently an architectural choice, not a derived consequence.
       L¹ is selected by additivity + non-negativity (QM_004).
       L² is selected by inner-product/interference requirements (QM_025/026).
       Schatten-1 is selected by CPTP contractivity (QM_006).
       Question: does the ladder force exactly these three, or are alternatives admitted?
```

Claim ledger
------------

| # | Statement | Type | Evidence |
|---|-----------|------|----------|
| 1 | L¹ is the canonical observer for residual mass under non-negative additivity | [DERIVED] | QM_004 (L1 Additivity) |
| 2 | L² is the canonical amplitude geometry norm given inner-product structure | [CONDITIONAL] | Conditional on Hilbert-space lift (QM_010 optional) |
| 3 | Schatten-1 is the operational distinguishability norm given CPTP interface | [CONDITIONAL] | Conditional on CPTP channel declaration (QM_006, QM_023) |
| 4 | General Lp (p ≠ 1, 2, ∞) norms lack tensor-product multiplicativity | [STANDARD] | Classical functional analysis |
| 5 | All norms agree on finite-dimensional spaces up to dimension-dependent constants | [STANDARD] | Finite-dimensional norm equivalence |
| 6 | The norm-selection hierarchy is derivable from carrier + composition + pairing | [CONJECTURE] | Not yet mechanized |

Support boundary
----------------

* **Supports:** The three-norm architecture (L¹/L²/Schatten-1) is consistent with the declared carrier and operations at each layer.
* **Does not support:** A claim that exactly these three norms are uniquely selected by the ladder alone. The composition-rule dependency (Q-REAL-001) may affect norm selection.
* **Narrowest defensible claim:** L¹ is forced by non-negative additivity (QM_004). L² and Schatten-1 are conditionally selected given their respective interface declarations.
* **Next test needed:** Mechanize the norm-selection as a CODA-OR/CODA-MUR classification: which axioms force which norm, and does composition-rule choice affect the hierarchy?

Q-layer status
--------------

This packet does not enter Q. All components are finite-dimensional. The norm-selection question is a finite classification problem.

References
----------

* QM_004 (State Effect Pairing Audit) — L¹ additivity
* QM_006 (Trace Norm CPTP Transport Audit) — Schatten-1 selection
* QM_017 (Residual Density Calculus L1 L2 Boundary) — L¹/L² interface
* QM_025 (Superposition as the Quotient Fiber) — L² amplitude geometry
* QM_026 (Interference as the Non-L1 Resource) — signedness / L² forcing
* Q-REAL-001 — composition-rule dependency
