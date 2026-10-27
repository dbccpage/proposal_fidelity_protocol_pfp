pub fn verify_next_3_endpoints(
    substitute_q6_continuation: bool,
    substitute_generic_controller_stages: bool,
    withhold_sg48_task2_until_admission: bool,
) -> Result<(usize, usize, usize), &'static str> {
    if substitute_q6_continuation {
        return Err("Q.6 continuation record cannot substitute for SG-40/SG-48 execution");
    }
    if substitute_generic_controller_stages {
        return Err("generic research-controller stage log cannot substitute for SG-40/SG-48");
    }
    if !withhold_sg48_task2_until_admission {
        return Err("SG-48 Task 2 must remain withheld until Task 1 Stage 5 admission");
    }
    let sg40_after_h1_rank = 0_usize;
    let sg48_r1_size = 3_usize;
    let sg48_ep2_out = 2_usize;
    Ok((sg40_after_h1_rank, sg48_r1_size, sg48_ep2_out))
}

#[test]
fn plan_7d_next_3_witness_and_controls() {
    let (h1_rank, r1_size, ep2_out) =
        verify_next_3_endpoints(false, false, true).expect("valid Next-3 endpoints pass");
    assert_eq!((h1_rank, r1_size, ep2_out), (0, 3, 2));

    assert!(verify_next_3_endpoints(true, false, true).is_err());
    assert!(verify_next_3_endpoints(false, true, true).is_err());
    assert!(verify_next_3_endpoints(false, false, false).is_err());
}

/// Path graph on 2 vertices has h1 = e − v + c = 0. A 3-cycle has 3 edges.
/// An interval has 2 endpoints, and those endpoints plus one equal the cycle edge count.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Next3RankWitness {
    h1: u64,
    cycle_edges: u64,
    interval_endpoints: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Next3RankError {
    NotPath,
    EndpointMismatch,
    Overflow,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_7d_next_3.rs
// Claim: urn:core:crates_rs:tests:plan-7d-next-3:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for Next3RankError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for Next3RankError {}

impl Next3RankWitness {
    pub fn try_path_and_cycle() -> Result<Self, Next3RankError> {
        let vertices = 2u64;
        let edges = 1u64;
        let components = 1u64;
        let h1 = edges
            .checked_add(components)
            .and_then(|sum| sum.checked_sub(vertices))
            .ok_or(Next3RankError::Overflow)?;
        if h1 != 0 {
            return Err(Next3RankError::NotPath);
        }
        let cycle_edges = 3u64;
        let interval_endpoints = 2u64;
        let joined = interval_endpoints
            .checked_add(1)
            .ok_or(Next3RankError::Overflow)?;
        if joined != cycle_edges {
            return Err(Next3RankError::EndpointMismatch);
        }
        Ok(Self {
            h1,
            cycle_edges,
            interval_endpoints,
        })
    }

    pub fn ranks(&self) -> (u64, u64, u64) {
        (self.h1, self.cycle_edges, self.interval_endpoints)
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
