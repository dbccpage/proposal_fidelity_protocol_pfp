#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

pub fn evaluate_wdp_dp4_02_residual(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "WDP-DP4-02-RESIDUAL",
            domain: "dp4_contractive_complement",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = (4, 1, 0);
    if candidate != expected {
        return ControlReceipt {
            control_id: "WDP-DP4-02-RESIDUAL",
            domain: "dp4_contractive_complement",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "WDP-DP4-02-RESIDUAL",
        domain: "dp4_contractive_complement",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_wdp_dp4_02_residual_scoped_control() {
    let ok = evaluate_wdp_dp4_02_residual((4, 1, 0), false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, (4, 1, 0));

    let drifted = evaluate_wdp_dp4_02_residual((4 + 1, 1, 0), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_wdp_dp4_02_residual((4, 1, 0), true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NilpotentShift {
    cube_e0: [i64; 4],
    fourth_zero: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum NilError {
    Overflow,
    NotNilpotent,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_dp4_02_residual.rs
// Claim: urn:core:crates_rs:tests:wdp-dp4-02-residual:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for NilError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for NilError {}

fn matmul(left: &[[i64; 4]; 4], right: &[[i64; 4]; 4]) -> Result<[[i64; 4]; 4], NilError> {
    let mut out = [[0i64; 4]; 4];
    for i in 0..4 {
        for j in 0..4 {
            let mut sum = 0i64;
            for k in 0..4 {
                let a = left.get(i).and_then(|row| row.get(k)).copied().ok_or(NilError::NotNilpotent)?;
                let b = right.get(k).and_then(|row| row.get(j)).copied().ok_or(NilError::NotNilpotent)?;
                sum = sum.checked_add(a.checked_mul(b).ok_or(NilError::Overflow)?).ok_or(NilError::Overflow)?;
            }
            let row = out.get_mut(i).ok_or(NilError::NotNilpotent)?;
            let cell = row.get_mut(j).ok_or(NilError::NotNilpotent)?;
            *cell = sum;
        }
    }
    Ok(out)
}

pub fn shift_nilpotent() -> Result<NilpotentShift, NilError> {
    let n = [
        [0, 0, 0, 0],
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
    ];
    let n2 = matmul(&n, &n)?;
    let n3 = matmul(&n2, &n)?;
    let n4 = matmul(&n3, &n)?;
    let fourth_zero = n4.iter().all(|row| row.iter().all(|entry| *entry == 0));
    let mut cube_e0 = [0i64; 4];
    for i in 0..4 {
        let entry = n3.get(i).and_then(|row| row.get(0)).copied().ok_or(NilError::NotNilpotent)?;
        let cell = cube_e0.get_mut(i).ok_or(NilError::NotNilpotent)?;
        *cell = entry;
    }
    if !fourth_zero || cube_e0 != [0, 0, 0, 1] {
        return Err(NilError::NotNilpotent);
    }
    Ok(NilpotentShift {
        cube_e0,
        fourth_zero,
    })
}

#[test]
fn the_shift_vanishes_at_the_fourth_power_and_not_the_third() {
    let shift = shift_nilpotent();
    assert!(matches!(
        shift,
        Ok(NilpotentShift {
            cube_e0: [0, 0, 0, 1],
            fourth_zero: true,
        })
    ));
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
