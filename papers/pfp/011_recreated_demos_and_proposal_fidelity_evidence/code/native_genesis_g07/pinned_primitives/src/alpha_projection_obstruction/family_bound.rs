//! Corollary 5.1.A — the uniform family bound on a *supplied* finite
//! family: audit the displayed premises (`g ≤ g*`, active density `≥ η*`,
//! active rates `≥ ν*`, edge/site density `≥ a*`, `0 < t ≤ ν*/(48 g*²)`),
//! then compute the exact floors `η*(ν*t − 24g*²t²)` per edge and
//! `a*η*(ν*t − 24g*²t²)` per site.
//!
//! Replicates `family_bound.py`.  Ledger E5/E9: members `N4` (4 sites,
//! 4 edges, `g = 2`, rates `3, 4`) and `N6` (6 sites, 9 edges, `g = 3/2`,
//! rates `3, 3, 4, 4, 5, 5`), premises `(g*, η*, ν*, a*) = (2, 1/2, 3, 1)`,
//! `t = 1/64`: window `1/64`, edge floor `3/256`, site floor `3/256`,
//! two member bounds.
//!
//! Refused premises are returned as data, never hidden behind a boolean,
//! and a refused certificate carries no member bounds at all.  No
//! infinite-family quantifier is discharged: the certificate says only
//! that *these rows* satisfy *these constants* and that the arithmetic is
//! exact.

use super::rational::{q, Rational};

/// One finite system and the active-edge rates supplied by its caller.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct FiniteFamilyMember {
    /// Identifier.
    pub system_id: String,
    /// `|V|`.
    pub site_count: usize,
    /// `|E|`.
    pub edge_count: usize,
    /// The local interaction norm `g` of this member.
    pub local_interaction_norm: Rational,
    /// The rates `ν_e` of its active edges.
    pub active_edge_rates: Vec<Rational>,
}

impl FiniteFamilyMember {
    /// Build and validate.
    pub fn new(system_id: &str, site_count: usize, edge_count: usize, local_interaction_norm: Rational, active_edge_rates: Vec<Rational>) -> Result<FiniteFamilyMember, String> {
        if system_id.trim().is_empty() {
            return Err("system_id must be nonempty".into());
        }
        if site_count == 0 {
            return Err("site_count must be a positive integer".into());
        }
        if edge_count == 0 {
            return Err("edge_count must be a positive integer".into());
        }
        if local_interaction_norm < Rational::ZERO {
            return Err("local_interaction_norm must be nonnegative".into());
        }
        if active_edge_rates.len() > edge_count {
            return Err("active-edge count cannot exceed edge_count".into());
        }
        if active_edge_rates.iter().any(|r| *r < Rational::ZERO) {
            return Err("active-edge rates must be nonnegative".into());
        }
        Ok(FiniteFamilyMember { system_id: system_id.to_string(), site_count, edge_count, local_interaction_norm, active_edge_rates })
    }

    /// Number of active edges.
    pub fn active_edge_count(&self) -> usize {
        self.active_edge_rates.len()
    }

    /// `|E_active| / |E|`.
    pub fn active_edge_density(&self) -> Rational {
        Rational::new(self.active_edge_count() as i128, self.edge_count as i128)
    }

    /// `|E| / |V|`.
    pub fn edge_site_density(&self) -> Rational {
        Rational::new(self.edge_count as i128, self.site_count as i128)
    }
}

/// Candidate constants from the displayed hypotheses of Corollary 5.1.A.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct UniformFamilyPremises {
    /// `g*`.
    pub g_star: Rational,
    /// `η*`.
    pub eta_star: Rational,
    /// `ν*`.
    pub nu_star: Rational,
    /// `a*`.
    pub a_star: Rational,
}

/// A checkable reason that the finite certificate was not issued.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PremiseRefusal {
    /// Code.
    pub code: String,
    /// Detail.
    pub detail: String,
    /// The member, if the refusal is per member.
    pub system_id: Option<String>,
}

/// The exact conditional lower-bound arithmetic for one supplied member.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct MemberDensityBound {
    /// Member.
    pub system_id: String,
    /// `|E_active| / |E|`.
    pub active_edge_density: Rational,
    /// `|E| / |V|`.
    pub edge_site_density: Rational,
    /// `active_edge_density · (ν*t − 24g*²t²)`.
    pub edge_density_lower_bound: Rational,
    /// `|E_active| · (ν*t − 24g*²t²) / |V|`.
    pub site_density_lower_bound: Rational,
}

/// Result of the finite premise audit and exact bound calculation.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct UniformFamilyBoundCertificate {
    /// Supplied member rows, retained so a report cannot omit its witnesses.
    pub members: Vec<FiniteFamilyMember>,
    /// Declared constants retained for rechecking the displayed formulas.
    pub premises: UniformFamilyPremises,
    /// Issued.
    pub accepted: bool,
    /// `t`.
    pub time: Rational,
    /// `ν*/(48 g*²)`, when the constants allow it.
    pub uniform_window_upper: Option<Rational>,
    /// `ν*t − 24g*²t²`.
    pub local_edge_polynomial: Option<Rational>,
    /// `η* · polynomial`.
    pub edge_density_floor: Option<Rational>,
    /// `a* η* · polynomial`.
    pub site_density_floor: Option<Rational>,
    /// `a* η* ν* t / 2`.
    pub half_slope_site_floor: Option<Rational>,
    /// One per member, when accepted.
    pub member_bounds: Vec<MemberDensityBound>,
    /// Why not, when not.
    pub refusals: Vec<PremiseRefusal>,
}

impl UniformFamilyBoundCertificate {
    /// Recheck internal consistency without strengthening the scope.
    pub fn verify(&self) -> bool {
        calculate_uniform_family(&self.members, &self.premises, self.time)
            .is_ok_and(|expected| expected == *self)
    }
}

fn constant_refusals(p: &UniformFamilyPremises) -> Vec<PremiseRefusal> {
    let mut out = Vec::new();
    let refuse = |code: &str, detail: &str| PremiseRefusal { code: code.into(), detail: detail.into(), system_id: None };
    if p.g_star <= Rational::ZERO {
        out.push(refuse("g_star_not_positive", "the displayed finite time window requires g_star > 0"));
    }
    if p.eta_star <= Rational::ZERO {
        out.push(refuse("eta_star_not_positive", "eta_star must be strictly positive"));
    } else if p.eta_star > Rational::ONE {
        out.push(refuse("eta_star_exceeds_one", "an active-edge density cannot exceed one"));
    }
    if p.nu_star <= Rational::ZERO {
        out.push(refuse("nu_star_not_positive", "nu_star must be strictly positive"));
    }
    if p.a_star <= Rational::ZERO {
        out.push(refuse("a_star_not_positive", "a_star must be strictly positive"));
    }
    out
}

/// Audit a finite family and calculate the conditional density floors.
pub fn certify_uniform_family(members: &[FiniteFamilyMember], premises: &UniformFamilyPremises, time: Rational) -> Result<UniformFamilyBoundCertificate, String> {
    let certificate = calculate_uniform_family(members, premises, time)?;
    if !certificate.verify() { return Err("family certificate replay failed".into()); }
    Ok(certificate)
}

fn calculate_uniform_family(members: &[FiniteFamilyMember], premises: &UniformFamilyPremises, time: Rational) -> Result<UniformFamilyBoundCertificate, String> {
    let t = time;
    let mut refusals = constant_refusals(premises);
    if members.is_empty() {
        refusals.push(PremiseRefusal { code: "empty_family".into(), detail: "at least one system is required".into(), system_id: None });
    }
    if t <= Rational::ZERO {
        refusals.push(PremiseRefusal { code: "time_not_positive".into(), detail: "the theorem window requires t > 0".into(), system_id: None });
    }
    let mut ids: Vec<&str> = members.iter().map(|m| m.system_id.as_str()).collect();
    ids.sort();
    ids.dedup();
    if ids.len() != members.len() {
        refusals.push(PremiseRefusal { code: "duplicate_system_id".into(), detail: "system identifiers must be unique".into(), system_id: None });
    }
    for m in members {
        FiniteFamilyMember::new(&m.system_id, m.site_count, m.edge_count,
            m.local_interaction_norm, m.active_edge_rates.clone())?;
        let per = |code: &str, detail: String| PremiseRefusal { code: code.into(), detail, system_id: Some(m.system_id.clone()) };
        if m.local_interaction_norm > premises.g_star {
            refusals.push(per("interaction_bound_failed", format!("{} > g_star={}", m.local_interaction_norm, premises.g_star)));
        }
        if m.active_edge_density() < premises.eta_star {
            refusals.push(per("active_density_failed", format!("{} < eta_star={}", m.active_edge_density(), premises.eta_star)));
        }
        match m.active_edge_rates.iter().copied().min() {
            None => refusals.push(per("no_active_edges", "a positive active-rate infimum needs a nonempty active set".into())),
            Some(min) if min < premises.nu_star => refusals.push(per("active_rate_failed", format!("minimum rate {min} < nu_star={}", premises.nu_star))),
            _ => {}
        }
        if m.edge_site_density() < premises.a_star {
            refusals.push(per("edge_site_density_failed", format!("{} < a_star={}", m.edge_site_density(), premises.a_star)));
        }
    }
    let mut window = None;
    if premises.g_star > Rational::ZERO && premises.nu_star > Rational::ZERO {
        let w = premises.nu_star / (q(48) * premises.g_star.pow(2));
        window = Some(w);
        if t > w {
            refusals.push(PremiseRefusal { code: "outside_uniform_window".into(), detail: format!("time {t} exceeds nu_star/(48*g_star^2)={w}"), system_id: None });
        }
    }
    if !refusals.is_empty() {
        let cert = UniformFamilyBoundCertificate {
            members: members.to_vec(), premises: *premises,
            accepted: false,
            time: t,
            uniform_window_upper: window,
            local_edge_polynomial: None,
            edge_density_floor: None,
            site_density_floor: None,
            half_slope_site_floor: None,
            member_bounds: Vec::new(),
            refusals,
        };
        return Ok(cert);
    }
    let polynomial = premises.nu_star * t - q(24) * premises.g_star.pow(2) * t.pow(2);
    let edge_floor = premises.eta_star * polynomial;
    let site_floor = premises.a_star * premises.eta_star * polynomial;
    let half_slope = premises.a_star * premises.eta_star * premises.nu_star * t / q(2);
    let member_bounds = members
        .iter()
        .map(|m| MemberDensityBound {
            system_id: m.system_id.clone(),
            active_edge_density: m.active_edge_density(),
            edge_site_density: m.edge_site_density(),
            edge_density_lower_bound: m.active_edge_density() * polynomial,
            site_density_lower_bound: q(m.active_edge_count() as i128) * polynomial / q(m.site_count as i128),
        })
        .collect();
    let cert = UniformFamilyBoundCertificate {
        members: members.to_vec(), premises: *premises,
        accepted: true,
        time: t,
        uniform_window_upper: window,
        local_edge_polynomial: Some(polynomial),
        edge_density_floor: Some(edge_floor),
        site_density_floor: Some(site_floor),
        half_slope_site_floor: Some(half_slope),
        member_bounds,
        refusals: Vec::new(),
    };
    Ok(cert)
}

/// The receipt family: `N4` and `N6`, premises `(2, 1/2, 3, 1)`.
pub fn receipt_family() -> (Vec<FiniteFamilyMember>, UniformFamilyPremises) {
    let members = vec![
        FiniteFamilyMember::new("N4", 4, 4, q(2), vec![q(3), q(4)]).expect("valid"),
        FiniteFamilyMember::new("N6", 6, 9, Rational::new(3, 2), vec![q(3), q(3), q(4), q(4), q(5), q(5)]).expect("valid"),
    ];
    (members, UniformFamilyPremises { g_star: q(2), eta_star: Rational::new(1, 2), nu_star: q(3), a_star: q(1) })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::alpha_projection_obstruction::rational::r;

    /// E5/E9: window 1/64, floors 3/256 and 3/256, two members.
    #[test]
    fn the_receipt_family_certifies_at_one_sixty_fourth() {
        let (members, premises) = receipt_family();
        let c = certify_uniform_family(&members, &premises, r(1, 64)).unwrap();
        assert!(c.accepted && c.verify());
        assert_eq!(c.uniform_window_upper, Some(r(1, 64)));
        assert_eq!(c.edge_density_floor, Some(r(3, 256)));
        assert_eq!(c.site_density_floor, Some(r(3, 256)));
        assert_eq!(c.member_bounds.len(), 2);
        // polynomial = 3/64 - 24*4/4096 = 3/64 - 3/128 = 3/128
        assert_eq!(c.local_edge_polynomial, Some(r(3, 128)));
        // a* eta* nu* t / 2 = 1 * 1/2 * 3 * 1/64 / 2 = 3/256, equal to the site floor here.
        assert_eq!(c.half_slope_site_floor, Some(r(3, 256)));
    }

    /// Past the window, or with a member out of premise, the certificate
    /// is refused with the reason as data.
    #[test]
    fn refusals_are_data_and_carry_no_member_bounds() {
        let (members, premises) = receipt_family();
        let late = certify_uniform_family(&members, &premises, r(1, 32)).unwrap();
        assert!(!late.accepted && late.verify() && late.member_bounds.is_empty());
        assert_eq!(late.refusals[0].code, "outside_uniform_window");
        let mut weak = members.clone();
        weak[0].active_edge_rates = vec![q(1), q(4)];
        let c = certify_uniform_family(&weak, &premises, r(1, 64)).unwrap();
        assert!(!c.accepted);
        assert_eq!(c.refusals[0].code, "active_rate_failed");
        assert_eq!(c.refusals[0].system_id.as_deref(), Some("N4"));
        assert!(FiniteFamilyMember::new("x", 2, 1, q(1), vec![q(1), q(1)]).is_err());
    }
}
