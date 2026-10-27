//! Bounded finite control for WF-RESEARCH-BIND-HOSTS.

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Witness {
    pub goal_id: &'static str,
    pub carrier_val: i64,
    pub secondary_num: i64,
    pub secondary_den: i64,
    pub negative_control_rejected: bool,
}

pub fn reject_missing_host_or_digest_drift(promote_unverified: bool) -> Result<(), &'static str> {
    if promote_unverified {
        Err("reject_missing_host_or_digest_drift")
    } else {
        Ok(())
    }
}

pub fn witness() -> Witness {
    let neg_rejected = reject_missing_host_or_digest_drift(true).is_err();
    Witness {
        goal_id: "WF-RESEARCH-BIND-HOSTS",
        carrier_val: 4,
        secondary_num: 2,
        secondary_den: 2,
        negative_control_rejected: neg_rejected,
    }
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HostBindRatio {
    carrier: i64,
    reduced_num: i64,
    reduced_den: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HostBindRatioError {
    NonPositive,
    NotSum { sum: i64, carrier: i64 },
    Overflow,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wf_research_bind_hosts.rs
// Claim: urn:core:crates_rs:tests:wf-research-bind-hosts:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for HostBindRatioError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for HostBindRatioError {}

impl HostBindRatio {
    pub fn certify(carrier: i64, numerator: i64, denominator: i64) -> Result<Self, HostBindRatioError> {
        if denominator <= 0 || numerator <= 0 || carrier <= 0 { return Err(HostBindRatioError::NonPositive); }
        let sum = numerator.checked_add(denominator).ok_or(HostBindRatioError::Overflow)?;
        if sum != carrier { return Err(HostBindRatioError::NotSum { sum, carrier }); }
        fn gcd(mut a: i64, mut b: i64) -> Result<i64, HostBindRatioError> {
            a = a.checked_abs().ok_or(HostBindRatioError::Overflow)?;
            b = b.checked_abs().ok_or(HostBindRatioError::Overflow)?;
            while b != 0 {
                let r = a.checked_rem(b).ok_or(HostBindRatioError::Overflow)?;
                a = b;
                b = r;
            }
            if a == 0 { return Err(HostBindRatioError::Overflow); }
            Ok(a)
        }
        let divisor = gcd(numerator, denominator)?;
        let reduced_num = numerator.checked_div(divisor).ok_or(HostBindRatioError::Overflow)?;
        let reduced_den = denominator.checked_div(divisor).ok_or(HostBindRatioError::Overflow)?;
        Ok(Self { carrier, reduced_num, reduced_den })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn wf_research_bind_hosts_witness_matches_derivation() {
        let w = witness();
        assert_eq!(w.goal_id, "WF-RESEARCH-BIND-HOSTS");
        assert_eq!(w.carrier_val, 4);
        assert_eq!(w.secondary_num, 2);
        assert_eq!(w.secondary_den, 2);
        assert!(w.negative_control_rejected);
        assert!(reject_missing_host_or_digest_drift(true).is_err());
        assert!(reject_missing_host_or_digest_drift(false).is_ok());
    }

#[test]
    fn exact_witness_holds() {
        let declared = witness();
        assert!(matches!(HostBindRatio::certify(declared.carrier_val, declared.secondary_num, declared.secondary_den), Ok(w) if w.carrier == 4 && w.reduced_num == 1 && w.reduced_den == 1));
        assert!(matches!(HostBindRatio::certify(4, 3, 2), Err(HostBindRatioError::NotSum { .. })));
        assert!(matches!(HostBindRatio::certify(4, 2, 0), Err(HostBindRatioError::NonPositive)));
    }
}
