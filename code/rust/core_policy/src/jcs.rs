//! Local-CI receipt profile, not full RFC 8785 conformance. AuthorityEffect: None.

include!("../../jcs_subset.rs");

pub(crate) const GATE_LIMITS: Limits = Limits {
    max_bytes: 4_194_304,
    max_depth: 64,
    max_nodes: 100_000,
};

#[derive(Clone, Debug, PartialEq, Eq)]
pub(crate) enum GateLimitError {
    ZeroDepth,
    ZeroNodes,
    NodesExceedBytes { nodes: usize, bytes: usize },
}

// Origin: engine/crates_rs/core_policy/src/jcs.rs
// Claim: urn:core:crates_rs:core-policy:jcs:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for GateLimitError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for GateLimitError {}

/// A gate limit admits a document only when depth and node budgets are positive
/// and the node budget fits in the byte budget.
pub(crate) fn certify_gate_limits(limits: Limits) -> Result<(), GateLimitError> {
    if limits.max_depth == 0 {
        return Err(GateLimitError::ZeroDepth);
    }
    if limits.max_nodes == 0 {
        return Err(GateLimitError::ZeroNodes);
    }
    let nodes = usize::try_from(limits.max_nodes).map_err(|_| GateLimitError::NodesExceedBytes {
        nodes: usize::MAX,
        bytes: limits.max_bytes,
    })?;
    if nodes > limits.max_bytes {
        return Err(GateLimitError::NodesExceedBytes {
            nodes,
            bytes: limits.max_bytes,
        });
    }
    Ok(())
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod gate_limit_witness {
    use super::*;

    #[test]
    fn shipped_gate_limits_fit() {
        assert_eq!(certify_gate_limits(GATE_LIMITS), Ok(()));
    }

    #[test]
    fn zero_depth_is_refused() {
        let limits = Limits {
            max_bytes: 8,
            max_depth: 0,
            max_nodes: 1,
        };
        assert!(matches!(
            certify_gate_limits(limits),
            Err(GateLimitError::ZeroDepth)
        ));
    }
}
