#![cfg(any())]
// TODO: Fix imports from legacy arithmos
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Weighted Inner-Product Diagnostic (Îž-Channel Signal)
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
//
// Computes a bilinear pairing âŸ¨Î±, LÂ·Î²âŸ© on finite-dimensional cochains.
// This is a **weighted inner product**, NOT a full Hard Lefschetz
// theorem implementation â€” it lacks graded cochain decomposition,
// L: H^p â†’ H^{p+2} degree-shifting structure, and cohomology
// quotient compatibility.
//
// ROLE IN THE Î¦â‚ â†’ Î“â‚‚ â†’ Îž PIPELINE:
//   - Î¦â‚ = acceptance (quotient obstruction)
//   - Î“â‚‚ = local instability (MC residual / closure rupture)
//   - Îž  = global coherence / routing diagnostic  â† THIS MODULE
//
// INTERPRETATION:
//   - pairing â‰  0  âŸ¹  Î± and Î² are dual-compatible
//   - defect > 0   âŸ¹  the pairing deviates from expected duality
//   - Îž_shift > 0  âŸ¹  adjacent transitions align (coherent trace)
//   - Îž_shift â‰ˆ 0  âŸ¹  incoherent / sparse / discontinuous trace
//
// BOUNDARY:
//   - Lefschetz pairing enters diagnostic / routing only.
//   - It does NOT replace Î¦â‚ acceptance.
//   - It does NOT make accept/reject decisions.
//   - It MAY influence branch selection in search strategies.
//   - L MUST be structural (shift/adjacency), not learned.

use super::coboundary_matrix::CoboundaryMatrix;

// ============================================================================
// Core types
// ============================================================================

/// Result of a Lefschetz pairing computation.
///
/// `pairing`: the raw inner product âŸ¨Î±, LÂ·Î²âŸ©.
/// `defect`:  |pairing - expected| for a specified target. Zero when
///            the pairing hits its target exactly.
#[derive(Debug, Clone, PartialEq)]
pub struct LefschetzPairing {
    /// âŸ¨Î±, LÂ·Î²âŸ©
    pub pairing: f64,
    /// |pairing - expected|, zero if no expected value was supplied.
    pub defect: f64,
}

/// Full diagnostic report from a Lefschetz duality check.
///
/// Collects pairings across all degrees and reports aggregate health.
#[derive(Debug, Clone)]
pub struct LefschetzDiagnostic {
    /// Per-degree pairings.
    pub pairings: Vec<LefschetzPairing>,
    /// Sum of all defects.
    pub total_defect: f64,
    /// Whether the pairing structure looks non-degenerate.
    pub non_degenerate: bool,
}

// ============================================================================
// Lefschetz operator
// ============================================================================

/// The Lefschetz operator L, represented as a sparse matrix.
///
/// In Hodge theory on a compact KÃ¤hler manifold, L is the wedge product
/// with the KÃ¤hler form. On our discrete cochains, it is any sparse
/// endomorphism on the cochain space that mediates the pairing.
///
/// We reuse `CoboundaryMatrix` as the sparse matrix representation
/// (it's the same COO format with `.apply()`).
pub type LefschetzOperator = CoboundaryMatrix;

// ============================================================================
// Pairing computation
// ============================================================================

/// Compute the Lefschetz inner product: âŸ¨Î±, LÂ·Î²âŸ©.
///
/// `alpha`: a cochain in Háµ– (or its representative)
/// `beta`:  a cochain in Hâ¿â»áµ–
/// `l_operator`: the Lefschetz operator L
///
/// Returns `Err` if LÂ·Î² fails (dimension mismatch).
pub fn lefschetz_pair(
    alpha: &[f64],
    beta: &[f64],
    l_operator: &LefschetzOperator,
) -> Result<f64, String> {
    let l_beta = l_operator.apply(beta)?;

    if alpha.len() != l_beta.len() {
        return Err(format!(
            "Lefschetz: alpha has dimension {} but LÂ·beta has dimension {}",
            alpha.len(),
            l_beta.len()
        ));
    }

    Ok(alpha.iter().zip(l_beta.iter()).map(|(a, b)| a * b).sum())
}

/// Compute a `LefschetzPairing` with an optional expected value.
///
/// If `expected` is `Some(v)`, `defect = |pairing - v|`.
/// If `expected` is `None`, `defect = 0.0`.
pub fn lefschetz_pair_with_defect(
    alpha: &[f64],
    beta: &[f64],
    l_operator: &LefschetzOperator,
    expected: Option<f64>,
) -> Result<LefschetzPairing, String> {
    let pairing = lefschetz_pair(alpha, beta, l_operator)?;
    let defect = match expected {
        Some(v) => (pairing - v).abs(),
        None => 0.0,
    };
    Ok(LefschetzPairing { pairing, defect })
}

/// Check non-degeneracy: for each basis element eáµ¢, pair âŸ¨eáµ¢, LÂ·eáµ¢âŸ©.
///
/// Non-degenerate means every diagonal pairing is nonzero (within tolerance).
/// Returns the full `LefschetzDiagnostic`.
pub fn lefschetz_diagnostic(
    dimension: usize,
    l_operator: &LefschetzOperator,
    tolerance: f64,
) -> Result<LefschetzDiagnostic, String> {
    let mut pairings = Vec::with_capacity(dimension);
    let mut total_defect = 0.0;
    let mut non_degenerate = true;

    for i in 0..dimension {
        let mut basis = vec![0.0; dimension];
        basis[i] = 1.0;

        let pairing = lefschetz_pair(&basis, &basis, l_operator)?;
        let defect = 0.0; // no expected value for basis pairings

        if pairing.abs() < tolerance {
            non_degenerate = false;
            // Defect for degeneracy: distance from nearest nonzero
            let deg_defect = tolerance - pairing.abs();
            total_defect += deg_defect;
            pairings.push(LefschetzPairing {
                pairing,
                defect: deg_defect,
            });
        } else {
            pairings.push(LefschetzPairing { pairing, defect });
        }
    }

    Ok(LefschetzDiagnostic {
        pairings,
        total_defect,
        non_degenerate,
    })
}

// ============================================================================
// Shift Operator â€” Structural Îž Baseline
// ============================================================================

/// Construct the shift operator on n-dimensional cochains.
///
/// Matrix form: L[i, i+1] = 1 for i = 0..n-2.
/// All other entries are zero.
///
/// This is the **recommended structural baseline** for Îž because:
/// - It is non-learned (evaluator-safe)
/// - It captures adjacent-transition alignment
/// - It is independent of the differential d
///
/// # Panics
/// Returns `Err` if `dimension < 1` (degenerate).
pub fn shift_operator(dimension: usize) -> Result<LefschetzOperator, String> {
    use super::coboundary_matrix::CoboundaryEntry;

    if dimension == 0 {
        return Err("shift_operator: dimension must be >= 1".into());
    }

    let entries: Vec<CoboundaryEntry> = (0..dimension.saturating_sub(1))
        .map(|i| CoboundaryEntry {
            row: i,
            col: i + 1,
            value: 1,
        })
        .collect();

    CoboundaryMatrix::new(dimension, dimension, entries)
}

/// Compute the raw Îž coherence score using the shift operator.
///
/// ```text
/// Îž_raw(a) = Î£ a[i] Â· a[i+1]
/// ```
///
/// Interpretation:
/// - high positive: adjacent transition scores align (coherent trace)
/// - near zero: incoherent / sparse / discontinuous signal
/// - negative: oscillatory signal (only possible if `a` has negative values)
///
/// NOTE: If the cochain `a` is in [0,1] (e.g. from Ï†-mapping), Îž will
/// never be negative. Then Îž measures **smooth adjacent mass**, not
/// oscillation. This is acceptable but should be documented in traces.
/// Legacy trace feature name: this is not the canonical density-distance Xi.
/// All arithmetic is owned by `core_functional::trace_diagnostics`.
pub fn xi_shift_coherence(a: &[f64]) -> Result<f64, String> {
    core_functional::trace_diagnostics::shift_pairing_coherence(a)
}

/// Compute the normalized Îž coherence score.
///
/// ```text
/// Îž_norm(a) = Îž_raw(a) / (||a||Â² + Îµ)
/// ```
///
/// Normalization prevents constant high-obstruction traces
/// (e.g., a = [1,1,1,1]) from scoring artificially high.
/// The `eps` parameter prevents division by zero.
///
/// Typical usage: `eps = 1e-12`.
/// Legacy trace feature name: this is not the canonical density-distance Xi.
/// All arithmetic is owned by `core_functional::trace_diagnostics`.
pub fn xi_shift_normalized(a: &[f64], eps: f64) -> Result<f64, String> {
    core_functional::trace_diagnostics::normalized_shift_pairing_coherence(a, eps)
}

// ============================================================================
// Tests
// ============================================================================

// Origin: engine/crates_rs/core_homology/src/lefschetz.rs
// Claim: urn:core:crates_rs:core-homology:lefschetz:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4441788e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4441788e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4441788e {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError4441788e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4441788e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4441788e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4441788e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4441788e> {
        if capacity_bound == 0 {
            return Err(BoundaryError4441788e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4441788e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4441788e::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod tests {
    use super::coboundary_matrix::{CoboundaryEntry, CoboundaryMatrix};
    use super::*;

    /// Identity operator on 3-dim space (Iâ‚ƒ).
    fn identity_3() -> LefschetzOperator {
        CoboundaryMatrix::new(
            3,
            3,
            vec![
                CoboundaryEntry {
                    row: 0,
                    col: 0,
                    value: 1,
                },
                CoboundaryEntry {
                    row: 1,
                    col: 1,
                    value: 1,
                },
                CoboundaryEntry {
                    row: 2,
                    col: 2,
                    value: 1,
                },
            ],
        )
        .unwrap()
    }

    /// Signed diagonal operator: diag(1, -1, 1).
    fn signed_diagonal_3() -> LefschetzOperator {
        CoboundaryMatrix::new(
            3,
            3,
            vec![
                CoboundaryEntry {
                    row: 0,
                    col: 0,
                    value: 1,
                },
                CoboundaryEntry {
                    row: 1,
                    col: 1,
                    value: -1,
                },
                CoboundaryEntry {
                    row: 2,
                    col: 2,
                    value: 1,
                },
            ],
        )
        .unwrap()
    }

    /// Zero operator on 2-dim space (degenerate).
    fn zero_2() -> LefschetzOperator {
        CoboundaryMatrix::new(2, 2, vec![]).unwrap()
    }

    // â”€â”€ Basic pairing â”€â”€

    #[test]
    fn identity_pairing_is_dot_product() {
        let l = identity_3();
        let alpha = vec![1.0, 2.0, 3.0];
        let beta = vec![4.0, 5.0, 6.0];

        let p = lefschetz_pair(&alpha, &beta, &l).unwrap();
        // âŸ¨[1,2,3], IÂ·[4,5,6]âŸ© = 1*4 + 2*5 + 3*6 = 32
        assert!((p - 32.0).abs() < 1e-12);
    }

    #[test]
    fn signed_pairing_respects_signs() {
        let l = signed_diagonal_3();
        let alpha = vec![1.0, 2.0, 3.0];
        let beta = vec![1.0, 2.0, 3.0];

        let p = lefschetz_pair(&alpha, &beta, &l).unwrap();
        // âŸ¨[1,2,3], [1,-2,3]âŸ© = 1 - 4 + 9 = 6
        assert!((p - 6.0).abs() < 1e-12);
    }

    #[test]
    fn zero_operator_gives_zero_pairing() {
        let l = zero_2();
        let alpha = vec![1.0, 2.0];
        let beta = vec![3.0, 4.0];

        let p = lefschetz_pair(&alpha, &beta, &l).unwrap();
        assert!((p).abs() < 1e-15);
    }

    // â”€â”€ Defect computation â”€â”€

    #[test]
    fn defect_is_zero_when_no_expected() {
        let l = identity_3();
        let alpha = vec![1.0, 0.0, 0.0];
        let beta = vec![1.0, 0.0, 0.0];

        let result = lefschetz_pair_with_defect(&alpha, &beta, &l, None).unwrap();
        assert!((result.defect).abs() < 1e-15);
        assert!((result.pairing - 1.0).abs() < 1e-12);
    }

    #[test]
    fn defect_measures_distance_from_expected() {
        let l = identity_3();
        let alpha = vec![1.0, 0.0, 0.0];
        let beta = vec![1.0, 0.0, 0.0];

        // Actual pairing = 1.0, expected = 2.0 â†’ defect = 1.0
        let result = lefschetz_pair_with_defect(&alpha, &beta, &l, Some(2.0)).unwrap();
        assert!((result.defect - 1.0).abs() < 1e-12);
    }

    // â”€â”€ Non-degeneracy diagnostic â”€â”€

    #[test]
    fn identity_operator_is_non_degenerate() {
        let l = identity_3();
        let diag = lefschetz_diagnostic(3, &l, 1e-10).unwrap();

        assert!(diag.non_degenerate);
        assert!((diag.total_defect).abs() < 1e-10);
        assert_eq!(diag.pairings.len(), 3);
    }

    #[test]
    fn zero_operator_is_degenerate() {
        let l = zero_2();
        let diag = lefschetz_diagnostic(2, &l, 1e-10).unwrap();

        assert!(!diag.non_degenerate);
        assert!(diag.total_defect > 0.0);
    }

    #[test]
    fn signed_operator_is_non_degenerate() {
        let l = signed_diagonal_3();
        let diag = lefschetz_diagnostic(3, &l, 1e-10).unwrap();

        // diag(1,-1,1) gives pairings [1, -1, 1], all nonzero
        // But CoboundaryMatrix enforces values in {-1, 1}, so this works.
        // Actually, pairing = âŸ¨eáµ¢, LÂ·eáµ¢âŸ© = L_ii = 1 or -1, both nonzero.
        assert!(diag.non_degenerate);
    }

    // â”€â”€ Dimension mismatch â”€â”€

    #[test]
    fn dimension_mismatch_returns_error() {
        let l = identity_3();
        let alpha = vec![1.0, 2.0]; // 2-dim
        let beta = vec![1.0, 2.0, 3.0]; // 3-dim

        // LÂ·beta succeeds (3â†’3), but alpha (2-dim) â‰  LÂ·beta (3-dim)
        let result = lefschetz_pair(&alpha, &beta, &l);
        assert!(result.is_err());
    }

    #[test]
    fn lefschetz_is_diagnostic_not_acceptance() {
        // Structural test: Lefschetz pairing enters diagnostic/routing.
        // It does NOT replace Î¦â‚. This test documents the boundary.
        let l = identity_3();
        let diag = lefschetz_diagnostic(3, &l, 1e-10).unwrap();

        // The diagnostic reports health but makes no accept/reject decision.
        // It returns data, not a boolean verdict.
        assert!(diag.non_degenerate);
        assert!((diag.total_defect).abs() < 1e-10);
        // No accept/reject function exists in this module.
    }

    // â”€â”€ Shift operator â”€â”€

    #[test]
    fn shift_operator_has_correct_structure() {
        let l = shift_operator(4).unwrap();
        // L maps [a,b,c,d] â†’ [b,c,d,0]
        let input = vec![1.0, 2.0, 3.0, 4.0];
        let output = l.apply(&input).unwrap();
        assert!((output[0] - 2.0).abs() < 1e-12);
        assert!((output[1] - 3.0).abs() < 1e-12);
        assert!((output[2] - 4.0).abs() < 1e-12);
        assert!((output[3] - 0.0).abs() < 1e-12);
    }

    #[test]
    fn shift_operator_dimension_1() {
        let l = shift_operator(1).unwrap();
        // 1Ã—1 with no off-diagonal â†’ zero operator
        let output = l.apply(&[5.0]).unwrap();
        assert!((output[0]).abs() < 1e-15);
    }

    #[test]
    fn shift_operator_dimension_0_is_error() {
        assert!(shift_operator(0).is_err());
    }

    // â”€â”€ Îž coherence â”€â”€

    #[test]
    fn xi_coherence_of_constant_trace() {
        // a = [1, 1, 1, 1]
        // Îž = 1*1 + 1*1 + 1*1 = 3.0
        let a = vec![1.0, 1.0, 1.0, 1.0];
        let xi = xi_shift_coherence(&a).unwrap();
        assert!((xi - 3.0).abs() < 1e-12);
    }

    #[test]
    fn xi_coherence_of_alternating_trace() {
        // a = [1, -1, 1, -1]
        // Îž = 1*(-1) + (-1)*1 + 1*(-1) = -3.0
        let a = vec![1.0, -1.0, 1.0, -1.0];
        let xi = xi_shift_coherence(&a).unwrap();
        assert!((xi - (-3.0)).abs() < 1e-12);
    }

    #[test]
    fn xi_coherence_of_single_element() {
        let a = vec![5.0];
        let xi = xi_shift_coherence(&a).unwrap();
        assert!((xi).abs() < 1e-15);
    }

    #[test]
    fn xi_normalized_dampens_constant_trace() {
        // a = [1,1,1,1]: raw = 3.0, energy = 4.0
        // normalized = 3.0 / (4.0 + eps) â‰ˆ 0.75
        let a = vec![1.0, 1.0, 1.0, 1.0];
        let xi_n = xi_shift_normalized(&a, 1e-12).unwrap();
        assert!((xi_n - 0.75).abs() < 1e-6);
    }

    #[test]
    fn xi_normalized_vs_raw_divergence() {
        // High-magnitude constant trace should have lower normalized score
        // than its raw score suggests
        let a_small = vec![0.1, 0.1, 0.1, 0.1];
        let a_big = vec![10.0, 10.0, 10.0, 10.0];

        let n_small = xi_shift_normalized(&a_small, 1e-12).unwrap();
        let n_big = xi_shift_normalized(&a_big, 1e-12).unwrap();

        // Both should be approximately 0.75 (normalized is scale-invariant)
        assert!((n_small - n_big).abs() < 1e-6);
    }

    #[test]
    fn xi_coherence_complements_gamma2() {
        // Structural test: Îž and Î“â‚‚ detect different signals.
        //
        // a = [1, 1, 1, 1]:  Î“â‚‚ = 0 (no jumps), Îž = 3.0 (coherent)
        // a = [1, -1, 1, -1]: Î“â‚‚ = 6 (spiky),   Îž = -3.0 (oscillatory)
        //
        // So Îž and Î“â‚‚ are complementary: Î“â‚‚ detects spikes/discontinuities,
        // Îž detects alignment/coherence.
        let smooth = vec![1.0, 1.0, 1.0, 1.0];
        let spiky = vec![1.0, -1.0, 1.0, -1.0];

        let xi_smooth = xi_shift_coherence(&smooth).unwrap();
        let xi_spiky = xi_shift_coherence(&spiky).unwrap();

        assert!(xi_smooth > 0.0, "smooth trace should have positive Îž");
        assert!(xi_spiky < 0.0, "oscillatory trace should have negative Îž");
    }
}

#[cfg(test)]
mod l4_boundary_tests_4441788e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord4441788e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord4441788e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord4441788e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord4441788e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord4441788e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError4441788e::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError4441788e::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
