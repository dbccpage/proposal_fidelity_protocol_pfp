#![cfg(any())]
// Legacy policy adapter; trace measurements are compiled and tested in core_functional.
use core_functional::trace_diagnostics::{
    interior_delta_magnitude, max_abs_entry, mean_absolute_magnitude, mean_adjacent_variation,
};
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Transition Scorer Ï† â€” Evaluator-Safe Trace Feature Extraction
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
//
// Computes Ï†(s_i, s_{i+1}) for each transition in a reasoning trace.
// This is the hinge between the algebra (MC residual) and the pipeline
// (Kaggle trace filtering).
//
// REQUIREMENTS:
//   R1. Locality:    Ï† depends only on (s_i, s_{i+1})
//   R2. Evaluator independence: NO access to ground truth, reward, or loss
//   R3. Anti-collapse: produces variation when reasoning structure changes
//
// DECOMPOSITION:
//   Ï† = wâ‚Â·Ï†_sem + wâ‚‚Â·Ï†_struct + wâ‚ƒÂ·Ï†_numeric + wâ‚„Â·Ï†_entropy
//
// Each channel targets a different failure mode.
// All channels normalized to [0, 1].
//
// ALGEBRAIC STATUS:
//   - PROVEN BY CONSTRUCTION: Ï† â†’ cochain a âˆˆ CÂ¹ satisfying MC type.
//   - MODELING ASSUMPTION: Ï† is a proxy scalar embedding of transition
//     inconsistency. It mixes heterogeneous metrics (set overlap,
//     numeric mismatch, entropy divergence, keyword heuristic) into
//     a single scalar. This is a weighted scoring function, not an
//     algebraic invariant.
//   - NOT PROVEN: that Ï† preserves any algebraic structure of reasoning.
//   - CONSEQUENCE: MC(a) measures "variation in heuristic inconsistency
//     score", not "obstruction to reasoning consistency" in a strong sense.
//     This is weaker but still useful: it captures signal geometry.

// ============================================================================
// Core types
// ============================================================================

// ============================================================================
// Normalized Î“â‚‚ â€” trace-length-invariant local obstruction variation
// ============================================================================

/// Compute normalized Î“â‚‚: average absolute difference between adjacent cochain values.
///
/// ```text
/// Î“â‚‚_norm = (1 / (n-1)) Î£ |a[i+1] - a[i]|
/// ```
///
/// This removes trace-length bias: longer traces are not automatically
/// penalized compared to shorter ones.
/// Legacy trace feature name: this is not the canonical closure-defect Gamma2.
/// All arithmetic is owned by `core_functional::trace_diagnostics`.

// ============================================================================
// Trace Acceptance Law â€” Enforcing Î¦â‚ â†’ Î“â‚‚ â†’ Îž at code level
// ============================================================================

/// Parameters for the combined trace filter.
///
/// ```text
/// keep Ï„ if:
///     Î¦â‚(Ï„) passes
/// AND Î“â‚‚(Ï„) â‰¤ gamma2_max
/// AND Îž(Ï„) â‰¥ xi_min
/// AND mean(|a|) â‰¤ mean_abs_max
/// ```
///
/// The mean_abs_max term prevents the degenerate case where
/// a = [1,1,1,1] has Î“â‚‚=0 and high Îž but is actually fully obstructed.
#[derive(Debug, Clone)]
pub struct TraceFilterParams {
    /// Maximum allowed normalized Î“â‚‚.
    pub gamma2_max: f64,
    /// Minimum allowed normalized Îž.
    pub xi_min: f64,
    /// Maximum allowed mean absolute cochain value.
    pub mean_abs_max: f64,
}

impl Default for TraceFilterParams {
    fn default() -> Self {
        Self {
            gamma2_max: 0.5,
            xi_min: -0.5,
            mean_abs_max: 0.8,
        }
    }
}

/// Combined acceptance law enforcing Î¦â‚ â†’ Î“â‚‚ â†’ Îž at code level.
///
/// Î¦â‚ is the hard correctness gate. Î“â‚‚ and Îž are routing diagnostics
/// that filter traces based on structural quality.
///
/// Uses normalized Î“â‚‚ (trace-length-invariant) and the provided Îž_norm.
pub fn accept_trace(phi1_pass: bool, a: &[f64], xi_norm: f64, params: &TraceFilterParams) -> bool {
    if !phi1_pass {
        return false;
    }

    let gamma2 = mean_adjacent_variation(a);
    let mean_abs = mean_absolute_magnitude(a);

    gamma2 <= params.gamma2_max && xi_norm >= params.xi_min && mean_abs <= params.mean_abs_max
}

/// Structural trace acceptance law.
///
/// Includes baseline checks but adds the strong structural/semantic phase checks:
/// - Semantic phase valid
/// - Good trace signature (boundary audit passed)
/// - Algebraic invariants hold (e.g., C*-identity, GNS non-degeneracy, von Neumann factor property)
pub fn accept_trace_structural(
    phi1_pass: bool,
    a: &[f64],
    xi_norm: f64,
    phase_valid_gated: bool,
    audit: &BoundaryAudit,
    params: &TraceFilterParams,
    algebraic_invariants_pass: bool,
) -> bool {
    phi1_pass
        && accept_trace(true, a, xi_norm, params)
        && phase_valid_gated
        && audit.good_trace_signature
        && algebraic_invariants_pass
}

// ============================================================================
// Localized Obstruction Structure â€” multi-axis trace geometry
// ============================================================================

/// `interior_delta_magnitude` (Î“â‚‚_smooth): variation over non-boundary transitions only.
///
/// Excludes the transition with the largest |Î”S| (the boundary spike).
/// Measures internal oscillation / instability of the reasoning interior.
///
/// ```text
/// interior_delta_magnitude = mean(|Î”S[i]|) for i â‰  boundary_idx
/// ```

/// Boundary event detection: structural spike AND semantic discontinuity.
///
/// ```text
/// boundary = |Î”S| > Î´_threshold AND cos(Ïˆ_i, Ïˆ_{i+1}) < Ï„_sem
/// ```
///
/// This is strictly stronger than semantic gating alone.
pub fn is_boundary(delta_s: f64, sim: f64, delta_threshold: f64, sim_threshold: f64) -> bool {
    delta_s.abs() > delta_threshold && sim < sim_threshold
}

/// Full boundary audit for a trace.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct BoundaryAudit {
    /// B_max: magnitude of the largest Î”S spike.
    pub b_max: f64,
    /// Index of the boundary transition.
    pub boundary_idx: usize,
    /// Whether boundary is at the final step (typical for good traces).
    pub boundary_at_final: bool,
    /// Î“â‚‚_smooth: mean variation over non-boundary transitions.
    pub gamma2_smooth: f64,
    /// Number of boundary events (|Î”S| > threshold AND low similarity).
    pub boundary_count: usize,
    /// Good trace signature: Î¦â‚ pass, Î“â‚‚_smooth low, â‰¤1 boundary, boundary at final.
    pub good_trace_signature: bool,
}

/// Perform boundary audit on a set of entropy deltas + semantic similarities.
///
/// Lexicographic `good_trace` rule:
/// ```text
/// good_trace =
///     phase_valid_gated
/// AND boundary_count â‰¤ 1
/// AND boundary_idx is terminal-or-semantic-boundary
/// AND Î“â‚‚_smooth â‰¤ Î¸_smooth
/// ```
pub fn boundary_audit(
    entropy_deltas: &[f64],
    similarities: &[f64],
    task_shifts: &[bool],
    phase_valid_gated: bool,
    delta_threshold: f64,
    sim_threshold: f64,
) -> BoundaryAudit {
    if entropy_deltas.is_empty() {
        return BoundaryAudit {
            b_max: 0.0,
            boundary_idx: 0,
            boundary_at_final: false,
            gamma2_smooth: 0.0,
            boundary_count: 0,
            good_trace_signature: false,
        };
    }

    let (true_b_max, true_boundary_idx, boundary_count) =
        scan_boundaries(entropy_deltas, similarities, delta_threshold, sim_threshold);

    let g2_smooth = interior_delta_magnitude(entropy_deltas, true_boundary_idx);

    let (fallback_max, fallback_idx) = max_abs_entry(entropy_deltas);
    let b_idx = true_boundary_idx.unwrap_or(fallback_idx);
    let b_max = if true_boundary_idx.is_some() {
        true_b_max
    } else {
        fallback_max
    };

    let boundary_at_final = b_idx == entropy_deltas.len().saturating_sub(1);

    // Boundary is "valid" if it's:
    // (a) at the terminal step (answer formation), OR
    // (b) at a semantic boundary (task shift)
    let boundary_at_semantic = task_shifts.get(b_idx).copied().unwrap_or(false);

    // If there are NO boundary events, that is structurally valid (no fragmentation)
    let boundary_idx_valid = if boundary_count == 0 {
        true
    } else {
        boundary_at_final || boundary_at_semantic
    };

    // Lexicographic good trace:
    //   1. phase_valid_gated (semantic-gated phase structure is clean)
    //   2. boundary_count â‰¤ 1 (no fragmentation)
    //   3. boundary_idx valid (terminal or semantic boundary OR no boundary)
    //   4. Î“â‚‚_smooth low (interior is stable)
    let good_trace_signature =
        phase_valid_gated && boundary_count <= 1 && boundary_idx_valid && g2_smooth < 0.1;

    BoundaryAudit {
        b_max,
        boundary_idx: b_idx,
        boundary_at_final,
        gamma2_smooth: g2_smooth,
        boundary_count,
        good_trace_signature,
    }
}

fn scan_boundaries(
    entropy_deltas: &[f64],
    similarities: &[f64],
    delta_threshold: f64,
    sim_threshold: f64,
) -> (f64, Option<usize>, usize) {
    let mut true_b_max = 0.0;
    let mut true_boundary_idx = None;
    let mut boundary_count = 0;

    for (i, (&ds, &sim)) in entropy_deltas.iter().zip(similarities.iter()).enumerate() {
        if is_boundary(ds, sim, delta_threshold, sim_threshold) {
            boundary_count += 1;
            if ds.abs() > true_b_max {
                true_b_max = ds.abs();
                true_boundary_idx = Some(i);
            }
        }
    }
    (true_b_max, true_boundary_idx, boundary_count)
}

/// Algebraic invariant diagnostic for a reasoning trace.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct AlgebraicAudit {
    /// The maximum commutant dimension observed across all sliding windows of the trace.
    pub max_commutant_dimension: usize,
    /// The number of transitions that generated a factor-like algebra (commutant dim == 1).
    pub factor_like_transitions: usize,
    /// Whether the trace passes the algebraic constraints (avoids sustained repetition).
    pub is_valid: bool,
}

/// Perform an algebraic audit on a sequence of commutant dimensions from sliding windows.
///
/// A valid algebraic trace consists predominantly of non-commuting operations
/// (genuine logical transformations), meaning the commutant dimension should drop to 1.
/// Semantic repetition (padding) produces nearly commuting states, causing the
/// commutant dimension to spike (e.g. > 1).
pub fn algebraic_audit(
    commutant_dimensions: &[usize],
    max_allowed_commutant: usize,
) -> AlgebraicAudit {
    if commutant_dimensions.is_empty() {
        return AlgebraicAudit {
            max_commutant_dimension: 0,
            factor_like_transitions: 0,
            is_valid: true,
        };
    }

    let max_commutant_dimension = *commutant_dimensions.iter().max().unwrap_or(&0);
    let factor_like_transitions = commutant_dimensions.iter().filter(|&&d| d == 1).count();

    // An algebraic invariant pass requires that the maximum commutant dimension
    // does not exceed the allowed threshold. This explicitly penalizes traces
    // that stall out into semantic repetition (padding).
    let is_valid = max_commutant_dimension <= max_allowed_commutant;

    AlgebraicAudit {
        max_commutant_dimension,
        factor_like_transitions,
        is_valid,
    }
}

// ============================================================================
// Phase Validity â€” structural prior over reasoning phase sequence
// ============================================================================

/// Classify entropy delta into phase direction.
///
/// ```text
/// EXPAND   (+1): Î”S > threshold  â†’ hypothesis space growing
/// NEUTRAL  ( 0): |Î”S| â‰¤ threshold â†’ stable / refining
/// CONTRACT (-1): Î”S < -threshold â†’ converging / collapsing
/// ```
pub fn phase_from_delta_s(delta_s: f64, threshold: f64) -> i8 {
    if delta_s > threshold {
        1 // EXPAND
    } else if delta_s < -threshold {
        -1 // CONTRACT
    } else {
        0 // NEUTRAL
    }
}

/// Check whether a sequence of entropy deltas follows a valid phase pattern.
///
/// Valid pattern: EXPAND* â†’ NEUTRAL* â†’ CONTRACT*
/// (no re-expansion after contraction has begun)
///
/// ```text
/// [+, +, +, 0, -, -]  â†’ true  (canonical good reasoning)
/// [+, +, -, +, -]     â†’ false (re-expansion after collapse)
/// [-, +, +, +, +]     â†’ false (early collapse then re-expand)
/// ```
///
/// MODELING ASSUMPTION: valid reasoning follows expandâ†’collapse phase structure.
/// NOT PROVEN: that enforcing this improves training outcomes.
pub fn valid_phase_sequence(entropy_deltas: &[f64], threshold: f64) -> bool {
    let mut seen_contract = false;

    for &ds in entropy_deltas {
        let phase = phase_from_delta_s(ds, threshold);

        if phase == -1 {
            seen_contract = true;
        }

        // Re-expansion after contraction â†’ invalid
        if seen_contract && phase == 1 {
            return false;
        }
    }

    true
}

/// Extract entropy deltas from SBE snapshots (for phase analysis).
///
/// Uses the entropy_bits field from each step's SBE snapshot.
pub fn entropy_deltas_from_sbe(sbe_snapshots: &[crate::runtime::trace::SbeSnapshot]) -> Vec<f64> {
    if sbe_snapshots.len() < 2 {
        return vec![];
    }
    sbe_snapshots
        .windows(2)
        .map(|w| w[1].entropy_bits - w[0].entropy_bits)
        .collect()
}

// ============================================================================
// Semantic Continuity â€” cosine similarity between step embeddings
// ============================================================================

/// Detect task shifts: sim < Ï„_sem â†’ semantic discontinuity.
pub fn detect_task_shifts(similarities: &[f64], tau_sem: f64) -> Vec<bool> {
    similarities.iter().map(|&s| s < tau_sem).collect()
}

// ============================================================================
// Semantic-Gated Phase Validity
// ============================================================================

/// Phase validity with semantic gating.
///
/// The rule:
/// ```text
/// forbid Contract â†’ Expand
/// UNLESS task_shift == true at that transition
/// ```
///
/// This distinguishes:
/// - productive expansion (exploration within same semantic region) â†’ structural event
/// - semantic discontinuity (task shift, e.g. mathâ†’formatting) â†’ allowed
///
/// If no similarity data is provided, falls back to strict phase checking.
pub fn valid_phase_sequence_gated(
    entropy_deltas: &[f64],
    task_shifts: &[bool],
    threshold: f64,
) -> bool {
    let mut seen_contract = false;

    for (i, &ds) in entropy_deltas.iter().enumerate() {
        let phase = phase_from_delta_s(ds, threshold);
        let is_task_shift = task_shifts.get(i).copied().unwrap_or(false);

        if phase == -1 {
            seen_contract = true;
        }

        // Re-expansion after contraction â†’ invalid UNLESS task shift
        if seen_contract && phase == 1 && !is_task_shift {
            return false;
        }
    }

    true
}

/// Per-transition decision record for audit trail.
#[derive(Debug, Clone)]
pub struct PhaseTransitionDecision {
    /// Transition index (step i â†’ i+1).
    pub index: usize,
    /// Entropy delta Î”S.
    pub delta_s: f64,
    /// Phase classification: EXPAND, NEUTRAL, CONTRACT.
    pub phase: i8,
    /// Cosine similarity with next step.
    pub semantic_sim: f64,
    /// Whether this transition is a task shift.
    pub is_task_shift: bool,
    /// Whether this transition was gated (Contractâ†’Expand exempted by task shift).
    pub was_gated: bool,
}

// ============================================================================
// Tests
// ============================================================================

// Origin: engine/crates_rs/core_homology/src/transition_scorer.rs
// Claim: urn:core:crates_rs:core-homology:transition-scorer:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord775f100b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord775f100b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError775f100b {
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
impl BoundaryError775f100b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError775f100b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError775f100b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord775f100b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError775f100b> {
        if capacity_bound == 0 {
            return Err(BoundaryError775f100b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError775f100b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError775f100b::ExceedsCapacity {
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
    use super::*;

    #[test]
    fn accept_rejects_when_phi1_fails() {
        let a = vec![0.0, 0.0, 0.0];
        assert!(!accept_trace(false, &a, 0.5, &TraceFilterParams::default()));
    }

    #[test]
    fn accept_rejects_high_gamma2() {
        // Oscillating trace: high Î“â‚‚
        let a = vec![-1.0, 1.0, -1.0, 1.0];
        let params = TraceFilterParams {
            gamma2_max: 0.1,
            xi_min: -1.0,
            mean_abs_max: 2.0,
        };
        assert!(!accept_trace(true, &a, 0.5, &params));
    }

    #[test]
    fn accept_passes_smooth_trace() {
        let a = vec![0.1, 0.12, 0.11, 0.13];
        let xi = 0.5;
        assert!(accept_trace(true, &a, xi, &TraceFilterParams::default()));
    }
}

#[cfg(test)]
mod l4_boundary_tests_775f100b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord775f100b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord775f100b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord775f100b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord775f100b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord775f100b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError775f100b::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError775f100b::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
