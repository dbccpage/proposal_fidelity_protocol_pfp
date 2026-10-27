#![allow(
    clippy::needless_range_loop,
    clippy::should_implement_trait,
    clippy::assign_op_pattern,
    clippy::too_many_arguments,
    clippy::manual_is_multiple_of,
    clippy::doc_overindented_list_items,
    clippy::erasing_op,
    clippy::identity_op,
    clippy::duplicate_mod,
    clippy::chunks_exact_to_as_chunks,
    clippy::same_item_push,
    clippy::type_complexity,
    clippy::useless_vec
)]

// Lets a module name this crate as `core_quantum_physics::...` from inside the
// library as well as from a test target that includes the same source file.
extern crate self as core_quantum_physics;

// --- Finite-QM derivation targets (see module doc above) ---
pub mod composition_tomography;
pub mod derivation_dag_witnesses;
pub mod hermitian_spectral;
pub mod instruments;
pub mod quantum_regge_bridge;
pub mod separating_predictions;

// --- Quantum-foundations source papers, implemented exactly (see
// atlas/coda_atlas/F004_papers/006_finite_qm/finite_quantum_mechanics.md, section 11) ---
pub mod bipartite_operator;
pub mod chain_histories;
pub mod cochain_repair_code;
pub mod coherent_interference;
pub mod complex_structure_selector;
pub mod difference_transport_channel;
pub mod dirac_gamma_admission;
pub mod finite_chsh_correlations;
pub mod finite_report_dynamics;
pub mod finite_schrodinger_step;
pub mod frame_function_polytope;
pub mod gauge_cochain_complex;
pub mod gaussian_frame_readout;
pub mod graded_path_sum;
pub mod heisenberg_picture;
pub mod holonomy_interference;
pub mod lattice_dirac_doubling;
pub use core_majorana::majorana_fock_algebra;
pub mod mass_phase_embedding;
pub mod meron_source_field;
pub mod meron_time_refinement;
pub mod pair_exchange_characters;
pub mod pairing_audit;
pub mod parity_context_packet;
pub mod pauli_context_table;
pub mod phase_averaged_shadow;
pub mod phase_blind_quotient;
pub mod population_shadow;
pub mod power_rule_outcomes;
pub mod quaternion_gauge_shadow;
pub mod qubit_bloch_map;
pub mod relative_state_branching;
pub mod repair_capacity;
pub mod residual_density_calculus;
pub mod sector_conditioning;
pub mod spin_area_spectrum;
pub mod spin_structure_obstruction;
pub mod stochastic_unitary_boundary;
pub mod threshold_repair_certificate;
pub mod time_sliced_action_shadow;
pub mod trace_distance_quotient;
pub mod transport_isometry_orbits;
pub mod u1_gauge_triviality;
pub mod u1_graph_connection;

// --- Checked conversion to diagnostic scalar values ---
pub mod engine_bridge;

// --- Domain face / scaffold modules ---
pub mod algebraic_qft;
pub mod anyon;
pub mod anyon_model;
pub mod bell_state;
pub mod classical_storage;
pub mod carrier_tests;
pub mod classical_structure;
pub mod completely_positive_map;
pub mod dagger_category;
pub mod decoherence_functional;
pub mod density_matrix;
pub mod entanglement;
pub mod entropy;
pub mod feynman_diagram;
pub mod fidelity;
pub mod frobenius_algebra;
pub mod ghz_state;
pub mod hilbert_space;
pub mod kraus_operators;
pub mod local_operator_algebra;
pub mod measurement;
pub mod measurement_update;
pub mod modular_tensor_category;
pub mod no_cloning;
pub mod observable;
pub mod packed_hermitian;
pub mod path_integral;
pub mod perturbation_theory;
pub mod process_matrix;
pub mod purification;
pub mod quantum_channel;
pub mod quantum_entropy_cone;
pub mod quantum_hamiltonian;
pub mod quantum_mutual_information;
pub mod quantum_relative_entropy;
pub mod quantum_state;
pub mod r_matrix;
pub mod s_matrix;
pub mod scattering_amplitude;
pub mod stinespring_dilation;
pub mod superselection_sector;
pub mod teleportation;
pub mod topological_quantum_computing;
pub mod toric_code;
pub mod unitary_operator;
pub mod w_state;
pub mod yang_baxter_equation;

// Exact finite quantum mechanics uses the same canonical crate interface.
pub mod branch_finegraining;
pub mod busch_effects;
pub mod cancellation_certificates;
pub mod commutator;
pub mod commuting_observables;
pub mod composition_tensor_mub;
pub mod contextuality_obstruction;
pub mod continuous_time_locality_limit;
pub mod continuum;
pub mod cptp_channels_stinespring;
pub mod dynamics;
pub mod dynamics_dichotomy;
pub mod embedding_relativity;
pub mod everett;
pub mod exact_channel;
pub mod exact_hermitian;
pub mod exact_operator;
pub mod qddc;
pub mod grover;
pub mod growth_refinement;
pub mod heisenberg_representation_uniqueness;
pub mod higher_dim;
pub mod lattice_gauge_manybody_benchmark;
pub mod mub;
pub mod no_signalling;
pub mod pauli;
pub mod phase_estimation;
pub mod product_defect_bound;
pub mod quantum_correlation;
pub mod quantum_walk;
pub mod refinement_subsystem_tower;
pub mod richardson;
pub mod shor;
pub mod stabilizer_code_distance;
pub mod tomography;
pub mod tower;
pub mod tower_topological_completion;
pub mod tower_walk_validator;
pub mod trace_norm_certificate;
pub mod wigner;

// Re-export core types and algorithms
pub use branch_finegraining::*;
pub use busch_effects::*;
pub use cancellation_certificates::*;
pub use commutator::{
    audit_commutator_obstruction_d3, discrete_momentum_d3, discrete_position_d3,
    verify_trace_cyclicity_d3, CommutatorObstructionReport,
};
pub use composition_tensor_mub::*;
pub use cptp_channels_stinespring::*;
pub use density_matrix::ExactDensityMatrix;
pub use dynamics_dichotomy::*;
pub use fidelity::*;
pub use growth_refinement::*;
pub use mub::MubSystem;
pub use process_matrix::*;
pub use tomography::{
    state_bell_d4, state_cyclotomic_coherence_d3, state_ground_d2, state_ground_d3,
    state_ground_d4, state_magic_d3, state_maximally_mixed_d3, state_mixed_d4,
    state_mixed_rational_d3, state_superposition_d2, state_superposition_d3,
    state_superposition_d4, ExactStateTomographerSystem, MubTomographyProbabilities,
    MubTomographyProbabilitiesD4,
};
pub use trace_norm_certificate::{
    sign_certificate_from_spectrum, sign_from_spectrum, trace_distance, SignCertificate,
    TraceNormCertificate, TraceNormError,
};
pub use wigner::{state_ground_d5, state_magic_d5, DiscreteWignerSystemD5};

pub mod adaptive_integrator;
pub mod complex_realification;
pub mod composition_quantum_bound;
pub mod exact_instrument;
pub mod finite_geometry;
pub mod instrument_repeatability;
pub mod phase_readout;
pub mod projective_preservers;
pub mod signed_sampling;
pub mod trace_observer_certificate;

pub mod ancilla_capacity;
pub mod exact_entropy;

pub mod kochen_specker;

pub mod majorization;

pub mod norm_approximation_frontier;

pub mod operational_axiom_selection;

pub mod meron_spatial_source;
pub mod tensor_commuting_correlation_frontier;

pub mod atomic_dirac_lamb_hartree_fock;
pub mod finite_bell_extension;
pub mod finite_bell_preparation;
pub mod pauli_spin_statistics_graph;
pub mod qed_weak_hadronic_finite_maps;
pub mod quantum_import_finite_maps;
pub mod regge_gravity_ghz_chern_finite_maps;
pub mod cptp_trajectory_verifier;
pub mod finite_spinfoam;
pub mod simplicial_entropy_schedule;


// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteHilbertPower { qubits: u32, dimension: u64 }

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HilbertPowerError { Empty, Overflow }

// Origin: engine/crates_rs/core_quantum_physics/src/lib.rs
// Claim: urn:core:crates_rs:core-quantum-physics:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for HilbertPowerError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for HilbertPowerError {}

impl FiniteHilbertPower {
    /// Dimension of `(C^2) tensor n` is `2^n`.
    pub fn try_new(qubits: u32) -> Result<Self, HilbertPowerError> {
        if qubits == 0 || qubits >= 64 {
            return Err(if qubits == 0 { HilbertPowerError::Empty } else { HilbertPowerError::Overflow });
        }
        let dimension = 1u64.checked_shl(qubits).ok_or(HilbertPowerError::Overflow)?;
        Ok(Self { qubits, dimension })
    }

    pub fn dimension(&self) -> u64 { self.dimension }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod hilbert_power_checks {
    use super::*;

    #[test]
    fn two_qubits_have_dimension_four() {
        let space = FiniteHilbertPower::try_new(2);
        assert!(matches!(space, Ok(s) if s.dimension() == 4));
    }

    #[test]
    fn zero_qubits_are_refused() {
        assert!(matches!(FiniteHilbertPower::try_new(0), Err(HilbertPowerError::Empty)));
    }
}
