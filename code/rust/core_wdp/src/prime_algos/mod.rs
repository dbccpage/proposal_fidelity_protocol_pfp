//! Engine Algorithm Prime Triad and Descent Engine.
//!
//! Owns:
//! - Prime -1: Candidate proposal and untrusted intake ([`prime_candidate`]).
//! - Prime 000: Binding twelve-step obstruction packet fill order, admission, and conformance ([`prime_algorithm_0`], [`prime_algorithm_0_admission`], [`prime_algorithm_0_conformance`]).
//! - Prime 001: Inter-carrier transport soundness and sealed loss ledgers ([`prime_algorithm_1`]).
//! - Prime 002: Continuation predicate `CanContinue_n`, six anti-cheat halting laws, and terminalizer ([`prime_algorithm_2`]).
//! - Scope commitments & sealed evidence ([`prime_scope`]).
//! - Nine Up-Lift Gate ([`licensed_lift_gate`]).
//! - Domain Adapters & Rosetta cross-domain stats ([`domain_adapters`], [`rosetta`]).
//! - Descent Engine: Sovereign coordinator wiring Prime Triad to [`crate::coda`] and [`crate::solver_of_solvers`] ([`descent_engine`]).
//!
//! AuthorityEffect: strictly None throughout. All mathematical decisions are exact rational (`BigRational`).

/// Finite mathematical lift/guard/terminal profile, not the full Prime 002 gate.
pub mod finite_routing;
pub mod descent_engine;
pub mod domain_adapters;
pub mod licensed_lift_gate;
pub mod prime_algorithm_0;
pub mod prime_algorithm_0_admission;
pub mod prime_algorithm_0_conformance;
pub mod prime_algorithm_1;
pub mod prime_algorithm_2;
pub mod prime_candidate;
pub mod prime_scope;
pub mod rosetta;

// Backward-compatibility aliases
pub use prime_algorithm_0 as oeprmalg0;
pub use prime_algorithm_0_admission as oeprmalg0_admission;
pub use prime_algorithm_0_conformance as oeprmalg0_conformance;
pub use prime_algorithm_1 as oeprmalg1;
pub use prime_algorithm_2 as oeprmalg2;

// Convenient re-exports
pub use descent_engine::{DescentExecutionReceipt, DescentRefusal, PrimeDescentCoordinator};
pub use licensed_lift_gate::{LicensedLiftAdmission, NineUpLiftBits, PaperEr003LiftCertificate};
pub use prime_algorithm_0::{
    run_admitted, run_oeprmalg0, run_prime_algorithm_0, DomainAdapter, Oeprmalg0Receipt,
    PrimeAlgorithm0Receipt, PrimeDomain,
};
pub use prime_algorithm_1::{
    transport, LossLedger, TransportRefusal, TransportStatus, TransportedPacket,
};
pub use prime_algorithm_2::{
    can_continue_n, terminalize, write_step, AntiCheatLaw, Budget, ContinuationEvidence,
    ControlState, Gamma2Zero, LawRefusal, OpenControlState, StepClaim, StepOp, StepPermit,
    TerminalControlState, TerminalPermit, TerminalRefusal,
};
pub use prime_candidate::{CandidateProposalV1, PrimeStage, PrimeStageRecordV1, PrimeTraceLogger};
pub use prime_scope::{BoundCarrierManifest, CallerAttested, ScopeBinding};

/// Operation ceiling `floor((n1/d1) / (n2/d2))` cross-checked against [`Budget::declare`].
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct OperationBound {
    max_ops: u64,
    spent: u64,
}

/// Refusal of a rational operation bound.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OperationBoundError {
    ZeroDenominator,
    NonPositiveFloor,
    ProductOverflow,
    DeclareFailed,
    QuotientMismatch { exact: u64, declared: usize },
    OpsOverflow,
}

// Origin: engine/crates_rs/core_wdp/src/prime_algos/mod.rs
// Claim: urn:core:crates_rs:core-wdp:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for OperationBoundError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for OperationBoundError {}

impl OperationBound {
    /// Declare a bound from two positive ratios and require [`Budget`] to report the same floor.
    pub fn declare(
        total_num: u64,
        total_den: u64,
        floor_num: u64,
        floor_den: u64,
    ) -> Result<Self, OperationBoundError> {
        let exact = Self::exact_quotient(total_num, total_den, floor_num, floor_den)?;
        let total = num_rational::BigRational::new(
            num_bigint::BigInt::from(total_num),
            num_bigint::BigInt::from(total_den),
        );
        let control_floor = num_rational::BigRational::new(
            num_bigint::BigInt::from(floor_num),
            num_bigint::BigInt::from(floor_den),
        );
        let declared =
            Budget::declare(&total, &control_floor).map_err(|_| OperationBoundError::DeclareFailed)?;
        let declared_ops =
            u64::try_from(declared.max_ops()).map_err(|_| OperationBoundError::OpsOverflow)?;
        if declared_ops != exact {
            return Err(OperationBoundError::QuotientMismatch {
                exact,
                declared: declared.max_ops(),
            });
        }
        let spent = u64::try_from(declared.spent()).map_err(|_| OperationBoundError::OpsOverflow)?;
        Ok(Self {
            max_ops: exact,
            spent,
        })
    }

    fn exact_quotient(
        total_num: u64,
        total_den: u64,
        floor_num: u64,
        floor_den: u64,
    ) -> Result<u64, OperationBoundError> {
        if total_den == 0 || floor_den == 0 {
            return Err(OperationBoundError::ZeroDenominator);
        }
        if floor_num == 0 {
            return Err(OperationBoundError::NonPositiveFloor);
        }
        let numerator = total_num
            .checked_mul(floor_den)
            .ok_or(OperationBoundError::ProductOverflow)?;
        let denominator = total_den
            .checked_mul(floor_num)
            .ok_or(OperationBoundError::ProductOverflow)?;
        if denominator == 0 {
            return Err(OperationBoundError::NonPositiveFloor);
        }
        Ok(numerator / denominator)
    }

    /// Exact floor quotient admitted by both calculations.
    pub fn max_ops(self) -> u64 {
        self.max_ops
    }

    /// Steps already spent. A fresh declaration has spent nothing.
    pub fn spent(self) -> u64 {
        self.spent
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod operation_bound_checks {
    use super::{OperationBound, OperationBoundError};

    #[test]
    fn the_floor_quotient_matches_the_declared_budget() {
        let two = OperationBound::declare(4, 1, 2, 1);
        assert_eq!(two.map(|bound| (bound.max_ops(), bound.spent())), Ok((2, 0)));
        let seven = OperationBound::declare(5, 2, 1, 3);
        assert_eq!(seven.map(|bound| bound.max_ops()), Ok(7));
        assert!(matches!(
            OperationBound::declare(4, 1, 0, 1),
            Err(OperationBoundError::NonPositiveFloor)
        ));
        assert!(matches!(
            OperationBound::declare(4, 0, 2, 1),
            Err(OperationBoundError::ZeroDenominator)
        ));
    }
}
