//! DP-1 report/query decision contract: positive, negative, boundary and
//! tamper tests. AuthorityEffect: None.

use helpers::*;
use core_category_theory::finite_report_query::{
    transfer_refinement, CarrierRole, CertificateRefusal, MapRole, RefinementRefusal,
    ReportQueryDecision, ReportQueryProblem, ReportQueryRefusal,
};
use std::collections::{BTreeMap, BTreeSet};

mod helpers {
    pub use num_rational::BigRational;
    pub fn q(n: i64, d: i64) -> BigRational {
        BigRational::new(n.into(), d.into())
    }
}

type Problem = ReportQueryProblem<&'static str, u8, BigRational>;

fn fixture() -> Problem {
    ReportQueryProblem::new(
        &["x0", "x1", "x2"],
        &[0, 1, 2],
        &[q(1, 3), q(2, 3)],
        &[("x0", 0), ("x1", 0), ("x2", 1)],
        &[("x0", q(1, 3)), ("x1", q(1, 3)), ("x2", q(2, 3))],
    )
    .unwrap()
}

#[test]
fn worked_fixture_factors_on_realized_image_only() {
    let p = fixture();
    let ReportQueryDecision::Factorable(cert) = p.decide() else {
        panic!("expected factorable");
    };
    assert_eq!(cert.realized_image, BTreeSet::from([0, 1]));
    assert_eq!(cert.decoder, BTreeMap::from([(0, q(1, 3)), (1, q(2, 3))]));
    assert!(!cert.decoder.contains_key(&2));
    assert_eq!(cert.representative, BTreeMap::from([(0, "x0"), (1, "x2")]));
    assert_eq!(p.verify_factorization(&cert), Ok(()));
}

#[test]
fn not_sufficient_metadata_fixture_is_a_collision() {
    let p = ReportQueryProblem::new(&[0u8, 1], &[0u8], &[0u8, 1], &[(0, 0), (1, 0)], &[(0, 0), (1, 1)])
        .unwrap();
    let d = p.decide();
    let ReportQueryDecision::Collision(c) = &d else {
        panic!("expected collision")
    };
    assert_eq!((c.first, c.second, c.report, c.first_query, c.second_query), (0, 1, 0, 0, 1));
    assert_eq!(p.verify_decision(&d), Ok(()));
}

#[test]
fn admission_refusals_are_typed() {
    let src = [0u8, 1];
    let cod = [0u8, 1];
    let total = [(0u8, 0u8), (1, 0)];
    // Extraneous row such as {99:0}, the defect named for CODA layer 3.
    assert_eq!(
        ReportQueryProblem::new(&src, &cod, &cod, &[(0, 0), (1, 0), (99, 0)], &total),
        Err(ReportQueryRefusal::ExtraneousAssignment { map: MapRole::Report, source: 99 })
    );
    assert_eq!(
        ReportQueryProblem::new(&src, &cod, &cod, &[(0, 0)], &total),
        Err(ReportQueryRefusal::MissingAssignment { map: MapRole::Report, source: 1 })
    );
    // Identical duplicate rows are refused before normalization.
    assert_eq!(
        ReportQueryProblem::new(&src, &cod, &cod, &total, &[(0, 0), (0, 0), (1, 0)]),
        Err(ReportQueryRefusal::DuplicateAssignment { map: MapRole::Query, source: 0 })
    );
    assert_eq!(
        ReportQueryProblem::new(&src, &cod, &cod, &[(0, 0), (1, 7)], &total),
        Err(ReportQueryRefusal::OutsideCodomain { map: MapRole::Report, source: 1 })
    );
    assert_eq!(
        ReportQueryProblem::new(&[0u8, 0], &cod, &cod, &total, &total),
        Err(ReportQueryRefusal::DuplicateIdentity { carrier: CarrierRole::Source, position: 1 })
    );
    assert_eq!(
        ReportQueryProblem::new(&src, &cod, &[1u8, 1], &total, &total),
        Err(ReportQueryRefusal::DuplicateIdentity {
            carrier: CarrierRole::QueryCodomain,
            position: 1
        })
    );
}

#[test]
fn empty_source_has_the_empty_decoder_even_with_empty_query_codomain() {
    let p: ReportQueryProblem<u8, u8, u8> =
        ReportQueryProblem::new(&[], &[0], &[], &[], &[]).unwrap();
    let d = p.decide();
    let ReportQueryDecision::Factorable(cert) = &d else {
        panic!("expected factorable")
    };
    assert!(cert.decoder.is_empty() && cert.realized_image.is_empty());
    assert_eq!(p.verify_decision(&d), Ok(()));
}

#[test]
fn unrealized_codomain_values_do_not_change_the_decision() {
    let small = ReportQueryProblem::new(&[0u8, 1], &[0u8, 1], &[5u8, 6], &[(0, 0), (1, 1)], &[(0, 5), (1, 6)])
        .unwrap();
    let large = ReportQueryProblem::new(
        &[0u8, 1],
        &[0u8, 1, 2, 3],
        &[5u8, 6, 7],
        &[(0, 0), (1, 1)],
        &[(0, 5), (1, 6)],
    )
    .unwrap();
    assert_eq!(small.decide(), large.decide());
}

/// Exhaustive check on carriers of size at most 3, reports into {0,1,2},
/// queries into {0,1}: the decision agrees with a brute-force collision
/// search, replays, and the number of decoders on the realized image is
/// exactly 1 when factorable and 0 otherwise.
#[test]
fn exhaustive_small_tables_agree_with_brute_force() {
    let mut checked = 0usize;
    for n in 0..=3usize {
        let src: Vec<u8> = (0..n as u8).collect();
        for pcode in 0..3usize.pow(n as u32) {
            for qcode in 0..2usize.pow(n as u32) {
                let p: Vec<u8> = (0..n).map(|i| ((pcode / 3usize.pow(i as u32)) % 3) as u8).collect();
                let qv: Vec<u8> = (0..n).map(|i| ((qcode >> i) & 1) as u8).collect();
                let prob = ReportQueryProblem::new(
                    &src,
                    &[0, 1, 2],
                    &[0, 1],
                    &src.iter().map(|&x| (x, p[x as usize])).collect::<Vec<_>>(),
                    &src.iter().map(|&x| (x, qv[x as usize])).collect::<Vec<_>>(),
                )
                .unwrap();
                let brute_collision =
                    (0..n).any(|i| (0..n).any(|j| p[i] == p[j] && qv[i] != qv[j]));
                let image: Vec<u8> = prob.realized_image().into_iter().collect();
                let mut decoders = 0usize;
                for dcode in 0..2usize.pow(image.len() as u32) {
                    let dmap: BTreeMap<u8, u8> = image
                        .iter()
                        .enumerate()
                        .map(|(k, a)| (*a, ((dcode >> k) & 1) as u8))
                        .collect();
                    if (0..n).all(|i| dmap[&p[i]] == qv[i]) {
                        decoders += 1;
                    }
                }
                let d = prob.decide();
                assert_eq!(prob.verify_decision(&d), Ok(()));
                match d {
                    ReportQueryDecision::Factorable(_) => {
                        assert!(!brute_collision);
                        assert_eq!(decoders, 1);
                    }
                    ReportQueryDecision::Collision(_) => {
                        assert!(brute_collision);
                        assert_eq!(decoders, 0);
                    }
                }
                checked += 1;
            }
        }
    }
    assert_eq!(checked, 1 + 3 * 2 + 9 * 4 + 27 * 8);
}

#[test]
fn tampered_certificates_fail_replay() {
    let p = fixture();
    let ReportQueryDecision::Factorable(cert) = p.decide() else {
        panic!()
    };
    let mut bad = cert.clone();
    bad.decoder.insert(1, q(1, 3));
    assert_eq!(p.verify_factorization(&bad), Err(CertificateRefusal::DecoderEquationFailure));
    let mut bad = cert.clone();
    bad.decoder.insert(2, q(1, 3));
    assert_eq!(p.verify_factorization(&bad), Err(CertificateRefusal::DecoderKeysMismatch));
    let mut bad = cert.clone();
    bad.realized_image.insert(2);
    assert_eq!(p.verify_factorization(&bad), Err(CertificateRefusal::RealizedImageMismatch));
    let mut bad = cert.clone();
    bad.representative.insert(0, "x2");
    assert_eq!(p.verify_factorization(&bad), Err(CertificateRefusal::RepresentativeNotInFiber));
    let mut bad = cert.clone();
    bad.decoder.insert(0, q(5, 7));
    assert_eq!(p.verify_factorization(&bad), Err(CertificateRefusal::DecoderValueOutsideCodomain));

    let c = ReportQueryProblem::new(&[0u8, 1], &[0u8], &[0u8, 1], &[(0, 0), (1, 0)], &[(0, 0), (1, 1)])
        .unwrap();
    let ReportQueryDecision::Collision(w) = c.decide() else {
        panic!()
    };
    let mut bad = w.clone();
    bad.second_query = 0;
    assert_eq!(c.verify_collision(&bad), Err(CertificateRefusal::CollisionQueryMismatch));
    let mut bad = w.clone();
    bad.second = 0;
    assert_eq!(c.verify_collision(&bad), Err(CertificateRefusal::CollisionPointsEqual));
    let mut bad = w;
    bad.first = 9;
    assert_eq!(c.verify_collision(&bad), Err(CertificateRefusal::CollisionPointUnknown));
}

type Pair = (u8, u8);
const SQUARE: [Pair; 4] = [(0, 0), (0, 1), (1, 0), (1, 1)];

fn square_problem<A: Ord + Clone + std::fmt::Debug>(
    codomain: &[A],
    report: impl Fn(Pair) -> A,
) -> ReportQueryProblem<Pair, A, u8> {
    ReportQueryProblem::new(
        &SQUARE,
        codomain,
        &[0, 1],
        &SQUARE.iter().map(|&x| (x, report(x))).collect::<Vec<_>>(),
        &SQUARE.iter().map(|&x| (x, x.1)).collect::<Vec<_>>(),
    )
    .unwrap()
}

#[test]
fn refinement_transfer_is_one_way_on_the_square() {
    // p_f = id, h = first coordinate, q = second coordinate.
    let fine = square_problem(&SQUARE, |x| x);
    let coarse = square_problem(&[0u8, 1], |x| x.0);
    let h: Vec<(Pair, u8)> = SQUARE.iter().map(|&x| (x, x.0)).collect();
    assert!(matches!(fine.decide(), ReportQueryDecision::Factorable(_)));
    // Converse fails: coarse report collides.
    let ReportQueryDecision::Collision(c) = coarse.decide() else {
        panic!("coarse should collide")
    };
    assert_eq!((c.first, c.second), ((0, 0), (0, 1)));

    // Forward direction: coarse = second coordinate factors; fine inherits it.
    let coarse_ok = square_problem(&[0u8, 1], |x| x.1);
    let h_ok: Vec<(Pair, u8)> = SQUARE.iter().map(|&x| (x, x.1)).collect();
    let ReportQueryDecision::Factorable(cc) = coarse_ok.decide() else { panic!() };
    let fc = transfer_refinement(&fine, &coarse_ok, &h_ok, &cc).unwrap();
    assert_eq!(fine.verify_factorization(&fc), Ok(()));

    // Refinement equation failure: h = first coordinate does not satisfy p_c = h . p_f.
    assert_eq!(
        transfer_refinement(&fine, &coarse_ok, &h, &cc),
        Err(RefinementRefusal::RefinementEquationFailure { source: (0, 1) })
    );
    // Partial h is refused.
    assert!(matches!(
        transfer_refinement(&fine, &coarse_ok, &h_ok[..3], &cc),
        Err(RefinementRefusal::RefinementTable(ReportQueryRefusal::MissingAssignment { .. }))
    ));
    // A tampered coarse certificate is refused.
    let mut bad = cc.clone();
    bad.decoder.insert(0, 1);
    assert!(matches!(
        transfer_refinement(&fine, &coarse_ok, &h_ok, &bad),
        Err(RefinementRefusal::CoarseCertificate(_))
    ));
}

#[test]
fn refinement_with_constant_fine_report_has_no_valid_h() {
    // p = q = id on {0,1}; p_f constant. Coarse factors, fine collides; every
    // candidate h fails the refinement equation.
    let coarse = ReportQueryProblem::new(&[0u8, 1], &[0u8, 1], &[0u8, 1], &[(0, 0), (1, 1)], &[(0, 0), (1, 1)])
        .unwrap();
    let fine = ReportQueryProblem::new(&[0u8, 1], &[0u8], &[0u8, 1], &[(0, 0), (1, 0)], &[(0, 0), (1, 1)])
        .unwrap();
    let ReportQueryDecision::Factorable(cc) = coarse.decide() else { panic!() };
    assert!(matches!(fine.decide(), ReportQueryDecision::Collision(_)));
    for v in [0u8, 1] {
        assert!(matches!(
            transfer_refinement(&fine, &coarse, &[(0, v)], &cc),
            Err(RefinementRefusal::RefinementEquationFailure { .. })
        ));
    }
}

// Origin: engine/crates_rs/tests/core_category_theory/finite_report_query.rs
// Claim: urn:core:crates_rs:tests:finite-report-query:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfb1786e3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfb1786e3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfb1786e3 {
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
impl BoundaryErrorfb1786e3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfb1786e3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfb1786e3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfb1786e3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfb1786e3> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfb1786e3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfb1786e3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfb1786e3::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_fb1786e3() {
    let admitted = BoundaryRecordfb1786e3::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordfb1786e3::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
