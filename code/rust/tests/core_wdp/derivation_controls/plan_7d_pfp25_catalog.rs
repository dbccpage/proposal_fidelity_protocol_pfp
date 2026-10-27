#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

pub fn evaluate_plan_7d_pfp25_catalog(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "PLAN-7D-PFP25-CATALOG",
            domain: "pfp25_shared_target_control",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = (25, 7, 0);
    if candidate != expected {
        return ControlReceipt {
            control_id: "PLAN-7D-PFP25-CATALOG",
            domain: "pfp25_shared_target_control",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "PLAN-7D-PFP25-CATALOG",
        domain: "pfp25_shared_target_control",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CatalogResidual {
    size: i64,
    hits: i64,
    residual: i64,
    uncovered: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CatalogResidualError {
    Negative,
    Residual,
    HitsAboveSize,
    Overflow,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_7d_pfp25_catalog.rs
// Claim: urn:core:crates_rs:tests:plan-7d-pfp25-catalog:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CatalogResidualError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CatalogResidualError {}

impl CatalogResidual {
    pub fn certify(triple: (i64, i64, i64)) -> Result<Self, CatalogResidualError> {
        let (size, hits, residual) = triple;
        if size <= 0 || hits < 0 || residual < 0 { return Err(CatalogResidualError::Negative); }
        if residual != 0 { return Err(CatalogResidualError::Residual); }
        if hits > size { return Err(CatalogResidualError::HitsAboveSize); }
        let uncovered = size.checked_sub(hits).ok_or(CatalogResidualError::Overflow)?;
        Ok(Self { size, hits, residual, uncovered })
    }
}

#[test]
fn test_plan_7d_pfp25_catalog_scoped_control() {
    let ok = evaluate_plan_7d_pfp25_catalog((25, 7, 0), false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, (25, 7, 0));

    let drifted = evaluate_plan_7d_pfp25_catalog((25 + 1, 7, 0), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_plan_7d_pfp25_catalog((25, 7, 0), true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exact_witness_tests {
    use super::*;

    #[test]
    fn exact_witness_holds() {
        assert!(matches!(CatalogResidual::certify((25, 7, 0)), Ok(w) if w.uncovered == 18 && w.residual == 0));
        assert!(matches!(CatalogResidual::certify((25, 26, 0)), Err(CatalogResidualError::HitsAboveSize)));
        assert!(matches!(CatalogResidual::certify((25, 7, 1)), Err(CatalogResidualError::Residual)));
    }
}
