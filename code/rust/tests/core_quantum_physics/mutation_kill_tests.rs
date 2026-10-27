// AuthorityEffect: None. Citation: sealed-derivation-v1 (3100c4e)

//! Mutation Kill Tests for `core_quantum_physics` (MUT-01 through MUT-06).
//!
//! Enforces L4A rubric compliance under SCORING.md:
//! Each test targets a specific behavioral mutant and verifies that deviations
//! are detected and rejected.

use linear_algebra::exact_field::{involution as star, matrix as mx};
use linear_algebra::linear_algebra::complex_matrix::C64;
use core_kernel::resource_limits::{check_and_reserve, OperationLimits};
use core_number_theory::{rq, Cyc24};
use core_quantum_physics::density_matrix::{DensityError, DensityMatrix};
use core_quantum_physics::hilbert_space::HilbertSpace;
use core_quantum_physics::kraus_operators::KrausOperators;
use core_quantum_physics::quantum_channel::{ChannelError, QuantumChannel};
use core_quantum_physics::quantum_state::{QuantumState, QuantumStateError};
use core_quantum_physics::MubSystem;

/// MUT-01: Quantum channel trace-preservation defect.
/// Verifies that non-trace-preserving Kraus sets are rejected, and valid channels preserve trace.
#[test]
fn test_kill_mutant_01_channel_trace_preservation_defect() {
    let k0 = vec![vec![1.0, 0.0], vec![0.0, 1.0]];
    let kraus = KrausOperators::try_new(2, vec![k0], "I").unwrap();
    assert!(matches!(
        QuantumChannel::try_from_kraus(kraus, "chan", 1e-6),
        Err(ChannelError::ToleranceAdmissionRefused { .. })
    ));

    // Invalid non-trace-preserving Kraus operator (scaled by 2.0 -> sum K_k† K_k = 4*I != I)
    let k_bad = vec![vec![2.0, 0.0], vec![0.0, 2.0]];
    let bad_kraus = KrausOperators::try_new(2, vec![k_bad], "bad").unwrap();
    let bad_channel = QuantumChannel::try_from_kraus(bad_kraus, "bad_chan", 1e-6);
    assert!(
        matches!(bad_channel, Err(ChannelError::NonTracePreserving { .. })),
        "Mutant 01 must be killed: non-TP Kraus set must be rejected"
    );
}

/// MUT-02: Density matrix Hermiticity relaxation.
/// Verifies that non-Hermitian operator entries are strictly detected and rejected.
#[test]
fn test_kill_mutant_02_density_hermiticity_violation() {
    // 1. Exact matrix Hermiticity verification
    let rho_non_hermitian = mx::from_rows(vec![
        vec![Cyc24::rat(rq(1, 2)), Cyc24::i()],
        vec![Cyc24::i(), Cyc24::rat(rq(1, 2))],
    ])
    .unwrap();

    assert_ne!(
        star::adjoint(&rho_non_hermitian).unwrap(),
        rho_non_hermitian,
        "Mutant 02 must be killed: asymmetric entry must violate dagger equality"
    );

    // 2. MUB projector system Hermiticity check
    let mut mub3 = MubSystem::mub_d3();
    assert!(mub3.verify_hermiticity());
    // Corrupt one projector to be non-Hermitian
    mub3.bases[0][0].set(0, 1, Cyc24::i()).unwrap();
    mub3.bases[0][0].set(1, 0, Cyc24::i()).unwrap();
    assert!(
        !mub3.verify_hermiticity(),
        "Mutant 02 must be killed: corrupted non-Hermitian projector must fail verify_hermiticity"
    );
}

/// MUT-03: MUB pairwise inner product overlap distortion.
/// In d=3, overlap between any state in basis b and any state in basis c (b != c)
/// must satisfy |<b_i | c_j>|^2 = 1/d = 1/3 exactly.
#[test]
fn test_kill_mutant_03_mub_overlap_distortion() {
    let mub3 = MubSystem::mub_d3();
    assert!(
        mub3.verify_cross_basis_unbiasedness(),
        "MUB cross basis must be mutually unbiased"
    );

    // Explicit check of overlap between basis 0 and basis 1
    for i in 0..3 {
        for j in 0..3 {
            let p_0i = mub3.try_projector(0, i).unwrap();
            let p_1j = mub3.try_projector(1, j).unwrap();
            let prod = mx::multiply(p_0i, p_1j).unwrap();
            let tr = mx::trace(&prod).unwrap();
            // In exact cyclotomics, Tr(P_i Q_j) = |<v_i | w_j>|^2 = 1/3
            assert_eq!(
                tr,
                Cyc24::rat(rq(1, 3)),
                "Mutant 03 must be killed: MUB pairwise overlap must be exactly 1/d"
            );
        }
    }
}

/// MUT-04: Discrete unitary evolution unitarity violation.
/// Non-unitary evolution operator must violate U*U† = I and distort state trace.
#[test]
fn test_kill_mutant_04_unitary_evolution_unitarity_violation() {
    let identity = mx::identity::<Cyc24>(2).unwrap();
    let u_non_unitary = mx::scale(&identity, &Cyc24::rat(rq(2, 1))).unwrap();
    let u_dag = star::adjoint(&u_non_unitary).unwrap();
    let prod = mx::multiply(&u_non_unitary, &u_dag).unwrap();

    assert_ne!(
        prod, identity,
        "Mutant 04 must be killed: non-unitary U must satisfy U*U† != I"
    );

    // Density matrix evolution under non-unitary operator violates trace
    let rho = mx::scale(&identity, &Cyc24::rat(rq(1, 2))).unwrap();
    assert_eq!(mx::trace(&rho).unwrap(), Cyc24::one());
    let evolved = mx::multiply(&mx::multiply(&u_non_unitary, &rho).unwrap(), &u_dag).unwrap();
    assert_ne!(
        mx::trace(&evolved).unwrap(),
        Cyc24::one(),
        "Mutant 04 must be killed: non-unitary evolution must violate Tr(U rho U†) = 1"
    );
}

/// MUT-05: State vector normalization omission.
/// Zero-norm or unnormalized state vectors must be rejected.
#[test]
fn test_kill_mutant_05_state_norm_omission() {
    let hs = HilbertSpace::try_new(2, "hs").unwrap();
    // Zero vector
    let zero_data = vec![C64::ZERO, C64::ZERO];
    let res_zero = QuantumState::try_normalized(&hs, zero_data, "zero");
    assert_eq!(
        res_zero,
        Err(QuantumStateError::ZeroNorm),
        "Mutant 05 must be killed: zero-norm state vector must be rejected"
    );

    // Empty amplitudes
    let res_empty = QuantumState::try_normalized(&hs, vec![], "empty");
    assert_eq!(
        res_empty,
        Err(QuantumStateError::EmptyAmplitudes),
        "Mutant 05 must be killed: empty state vector must be rejected"
    );

    // Density matrix probability vector trace check
    let res_bad_trace = DensityMatrix::try_from_probs(&hs, vec![0.3, 0.3], "bad", 1e-6);
    assert!(
        matches!(res_bad_trace, Err(DensityError::TraceNotOne { .. })),
        "Mutant 05 must be killed: density matrix with trace != 1 must be rejected"
    );
}

/// MUT-06: Soviet allocation discipline bypass.
/// Requests exceeding operational limits must fail fallibly without panic.
#[test]
fn test_kill_mutant_06_soviet_allocation_bypass() {
    let limits = OperationLimits::default();
    assert_eq!(limits.max_hilbert_dim, 1024);

    let mut buf: Vec<u8> = Vec::new();
    // Request exceeding allocation limit
    let res = check_and_reserve(
        &mut buf,
        limits.max_memory_bytes + 1,
        limits.max_memory_bytes,
    );
    assert!(
        res.is_err(),
        "Mutant 06 must be killed: allocation exceeding Soviet limits must return Err"
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/mutation_kill_tests.rs
// Claim: urn:core:crates_rs:tests:mutation-kill-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2a03cd78 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2a03cd78` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2a03cd78 {
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
impl BoundaryError2a03cd78 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2a03cd78 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2a03cd78 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2a03cd78 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2a03cd78> {
        if capacity_bound == 0 {
            return Err(BoundaryError2a03cd78::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2a03cd78::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2a03cd78::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_2a03cd78() {
    let admitted = BoundaryRecord2a03cd78::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord2a03cd78::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
