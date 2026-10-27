//! Constrained finite observer presentations with coherent report transports.
//!
//! A context carries admissible pointwise reports and an injective decoding into
//! shared report values. Transport is decode, restrict, then uniquely identify
//! the target chart's admissible report. Restriction closure is checked before
//! delegating identity/composition and finite descent classification to
//! `core_category_theory::finite_report_descent`. Global constraints can prevent
//! compatible local reports from gluing; their absence is not presumed.

use std::collections::{BTreeMap, BTreeSet};

use core_category_theory::finite_report_descent::{
    CoverClassification, DescentError, DescentFiber, FiniteReportPresheaf,
};
use thiserror::Error;

use crate::types::AuthorityEffect;

pub type ObserverReport = BTreeMap<String, String>;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObserverPresentation {
    pub points: BTreeSet<String>,
    pub admissible_reports: Vec<ObserverReport>,
    pub decoding: BTreeMap<String, String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ConstrainedObserverSite {
    pub carrier: BTreeSet<String>,
    pub presentations: BTreeMap<String, ObserverPresentation>,
}

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum ObserverSiteError {
    #[error("observer context identities must be nonempty and distinct subsets")]
    InvalidContextIdentity,
    #[error("context {context} contains a point outside the carrier")]
    ContextOutsideCarrier { context: String },
    #[error("context {context} has a report with the wrong domain")]
    ReportDomainMismatch { context: String },
    #[error("context {context} has a missing or noninjective report decoding")]
    InvalidDecoding { context: String },
    #[error("context {context} duplicates an admissible decoded report")]
    DuplicateReport { context: String },
    #[error(
        "restriction of report {section} from {source_context} to {target_context} is inadmissible"
    )]
    RestrictionNotAdmissible {
        source_context: String,
        target_context: String,
        section: usize,
    },
    #[error("unknown observer context {context}")]
    UnknownContext { context: String },
    #[error("finite report descent refusal: {0}")]
    Descent(#[from] DescentError),
}

struct CompiledSite {
    presheaf: FiniteReportPresheaf,
    masks: BTreeMap<String, u64>,
    decoded: BTreeMap<String, Vec<ObserverReport>>,
}

impl ConstrainedObserverSite {
    fn compile(&self) -> Result<CompiledSite, ObserverSiteError> {
        if self.carrier.len() > 64 {
            return Err(DescentError::CarrierTooLarge.into());
        }
        let indices: BTreeMap<_, _> = self
            .carrier
            .iter()
            .cloned()
            .enumerate()
            .map(|(i, p)| (p, i))
            .collect();
        let mut masks = BTreeMap::new();
        let mut counts = BTreeMap::new();
        let mut decoded = BTreeMap::new();
        for (context, presentation) in &self.presentations {
            let (mask, canonical_reports) =
                Self::compile_presentation(context, presentation, &indices, &counts)?;
            counts.insert(mask, canonical_reports.len());
            masks.insert(context.clone(), mask);
            decoded.insert(context.clone(), canonical_reports);
        }
        let restrictions = self.build_restrictions(&masks, &decoded)?;
        let presheaf = FiniteReportPresheaf::new(self.carrier.len(), counts, restrictions)?;
        Ok(CompiledSite {
            presheaf,
            masks,
            decoded,
        })
    }

    fn compile_presentation(
        context: &str,
        presentation: &ObserverPresentation,
        indices: &BTreeMap<String, usize>,
        counts: &BTreeMap<u64, usize>,
    ) -> Result<(u64, Vec<ObserverReport>), ObserverSiteError> {
        if context.is_empty() {
            return Err(ObserverSiteError::InvalidContextIdentity);
        }
        let mask = Self::presentation_mask(context, &presentation.points, indices)?;
        if counts.contains_key(&mask) {
            return Err(ObserverSiteError::InvalidContextIdentity);
        }
        let canonical_values: BTreeSet<_> = presentation.decoding.values().collect();
        if canonical_values.len() != presentation.decoding.len() {
            return Err(ObserverSiteError::InvalidDecoding {
                context: context.to_string(),
            });
        }
        let canonical_reports = Self::decode_admissible_reports(context, presentation)?;
        Ok((mask, canonical_reports))
    }

    fn presentation_mask(
        context: &str,
        points: &BTreeSet<String>,
        indices: &BTreeMap<String, usize>,
    ) -> Result<u64, ObserverSiteError> {
        let mut mask = 0u64;
        for point in points {
            let index =
                indices
                    .get(point)
                    .ok_or_else(|| ObserverSiteError::ContextOutsideCarrier {
                        context: context.to_string(),
                    })?;
            mask |= 1u64 << index;
        }
        Ok(mask)
    }

    fn decode_admissible_reports(
        context: &str,
        presentation: &ObserverPresentation,
    ) -> Result<Vec<ObserverReport>, ObserverSiteError> {
        let mut canonical_reports = Vec::new();
        for report in &presentation.admissible_reports {
            if report.keys().cloned().collect::<BTreeSet<_>>() != presentation.points {
                return Err(ObserverSiteError::ReportDomainMismatch {
                    context: context.to_string(),
                });
            }
            let canonical = Self::decode_single_report(context, report, &presentation.decoding)?;
            if canonical_reports.contains(&canonical) {
                return Err(ObserverSiteError::DuplicateReport {
                    context: context.to_string(),
                });
            }
            canonical_reports.push(canonical);
        }
        Ok(canonical_reports)
    }

    fn decode_single_report(
        context: &str,
        report: &ObserverReport,
        decoding: &BTreeMap<String, String>,
    ) -> Result<ObserverReport, ObserverSiteError> {
        report
            .iter()
            .map(|(point, value)| {
                let value =
                    decoding
                        .get(value)
                        .ok_or_else(|| ObserverSiteError::InvalidDecoding {
                            context: context.to_string(),
                        })?;
                Ok((point.clone(), value.clone()))
            })
            .collect()
    }

    fn build_restrictions(
        &self,
        masks: &BTreeMap<String, u64>,
        decoded: &BTreeMap<String, Vec<ObserverReport>>,
    ) -> Result<BTreeMap<(u64, u64), Vec<usize>>, ObserverSiteError> {
        let mut restrictions = BTreeMap::new();
        for (source, &a) in masks {
            for (target, &b) in masks {
                if a & b == b {
                    let rows = self.restrict_context_reports(source, target, decoded)?;
                    restrictions.insert((a, b), rows);
                }
            }
        }
        Ok(restrictions)
    }

    fn restrict_context_reports(
        &self,
        source: &str,
        target: &str,
        decoded: &BTreeMap<String, Vec<ObserverReport>>,
    ) -> Result<Vec<usize>, ObserverSiteError> {
        decoded[source]
            .iter()
            .enumerate()
            .map(|(section, report)| {
                let restricted: ObserverReport = report
                    .iter()
                    .filter(|(p, _)| self.presentations[target].points.contains(*p))
                    .map(|(p, v)| (p.clone(), v.clone()))
                    .collect();
                decoded[target]
                    .iter()
                    .position(|r| r == &restricted)
                    .ok_or_else(|| ObserverSiteError::RestrictionNotAdmissible {
                        source_context: source.to_string(),
                        target_context: target.to_string(),
                        section,
                    })
            })
            .collect()
    }

    pub fn validate(&self) -> Result<(), ObserverSiteError> {
        self.compile().map(|_| ())
    }
}

fn mask(compiled: &CompiledSite, context: &str) -> Result<u64, ObserverSiteError> {
    compiled
        .masks
        .get(context)
        .copied()
        .ok_or_else(|| ObserverSiteError::UnknownContext {
            context: context.to_string(),
        })
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ConstraintGluingObstruction {
    pub target_context: String,
    pub compatible_union_report: ObserverReport,
    pub reason: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObserverDescentReceipt {
    pub actual_site: ConstrainedObserverSite,
    pub target_context: String,
    pub cover_contexts: Vec<String>,
    pub local_sections: Vec<usize>,
    pub canonical_union_report: ObserverReport,
    pub fiber: DescentFiber,
    pub obstruction: Option<ConstraintGluingObstruction>,
    pub authority_effect: AuthorityEffect,
}

pub fn solve_constrained_observer_descent(
    site: &ConstrainedObserverSite,
    target: &str,
    cover: &[String],
    locals: &[usize],
) -> Result<ObserverDescentReceipt, ObserverSiteError> {
    let compiled = site.compile()?;
    let target_mask = mask(&compiled, target)?;
    let cover_masks = cover
        .iter()
        .map(|c| mask(&compiled, c))
        .collect::<Result<Vec<_>, _>>()?;
    let fiber = compiled
        .presheaf
        .descent_fiber(target_mask, &cover_masks, locals)?;
    let mut canonical_union_report = ObserverReport::new();
    for (context, &section) in cover.iter().zip(locals) {
        canonical_union_report.extend(compiled.decoded[context][section].clone());
    }
    let obstruction = if fiber.global_sections.is_empty() {
        Some(ConstraintGluingObstruction {
            target_context: target.to_string(),
            compatible_union_report: canonical_union_report.clone(),
            reason: "compatible pointwise union is excluded from the declared target report family"
                .to_string(),
        })
    } else {
        None
    };
    Ok(ObserverDescentReceipt {
        actual_site: site.clone(),
        target_context: target.to_string(),
        cover_contexts: cover.to_vec(),
        local_sections: locals.to_vec(),
        canonical_union_report,
        fiber,
        obstruction,
        authority_effect: AuthorityEffect::None,
    })
}

pub fn verify_constrained_observer_descent(
    actual_site: &ConstrainedObserverSite,
    actual_target: &str,
    actual_cover: &[String],
    actual_locals: &[usize],
    candidate: &ObserverDescentReceipt,
) -> Result<bool, ObserverSiteError> {
    Ok(candidate
        == &solve_constrained_observer_descent(
            actual_site,
            actual_target,
            actual_cover,
            actual_locals,
        )?)
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObserverCoverClassification {
    pub actual_site: ConstrainedObserverSite,
    pub target_context: String,
    pub cover_contexts: Vec<String>,
    pub classification: CoverClassification,
    pub authority_effect: AuthorityEffect,
}

pub fn classify_observer_cover(
    site: &ConstrainedObserverSite,
    target: &str,
    cover: &[String],
    enumeration_limit: usize,
) -> Result<ObserverCoverClassification, ObserverSiteError> {
    let compiled = site.compile()?;
    let target_mask = mask(&compiled, target)?;
    let cover_masks = cover
        .iter()
        .map(|c| mask(&compiled, c))
        .collect::<Result<Vec<_>, _>>()?;
    Ok(ObserverCoverClassification {
        actual_site: site.clone(),
        target_context: target.to_string(),
        cover_contexts: cover.to_vec(),
        classification: compiled.presheaf.classify_cover(
            target_mask,
            &cover_masks,
            enumeration_limit,
        )?,
        authority_effect: AuthorityEffect::None,
    })
}

pub fn verify_observer_cover_classification(
    site: &ConstrainedObserverSite,
    target: &str,
    cover: &[String],
    enumeration_limit: usize,
    candidate: &ObserverCoverClassification,
) -> Result<bool, ObserverSiteError> {
    Ok(candidate == &classify_observer_cover(site, target, cover, enumeration_limit)?)
}

// Origin: engine/crates_rs/core_wdp/src/observer_site.rs
// Claim: urn:core:crates_rs:core-wdp:observer-site:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    fn report(values: &[(&str, &str)]) -> ObserverReport {
        values
            .iter()
            .map(|(p, v)| (p.to_string(), v.to_string()))
            .collect()
    }
    fn equality_site() -> ConstrainedObserverSite {
        let global = ObserverPresentation {
            points: BTreeSet::from(["x".into(), "y".into()]),
            admissible_reports: vec![
                report(&[("x", "zero"), ("y", "zero")]),
                report(&[("x", "one"), ("y", "one")]),
            ],
            decoding: BTreeMap::from([("zero".into(), "0".into()), ("one".into(), "1".into())]),
        };
        let x = ObserverPresentation {
            points: BTreeSet::from(["x".into()]),
            admissible_reports: vec![report(&[("x", "off")]), report(&[("x", "on")])],
            decoding: BTreeMap::from([("off".into(), "0".into()), ("on".into(), "1".into())]),
        };
        let y = ObserverPresentation {
            points: BTreeSet::from(["y".into()]),
            admissible_reports: vec![report(&[("y", "false")]), report(&[("y", "true")])],
            decoding: BTreeMap::from([("false".into(), "0".into()), ("true".into(), "1".into())]),
        };
        ConstrainedObserverSite {
            carrier: global.points.clone(),
            presentations: BTreeMap::from([
                ("global".into(), global),
                ("x-chart".into(), x),
                ("y-chart".into(), y),
                (
                    "empty".into(),
                    ObserverPresentation {
                        points: BTreeSet::new(),
                        admissible_reports: vec![BTreeMap::new()],
                        decoding: BTreeMap::new(),
                    },
                ),
            ]),
        }
    }
    #[test]
    fn coherent_observer_charts_glue_exactly_when_global_constraint_allows() {
        let site = equality_site();
        site.validate().unwrap();
        let cover = vec!["x-chart".into(), "y-chart".into()];
        let obstructed =
            solve_constrained_observer_descent(&site, "global", &cover, &[0, 1]).unwrap();
        assert_eq!(
            obstructed.canonical_union_report,
            report(&[("x", "0"), ("y", "1")])
        );
        assert!(obstructed.fiber.global_sections.is_empty());
        assert!(obstructed.obstruction.is_some());
        assert!(
            verify_constrained_observer_descent(&site, "global", &cover, &[0, 1], &obstructed)
                .unwrap()
        );
        let glued = solve_constrained_observer_descent(&site, "global", &cover, &[1, 1]).unwrap();
        assert_eq!(glued.fiber.global_sections, vec![1]);
        assert!(glued.obstruction.is_none());
        let classification = classify_observer_cover(&site, "global", &cover, 4).unwrap();
        assert!(classification.classification.is_separated);
        assert!(!classification.classification.has_existence);
        assert!(
            verify_observer_cover_classification(&site, "global", &cover, 4, &classification)
                .unwrap()
        );
    }
    #[test]
    fn complete_assignment_families_satisfy_the_cover_sheaf_law() {
        let mut site = equality_site();
        site.presentations
            .get_mut("global")
            .unwrap()
            .admissible_reports
            .extend([
                report(&[("x", "zero"), ("y", "one")]),
                report(&[("x", "one"), ("y", "zero")]),
            ]);
        let cover = vec!["x-chart".into(), "y-chart".into()];
        assert!(
            classify_observer_cover(&site, "global", &cover, 4)
                .unwrap()
                .classification
                .is_sheaf_cover
        );
    }
    #[test]
    fn replay_binds_actual_constraints_cover_and_local_reports() {
        let site = equality_site();
        let cover = vec!["x-chart".into(), "y-chart".into()];
        let receipt = solve_constrained_observer_descent(&site, "global", &cover, &[0, 1]).unwrap();
        let mut forged = receipt.clone();
        forged.fiber.global_sections = vec![0];
        forged.obstruction = None;
        assert!(
            !verify_constrained_observer_descent(&site, "global", &cover, &[0, 1], &forged)
                .unwrap()
        );
        assert!(
            !verify_constrained_observer_descent(&site, "global", &cover, &[1, 0], &receipt)
                .unwrap()
        );
        let mut changed = site.clone();
        changed
            .presentations
            .get_mut("global")
            .unwrap()
            .admissible_reports
            .push(report(&[("x", "zero"), ("y", "one")]));
        assert!(!verify_constrained_observer_descent(
            &changed,
            "global",
            &cover,
            &[0, 1],
            &receipt
        )
        .unwrap());
    }
    #[test]
    fn invalid_report_families_do_not_become_presheaves() {
        let mut site = equality_site();
        site.presentations
            .get_mut("x-chart")
            .unwrap()
            .admissible_reports
            .pop();
        assert!(matches!(
            site.validate(),
            Err(ObserverSiteError::RestrictionNotAdmissible { .. })
        ));
        let mut site = equality_site();
        site.presentations
            .get_mut("x-chart")
            .unwrap()
            .decoding
            .insert("off".into(), "1".into());
        assert!(matches!(
            site.validate(),
            Err(ObserverSiteError::InvalidDecoding { .. })
        ));
    }
}
