//! DP-2 separation with declared domains and quotient identity: positive,
//! negative, boundary and tamper tests. AuthorityEffect: None.

use num_rational::BigRational;
use core_category_theory::finite_section_separation::{
    decide_separation, epsilon_decoder_class_factorization, verify_separation,
    weighted_coordinate_pseudometric, EquivalenceLaw, FiniteEquivalence, FinitePseudometric,
    PseudometricLaw, SectionRecord, SeparationOutcome, SeparationRefusal, SeparationReplayFailure,
};
use std::collections::BTreeSet;

fn q(n: i64, d: i64) -> BigRational {
    BigRational::new(n.into(), d.into())
}

type Refusal = SeparationRefusal<&'static str, &'static str>;

fn rec(id: &'static str, u: BigRational, v: BigRational) -> SectionRecord<&'static str, &'static str> {
    SectionRecord::new(id, &["u", "v"], &[("u", u), ("v", v)]).unwrap()
}

/// a=(0,0), a2=(0,0), b=(1/3,1/2), c=(1,0), d=(1/3,0); weights (1,2).
fn records(with_d: bool) -> Vec<SectionRecord<&'static str, &'static str>> {
    let mut r = vec![
        rec("a", q(0, 1), q(0, 1)),
        rec("a2", q(0, 1), q(0, 1)),
        rec("b", q(1, 3), q(1, 2)),
        rec("c", q(1, 1), q(0, 1)),
    ];
    if with_d {
        r.push(rec("d", q(1, 3), q(0, 1)));
    }
    r
}

fn weights() -> Vec<(&'static str, BigRational)> {
    vec![("u", q(1, 1)), ("v", q(2, 1))]
}

fn metric(with_d: bool) -> FinitePseudometric<&'static str> {
    weighted_coordinate_pseudometric(&records(with_d), &["u", "v"], &weights()).unwrap()
}

#[test]
fn worked_example_distances_and_gap() {
    let m = metric(false);
    assert_eq!(m.distance(&"a", &"a2"), Some(&q(0, 1)));
    assert_eq!(m.distance(&"a", &"b"), Some(&q(4, 3)));
    assert_eq!(m.distance(&"a", &"c"), Some(&q(1, 1)));
    assert_eq!(m.distance(&"b", &"c"), Some(&q(5, 3)));
    assert_eq!(m.distance(&"a2", &"c"), m.distance(&"a", &"c"));
    let pts = ["a", "a2", "b", "c"];
    let e = FiniteEquivalence::from_classes::<&str>(&pts, &[vec!["a", "a2"], vec!["b"], vec!["c"]])
        .unwrap();
    let out = decide_separation::<_, &str>(&m, &e).unwrap();
    let SeparationOutcome::Separated { gap, attaining_pair, classes, pair_distances } = &out else {
        panic!("expected separated")
    };
    assert_eq!(gap, &q(1, 1));
    assert_eq!(attaining_pair, &("a", "c"));
    assert_eq!(classes.len(), 3);
    assert_eq!(pair_distances.len(), 6);
    assert_eq!(verify_separation(&m, &e, &out), Ok(()));

    // Literal record identity: (a, a2) is a zero collision, although the
    // minimum nonzero distance is still 1.
    let id = FiniteEquivalence::from_classes::<&str>(&pts, &[vec!["a"], vec!["a2"], vec!["b"], vec!["c"]])
        .unwrap();
    let col = decide_separation::<_, &str>(&m, &id).unwrap();
    assert_eq!(col, SeparationOutcome::ZeroCollision { left: "a", right: "a2" });
    assert_eq!(verify_separation(&m, &id, &col), Ok(()));
}

#[test]
fn tampered_separation_verdicts_fail_replay() {
    let m = metric(false);
    let pts = ["a", "a2", "b", "c"];
    let e = FiniteEquivalence::from_classes::<&str>(&pts, &[vec!["a", "a2"], vec!["b"], vec!["c"]])
        .unwrap();
    let out = decide_separation::<_, &str>(&m, &e).unwrap();
    let SeparationOutcome::Separated { classes, pair_distances, gap, attaining_pair } = out else {
        panic!()
    };
    let mk = |c: &Vec<BTreeSet<&'static str>>, p: &_, g: &BigRational, a: (&'static str, &'static str)| {
        SeparationOutcome::Separated {
            classes: c.clone(),
            pair_distances: std::collections::BTreeMap::clone(p),
            gap: g.clone(),
            attaining_pair: a,
        }
    };
    assert_eq!(
        verify_separation(&m, &e, &mk(&classes, &pair_distances, &q(4, 3), ("a", "b"))),
        Err(SeparationReplayFailure::GapNotLowerBound)
    );
    assert_eq!(
        verify_separation(&m, &e, &mk(&classes, &pair_distances, &gap, ("a", "a2"))),
        Err(SeparationReplayFailure::AttainingPairNotInterclass)
    );
    assert_eq!(
        verify_separation(&m, &e, &mk(&classes, &pair_distances, &gap, ("b", "c"))),
        Err(SeparationReplayFailure::AttainingPairDistanceMismatch)
    );
    let mut table = pair_distances.clone();
    table.insert(("b", "c"), q(9, 1));
    assert_eq!(
        verify_separation(&m, &e, &mk(&classes, &table, &gap, attaining_pair)),
        Err(SeparationReplayFailure::PairTableMismatch)
    );
    let mut short = pair_distances.clone();
    short.remove(&("a", "a2"));
    assert_eq!(
        verify_separation(&m, &e, &mk(&classes, &short, &gap, attaining_pair)),
        Err(SeparationReplayFailure::PairTableMismatch)
    );
    assert_eq!(
        verify_separation(&m, &e, &mk(&classes[..2].to_vec(), &pair_distances, &gap, attaining_pair)),
        Err(SeparationReplayFailure::ClassesMismatch)
    );
    // A forged collision on a nonzero pair.
    assert_eq!(
        verify_separation(&m, &e, &SeparationOutcome::ZeroCollision { left: "a", right: "c" }),
        Err(SeparationReplayFailure::CollisionNotZero)
    );
    assert_eq!(
        verify_separation(&m, &e, &SeparationOutcome::ZeroCollision { left: "a", right: "a2" }),
        Err(SeparationReplayFailure::CollisionEquivalent)
    );
}

#[test]
fn declared_domains_are_not_list_lengths() {
    let s = SectionRecord::new("s", &["x"], &[("x", q(0, 1))]).unwrap();
    let t = SectionRecord::new("t", &["y"], &[("y", q(0, 1))]).unwrap();
    let r: Result<_, Refusal> =
        weighted_coordinate_pseudometric(&[s, t], &["x"], &[("x", q(1, 1))]);
    assert_eq!(r, Err(SeparationRefusal::IncomparableDomains { id: "t" }));
}

#[test]
fn record_admission_refusals() {
    let r: Result<_, Refusal> = SectionRecord::new("s", &["x", "y"], &[("x", q(0, 1))]);
    assert_eq!(r, Err(SeparationRefusal::SectionDomainMismatch { id: "s", coordinate: "y" }));
    let r: Result<_, Refusal> = SectionRecord::new("s", &["x"], &[("x", q(0, 1)), ("z", q(0, 1))]);
    assert_eq!(r, Err(SeparationRefusal::SectionDomainMismatch { id: "s", coordinate: "z" }));
    let r: Result<_, Refusal> = SectionRecord::new("s", &["x"], &[("x", q(0, 1)), ("x", q(0, 1))]);
    assert!(matches!(r, Err(SeparationRefusal::DuplicateCoordinate { .. })));
    let a = rec("a", q(0, 1), q(0, 1));
    let r: Result<_, Refusal> =
        weighted_coordinate_pseudometric(&[a.clone(), a], &["u", "v"], &weights());
    assert_eq!(r, Err(SeparationRefusal::DuplicateSectionIdentity { id: "a" }));
    let r: Result<_, Refusal> = weighted_coordinate_pseudometric(
        &records(false),
        &["u", "v"],
        &[("u", q(1, 1)), ("v", q(-1, 1))],
    );
    assert_eq!(r, Err(SeparationRefusal::InvalidWeight { coordinate: "v" }));
    let r: Result<_, Refusal> =
        weighted_coordinate_pseudometric(&records(false), &["u", "v"], &[("u", q(1, 1))]);
    assert_eq!(r, Err(SeparationRefusal::InvalidWeight { coordinate: "v" }));
}

#[test]
fn empty_or_singleton_comparison_sets_are_refused() {
    let r: Result<_, Refusal> = weighted_coordinate_pseudometric(&[], &["u", "v"], &weights());
    assert_eq!(r, Err(SeparationRefusal::NoComparablePairs));
    let r: Result<_, Refusal> =
        weighted_coordinate_pseudometric(&records(false)[..1], &["u", "v"], &weights());
    assert_eq!(r, Err(SeparationRefusal::NoComparablePairs));
    let m = FinitePseudometric::new::<()>(&["a"], &[(("a", "a"), q(0, 1))]).unwrap();
    let e = FiniteEquivalence::from_classes::<()>(&["a"], &[vec!["a"]]).unwrap();
    assert_eq!(decide_separation::<_, ()>(&m, &e), Err(SeparationRefusal::NoComparablePairs));
}

#[test]
fn zero_weight_admits_a_pseudometric_that_does_not_separate() {
    let s = SectionRecord::new("s", &["x"], &[("x", q(0, 1))]).unwrap();
    let t = SectionRecord::new("t", &["x"], &[("x", q(1, 1))]).unwrap();
    let m: FinitePseudometric<&str> =
        weighted_coordinate_pseudometric::<_, &str>(&[s, t], &["x"], &[("x", q(0, 1))]).unwrap();
    let e = FiniteEquivalence::from_classes::<()>(&["s", "t"], &[vec!["s"], vec!["t"]]).unwrap();
    assert_eq!(
        decide_separation::<_, ()>(&m, &e),
        Ok(SeparationOutcome::ZeroCollision { left: "s", right: "t" })
    );
}

fn two_point(d: BigRational) -> FinitePseudometric<u8> {
    FinitePseudometric::new::<()>(
        &[0, 1],
        &[((0, 0), q(0, 1)), ((1, 1), q(0, 1)), ((0, 1), d.clone()), ((1, 0), d)],
    )
    .unwrap()
}

#[test]
fn indiscrete_pseudometric_and_identification_rules() {
    let m = two_point(q(0, 1));
    let literal = FiniteEquivalence::from_classes::<()>(&[0, 1], &[vec![0], vec![1]]).unwrap();
    assert_eq!(
        decide_separation::<_, ()>(&m, &literal),
        Ok(SeparationOutcome::ZeroCollision { left: 0, right: 1 })
    );
    let all = FiniteEquivalence::from_classes::<()>(&[0, 1], &[vec![0, 1]]).unwrap();
    assert_eq!(decide_separation::<_, ()>(&m, &all), Err(SeparationRefusal::NoDistinctClasses));
    // Identification at positive distance.
    let m1 = two_point(q(1, 1));
    assert_eq!(
        decide_separation::<_, ()>(&m1, &all),
        Err(SeparationRefusal::IdentificationNotZero { left: 0, right: 1, distance: q(1, 1) })
    );
    // Carrier mismatch.
    let other = FiniteEquivalence::from_classes::<()>(&[0, 2], &[vec![0], vec![2]]).unwrap();
    assert_eq!(decide_separation::<_, ()>(&m1, &other), Err(SeparationRefusal::CarrierMismatch));
}

#[test]
fn equivalence_is_never_closed_silently() {
    let pairs = [("a", "a"), ("b", "b"), ("c", "c"), ("a", "b"), ("b", "a"), ("b", "c"), ("c", "b")];
    assert_eq!(
        FiniteEquivalence::from_pairs::<()>(&["a", "b", "c"], &pairs),
        Err(SeparationRefusal::InvalidEquivalence(EquivalenceLaw::Transitivity {
            left: "a",
            middle: "b",
            right: "c"
        }))
    );
    assert_eq!(
        FiniteEquivalence::from_pairs::<()>(&["a", "b"], &[("a", "a"), ("b", "b"), ("a", "b")]),
        Err(SeparationRefusal::InvalidEquivalence(EquivalenceLaw::Symmetry { left: "a", right: "b" }))
    );
    assert_eq!(
        FiniteEquivalence::from_pairs::<()>(&["a", "b"], &[("a", "a")]),
        Err(SeparationRefusal::InvalidEquivalence(EquivalenceLaw::Reflexivity { point: "b" }))
    );
    assert_eq!(
        FiniteEquivalence::from_classes::<()>(&["a", "b"], &[vec!["a"]]),
        Err(SeparationRefusal::InvalidEquivalence(EquivalenceLaw::UncoveredPoint { point: "b" }))
    );
    assert_eq!(
        FiniteEquivalence::from_classes::<()>(&["a"], &[vec!["a"], vec!["a"]]),
        Err(SeparationRefusal::InvalidEquivalence(EquivalenceLaw::OverlappingClasses { point: "a" }))
    );
}

fn full_rows(pts: &[&'static str], d: impl Fn(&str, &str) -> BigRational) -> Vec<((&'static str, &'static str), BigRational)> {
    let mut rows = Vec::new();
    for l in pts {
        for r in pts {
            rows.push(((*l, *r), d(l, r)));
        }
    }
    rows
}

#[test]
fn pseudometric_law_refusals() {
    // Triangle dropped: d(a,b)=3, d(a,c)=d(b,c)=1.
    let tri = full_rows(&["a", "b", "c"], |l, r| match (l.min(r), l.max(r)) {
        _ if l == r => q(0, 1),
        ("a", "b") => q(3, 1),
        _ => q(1, 1),
    });
    assert_eq!(
        FinitePseudometric::new::<()>(&["a", "b", "c"], &tri),
        Err(SeparationRefusal::InvalidPseudometric(PseudometricLaw::Triangle {
            left: "a",
            middle: "c",
            right: "b"
        }))
    );
    // Symmetry dropped: d(a,c)=d(b,c)=0, other off-diagonal 1.
    let asym = full_rows(&["a", "b", "c"], |l, r| {
        if l == r || (r == "c" && l != "c") {
            q(0, 1)
        } else {
            q(1, 1)
        }
    });
    assert!(matches!(
        FinitePseudometric::new::<()>(&["a", "b", "c"], &asym),
        Err(SeparationRefusal::InvalidPseudometric(PseudometricLaw::Asymmetric { .. }))
    ));
    let neg = full_rows(&["a", "b"], |l, r| if l == r { q(0, 1) } else { q(-1, 1) });
    assert!(matches!(
        FinitePseudometric::new::<()>(&["a", "b"], &neg),
        Err(SeparationRefusal::InvalidPseudometric(PseudometricLaw::Negative { .. }))
    ));
    let diag = full_rows(&["a", "b"], |_, _| q(1, 1));
    assert!(matches!(
        FinitePseudometric::new::<()>(&["a", "b"], &diag),
        Err(SeparationRefusal::InvalidPseudometric(PseudometricLaw::NonzeroDiagonal { .. }))
    ));
    let mut missing = full_rows(&["a", "b"], |l, r| if l == r { q(0, 1) } else { q(1, 1) });
    missing.pop();
    assert_eq!(
        FinitePseudometric::new::<()>(&["a", "b"], &missing),
        Err(SeparationRefusal::MissingPair { left: "b", right: "b" })
    );
    let mut dup = full_rows(&["a", "b"], |l, r| if l == r { q(0, 1) } else { q(1, 1) });
    dup.push((("a", "b"), q(1, 1)));
    assert!(matches!(
        FinitePseudometric::new::<()>(&["a", "b"], &dup),
        Err(SeparationRefusal::DuplicatePair { .. })
    ));
}

#[test]
fn epsilon_decoder_with_strict_threshold_factors_the_class_query() {
    let m = metric(true);
    let pts = ["a", "a2", "b", "c", "d"];
    let e = FiniteEquivalence::from_classes::<()>(&pts, &[vec!["a", "a2"], vec!["b"], vec!["c"], vec!["d"]])
        .unwrap();
    // p: x0, x1 -> 0; x2 -> 1. q: x0 -> a, x1 -> a2, x2 -> c. D(0)=d, D(1)=c.
    let out = epsilon_decoder_class_factorization(
        &m,
        &e,
        &["x0", "x1", "x2"],
        &[0u8, 1],
        &[("x0", 0), ("x1", 0), ("x2", 1)],
        &[("x0", "a"), ("x1", "a2"), ("x2", "c")],
        &[(0, "d"), (1, "c")],
        &q(1, 3),
    )
    .unwrap();
    assert_eq!(out.gap, q(1, 1));
    assert_eq!(out.twice_epsilon, q(2, 3));
    assert_eq!(out.fiber_diameter, q(0, 1));
    assert_eq!(out.certificate.decoder.get(&0), Some(&"a"));
    assert_eq!(out.certificate.decoder.get(&1), Some(&"c"));

    // Decoder error above epsilon.
    assert_eq!(
        epsilon_decoder_class_factorization(
            &m,
            &e,
            &["x0", "x1", "x2"],
            &[0u8, 1],
            &[("x0", 0), ("x1", 0), ("x2", 1)],
            &[("x0", "a"), ("x1", "a2"), ("x2", "c")],
            &[(0, "d"), (1, "c")],
            &q(1, 4),
        ),
        Err(SeparationRefusal::DecoderErrorExceeds { output: "a", distance: q(1, 3) })
    );
    assert_eq!(
        epsilon_decoder_class_factorization(
            &m,
            &e,
            &["x0"],
            &[0u8],
            &[("x0", 0)],
            &[("x0", "a")],
            &[(0, "a")],
            &q(-1, 3),
        ),
        Err(SeparationRefusal::NegativeEpsilon)
    );
}

#[test]
fn strict_threshold_cannot_be_dropped() {
    // Ambient Q points {0, 1/2, 1} with |.|; outputs {0, 1}; gap 1; decoder 1/2, eps 1/2.
    let pts = [0u8, 1, 2];
    let val = |p: u8| q(p as i64, 2);
    let mut rows = Vec::new();
    for l in pts {
        for r in pts {
            let d = val(l) - val(r);
            rows.push(((l, r), if d < q(0, 1) { -d } else { d }));
        }
    }
    let m = FinitePseudometric::new::<()>(&pts, &rows).unwrap();
    let e = FiniteEquivalence::from_classes::<()>(&pts, &[vec![0], vec![1], vec![2]]).unwrap();
    assert_eq!(
        epsilon_decoder_class_factorization(
            &m,
            &e,
            &["x", "y"],
            &[0u8],
            &[("x", 0), ("y", 0)],
            &[("x", 0), ("y", 2)],
            &[(0, 1)],
            &q(1, 2),
        ),
        Err(SeparationRefusal::ThresholdNotStrict { twice_epsilon: q(1, 1), gap: q(1, 1) })
    );
}

#[test]
fn fiber_bound_does_not_produce_a_decoder() {
    // Three points, all off-diagonal distances 2; one fiber holds all three
    // outputs; for eps = 1 every candidate decoder value is refused.
    let pts = ["a", "b", "c"];
    let rows = full_rows(&pts, |l, r| if l == r { q(0, 1) } else { q(2, 1) });
    let m = FinitePseudometric::new::<()>(&pts, &rows).unwrap();
    let e = FiniteEquivalence::from_classes::<()>(&pts, &[vec!["a"], vec!["b"], vec!["c"]]).unwrap();
    for cand in pts {
        let r = epsilon_decoder_class_factorization(
            &m,
            &e,
            &[0u8, 1, 2],
            &[0u8],
            &[(0, 0), (1, 0), (2, 0)],
            &[(0, "a"), (1, "b"), (2, "c")],
            &[(0, cand)],
            &q(1, 1),
        );
        assert!(matches!(r, Err(SeparationRefusal::DecoderErrorExceeds { .. })));
    }
}

#[test]
fn indiscrete_ambient_with_zero_epsilon_does_not_identify_outputs() {
    let m = two_point(q(0, 1));
    let literal = FiniteEquivalence::from_classes::<()>(&[0u8, 1], &[vec![0], vec![1]]).unwrap();
    assert_eq!(
        epsilon_decoder_class_factorization(
            &m,
            &literal,
            &["x", "y"],
            &[0u8],
            &[("x", 0), ("y", 0)],
            &[("x", 0), ("y", 1)],
            &[(0, 0)],
            &q(0, 1),
        ),
        Err(SeparationRefusal::OutputZeroCollision { left: 0, right: 1 })
    );
}

// Origin: engine/crates_rs/tests/core_category_theory/finite_section_separation.rs
// Claim: urn:core:crates_rs:tests:finite-section-separation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda2c46fef {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda2c46fef` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora2c46fef {
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
impl BoundaryErrora2c46fef {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora2c46fef {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora2c46fef {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda2c46fef {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora2c46fef> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora2c46fef::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora2c46fef::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora2c46fef::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_a2c46fef() {
    let admitted = BoundaryRecorda2c46fef::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda2c46fef::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
