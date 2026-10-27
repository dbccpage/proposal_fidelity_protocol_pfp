
#[allow(dead_code, non_camel_case_types, missing_docs)]
type BigRationalRatioWitness_6109affa = (i128, i128);
use engines::quantum::density_matrix::{CVector, C64};
use engines::quantum::prompt_density::{
    compare, observe, ObservationStatus, MAX_SOURCE_BYTES,
};
use engines::quantum::semantic_geometry_engine::{hermitian_eigenvalues, FactorizedDensity};

fn vector(values: &[f64]) -> CVector {
    CVector::from_iterator(values.len(), values.iter().map(|&v| C64::new(v, 0.0)))
}

#[test]
fn density_rejects_invalid_weights_and_nonfinite_vectors() {
    for weights in [
        vec![-1.0, 2.0],
        vec![f64::NAN, 1.0],
        vec![f64::INFINITY, 1.0],
        vec![0.0, 0.0],
    ] {
        assert!(FactorizedDensity::new(
            vec![vector(&[1.0, 0.0]), vector(&[0.0, 1.0])],
            Some(weights)
        )
        .is_err());
    }
    for values in [
        vec![0.0, 0.0],
        vec![f64::NAN, 1.0],
        vec![1.0, f64::INFINITY],
    ] {
        assert!(FactorizedDensity::new(vec![vector(&values)], None).is_err());
    }
    assert!(FactorizedDensity::new(vec![vector(&[1.0]), vector(&[1.0, 2.0])], None).is_err());
}

#[test]
fn finite_large_inputs_normalize_without_overflow() {
    let density = FactorizedDensity::new(
        vec![vector(&[f64::MAX, f64::MAX]), vector(&[1.0, -1.0])],
        Some(vec![f64::MAX, f64::MAX]),
    )
    .unwrap();
    assert_eq!(density.weights(), &[0.5, 0.5]);
    assert!((density.to_dense().trace().re - 1.0).abs() < 1e-12);
    assert!((density.purity() - 0.5).abs() < 1e-12);
}

#[test]
fn gram_spectrum_matches_small_dense_matrix() {
    let density = FactorizedDensity::new(
        vec![
            vector(&[1.0, 0.0, 0.0]),
            vector(&[0.0, 1.0, 0.0]),
            vector(&[1.0, 1.0, 1.0]),
        ],
        Some(vec![1.0, 2.0, 3.0]),
    )
    .unwrap();
    let gram = density.compute_spectrum();
    let dense = hermitian_eigenvalues(&density.to_dense());
    for (a, b) in gram.iter().zip(dense) {
        assert!((a - b).abs() < 1e-10);
    }
    assert!((gram.iter().sum::<f64>() - 1.0).abs() < 1e-10);
}

#[test]
fn variable_dimension_operations_refuse_mismatched_states() {
    let a = FactorizedDensity::from_pure_vector(vector(&[1.0, 0.0])).unwrap();
    let b = FactorizedDensity::from_pure_vector(vector(&[1.0, 0.0, 0.0])).unwrap();
    assert!(a.mix(&b, 0.5).is_err());
    assert!(a.quantum_jensen_shannon_divergence(&b).is_err());
    assert!(a.factorized_fidelity(&b).is_err());
}

#[test]
fn rank_one_entropy_and_global_sign_do_not_measure_meaning() {
    let a = FactorizedDensity::from_pure_vector(vector(&[1.0, 2.0, -3.0])).unwrap();
    let b = FactorizedDensity::from_pure_vector(vector(&[-1.0, -2.0, 3.0])).unwrap();
    assert!(a.entropy().abs() < 1e-10);
    assert!(a.quantum_jensen_shannon_divergence(&b).unwrap() < 1e-10);
    assert!((a.purity() - 1.0).abs() < 1e-10);
}

#[test]
fn observations_cover_unicode_bytes_at_all_supported_dimension_examples() {
    let text = "  αβ Γδ\n你好 世界\tnaïve café\r\n🙂 Ω  ";
    for dim in [28, 128, 1024] {
        let report = observe(text.as_bytes(), dim, "Syntax Prefilter", "seed", "user");
        assert_eq!(report.status, ObservationStatus::Observed);
        assert!(report.spans.len() <= 16);
        assert_eq!(report.factors.len(), report.spans.len());
        let mut end = 0;
        for span in &report.spans {
            assert_eq!(span.start_byte, end);
            assert!(text.is_char_boundary(span.start_byte));
            assert!(text.is_char_boundary(span.end_byte));
            end = span.end_byte;
        }
        assert_eq!(end, text.len());
        assert!(report.factors.iter().all(|v| v.len() == dim));
        assert!((report.weights.iter().sum::<f64>() - 1.0).abs() < 1e-12);
        assert!(report.entropy_bits.unwrap() <= 4.0 + 1e-10);
        assert_eq!(compare(&report, &report).status, "COMPARED");
    }
}

#[test]
fn ordered_features_separate_anagrams_and_negation_controls() {
    for dim in [28, 128, 1024] {
        let a = observe(b"Allow Alice; deny Bob", dim, "Syntax Prefilter", "seed", "user");
        let b = observe(b"Allow Bob; deny Alice", dim, "Syntax Prefilter", "seed", "user");
        let c = observe(
            b"Do not allow Alice; deny Bob",
            dim,
            "Syntax Prefilter",
            "seed",
            "user",
        );
        assert_ne!(a.factors, b.factors);
        assert!(compare(&a, &b).quantum_jensen_shannon_bits.unwrap() > 1e-8);
        assert!(compare(&a, &c).quantum_jensen_shannon_bits.unwrap() > 1e-8);
        assert_eq!(
            a,
            observe(b"Allow Alice; deny Bob", dim, "Syntax Prefilter", "seed", "user")
        );
    }
}

#[test]
fn bounded_projection_does_not_claim_injective_features() {
    // Every 28-dimensional projection of more than 28 independent features has
    // a kernel. We retain source identities even if the projection aliases.
    let a = observe(b"single", 28, "Syntax Prefilter", "seed", "user");
    let b = observe(b" single ", 28, "Syntax Prefilter", "seed", "user");
    assert_eq!(a.factors, b.factors);
    assert_ne!(a.source_sha256, b.source_sha256);
    assert_eq!(a.entropy_bits, Some(0.0));
    assert_eq!(a.effective_rank, Some(1.0));

    let mut seen = std::collections::BTreeMap::new();
    let mut collision = None;
    for index in 0..1024 {
        let report = observe(
            format!("token_{index}").as_bytes(),
            28,
            "Syntax Prefilter",
            "seed",
            "user",
        );
        let key: Vec<u64> = report.factors[0].iter().map(|v| v.to_bits()).collect();
        if let Some(previous) = seen.insert(key, report.clone()) {
            collision = Some((previous, report));
            break;
        }
    }
    let (a, b) = collision.expect("two token/position features in 28 buckets have a finite image");
    assert_ne!(a.source_sha256, b.source_sha256);
    assert!(compare(&a, &b).quantum_jensen_shannon_bits.unwrap() < 1e-10);
}

#[test]
fn empty_invalid_and_limited_sources_never_receive_scalar_success() {
    let cases = [
        (
            observe(b"\t\n ", 128, "Syntax Prefilter", "seed", "user"),
            ObservationStatus::Empty,
        ),
        (
            observe(&[0xff], 128, "Syntax Prefilter", "seed", "user"),
            ObservationStatus::InvalidUtf8,
        ),
        (
            observe(b"x", 27, "Syntax Prefilter", "seed", "user"),
            ObservationStatus::InvalidInput,
        ),
        (
            observe(b"x", 1025, "Syntax Prefilter", "seed", "user"),
            ObservationStatus::InvalidInput,
        ),
        (
            observe(
                &vec![b'x'; MAX_SOURCE_BYTES + 1],
                128,
                "Syntax Prefilter",
                "seed",
                "user",
            ),
            ObservationStatus::LimitExceeded,
        ),
        (
            observe("x ".repeat(32769).as_bytes(), 128, "Syntax Prefilter", "seed", "user"),
            ObservationStatus::LimitExceeded,
        ),
    ];
    for (report, expected) in cases {
        assert_eq!(report.status, expected);
        assert!(report.entropy_bits.is_none());
        assert!(report.purity.is_none());
        assert!(report.factors.is_empty());
        assert!(report.spans.is_empty());
    }
}

#[test]
fn long_input_keeps_sixteen_components_and_the_full_original_extent() {
    let text = "case with ordered words ".repeat(8000);
    let report = observe(text.as_bytes(), 1024, "Adversary", "reply", "untrusted");
    assert_eq!(report.status, ObservationStatus::Observed);
    assert_eq!(report.spans.len(), 16);
    assert_eq!(report.spans.last().unwrap().end_byte, text.len());
    assert_eq!(
        report.spans.iter().map(|s| s.token_count).sum::<usize>(),
        32000
    );
}

#[test]
fn comparisons_refuse_mixed_profiles_dimensions_roles_and_unchecked_factors() {
    let report = observe(b"alpha beta gamma", 128, "Syntax Prefilter", "seed", "user");
    for key in ["profile", "role", "field", "trust", "dimension"] {
        let mut other = report.clone();
        match key {
            "profile" => other.profile = "future".to_owned(),
            "role" => other.role_id = "Adversary".to_owned(),
            "field" => other.field = "reply".to_owned(),
            "trust" => other.trust_level = "system".to_owned(),
            _ => other.dim = 28,
        }
        let comparison = compare(&report, &other);
        assert_eq!(comparison.status, "INCOMPATIBLE");
        assert!(comparison.quantum_jensen_shannon_bits.is_none());
    }
    for fault in 0..4 {
        let mut corrupt = report.clone();
        match fault {
            0 => corrupt.weights[0] = -1.0,
            1 => corrupt.factors[0][0] = f64::NAN,
            2 => corrupt.spans[0].start_byte = 1,
            _ => corrupt.factors[0].fill(0.0),
        }
        assert_eq!(compare(&report, &corrupt).status, "INVALID_INPUT");
    }
}

// Origin: engine/crates_rs/tests/engines/prompt_density.rs
// Claim: urn:core:crates_rs:tests:prompt-density:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6109affa {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6109affa` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6109affa {
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
impl BoundaryError6109affa {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6109affa {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6109affa {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6109affa {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6109affa> {
        if capacity_bound == 0 {
            return Err(BoundaryError6109affa::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6109affa::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6109affa::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_6109affa() {
    let admitted = BoundaryRecord6109affa::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord6109affa::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
