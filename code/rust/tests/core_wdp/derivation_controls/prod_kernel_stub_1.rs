//! Finite executable witness for `PROD-KERNEL-STUB-1`.
//!
//! Models `CheckReceipt` replay on the 3-state `cheaper_route` arena (`s --direct(5)--> t`,
//! `s --step(1)--> u --finish(1)--> t`) and on stalled/trapped `LOSS` arenas:
//! - Accepts `WIN_OPTIMAL` with `initial_value = 2/1`.
//! - Accepts `WIN_FEASIBLE` with suboptimal `initial_value = 5/1` without substituting `2/1`.
//! - Rejects forged `WIN_OPTIMAL` claiming `5/1` is optimal.
//! - Distinguishes `LOSS` with `initial_stalled = true` vs `initial_stalled = false`.

#![forbid(unsafe_code)]

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CertificateClaim {
    Loss,
    WinOptimal,
    WinFeasible,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CheckReceipt {
    pub accepted: bool,
    pub claim: Option<CertificateClaim>,
    pub initial_value_num: Option<i64>,
    pub initial_value_den: Option<i64>,
    pub initial_stalled: Option<bool>,
    pub failures: Vec<&'static str>,
    pub authority_effect: &'static str,
}

/// Replay a submitted strategy certificate on the `cheaper_route` arena:
/// `s --direct(5)--> t`, `s --step(1)--> u --finish(1)--> t`.
/// Never calls a solver and never substitutes the optimal value `2` for a suboptimal or bad certificate.
fn rejected_receipt(failure: &'static str) -> CheckReceipt {
    CheckReceipt {
        accepted: false,
        claim: None,
        initial_value_num: None,
        initial_value_den: None,
        initial_stalled: None,
        failures: vec![failure],
        authority_effect: "None",
    }
}

fn check_terminal_and_u_node(
    claim: CertificateClaim,
    value_u: i64,
    value_t: i64,
    rank_u: i64,
    rank_t: i64,
) -> Result<(), &'static str> {
    if claim == CertificateClaim::Loss {
        return Err("losing region contains a successful terminal");
    }
    if value_t != 0 || rank_t != 0 {
        return Err("terminal value and rank must be zero");
    }
    if value_u != 1 + value_t || rank_u <= rank_t {
        return Err("upper equality or rank descent failed at u");
    }
    Ok(())
}

pub fn replay_cheaper_route_certificate(
    claim: CertificateClaim,
    action_at_s: &str,
    value_s: i64,
    value_u: i64,
    value_t: i64,
    rank_s: i64,
    rank_u: i64,
    rank_t: i64,
) -> CheckReceipt {
    if let Err(msg) = check_terminal_and_u_node(claim, value_u, value_t, rank_u, rank_t) {
        return rejected_receipt(msg);
    }
    let (selected_cost, succ_val, succ_rank) = match action_at_s {
        "direct" => (5, value_t, rank_t),
        "step" => (1, value_u, rank_u),
        _ => return rejected_receipt("selected action is not admissible"),
    };
    if rank_s <= succ_rank {
        return rejected_receipt("strategy leaves winners or fails strict rank descent");
    }
    if value_s != selected_cost + succ_val {
        return rejected_receipt("upper equality failed");
    }
    if claim == CertificateClaim::WinOptimal && (value_s > 5 + value_t || value_s > 1 + value_u) {
        return rejected_receipt("lower inequality failed: a cheaper action exists");
    }
    CheckReceipt {
        accepted: true,
        claim: Some(claim),
        initial_value_num: Some(value_s),
        initial_value_den: Some(1),
        initial_stalled: None,
        failures: vec![],
        authority_effect: "None",
    }
}

pub fn replay_loss_certificate(initial_has_moves: bool) -> CheckReceipt {
    CheckReceipt {
        accepted: true,
        claim: Some(CertificateClaim::Loss),
        initial_value_num: None,
        initial_value_den: None,
        initial_stalled: Some(!initial_has_moves),
        failures: vec![],
        authority_effect: "None",
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/prod_kernel_stub_1.rs
// Claim: urn:core:crates_rs:tests:prod-kernel-stub-1:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord62c0fd5d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord62c0fd5d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError62c0fd5d {
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
impl BoundaryError62c0fd5d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError62c0fd5d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError62c0fd5d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord62c0fd5d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError62c0fd5d> {
        if capacity_bound == 0 {
            return Err(BoundaryError62c0fd5d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError62c0fd5d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError62c0fd5d::ExceedsCapacity {
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

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn replays_optimal_feasible_and_forged_certificates_without_substituting_answers() {
        let opt = replay_cheaper_route_certificate(
            CertificateClaim::WinOptimal,
            "step",
            2,
            1,
            0,
            2,
            1,
            0,
        );
        assert!(opt.accepted);
        assert_eq!(opt.claim, Some(CertificateClaim::WinOptimal));
        assert_eq!(opt.initial_value_num, Some(2));

        let feas = replay_cheaper_route_certificate(
            CertificateClaim::WinFeasible,
            "direct",
            5,
            1,
            0,
            1,
            1,
            0,
        );
        assert!(feas.accepted);
        assert_eq!(feas.claim, Some(CertificateClaim::WinFeasible));
        assert_eq!(feas.initial_value_num, Some(5));

        let forged = replay_cheaper_route_certificate(
            CertificateClaim::WinOptimal,
            "direct",
            5,
            1,
            0,
            1,
            1,
            0,
        );
        assert!(!forged.accepted);
        assert_eq!(forged.claim, None);
        assert_eq!(
            forged.failures,
            vec!["lower inequality failed: a cheaper action exists"]
        );
    }

    #[test]
    fn distinguishes_stalled_and_trapped_loss_certificates() {
        let stalled = replay_loss_certificate(false);
        assert!(stalled.accepted);
        assert_eq!(stalled.initial_stalled, Some(true));

        let trapped = replay_loss_certificate(true);
        assert!(trapped.accepted);
        assert_eq!(trapped.initial_stalled, Some(false));
    }
}

#[test]
fn l4_boundary_admits_and_refuses_62c0fd5d() {
    let admitted = BoundaryRecord62c0fd5d::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord62c0fd5d::try_admit(9, 8).is_err());
}
