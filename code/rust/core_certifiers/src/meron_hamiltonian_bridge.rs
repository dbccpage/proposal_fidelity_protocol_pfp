use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};
use thiserror::Error;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LoopDescriptor {
    pub temporal_winding: u32,
    pub bond_count: u32,
}

impl LoopDescriptor {
    /// Liu-Chandrasekharan-Kaul loop sign:
    /// eta(l) = (-1)^(n_t + n_b/2 + 1).
    pub fn sign_factor(&self) -> Result<i8, HamiltonianBridgeError> {
        if !self.bond_count.is_multiple_of(2) {
            return Err(HamiltonianBridgeError::OddBondCount {
                bond_count: self.bond_count,
            });
        }
        let parity = (self.temporal_winding + self.bond_count / 2 + 1) % 2;
        Ok(if parity == 0 { 1 } else { -1 })
    }

    pub fn is_meron(&self) -> Result<bool, HamiltonianBridgeError> {
        Ok(self.sign_factor()? == -1)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LoopSkeleton {
    pub loops: Vec<LoopDescriptor>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BridgeCheckSummary {
    pub loop_count: usize,
    pub meron_count: usize,
    pub total_orientations: u64,
    pub signed_orientation_sum: i64,
    pub candidate_flip_total_on_multi_meron_sector: bool,
    pub fixed_point_free: bool,
    pub absolute_weight_preserving: bool,
    pub sign_reversing: bool,
    pub nonzero_meron_sector_cancels: bool,
    pub zero_meron_sector_positive: bool,
}

pub const LCK_HAMILTONIAN_FAMILY_ID: &str = "LCK_HJ_HU_HALF_FILLED_BIPARTITE";

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LoopExtractionPacket {
    pub family_id: String,
    pub bipartite_lattice: bool,
    pub loops: Vec<LoopDescriptor>,
    pub orientation_abs_weights: Vec<i64>,
    pub orientation_signs: Vec<i8>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LoopExtractionSummary {
    pub family_id: String,
    pub loop_count: usize,
    pub meron_count: usize,
    pub total_orientations: u64,
    pub common_abs_weight: i64,
    pub sign_factorization_verified: bool,
    pub orientation_independent_weight_verified: bool,
    pub licenses_independent_loop_theorem: bool,
    pub bridge_summary: BridgeCheckSummary,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LoopGraphEdge {
    pub target: usize,
    pub temporal_wrap: bool,
    pub spatial_bond: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LoopGraphExtractionPacket {
    pub family_id: String,
    pub bipartite_lattice: bool,
    pub edges: Vec<LoopGraphEdge>,
    pub orientation_abs_weights: Vec<i64>,
    pub orientation_signs: Vec<i8>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LoopGraphExtractionSummary {
    pub derived_loops: Vec<LoopDescriptor>,
    pub extraction_summary: LoopExtractionSummary,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LoopOrientationSignEvidence {
    pub temporal_boundary_parity: u8,
    pub bond_permutation_parity: u8,
    pub closure_permutation_parity: u8,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LoopOrientationSignExtractionPacket {
    pub family_id: String,
    pub bipartite_lattice: bool,
    pub loops: Vec<LoopDescriptor>,
    pub orientation_abs_weights: Vec<i64>,
    pub sign_evidence: Vec<LoopOrientationSignEvidence>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LoopOrientationSignExtractionSummary {
    pub loop_signs: Vec<i8>,
    pub orientation_signs: Vec<i8>,
    pub extraction_summary: LoopExtractionSummary,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LoopGraphWithDerivedOrientationSignsPacket {
    pub family_id: String,
    pub bipartite_lattice: bool,
    pub edges: Vec<LoopGraphEdge>,
    pub orientation_abs_weights: Vec<i64>,
    pub sign_evidence: Vec<LoopOrientationSignEvidence>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LoopGraphWithDerivedOrientationSignsSummary {
    pub derived_loops: Vec<LoopDescriptor>,
    pub sign_summary: LoopOrientationSignExtractionSummary,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LoopGraphWithAutoOrientationSignsPacket {
    pub family_id: String,
    pub bipartite_lattice: bool,
    pub edges: Vec<LoopGraphEdge>,
    pub orientation_abs_weights: Vec<i64>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LoopGraphWithAutoOrientationSignsSummary {
    pub derived_loops: Vec<LoopDescriptor>,
    pub derived_sign_evidence: Vec<LoopOrientationSignEvidence>,
    pub sign_summary: LoopOrientationSignExtractionSummary,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum LocalOperatorKind {
    TemporalPropagation,
    HjBond,
    HuOnsite,
}

impl LocalOperatorKind {
    fn spatial_bond(self) -> bool {
        matches!(self, LocalOperatorKind::HjBond)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalHamiltonianMatrixElement {
    pub source: usize,
    pub target: usize,
    pub operator: LocalOperatorKind,
    pub temporal_wrap: bool,
    pub abs_matrix_element: i64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OperatorToSuccessorGraphPacket {
    pub family_id: String,
    pub bipartite_lattice: bool,
    pub vertex_count: usize,
    pub matrix_elements: Vec<LocalHamiltonianMatrixElement>,
    pub orientation_matrix_signs: Vec<i8>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OperatorToSuccessorGraphSummary {
    pub local_matrix_element_count: usize,
    pub local_abs_weight_product: i64,
    pub graph_summary: LoopGraphExtractionSummary,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OperatorToSuccessorGraphWithDerivedSignsPacket {
    pub family_id: String,
    pub bipartite_lattice: bool,
    pub vertex_count: usize,
    pub matrix_elements: Vec<LocalHamiltonianMatrixElement>,
    pub sign_evidence: Vec<LoopOrientationSignEvidence>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OperatorToSuccessorGraphWithDerivedSignsSummary {
    pub local_matrix_element_count: usize,
    pub local_abs_weight_product: i64,
    pub graph_sign_summary: LoopGraphWithDerivedOrientationSignsSummary,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OperatorToSuccessorGraphWithAutoSignsPacket {
    pub family_id: String,
    pub bipartite_lattice: bool,
    pub vertex_count: usize,
    pub matrix_elements: Vec<LocalHamiltonianMatrixElement>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OperatorToSuccessorGraphWithAutoSignsSummary {
    pub local_matrix_element_count: usize,
    pub local_abs_weight_product: i64,
    pub graph_auto_sign_summary: LoopGraphWithAutoOrientationSignsSummary,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LckSymbolicLocalMatrixRow {
    pub source: usize,
    pub target: usize,
    pub operator: LocalOperatorKind,
    pub temporal_wrap: bool,
    pub source_up_state: u8,
    pub target_up_state: u8,
    pub source_down_state: u8,
    pub target_down_state: u8,
    pub onsite_site: Option<u8>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LckSymbolicLocalMatrixPacket {
    pub family_id: String,
    pub bipartite_lattice: bool,
    pub vertex_count: usize,
    pub rows: Vec<LckSymbolicLocalMatrixRow>,
    pub orientation_matrix_signs: Vec<i8>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LckSymbolicLocalMatrixSummary {
    pub single_spin_h_matrix: [[i64; 4]; 4],
    pub signed_local_matrix_elements: Vec<i64>,
    pub derived_operator_packet: OperatorToSuccessorGraphPacket,
    pub operator_summary: OperatorToSuccessorGraphSummary,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LckSymbolicLocalMatrixDerivedSignPacket {
    pub family_id: String,
    pub bipartite_lattice: bool,
    pub vertex_count: usize,
    pub rows: Vec<LckSymbolicLocalMatrixRow>,
    pub sign_evidence: Vec<LoopOrientationSignEvidence>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LckSymbolicLocalMatrixDerivedSignSummary {
    pub single_spin_h_matrix: [[i64; 4]; 4],
    pub signed_local_matrix_elements: Vec<i64>,
    pub derived_operator_packet: OperatorToSuccessorGraphWithDerivedSignsPacket,
    pub operator_summary: OperatorToSuccessorGraphWithDerivedSignsSummary,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LckSymbolicLocalMatrixAutoSignPacket {
    pub family_id: String,
    pub bipartite_lattice: bool,
    pub vertex_count: usize,
    pub rows: Vec<LckSymbolicLocalMatrixRow>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LckSymbolicLocalMatrixAutoSignSummary {
    pub single_spin_h_matrix: [[i64; 4]; 4],
    pub signed_local_matrix_elements: Vec<i64>,
    pub derived_operator_packet: OperatorToSuccessorGraphWithAutoSignsPacket,
    pub operator_summary: OperatorToSuccessorGraphWithAutoSignsSummary,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LckPhysicalGraphTransportPacket {
    pub family_id: String,
    pub bipartite_lattice: bool,
    pub vertex_count: usize,
    pub rows: Vec<LckSymbolicLocalMatrixRow>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LckPhysicalGraphTransportSummary {
    pub transport_continuity_verified: bool,
    pub symbolic_auto_sign_summary: LckSymbolicLocalMatrixAutoSignSummary,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LckGlobalSiteTransportRow {
    pub source: usize,
    pub target: usize,
    pub operator: LocalOperatorKind,
    pub temporal_wrap: bool,
    pub left_site: usize,
    pub right_site: usize,
    pub hu_site: Option<usize>,
    pub source_up_occupancy: Vec<u8>,
    pub target_up_occupancy: Vec<u8>,
    pub source_down_occupancy: Vec<u8>,
    pub target_down_occupancy: Vec<u8>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LckGlobalSiteTransportPacket {
    pub family_id: String,
    pub bipartite_lattice: bool,
    pub site_count: usize,
    pub vertex_count: usize,
    pub rows: Vec<LckGlobalSiteTransportRow>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LckGlobalSiteTransportSummary {
    pub global_transport_continuity_verified: bool,
    pub derived_local_rows: Vec<LckSymbolicLocalMatrixRow>,
    pub symbolic_auto_sign_summary: LckSymbolicLocalMatrixAutoSignSummary,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GlobalSiteShuttleFamily {
    pub path_length: usize,
    pub hu_insertions_per_hop: usize,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GlobalSiteShuttleFamilySummary {
    pub path_length: usize,
    pub hu_insertions_per_hop: usize,
    pub site_count: usize,
    pub row_count: usize,
    pub signed_local_matrix_elements: Vec<i64>,
    pub derived_loops: Vec<LoopDescriptor>,
    pub derived_sign_evidence: Vec<LoopOrientationSignEvidence>,
    pub orientation_signs: Vec<i8>,
    pub bridge_summary: BridgeCheckSummary,
    pub transport_summary: LckGlobalSiteTransportSummary,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HuDecoratedMeronCycleFamily {
    pub hu_insertions_per_arc: usize,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HuDecoratedMeronCycleSummary {
    pub hu_insertions_per_arc: usize,
    pub row_count: usize,
    pub signed_local_matrix_elements: Vec<i64>,
    pub derived_loops: Vec<LoopDescriptor>,
    pub derived_sign_evidence: Vec<LoopOrientationSignEvidence>,
    pub orientation_signs: Vec<i8>,
    pub transport_summary: LckPhysicalGraphTransportSummary,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HuDecoratedLoopFamily {
    pub loop_count: usize,
    pub meron_mask: u64,
    pub hu_insertions_per_arc: usize,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HuDecoratedLoopFamilySummary {
    pub loop_count: usize,
    pub meron_mask: u64,
    pub hu_insertions_per_arc: usize,
    pub row_count: usize,
    pub signed_local_matrix_elements: Vec<i64>,
    pub derived_loops: Vec<LoopDescriptor>,
    pub derived_sign_evidence: Vec<LoopOrientationSignEvidence>,
    pub orientation_signs: Vec<i8>,
    pub bridge_summary: BridgeCheckSummary,
    pub transport_summary: LckPhysicalGraphTransportSummary,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FamilyCarrierSummary {
    pub loop_count: usize,
    pub carrier_size: u64,
    pub zero_sector_size: u64,
    pub multi_sector_size: u64,
    pub z_all: i64,
    pub z_zero: i64,
    pub z_multi: i64,
    pub candidate_flip_total_on_multi_meron_sector: bool,
    pub fixed_point_free: bool,
    pub involutive: bool,
    pub absolute_weight_preserving: bool,
    pub sign_reversing: bool,
    pub complete_orbit_coverage: bool,
    pub non_meron_move_count: u64,
    pub non_meron_moves_preserve_weight_and_sign: bool,
    pub zero_rel_component_count: u64,
    pub observable_survivor_classes: u64,
}

#[derive(Debug, Error, PartialEq, Eq)]
pub enum HamiltonianBridgeError {
    #[error("unsupported Hamiltonian family: {family_id}")]
    UnsupportedHamiltonianFamily { family_id: String },
    #[error("LCK loop extraction requires a bipartite lattice declaration")]
    NonBipartiteLattice,
    #[error("loop bond count must be even, got {bond_count}")]
    OddBondCount { bond_count: u32 },
    #[error(
        "loop skeleton has too many loops for exhaustive orientation enumeration: {loop_count}"
    )]
    TooManyLoops { loop_count: usize },
    #[error("global site shuttle path_length must be positive, got {path_length}")]
    InvalidShuttlePathLength { path_length: usize },
    #[error("meron mask {meron_mask} is outside loop_count {loop_count}")]
    MeronMaskOutOfRange { loop_count: usize, meron_mask: u64 },
    #[error("expected {expected} orientation entries, got {actual}")]
    OrientationEntryCountMismatch { expected: u64, actual: usize },
    #[error("loop graph edge {edge} targets {target}, outside vertex count {vertex_count}")]
    LoopGraphTargetOutOfBounds {
        edge: usize,
        target: usize,
        vertex_count: usize,
    },
    #[error("loop graph vertex {vertex} has indegree {indegree}, expected 1")]
    LoopGraphIndegreeNotOne { vertex: usize, indegree: usize },
    #[error("expected {expected} loop sign-evidence entries, got {actual}")]
    SignEvidenceCountMismatch { expected: usize, actual: usize },
    #[error("loop {loop_index} sign evidence field {parity_name} has non-binary value {value}")]
    InvalidSignEvidenceParity {
        loop_index: usize,
        parity_name: &'static str,
        value: u8,
    },
    #[error("loop {loop_index} temporal-boundary parity is {actual}, expected {expected}")]
    TemporalBoundaryParityMismatch {
        loop_index: usize,
        expected: u8,
        actual: u8,
    },
    #[error("loop {loop_index} bond-permutation parity is {actual}, expected {expected}")]
    BondPermutationParityMismatch {
        loop_index: usize,
        expected: u8,
        actual: u8,
    },
    #[error("loop {loop_index} closure-permutation parity is {actual}, expected 1")]
    ClosurePermutationParityMismatch { loop_index: usize, actual: u8 },
    #[error(
        "operator packet row {row} source {source_vertex} is outside vertex count {vertex_count}"
    )]
    OperatorSourceOutOfBounds {
        row: usize,
        source_vertex: usize,
        vertex_count: usize,
    },
    #[error(
        "operator packet source vertex {source_vertex} appears {multiplicity} times, expected 1"
    )]
    OperatorSourceMultiplicity {
        source_vertex: usize,
        multiplicity: usize,
    },
    #[error("operator packet row {row} has non-positive local absolute matrix element {weight}")]
    NonPositiveLocalMatrixElement { row: usize, weight: i64 },
    #[error("operator packet local absolute weight product overflowed at row {row}")]
    LocalWeightProductOverflow { row: usize },
    #[error("symbolic local row {row} has invalid {state_role} two-site spin state {state}")]
    InvalidTwoSiteSpinState {
        row: usize,
        state_role: &'static str,
        state: u8,
    },
    #[error("symbolic local row {row} has zero matrix element for {operator:?}")]
    ZeroSymbolicLocalMatrixElement {
        row: usize,
        operator: LocalOperatorKind,
    },
    #[error("symbolic H_U onsite row {row} must declare onsite_site")]
    MissingHuOnsiteSite { row: usize },
    #[error("symbolic H_U onsite row {row} has invalid onsite_site {site}")]
    InvalidHuOnsiteSite { row: usize, site: u8 },
    #[error(
        "physical transport row {row} targets vertex {target_vertex}; {spin} target state {row_target_state} does not match successor source state {successor_source_state}"
    )]
    PhysicalTransportStateMismatch {
        row: usize,
        target_vertex: usize,
        spin: &'static str,
        row_target_state: u8,
        successor_source_state: u8,
    },
    #[error(
        "global transport row {row} has {role} occupancy length {actual}, expected site_count {expected}"
    )]
    GlobalOccupancyLengthMismatch {
        row: usize,
        role: &'static str,
        expected: usize,
        actual: usize,
    },
    #[error("global transport row {row} has non-binary {role} occupancy {value} at site {site}")]
    GlobalOccupancyNonBinary {
        row: usize,
        role: &'static str,
        site: usize,
        value: u8,
    },
    #[error("global transport row {row} local site {site} is outside site_count {site_count}")]
    GlobalSiteOutOfBounds {
        row: usize,
        site: usize,
        site_count: usize,
    },
    #[error("global transport row {row} has repeated local sites {left_site} and {right_site}")]
    GlobalLocalSitesNotDistinct {
        row: usize,
        left_site: usize,
        right_site: usize,
    },
    #[error("global H_U row {row} must declare hu_site")]
    GlobalHuSiteMissing { row: usize },
    #[error(
        "global H_U row {row} hu_site {hu_site} is not one of local sites {left_site}, {right_site}"
    )]
    GlobalHuSiteNotInLocalPair {
        row: usize,
        hu_site: usize,
        left_site: usize,
        right_site: usize,
    },
    #[error("global non-H_U row {row} must not declare hu_site")]
    GlobalUnexpectedHuSite { row: usize },
    #[error(
        "global transport row {row} targets vertex {target_vertex}; {spin} site {site} target occupancy {row_target_occupancy} does not match successor source occupancy {successor_source_occupancy}"
    )]
    GlobalTransportStateMismatch {
        row: usize,
        target_vertex: usize,
        spin: &'static str,
        site: usize,
        row_target_occupancy: u8,
        successor_source_occupancy: u8,
    },
    #[error("orientation {orientation} has non-positive absolute weight {weight}")]
    NonPositiveOrientationWeight { orientation: u64, weight: i64 },
    #[error("orientation {orientation} weight is {actual}, expected {expected}")]
    OrientationWeightNotIndependent {
        orientation: u64,
        expected: i64,
        actual: i64,
    },
    #[error("orientation {orientation} sign is {actual}, expected {expected}")]
    OrientationSignMismatch {
        orientation: u64,
        expected: i8,
        actual: i8,
    },
    #[error("orientation {orientation} missing observable value")]
    MissingObservable { orientation: u64 },
    #[error("observable is not invariant under candidate meron flip: {left} -> {right}")]
    ObservableNotInvariant { left: u64, right: u64 },
    #[error("orientation {orientation} has no candidate flip")]
    MissingCandidateFlip { orientation: u64 },
    #[error(
        "state with meron_mask {meron_mask} and orientation {orientation} has no involution flip"
    )]
    MissingInvolutionFlip { meron_mask: u64, orientation: u64 },
}

pub fn lck_single_spin_h_matrix() -> [[i64; 4]; 4] {
    let mut matrix = [[0_i64; 4]; 4];
    for (target, row) in matrix.iter_mut().enumerate() {
        for (source, cell) in row.iter_mut().enumerate() {
            *cell = lck_single_spin_h_entry(target, source);
        }
    }
    matrix
}

fn lck_single_spin_h_entry(target: usize, source: usize) -> i64 {
    match (target, source) {
        (1, 1) | (2, 2) | (1, 2) | (2, 1) => -1,
        _ => 0,
    }
}

fn validate_two_site_spin_state(
    row: usize,
    state_role: &'static str,
    state: u8,
) -> Result<usize, HamiltonianBridgeError> {
    if state < 4 {
        Ok(state as usize)
    } else {
        Err(HamiltonianBridgeError::InvalidTwoSiteSpinState {
            row,
            state_role,
            state,
        })
    }
}

impl LoopOrientationSignEvidence {
    pub fn canonical_for_loop(loop_desc: &LoopDescriptor) -> Result<Self, HamiltonianBridgeError> {
        loop_desc.sign_factor()?;
        Ok(Self {
            temporal_boundary_parity: (loop_desc.temporal_winding % 2) as u8,
            bond_permutation_parity: ((loop_desc.bond_count / 2) % 2) as u8,
            closure_permutation_parity: 1,
        })
    }

    fn validate_binary(
        loop_index: usize,
        parity_name: &'static str,
        value: u8,
    ) -> Result<(), HamiltonianBridgeError> {
        if value <= 1 {
            Ok(())
        } else {
            Err(HamiltonianBridgeError::InvalidSignEvidenceParity {
                loop_index,
                parity_name,
                value,
            })
        }
    }

    pub fn loop_sign(
        &self,
        loop_index: usize,
        loop_desc: &LoopDescriptor,
    ) -> Result<i8, HamiltonianBridgeError> {
        Self::validate_binary(
            loop_index,
            "temporal_boundary_parity",
            self.temporal_boundary_parity,
        )?;
        Self::validate_binary(
            loop_index,
            "bond_permutation_parity",
            self.bond_permutation_parity,
        )?;
        Self::validate_binary(
            loop_index,
            "closure_permutation_parity",
            self.closure_permutation_parity,
        )?;

        loop_desc.sign_factor()?;
        let expected_temporal = (loop_desc.temporal_winding % 2) as u8;
        if self.temporal_boundary_parity != expected_temporal {
            return Err(HamiltonianBridgeError::TemporalBoundaryParityMismatch {
                loop_index,
                expected: expected_temporal,
                actual: self.temporal_boundary_parity,
            });
        }
        let expected_bond = ((loop_desc.bond_count / 2) % 2) as u8;
        if self.bond_permutation_parity != expected_bond {
            return Err(HamiltonianBridgeError::BondPermutationParityMismatch {
                loop_index,
                expected: expected_bond,
                actual: self.bond_permutation_parity,
            });
        }
        if self.closure_permutation_parity != 1 {
            return Err(HamiltonianBridgeError::ClosurePermutationParityMismatch {
                loop_index,
                actual: self.closure_permutation_parity,
            });
        }

        let parity = (u32::from(self.temporal_boundary_parity)
            + u32::from(self.bond_permutation_parity)
            + u32::from(self.closure_permutation_parity))
            % 2;
        Ok(if parity == 0 { 1 } else { -1 })
    }
}

impl LoopOrientationSignExtractionPacket {
    pub fn derive_loop_signs(&self) -> Result<Vec<i8>, HamiltonianBridgeError> {
        if self.sign_evidence.len() != self.loops.len() {
            return Err(HamiltonianBridgeError::SignEvidenceCountMismatch {
                expected: self.loops.len(),
                actual: self.sign_evidence.len(),
            });
        }
        self.loops
            .iter()
            .zip(self.sign_evidence.iter())
            .enumerate()
            .map(|(idx, (loop_desc, evidence))| evidence.loop_sign(idx, loop_desc))
            .collect()
    }

    pub fn derive_orientation_signs(&self) -> Result<Vec<i8>, HamiltonianBridgeError> {
        let loop_signs = self.derive_loop_signs()?;
        let skeleton = LoopSkeleton {
            loops: self.loops.clone(),
        };
        let total_orientations = skeleton.checked_orientation_count()?;
        let mut orientation_signs = Vec::with_capacity(total_orientations as usize);
        for orientation in 0..total_orientations {
            let mut sign = 1_i8;
            for (idx, loop_sign) in loop_signs.iter().enumerate() {
                if ((orientation >> idx) & 1) == 1 {
                    sign *= *loop_sign;
                }
            }
            orientation_signs.push(sign);
        }
        Ok(orientation_signs)
    }

    pub fn verify(&self) -> Result<LoopOrientationSignExtractionSummary, HamiltonianBridgeError> {
        let loop_signs = self.derive_loop_signs()?;
        let orientation_signs = self.derive_orientation_signs()?;
        let extraction_packet = LoopExtractionPacket {
            family_id: self.family_id.clone(),
            bipartite_lattice: self.bipartite_lattice,
            loops: self.loops.clone(),
            orientation_abs_weights: self.orientation_abs_weights.clone(),
            orientation_signs: orientation_signs.clone(),
        };
        Ok(LoopOrientationSignExtractionSummary {
            loop_signs,
            orientation_signs,
            extraction_summary: extraction_packet.verify()?,
        })
    }
}

impl LoopGraphWithDerivedOrientationSignsPacket {
    pub fn verify(
        &self,
    ) -> Result<LoopGraphWithDerivedOrientationSignsSummary, HamiltonianBridgeError> {
        let derived_loops = LoopGraphExtractionPacket {
            family_id: self.family_id.clone(),
            bipartite_lattice: self.bipartite_lattice,
            edges: self.edges.clone(),
            orientation_abs_weights: Vec::new(),
            orientation_signs: Vec::new(),
        }
        .derive_loops()?;
        let sign_packet = LoopOrientationSignExtractionPacket {
            family_id: self.family_id.clone(),
            bipartite_lattice: self.bipartite_lattice,
            loops: derived_loops.clone(),
            orientation_abs_weights: self.orientation_abs_weights.clone(),
            sign_evidence: self.sign_evidence.clone(),
        };
        Ok(LoopGraphWithDerivedOrientationSignsSummary {
            derived_loops,
            sign_summary: sign_packet.verify()?,
        })
    }
}

impl LoopGraphWithAutoOrientationSignsPacket {
    pub fn verify(
        &self,
    ) -> Result<LoopGraphWithAutoOrientationSignsSummary, HamiltonianBridgeError> {
        let derived_loops = LoopGraphExtractionPacket {
            family_id: self.family_id.clone(),
            bipartite_lattice: self.bipartite_lattice,
            edges: self.edges.clone(),
            orientation_abs_weights: Vec::new(),
            orientation_signs: Vec::new(),
        }
        .derive_loops()?;
        let derived_sign_evidence = derived_loops
            .iter()
            .map(LoopOrientationSignEvidence::canonical_for_loop)
            .collect::<Result<Vec<_>, _>>()?;
        let sign_packet = LoopOrientationSignExtractionPacket {
            family_id: self.family_id.clone(),
            bipartite_lattice: self.bipartite_lattice,
            loops: derived_loops.clone(),
            orientation_abs_weights: self.orientation_abs_weights.clone(),
            sign_evidence: derived_sign_evidence.clone(),
        };
        Ok(LoopGraphWithAutoOrientationSignsSummary {
            derived_loops,
            derived_sign_evidence,
            sign_summary: sign_packet.verify()?,
        })
    }
}

impl LckSymbolicLocalMatrixRow {
    fn hu_onsite_element(
        &self,
        row: usize,
        source_up: usize,
        target_up: usize,
        source_down: usize,
        target_down: usize,
    ) -> Result<i64, HamiltonianBridgeError> {
        let site = self
            .onsite_site
            .ok_or(HamiltonianBridgeError::MissingHuOnsiteSite { row })?;
        if site > 1 {
            return Err(HamiltonianBridgeError::InvalidHuOnsiteSite { row, site });
        }
        if source_up != target_up || source_down != target_down {
            return Ok(0);
        }
        let up_occupied = (source_up >> site) & 1;
        let down_occupied = (source_down >> site) & 1;
        Ok(i64::from(up_occupied == down_occupied))
    }

    fn signed_matrix_element(&self, row: usize) -> Result<i64, HamiltonianBridgeError> {
        let source_up = validate_two_site_spin_state(row, "source_up_state", self.source_up_state)?;
        let target_up = validate_two_site_spin_state(row, "target_up_state", self.target_up_state)?;
        let source_down =
            validate_two_site_spin_state(row, "source_down_state", self.source_down_state)?;
        let target_down =
            validate_two_site_spin_state(row, "target_down_state", self.target_down_state)?;

        let signed = match self.operator {
            LocalOperatorKind::TemporalPropagation => {
                i64::from(source_up == target_up && source_down == target_down)
            }
            LocalOperatorKind::HjBond => {
                -lck_single_spin_h_entry(target_up, source_up)
                    * lck_single_spin_h_entry(target_down, source_down)
            }
            LocalOperatorKind::HuOnsite => {
                self.hu_onsite_element(row, source_up, target_up, source_down, target_down)?
            }
        };

        if signed == 0 {
            return Err(HamiltonianBridgeError::ZeroSymbolicLocalMatrixElement {
                row,
                operator: self.operator,
            });
        }
        Ok(signed)
    }
}

impl LckSymbolicLocalMatrixPacket {
    fn derive_operator_packet(
        &self,
    ) -> Result<(OperatorToSuccessorGraphPacket, Vec<i64>), HamiltonianBridgeError> {
        if self.family_id != LCK_HAMILTONIAN_FAMILY_ID {
            return Err(HamiltonianBridgeError::UnsupportedHamiltonianFamily {
                family_id: self.family_id.clone(),
            });
        }

        let mut signed_local_matrix_elements = Vec::with_capacity(self.rows.len());
        let mut matrix_elements = Vec::with_capacity(self.rows.len());
        for (row, symbolic_row) in self.rows.iter().enumerate() {
            let signed = symbolic_row.signed_matrix_element(row)?;
            signed_local_matrix_elements.push(signed);
            matrix_elements.push(LocalHamiltonianMatrixElement {
                source: symbolic_row.source,
                target: symbolic_row.target,
                operator: symbolic_row.operator,
                temporal_wrap: symbolic_row.temporal_wrap,
                abs_matrix_element: signed.abs(),
            });
        }

        Ok((
            OperatorToSuccessorGraphPacket {
                family_id: self.family_id.clone(),
                bipartite_lattice: self.bipartite_lattice,
                vertex_count: self.vertex_count,
                matrix_elements,
                orientation_matrix_signs: self.orientation_matrix_signs.clone(),
            },
            signed_local_matrix_elements,
        ))
    }

    pub fn verify(&self) -> Result<LckSymbolicLocalMatrixSummary, HamiltonianBridgeError> {
        let (derived_operator_packet, signed_local_matrix_elements) =
            self.derive_operator_packet()?;
        let operator_summary = derived_operator_packet.verify()?;
        Ok(LckSymbolicLocalMatrixSummary {
            single_spin_h_matrix: lck_single_spin_h_matrix(),
            signed_local_matrix_elements,
            derived_operator_packet,
            operator_summary,
        })
    }
}

impl LckSymbolicLocalMatrixDerivedSignPacket {
    fn derive_operator_packet(
        &self,
    ) -> Result<(OperatorToSuccessorGraphWithDerivedSignsPacket, Vec<i64>), HamiltonianBridgeError>
    {
        if self.family_id != LCK_HAMILTONIAN_FAMILY_ID {
            return Err(HamiltonianBridgeError::UnsupportedHamiltonianFamily {
                family_id: self.family_id.clone(),
            });
        }

        let mut signed_local_matrix_elements = Vec::with_capacity(self.rows.len());
        let mut matrix_elements = Vec::with_capacity(self.rows.len());
        for (row, symbolic_row) in self.rows.iter().enumerate() {
            let signed = symbolic_row.signed_matrix_element(row)?;
            signed_local_matrix_elements.push(signed);
            matrix_elements.push(LocalHamiltonianMatrixElement {
                source: symbolic_row.source,
                target: symbolic_row.target,
                operator: symbolic_row.operator,
                temporal_wrap: symbolic_row.temporal_wrap,
                abs_matrix_element: signed.abs(),
            });
        }

        Ok((
            OperatorToSuccessorGraphWithDerivedSignsPacket {
                family_id: self.family_id.clone(),
                bipartite_lattice: self.bipartite_lattice,
                vertex_count: self.vertex_count,
                matrix_elements,
                sign_evidence: self.sign_evidence.clone(),
            },
            signed_local_matrix_elements,
        ))
    }

    pub fn verify(
        &self,
    ) -> Result<LckSymbolicLocalMatrixDerivedSignSummary, HamiltonianBridgeError> {
        let (derived_operator_packet, signed_local_matrix_elements) =
            self.derive_operator_packet()?;
        let operator_summary = derived_operator_packet.verify()?;
        Ok(LckSymbolicLocalMatrixDerivedSignSummary {
            single_spin_h_matrix: lck_single_spin_h_matrix(),
            signed_local_matrix_elements,
            derived_operator_packet,
            operator_summary,
        })
    }
}

impl LckSymbolicLocalMatrixAutoSignPacket {
    fn derive_operator_packet(
        &self,
    ) -> Result<(OperatorToSuccessorGraphWithAutoSignsPacket, Vec<i64>), HamiltonianBridgeError>
    {
        if self.family_id != LCK_HAMILTONIAN_FAMILY_ID {
            return Err(HamiltonianBridgeError::UnsupportedHamiltonianFamily {
                family_id: self.family_id.clone(),
            });
        }

        let mut signed_local_matrix_elements = Vec::with_capacity(self.rows.len());
        let mut matrix_elements = Vec::with_capacity(self.rows.len());
        for (row, symbolic_row) in self.rows.iter().enumerate() {
            let signed = symbolic_row.signed_matrix_element(row)?;
            signed_local_matrix_elements.push(signed);
            matrix_elements.push(LocalHamiltonianMatrixElement {
                source: symbolic_row.source,
                target: symbolic_row.target,
                operator: symbolic_row.operator,
                temporal_wrap: symbolic_row.temporal_wrap,
                abs_matrix_element: signed.abs(),
            });
        }

        Ok((
            OperatorToSuccessorGraphWithAutoSignsPacket {
                family_id: self.family_id.clone(),
                bipartite_lattice: self.bipartite_lattice,
                vertex_count: self.vertex_count,
                matrix_elements,
            },
            signed_local_matrix_elements,
        ))
    }

    pub fn verify(&self) -> Result<LckSymbolicLocalMatrixAutoSignSummary, HamiltonianBridgeError> {
        let (derived_operator_packet, signed_local_matrix_elements) =
            self.derive_operator_packet()?;
        let operator_summary = derived_operator_packet.verify()?;
        Ok(LckSymbolicLocalMatrixAutoSignSummary {
            single_spin_h_matrix: lck_single_spin_h_matrix(),
            signed_local_matrix_elements,
            derived_operator_packet,
            operator_summary,
        })
    }
}

impl LckPhysicalGraphTransportPacket {
    fn verify_successor_states(
        &self,
        row_by_source: &[Option<usize>],
    ) -> Result<(), HamiltonianBridgeError> {
        for (row_idx, row) in self.rows.iter().enumerate() {
            let successor_row_idx = row_by_source[row.target].ok_or(
                HamiltonianBridgeError::OperatorSourceMultiplicity {
                    source_vertex: row.target,
                    multiplicity: 0,
                },
            )?;
            let successor = &self.rows[successor_row_idx];
            if row.target_up_state != successor.source_up_state {
                return Err(HamiltonianBridgeError::PhysicalTransportStateMismatch {
                    row: row_idx,
                    target_vertex: row.target,
                    spin: "up",
                    row_target_state: row.target_up_state,
                    successor_source_state: successor.source_up_state,
                });
            }
            if row.target_down_state != successor.source_down_state {
                return Err(HamiltonianBridgeError::PhysicalTransportStateMismatch {
                    row: row_idx,
                    target_vertex: row.target,
                    spin: "down",
                    row_target_state: row.target_down_state,
                    successor_source_state: successor.source_down_state,
                });
            }
        }
        Ok(())
    }

    fn verify_transport_continuity(&self) -> Result<(), HamiltonianBridgeError> {
        if self.family_id != LCK_HAMILTONIAN_FAMILY_ID {
            return Err(HamiltonianBridgeError::UnsupportedHamiltonianFamily {
                family_id: self.family_id.clone(),
            });
        }

        let mut source_multiplicity = vec![0_usize; self.vertex_count];
        let mut row_by_source = vec![None; self.vertex_count];
        for (row_idx, row) in self.rows.iter().enumerate() {
            if row.source >= self.vertex_count {
                return Err(HamiltonianBridgeError::OperatorSourceOutOfBounds {
                    row: row_idx,
                    source_vertex: row.source,
                    vertex_count: self.vertex_count,
                });
            }
            if row.target >= self.vertex_count {
                return Err(HamiltonianBridgeError::LoopGraphTargetOutOfBounds {
                    edge: row_idx,
                    target: row.target,
                    vertex_count: self.vertex_count,
                });
            }
            source_multiplicity[row.source] += 1;
            if row_by_source[row.source].is_none() {
                row_by_source[row.source] = Some(row_idx);
            }
        }

        for (source_vertex, multiplicity) in source_multiplicity.into_iter().enumerate() {
            if multiplicity != 1 {
                return Err(HamiltonianBridgeError::OperatorSourceMultiplicity {
                    source_vertex,
                    multiplicity,
                });
            }
        }

        self.verify_successor_states(&row_by_source)
    }

    pub fn verify(&self) -> Result<LckPhysicalGraphTransportSummary, HamiltonianBridgeError> {
        let auto_packet = LckSymbolicLocalMatrixAutoSignPacket {
            family_id: self.family_id.clone(),
            bipartite_lattice: self.bipartite_lattice,
            vertex_count: self.vertex_count,
            rows: self.rows.clone(),
        };
        let symbolic_auto_sign_summary = auto_packet.verify()?;
        self.verify_transport_continuity()?;
        Ok(LckPhysicalGraphTransportSummary {
            transport_continuity_verified: true,
            symbolic_auto_sign_summary,
        })
    }
}

impl LckGlobalSiteTransportRow {
    fn validate_occupancy_vector(
        row: usize,
        role: &'static str,
        site_count: usize,
        occupancies: &[u8],
    ) -> Result<(), HamiltonianBridgeError> {
        if occupancies.len() != site_count {
            return Err(HamiltonianBridgeError::GlobalOccupancyLengthMismatch {
                row,
                role,
                expected: site_count,
                actual: occupancies.len(),
            });
        }
        for (site, value) in occupancies.iter().copied().enumerate() {
            if value > 1 {
                return Err(HamiltonianBridgeError::GlobalOccupancyNonBinary {
                    row,
                    role,
                    site,
                    value,
                });
            }
        }
        Ok(())
    }

    fn validate_global_shape(
        &self,
        row: usize,
        site_count: usize,
    ) -> Result<(), HamiltonianBridgeError> {
        if self.left_site >= site_count {
            return Err(HamiltonianBridgeError::GlobalSiteOutOfBounds {
                row,
                site: self.left_site,
                site_count,
            });
        }
        if self.right_site >= site_count {
            return Err(HamiltonianBridgeError::GlobalSiteOutOfBounds {
                row,
                site: self.right_site,
                site_count,
            });
        }
        if self.left_site == self.right_site {
            return Err(HamiltonianBridgeError::GlobalLocalSitesNotDistinct {
                row,
                left_site: self.left_site,
                right_site: self.right_site,
            });
        }
        Self::validate_occupancy_vector(
            row,
            "source_up_occupancy",
            site_count,
            &self.source_up_occupancy,
        )?;
        Self::validate_occupancy_vector(
            row,
            "target_up_occupancy",
            site_count,
            &self.target_up_occupancy,
        )?;
        Self::validate_occupancy_vector(
            row,
            "source_down_occupancy",
            site_count,
            &self.source_down_occupancy,
        )?;
        Self::validate_occupancy_vector(
            row,
            "target_down_occupancy",
            site_count,
            &self.target_down_occupancy,
        )?;
        Ok(())
    }

    fn local_state(&self, occupancies: &[u8]) -> u8 {
        occupancies[self.left_site] + 2 * occupancies[self.right_site]
    }

    fn derive_local_row(
        &self,
        row: usize,
        site_count: usize,
    ) -> Result<LckSymbolicLocalMatrixRow, HamiltonianBridgeError> {
        self.validate_global_shape(row, site_count)?;
        let onsite_site = match self.operator {
            LocalOperatorKind::HuOnsite => {
                let hu_site = self
                    .hu_site
                    .ok_or(HamiltonianBridgeError::GlobalHuSiteMissing { row })?;
                if hu_site == self.left_site {
                    Some(0)
                } else if hu_site == self.right_site {
                    Some(1)
                } else {
                    return Err(HamiltonianBridgeError::GlobalHuSiteNotInLocalPair {
                        row,
                        hu_site,
                        left_site: self.left_site,
                        right_site: self.right_site,
                    });
                }
            }
            LocalOperatorKind::HjBond | LocalOperatorKind::TemporalPropagation => {
                if self.hu_site.is_some() {
                    return Err(HamiltonianBridgeError::GlobalUnexpectedHuSite { row });
                }
                None
            }
        };

        Ok(LckSymbolicLocalMatrixRow {
            source: self.source,
            target: self.target,
            operator: self.operator,
            temporal_wrap: self.temporal_wrap,
            source_up_state: self.local_state(&self.source_up_occupancy),
            target_up_state: self.local_state(&self.target_up_occupancy),
            source_down_state: self.local_state(&self.source_down_occupancy),
            target_down_state: self.local_state(&self.target_down_occupancy),
            onsite_site,
        })
    }
}

impl LckGlobalSiteTransportPacket {
    fn derive_local_rows(&self) -> Result<Vec<LckSymbolicLocalMatrixRow>, HamiltonianBridgeError> {
        self.rows
            .iter()
            .enumerate()
            .map(|(row_idx, row)| row.derive_local_row(row_idx, self.site_count))
            .collect()
    }

    fn verify_global_successor_occupancies(
        &self,
        row_by_source: &[Option<usize>],
    ) -> Result<(), HamiltonianBridgeError> {
        for (row_idx, row) in self.rows.iter().enumerate() {
            let successor_row_idx = row_by_source[row.target].ok_or(
                HamiltonianBridgeError::OperatorSourceMultiplicity {
                    source_vertex: row.target,
                    multiplicity: 0,
                },
            )?;
            let successor = &self.rows[successor_row_idx];
            for site in 0..self.site_count {
                if row.target_up_occupancy[site] != successor.source_up_occupancy[site] {
                    return Err(HamiltonianBridgeError::GlobalTransportStateMismatch {
                        row: row_idx,
                        target_vertex: row.target,
                        spin: "up",
                        site,
                        row_target_occupancy: row.target_up_occupancy[site],
                        successor_source_occupancy: successor.source_up_occupancy[site],
                    });
                }
                if row.target_down_occupancy[site] != successor.source_down_occupancy[site] {
                    return Err(HamiltonianBridgeError::GlobalTransportStateMismatch {
                        row: row_idx,
                        target_vertex: row.target,
                        spin: "down",
                        site,
                        row_target_occupancy: row.target_down_occupancy[site],
                        successor_source_occupancy: successor.source_down_occupancy[site],
                    });
                }
            }
        }
        Ok(())
    }

    fn verify_global_transport_continuity(&self) -> Result<(), HamiltonianBridgeError> {
        if self.family_id != LCK_HAMILTONIAN_FAMILY_ID {
            return Err(HamiltonianBridgeError::UnsupportedHamiltonianFamily {
                family_id: self.family_id.clone(),
            });
        }

        let mut source_multiplicity = vec![0_usize; self.vertex_count];
        let mut row_by_source = vec![None; self.vertex_count];
        for (row_idx, row) in self.rows.iter().enumerate() {
            if row.source >= self.vertex_count {
                return Err(HamiltonianBridgeError::OperatorSourceOutOfBounds {
                    row: row_idx,
                    source_vertex: row.source,
                    vertex_count: self.vertex_count,
                });
            }
            if row.target >= self.vertex_count {
                return Err(HamiltonianBridgeError::LoopGraphTargetOutOfBounds {
                    edge: row_idx,
                    target: row.target,
                    vertex_count: self.vertex_count,
                });
            }
            row.validate_global_shape(row_idx, self.site_count)?;
            source_multiplicity[row.source] += 1;
            if row_by_source[row.source].is_none() {
                row_by_source[row.source] = Some(row_idx);
            }
        }

        for (source_vertex, multiplicity) in source_multiplicity.into_iter().enumerate() {
            if multiplicity != 1 {
                return Err(HamiltonianBridgeError::OperatorSourceMultiplicity {
                    source_vertex,
                    multiplicity,
                });
            }
        }

        self.verify_global_successor_occupancies(&row_by_source)
    }

    pub fn verify(&self) -> Result<LckGlobalSiteTransportSummary, HamiltonianBridgeError> {
        let derived_local_rows = self.derive_local_rows()?;
        let auto_packet = LckSymbolicLocalMatrixAutoSignPacket {
            family_id: self.family_id.clone(),
            bipartite_lattice: self.bipartite_lattice,
            vertex_count: self.vertex_count,
            rows: derived_local_rows.clone(),
        };
        let symbolic_auto_sign_summary = auto_packet.verify()?;
        self.verify_global_transport_continuity()?;
        Ok(LckGlobalSiteTransportSummary {
            global_transport_continuity_verified: true,
            derived_local_rows,
            symbolic_auto_sign_summary,
        })
    }
}

impl GlobalSiteShuttleFamily {
    pub fn new(
        path_length: usize,
        hu_insertions_per_hop: usize,
    ) -> Result<Self, HamiltonianBridgeError> {
        if path_length == 0 {
            return Err(HamiltonianBridgeError::InvalidShuttlePathLength { path_length });
        }
        Ok(Self {
            path_length,
            hu_insertions_per_hop,
        })
    }

    pub fn site_count(&self) -> usize {
        self.path_length + 1
    }

    pub fn row_count(&self) -> usize {
        2 * self.path_length * (1 + self.hu_insertions_per_hop)
    }

    pub fn expected_loop(&self) -> LoopDescriptor {
        LoopDescriptor {
            temporal_winding: 0,
            bond_count: 2 * self.path_length as u32,
        }
    }

    fn occupancy(&self, occupied_site: usize) -> Vec<u8> {
        let mut occupancy = vec![0; self.site_count()];
        occupancy[occupied_site] = 1;
        occupancy
    }

    fn local_pair_for_hu(&self, site: usize) -> (usize, usize) {
        if site < self.path_length {
            (site, site + 1)
        } else {
            (site - 1, site)
        }
    }

    fn push_hj_row(
        &self,
        rows: &mut Vec<LckGlobalSiteTransportRow>,
        row_count: usize,
        from_site: usize,
        to_site: usize,
    ) {
        let source = rows.len();
        let target = (source + 1) % row_count;
        let left_site = from_site.min(to_site);
        let right_site = from_site.max(to_site);
        let source_occupancy = self.occupancy(from_site);
        let target_occupancy = self.occupancy(to_site);
        rows.push(LckGlobalSiteTransportRow {
            source,
            target,
            operator: LocalOperatorKind::HjBond,
            temporal_wrap: false,
            left_site,
            right_site,
            hu_site: None,
            source_up_occupancy: source_occupancy.clone(),
            target_up_occupancy: target_occupancy.clone(),
            source_down_occupancy: source_occupancy,
            target_down_occupancy: target_occupancy,
        });
    }

    fn push_hu_row(
        &self,
        rows: &mut Vec<LckGlobalSiteTransportRow>,
        row_count: usize,
        occupied_site: usize,
    ) {
        let source = rows.len();
        let target = (source + 1) % row_count;
        let (left_site, right_site) = self.local_pair_for_hu(occupied_site);
        let occupancy = self.occupancy(occupied_site);
        rows.push(LckGlobalSiteTransportRow {
            source,
            target,
            operator: LocalOperatorKind::HuOnsite,
            temporal_wrap: false,
            left_site,
            right_site,
            hu_site: Some(occupied_site),
            source_up_occupancy: occupancy.clone(),
            target_up_occupancy: occupancy.clone(),
            source_down_occupancy: occupancy.clone(),
            target_down_occupancy: occupancy,
        });
    }

    pub fn rows(&self) -> Vec<LckGlobalSiteTransportRow> {
        let row_count = self.row_count();
        let mut rows = Vec::with_capacity(row_count);

        for site in 0..self.path_length {
            self.push_hj_row(&mut rows, row_count, site, site + 1);
            for _ in 0..self.hu_insertions_per_hop {
                self.push_hu_row(&mut rows, row_count, site + 1);
            }
        }

        for site in (0..self.path_length).rev() {
            self.push_hj_row(&mut rows, row_count, site + 1, site);
            for _ in 0..self.hu_insertions_per_hop {
                self.push_hu_row(&mut rows, row_count, site);
            }
        }

        rows
    }

    pub fn verify(&self) -> Result<GlobalSiteShuttleFamilySummary, HamiltonianBridgeError> {
        let rows = self.rows();
        let row_count = rows.len();
        let transport_packet = LckGlobalSiteTransportPacket {
            family_id: LCK_HAMILTONIAN_FAMILY_ID.to_string(),
            bipartite_lattice: true,
            site_count: self.site_count(),
            vertex_count: row_count,
            rows,
        };
        let transport_summary = transport_packet.verify()?;
        let signed_local_matrix_elements = transport_summary
            .symbolic_auto_sign_summary
            .signed_local_matrix_elements
            .clone();
        let graph_summary = &transport_summary
            .symbolic_auto_sign_summary
            .operator_summary
            .graph_auto_sign_summary;
        Ok(GlobalSiteShuttleFamilySummary {
            path_length: self.path_length,
            hu_insertions_per_hop: self.hu_insertions_per_hop,
            site_count: self.site_count(),
            row_count,
            signed_local_matrix_elements,
            derived_loops: graph_summary.derived_loops.clone(),
            derived_sign_evidence: graph_summary.derived_sign_evidence.clone(),
            orientation_signs: graph_summary.sign_summary.orientation_signs.clone(),
            bridge_summary: graph_summary
                .sign_summary
                .extraction_summary
                .bridge_summary
                .clone(),
            transport_summary,
        })
    }
}

impl HuDecoratedMeronCycleFamily {
    pub fn new(hu_insertions_per_arc: usize) -> Self {
        Self {
            hu_insertions_per_arc,
        }
    }

    pub fn row_count(&self) -> usize {
        2 + 2 * self.hu_insertions_per_arc
    }

    pub fn rows(&self) -> Vec<LckSymbolicLocalMatrixRow> {
        let k = self.hu_insertions_per_arc;
        let row_count = self.row_count();
        let return_hj_source = 1 + k;
        let mut rows = Vec::with_capacity(row_count);

        rows.push(LckSymbolicLocalMatrixRow {
            source: 0,
            target: if k == 0 { return_hj_source } else { 1 },
            operator: LocalOperatorKind::HjBond,
            temporal_wrap: false,
            source_up_state: 1,
            target_up_state: 2,
            source_down_state: 1,
            target_down_state: 2,
            onsite_site: None,
        });

        for idx in 0..k {
            let source = 1 + idx;
            rows.push(LckSymbolicLocalMatrixRow {
                source,
                target: source + 1,
                operator: LocalOperatorKind::HuOnsite,
                temporal_wrap: false,
                source_up_state: 2,
                target_up_state: 2,
                source_down_state: 2,
                target_down_state: 2,
                onsite_site: Some(1),
            });
        }

        rows.push(LckSymbolicLocalMatrixRow {
            source: return_hj_source,
            target: if k == 0 { 0 } else { return_hj_source + 1 },
            operator: LocalOperatorKind::HjBond,
            temporal_wrap: true,
            source_up_state: 2,
            target_up_state: 1,
            source_down_state: 2,
            target_down_state: 1,
            onsite_site: None,
        });

        for idx in 0..k {
            let source = return_hj_source + 1 + idx;
            rows.push(LckSymbolicLocalMatrixRow {
                source,
                target: if idx + 1 == k { 0 } else { source + 1 },
                operator: LocalOperatorKind::HuOnsite,
                temporal_wrap: false,
                source_up_state: 1,
                target_up_state: 1,
                source_down_state: 1,
                target_down_state: 1,
                onsite_site: Some(0),
            });
        }

        rows
    }

    pub fn verify(&self) -> Result<HuDecoratedMeronCycleSummary, HamiltonianBridgeError> {
        let rows = self.rows();
        let row_count = rows.len();
        let transport_packet = LckPhysicalGraphTransportPacket {
            family_id: LCK_HAMILTONIAN_FAMILY_ID.to_string(),
            bipartite_lattice: true,
            vertex_count: row_count,
            rows,
        };
        let transport_summary = transport_packet.verify()?;
        let signed_local_matrix_elements = transport_summary
            .symbolic_auto_sign_summary
            .signed_local_matrix_elements
            .clone();
        let graph_summary = &transport_summary
            .symbolic_auto_sign_summary
            .operator_summary
            .graph_auto_sign_summary;
        Ok(HuDecoratedMeronCycleSummary {
            hu_insertions_per_arc: self.hu_insertions_per_arc,
            row_count,
            signed_local_matrix_elements,
            derived_loops: graph_summary.derived_loops.clone(),
            derived_sign_evidence: graph_summary.derived_sign_evidence.clone(),
            orientation_signs: graph_summary.sign_summary.orientation_signs.clone(),
            transport_summary,
        })
    }
}

impl HuDecoratedLoopFamily {
    pub fn new(
        loop_count: usize,
        meron_mask: u64,
        hu_insertions_per_arc: usize,
    ) -> Result<Self, HamiltonianBridgeError> {
        if loop_count >= u64::BITS as usize {
            return Err(HamiltonianBridgeError::TooManyLoops { loop_count });
        }
        if meron_mask >= (1_u64 << loop_count) {
            return Err(HamiltonianBridgeError::MeronMaskOutOfRange {
                loop_count,
                meron_mask,
            });
        }
        Ok(Self {
            loop_count,
            meron_mask,
            hu_insertions_per_arc,
        })
    }

    pub fn rows_per_loop(&self) -> usize {
        2 + 2 * self.hu_insertions_per_arc
    }

    pub fn row_count(&self) -> usize {
        self.loop_count * self.rows_per_loop()
    }

    pub fn expected_loops(&self) -> Vec<LoopDescriptor> {
        (0..self.loop_count)
            .map(|loop_idx| LoopDescriptor {
                temporal_winding: if ((self.meron_mask >> loop_idx) & 1) == 1 {
                    1
                } else {
                    0
                },
                bond_count: 2,
            })
            .collect()
    }

    pub fn rows(&self) -> Vec<LckSymbolicLocalMatrixRow> {
        let k = self.hu_insertions_per_arc;
        let stride = self.rows_per_loop();
        let mut rows = Vec::with_capacity(self.row_count());

        for loop_idx in 0..self.loop_count {
            let base = loop_idx * stride;
            let return_hj_source = base + 1 + k;
            let is_meron = ((self.meron_mask >> loop_idx) & 1) == 1;

            rows.push(LckSymbolicLocalMatrixRow {
                source: base,
                target: if k == 0 { return_hj_source } else { base + 1 },
                operator: LocalOperatorKind::HjBond,
                temporal_wrap: false,
                source_up_state: 1,
                target_up_state: 2,
                source_down_state: 1,
                target_down_state: 2,
                onsite_site: None,
            });

            for idx in 0..k {
                let source = base + 1 + idx;
                rows.push(LckSymbolicLocalMatrixRow {
                    source,
                    target: source + 1,
                    operator: LocalOperatorKind::HuOnsite,
                    temporal_wrap: false,
                    source_up_state: 2,
                    target_up_state: 2,
                    source_down_state: 2,
                    target_down_state: 2,
                    onsite_site: Some(1),
                });
            }

            rows.push(LckSymbolicLocalMatrixRow {
                source: return_hj_source,
                target: if k == 0 { base } else { return_hj_source + 1 },
                operator: LocalOperatorKind::HjBond,
                temporal_wrap: is_meron,
                source_up_state: 2,
                target_up_state: 1,
                source_down_state: 2,
                target_down_state: 1,
                onsite_site: None,
            });

            for idx in 0..k {
                let source = return_hj_source + 1 + idx;
                rows.push(LckSymbolicLocalMatrixRow {
                    source,
                    target: if idx + 1 == k { base } else { source + 1 },
                    operator: LocalOperatorKind::HuOnsite,
                    temporal_wrap: false,
                    source_up_state: 1,
                    target_up_state: 1,
                    source_down_state: 1,
                    target_down_state: 1,
                    onsite_site: Some(0),
                });
            }
        }

        rows
    }

    pub fn verify(&self) -> Result<HuDecoratedLoopFamilySummary, HamiltonianBridgeError> {
        let rows = self.rows();
        let row_count = rows.len();
        let transport_packet = LckPhysicalGraphTransportPacket {
            family_id: LCK_HAMILTONIAN_FAMILY_ID.to_string(),
            bipartite_lattice: true,
            vertex_count: row_count,
            rows,
        };
        let transport_summary = transport_packet.verify()?;
        let signed_local_matrix_elements = transport_summary
            .symbolic_auto_sign_summary
            .signed_local_matrix_elements
            .clone();
        let graph_summary = &transport_summary
            .symbolic_auto_sign_summary
            .operator_summary
            .graph_auto_sign_summary;
        Ok(HuDecoratedLoopFamilySummary {
            loop_count: self.loop_count,
            meron_mask: self.meron_mask,
            hu_insertions_per_arc: self.hu_insertions_per_arc,
            row_count,
            signed_local_matrix_elements,
            derived_loops: graph_summary.derived_loops.clone(),
            derived_sign_evidence: graph_summary.derived_sign_evidence.clone(),
            orientation_signs: graph_summary.sign_summary.orientation_signs.clone(),
            bridge_summary: graph_summary
                .sign_summary
                .extraction_summary
                .bridge_summary
                .clone(),
            transport_summary,
        })
    }
}

impl OperatorToSuccessorGraphPacket {
    fn derive_edges_and_weight(&self) -> Result<(Vec<LoopGraphEdge>, i64), HamiltonianBridgeError> {
        let mut source_multiplicity = vec![0_usize; self.vertex_count];
        let mut edges: Vec<Option<LoopGraphEdge>> = vec![None; self.vertex_count];
        let mut local_abs_weight_product = 1_i64;

        for (row, matrix_element) in self.matrix_elements.iter().enumerate() {
            if matrix_element.source >= self.vertex_count {
                return Err(HamiltonianBridgeError::OperatorSourceOutOfBounds {
                    row,
                    source_vertex: matrix_element.source,
                    vertex_count: self.vertex_count,
                });
            }
            if matrix_element.target >= self.vertex_count {
                return Err(HamiltonianBridgeError::LoopGraphTargetOutOfBounds {
                    edge: row,
                    target: matrix_element.target,
                    vertex_count: self.vertex_count,
                });
            }
            if matrix_element.abs_matrix_element <= 0 {
                return Err(HamiltonianBridgeError::NonPositiveLocalMatrixElement {
                    row,
                    weight: matrix_element.abs_matrix_element,
                });
            }
            local_abs_weight_product = local_abs_weight_product
                .checked_mul(matrix_element.abs_matrix_element)
                .ok_or(HamiltonianBridgeError::LocalWeightProductOverflow { row })?;

            source_multiplicity[matrix_element.source] += 1;
            edges[matrix_element.source] = Some(LoopGraphEdge {
                target: matrix_element.target,
                temporal_wrap: matrix_element.temporal_wrap,
                spatial_bond: matrix_element.operator.spatial_bond(),
            });
        }

        for (source, multiplicity) in source_multiplicity.into_iter().enumerate() {
            if multiplicity != 1 {
                return Err(HamiltonianBridgeError::OperatorSourceMultiplicity {
                    source_vertex: source,
                    multiplicity,
                });
            }
        }

        let resolved_edges: Result<Vec<LoopGraphEdge>, HamiltonianBridgeError> = edges
            .into_iter()
            .enumerate()
            .map(|(idx, edge)| {
                edge.ok_or(HamiltonianBridgeError::OperatorSourceMultiplicity {
                    source_vertex: idx,
                    multiplicity: 0,
                })
            })
            .collect();

        Ok((resolved_edges?, local_abs_weight_product))
    }

    pub fn verify(&self) -> Result<OperatorToSuccessorGraphSummary, HamiltonianBridgeError> {
        let (edges, local_abs_weight_product) = self.derive_edges_and_weight()?;
        let loop_count = LoopGraphExtractionPacket {
            family_id: self.family_id.clone(),
            bipartite_lattice: self.bipartite_lattice,
            edges: edges.clone(),
            orientation_abs_weights: Vec::new(),
            orientation_signs: Vec::new(),
        }
        .derive_loops()?
        .len();
        if loop_count >= u64::BITS as usize {
            return Err(HamiltonianBridgeError::TooManyLoops { loop_count });
        }
        let total_orientations = 1_u64 << loop_count;
        if self.orientation_matrix_signs.len() as u64 != total_orientations {
            return Err(HamiltonianBridgeError::OrientationEntryCountMismatch {
                expected: total_orientations,
                actual: self.orientation_matrix_signs.len(),
            });
        }

        let graph_packet = LoopGraphExtractionPacket {
            family_id: self.family_id.clone(),
            bipartite_lattice: self.bipartite_lattice,
            edges,
            orientation_abs_weights: vec![local_abs_weight_product; total_orientations as usize],
            orientation_signs: self.orientation_matrix_signs.clone(),
        };
        Ok(OperatorToSuccessorGraphSummary {
            local_matrix_element_count: self.matrix_elements.len(),
            local_abs_weight_product,
            graph_summary: graph_packet.verify()?,
        })
    }
}

impl OperatorToSuccessorGraphWithDerivedSignsPacket {
    pub fn verify(
        &self,
    ) -> Result<OperatorToSuccessorGraphWithDerivedSignsSummary, HamiltonianBridgeError> {
        let operator_packet = OperatorToSuccessorGraphPacket {
            family_id: self.family_id.clone(),
            bipartite_lattice: self.bipartite_lattice,
            vertex_count: self.vertex_count,
            matrix_elements: self.matrix_elements.clone(),
            orientation_matrix_signs: Vec::new(),
        };
        let (edges, local_abs_weight_product) = operator_packet.derive_edges_and_weight()?;
        let derived_loops = LoopGraphExtractionPacket {
            family_id: self.family_id.clone(),
            bipartite_lattice: self.bipartite_lattice,
            edges: edges.clone(),
            orientation_abs_weights: Vec::new(),
            orientation_signs: Vec::new(),
        }
        .derive_loops()?;
        if derived_loops.len() >= u64::BITS as usize {
            return Err(HamiltonianBridgeError::TooManyLoops {
                loop_count: derived_loops.len(),
            });
        }
        let total_orientations = 1_u64 << derived_loops.len();
        let graph_sign_packet = LoopGraphWithDerivedOrientationSignsPacket {
            family_id: self.family_id.clone(),
            bipartite_lattice: self.bipartite_lattice,
            edges,
            orientation_abs_weights: vec![local_abs_weight_product; total_orientations as usize],
            sign_evidence: self.sign_evidence.clone(),
        };
        Ok(OperatorToSuccessorGraphWithDerivedSignsSummary {
            local_matrix_element_count: self.matrix_elements.len(),
            local_abs_weight_product,
            graph_sign_summary: graph_sign_packet.verify()?,
        })
    }
}

impl OperatorToSuccessorGraphWithAutoSignsPacket {
    pub fn verify(
        &self,
    ) -> Result<OperatorToSuccessorGraphWithAutoSignsSummary, HamiltonianBridgeError> {
        let operator_packet = OperatorToSuccessorGraphPacket {
            family_id: self.family_id.clone(),
            bipartite_lattice: self.bipartite_lattice,
            vertex_count: self.vertex_count,
            matrix_elements: self.matrix_elements.clone(),
            orientation_matrix_signs: Vec::new(),
        };
        let (edges, local_abs_weight_product) = operator_packet.derive_edges_and_weight()?;
        let derived_loops = LoopGraphExtractionPacket {
            family_id: self.family_id.clone(),
            bipartite_lattice: self.bipartite_lattice,
            edges: edges.clone(),
            orientation_abs_weights: Vec::new(),
            orientation_signs: Vec::new(),
        }
        .derive_loops()?;
        if derived_loops.len() >= u64::BITS as usize {
            return Err(HamiltonianBridgeError::TooManyLoops {
                loop_count: derived_loops.len(),
            });
        }
        let total_orientations = 1_u64 << derived_loops.len();
        let graph_auto_sign_packet = LoopGraphWithAutoOrientationSignsPacket {
            family_id: self.family_id.clone(),
            bipartite_lattice: self.bipartite_lattice,
            edges,
            orientation_abs_weights: vec![local_abs_weight_product; total_orientations as usize],
        };
        Ok(OperatorToSuccessorGraphWithAutoSignsSummary {
            local_matrix_element_count: self.matrix_elements.len(),
            local_abs_weight_product,
            graph_auto_sign_summary: graph_auto_sign_packet.verify()?,
        })
    }
}

impl LoopGraphExtractionPacket {
    pub fn derive_loops(&self) -> Result<Vec<LoopDescriptor>, HamiltonianBridgeError> {
        let vertex_count = self.edges.len();
        let mut indegree = vec![0_usize; vertex_count];
        for (idx, edge) in self.edges.iter().enumerate() {
            if edge.target >= vertex_count {
                return Err(HamiltonianBridgeError::LoopGraphTargetOutOfBounds {
                    edge: idx,
                    target: edge.target,
                    vertex_count,
                });
            }
            indegree[edge.target] += 1;
        }
        for (vertex, degree) in indegree.into_iter().enumerate() {
            if degree != 1 {
                return Err(HamiltonianBridgeError::LoopGraphIndegreeNotOne {
                    vertex,
                    indegree: degree,
                });
            }
        }

        let mut visited = vec![false; vertex_count];
        let mut loops = Vec::new();
        for start in 0..vertex_count {
            if visited[start] {
                continue;
            }
            let mut current = start;
            let mut temporal_winding = 0_u32;
            let mut bond_count = 0_u32;
            loop {
                if visited[current] {
                    break;
                }
                visited[current] = true;
                let edge = &self.edges[current];
                if edge.temporal_wrap {
                    temporal_winding += 1;
                }
                if edge.spatial_bond {
                    bond_count += 1;
                }
                current = edge.target;
            }
            loops.push(LoopDescriptor {
                temporal_winding,
                bond_count,
            });
        }
        Ok(loops)
    }

    pub fn verify(&self) -> Result<LoopGraphExtractionSummary, HamiltonianBridgeError> {
        let derived_loops = self.derive_loops()?;
        let extraction_packet = LoopExtractionPacket {
            family_id: self.family_id.clone(),
            bipartite_lattice: self.bipartite_lattice,
            loops: derived_loops.clone(),
            orientation_abs_weights: self.orientation_abs_weights.clone(),
            orientation_signs: self.orientation_signs.clone(),
        };
        Ok(LoopGraphExtractionSummary {
            derived_loops,
            extraction_summary: extraction_packet.verify()?,
        })
    }
}

impl LoopExtractionPacket {
    fn verify_orientation_weights_and_signs(
        &self,
        skeleton: &LoopSkeleton,
        total_orientations: u64,
        common_abs_weight: i64,
    ) -> Result<(), HamiltonianBridgeError> {
        for orientation in 0..total_orientations {
            let idx = orientation as usize;
            let weight = self.orientation_abs_weights[idx];
            if weight <= 0 {
                return Err(HamiltonianBridgeError::NonPositiveOrientationWeight {
                    orientation,
                    weight,
                });
            }
            if weight != common_abs_weight {
                return Err(HamiltonianBridgeError::OrientationWeightNotIndependent {
                    orientation,
                    expected: common_abs_weight,
                    actual: weight,
                });
            }

            let expected = skeleton.orientation_sign(orientation)?;
            let actual = self.orientation_signs[idx];
            if actual != expected {
                return Err(HamiltonianBridgeError::OrientationSignMismatch {
                    orientation,
                    expected,
                    actual,
                });
            }
        }
        Ok(())
    }

    fn validate_packet_header_and_counts(
        &self,
        total_orientations: u64,
    ) -> Result<i64, HamiltonianBridgeError> {
        if self.family_id != LCK_HAMILTONIAN_FAMILY_ID {
            return Err(HamiltonianBridgeError::UnsupportedHamiltonianFamily {
                family_id: self.family_id.clone(),
            });
        }
        if !self.bipartite_lattice {
            return Err(HamiltonianBridgeError::NonBipartiteLattice);
        }
        if self.orientation_abs_weights.len() as u64 != total_orientations {
            return Err(HamiltonianBridgeError::OrientationEntryCountMismatch {
                expected: total_orientations,
                actual: self.orientation_abs_weights.len(),
            });
        }
        if self.orientation_signs.len() as u64 != total_orientations {
            return Err(HamiltonianBridgeError::OrientationEntryCountMismatch {
                expected: total_orientations,
                actual: self.orientation_signs.len(),
            });
        }
        let common_abs_weight = *self.orientation_abs_weights.first().ok_or(
            HamiltonianBridgeError::OrientationEntryCountMismatch {
                expected: total_orientations,
                actual: 0,
            },
        )?;
        if common_abs_weight <= 0 {
            return Err(HamiltonianBridgeError::NonPositiveOrientationWeight {
                orientation: 0,
                weight: common_abs_weight,
            });
        }
        Ok(common_abs_weight)
    }

    pub fn verify(&self) -> Result<LoopExtractionSummary, HamiltonianBridgeError> {
        let skeleton = LoopSkeleton {
            loops: self.loops.clone(),
        };
        let total_orientations = skeleton.checked_orientation_count()?;
        let common_abs_weight = self.validate_packet_header_and_counts(total_orientations)?;

        self.verify_orientation_weights_and_signs(
            &skeleton,
            total_orientations,
            common_abs_weight,
        )?;

        let bridge_summary = skeleton.verify_independent_loop_bridge()?;
        Ok(LoopExtractionSummary {
            family_id: self.family_id.clone(),
            loop_count: self.loops.len(),
            meron_count: skeleton.meron_indices()?.len(),
            total_orientations,
            common_abs_weight,
            sign_factorization_verified: true,
            orientation_independent_weight_verified: true,
            licenses_independent_loop_theorem: true,
            bridge_summary,
        })
    }
}

impl LoopSkeleton {
    fn checked_orientation_count(&self) -> Result<u64, HamiltonianBridgeError> {
        if self.loops.len() >= u64::BITS as usize {
            return Err(HamiltonianBridgeError::TooManyLoops {
                loop_count: self.loops.len(),
            });
        }
        Ok(1_u64 << self.loops.len())
    }

    pub fn sign_factors(&self) -> Result<Vec<i8>, HamiltonianBridgeError> {
        self.loops.iter().map(LoopDescriptor::sign_factor).collect()
    }

    pub fn meron_indices(&self) -> Result<Vec<usize>, HamiltonianBridgeError> {
        self.loops
            .iter()
            .enumerate()
            .filter_map(|(idx, loop_desc)| match loop_desc.is_meron() {
                Ok(true) => Some(Ok(idx)),
                Ok(false) => None,
                Err(err) => Some(Err(err)),
            })
            .collect()
    }

    pub fn orientation_sign(&self, orientation: u64) -> Result<i8, HamiltonianBridgeError> {
        let signs = self.sign_factors()?;
        let mut sign = 1_i8;
        for (idx, factor) in signs.iter().enumerate() {
            if ((orientation >> idx) & 1) == 1 {
                sign *= *factor;
            }
        }
        Ok(sign)
    }

    pub fn signed_orientation_sum(&self) -> Result<i64, HamiltonianBridgeError> {
        let count = self.checked_orientation_count()?;
        let mut total = 0_i64;
        for orientation in 0..count {
            total += i64::from(self.orientation_sign(orientation)?);
        }
        Ok(total)
    }

    pub fn candidate_flip(&self, orientation: u64) -> Result<Option<u64>, HamiltonianBridgeError> {
        let Some(first_meron) = self.meron_indices()?.first().copied() else {
            return Ok(None);
        };
        Ok(Some(orientation ^ (1_u64 << first_meron)))
    }

    fn evaluate_orientation_flips(
        &self,
        count: u64,
        meron_count: usize,
    ) -> Result<(bool, bool, bool), HamiltonianBridgeError> {
        let mut fixed_point_free = true;
        let mut sign_reversing = true;
        let mut candidate_flip_total = meron_count > 0;

        for orientation in 0..count {
            match self.candidate_flip(orientation)? {
                Some(flipped) => {
                    fixed_point_free &= flipped != orientation;
                    sign_reversing &=
                        self.orientation_sign(flipped)? == -self.orientation_sign(orientation)?;
                }
                None => {
                    candidate_flip_total = false;
                }
            }
        }
        Ok((fixed_point_free, sign_reversing, candidate_flip_total))
    }

    pub fn verify_independent_loop_bridge(
        &self,
    ) -> Result<BridgeCheckSummary, HamiltonianBridgeError> {
        let count = self.checked_orientation_count()?;
        let meron_count = self.meron_indices()?.len();
        let signed_sum = self.signed_orientation_sum()?;
        let (fixed_point_free, sign_reversing, candidate_flip_total) =
            self.evaluate_orientation_flips(count, meron_count)?;

        Ok(BridgeCheckSummary {
            loop_count: self.loops.len(),
            meron_count,
            total_orientations: count,
            signed_orientation_sum: signed_sum,
            candidate_flip_total_on_multi_meron_sector: candidate_flip_total,
            fixed_point_free,
            absolute_weight_preserving: true,
            sign_reversing,
            nonzero_meron_sector_cancels: meron_count == 0 || signed_sum == 0,
            zero_meron_sector_positive: meron_count != 0 || signed_sum > 0,
        })
    }

    pub fn verify_observable_invariant(
        &self,
        observable: &BTreeMap<u64, i64>,
    ) -> Result<(), HamiltonianBridgeError> {
        if self.meron_indices()?.is_empty() {
            return Ok(());
        }
        let count = self.checked_orientation_count()?;
        for orientation in 0..count {
            let flipped = self
                .candidate_flip(orientation)?
                .ok_or(HamiltonianBridgeError::MissingCandidateFlip { orientation })?;
            let left = observable
                .get(&orientation)
                .ok_or(HamiltonianBridgeError::MissingObservable { orientation })?;
            let right =
                observable
                    .get(&flipped)
                    .ok_or(HamiltonianBridgeError::MissingObservable {
                        orientation: flipped,
                    })?;
            if left != right {
                return Err(HamiltonianBridgeError::ObservableNotInvariant {
                    left: orientation,
                    right: flipped,
                });
            }
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct FamilyCarrierState {
    pub meron_mask: u64,
    pub orientation: u64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct IndependentLoopFamily {
    pub loop_count: usize,
}

impl IndependentLoopFamily {
    pub fn new(loop_count: usize) -> Result<Self, HamiltonianBridgeError> {
        if 2 * loop_count >= u64::BITS as usize {
            return Err(HamiltonianBridgeError::TooManyLoops { loop_count });
        }
        Ok(Self { loop_count })
    }

    pub fn carrier_size(&self) -> u64 {
        1_u64 << (2 * self.loop_count)
    }

    pub fn sector_mask_bound(&self) -> u64 {
        1_u64 << self.loop_count
    }

    pub fn is_zero_sector(&self, state: &FamilyCarrierState) -> bool {
        state.meron_mask == 0
    }

    pub fn sign(&self, state: &FamilyCarrierState) -> i8 {
        let active_meron_flips = (state.meron_mask & state.orientation).count_ones();
        if active_meron_flips.is_multiple_of(2) {
            1
        } else {
            -1
        }
    }

    pub fn weight(&self, _state: &FamilyCarrierState) -> i64 {
        1
    }

    fn least_meron_bit(&self, meron_mask: u64) -> Option<u32> {
        if meron_mask == 0 {
            None
        } else {
            Some(meron_mask.trailing_zeros())
        }
    }

    pub fn involution(&self, state: &FamilyCarrierState) -> Option<FamilyCarrierState> {
        let bit = self.least_meron_bit(state.meron_mask)?;
        Some(FamilyCarrierState {
            meron_mask: state.meron_mask,
            orientation: state.orientation ^ (1_u64 << bit),
        })
    }

    /// Primitive non-meron moves flip orientation bits whose loop is not a
    /// meron in this skeleton. These moves preserve weight and sign and
    /// generate ZeroRel.
    pub fn non_meron_moves(&self, state: &FamilyCarrierState) -> Vec<FamilyCarrierState> {
        (0..self.loop_count)
            .filter(|idx| ((state.meron_mask >> idx) & 1) == 0)
            .map(|idx| FamilyCarrierState {
                meron_mask: state.meron_mask,
                orientation: state.orientation ^ (1_u64 << idx),
            })
            .collect()
    }

    pub fn zero_rel_component_key(&self, state: &FamilyCarrierState) -> (u64, u64) {
        (state.meron_mask, state.orientation & state.meron_mask)
    }

    pub fn iter_states(&self) -> impl Iterator<Item = FamilyCarrierState> + '_ {
        let bound = self.sector_mask_bound();
        (0..bound).flat_map(move |meron_mask| {
            (0..bound).map(move |orientation| FamilyCarrierState {
                meron_mask,
                orientation,
            })
        })
    }

    pub fn verify(&self) -> FamilyCarrierSummary {
        let mut z_all = 0_i64;
        let mut z_zero = 0_i64;
        let mut z_multi = 0_i64;
        let mut candidate_flip_total = true;
        let mut fixed_point_free = true;
        let mut involutive = true;
        let mut absolute_weight_preserving = true;
        let mut sign_reversing = true;
        let mut complete_orbit_coverage = true;
        let mut multi_seen = BTreeSet::new();
        let mut zero_rel_components = BTreeSet::new();
        let mut directed_non_meron_moves = 0_u64;
        let mut non_meron_moves_preserve_weight_and_sign = true;

        for state in self.iter_states() {
            let contribution = self.weight(&state) * i64::from(self.sign(&state));
            z_all += contribution;
            zero_rel_components.insert(self.zero_rel_component_key(&state));
            for moved in self.non_meron_moves(&state) {
                directed_non_meron_moves += 1;
                non_meron_moves_preserve_weight_and_sign &= self.weight(&moved)
                    == self.weight(&state)
                    && self.sign(&moved) == self.sign(&state);
            }
            if self.is_zero_sector(&state) {
                z_zero += contribution;
            } else {
                z_multi += contribution;
                let Some(flipped) = self.involution(&state) else {
                    candidate_flip_total = false;
                    complete_orbit_coverage = false;
                    continue;
                };
                fixed_point_free &= flipped != state;
                involutive &= self.involution(&flipped).as_ref() == Some(&state);
                absolute_weight_preserving &= self.weight(&flipped) == self.weight(&state);
                sign_reversing &= self.sign(&flipped) == -self.sign(&state);
                complete_orbit_coverage &= !self.is_zero_sector(&flipped);
                multi_seen.insert(state);
                multi_seen.insert(flipped);
            }
        }

        let bound = self.sector_mask_bound();
        FamilyCarrierSummary {
            loop_count: self.loop_count,
            carrier_size: self.carrier_size(),
            zero_sector_size: bound,
            multi_sector_size: (bound - 1) * bound,
            z_all,
            z_zero,
            z_multi,
            candidate_flip_total_on_multi_meron_sector: candidate_flip_total,
            fixed_point_free,
            involutive,
            absolute_weight_preserving,
            sign_reversing,
            complete_orbit_coverage: complete_orbit_coverage
                && multi_seen.len() as u64 == (bound - 1) * bound,
            non_meron_move_count: directed_non_meron_moves / 2,
            non_meron_moves_preserve_weight_and_sign,
            zero_rel_component_count: zero_rel_components.len() as u64,
            observable_survivor_classes: ((bound - 1) * bound / 2) + bound,
        }
    }

    pub fn verify_observable_invariant(
        &self,
        observable: &BTreeMap<FamilyCarrierState, i64>,
    ) -> Result<(), HamiltonianBridgeError> {
        for state in self
            .iter_states()
            .filter(|state| !self.is_zero_sector(state))
        {
            let flipped =
                self.involution(&state)
                    .ok_or(HamiltonianBridgeError::MissingInvolutionFlip {
                        meron_mask: state.meron_mask,
                        orientation: state.orientation,
                    })?;
            let left = observable
                .get(&state)
                .ok_or(HamiltonianBridgeError::MissingObservable {
                    orientation: state.orientation,
                })?;
            let right =
                observable
                    .get(&flipped)
                    .ok_or(HamiltonianBridgeError::MissingObservable {
                        orientation: flipped.orientation,
                    })?;
            if left != right {
                return Err(HamiltonianBridgeError::ObservableNotInvariant {
                    left: state.orientation,
                    right: flipped.orientation,
                });
            }
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_certifiers/src/meron_hamiltonian_bridge.rs
// Claim: urn:core:crates_rs:core-certifiers:meron-hamiltonian-bridge:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn non_meron_loop() -> LoopDescriptor {
        LoopDescriptor {
            temporal_winding: 0,
            bond_count: 2,
        }
    }

    fn meron_loop() -> LoopDescriptor {
        LoopDescriptor {
            temporal_winding: 1,
            bond_count: 2,
        }
    }

    fn extraction_packet(loops: Vec<LoopDescriptor>, weight: i64) -> LoopExtractionPacket {
        let skeleton = LoopSkeleton {
            loops: loops.clone(),
        };
        let total = skeleton.checked_orientation_count().unwrap();
        let signs = (0..total)
            .map(|orientation| skeleton.orientation_sign(orientation).unwrap())
            .collect();
        LoopExtractionPacket {
            family_id: LCK_HAMILTONIAN_FAMILY_ID.to_string(),
            bipartite_lattice: true,
            loops,
            orientation_abs_weights: vec![weight; total as usize],
            orientation_signs: signs,
        }
    }

    fn graph_packet(
        edges: Vec<LoopGraphEdge>,
        orientation_abs_weights: Vec<i64>,
        orientation_signs: Vec<i8>,
    ) -> LoopGraphExtractionPacket {
        LoopGraphExtractionPacket {
            family_id: LCK_HAMILTONIAN_FAMILY_ID.to_string(),
            bipartite_lattice: true,
            edges,
            orientation_abs_weights,
            orientation_signs,
        }
    }

    fn valid_operator_matrix_elements() -> Vec<LocalHamiltonianMatrixElement> {
        vec![
            LocalHamiltonianMatrixElement {
                source: 0,
                target: 1,
                operator: LocalOperatorKind::HjBond,
                temporal_wrap: false,
                abs_matrix_element: 2,
            },
            LocalHamiltonianMatrixElement {
                source: 1,
                target: 0,
                operator: LocalOperatorKind::HjBond,
                temporal_wrap: true,
                abs_matrix_element: 3,
            },
            LocalHamiltonianMatrixElement {
                source: 2,
                target: 3,
                operator: LocalOperatorKind::HjBond,
                temporal_wrap: false,
                abs_matrix_element: 5,
            },
            LocalHamiltonianMatrixElement {
                source: 3,
                target: 2,
                operator: LocalOperatorKind::HjBond,
                temporal_wrap: false,
                abs_matrix_element: 7,
            },
        ]
    }

    fn operator_packet(
        vertex_count: usize,
        matrix_elements: Vec<LocalHamiltonianMatrixElement>,
        orientation_matrix_signs: Vec<i8>,
    ) -> OperatorToSuccessorGraphPacket {
        OperatorToSuccessorGraphPacket {
            family_id: LCK_HAMILTONIAN_FAMILY_ID.to_string(),
            bipartite_lattice: true,
            vertex_count,
            matrix_elements,
            orientation_matrix_signs,
        }
    }

    fn valid_symbolic_hj_rows() -> Vec<LckSymbolicLocalMatrixRow> {
        vec![
            LckSymbolicLocalMatrixRow {
                source: 0,
                target: 1,
                operator: LocalOperatorKind::HjBond,
                temporal_wrap: false,
                source_up_state: 1,
                target_up_state: 2,
                source_down_state: 1,
                target_down_state: 2,
                onsite_site: None,
            },
            LckSymbolicLocalMatrixRow {
                source: 1,
                target: 0,
                operator: LocalOperatorKind::HjBond,
                temporal_wrap: true,
                source_up_state: 2,
                target_up_state: 1,
                source_down_state: 2,
                target_down_state: 1,
                onsite_site: None,
            },
            LckSymbolicLocalMatrixRow {
                source: 2,
                target: 3,
                operator: LocalOperatorKind::HjBond,
                temporal_wrap: false,
                source_up_state: 1,
                target_up_state: 2,
                source_down_state: 2,
                target_down_state: 1,
                onsite_site: None,
            },
            LckSymbolicLocalMatrixRow {
                source: 3,
                target: 2,
                operator: LocalOperatorKind::HjBond,
                temporal_wrap: false,
                source_up_state: 2,
                target_up_state: 1,
                source_down_state: 1,
                target_down_state: 2,
                onsite_site: None,
            },
        ]
    }

    fn valid_mixed_hj_hu_rows() -> Vec<LckSymbolicLocalMatrixRow> {
        vec![
            LckSymbolicLocalMatrixRow {
                source: 0,
                target: 1,
                operator: LocalOperatorKind::HjBond,
                temporal_wrap: false,
                source_up_state: 1,
                target_up_state: 2,
                source_down_state: 1,
                target_down_state: 2,
                onsite_site: None,
            },
            LckSymbolicLocalMatrixRow {
                source: 1,
                target: 2,
                operator: LocalOperatorKind::HuOnsite,
                temporal_wrap: false,
                source_up_state: 2,
                target_up_state: 2,
                source_down_state: 2,
                target_down_state: 2,
                onsite_site: Some(1),
            },
            LckSymbolicLocalMatrixRow {
                source: 2,
                target: 3,
                operator: LocalOperatorKind::HjBond,
                temporal_wrap: true,
                source_up_state: 2,
                target_up_state: 1,
                source_down_state: 2,
                target_down_state: 1,
                onsite_site: None,
            },
            LckSymbolicLocalMatrixRow {
                source: 3,
                target: 0,
                operator: LocalOperatorKind::HuOnsite,
                temporal_wrap: false,
                source_up_state: 1,
                target_up_state: 1,
                source_down_state: 1,
                target_down_state: 1,
                onsite_site: Some(0),
            },
        ]
    }

    fn symbolic_local_packet(
        rows: Vec<LckSymbolicLocalMatrixRow>,
        orientation_matrix_signs: Vec<i8>,
    ) -> LckSymbolicLocalMatrixPacket {
        LckSymbolicLocalMatrixPacket {
            family_id: LCK_HAMILTONIAN_FAMILY_ID.to_string(),
            bipartite_lattice: true,
            vertex_count: 4,
            rows,
            orientation_matrix_signs,
        }
    }

    fn sign_evidence_for(loops: &[LoopDescriptor]) -> Vec<LoopOrientationSignEvidence> {
        loops
            .iter()
            .map(|loop_desc| LoopOrientationSignEvidence::canonical_for_loop(loop_desc).unwrap())
            .collect()
    }

    fn graph_with_derived_signs_packet(
        edges: Vec<LoopGraphEdge>,
        orientation_abs_weights: Vec<i64>,
        sign_evidence: Vec<LoopOrientationSignEvidence>,
    ) -> LoopGraphWithDerivedOrientationSignsPacket {
        LoopGraphWithDerivedOrientationSignsPacket {
            family_id: LCK_HAMILTONIAN_FAMILY_ID.to_string(),
            bipartite_lattice: true,
            edges,
            orientation_abs_weights,
            sign_evidence,
        }
    }

    fn graph_with_auto_signs_packet(
        edges: Vec<LoopGraphEdge>,
        orientation_abs_weights: Vec<i64>,
    ) -> LoopGraphWithAutoOrientationSignsPacket {
        LoopGraphWithAutoOrientationSignsPacket {
            family_id: LCK_HAMILTONIAN_FAMILY_ID.to_string(),
            bipartite_lattice: true,
            edges,
            orientation_abs_weights,
        }
    }

    fn operator_with_derived_signs_packet(
        vertex_count: usize,
        matrix_elements: Vec<LocalHamiltonianMatrixElement>,
        sign_evidence: Vec<LoopOrientationSignEvidence>,
    ) -> OperatorToSuccessorGraphWithDerivedSignsPacket {
        OperatorToSuccessorGraphWithDerivedSignsPacket {
            family_id: LCK_HAMILTONIAN_FAMILY_ID.to_string(),
            bipartite_lattice: true,
            vertex_count,
            matrix_elements,
            sign_evidence,
        }
    }

    fn operator_with_auto_signs_packet(
        vertex_count: usize,
        matrix_elements: Vec<LocalHamiltonianMatrixElement>,
    ) -> OperatorToSuccessorGraphWithAutoSignsPacket {
        OperatorToSuccessorGraphWithAutoSignsPacket {
            family_id: LCK_HAMILTONIAN_FAMILY_ID.to_string(),
            bipartite_lattice: true,
            vertex_count,
            matrix_elements,
        }
    }

    fn symbolic_local_derived_sign_packet(
        rows: Vec<LckSymbolicLocalMatrixRow>,
        sign_evidence: Vec<LoopOrientationSignEvidence>,
    ) -> LckSymbolicLocalMatrixDerivedSignPacket {
        LckSymbolicLocalMatrixDerivedSignPacket {
            family_id: LCK_HAMILTONIAN_FAMILY_ID.to_string(),
            bipartite_lattice: true,
            vertex_count: 4,
            rows,
            sign_evidence,
        }
    }

    fn symbolic_local_auto_sign_packet(
        rows: Vec<LckSymbolicLocalMatrixRow>,
    ) -> LckSymbolicLocalMatrixAutoSignPacket {
        LckSymbolicLocalMatrixAutoSignPacket {
            family_id: LCK_HAMILTONIAN_FAMILY_ID.to_string(),
            bipartite_lattice: true,
            vertex_count: 4,
            rows,
        }
    }

    fn physical_graph_transport_packet(
        vertex_count: usize,
        rows: Vec<LckSymbolicLocalMatrixRow>,
    ) -> LckPhysicalGraphTransportPacket {
        LckPhysicalGraphTransportPacket {
            family_id: LCK_HAMILTONIAN_FAMILY_ID.to_string(),
            bipartite_lattice: true,
            vertex_count,
            rows,
        }
    }

    fn global_site_transport_packet(
        site_count: usize,
        rows: Vec<LckGlobalSiteTransportRow>,
    ) -> LckGlobalSiteTransportPacket {
        LckGlobalSiteTransportPacket {
            family_id: LCK_HAMILTONIAN_FAMILY_ID.to_string(),
            bipartite_lattice: true,
            site_count,
            vertex_count: rows.len(),
            rows,
        }
    }

    fn shared_vertex_hj_hu_global_rows() -> Vec<LckGlobalSiteTransportRow> {
        let state_a = vec![1, 0, 0];
        let state_b = vec![0, 1, 0];
        let state_c = vec![0, 0, 1];
        vec![
            LckGlobalSiteTransportRow {
                source: 0,
                target: 1,
                operator: LocalOperatorKind::HjBond,
                temporal_wrap: false,
                left_site: 0,
                right_site: 1,
                hu_site: None,
                source_up_occupancy: state_a.clone(),
                target_up_occupancy: state_b.clone(),
                source_down_occupancy: state_a.clone(),
                target_down_occupancy: state_b.clone(),
            },
            LckGlobalSiteTransportRow {
                source: 1,
                target: 2,
                operator: LocalOperatorKind::HuOnsite,
                temporal_wrap: false,
                left_site: 1,
                right_site: 2,
                hu_site: Some(1),
                source_up_occupancy: state_b.clone(),
                target_up_occupancy: state_b.clone(),
                source_down_occupancy: state_b.clone(),
                target_down_occupancy: state_b.clone(),
            },
            LckGlobalSiteTransportRow {
                source: 2,
                target: 3,
                operator: LocalOperatorKind::HjBond,
                temporal_wrap: false,
                left_site: 1,
                right_site: 2,
                hu_site: None,
                source_up_occupancy: state_b.clone(),
                target_up_occupancy: state_c.clone(),
                source_down_occupancy: state_b.clone(),
                target_down_occupancy: state_c.clone(),
            },
            LckGlobalSiteTransportRow {
                source: 3,
                target: 4,
                operator: LocalOperatorKind::HjBond,
                temporal_wrap: false,
                left_site: 1,
                right_site: 2,
                hu_site: None,
                source_up_occupancy: state_c.clone(),
                target_up_occupancy: state_b.clone(),
                source_down_occupancy: state_c.clone(),
                target_down_occupancy: state_b.clone(),
            },
            LckGlobalSiteTransportRow {
                source: 4,
                target: 5,
                operator: LocalOperatorKind::HuOnsite,
                temporal_wrap: false,
                left_site: 1,
                right_site: 2,
                hu_site: Some(1),
                source_up_occupancy: state_b.clone(),
                target_up_occupancy: state_b.clone(),
                source_down_occupancy: state_b.clone(),
                target_down_occupancy: state_b.clone(),
            },
            LckGlobalSiteTransportRow {
                source: 5,
                target: 0,
                operator: LocalOperatorKind::HjBond,
                temporal_wrap: false,
                left_site: 0,
                right_site: 1,
                hu_site: None,
                source_up_occupancy: state_b.clone(),
                target_up_occupancy: state_a.clone(),
                source_down_occupancy: state_b,
                target_down_occupancy: state_a,
            },
        ]
    }

    #[test]
    fn lck_loop_sign_formula_classifies_merons() {
        assert_eq!(non_meron_loop().sign_factor(), Ok(1));
        assert_eq!(meron_loop().sign_factor(), Ok(-1));
    }

    #[test]
    fn lck_single_spin_bond_matrix_matches_declared_formula() {
        assert_eq!(
            lck_single_spin_h_matrix(),
            [[0, 0, 0, 0], [0, -1, -1, 0], [0, -1, -1, 0], [0, 0, 0, 0]]
        );
    }

    #[test]
    fn independent_loop_bridge_cancels_every_nonzero_meron_skeleton() {
        for loop_count in 1..=6 {
            for mask in 1_u32..(1_u32 << loop_count) {
                let loops = (0..loop_count)
                    .map(|idx| {
                        if ((mask >> idx) & 1) == 1 {
                            meron_loop()
                        } else {
                            non_meron_loop()
                        }
                    })
                    .collect();
                let summary = LoopSkeleton { loops }
                    .verify_independent_loop_bridge()
                    .expect("valid skeleton");
                assert!(summary.candidate_flip_total_on_multi_meron_sector);
                assert!(summary.fixed_point_free);
                assert!(summary.absolute_weight_preserving);
                assert!(summary.sign_reversing);
                assert!(summary.nonzero_meron_sector_cancels);
                assert_eq!(summary.signed_orientation_sum, 0);
            }
        }
    }

    #[test]
    fn zero_meron_skeleton_is_positive() {
        let skeleton = LoopSkeleton {
            loops: vec![non_meron_loop(), non_meron_loop(), non_meron_loop()],
        };
        let summary = skeleton.verify_independent_loop_bridge().unwrap();
        assert_eq!(summary.meron_count, 0);
        assert_eq!(summary.signed_orientation_sum, 8);
        assert!(summary.zero_meron_sector_positive);
    }

    #[test]
    fn malformed_loop_with_odd_bond_count_is_refused() {
        let skeleton = LoopSkeleton {
            loops: vec![LoopDescriptor {
                temporal_winding: 0,
                bond_count: 1,
            }],
        };
        assert!(matches!(
            skeleton.verify_independent_loop_bridge(),
            Err(HamiltonianBridgeError::OddBondCount { bond_count: 1 })
        ));
    }

    #[test]
    fn observable_must_be_invariant_on_candidate_flip_orbits() {
        let skeleton = LoopSkeleton {
            loops: vec![meron_loop()],
        };
        let invariant = BTreeMap::from([(0, 7), (1, 7)]);
        assert!(skeleton.verify_observable_invariant(&invariant).is_ok());

        let non_invariant = BTreeMap::from([(0, 7), (1, 9)]);
        assert!(matches!(
            skeleton.verify_observable_invariant(&non_invariant),
            Err(HamiltonianBridgeError::ObservableNotInvariant { left: 0, right: 1 })
        ));
    }

    #[test]
    fn valid_lck_loop_extraction_packet_licenses_independent_loop_theorem() {
        let packet = extraction_packet(vec![meron_loop(), non_meron_loop()], 3);
        let summary = packet.verify().unwrap();
        assert_eq!(summary.family_id, LCK_HAMILTONIAN_FAMILY_ID);
        assert_eq!(summary.loop_count, 2);
        assert_eq!(summary.meron_count, 1);
        assert_eq!(summary.total_orientations, 4);
        assert_eq!(summary.common_abs_weight, 3);
        assert!(summary.sign_factorization_verified);
        assert!(summary.orientation_independent_weight_verified);
        assert!(summary.licenses_independent_loop_theorem);
        assert_eq!(summary.bridge_summary.signed_orientation_sum, 0);
    }

    #[test]
    fn loop_extraction_rejects_orientation_dependent_weight() {
        let mut packet = extraction_packet(vec![meron_loop()], 1);
        packet.orientation_abs_weights[1] = 2;
        assert!(matches!(
            packet.verify(),
            Err(HamiltonianBridgeError::OrientationWeightNotIndependent {
                orientation: 1,
                expected: 1,
                actual: 2,
            })
        ));
    }

    #[test]
    fn loop_extraction_rejects_sign_factorization_mismatch() {
        let mut packet = extraction_packet(vec![meron_loop()], 1);
        packet.orientation_signs[1] = 1;
        assert!(matches!(
            packet.verify(),
            Err(HamiltonianBridgeError::OrientationSignMismatch {
                orientation: 1,
                expected: -1,
                actual: 1,
            })
        ));
    }

    #[test]
    fn loop_extraction_rejects_unlicensed_hamiltonian_family() {
        let mut packet = extraction_packet(vec![meron_loop()], 1);
        packet.family_id = "OTHER_H".to_string();
        assert!(matches!(
            packet.verify(),
            Err(HamiltonianBridgeError::UnsupportedHamiltonianFamily { .. })
        ));
    }

    #[test]
    fn loop_extraction_rejects_non_bipartite_lattice_declaration() {
        let mut packet = extraction_packet(vec![meron_loop()], 1);
        packet.bipartite_lattice = false;
        assert!(matches!(
            packet.verify(),
            Err(HamiltonianBridgeError::NonBipartiteLattice)
        ));
    }

    #[test]
    fn loop_graph_extraction_derives_descriptors_and_licenses_theorem() {
        let derived = vec![meron_loop(), non_meron_loop()];
        let skeleton = LoopSkeleton {
            loops: derived.clone(),
        };
        let signs = (0..4)
            .map(|orientation| skeleton.orientation_sign(orientation).unwrap())
            .collect();
        let packet = graph_packet(
            vec![
                LoopGraphEdge {
                    target: 1,
                    temporal_wrap: false,
                    spatial_bond: true,
                },
                LoopGraphEdge {
                    target: 0,
                    temporal_wrap: true,
                    spatial_bond: true,
                },
                LoopGraphEdge {
                    target: 3,
                    temporal_wrap: false,
                    spatial_bond: true,
                },
                LoopGraphEdge {
                    target: 2,
                    temporal_wrap: false,
                    spatial_bond: true,
                },
            ],
            vec![5; 4],
            signs,
        );
        let summary = packet.verify().unwrap();
        assert_eq!(summary.derived_loops, derived);
        assert!(summary.extraction_summary.licenses_independent_loop_theorem);
        assert_eq!(
            summary
                .extraction_summary
                .bridge_summary
                .signed_orientation_sum,
            0
        );
    }

    #[test]
    fn loop_graph_extraction_rejects_target_out_of_bounds() {
        let packet = graph_packet(
            vec![LoopGraphEdge {
                target: 1,
                temporal_wrap: false,
                spatial_bond: true,
            }],
            vec![1],
            vec![1],
        );
        assert!(matches!(
            packet.verify(),
            Err(HamiltonianBridgeError::LoopGraphTargetOutOfBounds {
                edge: 0,
                target: 1,
                vertex_count: 1,
            })
        ));
    }

    #[test]
    fn loop_graph_extraction_rejects_non_permutation_successor_graph() {
        let packet = graph_packet(
            vec![
                LoopGraphEdge {
                    target: 1,
                    temporal_wrap: false,
                    spatial_bond: true,
                },
                LoopGraphEdge {
                    target: 1,
                    temporal_wrap: false,
                    spatial_bond: true,
                },
            ],
            vec![1],
            vec![1],
        );
        assert!(matches!(
            packet.verify(),
            Err(HamiltonianBridgeError::LoopGraphIndegreeNotOne {
                vertex: 0,
                indegree: 0,
            })
        ));
    }

    #[test]
    fn one_loop_orientation_sign_evidence_matches_eta_formula() {
        for temporal_winding in 0..=3 {
            for bond_count in [0, 2, 4, 6, 8] {
                let loop_desc = LoopDescriptor {
                    temporal_winding,
                    bond_count,
                };
                let evidence = LoopOrientationSignEvidence::canonical_for_loop(&loop_desc).unwrap();
                assert_eq!(evidence.loop_sign(0, &loop_desc), loop_desc.sign_factor());
            }
        }
    }

    #[test]
    fn derived_orientation_signs_license_loop_extraction() {
        let loops = vec![meron_loop(), non_meron_loop()];
        let packet = LoopOrientationSignExtractionPacket {
            family_id: LCK_HAMILTONIAN_FAMILY_ID.to_string(),
            bipartite_lattice: true,
            orientation_abs_weights: vec![11; 4],
            sign_evidence: sign_evidence_for(&loops),
            loops,
        };
        let summary = packet.verify().unwrap();
        assert_eq!(summary.loop_signs, vec![-1, 1]);
        assert_eq!(summary.orientation_signs, vec![1, -1, 1, -1]);
        assert_eq!(summary.extraction_summary.common_abs_weight, 11);
        assert!(summary.extraction_summary.licenses_independent_loop_theorem);
    }

    #[test]
    fn derived_orientation_signs_reject_missing_evidence() {
        let packet = LoopOrientationSignExtractionPacket {
            family_id: LCK_HAMILTONIAN_FAMILY_ID.to_string(),
            bipartite_lattice: true,
            loops: vec![meron_loop(), non_meron_loop()],
            orientation_abs_weights: vec![1; 4],
            sign_evidence: vec![LoopOrientationSignEvidence {
                temporal_boundary_parity: 1,
                bond_permutation_parity: 1,
                closure_permutation_parity: 1,
            }],
        };
        assert!(matches!(
            packet.verify(),
            Err(HamiltonianBridgeError::SignEvidenceCountMismatch {
                expected: 2,
                actual: 1,
            })
        ));
    }

    #[test]
    fn derived_orientation_signs_reject_temporal_parity_mismatch() {
        let loop_desc = meron_loop();
        let packet = LoopOrientationSignExtractionPacket {
            family_id: LCK_HAMILTONIAN_FAMILY_ID.to_string(),
            bipartite_lattice: true,
            loops: vec![loop_desc],
            orientation_abs_weights: vec![1; 2],
            sign_evidence: vec![LoopOrientationSignEvidence {
                temporal_boundary_parity: 0,
                bond_permutation_parity: 1,
                closure_permutation_parity: 1,
            }],
        };
        assert!(matches!(
            packet.verify(),
            Err(HamiltonianBridgeError::TemporalBoundaryParityMismatch {
                loop_index: 0,
                expected: 1,
                actual: 0,
            })
        ));
    }

    #[test]
    fn derived_orientation_signs_reject_bond_parity_mismatch() {
        let loop_desc = non_meron_loop();
        let packet = LoopOrientationSignExtractionPacket {
            family_id: LCK_HAMILTONIAN_FAMILY_ID.to_string(),
            bipartite_lattice: true,
            loops: vec![loop_desc],
            orientation_abs_weights: vec![1; 2],
            sign_evidence: vec![LoopOrientationSignEvidence {
                temporal_boundary_parity: 0,
                bond_permutation_parity: 0,
                closure_permutation_parity: 1,
            }],
        };
        assert!(matches!(
            packet.verify(),
            Err(HamiltonianBridgeError::BondPermutationParityMismatch {
                loop_index: 0,
                expected: 1,
                actual: 0,
            })
        ));
    }

    #[test]
    fn derived_orientation_signs_reject_closure_parity_mismatch() {
        let loop_desc = non_meron_loop();
        let packet = LoopOrientationSignExtractionPacket {
            family_id: LCK_HAMILTONIAN_FAMILY_ID.to_string(),
            bipartite_lattice: true,
            loops: vec![loop_desc],
            orientation_abs_weights: vec![1; 2],
            sign_evidence: vec![LoopOrientationSignEvidence {
                temporal_boundary_parity: 0,
                bond_permutation_parity: 1,
                closure_permutation_parity: 0,
            }],
        };
        assert!(matches!(
            packet.verify(),
            Err(HamiltonianBridgeError::ClosurePermutationParityMismatch {
                loop_index: 0,
                actual: 0,
            })
        ));
    }

    #[test]
    fn loop_graph_with_derived_orientation_signs_licenses_theorem() {
        let loops = vec![meron_loop(), non_meron_loop()];
        let packet = graph_with_derived_signs_packet(
            vec![
                LoopGraphEdge {
                    target: 1,
                    temporal_wrap: false,
                    spatial_bond: true,
                },
                LoopGraphEdge {
                    target: 0,
                    temporal_wrap: true,
                    spatial_bond: true,
                },
                LoopGraphEdge {
                    target: 3,
                    temporal_wrap: false,
                    spatial_bond: true,
                },
                LoopGraphEdge {
                    target: 2,
                    temporal_wrap: false,
                    spatial_bond: true,
                },
            ],
            vec![13; 4],
            sign_evidence_for(&loops),
        );
        let summary = packet.verify().unwrap();
        assert_eq!(summary.derived_loops, loops);
        assert_eq!(summary.sign_summary.orientation_signs, vec![1, -1, 1, -1]);
        assert!(
            summary
                .sign_summary
                .extraction_summary
                .licenses_independent_loop_theorem
        );
    }

    #[test]
    fn loop_graph_auto_derives_orientation_sign_evidence_and_licenses_theorem() {
        let loops = vec![meron_loop(), non_meron_loop()];
        let packet = graph_with_auto_signs_packet(
            vec![
                LoopGraphEdge {
                    target: 1,
                    temporal_wrap: false,
                    spatial_bond: true,
                },
                LoopGraphEdge {
                    target: 0,
                    temporal_wrap: true,
                    spatial_bond: true,
                },
                LoopGraphEdge {
                    target: 3,
                    temporal_wrap: false,
                    spatial_bond: true,
                },
                LoopGraphEdge {
                    target: 2,
                    temporal_wrap: false,
                    spatial_bond: true,
                },
            ],
            vec![17; 4],
        );
        let summary = packet.verify().unwrap();
        assert_eq!(summary.derived_loops, loops);
        assert_eq!(summary.derived_sign_evidence, sign_evidence_for(&loops));
        assert_eq!(summary.sign_summary.orientation_signs, vec![1, -1, 1, -1]);
        assert_eq!(
            summary.sign_summary.extraction_summary.common_abs_weight,
            17
        );
        assert!(
            summary
                .sign_summary
                .extraction_summary
                .licenses_independent_loop_theorem
        );
    }

    #[test]
    fn operator_packet_derives_successor_graph_and_licenses_theorem() {
        let skeleton = LoopSkeleton {
            loops: vec![meron_loop(), non_meron_loop()],
        };
        let signs = (0..4)
            .map(|orientation| skeleton.orientation_sign(orientation).unwrap())
            .collect();
        let packet = operator_packet(4, valid_operator_matrix_elements(), signs);

        let summary = packet.verify().unwrap();
        assert_eq!(summary.local_matrix_element_count, 4);
        assert_eq!(summary.local_abs_weight_product, 210);
        assert_eq!(
            summary.graph_summary.derived_loops,
            vec![meron_loop(), non_meron_loop()]
        );
        assert_eq!(
            summary.graph_summary.extraction_summary.common_abs_weight,
            210
        );
        assert!(
            summary
                .graph_summary
                .extraction_summary
                .licenses_independent_loop_theorem
        );
        assert_eq!(
            summary
                .graph_summary
                .extraction_summary
                .bridge_summary
                .signed_orientation_sum,
            0
        );
    }

    #[test]
    fn operator_packet_rejects_duplicate_source() {
        let mut rows = valid_operator_matrix_elements();
        rows[1].source = 0;
        let packet = operator_packet(4, rows, vec![1, -1, 1, -1]);
        assert!(matches!(
            packet.verify(),
            Err(HamiltonianBridgeError::OperatorSourceMultiplicity {
                source_vertex: 0,
                multiplicity: 2,
            })
        ));
    }

    #[test]
    fn operator_packet_rejects_missing_source() {
        let packet = operator_packet(
            2,
            vec![valid_operator_matrix_elements()[0].clone()],
            vec![1],
        );
        assert!(matches!(
            packet.verify(),
            Err(HamiltonianBridgeError::OperatorSourceMultiplicity {
                source_vertex: 1,
                multiplicity: 0,
            })
        ));
    }

    #[test]
    fn operator_packet_rejects_target_out_of_bounds() {
        let mut rows = valid_operator_matrix_elements();
        rows[0].target = 4;
        let packet = operator_packet(4, rows, vec![1, -1, 1, -1]);
        assert!(matches!(
            packet.verify(),
            Err(HamiltonianBridgeError::LoopGraphTargetOutOfBounds {
                edge: 0,
                target: 4,
                vertex_count: 4,
            })
        ));
    }

    #[test]
    fn operator_packet_rejects_nonpositive_local_weight() {
        let mut rows = valid_operator_matrix_elements();
        rows[2].abs_matrix_element = 0;
        let packet = operator_packet(4, rows, vec![1, -1, 1, -1]);
        assert!(matches!(
            packet.verify(),
            Err(HamiltonianBridgeError::NonPositiveLocalMatrixElement { row: 2, weight: 0 })
        ));
    }

    #[test]
    fn operator_packet_rejects_matrix_sign_mismatch() {
        let packet = operator_packet(4, valid_operator_matrix_elements(), vec![1, 1, 1, -1]);
        assert!(matches!(
            packet.verify(),
            Err(HamiltonianBridgeError::OrientationSignMismatch {
                orientation: 1,
                expected: -1,
                actual: 1,
            })
        ));
    }

    #[test]
    fn operator_packet_with_derived_orientation_signs_licenses_theorem() {
        let loops = vec![meron_loop(), non_meron_loop()];
        let packet = operator_with_derived_signs_packet(
            4,
            valid_operator_matrix_elements(),
            sign_evidence_for(&loops),
        );
        let summary = packet.verify().unwrap();
        assert_eq!(summary.local_matrix_element_count, 4);
        assert_eq!(summary.local_abs_weight_product, 210);
        assert_eq!(summary.graph_sign_summary.derived_loops, loops);
        assert_eq!(
            summary.graph_sign_summary.sign_summary.orientation_signs,
            vec![1, -1, 1, -1]
        );
        assert!(
            summary
                .graph_sign_summary
                .sign_summary
                .extraction_summary
                .licenses_independent_loop_theorem
        );
    }

    #[test]
    fn operator_packet_auto_derives_orientation_signs_and_licenses_theorem() {
        let loops = vec![meron_loop(), non_meron_loop()];
        let packet = operator_with_auto_signs_packet(4, valid_operator_matrix_elements());
        let summary = packet.verify().unwrap();
        assert_eq!(summary.local_matrix_element_count, 4);
        assert_eq!(summary.local_abs_weight_product, 210);
        assert_eq!(summary.graph_auto_sign_summary.derived_loops, loops);
        assert_eq!(
            summary.graph_auto_sign_summary.derived_sign_evidence,
            sign_evidence_for(&loops)
        );
        assert_eq!(
            summary
                .graph_auto_sign_summary
                .sign_summary
                .orientation_signs,
            vec![1, -1, 1, -1]
        );
        assert!(
            summary
                .graph_auto_sign_summary
                .sign_summary
                .extraction_summary
                .licenses_independent_loop_theorem
        );
    }

    #[test]
    fn symbolic_hj_rows_derive_operator_packet_and_license_theorem() {
        let skeleton = LoopSkeleton {
            loops: vec![meron_loop(), non_meron_loop()],
        };
        let signs = (0..4)
            .map(|orientation| skeleton.orientation_sign(orientation).unwrap())
            .collect();
        let packet = symbolic_local_packet(valid_symbolic_hj_rows(), signs);

        let summary = packet.verify().unwrap();
        assert_eq!(summary.signed_local_matrix_elements, vec![-1, -1, -1, -1]);
        assert_eq!(summary.operator_summary.local_matrix_element_count, 4);
        assert_eq!(summary.operator_summary.local_abs_weight_product, 1);
        assert_eq!(
            summary.operator_summary.graph_summary.derived_loops,
            vec![meron_loop(), non_meron_loop()]
        );
        assert!(
            summary
                .operator_summary
                .graph_summary
                .extraction_summary
                .licenses_independent_loop_theorem
        );
    }

    #[test]
    fn symbolic_hj_rows_reject_zero_local_matrix_element() {
        let mut rows = valid_symbolic_hj_rows();
        rows[0].source_up_state = 0;
        rows[0].target_up_state = 0;
        let packet = symbolic_local_packet(rows, vec![1, -1, 1, -1]);
        assert!(matches!(
            packet.verify(),
            Err(HamiltonianBridgeError::ZeroSymbolicLocalMatrixElement {
                row: 0,
                operator: LocalOperatorKind::HjBond,
            })
        ));
    }

    #[test]
    fn symbolic_local_rows_reject_invalid_spin_state() {
        let mut rows = valid_symbolic_hj_rows();
        rows[1].target_down_state = 4;
        let packet = symbolic_local_packet(rows, vec![1, -1, 1, -1]);
        assert!(matches!(
            packet.verify(),
            Err(HamiltonianBridgeError::InvalidTwoSiteSpinState {
                row: 1,
                state_role: "target_down_state",
                state: 4,
            })
        ));
    }

    #[test]
    fn symbolic_hj_rows_with_derived_orientation_signs_license_theorem() {
        let loops = vec![meron_loop(), non_meron_loop()];
        let packet =
            symbolic_local_derived_sign_packet(valid_symbolic_hj_rows(), sign_evidence_for(&loops));

        let summary = packet.verify().unwrap();
        assert_eq!(summary.signed_local_matrix_elements, vec![-1, -1, -1, -1]);
        assert_eq!(summary.operator_summary.local_matrix_element_count, 4);
        assert_eq!(summary.operator_summary.local_abs_weight_product, 1);
        assert_eq!(
            summary.operator_summary.graph_sign_summary.derived_loops,
            loops
        );
        assert_eq!(
            summary
                .operator_summary
                .graph_sign_summary
                .sign_summary
                .orientation_signs,
            vec![1, -1, 1, -1]
        );
        assert!(
            summary
                .operator_summary
                .graph_sign_summary
                .sign_summary
                .extraction_summary
                .licenses_independent_loop_theorem
        );
    }

    #[test]
    fn symbolic_hj_rows_auto_derive_orientation_signs_and_license_theorem() {
        let loops = vec![meron_loop(), non_meron_loop()];
        let packet = symbolic_local_auto_sign_packet(valid_symbolic_hj_rows());

        let summary = packet.verify().unwrap();
        assert_eq!(summary.signed_local_matrix_elements, vec![-1, -1, -1, -1]);
        assert_eq!(summary.operator_summary.local_matrix_element_count, 4);
        assert_eq!(summary.operator_summary.local_abs_weight_product, 1);
        assert_eq!(
            summary
                .operator_summary
                .graph_auto_sign_summary
                .derived_loops,
            loops
        );
        assert_eq!(
            summary
                .operator_summary
                .graph_auto_sign_summary
                .derived_sign_evidence,
            sign_evidence_for(&loops)
        );
        assert_eq!(
            summary
                .operator_summary
                .graph_auto_sign_summary
                .sign_summary
                .orientation_signs,
            vec![1, -1, 1, -1]
        );
        assert!(
            summary
                .operator_summary
                .graph_auto_sign_summary
                .sign_summary
                .extraction_summary
                .licenses_independent_loop_theorem
        );
    }

    #[test]
    fn operator_projection_collides_for_distinct_spin_resolved_hj_transport() {
        let both_spins_move = LckSymbolicLocalMatrixRow {
            source: 0,
            target: 1,
            operator: LocalOperatorKind::HjBond,
            temporal_wrap: false,
            source_up_state: 1,
            target_up_state: 2,
            source_down_state: 1,
            target_down_state: 2,
            onsite_site: None,
        };
        let up_moves_down_stays = LckSymbolicLocalMatrixRow {
            target_down_state: 1,
            ..both_spins_move.clone()
        };
        let both_packet = LckSymbolicLocalMatrixAutoSignPacket {
            family_id: LCK_HAMILTONIAN_FAMILY_ID.to_string(),
            bipartite_lattice: true,
            vertex_count: 2,
            rows: vec![both_spins_move.clone()],
        };
        let mixed_packet = LckSymbolicLocalMatrixAutoSignPacket {
            rows: vec![up_moves_down_stays.clone()],
            ..both_packet.clone()
        };
        let (both_projection, both_signed) = both_packet.derive_operator_packet().unwrap();
        let (mixed_projection, mixed_signed) = mixed_packet.derive_operator_packet().unwrap();

        assert_ne!(both_spins_move, up_moves_down_stays);
        assert_eq!(both_signed, vec![-1]);
        assert_eq!(mixed_signed, vec![-1]);
        assert_eq!(both_projection, mixed_projection);
    }

    #[test]
    fn physical_graph_transport_valid_symbolic_hj_rows_license_theorem() {
        let loops = vec![meron_loop(), non_meron_loop()];
        let packet = physical_graph_transport_packet(4, valid_symbolic_hj_rows());

        let summary = packet.verify().unwrap();
        assert!(summary.transport_continuity_verified);
        assert_eq!(
            summary
                .symbolic_auto_sign_summary
                .operator_summary
                .graph_auto_sign_summary
                .derived_loops,
            loops
        );
        assert_eq!(
            summary
                .symbolic_auto_sign_summary
                .operator_summary
                .graph_auto_sign_summary
                .derived_sign_evidence,
            sign_evidence_for(&loops)
        );
        assert_eq!(
            summary
                .symbolic_auto_sign_summary
                .operator_summary
                .graph_auto_sign_summary
                .sign_summary
                .orientation_signs,
            vec![1, -1, 1, -1]
        );
        assert!(
            summary
                .symbolic_auto_sign_summary
                .operator_summary
                .graph_auto_sign_summary
                .sign_summary
                .extraction_summary
                .licenses_independent_loop_theorem
        );
    }

    #[test]
    fn physical_graph_transport_valid_mixed_hj_hu_rows_license_theorem() {
        let loops = vec![meron_loop()];
        let packet = physical_graph_transport_packet(4, valid_mixed_hj_hu_rows());

        let summary = packet.verify().unwrap();
        assert!(summary.transport_continuity_verified);
        assert_eq!(
            summary
                .symbolic_auto_sign_summary
                .signed_local_matrix_elements,
            vec![-1, 1, -1, 1]
        );
        assert_eq!(
            summary
                .symbolic_auto_sign_summary
                .operator_summary
                .graph_auto_sign_summary
                .derived_loops,
            loops
        );
        assert_eq!(
            summary
                .symbolic_auto_sign_summary
                .operator_summary
                .graph_auto_sign_summary
                .derived_sign_evidence,
            sign_evidence_for(&loops)
        );
        assert_eq!(
            summary
                .symbolic_auto_sign_summary
                .operator_summary
                .graph_auto_sign_summary
                .sign_summary
                .orientation_signs,
            vec![1, -1]
        );
        assert!(
            summary
                .symbolic_auto_sign_summary
                .operator_summary
                .graph_auto_sign_summary
                .sign_summary
                .extraction_summary
                .licenses_independent_loop_theorem
        );
    }

    #[test]
    fn hu_decorated_meron_cycle_family_verifies_for_multiple_decoration_counts() {
        for hu_insertions_per_arc in 0..=8 {
            let family = HuDecoratedMeronCycleFamily::new(hu_insertions_per_arc);
            let summary = family.verify().unwrap();
            let hu_count = 2 * hu_insertions_per_arc;

            assert_eq!(summary.hu_insertions_per_arc, hu_insertions_per_arc);
            assert_eq!(summary.row_count, 2 + hu_count);
            assert_eq!(summary.derived_loops, vec![meron_loop()]);
            assert_eq!(
                summary.derived_sign_evidence,
                sign_evidence_for(&[meron_loop()])
            );
            assert_eq!(summary.orientation_signs, vec![1, -1]);
            assert_eq!(summary.signed_local_matrix_elements.len(), 2 + hu_count);
            assert_eq!(
                summary
                    .signed_local_matrix_elements
                    .iter()
                    .filter(|entry| **entry == -1)
                    .count(),
                2
            );
            assert_eq!(
                summary
                    .signed_local_matrix_elements
                    .iter()
                    .filter(|entry| **entry == 1)
                    .count(),
                hu_count
            );
            assert!(
                summary
                    .transport_summary
                    .symbolic_auto_sign_summary
                    .operator_summary
                    .graph_auto_sign_summary
                    .sign_summary
                    .extraction_summary
                    .licenses_independent_loop_theorem
            );
        }
    }

    #[test]
    fn hu_decorated_loop_family_verifies_all_masks_for_small_multi_loop_instances() {
        for loop_count in 1..=4 {
            for hu_insertions_per_arc in 0..=3 {
                for meron_mask in 0_u64..(1_u64 << loop_count) {
                    let family =
                        HuDecoratedLoopFamily::new(loop_count, meron_mask, hu_insertions_per_arc)
                            .unwrap();
                    let summary = family.verify().unwrap();
                    let expected_loops = family.expected_loops();
                    let expected_skeleton = LoopSkeleton {
                        loops: expected_loops.clone(),
                    };
                    let expected_signs = (0..(1_u64 << loop_count))
                        .map(|orientation| expected_skeleton.orientation_sign(orientation).unwrap())
                        .collect::<Vec<_>>();
                    let hu_count = 2 * hu_insertions_per_arc * loop_count;

                    assert_eq!(summary.loop_count, loop_count);
                    assert_eq!(summary.meron_mask, meron_mask);
                    assert_eq!(summary.hu_insertions_per_arc, hu_insertions_per_arc);
                    assert_eq!(
                        summary.row_count,
                        loop_count * (2 + 2 * hu_insertions_per_arc)
                    );
                    assert_eq!(summary.derived_loops, expected_loops);
                    assert_eq!(summary.orientation_signs, expected_signs);
                    assert_eq!(summary.bridge_summary.loop_count, loop_count);
                    assert_eq!(
                        summary.bridge_summary.meron_count,
                        meron_mask.count_ones() as usize
                    );
                    assert_eq!(
                        summary
                            .signed_local_matrix_elements
                            .iter()
                            .filter(|entry| **entry == -1)
                            .count(),
                        2 * loop_count
                    );
                    assert_eq!(
                        summary
                            .signed_local_matrix_elements
                            .iter()
                            .filter(|entry| **entry == 1)
                            .count(),
                        hu_count
                    );
                    if meron_mask == 0 {
                        assert_eq!(
                            summary.bridge_summary.signed_orientation_sum,
                            1_i64 << loop_count
                        );
                        assert!(summary.bridge_summary.zero_meron_sector_positive);
                    } else {
                        assert_eq!(summary.bridge_summary.signed_orientation_sum, 0);
                        assert!(summary.bridge_summary.nonzero_meron_sector_cancels);
                        assert!(summary.bridge_summary.sign_reversing);
                        assert!(summary.bridge_summary.absolute_weight_preserving);
                    }
                }
            }
        }
    }

    #[test]
    fn hu_decorated_loop_family_rejects_mask_outside_loop_count() {
        assert!(matches!(
            HuDecoratedLoopFamily::new(2, 4, 1),
            Err(HamiltonianBridgeError::MeronMaskOutOfRange {
                loop_count: 2,
                meron_mask: 4,
            })
        ));
    }

    #[test]
    fn global_site_transport_shared_vertex_hj_hu_packet_licenses_theorem() {
        let packet = global_site_transport_packet(3, shared_vertex_hj_hu_global_rows());
        let summary = packet.verify().unwrap();
        let expected_loop = LoopDescriptor {
            temporal_winding: 0,
            bond_count: 4,
        };

        assert!(summary.global_transport_continuity_verified);
        assert_eq!(
            summary
                .symbolic_auto_sign_summary
                .signed_local_matrix_elements,
            vec![-1, 1, -1, -1, 1, -1]
        );
        assert_eq!(
            summary
                .symbolic_auto_sign_summary
                .operator_summary
                .graph_auto_sign_summary
                .derived_loops,
            vec![expected_loop.clone()]
        );
        assert_eq!(expected_loop.sign_factor(), Ok(-1));
        assert_eq!(
            summary
                .symbolic_auto_sign_summary
                .operator_summary
                .graph_auto_sign_summary
                .sign_summary
                .orientation_signs,
            vec![1, -1]
        );
        assert!(
            summary
                .symbolic_auto_sign_summary
                .operator_summary
                .graph_auto_sign_summary
                .sign_summary
                .extraction_summary
                .licenses_independent_loop_theorem
        );
    }

    #[test]
    fn global_site_shuttle_family_verifies_path_lengths_and_hu_insertions() {
        for path_length in 1..=6 {
            for hu_insertions_per_hop in 0..=2 {
                let family =
                    GlobalSiteShuttleFamily::new(path_length, hu_insertions_per_hop).unwrap();
                let summary = family.verify().unwrap();
                let expected_loop = family.expected_loop();
                let expected_sign = expected_loop.sign_factor().unwrap();
                let hj_row_count = 2 * path_length;
                let hu_row_count = hj_row_count * hu_insertions_per_hop;

                assert_eq!(summary.path_length, path_length);
                assert_eq!(summary.hu_insertions_per_hop, hu_insertions_per_hop);
                assert_eq!(summary.site_count, path_length + 1);
                assert_eq!(summary.row_count, hj_row_count + hu_row_count);
                assert_eq!(summary.derived_loops, vec![expected_loop.clone()]);
                assert_eq!(
                    summary.derived_sign_evidence,
                    sign_evidence_for(std::slice::from_ref(&expected_loop))
                );
                assert_eq!(summary.orientation_signs, vec![1, expected_sign]);
                assert_eq!(
                    summary
                        .signed_local_matrix_elements
                        .iter()
                        .filter(|entry| **entry == -1)
                        .count(),
                    hj_row_count
                );
                assert_eq!(
                    summary
                        .signed_local_matrix_elements
                        .iter()
                        .filter(|entry| **entry == 1)
                        .count(),
                    hu_row_count
                );

                if expected_loop.is_meron().unwrap() {
                    assert_eq!(summary.bridge_summary.signed_orientation_sum, 0);
                    assert!(summary.bridge_summary.nonzero_meron_sector_cancels);
                    assert!(summary.bridge_summary.sign_reversing);
                    assert!(summary.bridge_summary.absolute_weight_preserving);
                } else {
                    assert_eq!(summary.bridge_summary.signed_orientation_sum, 2);
                    assert!(summary.bridge_summary.zero_meron_sector_positive);
                }
            }
        }
    }

    #[test]
    fn global_site_shuttle_family_rejects_zero_path_length() {
        assert!(matches!(
            GlobalSiteShuttleFamily::new(0, 1),
            Err(HamiltonianBridgeError::InvalidShuttlePathLength { path_length: 0 })
        ));
    }

    #[test]
    fn global_site_transport_rejects_shared_site_state_mismatch() {
        let mut rows = shared_vertex_hj_hu_global_rows();
        rows[1].source_up_occupancy[2] = 1;
        rows[1].target_up_occupancy[2] = 1;
        let packet = global_site_transport_packet(3, rows);

        assert!(matches!(
            packet.verify(),
            Err(HamiltonianBridgeError::GlobalTransportStateMismatch {
                row: 0,
                target_vertex: 1,
                spin: "up",
                site: 2,
                row_target_occupancy: 0,
                successor_source_occupancy: 1,
            })
        ));
    }

    #[test]
    fn global_site_transport_rejects_hu_site_outside_local_pair() {
        let mut rows = shared_vertex_hj_hu_global_rows();
        rows[1].hu_site = Some(0);
        let packet = global_site_transport_packet(3, rows);

        assert!(matches!(
            packet.verify(),
            Err(HamiltonianBridgeError::GlobalHuSiteNotInLocalPair {
                row: 1,
                hu_site: 0,
                left_site: 1,
                right_site: 2,
            })
        ));
    }

    #[test]
    fn physical_graph_transport_rejects_offdiagonal_hu_transport() {
        let mut rows = valid_mixed_hj_hu_rows();
        rows[1].target_up_state = 1;
        let packet = physical_graph_transport_packet(4, rows);

        assert!(matches!(
            packet.verify(),
            Err(HamiltonianBridgeError::ZeroSymbolicLocalMatrixElement {
                row: 1,
                operator: LocalOperatorKind::HuOnsite,
            })
        ));
    }

    #[test]
    fn physical_graph_transport_rejects_state_mismatch() {
        let mut rows = valid_symbolic_hj_rows();
        rows[2].target_up_state = 1;
        let packet = physical_graph_transport_packet(4, rows);

        assert!(matches!(
            packet.verify(),
            Err(HamiltonianBridgeError::PhysicalTransportStateMismatch {
                row: 2,
                target_vertex: 3,
                spin: "up",
                row_target_state: 1,
                successor_source_state: 2,
            })
        ));
    }

    #[test]
    fn physical_graph_transport_rejects_odd_spatial_bond_cycle() {
        let packet = physical_graph_transport_packet(
            1,
            vec![LckSymbolicLocalMatrixRow {
                source: 0,
                target: 0,
                operator: LocalOperatorKind::HjBond,
                temporal_wrap: false,
                source_up_state: 1,
                target_up_state: 1,
                source_down_state: 1,
                target_down_state: 1,
                onsite_site: None,
            }],
        );

        assert!(matches!(
            packet.verify(),
            Err(HamiltonianBridgeError::OddBondCount { bond_count: 1 })
        ));
    }

    #[test]
    fn symbolic_hu_onsite_support_is_diagonal_and_positive_in_doubled_units() {
        let row = LckSymbolicLocalMatrixRow {
            source: 0,
            target: 0,
            operator: LocalOperatorKind::HuOnsite,
            temporal_wrap: false,
            source_up_state: 0,
            target_up_state: 0,
            source_down_state: 0,
            target_down_state: 0,
            onsite_site: Some(0),
        };
        assert_eq!(row.signed_matrix_element(0), Ok(1));

        let mut zero_row = row.clone();
        zero_row.source_up_state = 1;
        zero_row.target_up_state = 1;
        assert!(matches!(
            zero_row.signed_matrix_element(0),
            Err(HamiltonianBridgeError::ZeroSymbolicLocalMatrixElement {
                row: 0,
                operator: LocalOperatorKind::HuOnsite,
            })
        ));
    }

    #[test]
    fn parameterized_family_verifies_n_2_3_4() {
        for loop_count in 2..=4 {
            let family = IndependentLoopFamily::new(loop_count).unwrap();
            let summary = family.verify();
            assert_eq!(summary.carrier_size, 1_u64 << (2 * loop_count));
            assert_eq!(summary.zero_sector_size, 1_u64 << loop_count);
            assert_eq!(
                summary.multi_sector_size,
                ((1_u64 << loop_count) - 1) * (1_u64 << loop_count)
            );
            assert_eq!(summary.z_multi, 0);
            assert_eq!(summary.z_all, summary.z_zero);
            assert_eq!(summary.z_zero, 1_i64 << loop_count);
            assert!(summary.candidate_flip_total_on_multi_meron_sector);
            assert!(summary.fixed_point_free);
            assert!(summary.involutive);
            assert!(summary.absolute_weight_preserving);
            assert!(summary.sign_reversing);
            assert!(summary.complete_orbit_coverage);
            assert!(summary.non_meron_moves_preserve_weight_and_sign);
            assert_eq!(
                summary.non_meron_move_count,
                (loop_count as u64) * (1_u64 << (2 * loop_count - 2))
            );
            assert_eq!(
                summary.zero_rel_component_count,
                3_u64.pow(loop_count as u32)
            );
        }
    }

    #[test]
    fn primitive_non_meron_moves_preserve_weight_and_sign_and_derive_zero_rel() {
        let family = IndependentLoopFamily::new(4).unwrap();
        for state in family.iter_states() {
            for moved in family.non_meron_moves(&state) {
                assert_eq!(family.weight(&moved), family.weight(&state));
                assert_eq!(family.sign(&moved), family.sign(&state));
                assert_eq!(
                    family.zero_rel_component_key(&moved),
                    family.zero_rel_component_key(&state)
                );
            }
        }
        assert_eq!(family.verify().zero_rel_component_count, 81);
    }

    #[test]
    fn parameterized_family_characterizes_surviving_observables_as_orbit_invariant() {
        let family = IndependentLoopFamily::new(3).unwrap();
        let invariant = family
            .iter_states()
            .map(|state| {
                let orbit_key = if family.is_zero_sector(&state) {
                    state.orientation
                } else {
                    let flipped = family.involution(&state).unwrap();
                    state.orientation.min(flipped.orientation)
                };
                (state, orbit_key as i64)
            })
            .collect();
        assert!(family.verify_observable_invariant(&invariant).is_ok());

        let mut non_invariant: BTreeMap<FamilyCarrierState, i64> =
            family.iter_states().map(|state| (state, 0)).collect();
        non_invariant.insert(
            FamilyCarrierState {
                meron_mask: 1,
                orientation: 1,
            },
            1,
        );
        assert!(matches!(
            family.verify_observable_invariant(&non_invariant),
            Err(HamiltonianBridgeError::ObservableNotInvariant { .. })
        ));
    }
}
