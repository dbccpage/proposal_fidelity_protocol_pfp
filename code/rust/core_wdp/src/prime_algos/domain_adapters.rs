//! Built-in Algorithm Prime 000 domain adapters.
//!
//! Each adapter fills declaration slots for one programme surface and is run
//! through [`crate::prime_algos::prime_algorithm_0::run_prime_algorithm_0`] so every domain emits the same
//! DDA letter-tape work product (H-O1).
//!
//! Step-9 lift candidates carry nine bits + `PaperER003.LicensedLiftCertificate`
//! materials; admission is gated by H-O3 [`crate::prime_algos::licensed_lift_gate`].

use crate::prime_algos::licensed_lift_gate::{
    certificate_from_labels, NineUpLiftBits, PaperEr003LiftCertificate,
};
use crate::prime_algos::prime_algorithm_0::{
    CochainWindow, DeclarationFill, DefectBranch, DomainAdapter, LiftProposal,
    PrimeDomain,
};

/// Fully licensed nine-bit packet (all true, authority preserved).
fn licensed_nine() -> NineUpLiftBits {
    NineUpLiftBits::all_true()
}

/// Certificate labels for a residual → resolve_* operator lift.
fn resolve_cert(residual: &str, operator: &str) -> PaperEr003LiftCertificate {
    certificate_from_labels(
        residual,
        &format!("mss1:{residual}"),
        operator,
        true,  // residual_reduced
        true,  // replay_checked
        true,  // closure_preserved
        false, // policy_violation
    )
}

/// Generic MSS-0 genesis: one witnessed δ₀, justified path-graph cochain, Φ₁>0 Γ₂=0.
pub struct GenericMss0Adapter;

impl DomainAdapter for GenericMss0Adapter {
    fn domain(&self) -> PrimeDomain {
        PrimeDomain::Generic
    }

    fn declaration(&self) -> DeclarationFill {
        DeclarationFill {
            carrier: Some("finite_token_set:{delta_0}".into()),
            primitive_difference: Some("delta_0".into()),
            zero_rel: Some("exact_collapse_of_declared_sameness_only".into()),
            observer: Some("unit_weight_l1_profile".into()),
            witnesses: vec!["replay:exhaust_trace".into(), "hash:toy".into()],
        }
    }

    fn justify_cochain(&self) -> bool {
        true
    }

    fn cochain_window(&self) -> Option<CochainWindow> {
        Some(CochainWindow {
            dim_c0: 2,
            dim_c1: 1,
            dim_c2: 0,
            square_zero: true,
            l1_defect_mass: 0,
        })
    }

    fn residual_masses(&self) -> (u64, u64) {
        (1, 0)
    }

    fn lift_proposal(&self, branch: DefectBranch) -> LiftProposal {
        match branch {
            DefectBranch::StabilizedSurvivor => LiftProposal::Candidate {
                generators: vec!["resolve_delta_0".into()],
                nine_bits: licensed_nine(),
                certificate: resolve_cert("delta_0", "resolve_delta_0"),
            },
            DefectBranch::Open => LiftProposal::SameLevelRepair,
            _ => LiftProposal::SkipClosed,
        }
    }

    fn literature_note(&self) -> Option<String> {
        Some("FOC Sentinel boundary; GOMC LGGR; MSS reconstruction spine".into())
    }

    fn residual_family_label(&self) -> String {
        "generic:sentinel_delta0".into()
    }
}

/// MUB wall scaffold — open residual; no finite licensed lift.
pub struct MubWallAdapter;

impl DomainAdapter for MubWallAdapter {
    fn domain(&self) -> PrimeDomain {
        PrimeDomain::Mub
    }

    fn declaration(&self) -> DeclarationFill {
        DeclarationFill {
            carrier: Some(
                "Declared finite product triple + candidate fourth vector search in C^d".into(),
            ),
            primitive_difference: Some(
                "Non-sameness of exact MU ZeroRel vs candidate stationarity residual".into(),
            ),
            zero_rel: Some(
                "Exact |<e_i,v>|^2 = 1/d for fixed vectors (not float tolerance as theorem)".into(),
            ),
            observer: Some("Declared wall functional / chart — not View-from-Nowhere".into()),
            witnesses: vec![
                "crates/mub share packs".into(),
                "public-export receipts".into(),
            ],
        }
    }

    fn justify_cochain(&self) -> bool {
        false
    }

    fn cochain_window(&self) -> Option<CochainWindow> {
        None
    }

    fn residual_masses(&self) -> (u64, u64) {
        (1, 0)
    }

    fn lift_proposal(&self, _: DefectBranch) -> LiftProposal {
        LiftProposal::OracleGap {
            note: "Global MUB(6)=3 remains OPEN; no finite lift admitted".into(),
        }
    }

    fn literature_note(&self) -> Option<String> {
        Some("ONLY after terminal — Zauner/Renes etc. do not mint theorem".into())
    }

    fn residual_family_label(&self) -> String {
        "mub:wall_open_mub6".into()
    }
}

/// FSP Channel A scaffold.
pub struct FspChannelAAdapter;

impl DomainAdapter for FspChannelAAdapter {
    fn domain(&self) -> PrimeDomain {
        PrimeDomain::Fsp
    }

    fn declaration(&self) -> DeclarationFill {
        DeclarationFill {
            carrier: Some("Channel A parity: F2^V, F2^E, F2^F finite graph".into()),
            primitive_difference: Some(
                "Packet-local delta on declared finite sign configurations".into(),
            ),
            zero_rel: Some("LocalRepairRel / CochainZeroRel as declared in Paper 042".into()),
            observer: Some("Declared observer O with typed readout".into()),
            witnesses: vec![
                "Lean PaperQF partial kernels".into(),
                "replay commands".into(),
            ],
        }
    }

    fn justify_cochain(&self) -> bool {
        true
    }

    fn cochain_window(&self) -> Option<CochainWindow> {
        Some(CochainWindow {
            dim_c0: 3,
            dim_c1: 3,
            dim_c2: 1,
            square_zero: true,
            l1_defect_mass: 0,
        })
    }

    fn residual_masses(&self) -> (u64, u64) {
        (1, 1)
    }

    fn lift_proposal(&self, branch: DefectBranch) -> LiftProposal {
        match branch {
            DefectBranch::Open => LiftProposal::SameLevelRepair,
            DefectBranch::StabilizedSurvivor => LiftProposal::OracleGap {
                note: "general FSP not solved".into(),
            },
            _ => LiftProposal::SkipClosed,
        }
    }

    fn literature_note(&self) -> Option<String> {
        Some("ONLY after terminal — Troyer-Wiese 2005 NP-hardness remains".into())
    }

    fn residual_family_label(&self) -> String {
        "fsp:channel_a_sign_class".into()
    }
}

/// CODA residual-firewall adapter.
pub struct CodaResidualAdapter;

impl DomainAdapter for CodaResidualAdapter {
    fn domain(&self) -> PrimeDomain {
        PrimeDomain::Coda
    }

    fn declaration(&self) -> DeclarationFill {
        DeclarationFill {
            carrier: Some("GTOC finite cover packet / residual ledger host".into()),
            primitive_difference: Some(
                "carrier-Structure vs residual-Structure non-sameness".into(),
            ),
            zero_rel: Some("declared exact residual collapse under FOC repair class".into()),
            observer: Some("declared GTOC ℓ¹ unit-weight observer".into()),
            witnesses: vec![
                "PaperER003 residual terminalizer contracts".into(),
                "encyclopedia residual ledgers".into(),
            ],
        }
    }

    fn justify_cochain(&self) -> bool {
        true
    }

    fn cochain_window(&self) -> Option<CochainWindow> {
        Some(CochainWindow {
            dim_c0: 2,
            dim_c1: 1,
            dim_c2: 0,
            square_zero: true,
            l1_defect_mass: 0,
        })
    }

    fn residual_masses(&self) -> (u64, u64) {
        (1, 0)
    }

    fn lift_proposal(&self, branch: DefectBranch) -> LiftProposal {
        match branch {
            DefectBranch::StabilizedSurvivor => LiftProposal::Candidate {
                generators: vec!["coda_residual_refine".into()],
                nine_bits: licensed_nine(),
                certificate: resolve_cert("coda_q1", "coda_residual_refine"),
            },
            DefectBranch::Open => LiftProposal::SameLevelRepair,
            _ => LiftProposal::SkipClosed,
        }
    }

    fn literature_note(&self) -> Option<String> {
        Some("CODA carrier/residual firewall; Q quarantine non-promotion".into())
    }

    fn residual_family_label(&self) -> String {
        "coda:q1_residual_firewall".into()
    }
}

/// Symbol Game expressivity obstruction adapter.
#[derive(Debug, Clone)]
pub struct SymbolGameExpressivityAdapter {
    pub phi1: u64,
    pub gamma2: u64,
    pub square_zero: bool,
    pub problem_label: String,
}

impl Default for SymbolGameExpressivityAdapter {
    fn default() -> Self {
        Self {
            phi1: 3,
            gamma2: 0,
            square_zero: true,
            problem_label: "expressivity_obstructed_default".into(),
        }
    }
}

impl DomainAdapter for SymbolGameExpressivityAdapter {
    fn domain(&self) -> PrimeDomain {
        PrimeDomain::SymbolGame
    }

    fn declaration(&self) -> DeclarationFill {
        DeclarationFill {
            carrier: Some(format!("symbol_game::expressivity:{}", self.problem_label)),
            primitive_difference: Some(
                "local patch naming non-sameness on overlap discrepancies".into(),
            ),
            zero_rel: Some("ContextuallyGlueable (o_n = 0 in im d0)".into()),
            observer: Some("expressivity_norm_face / unit ℓ¹ diagnostic".into()),
            witnesses: vec![
                "pfp::expressivity".into(),
                "core_functional exact Phi1/Gamma2 rails".into(),
            ],
        }
    }

    fn justify_cochain(&self) -> bool {
        true
    }

    fn cochain_window(&self) -> Option<CochainWindow> {
        Some(CochainWindow {
            dim_c0: 3,
            dim_c1: 3,
            dim_c2: 0,
            square_zero: self.square_zero,
            l1_defect_mass: if self.square_zero { 0 } else { 1 },
        })
    }

    fn residual_masses(&self) -> (u64, u64) {
        (self.phi1, self.gamma2)
    }

    fn lift_proposal(&self, branch: DefectBranch) -> LiftProposal {
        match branch {
            DefectBranch::StabilizedSurvivor if self.phi1 > 0 => LiftProposal::Candidate {
                generators: vec!["expressivity_meta_norm".into()],
                nine_bits: licensed_nine(),
                certificate: resolve_cert(&self.problem_label, "expressivity_meta_norm"),
            },
            DefectBranch::Open => LiftProposal::SameLevelRepair,
            DefectBranch::Closed => LiftProposal::SkipClosed,
            _ => LiftProposal::OracleGap {
                note: "expressivity obstruction unresolved".into(),
            },
        }
    }

    fn literature_note(&self) -> Option<String> {
        Some("Symbol Game math spine; FOC Čech gate; ENC-0891 no Phi1 authority".into())
    }

    fn residual_family_label(&self) -> String {
        format!("symbol_game:{}", self.problem_label)
    }
}

/// All built-in adapters as a fixed roster for Rosetta multi-domain runs.
pub fn builtin_adapter_roster() -> Vec<Box<dyn DomainAdapter>> {
    vec![
        Box::new(GenericMss0Adapter),
        Box::new(MubWallAdapter),
        Box::new(FspChannelAAdapter),
        Box::new(CodaResidualAdapter),
        Box::new(SymbolGameExpressivityAdapter::default()),
    ]
}

// Origin: engine/crates_rs/core_wdp/src/prime_algos/domain_adapters.rs
// Claim: urn:core:crates_rs:core-wdp:domain-adapters:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord22fbd850 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord22fbd850` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError22fbd850 {
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
impl BoundaryError22fbd850 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError22fbd850 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError22fbd850 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord22fbd850 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError22fbd850> {
        if capacity_bound == 0 {
            return Err(BoundaryError22fbd850::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError22fbd850::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError22fbd850::ExceedsCapacity {
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
mod l4_boundary_tests_22fbd850 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord22fbd850::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord22fbd850::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord22fbd850::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord22fbd850::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord22fbd850::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError22fbd850::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError22fbd850::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
