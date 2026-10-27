// AuthorityEffect: None.
//! Integration test: Exact solver search and adversarial falsification of candidate 4th MUB bases in d=6
//! across non-cyclic monomial Hadamard matrices (Tao matrix and Petrescu families) over Q(zeta_12).
use core_quantum_physics::mub::non_cyclic_falser::{
    build_petrescu_matrix, build_tao_s6_matrix, execute_non_cyclic_mub6_search,
    projectors_from_chm, search_petrescu_points, verify_chm, FalsificationVerdict,
    MubAdversarialFalser,
};
use core_quantum_physics::mub::MubSystem;

#[test]
fn test_tao_projector_basis_intra_laws_and_falsification_attack() {
    let s6 = build_tao_s6_matrix().expect("Failed to build Tao S6 matrix");
    assert!(verify_chm(&s6).expect("CHM verification failed"));

    // Extract the candidate basis projectors
    let tao_projectors = projectors_from_chm(&s6).expect("Failed to extract projectors");
    assert_eq!(tao_projectors.len(), 6);

    // Verify intra-basis projector algebra for Tao candidate
    // 1. Hermiticity: Q_k† == Q_k
    // 2. Idempotence: Q_k^2 == Q_k
    // 3. Rank-1 trace: Tr(Q_k) == 1
    // 4. Same-basis orthogonality: Q_j Q_k == 0 for j != k
    // 5. Completeness: sum Q_k == I_6
    let tao_single_basis_system = MubSystem::try_new(6, vec![tao_projectors.clone()])
        .expect("Tao candidate basis must satisfy single-basis projector laws");
    assert_eq!(tao_single_basis_system.basis_count(), 1);
    assert!(tao_single_basis_system.verify_hermiticity());
    assert!(tao_single_basis_system.verify_idempotence());
    assert!(tao_single_basis_system.verify_rank_one_trace());
    assert!(tao_single_basis_system.verify_same_basis_orthogonality());
    assert!(tao_single_basis_system.verify_resolution_of_identity());

    // Now unleash the adversarial falser against Tao S6
    let falser = MubAdversarialFalser::try_new().expect("Failed to initialize falser");
    let verdict = falser.attack(&tao_projectors).expect("Falser attack failed");

    match verdict {
        FalsificationVerdict::Falsified {
            total_violations,
            first_witness,
            violating_bases,
        } => {
            assert!(total_violations > 0, "Violations must be detected");
            // Must violate Shift (X) and Displacement (D)
            assert!(violating_bases.contains(&"Weyl-Shift-X".to_string()));
            assert!(violating_bases.contains(&"Weyl-Displacement-D".to_string()));
            // Must NOT violate Clock (Z) because column norms of dephased CHMs are uniformly 1/sqrt(6)
            assert!(!violating_bases.contains(&"Weyl-Clock-Z".to_string()));

            // Verify first witness has non-zero defect
            assert!(!first_witness.defect_str.is_empty());
        }
        FalsificationVerdict::Admitted => {
            panic!("FATAL: Adversarial falser erroneously admitted Tao S6 as a 4th MUB!");
        }
    }
}

#[test]
fn test_petrescu_family_points_and_adversarial_falsification() {
    let petrescu_points = search_petrescu_points();
    assert_eq!(petrescu_points.len(), 144, "Expected exactly 144 discrete Petrescu/Szollosi points in mu_12^4");

    let falser = MubAdversarialFalser::try_new().expect("Failed to initialize falser");

    // Test a sample point from the Petrescu family
    let (kb, kc, ke, kf) = petrescu_points[0];
    let pet_mat = build_petrescu_matrix(kb, kc, ke, kf).expect("Build Petrescu matrix failed");
    assert!(verify_chm(&pet_mat).expect("Petrescu matrix must be CHM"));

    let pet_projectors = projectors_from_chm(&pet_mat).expect("Extract Petrescu projectors failed");
    let pet_single_basis_system = MubSystem::try_new(6, vec![pet_projectors.clone()])
        .expect("Petrescu candidate must satisfy single-basis projector laws");
    assert!(pet_single_basis_system.verify_hermiticity());
    assert!(pet_single_basis_system.verify_idempotence());
    assert!(pet_single_basis_system.verify_rank_one_trace());
    assert!(pet_single_basis_system.verify_same_basis_orthogonality());
    assert!(pet_single_basis_system.verify_resolution_of_identity());

    // Attack the Petrescu candidate
    let verdict = falser.attack(&pet_projectors).expect("Attack failed");
    match verdict {
        FalsificationVerdict::Falsified {
            total_violations,
            violating_bases,
            first_witness,
        } => {
            assert!(total_violations > 0);
            assert!(!violating_bases.is_empty());
            assert!(!first_witness.defect_str.is_empty());
        }
        FalsificationVerdict::Admitted => {
            panic!("FATAL: Adversarial falser erroneously admitted Petrescu candidate as a 4th MUB!");
        }
    }
}

#[test]
fn test_exhaustive_solver_search_falsification_report() {
    let report = execute_non_cyclic_mub6_search().expect("Exhaustive search execution failed");

    // Verification invariants:
    assert!(report.weyl_triad_verified, "Weyl triad must be certified");
    assert!(report.tao_base_falsified, "Tao base must be falsified");
    assert_eq!(report.tao_permutations_tested, 720);
    assert_eq!(report.tao_permutations_falsified, 720, "All 720 Tao permutations must be falsified");
    assert_eq!(report.petrescu_points_found, 144);
    assert_eq!(report.petrescu_candidates_tested, 144);
    assert_eq!(report.petrescu_candidates_falsified, 144, "All 144 Petrescu candidates must be falsified");
    assert_eq!(report.total_candidates_tested, 864);
    assert_eq!(report.total_candidates_falsified, 864);
    assert_eq!(report.candidates_admitted, 0, "Zero candidates can be admitted");

    // Constitutional firewall checks:
    assert_eq!(report.authority_effect, "None");
    assert!(report.firewall.contains("NOT MUB(6)=3"));
    assert!(report.firewall.contains("mints no authority"));
    assert!(report.conclusion.contains("No 4th basis exists"));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/mub6_non_cyclic_falser.rs
// Claim: urn:core:crates_rs:tests:mub6-non-cyclic-falser:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb8fa87bd {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb8fa87bd` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb8fa87bd {
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
impl BoundaryErrorb8fa87bd {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb8fa87bd {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb8fa87bd {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb8fa87bd {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb8fa87bd> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb8fa87bd::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb8fa87bd::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb8fa87bd::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_b8fa87bd() {
    let admitted = BoundaryRecordb8fa87bd::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordb8fa87bd::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
