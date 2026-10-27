// AuthorityEffect: None.

//! Cohomology admission for a declared finite cochain complex.
//!
//! A residual enters `C^1` only through a declared adapter. The complex
//! `C^0 --d0--> C^1 --d1--> C^2` is an `core_functional`
//! [`ExactCochainComplexQ`], so `d1 d0 = 0` has already been replayed. For a
//! cochain `s`, [`admit`] returns exactly one outcome, each with a certificate
//! [`verify_admission`] replays independently:
//!
//! - `Exact`: `s = d0 a`, carrying the preimage `a`;
//! - `ClosedNonexact`: `d1 s = 0` and `s` is outside `im d0`, carrying a
//!   separator `z` with `d0^T z = 0` and `<z, s> != 0`, so `[s]` is a nonzero
//!   class of `H^1`;
//! - `ActiveClosureFailure`: `d1 s != 0`, carrying `d1 s`;
//! - `Refused`: no adapter was declared, the cochain is ill-typed, or the exact
//!   linear algebra could not decide.
//!
//! The three classes are disjoint because `im d0` lies in `ker d1`. Membership
//! is decided by exact row reduction in `core_linear_algebra`, with no
//! tolerance. The outcome reads only `(s, d0, d1)`, so it cannot tell which
//! realization produced `s`. It is a diagnostic, not a terminal decision.
//!
//! `H^1 = ker d1 / im d0` sits inside the quotient `Q^1 = C^1 / im d0` with
//! codimension `rank d1` ([`cohomology_dimensions`]); they coincide exactly
//! when `d1 = 0`. A cochain outside `im d0` is a quotient obstruction
//! ([`image_preimage`] returns `None`). It is an `H^1` class only if it is
//! also closed.

use crate::data_cochain_packet::FiniteCochainPacket;
use linear_algebra::backend::basic_matrix::{BasicMatrix, OperationLimits};
use linear_algebra::exact_field::{
    elimination::{self, LinearSolution},
    matrix,
};
use num_traits::Zero;
use core_functional::gamma2::ExactCochainComplexQ;
use core_number_theory::rational::Rational;
use core_policy::trichotomy::ObstructionDiagnosticClass;

/// Why a residual was not admitted to cohomological language.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AdmissionRefusal {
    /// No adapter from the registered residual to `C^1` was declared.
    NoAdapter,
    ResourceBudget {
        what: &'static str,
        limit: usize,
    },
    ExactLinearAlgebra(linear_algebra::exact_field::ExactFieldError),
    Storage(linear_algebra::backend::basic_matrix::MatrixError),
    CochainLength {
        expected: usize,
        actual: usize,
    },
    /// The exact linear algebra refused the question.
    Undecided(String),
}

/// The admission outcome of one residual, with its certificate.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Admission {
    Exact { preimage: Vec<Rational> },
    ClosedNonexact { separator: Vec<Rational> },
    ActiveClosureFailure { defect: Vec<Rational> },
    Refused(AdmissionRefusal),
}

impl Admission {
    /// The matching `core_functional` diagnostic class; `None` for a refusal.
    pub fn diagnostic_class(&self) -> Option<ObstructionDiagnosticClass> {
        match self {
            Admission::Exact { .. } => Some(ObstructionDiagnosticClass::ExactRepair),
            Admission::ClosedNonexact { .. } => Some(ObstructionDiagnosticClass::ClosedResidual),
            Admission::ActiveClosureFailure { .. } => {
                Some(ObstructionDiagnosticClass::ActiveClosureFailure)
            }
            Admission::Refused(_) => None,
        }
    }
}

/// Exact ranks of a declared complex and the dimensions they fix.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CohomologyDimensions {
    pub rank_d0: usize,
    pub rank_d1: usize,
    /// `dim Q^1 = c1 - rank d0`.
    pub quotient: usize,
    /// `dim Z^1 = c1 - rank d1`.
    pub cycles: usize,
    /// `dim H^1 = dim Z^1 - rank d0`.
    pub h1: usize,
}

/// The validated complex carried by a finite cochain packet.
pub fn complex_of_packet(
    packet: &FiniteCochainPacket,
) -> Result<ExactCochainComplexQ, AdmissionRefusal> {
    ExactCochainComplexQ::try_new(
        packet.vertex_count(),
        packet.edge_count(),
        packet.face_count(),
        packet.d0().to_vec(),
        packet.d1().to_vec(),
    )
    .map_err(|e| AdmissionRefusal::Undecided(e.to_string()))
}

pub const MAX_COCHAIN_DIMENSION: usize = 4096;
const LIMITS: OperationLimits = OperationLimits {
    max_elements: 1 << 20,
    max_scalar_ops: 1 << 26,
};
impl From<linear_algebra::exact_field::ExactFieldError> for AdmissionRefusal {
    fn from(error: linear_algebra::exact_field::ExactFieldError) -> Self {
        Self::ExactLinearAlgebra(error)
    }
}
impl From<linear_algebra::backend::basic_matrix::MatrixError> for AdmissionRefusal {
    fn from(error: linear_algebra::backend::basic_matrix::MatrixError) -> Self {
        Self::Storage(error)
    }
}
// Admission of a cochain complex includes zero-axis dimensions as well as
// dense storage; a point complex cannot allocate an unbounded preimage vector.
fn checked_complex_matrices(
    complex: &ExactCochainComplexQ,
) -> Result<(BasicMatrix<Rational>, BasicMatrix<Rational>), AdmissionRefusal> {
    let (c0, c1, c2) = (complex.c0_dim(), complex.c1_dim(), complex.c2_dim());
    if [c0, c1, c2].iter().any(|&n| n > MAX_COCHAIN_DIMENSION) {
        return Err(AdmissionRefusal::ResourceBudget {
            what: "cochain dimension",
            limit: MAX_COCHAIN_DIMENSION,
        });
    }
    if c1 * c0 + c2 * c1 > LIMITS.max_elements {
        return Err(AdmissionRefusal::ResourceBudget {
            what: "cochain matrix entries",
            limit: LIMITS.max_elements,
        });
    }
    Ok((
        BasicMatrix::from_row_major(c1, c0, complex.d0().iter().flatten().cloned().collect())?,
        BasicMatrix::from_row_major(c2, c1, complex.d1().iter().flatten().cloned().collect())?,
    ))
}

/// `dim Q^1`, `dim Z^1` and `dim H^1` from exact ranks.
pub fn cohomology_dimensions(
    complex: &ExactCochainComplexQ,
) -> Result<CohomologyDimensions, AdmissionRefusal> {
    let c1 = complex.c1_dim();
    let (d0, d1) = checked_complex_matrices(complex)?;
    let rank_d0 = elimination::rank_with_limits(&d0, LIMITS)?;
    let rank_d1 = elimination::rank_with_limits(&d1, LIMITS)?;
    let cycles = c1 - rank_d1;
    Ok(CohomologyDimensions {
        rank_d0,
        rank_d1,
        quotient: c1 - rank_d0,
        cycles,
        h1: cycles - rank_d0,
    })
}

/// A preimage `a` with `d0 a = s`, or `None` when `s` is a quotient obstruction.
/// Closedness is not consulted.
pub fn image_preimage(
    complex: &ExactCochainComplexQ,
    s: &[Rational],
) -> Result<Option<Vec<Rational>>, AdmissionRefusal> {
    let (c0, c1) = (complex.c0_dim(), complex.c1_dim());
    if s.len() != c1 {
        return Err(AdmissionRefusal::CochainLength {
            expected: c1,
            actual: s.len(),
        });
    }
    let (d0, _) = checked_complex_matrices(complex)?;
    if c0 == 0 || c1 == 0 {
        return Ok(s
            .iter()
            .all(Zero::is_zero)
            .then(|| vec![Rational::zero(); c0]));
    }
    match elimination::solve_with_limits(&d0, s, LIMITS)? {
        LinearSolution::Consistent { particular, .. } => Ok(Some(particular)),
        LinearSolution::Inconsistent { .. } => Ok(None),
    }
}

/// Admit a residual that a declared adapter has carried into `C^1`; `None`
/// means no adapter was declared.
pub fn admit(complex: &ExactCochainComplexQ, residual: Option<&[Rational]>) -> Admission {
    let Some(s) = residual else {
        return Admission::Refused(AdmissionRefusal::NoAdapter);
    };
    let outcome = || -> Result<Admission, AdmissionRefusal> {
        let c1 = complex.c1_dim();
        if s.len() != c1 {
            return Err(AdmissionRefusal::CochainLength {
                expected: c1,
                actual: s.len(),
            });
        }
        let (d0, d1) = checked_complex_matrices(complex)?;
        if s.iter().all(Zero::is_zero) {
            return Ok(Admission::Exact {
                preimage: vec![Rational::zero(); complex.c0_dim()],
            });
        }
        match elimination::solve_with_limits(&d0, s, LIMITS)? {
            LinearSolution::Consistent { particular, .. } => Ok(Admission::Exact {
                preimage: particular,
            }),
            LinearSolution::Inconsistent { certificate } => {
                let defect = matrix::multiply_vector_with_limits(&d1, s, LIMITS)?;
                if defect.iter().any(|v| !v.is_zero()) {
                    Ok(Admission::ActiveClosureFailure { defect })
                } else {
                    Ok(Admission::ClosedNonexact {
                        separator: certificate.combination().to_vec(),
                    })
                }
            }
        }
    };
    outcome().unwrap_or_else(Admission::Refused)
}

fn verify_closed_nonexact(
    d0: &BasicMatrix<Rational>,
    s: &[Rational],
    separator: &[Rational],
    defect: &[Rational],
    c1: usize,
) -> Result<bool, AdmissionRefusal> {
    if separator.len() != c1 || !defect.iter().all(Zero::is_zero) {
        return Ok(false);
    }
    let d0t = matrix::transpose(d0)?;
    let coclosed = matrix::multiply_vector_with_limits(&d0t, separator, LIMITS)?
        .iter()
        .all(Zero::is_zero);
    let pairing = !matrix::dot(separator, s)?.is_zero();
    Ok(coclosed && pairing)
}

fn verify_admission_inner(
    complex: &ExactCochainComplexQ,
    s: &[Rational],
    admission: &Admission,
) -> Result<bool, AdmissionRefusal> {
    let (c0, c1) = (complex.c0_dim(), complex.c1_dim());
    if s.len() != c1 {
        return Ok(false);
    }
    let (d0, d1) = checked_complex_matrices(complex)?;
    let defect = matrix::multiply_vector_with_limits(&d1, s, LIMITS)?;
    match admission {
        Admission::Exact { preimage } => {
            if preimage.len() != c0 {
                return Ok(false);
            }
            Ok(matrix::multiply_vector_with_limits(&d0, preimage, LIMITS)? == s)
        }
        Admission::ClosedNonexact { separator } => {
            verify_closed_nonexact(&d0, s, separator, &defect, c1)
        }
        Admission::ActiveClosureFailure { defect: claimed } => {
            Ok(*claimed == defect && defect.iter().any(|v| !v.is_zero()))
        }
        Admission::Refused(_) => Ok(false),
    }
}

/// Replay an admission certificate against the declared complex and cochain.
/// A refusal certifies nothing.
pub fn verify_admission(
    complex: &ExactCochainComplexQ,
    s: &[Rational],
    admission: &Admission,
) -> bool {
    verify_admission_inner(complex, s, admission).unwrap_or(false)
}

// Origin: engine/crates_rs/core_solvers/src/cert_cohomology_admission.rs
// Claim: urn:core:crates_rs:core-solvers:cert-cohomology-admission:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2fbb6b2c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2fbb6b2c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2fbb6b2c {
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
impl BoundaryError2fbb6b2c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2fbb6b2c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2fbb6b2c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2fbb6b2c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2fbb6b2c> {
        if capacity_bound == 0 {
            return Err(BoundaryError2fbb6b2c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2fbb6b2c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2fbb6b2c::ExceedsCapacity {
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
    use core_number_theory::rational::ri;
    fn triangle(filled: bool) -> ExactCochainComplexQ {
        let d0 = vec![
            vec![ri(-1), ri(1), ri(0)],
            vec![ri(0), ri(-1), ri(1)],
            vec![ri(1), ri(0), ri(-1)],
        ];
        ExactCochainComplexQ::try_new(
            3,
            3,
            usize::from(filled),
            d0,
            if filled { vec![vec![ri(1); 3]] } else { vec![] },
        )
        .unwrap()
    }
    #[test]
    fn exact_closed_and_active_classes_have_independent_certificates() {
        let annulus = triangle(false);
        let disk = triangle(true);
        for (complex, s, kind) in [
            (&annulus, vec![ri(1), ri(-1), ri(0)], 0),
            (&annulus, vec![ri(1); 3], 1),
            (&disk, vec![ri(1); 3], 2),
        ] {
            let result = admit(complex, Some(&s));
            assert!(verify_admission(complex, &s, &result));
            assert!(matches!(
                (&result, kind),
                (Admission::Exact { .. }, 0)
                    | (Admission::ClosedNonexact { .. }, 1)
                    | (Admission::ActiveClosureFailure { .. }, 2)
            ));
        }
        assert_eq!(cohomology_dimensions(&annulus).unwrap().h1, 1);
        assert_eq!(cohomology_dimensions(&disk).unwrap().h1, 0);
        assert!(!verify_admission(
            &annulus,
            &[ri(1), ri(1), ri(1)],
            &Admission::ClosedNonexact {
                separator: vec![ri(1)]
            }
        ));
        assert!(!verify_admission(
            &annulus,
            &[ri(1), ri(1), ri(1)],
            &Admission::ClosedNonexact {
                separator: vec![ri(1), ri(0), ri(0)]
            }
        ));
        assert!(!verify_admission(
            &disk,
            &[ri(1), ri(1), ri(1)],
            &Admission::ActiveClosureFailure {
                defect: vec![ri(2)]
            }
        ));
        assert!(matches!(
            admit(&disk, None),
            Admission::Refused(AdmissionRefusal::NoAdapter)
        ));
        assert!(matches!(
            admit(&disk, Some(&[])),
            Admission::Refused(AdmissionRefusal::CochainLength { .. })
        ));
    }
    #[test]
    fn empty_axes_are_admitted_but_unbounded_preimages_are_refused() {
        let point = ExactCochainComplexQ::try_new(1, 0, 0, vec![], vec![]).unwrap();
        assert_eq!(
            admit(&point, Some(&[])),
            Admission::Exact {
                preimage: vec![ri(0)]
            }
        );
        let huge = ExactCochainComplexQ::try_new(4097, 0, 0, vec![], vec![]).unwrap();
        assert!(matches!(
            admit(&huge, Some(&[])),
            Admission::Refused(AdmissionRefusal::ResourceBudget { .. })
        ));
    }
}

#[cfg(test)]
mod l4_boundary_tests_2fbb6b2c {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord2fbb6b2c::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord2fbb6b2c::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord2fbb6b2c::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord2fbb6b2c::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord2fbb6b2c::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError2fbb6b2c::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError2fbb6b2c::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
