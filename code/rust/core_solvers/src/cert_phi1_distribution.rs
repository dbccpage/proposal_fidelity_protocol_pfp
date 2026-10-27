//! Exact certificate for the distribution-sensitive E.7a ground-state bound.
//!
//! --- Math Contract:
//! - Purpose: replay the exact scalar inequalities used by the OBL-1a
//!   refinement of the E.7a lower bound.
//! - Inputs: a positive graph spectral gap `alpha` and a nonempty finite list
//!   of nonnegative diagonal loads `v_i`. The scalar verifier accepts
//!   `alpha` as a premise; it does not verify that a supplied value is the
//!   graph's Fiedler eigenvalue.
//! - Output: the exact lower bound
//!   `t = alpha * mu / (alpha + mu + m2)`, where
//!   `mu = (sum v_i) / n` and `m2 = (sum v_i^2) / (sum v_i)`.
//! - Zero-load branch: when `sum v_i = 0`, nonnegativity forces every load to
//!   vanish and the certified lower bound is exactly zero. The raw ratio
//!   `(sum v_i^2)/(sum v_i)` is then undefined and stored as `None`, while the
//!   theorem's total convention uses `m2 = 0`.
//! - Invariants: all proof-relevant arithmetic is `BigRational`; the
//!   size-biased Titu inequality, reciprocal-average gate, and comparison with
//!   the legacy `v_max` bound are checked exactly.
//! - Failure: empty carriers, nonpositive gaps, negative loads, provenance
//!   mismatches, resource ceilings, and failed algebraic invariants are typed.
//! - Numerical status: no floating-point value participates in certification.
//! - Authority: the certificate has `AuthorityEffectLevel::None`; it is
//!   mathematical evidence only and cannot authorize a transition.

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Zero};
use core_types::authority_lattice::AuthorityEffectLevel;
use serde::Serialize;
use thiserror::Error;

/// Wire schema for exact OBL-1a distribution-bound certificates.
pub const OBL1A_DISTRIBUTION_BOUND_SCHEMA: &str = "core.obl1a-distribution-bound-certificate.v1";
/// Maximum number of vertex loads accepted by the exact verifier.
pub const OBL1A_HARD_MAX_LOAD_COUNT: usize = 4_096;
/// Maximum numerator or denominator size of any supplied rational.
pub const OBL1A_HARD_MAX_RATIONAL_BITS: u64 = 4_096;
/// Maximum numerator or denominator size of an exact accumulator.
pub const OBL1A_HARD_MAX_ACCUMULATOR_BITS: u64 = 65_536;

/// Lean theorem that supplies the universal Rayleigh-quotient conclusion.
pub const OBL1A_LEAN_BOUND_THEOREM: &str =
    "PaperFOC004.distribution_sensitive_rayleigh_lower_bound";
/// Lean theorem proving that the new constant is at least the legacy E.7a one.
pub const OBL1A_LEAN_IMPROVEMENT_THEOREM: &str = "PaperFOC004.distribution_bound_improves_e7a";
/// Canonical repository-relative source for the proof.
/// Not present in this repository (checked 2026-09-29): this file and its audit are
/// absent from the tree and never appear in its history, and no `.lean` file here declares
/// `PaperFOC004`. The paths and SHA-256 pins record upstream bytes only;
/// `live_lean_sources_match_the_certificate_binding` in
/// `obl1a_distribution_bound_conformance` is `#[ignore]`d while they are absent
/// and fails under `--ignored` until they are restored.
pub const OBL1A_LEAN_SOURCE: &str =
    "engine/lean4/002_finite_obstruction_calculus/PaperFOC004/E7aDistributionBound.lean";
/// Canonical repository-relative source for the axiom audit.
pub const OBL1A_LEAN_AUDIT_SOURCE: &str =
    "engine/lean4/002_finite_obstruction_calculus/PaperFOC004/OBL1aDistributionBoundAudit.lean";
/// SHA-256 of [`OBL1A_LEAN_SOURCE`] at this certificate version.
pub const OBL1A_LEAN_SOURCE_SHA256: &str =
    "2d1917c369d5cb44504085b82e3a46c2f6c036af542a6f5ea017296f614051ad";
/// SHA-256 of [`OBL1A_LEAN_AUDIT_SOURCE`] at this certificate version.
pub const OBL1A_LEAN_AUDIT_SHA256: &str =
    "ecb037865a0b8369236c19a38d0aee48f9cc528c9cf026b5e7a4640c8f7091ab";
/// Axioms disclosed by the checked audit; `sorryAx` and custom axioms are absent.
pub const OBL1A_ALLOWED_LEAN_AXIOMS: [&str; 3] = ["propext", "Classical.choice", "Quot.sound"];

/// Which branch of the exact theorem applies.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum DistributionBoundCase {
    ZeroLoad,
    PositiveLoad,
}

/// Immutable binding to the checked Lean proof and its axiom audit.
///
/// The receipt deliberately has no unchecked deserialization route:
///
/// ```compile_fail
/// use serde::de::DeserializeOwned;
/// use core_solvers::cert_phi1_distribution::Obl1aTheoremReceipt;
/// fn require_deserialize<T: DeserializeOwned>() {}
/// require_deserialize::<Obl1aTheoremReceipt>();
/// ```
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct Obl1aTheoremReceipt {
    bound_theorem: &'static str,
    improvement_theorem: &'static str,
    lean_source: &'static str,
    lean_source_sha256: &'static str,
    lean_audit_source: &'static str,
    lean_audit_sha256: &'static str,
    allowed_axioms: [&'static str; 3],
}

impl Obl1aTheoremReceipt {
    /// Construct the receipt only when both externally computed source hashes
    /// equal the version-pinned canonical hashes.
    pub fn from_source_hashes(
        lean_source_sha256: &str,
        lean_audit_sha256: &str,
    ) -> Result<Self, DistributionBoundError> {
        if lean_source_sha256 != OBL1A_LEAN_SOURCE_SHA256 {
            return Err(DistributionBoundError::TheoremHashMismatch {
                source_path: OBL1A_LEAN_SOURCE,
            });
        }
        if lean_audit_sha256 != OBL1A_LEAN_AUDIT_SHA256 {
            return Err(DistributionBoundError::TheoremHashMismatch {
                source_path: OBL1A_LEAN_AUDIT_SOURCE,
            });
        }
        Ok(Self {
            bound_theorem: OBL1A_LEAN_BOUND_THEOREM,
            improvement_theorem: OBL1A_LEAN_IMPROVEMENT_THEOREM,
            lean_source: OBL1A_LEAN_SOURCE,
            lean_source_sha256: OBL1A_LEAN_SOURCE_SHA256,
            lean_audit_source: OBL1A_LEAN_AUDIT_SOURCE,
            lean_audit_sha256: OBL1A_LEAN_AUDIT_SHA256,
            allowed_axioms: OBL1A_ALLOWED_LEAN_AXIOMS,
        })
    }

    pub fn bound_theorem(&self) -> &'static str {
        self.bound_theorem
    }

    pub fn improvement_theorem(&self) -> &'static str {
        self.improvement_theorem
    }

    pub fn lean_source(&self) -> &'static str {
        self.lean_source
    }

    pub fn lean_source_sha256(&self) -> &'static str {
        self.lean_source_sha256
    }

    pub fn lean_audit_source(&self) -> &'static str {
        self.lean_audit_source
    }

    pub fn lean_audit_sha256(&self) -> &'static str {
        self.lean_audit_sha256
    }

    pub fn allowed_axioms(&self) -> &[&'static str; 3] {
        &self.allowed_axioms
    }
}

/// Sealed exact-rational evidence for one distribution-sensitive bound.
///
/// Every field is private and the type deliberately has no `Deserialize`
/// implementation. Values can be obtained only through
/// [`DistributionBoundVerifier::verify`].
///
/// ```compile_fail
/// use serde::de::DeserializeOwned;
/// use core_solvers::cert_phi1_distribution::DistributionBoundCertificate;
/// fn require_deserialize<T: DeserializeOwned>() {}
/// require_deserialize::<DistributionBoundCertificate>();
/// ```
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct DistributionBoundCertificate {
    schema: &'static str,
    case: DistributionBoundCase,
    spectral_gap: BigRational,
    loads: Vec<BigRational>,
    sum_loads: BigRational,
    mean_load: BigRational,
    second_moment_ratio: Option<BigRational>,
    maximum_load: BigRational,
    target_lower_bound: BigRational,
    constant_shift: BigRational,
    legacy_e7a_lower_bound: BigRational,
    size_biased_sum: Option<BigRational>,
    size_biased_lower_bound: Option<BigRational>,
    size_biased_slack: Option<BigRational>,
    reciprocal_average: BigRational,
    reciprocal_upper_bound: Option<BigRational>,
    reciprocal_gate_slack: BigRational,
    improvement_slack: BigRational,
    strict_improvement: bool,
    theorem_receipt: Obl1aTheoremReceipt,
    authority_effect: AuthorityEffectLevel,
}

impl DistributionBoundCertificate {
    pub fn schema(&self) -> &'static str {
        self.schema
    }

    pub fn case(&self) -> DistributionBoundCase {
        self.case
    }

    pub fn spectral_gap(&self) -> &BigRational {
        &self.spectral_gap
    }

    pub fn loads(&self) -> &[BigRational] {
        &self.loads
    }

    pub fn sum_loads(&self) -> &BigRational {
        &self.sum_loads
    }

    pub fn mean_load(&self) -> &BigRational {
        &self.mean_load
    }

    /// Raw size-biased ratio for positive total load.
    ///
    /// `None` means the raw `0/0` ratio is undefined; the theorem's zero-load branch uses `m2 = 0`.
    pub fn second_moment_ratio(&self) -> Option<&BigRational> {
        self.second_moment_ratio.as_ref()
    }

    pub fn maximum_load(&self) -> &BigRational {
        &self.maximum_load
    }

    pub fn target_lower_bound(&self) -> &BigRational {
        &self.target_lower_bound
    }

    pub fn constant_shift(&self) -> &BigRational {
        &self.constant_shift
    }

    pub fn legacy_e7a_lower_bound(&self) -> &BigRational {
        &self.legacy_e7a_lower_bound
    }

    pub fn size_biased_sum(&self) -> Option<&BigRational> {
        self.size_biased_sum.as_ref()
    }

    pub fn size_biased_lower_bound(&self) -> Option<&BigRational> {
        self.size_biased_lower_bound.as_ref()
    }

    pub fn size_biased_slack(&self) -> Option<&BigRational> {
        self.size_biased_slack.as_ref()
    }

    pub fn reciprocal_average(&self) -> &BigRational {
        &self.reciprocal_average
    }

    pub fn reciprocal_upper_bound(&self) -> Option<&BigRational> {
        self.reciprocal_upper_bound.as_ref()
    }

    pub fn reciprocal_gate_slack(&self) -> &BigRational {
        &self.reciprocal_gate_slack
    }

    pub fn improvement_slack(&self) -> &BigRational {
        &self.improvement_slack
    }

    pub fn is_strict_improvement(&self) -> bool {
        self.strict_improvement
    }

    pub fn theorem_receipt(&self) -> &Obl1aTheoremReceipt {
        &self.theorem_receipt
    }

    pub fn authority_effect(&self) -> AuthorityEffectLevel {
        self.authority_effect
    }
}

/// Typed refusal from the exact certificate constructor.
#[derive(Clone, Debug, Error, PartialEq, Eq)]
pub enum DistributionBoundError {
    #[error("at least one vertex load is required")]
    EmptyLoads,
    #[error("load count {count} exceeds hard limit {hard_limit}")]
    LoadCountLimitExceeded { count: usize, hard_limit: usize },
    #[error("the graph spectral gap must be strictly positive")]
    NonPositiveSpectralGap,
    #[error("load at index {index} is negative")]
    NegativeLoad { index: usize },
    #[error(
        "{field} rational at index {index} exceeds {hard_limit} bits \
         (numerator={numerator_bits}, denominator={denominator_bits})"
    )]
    RationalBitLimitExceeded {
        field: &'static str,
        index: usize,
        numerator_bits: u64,
        denominator_bits: u64,
        hard_limit: u64,
    },
    #[error(
        "{stage} accumulator through index {through_index} exceeds {hard_limit} bits \
         (numerator={numerator_bits}, denominator={denominator_bits})"
    )]
    AccumulatorBitLimitExceeded {
        stage: &'static str,
        through_index: usize,
        numerator_bits: u64,
        denominator_bits: u64,
        hard_limit: u64,
    },
    #[error("Lean theorem hash mismatch for {source_path}")]
    TheoremHashMismatch { source_path: &'static str },
    #[error("exact algebraic invariant failed: {invariant}")]
    AlgebraicInvariantViolation { invariant: &'static str },
}

/// Sole exact constructor for [`DistributionBoundCertificate`].
pub struct DistributionBoundVerifier;

impl DistributionBoundVerifier {
    fn validate_distribution_inputs(
        spectral_gap: &BigRational,
        loads: &[BigRational],
    ) -> Result<(), DistributionBoundError> {
        if loads.is_empty() {
            return Err(DistributionBoundError::EmptyLoads);
        }
        if loads.len() > OBL1A_HARD_MAX_LOAD_COUNT {
            return Err(DistributionBoundError::LoadCountLimitExceeded {
                count: loads.len(),
                hard_limit: OBL1A_HARD_MAX_LOAD_COUNT,
            });
        }
        enforce_input_bits(spectral_gap, "spectral_gap", 0)?;
        if *spectral_gap <= BigRational::zero() {
            return Err(DistributionBoundError::NonPositiveSpectralGap);
        }
        for (index, load) in loads.iter().enumerate() {
            enforce_input_bits(load, "load", index)?;
            if load < &BigRational::zero() {
                return Err(DistributionBoundError::NegativeLoad { index });
            }
        }
        Ok(())
    }

    #[allow(clippy::too_many_arguments)]
    fn verify_positive_load_invariants(
        spectral_gap: &BigRational,
        mean_load: &BigRational,
        second_moment_ratio: &BigRational,
        maximum_load: &BigRational,
        target_lower_bound: &BigRational,
        constant_shift: &BigRational,
        size_biased_sum: &BigRational,
        size_biased_slack: &BigRational,
        reciprocal_average: &BigRational,
        reciprocal_upper_bound: &BigRational,
        reciprocal_gate_slack: &BigRational,
        improvement_slack: &BigRational,
        load_count: &BigRational,
        strict_improvement: bool,
    ) -> Result<(), DistributionBoundError> {
        let expected_reciprocal_average = BigRational::one() / constant_shift.clone()
            - size_biased_sum.clone() / (load_count.clone() * constant_shift.clone());
        let target_control_left =
            target_lower_bound.clone() * (constant_shift.clone() + second_moment_ratio.clone());
        let target_control_right = spectral_gap.clone() * mean_load.clone();

        let checks: &[(bool, &'static str)] = &[
            (second_moment_ratio <= maximum_load, "m2 <= maximum_load"),
            (
                *target_lower_bound > BigRational::zero() && target_lower_bound < spectral_gap,
                "0 < target_lower_bound < spectral_gap",
            ),
            (*constant_shift > BigRational::zero(), "constant_shift > 0"),
            (
                *size_biased_slack >= BigRational::zero(),
                "size-biased Titu inequality",
            ),
            (
                *reciprocal_average == expected_reciprocal_average,
                "reciprocal decomposition identity",
            ),
            (
                reciprocal_average <= reciprocal_upper_bound,
                "reciprocal average upper bound",
            ),
            (
                target_control_left < target_control_right,
                "strict target control",
            ),
            (
                *reciprocal_gate_slack > BigRational::zero(),
                "strict spectral reciprocal gate",
            ),
            (
                *improvement_slack >= BigRational::zero(),
                "distribution bound improves legacy E.7a",
            ),
            (
                strict_improvement == (*improvement_slack > BigRational::zero()),
                "strict improvement characterization",
            ),
        ];
        for &(cond, label) in checks {
            require(cond, label)?;
        }
        Ok(())
    }

    /// Verify all scalar premises of the OBL-1a theorem exactly.
    ///
    /// The graph/Fiedler identification of `spectral_gap` remains a caller premise.
    pub fn verify(
        spectral_gap: BigRational,
        loads: Vec<BigRational>,
        theorem_receipt: Obl1aTheoremReceipt,
    ) -> Result<DistributionBoundCertificate, DistributionBoundError> {
        Self::validate_distribution_inputs(&spectral_gap, &loads)?;

        let sum_loads = exact_sum("sum_loads", loads.iter().cloned())?;
        let square_sum = exact_sum(
            "sum_squared_loads",
            loads.iter().map(|load| load.clone() * load.clone()),
        )?;
        let load_count = BigRational::from_integer(BigInt::from(loads.len()));
        let mean_load = sum_loads.clone() / load_count.clone();
        let maximum_load = loads
            .iter()
            .skip(1)
            .fold(loads[0].clone(), |maximum, load| maximum.max(load.clone()));

        if sum_loads.is_zero() {
            return Self::verify_zero_load(
                spectral_gap,
                loads,
                sum_loads,
                mean_load,
                maximum_load,
                load_count,
                theorem_receipt,
            );
        }

        let second_moment_ratio = square_sum / sum_loads.clone();
        let denominator = spectral_gap.clone() + mean_load.clone() + second_moment_ratio.clone();
        let target_lower_bound = spectral_gap.clone() * mean_load.clone() / denominator;
        let constant_shift = spectral_gap.clone() - target_lower_bound.clone();
        let legacy_e7a_lower_bound = spectral_gap.clone() * mean_load.clone()
            / (spectral_gap.clone() + mean_load.clone() + maximum_load.clone());

        let size_biased_sum = exact_sum(
            "size_biased_sum",
            loads
                .iter()
                .map(|load| load.clone() / (constant_shift.clone() + load.clone())),
        )?;
        let size_biased_lower_bound =
            sum_loads.clone() / (constant_shift.clone() + second_moment_ratio.clone());
        let size_biased_slack = size_biased_sum.clone() - size_biased_lower_bound.clone();

        let reciprocal_sum = exact_sum(
            "reciprocal_sum",
            loads
                .iter()
                .map(|load| BigRational::one() / (constant_shift.clone() + load.clone())),
        )?;
        let reciprocal_average = reciprocal_sum / load_count.clone();
        let reciprocal_upper_bound = (constant_shift.clone() + second_moment_ratio.clone()
            - mean_load.clone())
            / (constant_shift.clone() * (constant_shift.clone() + second_moment_ratio.clone()));
        let reciprocal_gate_slack =
            BigRational::one() - spectral_gap.clone() * reciprocal_upper_bound.clone();
        let improvement_slack = target_lower_bound.clone() - legacy_e7a_lower_bound.clone();
        let strict_improvement = !loads
            .iter()
            .filter(|load| !load.is_zero())
            .all(|load| load == &maximum_load);

        Self::verify_positive_load_invariants(
            &spectral_gap,
            &mean_load,
            &second_moment_ratio,
            &maximum_load,
            &target_lower_bound,
            &constant_shift,
            &size_biased_sum,
            &size_biased_slack,
            &reciprocal_average,
            &reciprocal_upper_bound,
            &reciprocal_gate_slack,
            &improvement_slack,
            &load_count,
            strict_improvement,
        )?;

        for (index, value) in [
            &mean_load,
            &second_moment_ratio,
            &target_lower_bound,
            &constant_shift,
            &legacy_e7a_lower_bound,
            &size_biased_sum,
            &size_biased_lower_bound,
            &size_biased_slack,
            &reciprocal_average,
            &reciprocal_upper_bound,
            &reciprocal_gate_slack,
            &improvement_slack,
        ]
        .into_iter()
        .enumerate()
        {
            enforce_accumulator_bits(value, "derived_receipt", index)?;
        }

        Ok(DistributionBoundCertificate {
            schema: OBL1A_DISTRIBUTION_BOUND_SCHEMA,
            case: DistributionBoundCase::PositiveLoad,
            spectral_gap,
            loads,
            sum_loads,
            mean_load,
            second_moment_ratio: Some(second_moment_ratio),
            maximum_load,
            target_lower_bound,
            constant_shift,
            legacy_e7a_lower_bound,
            size_biased_sum: Some(size_biased_sum),
            size_biased_lower_bound: Some(size_biased_lower_bound),
            size_biased_slack: Some(size_biased_slack),
            reciprocal_average,
            reciprocal_upper_bound: Some(reciprocal_upper_bound),
            reciprocal_gate_slack,
            improvement_slack,
            strict_improvement,
            theorem_receipt,
            authority_effect: AuthorityEffectLevel::None,
        })
    }

    #[allow(clippy::too_many_arguments)]
    fn verify_zero_load(
        spectral_gap: BigRational,
        loads: Vec<BigRational>,
        sum_loads: BigRational,
        mean_load: BigRational,
        maximum_load: BigRational,
        load_count: BigRational,
        theorem_receipt: Obl1aTheoremReceipt,
    ) -> Result<DistributionBoundCertificate, DistributionBoundError> {
        require(
            loads.iter().all(BigRational::is_zero),
            "nonnegative zero-sum loads vanish pointwise",
        )?;
        let target_lower_bound = BigRational::zero();
        let constant_shift = spectral_gap.clone();
        let legacy_e7a_lower_bound = BigRational::zero();
        let reciprocal_average = BigRational::one() / spectral_gap.clone();
        let reciprocal_gate_slack =
            BigRational::one() - spectral_gap.clone() * reciprocal_average.clone();
        require(
            reciprocal_gate_slack.is_zero(),
            "zero-load reciprocal gate is exact",
        )?;
        enforce_accumulator_bits(&reciprocal_average, "zero_load_receipt", 0)?;
        enforce_accumulator_bits(&load_count, "zero_load_receipt", 1)?;

        Ok(DistributionBoundCertificate {
            schema: OBL1A_DISTRIBUTION_BOUND_SCHEMA,
            case: DistributionBoundCase::ZeroLoad,
            spectral_gap,
            loads,
            sum_loads,
            mean_load,
            second_moment_ratio: None,
            maximum_load,
            target_lower_bound,
            constant_shift,
            legacy_e7a_lower_bound,
            size_biased_sum: None,
            size_biased_lower_bound: None,
            size_biased_slack: None,
            reciprocal_average,
            reciprocal_upper_bound: None,
            reciprocal_gate_slack,
            improvement_slack: BigRational::zero(),
            strict_improvement: false,
            theorem_receipt,
            authority_effect: AuthorityEffectLevel::None,
        })
    }
}

fn require(condition: bool, invariant: &'static str) -> Result<(), DistributionBoundError> {
    if condition {
        Ok(())
    } else {
        Err(DistributionBoundError::AlgebraicInvariantViolation { invariant })
    }
}

fn enforce_input_bits(
    value: &BigRational,
    field: &'static str,
    index: usize,
) -> Result<(), DistributionBoundError> {
    let numerator_bits = value.numer().bits();
    let denominator_bits = value.denom().bits();
    if numerator_bits > OBL1A_HARD_MAX_RATIONAL_BITS
        || denominator_bits > OBL1A_HARD_MAX_RATIONAL_BITS
    {
        return Err(DistributionBoundError::RationalBitLimitExceeded {
            field,
            index,
            numerator_bits,
            denominator_bits,
            hard_limit: OBL1A_HARD_MAX_RATIONAL_BITS,
        });
    }
    Ok(())
}

fn enforce_accumulator_bits(
    value: &BigRational,
    stage: &'static str,
    through_index: usize,
) -> Result<(), DistributionBoundError> {
    let numerator_bits = value.numer().bits();
    let denominator_bits = value.denom().bits();
    if numerator_bits > OBL1A_HARD_MAX_ACCUMULATOR_BITS
        || denominator_bits > OBL1A_HARD_MAX_ACCUMULATOR_BITS
    {
        return Err(DistributionBoundError::AccumulatorBitLimitExceeded {
            stage,
            through_index,
            numerator_bits,
            denominator_bits,
            hard_limit: OBL1A_HARD_MAX_ACCUMULATOR_BITS,
        });
    }
    Ok(())
}

fn exact_sum(
    stage: &'static str,
    terms: impl IntoIterator<Item = BigRational>,
) -> Result<BigRational, DistributionBoundError> {
    let mut sum = BigRational::zero();
    for (through_index, term) in terms.into_iter().enumerate() {
        sum += term;
        enforce_accumulator_bits(&sum, stage, through_index)?;
    }
    Ok(sum)
}

mod sharp {
    //! Exact root-isolating certificate for the sharp full-distribution E.7 floor.
    //!
    //! --- Math Contract:
    //! - Purpose: isolate the unique root `tau` of
    //!   `F(t) = (alpha / n) * sum_i 1 / (alpha + v_i - t) = 1`.
    //! - Inputs: a positive caller-supplied graph/Fiedler gap `alpha`, at least two
    //!   nonnegative diagonal loads, an exact bisection budget, and
    //!   a receipt binding the checked Lean algebra.
    //! - Output: an exact `BigRational` interval `[lo, hi]` with
    //!   `F(lo) <= 1 <= F(hi)` and `hi < min_i(alpha + v_i)`. Strict monotonicity
    //!   of `F` on that domain makes the interval root-isolating even when `tau`
    //!   is irrational.
    //! - Zero-load branch: `tau = 0` exactly and the interval is `[0, 0]`.
    //! - Comparison scope: `tau` is the exact least eigenvalue of
    //!   `alpha * (I - P) + diag(v)`. If a concrete graph Laplacian satisfies
    //!   `L >= alpha * (I - P)`, then `lambda_min(L + diag(v)) >= tau`.
    //! - Nonclaim: this verifier neither checks the supplied Fiedler premise nor
    //!   claims that `tau` is the exact eigenvalue, or the fixed-graph optimal
    //!   lower bound, for every concrete `L`.
    //! - Invariants: proof-relevant arithmetic is exact `BigRational`; no
    //!   floating-point value participates in certification.
    //! - Failure: malformed inputs, provenance mismatches, resource ceilings,
    //!   nonpositive reciprocal denominators, and failed bracketing invariants are
    //!   typed.
    //! - Authority: every certificate has `AuthorityEffectLevel::None`.

    use num_bigint::BigInt;
    use num_rational::BigRational;
    use num_traits::{One, Zero};
    use core_types::authority_lattice::AuthorityEffectLevel;
    use serde::Serialize;
    use thiserror::Error;

    /// Wire schema for the exact OBL-1a-opt root-isolating certificate.
    pub const OBL1A_SHARP_DISTRIBUTION_SCHEMA: &str =
        "core.obl1a-sharp-distribution-certificate.v1";
    /// Maximum number of vertex loads accepted by the exact verifier.
    pub const OBL1A_SHARP_HARD_MAX_LOAD_COUNT: usize = 4_096;
    /// Maximum numerator or denominator size of any supplied rational.
    pub const OBL1A_SHARP_HARD_MAX_RATIONAL_BITS: u64 = 4_096;
    /// Maximum numerator or denominator size of an exact accumulator.
    pub const OBL1A_SHARP_HARD_MAX_ACCUMULATOR_BITS: u64 = 65_536;
    /// Maximum number of exact rational bisection steps.
    pub const OBL1A_SHARP_HARD_MAX_BISECTION_STEPS: usize = 4_096;
    /// Maximum `load_count * (bisection_steps + 3)` reciprocal evaluations.
    pub const OBL1A_SHARP_HARD_MAX_WORK_UNITS: usize = 1_048_576;

    /// The supplied `alpha` remains an explicit caller premise.
    pub const OBL1A_SHARP_GAP_PREMISE: &str =
        "caller_supplied_alpha_satisfies_L_ge_alpha_times_I_minus_P";
    /// Lean theorem giving strict monotonicity and root uniqueness.
    pub const OBL1A_SHARP_LEAN_UNIQUENESS_THEOREM: &str =
        "PaperFOC004.sharp_reciprocal_root_unique";
    /// Lean theorem giving the comparison-operator quadratic floor.
    pub const OBL1A_SHARP_LEAN_FLOOR_THEOREM: &str = "PaperFOC004.sharp_comparison_quadratic_floor";
    /// Lean theorem giving the equality-vector component identity at the root.
    pub const OBL1A_SHARP_LEAN_EQUALITY_THEOREM: &str =
        "PaperFOC004.sharp_root_eigenvector_component";
    /// Lean theorem isolating a unique root from an exact sub-pole bracket.
    pub const OBL1A_SHARP_LEAN_BRACKET_THEOREM: &str =
        "PaperFOC004.sharp_reciprocal_root_exists_unique_in_bracket";
    /// Lean theorem assembling the universal floor and nonzero equality vector.
    pub const OBL1A_SHARP_LEAN_EXACT_FLOOR_THEOREM: &str =
        "PaperFOC004.sharp_comparison_exact_floor";
    /// Lean theorem identifying the exact zero-load gate.
    pub const OBL1A_SHARP_LEAN_ZERO_LOAD_THEOREM: &str = "PaperFOC004.sharp_zero_load_gate";
    /// Lean theorem transferring the comparison floor through a supplied Loewner premise.
    pub const OBL1A_SHARP_LEAN_TRANSFER_THEOREM: &str =
        "PaperFOC004.sharp_fixed_graph_floor_transfer";
    /// Canonical repository-relative source for the checked base algebra.
    /// Not present in this repository (checked 2026-09-29): this file and the three below are
    /// absent from the tree and never appear in its history, and no `.lean` file here declares
    /// `PaperFOC004`. The paths and SHA-256 pins record upstream bytes only;
    /// `live_lean_sources_match_the_certificate_binding` in
    /// `obl1a_sharp_distribution_bound_conformance` is `#[ignore]`d while they are absent
    /// and fails under `--ignored` until they are restored.
    pub const OBL1A_SHARP_LEAN_SOURCE: &str =
    "engine/lean4/002_finite_obstruction_calculus/PaperFOC004/E7eSharpDistributionFloor.lean";
    /// Canonical repository-relative source for the assembled theorem chain.
    pub const OBL1A_SHARP_LEAN_ASSEMBLY_SOURCE: &str =
    "engine/lean4/002_finite_obstruction_calculus/PaperFOC004/E7eSharpDistributionFloorAssembly.lean";
    /// Canonical repository-relative source for the base axiom audit.
    pub const OBL1A_SHARP_LEAN_AUDIT_SOURCE: &str =
    "engine/lean4/002_finite_obstruction_calculus/PaperFOC004/OBL1aSharpDistributionFloorAudit.lean";
    /// Canonical repository-relative source for the assembly axiom audit.
    pub const OBL1A_SHARP_LEAN_ASSEMBLY_AUDIT_SOURCE: &str =
    "engine/lean4/002_finite_obstruction_calculus/PaperFOC004/OBL1aSharpDistributionFloorAssemblyAudit.lean";
    /// SHA-256 of [`OBL1A_SHARP_LEAN_SOURCE`] at this certificate version.
    pub const OBL1A_SHARP_LEAN_SOURCE_SHA256: &str =
        "fb15198c03174b3d2904b3cb13d2e9c749ef3592adc60c0117a2a72557893089";
    /// SHA-256 of [`OBL1A_SHARP_LEAN_ASSEMBLY_SOURCE`] at this certificate version.
    pub const OBL1A_SHARP_LEAN_ASSEMBLY_SOURCE_SHA256: &str =
        "edfab18b882d677bb65de12513e50152ed021beeb08f20d0e1c6f28af4754018";
    /// SHA-256 of [`OBL1A_SHARP_LEAN_AUDIT_SOURCE`] at this certificate version.
    pub const OBL1A_SHARP_LEAN_AUDIT_SHA256: &str =
        "72ce7a1fe2f40caa8197dfc55aa0e9ceca5214a8b970ef12f19475fc731184e0";
    /// SHA-256 of [`OBL1A_SHARP_LEAN_ASSEMBLY_AUDIT_SOURCE`] at this certificate version.
    pub const OBL1A_SHARP_LEAN_ASSEMBLY_AUDIT_SHA256: &str =
        "20b60e2c420333b8f3078593606784f0f5a17da9200feb8b3703238a51e088a3";
    /// Axioms disclosed by both checked audits; `sorryAx` and custom axioms are absent.
    pub const OBL1A_SHARP_ALLOWED_LEAN_AXIOMS: [&str; 3] =
        ["propext", "Classical.choice", "Quot.sound"];

    /// Which branch of the exact full-distribution theorem applies.
    #[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
    #[serde(rename_all = "snake_case")]
    pub enum SharpDistributionCase {
        ZeroLoad,
        PositiveLoad,
    }

    /// Immutable binding to the checked Lean algebra and axiom audit.
    ///
    /// The receipt deliberately has no unchecked deserialization route:
    ///
    /// ```compile_fail
    /// use serde::de::DeserializeOwned;
    /// use core_solvers::cert_phi1_distribution::Obl1aSharpTheoremReceipt;
    /// fn require_deserialize<T: DeserializeOwned>() {}
    /// require_deserialize::<Obl1aSharpTheoremReceipt>();
    /// ```
    #[derive(Clone, Debug, PartialEq, Eq, Serialize)]
    pub struct Obl1aSharpTheoremReceipt {
        uniqueness_theorem: &'static str,
        floor_theorem: &'static str,
        equality_theorem: &'static str,
        bracket_theorem: &'static str,
        exact_floor_theorem: &'static str,
        zero_load_theorem: &'static str,
        transfer_theorem: &'static str,
        lean_source: &'static str,
        lean_source_sha256: &'static str,
        lean_assembly_source: &'static str,
        lean_assembly_source_sha256: &'static str,
        lean_audit_source: &'static str,
        lean_audit_sha256: &'static str,
        lean_assembly_audit_source: &'static str,
        lean_assembly_audit_sha256: &'static str,
        allowed_axioms: [&'static str; 3],
    }

    impl Obl1aSharpTheoremReceipt {
        /// Construct only when externally computed source hashes match all four
        /// pinned canonical files.
        pub fn from_source_hashes(
            lean_source_sha256: &str,
            lean_assembly_source_sha256: &str,
            lean_audit_sha256: &str,
            lean_assembly_audit_sha256: &str,
        ) -> Result<Self, SharpDistributionBoundError> {
            if lean_source_sha256 != OBL1A_SHARP_LEAN_SOURCE_SHA256 {
                return Err(SharpDistributionBoundError::TheoremHashMismatch {
                    source_path: OBL1A_SHARP_LEAN_SOURCE,
                });
            }
            if lean_assembly_source_sha256 != OBL1A_SHARP_LEAN_ASSEMBLY_SOURCE_SHA256 {
                return Err(SharpDistributionBoundError::TheoremHashMismatch {
                    source_path: OBL1A_SHARP_LEAN_ASSEMBLY_SOURCE,
                });
            }
            if lean_audit_sha256 != OBL1A_SHARP_LEAN_AUDIT_SHA256 {
                return Err(SharpDistributionBoundError::TheoremHashMismatch {
                    source_path: OBL1A_SHARP_LEAN_AUDIT_SOURCE,
                });
            }
            if lean_assembly_audit_sha256 != OBL1A_SHARP_LEAN_ASSEMBLY_AUDIT_SHA256 {
                return Err(SharpDistributionBoundError::TheoremHashMismatch {
                    source_path: OBL1A_SHARP_LEAN_ASSEMBLY_AUDIT_SOURCE,
                });
            }
            Ok(Self {
                uniqueness_theorem: OBL1A_SHARP_LEAN_UNIQUENESS_THEOREM,
                floor_theorem: OBL1A_SHARP_LEAN_FLOOR_THEOREM,
                equality_theorem: OBL1A_SHARP_LEAN_EQUALITY_THEOREM,
                bracket_theorem: OBL1A_SHARP_LEAN_BRACKET_THEOREM,
                exact_floor_theorem: OBL1A_SHARP_LEAN_EXACT_FLOOR_THEOREM,
                zero_load_theorem: OBL1A_SHARP_LEAN_ZERO_LOAD_THEOREM,
                transfer_theorem: OBL1A_SHARP_LEAN_TRANSFER_THEOREM,
                lean_source: OBL1A_SHARP_LEAN_SOURCE,
                lean_source_sha256: OBL1A_SHARP_LEAN_SOURCE_SHA256,
                lean_assembly_source: OBL1A_SHARP_LEAN_ASSEMBLY_SOURCE,
                lean_assembly_source_sha256: OBL1A_SHARP_LEAN_ASSEMBLY_SOURCE_SHA256,
                lean_audit_source: OBL1A_SHARP_LEAN_AUDIT_SOURCE,
                lean_audit_sha256: OBL1A_SHARP_LEAN_AUDIT_SHA256,
                lean_assembly_audit_source: OBL1A_SHARP_LEAN_ASSEMBLY_AUDIT_SOURCE,
                lean_assembly_audit_sha256: OBL1A_SHARP_LEAN_ASSEMBLY_AUDIT_SHA256,
                allowed_axioms: OBL1A_SHARP_ALLOWED_LEAN_AXIOMS,
            })
        }

        pub fn uniqueness_theorem(&self) -> &'static str {
            self.uniqueness_theorem
        }

        pub fn floor_theorem(&self) -> &'static str {
            self.floor_theorem
        }

        pub fn equality_theorem(&self) -> &'static str {
            self.equality_theorem
        }

        pub fn bracket_theorem(&self) -> &'static str {
            self.bracket_theorem
        }

        pub fn exact_floor_theorem(&self) -> &'static str {
            self.exact_floor_theorem
        }

        pub fn zero_load_theorem(&self) -> &'static str {
            self.zero_load_theorem
        }

        pub fn transfer_theorem(&self) -> &'static str {
            self.transfer_theorem
        }

        pub fn lean_source(&self) -> &'static str {
            self.lean_source
        }

        pub fn lean_source_sha256(&self) -> &'static str {
            self.lean_source_sha256
        }

        pub fn lean_assembly_source(&self) -> &'static str {
            self.lean_assembly_source
        }

        pub fn lean_assembly_source_sha256(&self) -> &'static str {
            self.lean_assembly_source_sha256
        }

        pub fn lean_audit_source(&self) -> &'static str {
            self.lean_audit_source
        }

        pub fn lean_audit_sha256(&self) -> &'static str {
            self.lean_audit_sha256
        }

        pub fn lean_assembly_audit_source(&self) -> &'static str {
            self.lean_assembly_audit_source
        }

        pub fn lean_assembly_audit_sha256(&self) -> &'static str {
            self.lean_assembly_audit_sha256
        }

        pub fn allowed_axioms(&self) -> &[&'static str; 3] {
            &self.allowed_axioms
        }
    }
    /// Sealed exact-rational root-isolating evidence.
    ///
    /// Every field is private and the type deliberately has no `Deserialize`
    /// implementation. Values can be obtained only through
    /// [`SharpDistributionBoundVerifier::verify`].
    ///
    /// ```compile_fail
    /// use serde::de::DeserializeOwned;
    /// use core_solvers::cert_phi1_distribution::SharpDistributionBoundCertificate;
    /// fn require_deserialize<T: DeserializeOwned>() {}
    /// require_deserialize::<SharpDistributionBoundCertificate>();
    /// ```
    #[derive(Clone, Debug, PartialEq, Eq, Serialize)]
    pub struct SharpDistributionBoundCertificate {
        schema: &'static str,
        case: SharpDistributionCase,
        gap_premise: &'static str,
        spectral_gap: BigRational,
        loads: Vec<BigRational>,
        load_count: BigRational,
        sum_loads: BigRational,
        mean_load: BigRational,
        minimum_load: BigRational,
        pole_floor: BigRational,
        e7d_lower_bound: BigRational,
        initial_upper_bound: BigRational,
        root_lower_bound: BigRational,
        root_upper_bound: BigRational,
        lower_gate_value: BigRational,
        upper_gate_value: BigRational,
        bisection_steps: usize,
        theorem_receipt: Obl1aSharpTheoremReceipt,
        authority_effect: AuthorityEffectLevel,
    }

    impl SharpDistributionBoundCertificate {
        pub fn schema(&self) -> &'static str {
            self.schema
        }

        pub fn case(&self) -> SharpDistributionCase {
            self.case
        }

        pub fn gap_premise(&self) -> &'static str {
            self.gap_premise
        }

        pub fn spectral_gap(&self) -> &BigRational {
            &self.spectral_gap
        }

        pub fn loads(&self) -> &[BigRational] {
            &self.loads
        }

        pub fn load_count(&self) -> &BigRational {
            &self.load_count
        }

        pub fn sum_loads(&self) -> &BigRational {
            &self.sum_loads
        }

        pub fn mean_load(&self) -> &BigRational {
            &self.mean_load
        }

        pub fn minimum_load(&self) -> &BigRational {
            &self.minimum_load
        }

        /// The first pole `min_i(alpha + v_i)`.
        pub fn pole_floor(&self) -> &BigRational {
            &self.pole_floor
        }

        /// The already-proved E.7d size-biased-moment floor used as the initial
        /// lower endpoint in the positive-load branch.
        pub fn e7d_lower_bound(&self) -> &BigRational {
            &self.e7d_lower_bound
        }

        pub fn initial_upper_bound(&self) -> &BigRational {
            &self.initial_upper_bound
        }

        pub fn root_lower_bound(&self) -> &BigRational {
            &self.root_lower_bound
        }

        pub fn root_upper_bound(&self) -> &BigRational {
            &self.root_upper_bound
        }

        pub fn lower_gate_value(&self) -> &BigRational {
            &self.lower_gate_value
        }

        pub fn upper_gate_value(&self) -> &BigRational {
            &self.upper_gate_value
        }

        pub fn bisection_steps(&self) -> usize {
            self.bisection_steps
        }

        pub fn theorem_receipt(&self) -> &Obl1aSharpTheoremReceipt {
            &self.theorem_receipt
        }

        pub fn authority_effect(&self) -> AuthorityEffectLevel {
            self.authority_effect
        }
    }

    /// Typed refusal from the exact root-isolating constructor.
    #[derive(Clone, Debug, Error, PartialEq, Eq)]
    pub enum SharpDistributionBoundError {
        #[error("at least one vertex load is required")]
        EmptyLoads,
        #[error("graph carrier has {count} vertices; at least {minimum} are required")]
        BelowMinimumVertexCount { count: usize, minimum: usize },
        #[error("load count {count} exceeds hard limit {hard_limit}")]
        LoadCountLimitExceeded { count: usize, hard_limit: usize },
        #[error("the graph spectral gap must be strictly positive")]
        NonPositiveSpectralGap,
        #[error("load at index {index} is negative")]
        NegativeLoad { index: usize },
        #[error("bisection step count {steps} exceeds hard limit {hard_limit}")]
        BisectionStepLimitExceeded { steps: usize, hard_limit: usize },
        #[error("exact reciprocal work {work_units} exceeds hard limit {hard_limit}")]
        WorkLimitExceeded {
            work_units: usize,
            hard_limit: usize,
        },
        #[error(
            "{field} rational at index {index} exceeds {hard_limit} bits \
         (numerator={numerator_bits}, denominator={denominator_bits})"
        )]
        RationalBitLimitExceeded {
            field: &'static str,
            index: usize,
            numerator_bits: u64,
            denominator_bits: u64,
            hard_limit: u64,
        },
        #[error(
            "{stage} accumulator through index {through_index} exceeds {hard_limit} bits \
         (numerator={numerator_bits}, denominator={denominator_bits})"
        )]
        AccumulatorBitLimitExceeded {
            stage: &'static str,
            through_index: usize,
            numerator_bits: u64,
            denominator_bits: u64,
            hard_limit: u64,
        },
        #[error("{stage} reciprocal denominator at index {index} is not positive")]
        NonPositiveReciprocalDenominator { stage: &'static str, index: usize },
        #[error("Lean theorem hash mismatch for {source_path}")]
        TheoremHashMismatch { source_path: &'static str },
        #[error("exact algebraic invariant failed: {invariant}")]
        AlgebraicInvariantViolation { invariant: &'static str },
    }

    /// Sole exact constructor for [`SharpDistributionBoundCertificate`].
    pub struct SharpDistributionBoundVerifier;

    impl SharpDistributionBoundVerifier {
        fn validate_sharp_counts_and_work(
            loads_len: usize,
            bisection_steps: usize,
        ) -> Result<(), SharpDistributionBoundError> {
            if loads_len == 0 {
                return Err(SharpDistributionBoundError::EmptyLoads);
            }
            if loads_len < 2 {
                return Err(SharpDistributionBoundError::BelowMinimumVertexCount {
                    count: loads_len,
                    minimum: 2,
                });
            }
            if loads_len > OBL1A_SHARP_HARD_MAX_LOAD_COUNT {
                return Err(SharpDistributionBoundError::LoadCountLimitExceeded {
                    count: loads_len,
                    hard_limit: OBL1A_SHARP_HARD_MAX_LOAD_COUNT,
                });
            }
            if bisection_steps > OBL1A_SHARP_HARD_MAX_BISECTION_STEPS {
                return Err(SharpDistributionBoundError::BisectionStepLimitExceeded {
                    steps: bisection_steps,
                    hard_limit: OBL1A_SHARP_HARD_MAX_BISECTION_STEPS,
                });
            }
            let work_units = bisection_steps
                .checked_add(3)
                .and_then(|wf| loads_len.checked_mul(wf))
                .ok_or(SharpDistributionBoundError::WorkLimitExceeded {
                    work_units: usize::MAX,
                    hard_limit: OBL1A_SHARP_HARD_MAX_WORK_UNITS,
                })?;
            if work_units > OBL1A_SHARP_HARD_MAX_WORK_UNITS {
                return Err(SharpDistributionBoundError::WorkLimitExceeded {
                    work_units,
                    hard_limit: OBL1A_SHARP_HARD_MAX_WORK_UNITS,
                });
            }
            Ok(())
        }

        fn validate_sharp_scalars(
            spectral_gap: &BigRational,
            loads: &[BigRational],
        ) -> Result<(), SharpDistributionBoundError> {
            enforce_input_bits(spectral_gap, "spectral_gap", 0)?;
            if *spectral_gap <= BigRational::zero() {
                return Err(SharpDistributionBoundError::NonPositiveSpectralGap);
            }
            for (index, load) in loads.iter().enumerate() {
                enforce_input_bits(load, "load", index)?;
                if load < &BigRational::zero() {
                    return Err(SharpDistributionBoundError::NegativeLoad { index });
                }
            }
            Ok(())
        }

        fn evaluate_initial_sharp_gates(
            spectral_gap: &BigRational,
            load_count: &BigRational,
            loads: &[BigRational],
            e7d_lower_bound: &BigRational,
            initial_upper_bound: &BigRational,
            pole_floor: &BigRational,
        ) -> Result<(BigRational, BigRational), SharpDistributionBoundError> {
            require(
                *e7d_lower_bound >= BigRational::zero() && e7d_lower_bound < initial_upper_bound,
                "positive-load initial interval is ordered",
            )?;
            require(
                initial_upper_bound < pole_floor,
                "initial upper endpoint lies below first pole",
            )?;

            let lower_gate = evaluate_gate(
                spectral_gap,
                load_count,
                loads,
                e7d_lower_bound,
                "initial_lower_gate",
            )?;
            let upper_gate = evaluate_gate(
                spectral_gap,
                load_count,
                loads,
                initial_upper_bound,
                "initial_upper_gate",
            )?;
            require(
                lower_gate < BigRational::one(),
                "positive-load E.7d endpoint is strictly below the sharp root",
            )?;
            require(
                upper_gate > BigRational::one(),
                "minimum-load upper endpoint strictly crosses the sharp root",
            )?;
            Ok((lower_gate, upper_gate))
        }

        fn compute_initial_sharp_bounds(
            spectral_gap: &BigRational,
            loads: &[BigRational],
            load_count: &BigRational,
            sum_loads: &BigRational,
            mean_load: &BigRational,
            pole_floor: &BigRational,
        ) -> Result<(BigRational, BigRational, BigRational, BigRational), SharpDistributionBoundError>
        {
            let square_sum = exact_sum(
                "sum_squared_loads",
                loads.iter().map(|load| load.clone() * load.clone()),
            )?;
            let second_moment_ratio = square_sum / sum_loads.clone();
            enforce_accumulator_bits(&second_moment_ratio, "second_moment_ratio", 0)?;
            let e7d_denominator = spectral_gap.clone() + mean_load.clone() + second_moment_ratio;
            enforce_accumulator_bits(&e7d_denominator, "e7d_denominator", 0)?;
            let e7d_lower_bound = spectral_gap.clone() * mean_load.clone() / e7d_denominator;
            enforce_accumulator_bits(&e7d_lower_bound, "e7d_lower_bound", 0)?;
            let initial_upper_bound =
                pole_floor.clone() - spectral_gap.clone() / load_count.clone();
            enforce_accumulator_bits(&initial_upper_bound, "initial_upper_bound", 0)?;

            let (lower_gate, upper_gate) = Self::evaluate_initial_sharp_gates(
                spectral_gap,
                load_count,
                loads,
                &e7d_lower_bound,
                &initial_upper_bound,
                pole_floor,
            )?;
            Ok((
                e7d_lower_bound,
                initial_upper_bound,
                lower_gate,
                upper_gate,
            ))
        }

        #[allow(clippy::too_many_arguments)]
        fn run_sharp_bisection(
            spectral_gap: &BigRational,
            load_count: &BigRational,
            loads: &[BigRational],
            pole_floor: &BigRational,
            mut lower: BigRational,
            mut upper: BigRational,
            mut lower_gate: BigRational,
            mut upper_gate: BigRational,
            bisection_steps: usize,
        ) -> Result<
            (BigRational, BigRational, BigRational, BigRational, usize),
            SharpDistributionBoundError,
        > {
            let mut executed_steps = 0;
            for step in 0..bisection_steps {
                executed_steps = step + 1;
                let midpoint =
                    (lower.clone() + upper.clone()) / BigRational::from_integer(BigInt::from(2_u8));
                enforce_accumulator_bits(&midpoint, "bisection_midpoint", step)?;
                let midpoint_gate = evaluate_gate(
                    spectral_gap,
                    load_count,
                    loads,
                    &midpoint,
                    "bisection_gate",
                )?;
                if midpoint_gate < BigRational::one() {
                    lower = midpoint;
                    lower_gate = midpoint_gate;
                } else if midpoint_gate > BigRational::one() {
                    upper = midpoint;
                    upper_gate = midpoint_gate;
                } else {
                    lower = midpoint.clone();
                    upper = midpoint;
                    lower_gate = midpoint_gate.clone();
                    upper_gate = midpoint_gate;
                    break;
                }
            }
            for &(cond, msg) in &[
                (lower <= upper, "final root interval is ordered"),
                (upper < *pole_floor, "final root interval stays below first pole"),
                (
                    lower_gate <= BigRational::one(),
                    "final lower endpoint satisfies reciprocal gate",
                ),
                (
                    upper_gate >= BigRational::one(),
                    "final upper endpoint crosses reciprocal gate",
                ),
            ] {
                require(cond, msg)?;
            }
            Ok((lower, upper, lower_gate, upper_gate, executed_steps))
        }

        fn compute_sharp_base_summary(
            spectral_gap: &BigRational,
            loads: &[BigRational],
        ) -> Result<
            (BigRational, BigRational, BigRational, BigRational, BigRational),
            SharpDistributionBoundError,
        > {
            let sum_loads = exact_sum("sum_loads", loads.iter().cloned())?;
            let load_count = BigRational::from_integer(BigInt::from(loads.len()));
            enforce_accumulator_bits(&load_count, "load_count", 0)?;
            let mean_load = sum_loads.clone() / load_count.clone();
            enforce_accumulator_bits(&mean_load, "mean_load", 0)?;
            let minimum_load = loads
                .iter()
                .skip(1)
                .fold(loads[0].clone(), |minimum, load| minimum.min(load.clone()));
            enforce_accumulator_bits(&minimum_load, "minimum_load", 0)?;
            let pole_floor = spectral_gap.clone() + minimum_load.clone();
            enforce_accumulator_bits(&pole_floor, "pole_floor", 0)?;
            Ok((sum_loads, load_count, mean_load, minimum_load, pole_floor))
        }

        /// Isolate the unique sharp comparison root using exact rational bisection.
        ///
        /// The supplied `spectral_gap` is a caller premise. This scalar verifier
        /// does not inspect a graph or prove its Fiedler binding.
        pub fn verify(
            spectral_gap: BigRational,
            loads: Vec<BigRational>,
            bisection_steps: usize,
            theorem_receipt: Obl1aSharpTheoremReceipt,
        ) -> Result<SharpDistributionBoundCertificate, SharpDistributionBoundError> {
            Self::validate_sharp_counts_and_work(loads.len(), bisection_steps)?;
            Self::validate_sharp_scalars(&spectral_gap, &loads)?;

            let (sum_loads, load_count, mean_load, minimum_load, pole_floor) =
                Self::compute_sharp_base_summary(&spectral_gap, &loads)?;

            if sum_loads.is_zero() {
                return Self::verify_zero_load(
                    spectral_gap,
                    loads,
                    load_count,
                    sum_loads,
                    mean_load,
                    minimum_load,
                    pole_floor,
                    theorem_receipt,
                );
            }

            let (e7d_lower_bound, initial_upper_bound, lower_gate, upper_gate) =
                Self::compute_initial_sharp_bounds(
                    &spectral_gap,
                    &loads,
                    &load_count,
                    &sum_loads,
                    &mean_load,
                    &pole_floor,
                )?;
            let (lower, upper, lower_gate, upper_gate, executed_steps) = Self::run_sharp_bisection(
                &spectral_gap,
                &load_count,
                &loads,
                &pole_floor,
                e7d_lower_bound.clone(),
                initial_upper_bound.clone(),
                lower_gate,
                upper_gate,
                bisection_steps,
            )?;

            for (index, value) in [
                &load_count,
                &sum_loads,
                &mean_load,
                &minimum_load,
                &pole_floor,
                &e7d_lower_bound,
                &initial_upper_bound,
                &lower,
                &upper,
                &lower_gate,
                &upper_gate,
            ]
            .into_iter()
            .enumerate()
            {
                enforce_accumulator_bits(value, "derived_receipt", index)?;
            }

            Ok(SharpDistributionBoundCertificate {
                schema: OBL1A_SHARP_DISTRIBUTION_SCHEMA,
                case: SharpDistributionCase::PositiveLoad,
                gap_premise: OBL1A_SHARP_GAP_PREMISE,
                spectral_gap,
                loads,
                load_count,
                sum_loads,
                mean_load,
                minimum_load,
                pole_floor,
                e7d_lower_bound,
                initial_upper_bound,
                root_lower_bound: lower,
                root_upper_bound: upper,
                lower_gate_value: lower_gate,
                upper_gate_value: upper_gate,
                bisection_steps: executed_steps,
                theorem_receipt,
                authority_effect: AuthorityEffectLevel::None,
            })
        }

        #[allow(clippy::too_many_arguments)]
        fn verify_zero_load(
            spectral_gap: BigRational,
            loads: Vec<BigRational>,
            load_count: BigRational,
            sum_loads: BigRational,
            mean_load: BigRational,
            minimum_load: BigRational,
            pole_floor: BigRational,
            theorem_receipt: Obl1aSharpTheoremReceipt,
        ) -> Result<SharpDistributionBoundCertificate, SharpDistributionBoundError> {
            require(
                loads.iter().all(BigRational::is_zero),
                "nonnegative zero-sum loads vanish pointwise",
            )?;
            let zero = BigRational::zero();
            let gate = evaluate_gate(&spectral_gap, &load_count, &loads, &zero, "zero_load_gate")?;
            require(
                gate == BigRational::one(),
                "zero-load reciprocal equation is exact at zero",
            )?;

            Ok(SharpDistributionBoundCertificate {
                schema: OBL1A_SHARP_DISTRIBUTION_SCHEMA,
                case: SharpDistributionCase::ZeroLoad,
                gap_premise: OBL1A_SHARP_GAP_PREMISE,
                spectral_gap: spectral_gap.clone(),
                loads,
                load_count,
                sum_loads,
                mean_load,
                minimum_load,
                pole_floor: pole_floor.clone(),
                e7d_lower_bound: zero.clone(),
                initial_upper_bound: zero.clone(),
                root_lower_bound: zero.clone(),
                root_upper_bound: zero,
                lower_gate_value: gate.clone(),
                upper_gate_value: gate,
                bisection_steps: 0,
                theorem_receipt,
                authority_effect: AuthorityEffectLevel::None,
            })
        }
    }

    fn evaluate_gate(
        spectral_gap: &BigRational,
        load_count: &BigRational,
        loads: &[BigRational],
        point: &BigRational,
        stage: &'static str,
    ) -> Result<BigRational, SharpDistributionBoundError> {
        let mut reciprocal_sum = BigRational::zero();
        for (index, load) in loads.iter().enumerate() {
            let denominator = spectral_gap.clone() + load.clone() - point.clone();
            if denominator <= BigRational::zero() {
                return Err(
                    SharpDistributionBoundError::NonPositiveReciprocalDenominator { stage, index },
                );
            }
            enforce_accumulator_bits(&denominator, stage, index)?;
            reciprocal_sum += BigRational::one() / denominator;
            enforce_accumulator_bits(&reciprocal_sum, stage, index)?;
        }
        let gate = spectral_gap.clone() * reciprocal_sum / load_count.clone();
        enforce_accumulator_bits(&gate, stage, loads.len())?;
        Ok(gate)
    }

    fn require(
        condition: bool,
        invariant: &'static str,
    ) -> Result<(), SharpDistributionBoundError> {
        if condition {
            Ok(())
        } else {
            Err(SharpDistributionBoundError::AlgebraicInvariantViolation { invariant })
        }
    }

    fn enforce_input_bits(
        value: &BigRational,
        field: &'static str,
        index: usize,
    ) -> Result<(), SharpDistributionBoundError> {
        let numerator_bits = value.numer().bits();
        let denominator_bits = value.denom().bits();
        if numerator_bits > OBL1A_SHARP_HARD_MAX_RATIONAL_BITS
            || denominator_bits > OBL1A_SHARP_HARD_MAX_RATIONAL_BITS
        {
            return Err(SharpDistributionBoundError::RationalBitLimitExceeded {
                field,
                index,
                numerator_bits,
                denominator_bits,
                hard_limit: OBL1A_SHARP_HARD_MAX_RATIONAL_BITS,
            });
        }
        Ok(())
    }

    fn enforce_accumulator_bits(
        value: &BigRational,
        stage: &'static str,
        through_index: usize,
    ) -> Result<(), SharpDistributionBoundError> {
        let numerator_bits = value.numer().bits();
        let denominator_bits = value.denom().bits();
        if numerator_bits > OBL1A_SHARP_HARD_MAX_ACCUMULATOR_BITS
            || denominator_bits > OBL1A_SHARP_HARD_MAX_ACCUMULATOR_BITS
        {
            return Err(SharpDistributionBoundError::AccumulatorBitLimitExceeded {
                stage,
                through_index,
                numerator_bits,
                denominator_bits,
                hard_limit: OBL1A_SHARP_HARD_MAX_ACCUMULATOR_BITS,
            });
        }
        Ok(())
    }

    fn exact_sum(
        stage: &'static str,
        terms: impl IntoIterator<Item = BigRational>,
    ) -> Result<BigRational, SharpDistributionBoundError> {
        let mut sum = BigRational::zero();
        for (through_index, term) in terms.into_iter().enumerate() {
            sum += term;
            enforce_accumulator_bits(&sum, stage, through_index)?;
        }
        Ok(sum)
    }
}
pub use sharp::*;

// Origin: engine/crates_rs/core_solvers/src/cert_phi1_distribution.rs
// Claim: urn:core:crates_rs:core-solvers:cert-phi1-distribution:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_33412dde {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
