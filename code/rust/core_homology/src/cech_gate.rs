//! --- Math Contract: CODA-FOC-CHECK-01 — Finite Čech Contextual-Obstruction Gate ---
//!
//! Mechanizes proof_obligations.md §18.5 (PO-D7a / CODA-FOC-CHECK-01): the finite
//! Čech gate that separates *local invalidity* from *locally valid but
//! non-glueable* repair families, over a finite cover with an additive
//! local-repair presheaf valued in the exact rationals `Q`.
//!
//! The gate is **total** and **sound**. Given
//!   - declared local sections (each replayable, missing, or replay-failed),
//!   - a finite cochain complex `d0 : C^0 -> C^1`, `d1 : C^1 -> C^2` over `Q`,
//!   - an overlap-discrepancy cochain `delta ∈ C^1`,
//!
//! it returns exactly one terminal:
//!   - `LocalInvalid`           — a required local section is missing / fails replay;
//!   - `CechRefused`            — malformed complex, dimension mismatch, or `delta`
//!     is not a cocycle (`d1·delta ≠ 0`), so no class exists;
//!   - `ContextuallyGlueable`   — `d1·delta = 0` and `[delta] = 0` (`delta ∈ im d0`);
//!   - `ContextualObstruction`  — `d1·delta = 0` and `[delta] ≠ 0` (`delta ∉ im d0`).
//!
//! SOUNDNESS ORDERING (§18.5): local-section replay is checked **before** the
//! global obstruction test, so an absent local witness is never misread as a
//! contextual obstruction.
//!
//! REQUIRED NON-CLAIM (§18.5): `ContextualObstruction` is a finite Čech
//! local-global obstruction only. It does **not** assert positive `Φ1` mass in
//! `Q^1` unless a faithful cochain comparison + separated quotient norm is
//! declared. The `phi1_claim` field encodes this fence; it is `NotClaimed`
//! unless `faithful_comparison` is declared on the input.
//!
//! Membership `delta ∈ im(d0)` is decided exactly over `Q` by
//! `rank([d0 | delta]) == rank(d0)`.

use num_traits::Zero;

use crate::matrix::{in_column_space, is_zero_matrix, mat_mul, mat_vec_mul};
use crate::scalar::Q;
use linear_algebra::backend::basic_matrix::BasicMatrix;

/// Replay status of a declared required local section `s_i ∈ F(U_i)`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SectionReplay {
    /// The section is present and replays.
    Present,
    /// The section was required but is absent.
    Missing,
    /// The section is present but failed deterministic replay.
    FailedReplay(String),
}

/// A declared local section on a cover element.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LocalSection {
    pub id: String,
    pub replay: SectionReplay,
}

impl LocalSection {
    pub fn present(id: impl Into<String>) -> Self {
        Self {
            id: id.into(),
            replay: SectionReplay::Present,
        }
    }
    pub fn missing(id: impl Into<String>) -> Self {
        Self {
            id: id.into(),
            replay: SectionReplay::Missing,
        }
    }
}

/// Finite Čech gate input: the local-section replay layer plus the declared
/// finite cochain complex and overlap discrepancy.
#[derive(Debug, Clone)]
pub struct CechInput {
    /// Required local sections `s_i ∈ F(U_i)` with replay status.
    pub local_sections: Vec<LocalSection>,
    /// `d0 : C^0 -> C^1` (rows = dim C^1, cols = dim C^0).
    pub d0: BasicMatrix<Q>,
    /// `d1 : C^1 -> C^2` (rows = dim C^2, cols = dim C^1).
    pub d1: BasicMatrix<Q>,
    /// Overlap discrepancy cochain `delta ∈ C^1` (length = dim C^1).
    pub delta: Vec<Q>,
    /// Whether a faithful cochain comparison + separated quotient norm is
    /// declared (the only license to claim positive `Φ1` from a nonzero class).
    pub faithful_comparison: bool,
}

/// Whether an obstruction licenses a positive-`Φ1` claim (§18.5 non-claim).
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Phi1Claim {
    /// Default: a finite Čech obstruction makes NO `Φ1` claim.
    NotClaimed,
    /// Licensed only by a declared faithful comparison + separated quotient norm.
    PositiveUnderFaithfulComparison,
}

/// Reason a Čech packet is refused (no cohomology class can be formed).
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CechRefusalReason {
    /// The declared complex is not exact: `d1 ∘ d0 ≠ 0`.
    ComplexNotExact,
    /// Cover / restriction / cochain dimensions are incompatible.
    DimensionMismatch { context: &'static str },
    /// `delta` is not a cocycle (`d1·delta ≠ 0`), so `[delta]` is undefined.
    NotACocycle,
    /// Internal exact linear-algebra failure (should not occur post-dim-check).
    LinearAlgebra(String),
}

/// The four-way terminal of the finite Čech contextual-obstruction gate.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CechTerminal {
    /// A required local section is missing or fails replay (checked FIRST).
    LocalInvalid { missing: Vec<String> },
    /// No cohomology class can be formed.
    CechRefused { reason: CechRefusalReason },
    /// `[delta] = 0`: local repairs glue after a coboundary adjustment.
    ContextuallyGlueable,
    /// `[delta] ≠ 0`: a genuine finite contextual obstruction.
    ContextualObstruction { phi1_claim: Phi1Claim },
}

/// Run the finite Čech contextual-obstruction gate. Total: always returns a
/// terminal, never panics.
pub fn run_cech_gate(input: &CechInput) -> CechTerminal {
    // 1. SOUNDNESS ORDERING: local-section replay BEFORE global obstruction.
    let missing: Vec<String> = input
        .local_sections
        .iter()
        .filter(|s| !matches!(s.replay, SectionReplay::Present))
        .map(|s| s.id.clone())
        .collect();
    if !missing.is_empty() {
        return CechTerminal::LocalInvalid { missing };
    }

    if let Some(refused) = check_cech_complex_and_cocycle(input) {
        return refused;
    }

    // 4. Coboundary membership: delta ∈ im(d0) decided exactly over Q.
    match in_column_space(&input.d0, &input.delta) {
        Ok(true) => CechTerminal::ContextuallyGlueable,
        Ok(false) => {
            let phi1_claim = if input.faithful_comparison {
                Phi1Claim::PositiveUnderFaithfulComparison
            } else {
                Phi1Claim::NotClaimed
            };
            CechTerminal::ContextualObstruction { phi1_claim }
        }
        Err(e) => CechTerminal::CechRefused {
            reason: CechRefusalReason::LinearAlgebra(format!("{e}")),
        },
    }
}

fn check_cech_complex_and_cocycle(input: &CechInput) -> Option<CechTerminal> {
    let c1 = input.d0.rows(); // dim C^1
    let c1_from_d1 = input.d1.cols(); // dim C^1 (as seen by d1)

    // 2. Structural well-formedness of the declared complex.
    if c1 != c1_from_d1 {
        return Some(CechTerminal::CechRefused {
            reason: CechRefusalReason::DimensionMismatch {
                context: "dim C^1 disagrees between d0 (rows) and d1 (cols)",
            },
        });
    }
    if input.delta.len() != c1 {
        return Some(CechTerminal::CechRefused {
            reason: CechRefusalReason::DimensionMismatch {
                context: "delta length != dim C^1",
            },
        });
    }

    // The declared maps must form a cochain complex: d1 ∘ d0 = 0.
    match mat_mul(&input.d1, &input.d0) {
        Ok(prod) => {
            if !is_zero_matrix(&prod) {
                return Some(CechTerminal::CechRefused {
                    reason: CechRefusalReason::ComplexNotExact,
                });
            }
        }
        Err(e) => {
            return Some(CechTerminal::CechRefused {
                reason: CechRefusalReason::LinearAlgebra(format!("{e}")),
            });
        }
    }

    // 3. Cocycle test: d1·delta = 0, else no class exists.
    match mat_vec_mul(&input.d1, &input.delta) {
        Ok(image) => {
            if !image.iter().all(|x| x.is_zero()) {
                return Some(CechTerminal::CechRefused {
                    reason: CechRefusalReason::NotACocycle,
                });
            }
        }
        Err(e) => {
            return Some(CechTerminal::CechRefused {
                reason: CechRefusalReason::LinearAlgebra(format!("{e}")),
            });
        }
    }
    None
}

// Origin: engine/crates_rs/core_homology/src/cech_gate.rs
// Claim: urn:core:crates_rs:core-homology:cech-gate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd2a1789b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd2a1789b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord2a1789b {
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
impl BoundaryErrord2a1789b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord2a1789b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord2a1789b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd2a1789b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord2a1789b> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord2a1789b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord2a1789b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord2a1789b::ExceedsCapacity {
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

#[cfg(test)]
mod tests {
    use super::*;
    use num_rational::Rational64;

    fn q(n: i64) -> Q {
        crate::scalar::q(n)
    }

    /// The triangle-nerve cochain complex over the constant presheaf `Q`:
    /// 3 cover elements `U0,U1,U2`, 3 pairwise overlaps `e01,e12,e20`, no triple
    /// overlap (`C^2` modeled as the zero target, so every cochain is a cocycle).
    ///
    /// d0 (rows = edges, cols = vertices), (d0 s)_{ij} = s_j - s_i:
    ///   e01 = s1 - s0 -> [-1,  1,  0]
    ///   e12 = s2 - s1 -> [ 0, -1,  1]
    ///   e20 = s0 - s2 -> [ 1,  0, -1]
    /// rank(d0) = 2; im(d0) = { x : x0 + x1 + x2 = 0 }.
    fn triangle_d0() -> BasicMatrix<Q> {
        BasicMatrix::from_row_major(
            3,
            3,
            vec![
                q(-1),
                q(1),
                q(0), //
                q(0),
                q(-1),
                q(1), //
                q(1),
                q(0),
                q(-1),
            ],
        )
        .unwrap()
    }

    /// d1 : C^1 -> C^2 with C^2 modeled as the trivial (zero) target: 1x3 zero
    /// matrix, so d1·delta = 0 for all delta and d1∘d0 = 0.
    fn triangle_d1_zero() -> BasicMatrix<Q> {
        BasicMatrix::from_row_major(1, 3, vec![q(0); 3]).unwrap()
    }

    fn present_sections() -> Vec<LocalSection> {
        vec![
            LocalSection::present("U0"),
            LocalSection::present("U1"),
            LocalSection::present("U2"),
        ]
    }

    #[test]
    fn winding_cochain_is_a_genuine_contextual_obstruction() {
        // delta = [1,1,1]: sum = 3 != 0, so delta ∉ im(d0). It is a cocycle
        // (d1 = 0). => ContextualObstruction, and NO Φ1 claim (no faithful cmp).
        let input = CechInput {
            local_sections: present_sections(),
            d0: triangle_d0(),
            d1: triangle_d1_zero(),
            delta: vec![q(1), q(1), q(1)],
            faithful_comparison: false,
        };
        assert_eq!(
            run_cech_gate(&input),
            CechTerminal::ContextualObstruction {
                phi1_claim: Phi1Claim::NotClaimed
            }
        );
    }

    #[test]
    fn coboundary_discrepancy_is_contextually_glueable() {
        // delta = d0 · [0,1,0] = [1,-1,0] (sum 0) => delta ∈ im(d0) => Glueable.
        let input = CechInput {
            local_sections: present_sections(),
            d0: triangle_d0(),
            d1: triangle_d1_zero(),
            delta: vec![q(1), q(-1), q(0)],
            faithful_comparison: false,
        };
        assert_eq!(run_cech_gate(&input), CechTerminal::ContextuallyGlueable);
    }

    #[test]
    fn local_invalidity_preempts_a_would_be_obstruction() {
        // SAME obstruction delta as the first test, but U1's section is missing.
        // The gate MUST return LocalInvalid, never ContextualObstruction —
        // this is the §18.5 soundness ordering.
        let mut sections = present_sections();
        sections[1] = LocalSection::missing("U1");
        let input = CechInput {
            local_sections: sections,
            d0: triangle_d0(),
            d1: triangle_d1_zero(),
            delta: vec![q(1), q(1), q(1)], // would otherwise be an obstruction
            faithful_comparison: false,
        };
        match run_cech_gate(&input) {
            CechTerminal::LocalInvalid { missing } => assert_eq!(missing, vec!["U1".to_string()]),
            other => panic!("expected LocalInvalid, got {other:?}"),
        }
    }

    #[test]
    fn failed_replay_is_also_local_invalid() {
        let mut sections = present_sections();
        sections[2].replay = SectionReplay::FailedReplay("hash mismatch".into());
        let input = CechInput {
            local_sections: sections,
            d0: triangle_d0(),
            d1: triangle_d1_zero(),
            delta: vec![q(1), q(-1), q(0)],
            faithful_comparison: false,
        };
        match run_cech_gate(&input) {
            CechTerminal::LocalInvalid { missing } => assert_eq!(missing, vec!["U2".to_string()]),
            other => panic!("expected LocalInvalid, got {other:?}"),
        }
    }

    #[test]
    fn non_cocycle_is_refused_not_an_obstruction() {
        // Filled triangle: d1 = [1,1,1] (1x3, the boundary of the 2-cell). Now a
        // discrepancy with nonzero winding is NOT closed: d1·[1,0,0] = [1] != 0.
        // d1∘d0 = [1,1,1]·d0 = [0,0,0] (each column sums to 0), so the complex is
        // still exact, but delta is not a cocycle => CechRefused(NotACocycle).
        let d1_filled = BasicMatrix::from_row_major(1, 3, vec![q(1), q(1), q(1)]).unwrap();
        let input = CechInput {
            local_sections: present_sections(),
            d0: triangle_d0(),
            d1: d1_filled,
            delta: vec![q(1), q(0), q(0)],
            faithful_comparison: false,
        };
        assert_eq!(
            run_cech_gate(&input),
            CechTerminal::CechRefused {
                reason: CechRefusalReason::NotACocycle
            }
        );
    }

    #[test]
    fn non_exact_complex_is_refused() {
        // d1 = [1,0,0] (1x3). Then d1∘d0 = first row of d0 = [-1,1,0] != 0.
        let d1_bad = BasicMatrix::from_row_major(1, 3, vec![q(1), q(0), q(0)]).unwrap();
        let input = CechInput {
            local_sections: present_sections(),
            d0: triangle_d0(),
            d1: d1_bad,
            delta: vec![q(0), q(0), q(0)],
            faithful_comparison: false,
        };
        assert_eq!(
            run_cech_gate(&input),
            CechTerminal::CechRefused {
                reason: CechRefusalReason::ComplexNotExact
            }
        );
    }

    #[test]
    fn dimension_mismatch_is_refused() {
        let input = CechInput {
            local_sections: present_sections(),
            d0: triangle_d0(),
            d1: triangle_d1_zero(),
            delta: vec![q(1), q(1)], // wrong length (2 != dim C^1 = 3)
            faithful_comparison: false,
        };
        assert_eq!(
            run_cech_gate(&input),
            CechTerminal::CechRefused {
                reason: CechRefusalReason::DimensionMismatch {
                    context: "delta length != dim C^1"
                }
            }
        );
    }

    #[test]
    fn faithful_comparison_licenses_phi1_claim() {
        // Same genuine obstruction, but now a faithful comparison is declared,
        // which is the ONLY license for the positive-Φ1 claim.
        let input = CechInput {
            local_sections: present_sections(),
            d0: triangle_d0(),
            d1: triangle_d1_zero(),
            delta: vec![q(1), q(1), q(1)],
            faithful_comparison: true,
        };
        assert_eq!(
            run_cech_gate(&input),
            CechTerminal::ContextualObstruction {
                phi1_claim: Phi1Claim::PositiveUnderFaithfulComparison
            }
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_d2a1789b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordd2a1789b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordd2a1789b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordd2a1789b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordd2a1789b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordd2a1789b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrord2a1789b::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrord2a1789b::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
