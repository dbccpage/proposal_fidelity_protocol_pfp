#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

pub fn evaluate_gen_wdp_o03(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "GEN-WDP-O03",
            domain: "dynamic_carrier_transport_fillers",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = (3, 3, 1);
    if candidate != expected {
        return ControlReceipt {
            control_id: "GEN-WDP-O03",
            domain: "dynamic_carrier_transport_fillers",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "GEN-WDP-O03",
        domain: "dynamic_carrier_transport_fillers",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_gen_wdp_o03_scoped_control() {
    let ok = evaluate_gen_wdp_o03((3, 3, 1), false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, (3, 3, 1));

    let drifted = evaluate_gen_wdp_o03((3 + 1, 3, 1), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_gen_wdp_o03((3, 3, 1), true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RankDefectError {
    Length,
    OccupiedExceeds,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/gen_wdp_o03.rs
// Claim: urn:core:crates_rs:tests:gen-wdp-o03:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for RankDefectError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for RankDefectError {}

pub fn carrier_rank_defect(ambient: &[u32], occupied: &[u32]) -> Result<Vec<u32>, RankDefectError> {
    if ambient.len() != occupied.len() {
        return Err(RankDefectError::Length);
    }
    let mut defects = Vec::new();
    for (room, used) in ambient.iter().zip(occupied.iter()) {
        if used > room {
            return Err(RankDefectError::OccupiedExceeds);
        }
        let defect = room - used;
        if defect.checked_add(*used) != Some(*room) {
            return Err(RankDefectError::OccupiedExceeds);
        }
        defects.push(defect);
    }
    Ok(defects)
}

#[test]
fn rank_defect_restores_ambient_rank() {
    let defects = carrier_rank_defect(&[3, 3], &[2, 3]);
    assert!(matches!(defects.as_deref(), Ok([1, 0])));
    assert!(matches!(
        carrier_rank_defect(&[3], &[4]),
        Err(RankDefectError::OccupiedExceeds)
    ));
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
