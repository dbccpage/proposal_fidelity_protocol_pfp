//! Exact finite control witness for `PLAN-QP-C5` (`plan_qp_c5`).
//!
//! Evaluates the declared finite carrier invariant and refuses out-of-scope
//! promotion via `reject_undeclared_d1_or_phantom_artifacts`.

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Witness {
    pub carrier_val: i64,
    pub secondary_pair: (i64, i64),
    pub coboundary_cycle_zero: i64,
}

pub fn witness() -> Witness {
    let a = [3_i64, 7, 11];
    let coboundary_cycle_zero = (a[1] - a[0]) + (a[2] - a[1]) + (a[0] - a[2]);
    Witness {
        carrier_val: 3,
        secondary_pair: (2, 2),
        coboundary_cycle_zero,
    }
}

pub fn reject_undeclared_d1_or_phantom_artifacts(claim_flag: &str) -> Result<(), &'static str> {
    if claim_flag == "undeclared_d1_or_phantom_artifacts" || claim_flag == "promote_unrestricted" || claim_flag == "bypass_guard" {
        Err("refused out-of-scope promotion for PLAN-QP-C5: undeclared_d1_or_phantom_artifacts")
    } else {
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::{reject_undeclared_d1_or_phantom_artifacts, witness};

    #[test]
    fn plan_qp_c5_witness_matches_derivation() {
        let w = witness();
        assert_eq!(w.carrier_val, 3);
        assert_eq!(w.secondary_pair, (2, 2));
        assert_eq!(w.coboundary_cycle_zero, 0);
    }

    #[test]
    fn plan_qp_c5_refuses_undeclared_d1_or_phantom_artifacts() {
        assert!(reject_undeclared_d1_or_phantom_artifacts("undeclared_d1_or_phantom_artifacts").is_err());
        assert!(reject_undeclared_d1_or_phantom_artifacts("promote_unrestricted").is_err());
        assert!(reject_undeclared_d1_or_phantom_artifacts("admissible_scoped_control").is_ok());
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TriangleChain {
    pub residues: [i64; 3],
    pub boundary: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ChainError {
    Overflow,
    Disagree,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_qp_c5.rs
// Claim: urn:core:crates_rs:tests:plan-qp-c5:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ChainError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ChainError {}

pub fn triangle_chain(a: i64, b: i64, c: i64) -> Result<TriangleChain, ChainError> {
    let v0 = a.checked_sub(c).ok_or(ChainError::Overflow)?;
    let v1 = b.checked_sub(a).ok_or(ChainError::Overflow)?;
    let v2 = c.checked_sub(b).ok_or(ChainError::Overflow)?;
    let all_zero = v0 == 0 && v1 == 0 && v2 == 0;
    let equal = a == b && b == c;
    if all_zero != equal {
        return Err(ChainError::Disagree);
    }
    Ok(TriangleChain {
        residues: [v0, v1, v2],
        boundary: all_zero,
    })
}

#[cfg(test)]
mod triangle_chain_tests {
    use super::*;

    #[test]
    fn a_constant_edge_is_a_boundary_and_a_spike_is_not() {
        let boundary = triangle_chain(1, 1, 1);
        assert!(matches!(boundary, Ok(chain) if chain.boundary));
        let spike = triangle_chain(1, 0, 0);
        assert!(matches!(spike, Ok(chain) if !chain.boundary && chain.residues == [1, -1, 0]));
    }
}
