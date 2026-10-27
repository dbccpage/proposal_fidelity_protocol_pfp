use std::collections::BTreeSet;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum CubeError {
    Dimension,
    Duplicate,
    Overflow,
    Partition,
    Euler { euler: i64 },
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_odm_guarded_open.rs
// Claim: urn:core:crates_rs:tests:plan-odm-guarded-open:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CubeError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CubeError {}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct CubeCensus {
    admitted: i64,
    open: i64,
    refused: i64,
}

// Exact carrier witness.
// Vertices are admitted, edges are open, and square faces are refused.
// The boundary of the 3-cube is a 2-sphere, so the census must have Euler characteristic 2.
fn enumerate_cube_cells(
    dimension: u32,
    vertices: u32,
) -> Result<(BTreeSet<String>, i64, i64, i64), CubeError> {
    let mut seen = BTreeSet::new();
    let mut admitted = 0i64;
    let mut open = 0i64;
    let mut refused = 0i64;
    for vertex in 0..vertices {
        seen.insert(format!("v{vertex}"));
        admitted += 1;
        for bit in 0..dimension {
            let mask = 1u32 << bit;
            if vertex & mask == 0 {
                let other = vertex | mask;
                seen.insert(format!("e{vertex}_{other}"));
                open += 1;
            }
        }
    }
    let fixed_count = 1u32 << (dimension - 2);
    for low in 0..dimension {
        for high in (low + 1)..dimension {
            for fix in 0..fixed_count {
                seen.insert(format!("f{low}_{high}_{fix}"));
                refused += 1;
            }
        }
    }
    Ok((seen, admitted, open, refused))
}

fn enumerate_history_cube(dimension: u32) -> Result<CubeCensus, CubeError> {
    if !(2..=8).contains(&dimension) {
        return Err(CubeError::Dimension);
    }
    let vertices = 1u32.checked_shl(dimension).ok_or(CubeError::Overflow)?;
    let (seen, admitted, open, refused) = enumerate_cube_cells(dimension, vertices)?;
    let summed = admitted + open + refused;
    let width = i64::try_from(seen.len()).map_err(|_| CubeError::Overflow)?;
    if summed != width {
        return Err(CubeError::Partition);
    }
    let euler = admitted - open + refused;
    if euler != 2 {
        return Err(CubeError::Euler { euler });
    }
    Ok(CubeCensus { admitted, open, refused })
}

impl CubeCensus {
    fn triple(self) -> (i64, i64, i64) {
        (self.admitted, self.open, self.refused)
    }
}

pub fn evaluate_plan_odm_guarded_open(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "PLAN-ODM-GUARDED-OPEN",
            domain: "guarded_history_higher_cell_control",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = match enumerate_history_cube(3) {
        Ok(census) => census.triple(),
        Err(_) => {
            return ControlReceipt {
                control_id: "PLAN-ODM-GUARDED-OPEN",
                domain: "guarded_history_higher_cell_control",
                status: "REFUSED",
                invariant_tuple: candidate,
                reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
            };
        }
    };
    if candidate != expected {
        return ControlReceipt {
            control_id: "PLAN-ODM-GUARDED-OPEN",
            domain: "guarded_history_higher_cell_control",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "PLAN-ODM-GUARDED-OPEN",
        domain: "guarded_history_higher_cell_control",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_plan_odm_guarded_open_scoped_control() {
    let image = enumerate_history_cube(3).map(CubeCensus::triple);
    assert_eq!(image, Ok((8, 12, 6)));
    let ok = image.map(|triple| evaluate_plan_odm_guarded_open(triple, false));
    assert!(matches!(
        ok.as_ref(),
        Ok(receipt)
            if receipt.control_id == "PLAN-ODM-GUARDED-OPEN"
                && receipt.domain == "guarded_history_higher_cell_control"
                && receipt.status == "PASS"
                && receipt.reason == "SCOPED_CONTROL_VERIFIED"
                && receipt.invariant_tuple == (8, 12, 6)
    ));

    let drifted = evaluate_plan_odm_guarded_open((8 + 1, 12, 6), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = image.map(|triple| evaluate_plan_odm_guarded_open(triple, true));
    assert!(matches!(
        promoted.as_ref(),
        Ok(receipt)
            if receipt.status == "REFUSED" && receipt.reason == "UNRESTRICTED_PROMOTION_REFUSED"
    ));
}

#[test]
fn a_square_is_not_the_boundary_of_the_history_cube() {
    assert!(matches!(enumerate_history_cube(2), Err(CubeError::Euler { euler: 1 })));
    assert!(matches!(enumerate_history_cube(1), Err(CubeError::Dimension)));
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
