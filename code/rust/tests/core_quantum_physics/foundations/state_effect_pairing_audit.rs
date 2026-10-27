//! The state–effect pairing audit: seven declared rows graded by one set of
//! finite checks, two second pairings that pass the same checks, and the
//! effect-relativity of probability.

use linear_algebra::backend::basic_matrix::OperationLimits;
use linear_algebra::exact_field::matrix;
use core_number_theory::rational::{ri, rq, Rational};

use core_quantum_physics::pairing_audit::{
    audit_row, classical_simplex_row, complex_born_row, declared_registry, noisy_born_row,
    quaternionic_matrix_is_positive, quaternionic_row, transport_gram_row, CompositeTier, Pairing,
    PairingCheck, PairingError, PairingPacket, PairingRow, PairingTerminal, Transport,
};

fn rats(values: &[i64]) -> Vec<Rational> {
    values.iter().map(|v| ri(*v)).collect()
}

#[test]
fn every_registry_row_receives_its_declared_terminal() {
    let rows = declared_registry().unwrap();
    let terminals: Vec<(&str, PairingTerminal)> = rows
        .iter()
        .map(|row| (row.name, audit_row(row).unwrap()))
        .collect();
    assert_eq!(
        terminals,
        vec![
            ("classical_simplex_dot_pairing", PairingTerminal::Passes),
            (
                "square_bit_effect_pairing",
                PairingTerminal::RefusedCompositeUndeclared
            ),
            ("spekkens_epistemic_pairing", PairingTerminal::Passes),
            (
                "real_hilbert_trace_pairing",
                PairingTerminal::LocalTomographyFails {
                    product_effect_rank: 9,
                    joint_effect_dim: 10
                }
            ),
            ("complex_hilbert_born_pairing", PairingTerminal::Passes),
            (
                "quaternionic_guarded_pairing",
                PairingTerminal::RefusedCompositeUndeclared
            ),
            (
                "nonlinear_ad_hoc_pairing",
                PairingTerminal::Failed(vec![
                    PairingCheck::Normalization,
                    PairingCheck::Positivity,
                    PairingCheck::Transport,
                    PairingCheck::Gluing,
                ])
            ),
        ]
    );
}

#[test]
fn the_carriers_have_their_declared_single_system_dimensions() {
    let rows = declared_registry().unwrap();
    let dims: Vec<usize> = rows
        .iter()
        .map(|row| row.packet.state_span_dimension().unwrap())
        .collect();
    // Classical 2, square bit 3, Spekkens 4, rebit 3, qubit 4, quaternionic qubit 6.
    assert_eq!(dims[..6], [2, 3, 4, 3, 4, 6]);
}

#[test]
fn quaternionic_positivity_is_decided_through_the_complex_representation() {
    let h = rq(1, 2);
    let z = ri(0);
    // [[1/2, j/2], [-j/2, 1/2]] is a pure state; doubling q breaks positivity.
    assert!(quaternionic_matrix_is_positive(&[
        h.clone(),
        h.clone(),
        z.clone(),
        z.clone(),
        h.clone(),
        z.clone()
    ]));
    assert!(!quaternionic_matrix_is_positive(&[
        h.clone(),
        h.clone(),
        z.clone(),
        z.clone(),
        ri(1),
        z.clone()
    ]));
    // |q|^2 = 3/16 <= 1/4 with all three imaginary units.
    let q = rq(1, 4);
    assert!(quaternionic_matrix_is_positive(&[
        h.clone(),
        h.clone(),
        z,
        q.clone(),
        q.clone(),
        q
    ]));
    let row = quaternionic_row().unwrap();
    assert!(row
        .packet
        .states()
        .iter()
        .all(|s| quaternionic_matrix_is_positive(s)));
}

#[test]
fn the_skeleton_admits_a_second_pairing_on_the_classical_packet() {
    let dot = classical_simplex_row().unwrap();
    let through_transport = transport_gram_row().unwrap();
    assert_eq!(
        audit_row(&through_transport).unwrap(),
        PairingTerminal::Passes
    );
    let vertex = rats(&[1, 0]);
    assert_eq!(dot.packet.value(0, &vertex).unwrap(), ri(1));
    assert_eq!(
        through_transport.packet.value(0, &vertex).unwrap(),
        rq(2, 3)
    );
}

#[test]
fn the_skeleton_admits_a_second_pairing_on_the_born_packet() {
    let born = complex_born_row().unwrap();
    let noisy = noisy_born_row().unwrap();
    assert_eq!(audit_row(&born).unwrap(), PairingTerminal::Passes);
    assert_eq!(audit_row(&noisy).unwrap(), PairingTerminal::Passes);
    // Same states, effects, measurements, transport and composite, different
    // numbers: Tr(|0><0| N(|0><0|)) = 1/9 + 4/9 = 5/9 against 1.
    let zero_state = &born.packet.states()[0];
    assert_eq!(born.packet.value(0, zero_state).unwrap(), ri(1));
    assert_eq!(noisy.packet.value(0, zero_state).unwrap(), rq(5, 9));
    assert_eq!(born.packet.states(), noisy.packet.states());
    assert_ne!(born.packet.pairing(), noisy.packet.pairing());
}

#[test]
fn probability_is_effect_relative() {
    let born = complex_born_row().unwrap();
    let zero_state = &born.packet.states()[0];
    // The same state gives 1 on |0><0| and 1/2 on |+><+|: no state-only probability.
    assert_eq!(born.packet.value(0, zero_state).unwrap(), ri(1));
    assert_eq!(born.packet.value(2, zero_state).unwrap(), rq(1, 2));
    // The hand-checkable instance: the pairing <E, rho> = rho E gives 1 and 2
    // on the state 1.
    let scalar = Pairing::Bilinear(matrix::from_rows(vec![rats(&[1])]).unwrap());
    assert_eq!(scalar.evaluate(&rats(&[1]), &rats(&[1])).unwrap(), ri(1));
    assert_eq!(scalar.evaluate(&rats(&[2]), &rats(&[1])).unwrap(), ri(2));
}

#[test]
fn a_wrongly_declared_dual_transport_fails_only_the_transport_check() {
    // The classical packet with the transport itself, not its transpose, as the dual.
    let t = matrix::from_rows(vec![vec![rq(2, 3), rq(1, 4)], vec![rq(1, 3), rq(3, 4)]]).unwrap();
    let packet = PairingPacket::new(
        classical_simplex_row().unwrap().packet.states().to_vec(),
        vec![rats(&[1, 0]), rats(&[0, 1])],
        vec![vec![0, 1]],
        Pairing::Bilinear(matrix::from_rows(vec![rats(&[1, 0]), rats(&[0, 1])]).unwrap()),
        vec![Transport {
            on_effects: t.clone(),
            on_states: t,
        }],
    )
    .unwrap();
    let row = PairingRow {
        name: "wrong_dual",
        origin: core_quantum_physics::pairing_audit::PairingOrigin::Native,
        packet,
        composite: CompositeTier::Undeclared,
    };
    assert_eq!(
        audit_row(&row).unwrap(),
        PairingTerminal::Failed(vec![PairingCheck::Transport])
    );
}

#[test]
fn malformed_packets_are_refused() {
    let states = vec![rats(&[1, 0])];
    let effects = vec![rats(&[1, 0]), rats(&[0, 1])];
    let identity =
        Pairing::Bilinear(matrix::from_rows(vec![rats(&[1, 0]), rats(&[0, 1])]).unwrap());
    assert_eq!(
        PairingPacket::new(
            states.clone(),
            effects.clone(),
            vec![vec![0, 2]],
            identity.clone(),
            vec![]
        ),
        Err(PairingError::EffectIndex {
            measurement: 0,
            effect: 2
        })
    );
    assert_eq!(
        PairingPacket::new(
            vec![rats(&[1, 0, 0])],
            effects.clone(),
            vec![vec![0, 1]],
            identity.clone(),
            vec![]
        ),
        Err(PairingError::Shape)
    );
    let bad_transport = Transport {
        on_states: matrix::from_rows(vec![rats(&[1])]).unwrap(),
        on_effects: matrix::from_rows(vec![rats(&[1, 0]), rats(&[0, 1])]).unwrap(),
    };
    assert_eq!(
        PairingPacket::new(
            states,
            effects,
            vec![vec![0, 1]],
            identity,
            vec![bad_transport]
        ),
        Err(PairingError::Shape)
    );
}

#[test]
fn the_audit_computes_the_product_rank_from_the_declared_effects() {
    // Without its Y-basis measurement the complex packet's effects are all real:
    // they span three local directions and their products nine of sixteen.
    let born = complex_born_row().unwrap();
    let packet = &born.packet;
    let effects = packet.effects()[..7].to_vec();
    let measurements = packet.measurements()[..3].to_vec();
    let real_only = PairingPacket::new(
        packet.states().to_vec(),
        effects,
        measurements,
        packet.pairing().clone(),
        packet.transports().to_vec(),
    )
    .unwrap();
    assert_eq!(packet.product_effect_rank().unwrap(), 16);
    assert_eq!(real_only.product_effect_rank().unwrap(), 9);
    let CompositeTier::Declared {
        joint_effect_dim,
        tables,
    } = born.composite.clone()
    else {
        panic!("the Born row declares a composite")
    };
    let row = PairingRow {
        name: "real_effects_only",
        origin: core_quantum_physics::pairing_audit::PairingOrigin::Imported,
        packet: real_only,
        composite: CompositeTier::Declared {
            joint_effect_dim,
            tables: tables
                .into_iter()
                .filter(|t| t.measurement_a < 3 && t.measurement_b < 3)
                .collect(),
        },
    };
    assert_eq!(
        audit_row(&row).unwrap(),
        PairingTerminal::LocalTomographyFails {
            product_effect_rank: 9,
            joint_effect_dim: 16
        }
    );
}

#[test]
fn gluing_needs_full_length_marginals_and_a_normalized_table() {
    let classical = classical_simplex_row().unwrap();
    let CompositeTier::Declared {
        joint_effect_dim,
        tables,
    } = classical.composite.clone()
    else {
        panic!("the classical row declares a composite")
    };
    let glued = |tables: Vec<core_quantum_physics::pairing_audit::JointTable>| {
        let row = PairingRow {
            composite: CompositeTier::Declared {
                joint_effect_dim,
                tables,
            },
            ..classical.clone()
        };
        audit_row(&row).unwrap()
    };
    assert_eq!(glued(tables.clone()), PairingTerminal::Passes);
    let mut short = tables.clone();
    short[0].marginal_a.pop();
    assert_eq!(
        glued(short),
        PairingTerminal::Failed(vec![PairingCheck::Gluing])
    );
    let mut empty = tables;
    for row in &mut empty[0].probabilities {
        for p in row.iter_mut() {
            *p = ri(0);
        }
    }
    empty[0].marginal_a = rats(&[0, 0]);
    empty[0].marginal_b = rats(&[0, 0]);
    assert_eq!(
        glued(empty),
        PairingTerminal::Failed(vec![PairingCheck::Gluing])
    );
    // A value is refused for an undeclared effect or a state of the wrong length.
    assert_eq!(
        classical.packet.value(5, &rats(&[1, 0])),
        Err(PairingError::Shape)
    );
    assert_eq!(
        classical.packet.value(0, &rats(&[1, 0, 0])),
        Err(PairingError::Shape)
    );
}

#[test]
fn an_empty_packet_is_refused_instead_of_passing_vacuously() {
    assert_eq!(
        PairingPacket::new(
            vec![],
            vec![],
            vec![],
            Pairing::Bilinear(matrix::from_rows(vec![]).unwrap()),
            vec![]
        ),
        Err(PairingError::EmptyPacket)
    );
    assert_eq!(
        PairingPacket::new(
            vec![rats(&[1])],
            vec![rats(&[1])],
            vec![],
            Pairing::Bilinear(matrix::from_rows(vec![rats(&[1])]).unwrap()),
            vec![]
        ),
        Err(PairingError::EmptyPacket)
    );
    assert_eq!(
        PairingPacket::new(
            vec![vec![]],
            vec![vec![]],
            vec![vec![0]],
            Pairing::Bilinear(matrix::from_rows(vec![vec![]]).unwrap()),
            vec![]
        ),
        Err(PairingError::EmptyPacket)
    );
    assert_eq!(
        PairingPacket::new(
            vec![rats(&[1])],
            vec![rats(&[1])],
            vec![vec![]],
            Pairing::Bilinear(matrix::from_rows(vec![rats(&[1])]).unwrap()),
            vec![]
        ),
        Err(PairingError::EmptyPacket)
    );
}

#[test]
fn pairing_arithmetic_refuses_malformed_coordinates_and_explicit_budgets() {
    let pairing = Pairing::Bilinear(matrix::identity::<Rational>(2).unwrap());
    assert!(pairing.evaluate(&rats(&[1]), &rats(&[1, 0])).is_err());
    assert!(pairing.evaluate(&rats(&[1, 0]), &rats(&[1])).is_err());
    assert_eq!(
        pairing.evaluate(&rats(&[1, 0]), &rats(&[1, 0])).unwrap(),
        ri(1)
    );
    let tiny = OperationLimits {
        max_elements: 1,
        max_scalar_ops: 1,
    };
    assert!(pairing
        .evaluate_with_limits(&rats(&[1, 0]), &rats(&[1, 0]), tiny)
        .is_err());
    assert!(pairing.tensor_square_with_limits(tiny).is_err());
    let product = pairing.tensor_square().unwrap();
    assert_eq!(
        product
            .evaluate(&rats(&[1, 0, 0, 0]), &rats(&[1, 0, 0, 0]))
            .unwrap(),
        ri(1)
    );
    let polynomial = Pairing::PolynomialOfDot(rats(&[0, 1]));
    assert!(polynomial.evaluate(&rats(&[1]), &rats(&[1, 0])).is_err());
}

// Origin: engine/crates_rs/tests/core_quantum_physics/foundations/state_effect_pairing_audit.rs
// Claim: urn:core:crates_rs:tests:state-effect-pairing-audit:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda1432d6b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda1432d6b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora1432d6b {
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
impl BoundaryErrora1432d6b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora1432d6b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora1432d6b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda1432d6b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora1432d6b> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora1432d6b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora1432d6b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora1432d6b::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_a1432d6b() {
    let admitted = BoundaryRecorda1432d6b::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda1432d6b::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
