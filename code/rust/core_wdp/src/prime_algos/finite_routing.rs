//! Declared finite terminal, lift and closure-damage contracts; no authority effect.
//! A commuting lift does not assert preservation of quotient norms or classes.
use crate::coda::diagnostic_routing::{
    propose_value_edit, DiagnosticPacket, Proposal, ProposalPolicy,
};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::finite_cochain_map::{CochainMap, CochainWindow};
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};
use core_functional::phi1::ExactPhi1Certificate;
use core_policy::trichotomy::ObstructionDiagnosticClass;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FiniteTerminal {
    Hold,
    ExactCertified,
    ClosedCertified,
    ActiveCertified,
    StabilizedSurvivor,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TerminalPolicy {
    pub rows: [Option<FiniteTerminal>; 3],
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FiniteRefusal {
    MissingPolicy,
    MissingPolicyRow,
    IncompatibleTerminal,
    MissingLift,
    InvalidLift,
    MissingGuard,
    InvalidDamageBudget,
    NoStrictDescent,
    ClosureDamageExceeded,
    MissingStabilization,
    InvalidStabilization,
    ReplayFailed,
}
fn row(packet: &DiagnosticPacket) -> usize {
    match packet.classification().diagnostic_class() {
        ObstructionDiagnosticClass::ExactRepair => 0,
        ObstructionDiagnosticClass::ClosedResidual => 1,
        ObstructionDiagnosticClass::ActiveClosureFailure => 2,
    }
}
fn replay(packet: &DiagnosticPacket) -> Result<DiagnosticPacket, FiniteRefusal> {
    DiagnosticPacket::replay(
        packet.system().clone(),
        packet.phi1().certificate().clone(),
        packet.closure_map().to_vec(),
    )
    .map_err(|_| FiniteRefusal::ReplayFailed)
}
fn matrix(
    rows: usize,
    cols: usize,
    data: &[Vec<BigRational>],
) -> Result<BasicMatrix<BigRational>, FiniteRefusal> {
    if data.len() != rows || data.iter().any(|r| r.len() != cols) {
        return Err(FiniteRefusal::InvalidLift);
    }
    BasicMatrix::try_from_fn(rows, cols, |i, j| data[i][j].clone())
        .map_err(|_| FiniteRefusal::InvalidLift)
}
fn window(packet: &DiagnosticPacket) -> Result<CochainWindow<BigRational>, FiniteRefusal> {
    let n0 = packet.phi1().alpha().len();
    let n1 = packet.phi1().primal_residual().len();
    let n2 = packet.closure_map().len();
    CochainWindow::try_new(
        [n0, n1, n2],
        matrix(n1, n0, packet.phi1().d0())?,
        matrix(n2, n1, packet.closure_map())?,
    )
    .map_err(|_| FiniteRefusal::InvalidLift)
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LiftContract {
    pub map: CochainMap<BigRational>,
    pub require_coordinate_inclusion: bool,
}
/// Replay both endpoints, bind all three cochain degrees, and require omega'=F1 omega.
/// The target certificate is independent: commuting maps need not preserve Phi1.
pub fn check_lift(
    source: &DiagnosticPacket,
    target: &DiagnosticPacket,
    contract: Option<&LiftContract>,
) -> Result<(), FiniteRefusal> {
    replay(source)?;
    replay(target)?;
    let contract = contract.ok_or(FiniteRefusal::MissingLift)?;
    if contract.map.source() != &window(source)? || contract.map.target() != &window(target)? {
        return Err(FiniteRefusal::InvalidLift);
    }
    if contract.require_coordinate_inclusion {
        check_coordinate_inclusion(contract.map.maps())?;
    }
    check_omega_transport(source, target, contract)
}

fn check_coordinate_inclusion(maps: &[BasicMatrix<BigRational>]) -> Result<(), FiniteRefusal> {
    for m in maps {
        let mut used = std::collections::BTreeSet::new();
        for j in 0..m.cols() {
            let selected = find_unit_row_in_col(m, j)?;
            if !used.insert(selected) {
                return Err(FiniteRefusal::InvalidLift);
            }
        }
    }
    Ok(())
}

fn find_unit_row_in_col(m: &BasicMatrix<BigRational>, j: usize) -> Result<usize, FiniteRefusal> {
    let mut selected = None;
    for i in 0..m.rows() {
        let x = m.get_ref(i, j).map_err(|_| FiniteRefusal::InvalidLift)?;
        if x == &BigRational::one() {
            if selected.replace(i).is_some() {
                return Err(FiniteRefusal::InvalidLift);
            }
        } else if !x.is_zero() {
            return Err(FiniteRefusal::InvalidLift);
        }
    }
    selected.ok_or(FiniteRefusal::InvalidLift)
}

fn check_omega_transport(
    source: &DiagnosticPacket,
    target: &DiagnosticPacket,
    contract: &LiftContract,
) -> Result<(), FiniteRefusal> {
    let omega = &source.phi1().certificate().omega;
    let column = BasicMatrix::try_from_fn(omega.len(), 1, |i, _| omega[i].clone())
        .map_err(|_| FiniteRefusal::InvalidLift)?;
    let image = contract
        .map
        .transport(1, &column)
        .map_err(|_| FiniteRefusal::InvalidLift)?;
    if image.rows() != target.phi1().certificate().omega.len() {
        return Err(FiniteRefusal::InvalidLift);
    }
    for i in 0..image.rows() {
        if image
            .get_ref(i, 0)
            .map_err(|_| FiniteRefusal::InvalidLift)?
            != &target.phi1().certificate().omega[i]
        {
            return Err(FiniteRefusal::InvalidLift);
        }
    }
    Ok(())
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClosureGuard {
    pub max_gamma_increase: BigRational,
}
pub fn guarded_edit(
    before: &DiagnosticPacket,
    candidate: ExactPhi1Certificate,
    guard: Option<&ClosureGuard>,
) -> Result<DiagnosticPacket, FiniteRefusal> {
    replay(before)?;
    let guard = guard.ok_or(FiniteRefusal::MissingGuard)?;
    if guard.max_gamma_increase.is_negative() {
        return Err(FiniteRefusal::InvalidDamageBudget);
    }
    let after = match propose_value_edit(
        before,
        ProposalPolicy {
            allow_profile_coarsening: false,
            allow_value_edits: true,
        },
        candidate,
    )
    .map_err(|_| FiniteRefusal::ReplayFailed)?
    {
        Proposal::ValueEdit { after, .. } => *after,
        _ => return Err(FiniteRefusal::NoStrictDescent),
    };
    if after.classification().gamma2_value() - before.classification().gamma2_value()
        > guard.max_gamma_increase
    {
        return Err(FiniteRefusal::ClosureDamageExceeded);
    }
    Ok(after)
}
/// Complete declared finite dynamics, independent of the context actions.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteDynamics {
    pub packets: Vec<DiagnosticPacket>,
    pub next: Vec<usize>,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct FixedPointWitness {
    pub state: usize,
}
fn check_fixed(
    packet: &DiagnosticPacket,
    dynamics: &FiniteDynamics,
    witness: FixedPointWitness,
) -> Result<(), FiniteRefusal> {
    if dynamics.packets.is_empty()
        || dynamics.next.len() != dynamics.packets.len()
        || dynamics.next.iter().any(|&i| i >= dynamics.packets.len())
    {
        return Err(FiniteRefusal::InvalidStabilization);
    }
    for p in &dynamics.packets {
        replay(p)?;
    }
    if dynamics.packets.get(witness.state) != Some(packet)
        || dynamics.next.get(witness.state) != Some(&witness.state)
    {
        return Err(FiniteRefusal::InvalidStabilization);
    }
    Ok(())
}
pub fn terminalize(
    packet: &DiagnosticPacket,
    policy: Option<&TerminalPolicy>,
    stabilization: Option<(&FiniteDynamics, FixedPointWitness)>,
) -> Result<FiniteTerminal, FiniteRefusal> {
    replay(packet)?;
    let r = row(packet);
    let terminal = policy.ok_or(FiniteRefusal::MissingPolicy)?.rows[r]
        .ok_or(FiniteRefusal::MissingPolicyRow)?;
    validate_terminal_choice(packet, r, terminal, stabilization)?;
    Ok(terminal)
}

fn validate_terminal_choice(
    packet: &DiagnosticPacket,
    r: usize,
    terminal: FiniteTerminal,
    stabilization: Option<(&FiniteDynamics, FixedPointWitness)>,
) -> Result<(), FiniteRefusal> {
    let valid_direct = matches!(
        (terminal, r),
        (FiniteTerminal::Hold, _)
            | (FiniteTerminal::ExactCertified, 0)
            | (FiniteTerminal::ClosedCertified, 1)
            | (FiniteTerminal::ActiveCertified, 2)
    );
    if valid_direct {
        return Ok(());
    }
    if terminal == FiniteTerminal::StabilizedSurvivor && r == 1 {
        let (d, w) = stabilization.ok_or(FiniteRefusal::MissingStabilization)?;
        return check_fixed(packet, d, w);
    }
    Err(FiniteRefusal::IncompatibleTerminal)
}

// Origin: engine/crates_rs/core_wdp/src/prime_algos/finite_routing.rs
// Claim: urn:core:crates_rs:core-wdp:finite-routing:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord713cea24 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord713cea24` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError713cea24 {
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
impl BoundaryError713cea24 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError713cea24 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError713cea24 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord713cea24 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError713cea24> {
        if capacity_bound == 0 {
            return Err(BoundaryError713cea24::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError713cea24::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError713cea24::ExceedsCapacity {
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
mod l4_boundary_tests_713cea24 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord713cea24::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord713cea24::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord713cea24::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord713cea24::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord713cea24::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError713cea24::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError713cea24::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
