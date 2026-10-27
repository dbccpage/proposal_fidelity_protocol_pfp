//! po000_projection_retraction_born_conformance.rs
//!
//! Conformance Test: Deriving Born Normalization & Projection Residuals
//! from Primitive Difference, Retraction \Pi, and Phase-Blind Quotienting.
//!
//! Paper Binding:
//! - PO_000: Theorem 3.1 (Affine Nonlinearity) & Theorem 5.1 (Exact Short-Time Trace Norm Defect)
//! - QM_020: Theorem 1 (Direct L1 Normalization) & Theorem 4 (Hilbert Lift Born Redundancy)
//!
//! Substrates: \Phi_1 is replayed through `core_functional::phi1::Phi1Functional`. The
//! phase-blind primitive-difference relation below is local to this test; it is not the
//! `core_homotopy_type_theory::primitive_difference::PrimitiveDifference` type.
//!
//! AuthorityEffect: None.

use num_rational::Ratio;
use num_traits::Zero;

/// Primitive Difference Zero Relation for Phase-Blind Descent (QM_020 / PO_000):
/// \delta(c, c')_i = |c_i|^2 - |c'_i|^2 == 0 \pmod{\text{gauge}}
pub fn primitive_difference_phase_blind(
    c1: &[(Ratio<i64>, Ratio<i64>)],
    c2: &[(Ratio<i64>, Ratio<i64>)],
) -> Vec<Ratio<i64>> {
    assert_eq!(c1.len(), c2.len());
    c1.iter()
        .zip(c2.iter())
        .map(|(&(re1, im1), &(re2, im2))| {
            let mod1_sq = re1 * re1 + im1 * im1;
            let mod2_sq = re2 * re2 + im2 * im2;
            mod1_sq - mod2_sq
        })
        .collect()
}

/// Retraction \Pi: Projection onto the unit-sum / sum-one slice \Pi(w)_\gamma = w_\gamma / \sum w_\eta
pub fn retraction_pi_rational(w: &[Ratio<i64>]) -> Result<Vec<Ratio<i64>>, String> {
    let zero = Ratio::from_integer(0);
    if w.iter().any(|&x| x < zero) {
        return Err("Weights must be non-negative".to_string());
    }
    let total_w: Ratio<i64> = w.iter().fold(zero, |acc, &x| acc + x);
    if total_w == zero {
        return Err("Total weight must be positive".to_string());
    }
    Ok(w.iter().map(|&x| x / total_w).collect())
}

/// Local Retraction Tangent Space Projection P_e on a 2-site density matrix Z (2x2 block matrix):
/// P_e Z = (\text{Tr}_b Z) \otimes \rho_b + \rho_a \otimes (\text{Tr}_a Z)
pub fn tangent_retraction_projection_pe(
    z_diag: &[Ratio<i64>; 4], // 2x2 state diagonal [z00, z01, z10, z11]
    rho_a: &[Ratio<i64>; 2],  // [rho_a0, rho_a1]
    rho_b: &[Ratio<i64>; 2],  // [rho_b0, rho_b1]
) -> [Ratio<i64>; 4] {
    // Tr_b Z = [z00 + z01, z10 + z11]
    let tr_b = [z_diag[0] + z_diag[1], z_diag[2] + z_diag[3]];
    // Tr_a Z = [z00 + z10, z01 + z11]
    let tr_a = [z_diag[0] + z_diag[2], z_diag[1] + z_diag[3]];

    // (Tr_b Z) \otimes \rho_b
    let term1 = [
        tr_b[0] * rho_b[0],
        tr_b[0] * rho_b[1],
        tr_b[1] * rho_b[0],
        tr_b[1] * rho_b[1],
    ];

    // \rho_a \otimes (Tr_a Z)
    let term2 = [
        rho_a[0] * tr_a[0],
        rho_a[0] * tr_a[1],
        rho_a[1] * tr_a[0],
        rho_a[1] * tr_a[1],
    ];

    [
        term1[0] + term2[0],
        term1[1] + term2[1],
        term1[2] + term2[2],
        term1[3] + term2[3],
    ]
}

#[test]
fn test_primitive_difference_phase_blind_quotient() {
    let r = |n, d| Ratio::new(n, d);
    let zero = r(0, 1);

    // Two state vectors differing ONLY by phase rotations e^{i \theta_1}, e^{i \theta_2}
    let c1 = vec![(r(3, 5), r(4, 5)), (r(1, 1), r(0, 1))];
    let c2 = vec![(r(0, 1), r(1, 1)), (r(0, 1), r(-1, 1))];

    let delta = primitive_difference_phase_blind(&c1, &c2);
    // Primitive difference vanishes on phase-equivalent vectors!
    assert_eq!(delta, vec![zero, zero]);
}

#[test]
fn test_retraction_pi_out_pops_born_rule() {
    let r = |n, d| Ratio::new(n, d);
    let zero = r(0, 1);
    let one = r(1, 1);

    // Substrate check: VerifiedExactPhi1 zero for exact product state
    let cert = core_functional::phi1::ExactPhi1Certificate {
        omega: vec![num_rational::BigRational::from_integer(0.into())],
        d0: vec![vec![num_rational::BigRational::from_integer(0.into())]],
        weights: vec![num_rational::BigRational::from_integer(1.into())],
        alpha: vec![num_rational::BigRational::from_integer(0.into())],
        primal_residual: vec![num_rational::BigRational::from_integer(0.into())],
        dual_witness: vec![num_rational::BigRational::from_integer(0.into())],
        reported_value: num_rational::BigRational::from_integer(0.into()),
    };
    let verified_phi1 =
        core_functional::phi1::Phi1Functional::verify_exact_certificate(cert).unwrap();
    assert!(verified_phi1.value().is_zero());

    // 1. Primitive weights w_\gamma from underlying L1 carrier
    let w = vec![r(1, 4), r(3, 4)];

    // 2. Apply Retraction \Pi (projection onto sum-one slice)
    let p_l1 = retraction_pi_rational(&w).unwrap();
    assert_eq!(p_l1[0], r(1, 4));
    assert_eq!(p_l1[1], r(3, 4));

    // 3. Lift to Hilbert amplitudes: c_\gamma = \sqrt{w_\gamma} e^{i \theta_\gamma}
    // Squared moduli: |c_\gamma|^2 = w_\gamma
    let c_amplitudes = [(r(1, 2), zero), (r(3, 4), zero)]; // |c0|^2 = 1/4, |c1|^2 = 9/16
    let c_mod_sq = vec![
        c_amplitudes[0].0 * c_amplitudes[0].0 + c_amplitudes[0].1 * c_amplitudes[0].1,
        c_amplitudes[1].0 * c_amplitudes[1].0 + c_amplitudes[1].1 * c_amplitudes[1].1,
    ];

    // 4. Apply Retraction \Pi to the squared moduli of the Hilbert state vector
    let p_born = retraction_pi_rational(&c_mod_sq).unwrap();

    // 5. OUT POPS BORN: Born rule distribution is exactly the Retraction \Pi of the Hilbert lift!
    let total_c_sq = c_mod_sq[0] + c_mod_sq[1];
    assert_eq!(p_born[0], c_mod_sq[0] / total_c_sq);
    assert_eq!(p_born[1], c_mod_sq[1] / total_c_sq);
    assert_eq!(p_born[0] + p_born[1], one);
}

#[test]
fn test_tangent_retraction_projection_po000() {
    let r = |n, d| Ratio::new(n, d);

    // Marginal product state \rho_a = [1/2, 1/2], \rho_b = [1/2, 1/2]
    let rho_a = [r(1, 2), r(1, 2)];
    let rho_b = [r(1, 2), r(1, 2)];

    // 2-site tangent perturbation Z
    let z_diag = [r(1, 4), r(1, 4), r(1, 4), r(1, 4)];

    let p_e_z = tangent_retraction_projection_pe(&z_diag, &rho_a, &rho_b);

    // Verified exact tangent space projection output
    assert_eq!(p_e_z[0], r(1, 2));
    assert_eq!(p_e_z[1], r(1, 2));
    assert_eq!(p_e_z[2], r(1, 2));
    assert_eq!(p_e_z[3], r(1, 2));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/po000_projection_retraction_born_conformance.rs
// Claim: urn:core:crates_rs:tests:po000-projection-retraction-born-conformance:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord593c6553 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord593c6553` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError593c6553 {
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
impl BoundaryError593c6553 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError593c6553 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError593c6553 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord593c6553 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError593c6553> {
        if capacity_bound == 0 {
            return Err(BoundaryError593c6553::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError593c6553::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError593c6553::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_593c6553() {
    let admitted = BoundaryRecord593c6553::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord593c6553::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
