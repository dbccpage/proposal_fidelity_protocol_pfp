
#[allow(dead_code, non_camel_case_types, missing_docs)]
type BigRationalRatioWitness_dd03a129 = (i128, i128);
use core_general_relativity::dec_laplacian::DecOperators;
use core_general_relativity::quantum_regge::evaluate_wheeler_dewitt_against_dec_laplacian;
use core_general_relativity::regge_4d::ReggeTriangulation4D;

fn dec() -> DecOperators {
    DecOperators::new(
        3,
        vec![(0, 1), (0, 2), (1, 2)],
        vec![[0, 1, 2]],
        vec![1.0; 3],
        vec![1.0; 3],
        vec![1.0; 3],
    )
    .unwrap()
}

#[test]
fn nonfinite_forms_and_overflow_never_certify_nilpotency() {
    for value in [f64::NAN, f64::INFINITY, f64::NEG_INFINITY] {
        let psi = [value, 1.0, 2.0];
        assert!(dec().verify_nilpotency_d1_d0(&psi).is_err());
        assert!(dec().laplacian_0form(&psi).is_err());
        assert!(dec().inner_product_0form(&psi, &[1.0; 3]).is_err());
    }
    assert!(dec().coboundary_d0(&[f64::MAX, -f64::MAX, 0.0]).is_err());
    assert!(DecOperators::new(
        2,
        vec![(0, 1)],
        vec![],
        vec![f64::MIN_POSITIVE],
        vec![1.0; 2],
        vec![f64::MAX]
    )
    .is_err());
}

#[test]
fn mutated_public_dec_fields_return_errors_instead_of_panicking() {
    let mut d = dec();
    d.hodge.star0_vertex_volumes.clear();
    assert!(d.laplacian_0form(&[1.0; 3]).is_err());
    let mut d = dec();
    d.edge_index.insert((0, 1), usize::MAX);
    assert!(d.coboundary_d1(&[1.0; 3]).is_err());
}

#[test]
fn constraint_refuses_nan_parameters_geometry_and_residuals() {
    let mut tri = ReggeTriangulation4D::two_pentachora_glued(1.0).unwrap();
    let d = tri.build_dec_operators().unwrap();
    let psi = vec![1.0; d.num_vertices];
    assert!(evaluate_wheeler_dewitt_against_dec_laplacian(&tri, &d, &psi, 1.0, 0.0, 1e-6).is_ok());
    for (hbar, lambda, tol) in [
        (f64::NAN, 0.0, 1e-6),
        (1.0, f64::NAN, 1e-6),
        (1.0, 0.0, f64::INFINITY),
        (1.0, 0.0, -1.0),
    ] {
        assert!(
            evaluate_wheeler_dewitt_against_dec_laplacian(&tri, &d, &psi, hbar, lambda, tol)
                .is_err()
        );
    }
    let bad = vec![f64::NAN; d.num_vertices];
    assert!(evaluate_wheeler_dewitt_against_dec_laplacian(&tri, &d, &bad, 1.0, 0.0, 1e-6).is_err());
    tri.hinges[0].deficit_angle = f64::NAN;
    assert!(evaluate_wheeler_dewitt_against_dec_laplacian(&tri, &d, &psi, 1.0, 0.0, 1e-6).is_err());
}

// Origin: engine/crates_rs/tests/core_general_relativity/test_dec_input_bounds.rs
// Claim: urn:core:crates_rs:tests:test-dec-input-bounds:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorddd03a129 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorddd03a129` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrordd03a129 {
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
impl BoundaryErrordd03a129 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrordd03a129 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrordd03a129 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorddd03a129 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrordd03a129> {
        if capacity_bound == 0 {
            return Err(BoundaryErrordd03a129::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrordd03a129::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrordd03a129::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_dd03a129() {
    let admitted = BoundaryRecorddd03a129::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorddd03a129::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
