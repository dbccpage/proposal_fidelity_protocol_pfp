//! Exact quadratic density bounds for a supplied finite family.
//!
//! Migrated from the Majorana paper's `family_bound.py`. The supplied rates,
//! interaction bounds and finite counts are premises, not computed dynamics.
//! Acceptance certifies these rows and the displayed arithmetic only.

use num_rational::BigRational;
use num_traits::{One, Zero};
use std::collections::BTreeSet;

pub type Rational = BigRational;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum FamilyBoundError {
    #[error("system_id must be nonempty")]
    EmptyIdentifier,
    #[error("site_count and edge_count must be positive")]
    ZeroCount,
    #[error("local_interaction_norm and active-edge rates must be nonnegative")]
    NegativeInput,
    #[error("active-edge count cannot exceed edge_count")]
    TooManyActiveEdges,
    #[error("exact rational denominator must be nonzero")]
    ZeroDenominator,
}

fn canonical(value: &Rational) -> Result<Rational, FamilyBoundError> {
    if value.denom().is_zero() {
        return Err(FamilyBoundError::ZeroDenominator);
    }
    Ok(crate::gamma2::canonical_rational(value))
}

fn integer(value: usize) -> Rational {
    Rational::from_integer(value.into())
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteFamilyMember {
    system_id: String,
    site_count: usize,
    edge_count: usize,
    local_interaction_norm: Rational,
    active_edge_rates: Vec<Rational>,
}

impl FiniteFamilyMember {
    pub fn new(
        system_id: &str,
        site_count: usize,
        edge_count: usize,
        local_interaction_norm: Rational,
        active_edge_rates: Vec<Rational>,
    ) -> Result<Self, FamilyBoundError> {
        if system_id.trim().is_empty() {
            return Err(FamilyBoundError::EmptyIdentifier);
        }
        if site_count == 0 || edge_count == 0 {
            return Err(FamilyBoundError::ZeroCount);
        }
        if active_edge_rates.len() > edge_count {
            return Err(FamilyBoundError::TooManyActiveEdges);
        }
        let norm = canonical(&local_interaction_norm)?;
        let rates = active_edge_rates
            .iter()
            .map(canonical)
            .collect::<Result<Vec<_>, _>>()?;
        if norm < Rational::zero() || rates.iter().any(|rate| rate < &Rational::zero()) {
            return Err(FamilyBoundError::NegativeInput);
        }
        Ok(Self {
            system_id: system_id.into(),
            site_count,
            edge_count,
            local_interaction_norm: norm,
            active_edge_rates: rates,
        })
    }

    pub fn system_id(&self) -> &str {
        &self.system_id
    }
    pub fn site_count(&self) -> usize {
        self.site_count
    }
    pub fn edge_count(&self) -> usize {
        self.edge_count
    }
    pub fn local_interaction_norm(&self) -> &Rational {
        &self.local_interaction_norm
    }
    pub fn active_edge_rates(&self) -> &[Rational] {
        &self.active_edge_rates
    }

    pub fn active_edge_density(&self) -> Rational {
        // The constructor and evaluation boundary validate positive counts.
        integer(self.active_edge_rates.len()) / integer(self.edge_count)
    }

    pub fn edge_site_density(&self) -> Rational {
        integer(self.edge_count) / integer(self.site_count)
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct UniformFamilyPremises {
    pub g_star: Rational,
    pub eta_star: Rational,
    pub nu_star: Rational,
    pub a_star: Rational,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PremiseRefusal {
    pub code: &'static str,
    pub detail: String,
    pub system_id: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MemberDensityBound {
    pub system_id: String,
    pub active_edge_density: Rational,
    pub edge_site_density: Rational,
    pub edge_density_lower_bound: Rational,
    pub site_density_lower_bound: Rational,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct UniformFamilyBoundCertificate {
    pub members: Vec<FiniteFamilyMember>,
    pub premises: UniformFamilyPremises,
    pub accepted: bool,
    pub time: Rational,
    pub uniform_window_upper: Option<Rational>,
    pub local_edge_polynomial: Option<Rational>,
    pub edge_density_floor: Option<Rational>,
    pub site_density_floor: Option<Rational>,
    pub half_slope_site_floor: Option<Rational>,
    pub member_bounds: Vec<MemberDensityBound>,
    pub refusals: Vec<PremiseRefusal>,
}

impl UniformFamilyBoundCertificate {
    pub fn verify(&self) -> bool {
        certify_uniform_family(&self.members, &self.premises, &self.time)
            .is_ok_and(|expected| expected == *self)
    }
}

fn push_refusal(
    refusals: &mut Vec<PremiseRefusal>,
    code: &'static str,
    detail: &str,
    system_id: Option<&str>,
) {
    refusals.push(PremiseRefusal {
        code,
        detail: detail.into(),
        system_id: system_id.map(str::to_string),
    });
}

fn check_global_family_premises(
    p: &UniformFamilyPremises,
    members: &[FiniteFamilyMember],
    time: &Rational,
    refusals: &mut Vec<PremiseRefusal>,
) {
    let zero = Rational::zero();
    for (value, code, detail) in [
        (
            &p.g_star,
            "g_star_not_positive",
            "the displayed finite time window requires g_star > 0",
        ),
        (
            &p.eta_star,
            "eta_star_not_positive",
            "eta_star must be strictly positive",
        ),
        (
            &p.nu_star,
            "nu_star_not_positive",
            "nu_star must be strictly positive",
        ),
        (
            &p.a_star,
            "a_star_not_positive",
            "a_star must be strictly positive",
        ),
    ] {
        if value <= &zero {
            push_refusal(refusals, code, detail, None);
        }
    }
    if p.eta_star > Rational::one() {
        push_refusal(
            refusals,
            "eta_star_exceeds_one",
            "an active-edge density cannot exceed one",
            None,
        );
    }
    if members.is_empty() {
        push_refusal(
            refusals,
            "empty_family",
            "at least one system is required",
            None,
        );
    }
    if time <= &zero {
        push_refusal(
            refusals,
            "time_not_positive",
            "the theorem window requires t > 0",
            None,
        );
    }
    let ids: BTreeSet<_> = members.iter().map(|m| m.system_id.as_str()).collect();
    if ids.len() != members.len() {
        push_refusal(
            refusals,
            "duplicate_system_id",
            "system identifiers must be unique",
            None,
        );
    }
}

fn check_member_premises(
    m: &FiniteFamilyMember,
    p: &UniformFamilyPremises,
    refusals: &mut Vec<PremiseRefusal>,
) {
    if m.local_interaction_norm > p.g_star {
        push_refusal(
            refusals,
            "interaction_bound_failed",
            &format!("{} > g_star={}", m.local_interaction_norm, p.g_star),
            Some(&m.system_id),
        );
    }
    let density = m.active_edge_density();
    if density < p.eta_star {
        push_refusal(
            refusals,
            "active_density_failed",
            &format!("{} < eta_star={}", density, p.eta_star),
            Some(&m.system_id),
        );
    }
    match m.active_edge_rates.iter().min() {
        None => push_refusal(
            refusals,
            "no_active_edges",
            "a positive active-rate infimum needs a nonempty active set",
            Some(&m.system_id),
        ),
        Some(rate) if rate < &p.nu_star => push_refusal(
            refusals,
            "active_rate_failed",
            &format!("minimum rate {rate} < nu_star={}", p.nu_star),
            Some(&m.system_id),
        ),
        _ => {}
    }
    let density = m.edge_site_density();
    if density < p.a_star {
        push_refusal(
            refusals,
            "edge_site_density_failed",
            &format!("{} < a_star={}", density, p.a_star),
            Some(&m.system_id),
        );
    }
}

fn compute_uniform_window(
    p: &UniformFamilyPremises,
    time: &Rational,
    refusals: &mut Vec<PremiseRefusal>,
) -> Option<Rational> {
    let zero = Rational::zero();
    if p.g_star > zero && p.nu_star > zero {
        let w = &p.nu_star / (integer(48) * &p.g_star * &p.g_star);
        if time > &w {
            push_refusal(
                refusals,
                "outside_uniform_window",
                &format!("time {time} exceeds nu_star/(48*g_star^2)={w}"),
                None,
            );
        }
        Some(w)
    } else {
        None
    }
}

fn canonicalize_family_inputs(
    members: &[FiniteFamilyMember],
    premises: &UniformFamilyPremises,
    time: &Rational,
) -> Result<(UniformFamilyPremises, Rational, Vec<FiniteFamilyMember>), FamilyBoundError> {
    let p = UniformFamilyPremises {
        g_star: canonical(&premises.g_star)?,
        eta_star: canonical(&premises.eta_star)?,
        nu_star: canonical(&premises.nu_star)?,
        a_star: canonical(&premises.a_star)?,
    };
    let time = canonical(time)?;
    let members = members
        .iter()
        .map(|member| {
            FiniteFamilyMember::new(
                &member.system_id,
                member.site_count,
                member.edge_count,
                member.local_interaction_norm.clone(),
                member.active_edge_rates.clone(),
            )
        })
        .collect::<Result<Vec<_>, _>>()?;
    Ok((p, time, members))
}

/// Check every supplied member before computing `nu*t - 24*g^2*t^2`.
/// Invalid value objects are errors; well-formed failed premises produce a
/// refused certificate with no member bounds or conclusion fields.
pub fn certify_uniform_family(
    members: &[FiniteFamilyMember],
    premises: &UniformFamilyPremises,
    time: &Rational,
) -> Result<UniformFamilyBoundCertificate, FamilyBoundError> {
    let (p, time, members) = canonicalize_family_inputs(members, premises, time)?;
    let mut refusals = Vec::new();
    check_global_family_premises(&p, &members, &time, &mut refusals);
    for m in &members {
        check_member_premises(m, &p, &mut refusals);
    }
    let window = compute_uniform_window(&p, &time, &mut refusals);
    let mut result = UniformFamilyBoundCertificate {
        members,
        premises: p,
        accepted: refusals.is_empty(),
        time,
        uniform_window_upper: window,
        local_edge_polynomial: None,
        edge_density_floor: None,
        site_density_floor: None,
        half_slope_site_floor: None,
        member_bounds: Vec::new(),
        refusals,
    };
    if !result.accepted {
        return Ok(result);
    }
    let p = &result.premises;
    let t = &result.time;
    let polynomial = &p.nu_star * t - integer(24) * &p.g_star * &p.g_star * t * t;
    result.edge_density_floor = Some(&p.eta_star * &polynomial);
    result.site_density_floor = Some(&p.a_star * &p.eta_star * &polynomial);
    result.half_slope_site_floor = Some(&p.a_star * &p.eta_star * &p.nu_star * t / integer(2));
    result.member_bounds = result
        .members
        .iter()
        .map(|m| MemberDensityBound {
            system_id: m.system_id.clone(),
            active_edge_density: m.active_edge_density(),
            edge_site_density: m.edge_site_density(),
            edge_density_lower_bound: m.active_edge_density() * &polynomial,
            site_density_lower_bound: integer(m.active_edge_rates.len()) * &polynomial
                / integer(m.site_count),
        })
        .collect();
    result.local_edge_polynomial = Some(polynomial);
    Ok(result)
}

// Origin: engine/crates_rs/core_functional/src/finite_family_bound.rs
// Claim: urn:core:crates_rs:core-functional:finite-family-bound:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    fn q(n: i64) -> Rational {
        Rational::from_integer(n.into())
    }
    fn r(n: i64, d: i64) -> Rational {
        Rational::new(n.into(), d.into())
    }
    fn fixture() -> (Vec<FiniteFamilyMember>, UniformFamilyPremises) {
        (
            vec![
                FiniteFamilyMember::new("N4", 4, 4, q(2), vec![q(3), q(4)]).unwrap(),
                FiniteFamilyMember::new(
                    "N6",
                    6,
                    9,
                    r(3, 2),
                    vec![q(3), q(3), q(4), q(4), q(5), q(5)],
                )
                .unwrap(),
            ],
            UniformFamilyPremises {
                g_star: q(2),
                eta_star: r(1, 2),
                nu_star: q(3),
                a_star: q(1),
            },
        )
    }

    #[test]
    fn supplied_family_reproduces_the_uniform_and_member_floors() {
        let (m, p) = fixture();
        let c = certify_uniform_family(&m, &p, &r(1, 64)).unwrap();
        assert!(c.accepted && c.verify());
        assert_eq!(c.uniform_window_upper, Some(r(1, 64)));
        assert_eq!(c.local_edge_polynomial, Some(r(3, 128)));
        assert_eq!(c.edge_density_floor, Some(r(3, 256)));
        assert_eq!(c.site_density_floor, Some(r(3, 256)));
        assert_eq!(c.half_slope_site_floor, Some(r(3, 256)));
        assert_eq!(c.member_bounds[1].site_density_lower_bound, r(3, 128));
    }

    #[test]
    fn replay_binds_premises_members_and_bound_rows() {
        let (m, p) = fixture();
        let c = certify_uniform_family(&m, &p, &r(1, 64)).unwrap();
        let mut changed = c.clone();
        changed.member_bounds.pop();
        assert!(!changed.verify());
        let mut changed = c.clone();
        changed.premises.nu_star = q(4);
        assert!(!changed.verify());
        let mut changed = c;
        changed.members[0].active_edge_rates[0] = q(2);
        assert!(!changed.verify());
    }

    #[test]
    fn failed_premises_do_not_carry_conclusion_data() {
        let (mut m, p) = fixture();
        m[0].active_edge_rates.clear();
        let c = certify_uniform_family(&m, &p, &r(1, 32)).unwrap();
        assert!(!c.accepted && c.verify());
        assert!(c.member_bounds.is_empty());
        assert!(c.local_edge_polynomial.is_none() && c.site_density_floor.is_none());
        for code in [
            "no_active_edges",
            "active_density_failed",
            "outside_uniform_window",
        ] {
            assert!(c.refusals.iter().any(|reason| reason.code == code));
        }
        let empty = certify_uniform_family(&[], &p, &q(0)).unwrap();
        assert!(empty
            .refusals
            .iter()
            .any(|reason| reason.code == "empty_family"));
        assert!(empty
            .refusals
            .iter()
            .any(|reason| reason.code == "time_not_positive"));
        let (mut m, _) = fixture();
        m.push(m[0].clone());
        assert!(certify_uniform_family(&m, &p, &r(1, 64))
            .unwrap()
            .refusals
            .iter()
            .any(|reason| reason.code == "duplicate_system_id"));
    }

    #[test]
    fn value_errors_and_nonpositive_constants_are_distinct() {
        let (mut m, mut p) = fixture();
        m[0].site_count = 0;
        assert_eq!(
            certify_uniform_family(&m, &p, &r(1, 64)),
            Err(FamilyBoundError::ZeroCount)
        );
        let invalid = Rational::new_raw(1.into(), 0.into());
        p.g_star = invalid;
        assert_eq!(
            certify_uniform_family(&[], &p, &q(1)),
            Err(FamilyBoundError::ZeroDenominator)
        );
        p.g_star = q(0);
        let c = certify_uniform_family(&[], &p, &q(1)).unwrap();
        assert!(!c.accepted && c.uniform_window_upper.is_none());
        assert!(c
            .refusals
            .iter()
            .any(|reason| reason.code == "g_star_not_positive"));
    }

    #[test]
    fn arbitrary_precision_preserves_a_tiny_exact_time_window() {
        let huge = Rational::from_integer(num_bigint::BigInt::from(1u8) << 300);
        let m = vec![FiniteFamilyMember::new("large", 1, 1, huge.clone(), vec![q(1)]).unwrap()];
        let p = UniformFamilyPremises {
            g_star: huge.clone(),
            eta_star: q(1),
            nu_star: q(1),
            a_star: q(1),
        };
        let time = q(1) / (q(48) * &huge * &huge);
        let c = certify_uniform_family(&m, &p, &time).unwrap();
        assert!(c.accepted && c.verify());
        assert_eq!(c.half_slope_site_floor, Some(time / q(2)));
    }
}
