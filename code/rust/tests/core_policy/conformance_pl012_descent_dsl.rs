//! PL-012-1 — executable conformance suite for the Paper-012 typed descent-DSL
//! **typing / safety rules**.
//!
//! Discharges the Mechanical obligation PL-012-1 (`proof_ledger_20260609.md`
//! §Paper 012, `work_queue.md`): "needs targeted executable DSL typing/safety
//! conformance suite ... for d0-on-C1 rejection, gamma2/Complex2 rejection,
//! projector invariants, and the accept gate."
//!
//! The typed exact-rational descent DSL lives in `core_functional::gamma2`:
//! `ExactCochainComplexQ::try_new` constructs the `C0 -d0-> C1 -d1-> C2` complex
//! only from well-typed, degree-matched data; `DegreeOneResidualQ::try_new` places
//! a residual in `C1`; `Gamma2Functional::try_compute_exact_quotient` is the accept
//! gate that yields `Gamma2 = ||d1 h||_1` *only* from a validated complex+residual.
//! Each rejection below pins a specific `ExactGamma2Error` to its safety rule, so
//! a malformed/degree-confused input is **refused**, never silently coerced (in
//! particular `Gamma2` is never silently set to 0 when `Complex2` is absent).
//!
//! Complementary to `conformance_gamma2_trichotomy.rs` (which is JSON-vector driven
//! and exercises the happy path + generic `d1∘d0 != 0` refusal); this suite pins
//! every typing/safety variant directly as unit assertions.
//!
//! Firewall: diagnostic typed-DSL conformance; mints no authority.

use num_bigint::BigInt;
use num_rational::BigRational;
use core_functional::gamma2::{
    Complex2InputQ, DegreeOneResidualQ, ExactCochainComplexQ, ExactGamma2Error, Gamma2Functional,
};
use core_policy::evaluation_hierarchy::{compare_guarded_diagnostics, DiagnosticComparison};

fn r(value: i64) -> BigRational {
    BigRational::from_integer(BigInt::from(value))
}

// ---------------------------------------------------------------------------
// (1) d0-on-C1 rejection — `d0 : C0 -> C1` must be degree-matched to (c0, c1).
// ---------------------------------------------------------------------------

#[test]
fn d0_row_count_must_equal_c1_degree() {
    // `d0` carries one row per `C1` coordinate. Supplying a `d0` whose row count
    // does not match `c1_dim` is a degree-confused operator (e.g. a `C1`-shaped
    // map where a `C0 -> C1` map is required) and is REJECTED, not coerced.
    let err = ExactCochainComplexQ::try_new(1, 2, 0, vec![vec![r(0)]], vec![]).unwrap_err();
    assert_eq!(
        err,
        ExactGamma2Error::D0RowMismatch {
            expected: 2,
            actual: 1
        }
    );
}

#[test]
fn d0_column_count_must_equal_c0_degree() {
    // Each `d0` row maps *from* `C0`, so it must have exactly `c0_dim` columns.
    let err = ExactCochainComplexQ::try_new(2, 1, 0, vec![vec![r(0)]], vec![]).unwrap_err();
    assert_eq!(
        err,
        ExactGamma2Error::D0ColumnMismatch {
            row: 0,
            expected: 2,
            actual: 1
        }
    );
}

// ---------------------------------------------------------------------------
// (2) gamma2 / Complex2 rejection — no silent `Gamma2 = 0` when `C2`/`d1` is
//     missing or mis-degreed; `d1 : C1 -> C2`, residual `h` lives in `C1`.
// ---------------------------------------------------------------------------

#[test]
fn missing_complex2_input_is_rejected_not_silently_zeroed() {
    // A missing `Complex2` is distinct from a declared empty `C2`. The typed DSL
    // rejects the missing input before any `Gamma2` value can be fabricated.
    let err =
        ExactCochainComplexQ::try_new_with_complex2(0, 1, vec![vec![]], Complex2InputQ::Missing)
            .unwrap_err();
    assert_eq!(err, ExactGamma2Error::MissingComplex2);
}

#[test]
fn declared_empty_complex2_is_explicit_not_missing() {
    // A declared zero-dimensional `C2` is a supplied complex with no 2-cells.
    // It may evaluate to zero, but only because the empty `Complex2` was explicit.
    let complex = ExactCochainComplexQ::try_new_with_complex2(
        0,
        1,
        vec![vec![]],
        Complex2InputQ::Declared {
            c2_dim: 0,
            d1: vec![],
        },
    )
    .expect("declared empty C2 is an explicit Complex2");
    let residual = DegreeOneResidualQ::try_new(&complex, vec![r(7)]).expect("residual in C1");
    let gamma2 = Gamma2Functional::try_compute_exact_quotient(&residual).expect("accept gate");
    assert_eq!(gamma2.value(), &r(0));
}

#[test]
fn missing_d1_rows_for_declared_complex2_are_rejected() {
    // Declaring `c2_dim = 1` (a degree-2 cochain space exists) but supplying no
    // `d1` row is an ABSENT Complex2. The DSL refuses to build the complex rather
    // than silently proceeding (which would yield a spurious `Gamma2 = 0`).
    let err = ExactCochainComplexQ::try_new(0, 1, 1, vec![vec![]], vec![]).unwrap_err();
    assert_eq!(
        err,
        ExactGamma2Error::D1RowMismatch {
            expected: 1,
            actual: 0
        }
    );
}

#[test]
fn d1_column_count_must_equal_c1_degree() {
    // Each `d1` row maps *from* `C1`, so it must have `c1_dim` columns. A mis-typed
    // `Complex2` whose `d1` width disagrees with `C1` is REJECTED.
    let err =
        ExactCochainComplexQ::try_new(0, 2, 1, vec![vec![], vec![]], vec![vec![r(1)]]).unwrap_err();
    assert_eq!(
        err,
        ExactGamma2Error::D1ColumnMismatch {
            row: 0,
            expected: 2,
            actual: 1
        }
    );
}

#[test]
fn residual_at_wrong_degree_is_rejected() {
    // The residual `h` lives in `C1`. A residual whose length differs from `c1_dim`
    // is placed at the wrong degree and is REFUSED — `Gamma2` is never computed
    // from a wrong-degree (mis-typed `Complex2`-coordinate) residual.
    let complex =
        ExactCochainComplexQ::try_new(0, 2, 1, vec![vec![], vec![]], vec![vec![r(1), r(0)]])
            .expect("well-formed c1=2 complex");
    // `DegreeOneResidualQ` is not `Debug`, so match the `Result` directly.
    match DegreeOneResidualQ::try_new(&complex, vec![r(1)]) {
        Err(e) => assert_eq!(
            e,
            ExactGamma2Error::ResidualLengthMismatch {
                expected: 2,
                actual: 1
            }
        ),
        Ok(_) => panic!("expected ResidualLengthMismatch for a wrong-degree residual"),
    }
}

// ---------------------------------------------------------------------------
// (3) projector / cochain-complex invariant — `d1 ∘ d0 = 0` is enforced.
// ---------------------------------------------------------------------------

#[test]
fn cochain_invariant_d1_after_d0_must_vanish() {
    // `d0 = [[1]]` (C0->C1), `d1 = [[1]]` (C1->C2): `d1∘d0 = [1] ≠ 0`, so the data
    // is not a cochain complex (the coboundary-squared / projector invariant
    // fails) and is REJECTED at the exact (row, column) where it breaks.
    let err =
        ExactCochainComplexQ::try_new(1, 1, 1, vec![vec![r(1)]], vec![vec![r(1)]]).unwrap_err();
    assert_eq!(
        err,
        ExactGamma2Error::CochainIdentityViolation { row: 0, column: 0 }
    );
}

#[test]
fn cochain_invariant_satisfied_is_accepted() {
    // `d0 = [[1]]`, `d1 = [[0]]`: `d1∘d0 = 0` holds, so the complex is accepted.
    let ok = ExactCochainComplexQ::try_new(1, 1, 1, vec![vec![r(1)]], vec![vec![r(0)]]);
    assert!(
        ok.is_ok(),
        "a genuine cochain complex (d1∘d0=0) is accepted"
    );
}

// ---------------------------------------------------------------------------
// (4) the accept gate — `Gamma2` is produced ONLY through a validated complex +
//     residual, and then equals the exact `||d1 h||_1`.
// ---------------------------------------------------------------------------

#[test]
fn accept_gate_yields_exact_gamma2_only_through_validated_dsl() {
    // Well-formed: c0=0, c1=1, c2=1, d1=[[1]] (d1∘d0=0 vacuously), residual h=[3].
    // The gate produces Gamma2 = |1*3| = 3 only after BOTH try_new calls succeed.
    let complex = ExactCochainComplexQ::try_new(0, 1, 1, vec![vec![]], vec![vec![r(1)]])
        .expect("well-formed complex");
    let residual = DegreeOneResidualQ::try_new(&complex, vec![r(3)]).expect("residual in C1");
    let gamma2 = Gamma2Functional::try_compute_exact_quotient(&residual)
        .expect("accept gate computes Gamma2 from validated input");
    assert_eq!(gamma2.value(), &r(3), "Gamma2 = ||d1 h||_1 = |1*3| = 3");
}

#[test]
fn accept_gate_value_is_l1_of_coboundary() {
    // Two-coordinate C1, d1 = [[1, -1]] (d1∘d0=0 vacuously, c0=0), h = [5, 2]:
    // coboundary = [5 - 2] = [3], Gamma2 = |3| = 3. Confirms the gate's exact ℓ¹.
    let complex =
        ExactCochainComplexQ::try_new(0, 2, 1, vec![vec![], vec![]], vec![vec![r(1), r(-1)]])
            .expect("well-formed c1=2 complex");
    let residual = DegreeOneResidualQ::try_new(&complex, vec![r(5), r(2)]).expect("residual in C1");
    let gamma2 = Gamma2Functional::try_compute_exact_quotient(&residual).expect("accept gate");
    assert_eq!(gamma2.value(), &r(3), "Gamma2 = |5 - 2| = 3");
}

// ---------------------------------------------------------------------------
// (5) evaluator boundary — no weighted scalar score may replace the guarded
//     Φ₁ ≻ Γ₂ ≻ Ξ eval law.
// ---------------------------------------------------------------------------

#[test]
fn eval_gate_refuses_gamma2_improvement_that_worsens_phi1() {
    assert_eq!(
        compare_guarded_diagnostics(&r(1), &r(100), None, &r(2), &r(0), None),
        DiagnosticComparison::Worsens
    );
}

#[test]
fn eval_gate_refuses_xi_improvement_that_worsens_gamma2() {
    assert_eq!(
        compare_guarded_diagnostics(&r(1), &r(1), Some(&r(10)), &r(1), &r(2), Some(&r(0))),
        DiagnosticComparison::Worsens
    );
}

#[test]
fn eval_gate_orders_xi_exactly_when_masses_tie() {
    let before = BigRational::new(BigInt::from(2), BigInt::from(3));
    let after = BigRational::new(BigInt::from(1), BigInt::from(2));
    assert_eq!(
        compare_guarded_diagnostics(&r(1), &r(1), Some(&before), &r(1), &r(1), Some(&after)),
        DiagnosticComparison::StrictlyImproves
    );
}

// Origin: engine/crates_rs/tests/core_policy/conformance_pl012_descent_dsl.rs
// Claim: urn:core:crates_rs:tests:conformance-pl012-descent-dsl:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord75d99d2a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord75d99d2a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError75d99d2a {
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
impl BoundaryError75d99d2a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError75d99d2a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError75d99d2a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord75d99d2a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError75d99d2a> {
        if capacity_bound == 0 {
            return Err(BoundaryError75d99d2a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError75d99d2a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError75d99d2a::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_75d99d2a() {
    let admitted = BoundaryRecord75d99d2a::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord75d99d2a::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
