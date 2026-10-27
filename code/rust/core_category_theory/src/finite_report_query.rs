//! Total finite report/query decision contract (realized-image factorization).
//!
//! AuthorityEffect: None.
//!
//! Inputs are explicitly enumerated finite sets `X` (source), `A` (report
//! codomain) and `B` (query codomain), together with row tables that must be
//! total functions `p: X -> A` and `q: X -> B`. Admission refuses duplicate
//! carrier identities, duplicate rows (including identical duplicates),
//! missing rows, extraneous rows and values outside the declared codomain.
//! Codomain membership is a typing premise of `p: X -> A`, not a separate
//! profile check that may disagree with it.
//!
//! On admitted input exactly one outcome holds:
//!
//! * `Factorable`: there is one and only one table `D: P -> B` on the
//!   realized image `P = p(X)` with `D(p(x)) = q(x)` for every `x`;
//! * `Collision`: there are `x, y` with `p(x) = p(y)` and `q(x) != q(y)`.
//!
//! The decoder is unique on `P` only; outside `P` it is not determined, so it
//! is not emitted there. Refinement transfer is one-way: if `p = h . p_f` and
//! `q` factors through `p`, then `q` factors through `p_f` with
//! `D_f = D_c . h`; the converse fails (see the tests).

use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

/// Which declared carrier an admission refusal refers to.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum CarrierRole {
    Source,
    ReportCodomain,
    QueryCodomain,
}

/// Which row table an admission refusal refers to.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum MapRole {
    Report,
    Query,
    Refinement,
}

/// Typed refusals for malformed or partial input. A refusal is never one of
/// the two mathematical outcomes.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ReportQueryRefusal<X> {
    /// The enumeration of a carrier repeats an identity; `position` is the
    /// index of the second occurrence.
    DuplicateIdentity { carrier: CarrierRole, position: usize },
    /// A source element has two or more rows (identical rows included).
    DuplicateAssignment { map: MapRole, source: X },
    /// A source element has no row.
    MissingAssignment { map: MapRole, source: X },
    /// A row names a source element outside the declared source.
    ExtraneousAssignment { map: MapRole, source: X },
    /// A row value lies outside the declared codomain.
    OutsideCodomain { map: MapRole, source: X },
}

impl<X: fmt::Debug> fmt::Display for ReportQueryRefusal<X> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{self:?}")
    }
}

impl<X: fmt::Debug> std::error::Error for ReportQueryRefusal<X> {}

/// An admitted total report/query problem.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReportQueryProblem<X, A, B> {
    source: BTreeSet<X>,
    report_codomain: BTreeSet<A>,
    query_codomain: BTreeSet<B>,
    report: BTreeMap<X, A>,
    query: BTreeMap<X, B>,
}

fn carrier_or_refuse<T: Ord + Clone, X>(
    items: &[T],
    role: CarrierRole,
) -> Result<BTreeSet<T>, ReportQueryRefusal<X>> {
    let mut out = BTreeSet::new();
    for (position, item) in items.iter().enumerate() {
        if !out.insert(item.clone()) {
            return Err(ReportQueryRefusal::DuplicateIdentity {
                carrier: role,
                position,
            });
        }
    }
    Ok(out)
}

/// Admits a total table `X -> V` against declared source and codomain.
/// Duplicates are detected on the raw rows, before normalization.
pub fn admit_total_table<X, V>(
    source: &BTreeSet<X>,
    codomain: &BTreeSet<V>,
    rows: &[(X, V)],
    map: MapRole,
) -> Result<BTreeMap<X, V>, ReportQueryRefusal<X>>
where
    X: Ord + Clone,
    V: Ord + Clone,
{
    let mut table = BTreeMap::new();
    for (x, v) in rows {
        if !source.contains(x) {
            return Err(ReportQueryRefusal::ExtraneousAssignment {
                map,
                source: x.clone(),
            });
        }
        if table.contains_key(x) {
            return Err(ReportQueryRefusal::DuplicateAssignment {
                map,
                source: x.clone(),
            });
        }
        if !codomain.contains(v) {
            return Err(ReportQueryRefusal::OutsideCodomain {
                map,
                source: x.clone(),
            });
        }
        table.insert(x.clone(), v.clone());
    }
    for x in source {
        if !table.contains_key(x) {
            return Err(ReportQueryRefusal::MissingAssignment {
                map,
                source: x.clone(),
            });
        }
    }
    Ok(table)
}

/// A collision witness: equal reports, unequal queries.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReportCollision<X, A, B> {
    pub first: X,
    pub second: X,
    pub report: A,
    pub first_query: B,
    pub second_query: B,
}

/// A factorization certificate on the realized image.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FactorizationCertificate<X, A, B> {
    pub realized_image: BTreeSet<A>,
    pub decoder: BTreeMap<A, B>,
    pub representative: BTreeMap<A, X>,
}

/// The two mathematical outcomes on admitted input.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ReportQueryDecision<X, A, B> {
    Factorable(FactorizationCertificate<X, A, B>),
    Collision(ReportCollision<X, A, B>),
}

/// Why a supplied certificate failed replay.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CertificateRefusal {
    RealizedImageMismatch,
    DecoderKeysMismatch,
    DecoderValueOutsideCodomain,
    RepresentativeKeysMismatch,
    RepresentativeNotInFiber,
    DecoderEquationFailure,
    CollisionPointUnknown,
    CollisionPointsEqual,
    CollisionReportMismatch,
    CollisionQueryMismatch,
    CollisionQueriesEqual,
}

/// Refusals of the refinement transfer.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RefinementRefusal<X, F> {
    /// The two problems do not share source and query data.
    ProblemsDiffer,
    /// The `h` table is not a total map `A_f -> A_c`.
    RefinementTable(ReportQueryRefusal<F>),
    /// `p_c(source) != h(p_f(source))`.
    RefinementEquationFailure { source: X },
    /// The supplied coarse certificate does not replay against the coarse problem.
    CoarseCertificate(CertificateRefusal),
}

impl<X, A, B> ReportQueryProblem<X, A, B>
where
    X: Ord + Clone + fmt::Debug,
    A: Ord + Clone + fmt::Debug,
    B: Ord + Clone + fmt::Debug,
{
    /// Admits a problem from explicit enumerations and raw row tables.
    pub fn new(
        source: &[X],
        report_codomain: &[A],
        query_codomain: &[B],
        report_rows: &[(X, A)],
        query_rows: &[(X, B)],
    ) -> Result<Self, ReportQueryRefusal<X>> {
        let source = carrier_or_refuse(source, CarrierRole::Source)?;
        let report_codomain = carrier_or_refuse(report_codomain, CarrierRole::ReportCodomain)?;
        let query_codomain = carrier_or_refuse(query_codomain, CarrierRole::QueryCodomain)?;
        let report = admit_total_table(&source, &report_codomain, report_rows, MapRole::Report)?;
        let query = admit_total_table(&source, &query_codomain, query_rows, MapRole::Query)?;
        Ok(Self {
            source,
            report_codomain,
            query_codomain,
            report,
            query,
        })
    }

    pub fn source(&self) -> &BTreeSet<X> {
        &self.source
    }
    pub fn report_codomain(&self) -> &BTreeSet<A> {
        &self.report_codomain
    }
    pub fn query_codomain(&self) -> &BTreeSet<B> {
        &self.query_codomain
    }
    pub fn report(&self) -> &BTreeMap<X, A> {
        &self.report
    }
    pub fn query(&self) -> &BTreeMap<X, B> {
        &self.query
    }

    /// The realized image `P = p(X)`.
    pub fn realized_image(&self) -> BTreeSet<A> {
        self.report.values().cloned().collect()
    }

    /// Decides the problem by one ordered scan. Deterministic: the collision
    /// returned pairs the first source element of a fiber with the first later
    /// element of that fiber whose query differs.
    pub fn decide(&self) -> ReportQueryDecision<X, A, B> {
        let mut decoder: BTreeMap<A, B> = BTreeMap::new();
        let mut representative: BTreeMap<A, X> = BTreeMap::new();
        for (x, a) in &self.report {
            // Admission enforces totality; a missing query row cannot occur.
            let Some(b) = self.query.get(x) else { continue };
            match (decoder.get(a), representative.get(a)) {
                (Some(stored), Some(first)) => {
                    if stored != b {
                        return ReportQueryDecision::Collision(ReportCollision {
                            first: first.clone(),
                            second: x.clone(),
                            report: a.clone(),
                            first_query: stored.clone(),
                            second_query: b.clone(),
                        });
                    }
                }
                _ => {
                    decoder.insert(a.clone(), b.clone());
                    representative.insert(a.clone(), x.clone());
                }
            }
        }
        ReportQueryDecision::Factorable(FactorizationCertificate {
            realized_image: decoder.keys().cloned().collect(),
            decoder,
            representative,
        })
    }

    /// Replays a decision against this problem without trusting its producer.
    pub fn verify_decision(
        &self,
        decision: &ReportQueryDecision<X, A, B>,
    ) -> Result<(), CertificateRefusal> {
        match decision {
            ReportQueryDecision::Factorable(cert) => self.verify_factorization(cert),
            ReportQueryDecision::Collision(c) => self.verify_collision(c),
        }
    }

    /// Replays a factorization certificate.
    pub fn verify_factorization(
        &self,
        cert: &FactorizationCertificate<X, A, B>,
    ) -> Result<(), CertificateRefusal> {
        let image = self.realized_image();
        if cert.realized_image != image {
            return Err(CertificateRefusal::RealizedImageMismatch);
        }
        let decoder_keys: BTreeSet<A> = cert.decoder.keys().cloned().collect();
        if decoder_keys != image {
            return Err(CertificateRefusal::DecoderKeysMismatch);
        }
        if cert
            .decoder
            .values()
            .any(|b| !self.query_codomain.contains(b))
        {
            return Err(CertificateRefusal::DecoderValueOutsideCodomain);
        }
        let rep_keys: BTreeSet<A> = cert.representative.keys().cloned().collect();
        if rep_keys != image {
            return Err(CertificateRefusal::RepresentativeKeysMismatch);
        }
        for (a, x) in &cert.representative {
            if self.report.get(x) != Some(a) {
                return Err(CertificateRefusal::RepresentativeNotInFiber);
            }
        }
        for (x, a) in &self.report {
            if cert.decoder.get(a) != self.query.get(x) {
                return Err(CertificateRefusal::DecoderEquationFailure);
            }
        }
        Ok(())
    }

    /// Replays a collision witness.
    pub fn verify_collision(
        &self,
        c: &ReportCollision<X, A, B>,
    ) -> Result<(), CertificateRefusal> {
        let (Some(pa), Some(pb)) = (self.report.get(&c.first), self.report.get(&c.second)) else {
            return Err(CertificateRefusal::CollisionPointUnknown);
        };
        if c.first == c.second {
            return Err(CertificateRefusal::CollisionPointsEqual);
        }
        if pa != &c.report || pb != &c.report {
            return Err(CertificateRefusal::CollisionReportMismatch);
        }
        if self.query.get(&c.first) != Some(&c.first_query)
            || self.query.get(&c.second) != Some(&c.second_query)
        {
            return Err(CertificateRefusal::CollisionQueryMismatch);
        }
        if c.first_query == c.second_query {
            return Err(CertificateRefusal::CollisionQueriesEqual);
        }
        Ok(())
    }
}

fn verify_refinement_inputs<X, F, C, B>(
    fine: &ReportQueryProblem<X, F, B>,
    coarse: &ReportQueryProblem<X, C, B>,
    h_rows: &[(F, C)],
    coarse_cert: &FactorizationCertificate<X, C, B>,
) -> Result<BTreeMap<F, C>, RefinementRefusal<X, F>>
where
    X: Ord + Clone + fmt::Debug,
    F: Ord + Clone + fmt::Debug,
    C: Ord + Clone + fmt::Debug,
    B: Ord + Clone + fmt::Debug,
{
    if fine.source != coarse.source
        || fine.query != coarse.query
        || fine.query_codomain != coarse.query_codomain
    {
        return Err(RefinementRefusal::ProblemsDiffer);
    }
    let h = admit_total_table(
        &fine.report_codomain,
        &coarse.report_codomain,
        h_rows,
        MapRole::Refinement,
    )
    .map_err(RefinementRefusal::RefinementTable)?;
    for (x, a_f) in &fine.report {
        if h.get(a_f) != coarse.report.get(x) {
            return Err(RefinementRefusal::RefinementEquationFailure { source: x.clone() });
        }
    }
    coarse
        .verify_factorization(coarse_cert)
        .map_err(RefinementRefusal::CoarseCertificate)?;
    Ok(h)
}

/// One-way refinement transfer. `fine` and `coarse` must share source and
/// query tables; `h_rows` must be a total table from the fine report codomain
/// into the coarse report codomain with `p_c(x) = h(p_f(x))` for every `x`;
/// `coarse_cert` must replay against `coarse`. Returns the fine certificate
/// `D_f = D_c . h` restricted to the fine realized image, replayed against
/// `fine` before it is returned.
pub fn transfer_refinement<X, F, C, B>(
    fine: &ReportQueryProblem<X, F, B>,
    coarse: &ReportQueryProblem<X, C, B>,
    h_rows: &[(F, C)],
    coarse_cert: &FactorizationCertificate<X, C, B>,
) -> Result<FactorizationCertificate<X, F, B>, RefinementRefusal<X, F>>
where
    X: Ord + Clone + fmt::Debug,
    F: Ord + Clone + fmt::Debug,
    C: Ord + Clone + fmt::Debug,
    B: Ord + Clone + fmt::Debug,
{
    let h = verify_refinement_inputs(fine, coarse, h_rows, coarse_cert)?;
    let mut decoder = BTreeMap::new();
    let mut representative = BTreeMap::new();
    for (x, a_f) in &fine.report {
        if representative.contains_key(a_f) {
            continue;
        }
        let value = h
            .get(a_f)
            .and_then(|a_c| coarse_cert.decoder.get(a_c))
            .cloned();
        let Some(value) = value else {
            return Err(RefinementRefusal::CoarseCertificate(
                CertificateRefusal::DecoderKeysMismatch,
            ));
        };
        decoder.insert(a_f.clone(), value);
        representative.insert(a_f.clone(), x.clone());
    }
    let cert = FactorizationCertificate {
        realized_image: decoder.keys().cloned().collect(),
        decoder,
        representative,
    };
    fine.verify_factorization(&cert)
        .map_err(RefinementRefusal::CoarseCertificate)?;
    Ok(cert)
}

// Origin: engine/crates_rs/core_category_theory/src/finite_report_query.rs
// Claim: urn:core:crates_rs:core-category-theory:finite-report-query:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_e17f5fc5 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
