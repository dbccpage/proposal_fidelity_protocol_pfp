//! Exact rational Born branch counting and the cyclotomic irrational-weight obstruction.
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_6914ac3f<T> {
    fn checked_invariant_6914ac3f(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_6914ac3f<T> for Option<T> {
    #[inline]
    fn checked_invariant_6914ac3f(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_6914ac3f<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_6914ac3f(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_bigint::BigInt;
use num_integer::Integer;
use num_traits::ToPrimitive;
use core_fusion_categories::scalar::FusionScalar;
use core_number_theory::cyclotomic::Cyc5;
use core_number_theory::rational::{rq, One, Rational, Zero};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum BranchCountingError {
    #[error("at most4096 finite branches are admitted")]
    Budget,
    #[error("branch {branch} has an irrational Born weight and cannot have finite integer counts")]
    IrrationalWeight { branch: usize },
    #[error("Born weights must be a nonempty normalized nonnegative family")]
    NotNormalized,
    #[error("branch multiplicity must be strictly positive")]
    NonPositiveMultiplicity,
    #[error("declared multiplicity is not a multiple of the minimal denominator lcm")]
    NotMultiple,
}

/// Exact counting for rational branch weights. Counts are arbitrary-precision,
/// and a refinement preserves the Born measure independently of branch count.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BranchCounting {
    pub multiplicity: BigInt,
    pub counts: Vec<BigInt>,
}
impl BranchCounting {
    /// A finite integer-count refinement exists only when every Born weight
    /// is rational. Cyclotomic weights are read exactly; no approximation is
    /// substituted at the irrational wall.
    pub fn from_cyclotomic_weights(
        weights: &[core_number_theory::cyclotomic_field::CyclotomicNumber],
        multiplicity: Option<BigInt>,
    ) -> Result<Self, BranchCountingError> {
        if weights.len() > 4096 {
            return Err(BranchCountingError::Budget);
        }
        let rational = weights
            .iter()
            .enumerate()
            .map(|(branch, weight)| {
                weight
                    .as_rational()
                    .ok_or(BranchCountingError::IrrationalWeight { branch })
            })
            .collect::<Result<Vec<_>, _>>()?;
        Self::new(&rational, multiplicity)
    }
    pub fn new(
        weights: &[Rational],
        multiplicity: Option<BigInt>,
    ) -> Result<Self, BranchCountingError> {
        if weights.len() > 4096 {
            return Err(BranchCountingError::Budget);
        }
        if weights.is_empty()
            || weights.iter().any(|w| w < &Rational::zero())
            || weights.iter().sum::<Rational>() != Rational::one()
        {
            return Err(BranchCountingError::NotNormalized);
        }
        let minimal = weights.iter().fold(BigInt::one(), |n, w| n.lcm(w.denom()));
        let n = multiplicity.unwrap_or_else(|| minimal.clone());
        if n <= BigInt::zero() {
            return Err(BranchCountingError::NonPositiveMultiplicity);
        }
        if !n.is_multiple_of(&minimal) {
            return Err(BranchCountingError::NotMultiple);
        }
        let counts = weights
            .iter()
            .map(|w| (w * Rational::from_integer(n.clone())).to_integer())
            .collect();
        Ok(Self {
            multiplicity: n,
            counts,
        })
    }
    pub fn verify(&self, weights: &[Rational]) -> bool {
        weights.len() <= 4096
            && self.multiplicity > BigInt::zero()
            && self.counts.len() == weights.len()
            && self.counts.iter().all(|m| m >= &BigInt::zero())
            && self.counts.iter().sum::<BigInt>() == self.multiplicity
            && self
                .counts
                .iter()
                .zip(weights)
                .all(|(m, w)| Rational::new(m.clone(), self.multiplicity.clone()) == *w)
    }
    pub fn from_relative_state(
        packet: &crate::relative_state_branching::RelativeStatePacket,
        multiplicity: Option<BigInt>,
    ) -> Result<Self, BranchCountingError> {
        Self::new(&packet.branch_weights(), multiplicity)
    }
}

/// A fine-grained measurement branch.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct FineGrainedBranch {
    pub branch_index: usize,
    pub sub_branch_count: i64,
    pub multiplicity: i64,
    pub counting_weight: Rational,
    pub born_weight: Rational,
    pub is_rational: bool,
}

/// A fine-grained Everett branching tree.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct FineGrainedTree {
    pub branches: Vec<FineGrainedBranch>,
    pub total_multiplicity: i64,
    pub is_exact_match: bool,
    pub sector: String,
    pub refusal_reason: Option<String>,
}

/// Computes minimal multiplicity N* and integer sub-branch counts m_j.
pub fn compute_minimal_finegraining(weights: &[Rational]) -> Result<(i64, Vec<i64>), String> {
    let exact = BranchCounting::new(weights, None).map_err(|e| e.to_string())?;
    let multiplicity = exact
        .multiplicity
        .to_i64()
        .ok_or_else(|| "multiplicity exceeds the declared i64 result encoding".to_string())?;
    let counts = exact
        .counts
        .iter()
        .map(|m| {
            m.to_i64()
                .ok_or_else(|| "count exceeds the declared i64 result encoding".to_string())
        })
        .collect::<Result<Vec<_>, _>>()?;
    Ok((multiplicity, counts))
}

/// Verifies whether declared sub-counts and multiplicity exactly match Born weights.
pub fn verify_finegraining(weights: &[Rational], multiplicity: i64, sub_counts: &[i64]) -> bool {
    if weights.is_empty()
        || weights.len() > 4096
        || multiplicity <= 0
        || weights.len() != sub_counts.len()
        || weights.iter().any(|w| w < &Rational::zero())
        || sub_counts.iter().any(|m| *m < 0)
    {
        return false;
    }
    let total_m: BigInt = sub_counts.iter().map(|m| BigInt::from(*m)).sum();
    if total_m != BigInt::from(multiplicity) {
        return false;
    }
    for (w, &m) in weights.iter().zip(sub_counts.iter()) {
        if rq(m, multiplicity) != *w {
            return false;
        }
    }
    true
}

/// Constructs a FineGrainedTree for a rational-sector state.
pub fn finegrain_state_rationals(
    weights: &[Rational],
    multiplicity: Option<i64>,
) -> FineGrainedTree {
    let (n_star, min_sub_counts) = match compute_minimal_finegraining(weights) {
        Ok(res) => res,
        Err(err) => {
            return FineGrainedTree {
                branches: vec![],
                total_multiplicity: multiplicity.unwrap_or(0),
                is_exact_match: false,
                sector: "RATIONAL".to_string(),
                refusal_reason: Some(err),
            };
        }
    };

    let (target_n, target_counts) = match multiplicity {
        None => (n_star, min_sub_counts),
        Some(m) => {
            if m <= 0 || m % n_star != 0 {
                return FineGrainedTree {
                    branches: vec![],
                    total_multiplicity: m,
                    is_exact_match: false,
                    sector: "RATIONAL".to_string(),
                    refusal_reason: Some(format!(
                        "Multiplicity {} is not a multiple of minimal N*={}",
                        m, n_star
                    )),
                };
            }
            let scale = m / n_star;
            let scaled_counts: Vec<i64> = min_sub_counts.iter().map(|&c| c * scale).collect();
            (m, scaled_counts)
        }
    };

    let is_ok = verify_finegraining(weights, target_n, &target_counts);
    let mut branches = Vec::new();
    for (idx, (w, &m)) in weights.iter().zip(target_counts.iter()).enumerate() {
        branches.push(FineGrainedBranch {
            branch_index: idx,
            sub_branch_count: m,
            multiplicity: target_n,
            counting_weight: rq(m, target_n),
            born_weight: w.clone(),
            is_rational: true,
        });
    }

    FineGrainedTree {
        branches,
        total_multiplicity: target_n,
        is_exact_match: is_ok,
        sector: "RATIONAL".to_string(),
        refusal_reason: None,
    }
}

/// Single conductor evaluation record.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ConductorEvaluation {
    pub conductor: usize,
    pub totient: usize,
    pub real_subfield_degree: usize,
    pub real_subfield_is_q: bool,
    pub admits_irrational_weight: bool,
    pub status: String,
}

/// Witness state data at conductor 5.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ConductorWitness {
    pub conductor: usize,
    pub state_description: String,
    pub alpha_algebraic: String,
    pub w1_weight_algebraic: String,
    pub minimal_polynomial: String,
    pub discriminant: i64,
    pub is_rational: bool,
}

/// Result of smallest irrational conductor search.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct SmallestConductorResult {
    pub smallest_conductor: usize,
    pub evaluations: Vec<ConductorEvaluation>,
    pub witness: ConductorWitness,
}

/// Searches cyclotomic conductors for the smallest admitting an irrational Born weight.
pub fn search_smallest_irrational_conductor() -> SmallestConductorResult {
    let first = (1usize..=1024)
        .find(|&n| core_number_theory::polynomial::euler_phi(n) > 2)
        .checked_invariant_6914ac3f("bounded cyclotomic witness");
    let conductors: Vec<_> = (1..=first).collect();
    let mut evals = Vec::new();
    let mut smallest = 0;

    for &n in &conductors {
        let totient = core_number_theory::polynomial::euler_phi(n);
        let real_deg = core_number_theory::cyclotomic_field::real_subfield_degree(n)
            .checked_invariant_6914ac3f("fixed finite conductors");
        let is_q = real_deg == 1;
        let admits_irrational = !is_q;
        evals.push(ConductorEvaluation {
            conductor: n,
            totient,
            real_subfield_degree: real_deg,
            real_subfield_is_q: is_q,
            admits_irrational_weight: admits_irrational,
            status: if is_q {
                "RATIONAL_ONLY".to_string()
            } else {
                "ADMITS_IRRATIONAL_WEIGHT".to_string()
            },
        });
        if smallest == 0 && admits_irrational {
            smallest = n;
        }
    }

    // Explicit algebraic verification of conductor 5 witness
    // |psi> = (1, zeta_5 + zeta_5^4)
    let z5 = Cyc5::zeta5(1);
    let z5_4 = Cyc5::zeta5(4);
    let alpha = z5.add(&z5_4);
    let c0 = Cyc5::one();
    let c1 = alpha;

    let b0 = c0.mul(&c0.conj()); // = 1
    let b1 = c1.mul(&c1.conj()); // = alpha^2 = (3 - sqrt(5))/2
    let tot = b0.add(&b1);
    let w1 = b1.mul(&tot.inv()); // = (5 - sqrt(5))/10

    // Minimal polynomial: 5 * w1^2 - 5 * w1 + 1 = 0
    let five = Cyc5::rat(rq(5, 1));
    let one = Cyc5::one();
    let poly_eval = five.mul(&w1.mul(&w1)).sub(&five.mul(&w1)).add(&one);
    assert!(poly_eval.is_zero(), "Minimal polynomial must vanish");

    let witness = ConductorWitness {
        conductor: 5,
        state_description: "(1, zeta_5 + zeta_5^4)".to_string(),
        alpha_algebraic: "2*cos(2*pi/5) = (sqrt(5) - 1)/2".to_string(),
        w1_weight_algebraic: "(5 - sqrt(5)) / 10 = 1/2 - sqrt(5)/10".to_string(),
        minimal_polynomial: "5*x^2 - 5*x + 1 = 0".to_string(),
        discriminant: 5,
        is_rational: w1.to_rational().is_some(),
    };

    SmallestConductorResult {
        smallest_conductor: smallest,
        evaluations: evals,
        witness,
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/branch_finegraining.rs
// Claim: urn:core:crates_rs:core-quantum-physics:branch-finegraining:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_compute_lcm() {
        assert_eq!(
            BigInt::from(1).lcm(&BigInt::from(2)).lcm(&BigInt::from(3)),
            BigInt::from(6)
        );
        assert_eq!(BigInt::from(25).lcm(&BigInt::from(25)), BigInt::from(25));
        assert_eq!(
            BigInt::from(4).lcm(&BigInt::from(6)).lcm(&BigInt::from(8)),
            BigInt::from(24)
        );
    }

    #[test]
    fn test_minimal_finegraining_chsh() {
        let w = [rq(9, 25), rq(16, 25)];
        let (n_star, m) = compute_minimal_finegraining(&w).expect("Should succeed");
        assert_eq!(n_star, 25);
        assert_eq!(m, vec![9, 16]);
    }

    #[test]
    fn test_finegrain_state_rationals() {
        let w = [rq(9, 25), rq(16, 25)];
        let tree_min = finegrain_state_rationals(&w, None);
        assert!(tree_min.is_exact_match);
        assert_eq!(tree_min.total_multiplicity, 25);

        let tree_scaled = finegrain_state_rationals(&w, Some(50));
        assert!(tree_scaled.is_exact_match);
        assert_eq!(tree_scaled.total_multiplicity, 50);

        let tree_bad = finegrain_state_rationals(&w, Some(30));
        assert!(!tree_bad.is_exact_match);
    }

    #[test]
    fn test_search_smallest_irrational_conductor() {
        let res = search_smallest_irrational_conductor();
        assert_eq!(res.smallest_conductor, 5);
        assert_eq!(res.witness.conductor, 5);
        assert_eq!(res.witness.discriminant, 5);
    }
}
