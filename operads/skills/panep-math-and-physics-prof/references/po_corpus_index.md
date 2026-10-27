# Projection Obstruction Corpus Reference Index (PO-000 to PO-009)

This reference document provides comprehensive mathematical summaries, claim ledger references, and structural details for all 10 papers in the **Projection Obstruction (PO)** series (`atlas/coda_atlas/F004_papers/002_projection_obstruction`).

---

## 1. PO-000 — Anchor Monograph: Exact Short-Time Theorem & Mechanization Engine

- **Primary Paper:** [000_projection_obstruction.md](../../../../atlas/coda_atlas/F004_papers/002_projection_obstruction/000_projection_obstruction/projection_obstruction.md)
- **Claim Ledger:** [000_projection_obstruction_claim_ledger.md](../../../../atlas/coda_atlas/F004_papers/002_projection_obstruction/000_projection_obstruction/projection_obstruction_claim_ledger.md)
- **Change Log:** [000_projection_obstruction_change_log.md](../../../../atlas/coda_atlas/F004_papers/002_projection_obstruction/000_projection_obstruction/projection_obstruction_change_log.md)
- **Code & Engine:** `atlas/coda_atlas/F004_papers/002_projection_obstruction/000_projection_obstruction/` (`po000_projection_obstruction`)
- **Key Results:**
  - **Core Trichotomy:** Every observed residual $\omega \in C^1$ resolves into exactly one of:
    1. *Exact Repair:* $\omega \in \operatorname{im}(d_0)$.
    2. *Closed Survivor / Stabilized Survivor:* $d_1 \omega = 0$, but $\omega \notin \operatorname{im}(d_0)$.
    3. *Open Obstruction / Active Closure Failure:* $d_1 \omega \neq 0$.
  - **Short-Time Theorem:** For interaction norm $g_* > 0$ and active rate infimum $\nu_* > 0$, the uniform time window $0 < t \le \frac{\nu_*}{48 g_*^2}$ guarantees exact polynomial lower bounds on active edge and site defect densities.
  - **Site Density Floor:** $\text{site\_density\_floor}(t) = a_* \eta_* (\nu_* t - 24 g_*^2 t^2) \ge \text{half\_slope\_site\_floor}(t) = \frac{a_* \eta_* \nu_* t}{2}$.
  - **Full Incident Interaction Norm:** $g_* = \max_{v} \sum_{e \in I(v)} \|H_e\|$, eliminating target-edge shortcuts and accounting for all incident couplings.

---

## 2. PO-001 — Functorial Presheaves & Coherence Defects

- **Primary Paper:** [001_from_covering_edge_descent_complexes_to_functorial_presheaves_and_coherence_defects.md](../../../../atlas/coda_atlas/F004_papers/002_projection_obstruction/001_from_covering_edge_descent_complexes_to_functorial_presheaves_and_coherence_defects/covering_edge_descent.md)
- **Claim Ledger:** [001_from_covering_edge_descent_complexes_to_functorial_presheaves_and_coherence_defects_claim_ledger.md](../../../../atlas/coda_atlas/F004_papers/002_projection_obstruction/001_from_covering_edge_descent_complexes_to_functorial_presheaves_and_coherence_defects/covering_edge_descent_claim_ledger.md)
- **Key Results:**
  - Formulates covering-edge descent complexes as functorial presheaves $\mathcal{F}: \mathcal{C}^{\text{op}} \to \mathbf{Vect}$.
  - Proves that observation projections yield non-trivial Cech/cochain coherence defects $\delta^k$ when local data fail to glue into a global section.
  - Characterizes sheafification obstructions as boundary defects in the underlying Cech cochain complex.

---

## 3. PO-002 — Projection Residuals in AI Governance & Safety

- **Primary Paper:** `002_projection_residuals_ai_governance.md` (Archived provenance in `099_project_sentinel/PO-002`)
- **Claim Ledger:** `002_projection_residuals_ai_governance_claim_ledger.md`
- **Key Results:**
  - Applies projection obstruction theory to AI safety evaluators and alignment governance.
  - Demonstrates that safety evaluators act as *bounded observers* with strict projection loss.
  - Establishes that alignment claims certified by a bounded evaluator are subject to observer-blindspot residual bounds.

---

## 4. PO-003 — Projection to Cochain & Higher-Cell Lifts

- **Primary Paper:** `003_projection_to_cochain_and_higher_cells.md` (Archived catalog entry)
- **Claim Ledger:** `003_projection_to_cochain_and_higher_cells_claim_ledger.md`
- **Key Results:**
  - Constructs explicit cochain lifts $C^0 \xrightarrow{d_0} C^1 \xrightarrow{d_1} C^2 \dots$.
  - Proves the higher coboundary condition $d_1 \circ d_0 = 0$ for admitted covering-edge presentations.
  - Defines 2-cell face curvature $\delta^2 \omega$ as the obstruction to local edge-gauge consistency around closed faces.

---

## 5. PO-004 — Extensive Correlation Information (ECI)

- **Primary Paper:** `004_extensive_correlation_information.md` (Archived catalog entry)
- **Claim Ledger:** `004_extensive_correlation_information_claim_ledger.md`
- **Key Results:**
  - Introduces Extensive Correlation Information (ECI) as an information-theoretic metric over projection residuals.
  - Proves lower-bound inequalities for multi-party quantum correlation defects under local projection maps.

---

## 6. PO-005 — Projection Memory & Curvature Tensors

- **Primary Paper:** `005_projection_memory_curvature.md` (Archived catalog entry)
- **Claim Ledger:** `005_projection_memory_curvature_claim_ledger.md`
- **Key Results:**
  - Analyzes non-Markovian memory effects generated by iterated observation retractions.
  - Derives discrete curvature tensors $R_{\mu\nu}$ over retraction manifolds and quantifies memory accumulation over long time horizons.

---

## 7. PO-006 — Vector & Quantum Observer Geometries

- **Primary Paper:** [006_vector_and_quantum_observer_geometries.md](../../../../atlas/coda_atlas/F004_papers/002_projection_obstruction/006_vector_and_quantum_observer_geometries/vector_and_quantum_observer_geometries.md)
- **Claim Ledger:** [006_vector_and_quantum_observer_geometries_claim_ledger.md](../../../../atlas/coda_atlas/F004_papers/002_projection_obstruction/006_vector_and_quantum_observer_geometries/vector_and_quantum_observer_geometries_claim_ledger.md)
- **Key Results:**
  - Extends projection obstruction theory from scalar fields to vector bundles and quantum state spaces $\mathcal{H}_e$.
  - Formulates quantum local algebras, state-effect pairings $\langle E, \rho \rangle$, and linear observation maps $q_e: R_e \to V_e$.

---

## 8. PO-007 — M-Compatible Gauge Classification

- **Primary Paper:** [007_m_compatible_gauge_classification.md](../../../../atlas/coda_atlas/F004_papers/002_projection_obstruction/007_m_compatible_gauge_classification/m_compatible_gauge_classification.md)
- **Claim Ledger:** [007_m_compatible_gauge_classification_claim_ledger.md](../../../../atlas/coda_atlas/F004_papers/002_projection_obstruction/007_m_compatible_gauge_classification/m_compatible_gauge_classification_claim_ledger.md)
- **Key Results:**
  - Classifies gauge transformations that preserve local observation matrix structures ($M$-compatibility).
  - Establishes invariant subspaces and exact quotient metrics under $M$-compatible observer shifts.

---

## 9. PO-008 — SO(k)-Invariant Gauge Classification

- **Primary Paper:** [008_so_k_invariant_gauge_classification.md](../../../../atlas/coda_atlas/F004_papers/002_projection_obstruction/008_so_k_invariant_gauge_classification/so_k_invariant_gauge_classification.md)
- **Claim Ledger:** [008_so_k_invariant_gauge_classification_claim_ledger.md](../../../../atlas/coda_atlas/F004_papers/002_projection_obstruction/008_so_k_invariant_gauge_classification/so_k_invariant_gauge_classification_claim_ledger.md)
- **Key Results:**
  - Classifies rotational $SO(k)$ gauge symmetries acting on vector observation carriers.
  - Proves exact invariance theorems for isotropic retraction manifolds and isotropic cochain defects.

---

## 10. PO-009 — Coordinate-Wise Additivity & L1 Defect Theorems

- **Primary Paper:** [009_coordinate_wise_additivity.md](../../../../atlas/coda_atlas/F004_papers/002_projection_obstruction/009_coordinate_wise_additivity/coordinate_wise_additivity.md)
- **Claim Ledger:** [009_coordinate_wise_additivity_claim_ledger.md](../../../../atlas/coda_atlas/F004_papers/002_projection_obstruction/009_coordinate_wise_additivity/coordinate_wise_additivity_claim_ledger.md)
- **Key Results:**
  - Investigates coordinate-wise additivity of $L_1$ norms across uncoupled product observers.
  - Derives exact defect theorems showing where non-additive $L_1$ interference terms emerge under coupled observation maps.
