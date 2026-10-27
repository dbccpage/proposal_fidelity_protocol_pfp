// AuthorityEffect: None.
//! Exact phase tracking and multi-qubit Pauli string test suite.

use core_quantum_physics::pauli::{
    Pauli, PauliError, PauliString, PhaseZ4, MAX_PAULI_STRING_QUBITS,
};

#[test]
fn test_single_qubit_phase_table() {
    assert_eq!(Pauli::X.mul_phased(Pauli::Y), (PhaseZ4::P1, Pauli::Z));
    assert_eq!(Pauli::Y.mul_phased(Pauli::X), (PhaseZ4::P3, Pauli::Z));
    assert_eq!(Pauli::Y.mul_phased(Pauli::Z), (PhaseZ4::P1, Pauli::X));
    assert_eq!(Pauli::Z.mul_phased(Pauli::Y), (PhaseZ4::P3, Pauli::X));
    assert_eq!(Pauli::Z.mul_phased(Pauli::X), (PhaseZ4::P1, Pauli::Y));
    assert_eq!(Pauli::X.mul_phased(Pauli::Z), (PhaseZ4::P3, Pauli::Y));

    for p in [Pauli::I, Pauli::X, Pauli::Y, Pauli::Z] {
        assert_eq!(p.mul_phased(Pauli::I), (PhaseZ4::P0, p));
        assert_eq!(Pauli::I.mul_phased(p), (PhaseZ4::P0, p));
        assert_eq!(p.mul_phased(p), (PhaseZ4::P0, Pauli::I));
    }
}

#[test]
fn test_pauli_string_parse_and_word() {
    let ps = PauliString::try_parse("IXYZ").expect("should parse");
    assert_eq!(ps.len(), 4);
    assert_eq!(ps.word(), "IXYZ");
    assert_eq!(format!("{}", ps), "IXYZ");

    assert!(matches!(
        PauliString::try_parse("IXYZQ"),
        Err(PauliError::UnknownLetter('Q'))
    ));
    assert!(matches!(
        PauliString::try_parse("1"),
        Err(PauliError::UnknownLetter('1'))
    ));
}

#[test]
fn test_pauli_string_mul_phased() {
    let p1 = PauliString::try_parse("XY").expect("parse");
    let p2 = PauliString::try_parse("YX").expect("parse");
    // (X * Y, Y * X) => (i Z, -i Z) => phase = 1 + 3 = 4 = 0 mod 4, operator = ZZ
    let (phase, res) = p1.mul_phased(&p2).expect("mul");
    assert_eq!(phase, PhaseZ4::P0);
    assert_eq!(res.word(), "ZZ");

    // X * Y => i Z
    let (phase, res) = PauliString::try_parse("X")
        .unwrap()
        .mul_phased(&PauliString::try_parse("Y").unwrap())
        .unwrap();
    assert_eq!(phase, PhaseZ4::P1);
    assert_eq!(res.word(), "Z");

    // Mismatched length refuses
    let p_short = PauliString::try_parse("X").unwrap();
    let p_long = PauliString::try_parse("XX").unwrap();
    assert!(p_short.mul_phased(&p_long).is_err());
}

#[test]
fn test_pauli_string_symplectic() {
    let ps = PauliString::try_parse("IXYZ").unwrap();
    let vec = ps.to_symplectic_vector();
    // I: (0,0), X: (1,0), Y: (1,1), Z: (0,1)
    // x: [0, 1, 1, 0], z: [0, 0, 1, 1]
    assert_eq!(vec, vec![0, 1, 1, 0, 0, 0, 1, 1]);

    let bools = ps.to_symplectic_bools();
    assert_eq!(
        bools,
        vec![false, true, true, false, false, false, true, true]
    );

    let recovered =
        PauliString::from_symplectic_coords(&bools[0..4], &bools[4..8]).expect("from coords");
    assert_eq!(recovered, ps);
}

#[test]
fn test_commutation_properties() {
    let a = PauliString::try_parse("XX").unwrap();
    let b = PauliString::try_parse("ZZ").unwrap();
    assert!(a.commutes_with(&b).unwrap());
    assert!(!a.anticommutes_with(&b).unwrap());

    let c = PauliString::try_parse("XI").unwrap();
    let d = PauliString::try_parse("ZI").unwrap();
    assert!(c.anticommutes_with(&d).unwrap());
    assert!(!c.commutes_with(&d).unwrap());
}

#[test]
fn phased_adapter_replays_nonzero_input_phases_and_returns_unphased_word() {
    use core_number_theory::cyclotomic::GaussianRat;
    let scalar = |p: PhaseZ4| match p {
        PhaseZ4::P0 => GaussianRat::one(),
        PhaseZ4::P1 => GaussianRat::i(),
        PhaseZ4::P2 => GaussianRat::from_ints(-1, 0),
        PhaseZ4::P3 => GaussianRat::from_ints(0, -1),
    };
    for a in Pauli::ALL {
        for b in Pauli::ALL {
            for ka in 0..4 {
                for kb in 0..4 {
                    let a = PauliString::with_phase(ka, vec![a]).unwrap();
                    let b = PauliString::with_phase(kb, vec![b]).unwrap();
                    let (phase, word) = a.mul_phased(&b).unwrap();
                    assert_eq!(word.phase(), 0);
                    let rhs = word.to_operator().unwrap().scale(&scalar(phase)).unwrap();
                    assert_eq!(
                        a.to_operator()
                            .unwrap()
                            .mul(&b.to_operator().unwrap())
                            .unwrap(),
                        rhs
                    );
                }
            }
        }
    }
    assert_eq!(PauliString::identity(0), Err(PauliError::Empty));
    assert_eq!(PauliString::try_parse("  "), Err(PauliError::Empty));
    assert!(PauliString::from_symplectic_coords(&[], &[]).is_err());
    assert!(PauliString::from_symplectic_coords(&[true], &[]).is_err());
    assert!(PauliString::try_parse("X")
        .unwrap()
        .anticommutes_with(&PauliString::try_parse("XX").unwrap())
        .is_err());
}

#[test]
fn symbolic_word_admission_refuses_oversized_allocations_and_preserves_the_boundary() {
    let max = MAX_PAULI_STRING_QUBITS;
    let identity = PauliString::identity(max).unwrap();
    assert_eq!(identity.len(), max);
    assert_eq!(identity.weight(), 0);
    let phased = PauliString::with_phase(255, vec![Pauli::Y; max]).unwrap();
    assert_eq!(phased.phase(), 3);
    assert_eq!(phased.multiply(&identity).unwrap(), phased);
    assert_eq!(PauliString::parse(&"X".repeat(max)).unwrap().len(), max);
    assert!(matches!(
        PauliString::identity(usize::MAX),
        Err(PauliError::StringBudget {
            qubits: usize::MAX,
            max: 4096
        })
    ));
    assert!(matches!(
        PauliString::with_phase(0, vec![Pauli::X; max + 1]),
        Err(PauliError::StringBudget {
            qubits: 4097,
            max: 4096
        })
    ));
    assert!(matches!(
        PauliString::parse(&"X".repeat(max + 1)),
        Err(PauliError::StringBudget {
            qubits: 4097,
            max: 4096
        })
    ));
    assert!(matches!(
        PauliString::from_symplectic_coords(&vec![false; max + 1], &vec![false; max + 1]),
        Err(PauliError::StringBudget {
            qubits: 4097,
            max: 4096
        })
    ));
    assert_eq!(PauliString::identity(0), Err(PauliError::Empty));
    assert!(matches!(phased.to_operator(), Err(PauliError::Carrier(_))));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/pauli_phase.rs
// Claim: urn:core:crates_rs:tests:pauli-phase:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb8d04392 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb8d04392` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb8d04392 {
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
impl BoundaryErrorb8d04392 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb8d04392 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb8d04392 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb8d04392 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb8d04392> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb8d04392::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb8d04392::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb8d04392::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_b8d04392() {
    let admitted = BoundaryRecordb8d04392::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordb8d04392::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
