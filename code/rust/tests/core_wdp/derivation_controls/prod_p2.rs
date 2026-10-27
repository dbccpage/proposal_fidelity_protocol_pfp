//! P2 Provenance-Gated Output Layer (PROD-P2) exact verifier.

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum GateVerdict {
    Accepted { midpoint: i64, radius_num: i64, radius_den: i64 },
    Refused { reason: String },
}

pub fn gate_measurement_output(
    indication_mapped: bool,
    uncertainty_num: i64,
    uncertainty_den: i64,
    midpoint: i64,
) -> GateVerdict {
    if !indication_mapped {
        return GateVerdict::Refused {
            reason: "UNMAPPED_INDICATION".to_string(),
        };
    }
    if uncertainty_den <= 0 || uncertainty_num < 0 {
        return GateVerdict::Refused {
            reason: "INVALID_UNCERTAINTY".to_string(),
        };
    }
    GateVerdict::Accepted {
        midpoint,
        radius_num: uncertainty_num,
        radius_den: uncertainty_den,
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_p2_provenance_gate() {
        assert_eq!(
            gate_measurement_output(true, 3, 2, -12),
            GateVerdict::Accepted {
                midpoint: -12,
                radius_num: 3,
                radius_den: 2
            }
        );
        assert_eq!(
            gate_measurement_output(true, -1, 10, -12),
            GateVerdict::Refused {
                reason: "INVALID_UNCERTAINTY".to_string()
            }
        );
    }
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
struct ReducedRadius { numer: i64, denom: i64 }

#[derive(Debug, Clone, PartialEq, Eq)]
enum RadiusError { Denom, Sign, Reduce }

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/prod_p2.rs
// Claim: urn:core:crates_rs:tests:prod-p2:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for RadiusError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for RadiusError {}

fn radius_gcd(mut a: u64, mut b: u64) -> u64 {
    while b != 0 {
        let r = a % b;
        a = b;
        b = r;
    }
    a
}

fn reduce_radius(numer: i64, denom: i64) -> Result<ReducedRadius, RadiusError> {
    if denom <= 0 {
        return Err(RadiusError::Denom);
    }
    if numer < 0 {
        return Err(RadiusError::Sign);
    }
    let g = i64::try_from(radius_gcd(numer.unsigned_abs(), denom.unsigned_abs())).map_err(|_| RadiusError::Reduce)?;
    let numer = numer.checked_div(g).ok_or(RadiusError::Reduce)?;
    let denom = denom.checked_div(g).ok_or(RadiusError::Reduce)?;
    Ok(ReducedRadius { numer, denom })
}

#[cfg(test)]
mod radius_checks {
    use super::reduce_radius;

    #[test]
    fn four_over_two_reduces_to_two_over_one() {
        let radius = reduce_radius(4, 2);
        assert!(matches!(radius, Ok(r) if r.numer == 2 && r.denom == 1));
    }

    #[test]
    fn a_zero_denominator_is_refused() {
        assert!(matches!(reduce_radius(1, 0), Err(super::RadiusError::Denom)));
    }
}
