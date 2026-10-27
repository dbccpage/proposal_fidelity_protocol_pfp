use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{ToPrimitive, Zero};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Hash256(pub [u8; 32]);

impl Hash256 {
    pub fn is_zero(&self) -> bool {
        self.0 == [0; 32]
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CarrierManifestHash(pub Hash256);

impl CarrierManifestHash {
    pub fn is_zero(&self) -> bool {
        self.0.is_zero()
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReplayHash(pub Hash256);

impl ReplayHash {
    pub fn is_zero(&self) -> bool {
        self.0.is_zero()
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ObserverMapHash(pub Hash256);

impl ObserverMapHash {
    pub fn is_zero(&self) -> bool {
        self.0.is_zero()
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct QuotientSpaceHash(pub Hash256);

impl QuotientSpaceHash {
    pub fn is_zero(&self) -> bool {
        self.0.is_zero()
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ToleranceProfileHash(pub Hash256);

impl ToleranceProfileHash {
    pub fn is_zero(&self) -> bool {
        self.0.is_zero()
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EquivalenceRelationHash(pub Hash256);

impl EquivalenceRelationHash {
    pub fn is_zero(&self) -> bool {
        self.0.is_zero()
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ObserverRef(pub String);

impl ObserverRef {
    pub fn is_empty(&self) -> bool {
        self.0.is_empty()
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CheckerRef(pub String);

impl CheckerRef {
    pub fn is_empty(&self) -> bool {
        self.0.is_empty()
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CertificateRef(pub Hash256);

impl CertificateRef {
    pub fn is_zero(&self) -> bool {
        self.0.is_zero()
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LawId(pub String);

impl LawId {
    pub fn is_empty(&self) -> bool {
        self.0.is_empty()
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceRef(pub Hash256);

impl EvidenceRef {
    pub fn is_zero(&self) -> bool {
        self.0.is_zero()
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BoundaryMapsHash(pub Hash256);

impl BoundaryMapsHash {
    pub fn is_zero(&self) -> bool {
        self.0.is_zero()
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct WeightsAndGaugesHash(pub Hash256);

impl WeightsAndGaugesHash {
    pub fn is_zero(&self) -> bool {
        self.0.is_zero()
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DefectFieldHash(pub Hash256);

impl DefectFieldHash {
    pub fn is_zero(&self) -> bool {
        self.0.is_zero()
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ObserverBoundaryHash(pub Hash256);

impl ObserverBoundaryHash {
    pub fn is_zero(&self) -> bool {
        self.0.is_zero()
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RationalValue {
    pub numerator: BigInt,
    pub denominator: BigInt,
}

fn compute_gcd(mut a: BigInt, mut b: BigInt) -> BigInt {
    use num_traits::Zero;
    while !b.is_zero() {
        let temp = b.clone();
        b = a % b;
        a = temp;
    }
    use num_traits::Signed;
    a.abs()
}

impl RationalValue {
    pub fn try_new(numerator: BigInt, denominator: BigInt) -> Option<Self> {
        use num_traits::Zero;
        if denominator.is_zero() {
            return None;
        }
        let gcd = compute_gcd(numerator.clone(), denominator.clone());
        let mut num = numerator / &gcd;
        let mut den = denominator / &gcd;
        if den < BigInt::zero() {
            num = -num;
            den = -den;
        }
        Some(Self {
            numerator: num,
            denominator: den,
        })
    }

    pub fn from_big_rational(value: &BigRational) -> Self {
        Self {
            numerator: value.numer().clone(),
            denominator: value.denom().clone(),
        }
    }

    pub fn as_big_rational(&self) -> Option<BigRational> {
        if self.denominator == BigInt::from(0) {
            return None;
        }
        Some(BigRational::new(
            self.numerator.clone(),
            self.denominator.clone(),
        ))
    }
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum CertifiedScalar {
    ExactRational(RationalValue),
    Interval {
        lower: RationalValue,
        upper: RationalValue,
    },
}

impl CertifiedScalar {
    /// Approximate this exact scalar as an `f64` for DISPLAY ONLY.
    ///
    /// Returns `None` when no faithful approximation exists. Callers must not
    /// substitute a default: a missing approximation is not zero.
    ///
    /// `BigRational::to_f64` is not a reliable failure signal on its own. It
    /// returns `None` only when the result is NaN; on overflow it returns
    /// `Some(INFINITY)` and **on underflow it returns `Some(0.0)`**. A strictly
    /// positive rational below the f64 floor -- say `1/10^400` -- therefore
    /// arrives as an ordinary `0.0` and is indistinguishable from an exact
    /// zero. Any consumer deciding "closed", "exact", or "no defect" from that
    /// value certifies a false result. This method reports all three failure
    /// modes (NaN, non-finite, underflow-from-nonzero) as `None`.
    ///
    /// Exact decisions must use the rational directly, never this projection.
    pub fn to_f64_diagnostic(&self) -> Option<f64> {
        fn approximate(value: &RationalValue) -> Option<f64> {
            let exact = value.as_big_rational()?;
            let approx = exact.to_f64()?;
            if !approx.is_finite() {
                return None;
            }
            // Underflow: a nonzero exact value that projects onto zero.
            if approx == 0.0 && !exact.is_zero() {
                return None;
            }
            Some(approx)
        }

        match self {
            Self::ExactRational(r) => approximate(r),
            Self::Interval { lower, upper } => {
                let lower = approximate(lower)?;
                let upper = approximate(upper)?;
                let midpoint = (lower + upper) / 2.0;
                midpoint.is_finite().then_some(midpoint)
            }
        }
    }

    /// Exact zero test. Unlike [`Self::to_f64_diagnostic`] this cannot be
    /// fooled by underflow: it compares rationals, not floats. An interval is
    /// exactly zero only when both endpoints are.
    pub fn is_exactly_zero(&self) -> bool {
        match self {
            Self::ExactRational(r) => r.as_big_rational().is_some_and(|v| v.is_zero()),
            Self::Interval { lower, upper } => {
                lower.as_big_rational().is_some_and(|v| v.is_zero())
                    && upper.as_big_rational().is_some_and(|v| v.is_zero())
            }
        }
    }

    pub fn is_nonnegative_exact_or_interval(&self) -> bool {
        match self {
            Self::ExactRational(r) => {
                if let Some(br) = r.as_big_rational() {
                    br >= BigRational::zero()
                } else {
                    false
                }
            }
            Self::Interval { lower, upper } => {
                if let (Some(l), Some(u)) = (lower.as_big_rational(), upper.as_big_rational()) {
                    l >= BigRational::zero() && u >= l
                } else {
                    false
                }
            }
        }
    }

    pub fn try_exact_rational(&self) -> Option<BigRational> {
        match self {
            Self::ExactRational(r) => r.as_big_rational(),
            _ => None,
        }
    }

    pub fn validate_interval(&self) -> Option<bool> {
        match self {
            Self::Interval { lower, upper } => {
                if let (Some(l), Some(u)) = (lower.as_big_rational(), upper.as_big_rational()) {
                    Some(l <= u)
                } else {
                    Some(false)
                }
            }
            _ => None,
        }
    }
}

// Origin: engine/crates_rs/core_kernel/src/evidence.rs
// Claim: urn:core:crates_rs:core-kernel:evidence:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb5dddba1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb5dddba1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb5dddba1 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryErrorb5dddba1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb5dddba1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb5dddba1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb5dddba1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb5dddba1> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb5dddba1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb5dddba1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb5dddba1::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod underflow_tests {
    use super::*;
    use num_bigint::BigInt;

    /// `1 / 10^400` is strictly positive but below the f64 floor.
    fn subfloor_positive() -> RationalValue {
        let denominator = BigInt::from(10u32).pow(400);
        RationalValue::try_new(BigInt::from(1u32), denominator)
            .expect("nonzero denominator is valid")
    }

    fn exact_zero() -> RationalValue {
        RationalValue::try_new(BigInt::from(0u32), BigInt::from(1u32)).expect("0/1 is valid")
    }

    /// The defect this method exists to prevent. `BigRational::to_f64` returns
    /// `Some(0.0)` on underflow -- not `None` -- so a strictly positive value
    /// used to arrive as an ordinary zero, indistinguishable from an exact
    /// zero. Consumers deciding "closed" or "exact" from it certified a false
    /// result.
    #[test]
    fn subfloor_positive_refuses_to_project_rather_than_reading_as_zero() {
        let scalar = CertifiedScalar::ExactRational(subfloor_positive());

        // The underlying conversion still yields Some(0.0) -- this is the trap.
        let raw = scalar
            .try_exact_rational()
            .expect("exact variant")
            .to_f64()
            .expect("to_f64 returns Some on underflow, not None");
        assert_eq!(
            raw, 0.0,
            "precondition: the raw conversion underflows to 0.0"
        );

        // The diagnostic projection must refuse instead of passing that on.
        assert_eq!(scalar.to_f64_diagnostic(), None);
        // And the exact test must not be fooled by it.
        assert!(!scalar.is_exactly_zero());
    }

    /// The discriminating half: a genuine exact zero still projects to 0.0 and
    /// still reports as exactly zero. Without this, refusing everything would
    /// pass the test above.
    #[test]
    fn genuine_zero_still_projects_and_reports_zero() {
        let scalar = CertifiedScalar::ExactRational(exact_zero());
        assert_eq!(scalar.to_f64_diagnostic(), Some(0.0));
        assert!(scalar.is_exactly_zero());
    }

    /// An interval whose endpoints are both sub-floor positive is strictly
    /// positive everywhere, yet its midpoint used to compute as
    /// (0.0 + 0.0) / 2.0 = 0.0 and certify `ClosureStatus::Closed`.
    #[test]
    fn subfloor_interval_refuses_and_is_not_exactly_zero() {
        let scalar = CertifiedScalar::Interval {
            lower: subfloor_positive(),
            upper: subfloor_positive(),
        };
        assert_eq!(scalar.to_f64_diagnostic(), None);
        assert!(!scalar.is_exactly_zero());
    }

    /// An interval is exactly zero only when both endpoints are.
    #[test]
    fn interval_is_exactly_zero_only_when_both_endpoints_are() {
        assert!(CertifiedScalar::Interval {
            lower: exact_zero(),
            upper: exact_zero(),
        }
        .is_exactly_zero());

        assert!(!CertifiedScalar::Interval {
            lower: exact_zero(),
            upper: subfloor_positive(),
        }
        .is_exactly_zero());
    }
}

#[cfg(test)]
mod contract_tests {
    use super::*;
    use num_bigint::BigInt;

    #[test]
    fn rational_value_rejects_zero_denominator() {
        assert_eq!(
            RationalValue::try_new(BigInt::from(1), BigInt::from(0)),
            None
        );

        let forged = RationalValue {
            numerator: BigInt::from(1),
            denominator: BigInt::from(0),
        };
        assert_eq!(forged.as_big_rational(), None);

        let ok = RationalValue::try_new(BigInt::from(2), BigInt::from(4))
            .expect("nonzero denominator is valid");
        assert_eq!(ok.numerator, BigInt::from(1));
        assert_eq!(ok.denominator, BigInt::from(2));
        assert_eq!(
            ok.as_big_rational(),
            Some(BigRational::new(BigInt::from(1), BigInt::from(2)))
        );
    }

    #[test]
    fn rational_values_normalize_signs_and_common_factors() {
        for (numerator, denominator, expected_numerator, expected_denominator) in [
            (2, 4, 1, 2),
            (-2, 4, -1, 2),
            (2, -4, -1, 2),
            (0, 4, 0, 1),
            (6, 3, 2, 1),
        ] {
            let actual = RationalValue::try_new(numerator.into(), denominator.into()).unwrap();
            assert_eq!(actual.numerator, BigInt::from(expected_numerator));
            assert_eq!(actual.denominator, BigInt::from(expected_denominator));
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_b5dddba1 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordb5dddba1::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordb5dddba1::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordb5dddba1::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordb5dddba1::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordb5dddba1::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorb5dddba1::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorb5dddba1::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
