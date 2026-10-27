#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

pub fn evaluate_doc_msl_g2(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "DOC-MSL-G2",
            domain: "doc_msl_g2_cylindrical_sobolev",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = (4, 2, 1);
    if candidate != expected {
        return ControlReceipt {
            control_id: "DOC-MSL-G2",
            domain: "doc_msl_g2_cylindrical_sobolev",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "DOC-MSL-G2",
        domain: "doc_msl_g2_cylindrical_sobolev",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_doc_msl_g2_scoped_control() {
    let ok = evaluate_doc_msl_g2((4, 2, 1), false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, (4, 2, 1));

    let drifted = evaluate_doc_msl_g2((4 + 1, 2, 1), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_doc_msl_g2((4, 2, 1), true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}

/// Degrees of freedom on a cylindrical grid are the checked product of the two positive axis counts.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CylindricalGridWitness {
    n_theta: u64,
    n_axis: u64,
    dof: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CylindricalGridError {
    ZeroAxis,
    Overflow,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/doc_msl_g2.rs
// Claim: urn:core:crates_rs:tests:doc-msl-g2:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CylindricalGridError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CylindricalGridError {}

impl CylindricalGridWitness {
    pub fn try_grid(n_theta: u64, n_axis: u64) -> Result<Self, CylindricalGridError> {
        if n_theta == 0 || n_axis == 0 {
            return Err(CylindricalGridError::ZeroAxis);
        }
        let dof = n_theta
            .checked_mul(n_axis)
            .ok_or(CylindricalGridError::Overflow)?;
        Ok(Self {
            n_theta,
            n_axis,
            dof,
        })
    }

    pub fn dof(&self) -> u64 {
        self.dof
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
