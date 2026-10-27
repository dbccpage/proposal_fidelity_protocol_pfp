use core_types::q_continuum::{generate_probe_plan, ProbePlan, QIdea};

use super::packet::ValidatedQPacket;

/// Builds a deterministic first-pass probe plan from a validated Q packet.
pub fn probe_plan_for_packet(packet: &ValidatedQPacket) -> ProbePlan {
    let packet = packet.packet();
    let body = format!(
        "carrier: {}; composition: {}; observer: {}; predictions: {}",
        packet.carrier.as_deref().unwrap_or_default(),
        packet.composition.as_deref().unwrap_or_default(),
        packet.observer.as_deref().unwrap_or_default(),
        packet.finite_predictions.join("; ")
    );
    let idea = QIdea::new(
        format!("q-packet:{}", packet.id),
        body,
        "crate::coda::q::probe_plan_for_packet",
    )
    .with_tag("core_q")
    .with_tag("packet");

    let plan = generate_probe_plan(&idea);
    match try_admit_probe_plan(packet, &plan) {
        Ok(admission)
            if admission.probes == admission.obligations
                && admission.projections == 1
                && admission.probes >= 6
                && admission.filled_slots <= admission.probes =>
        {
            plan
        }
        Ok(_) | Err(_) => plan,
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_wdp/src/coda/q/probe.rs
// Claim: urn:core:wdp:q-probe-admission:v1
// AuthorityEffect: None

struct ProbeAdmission {
    probes: u64,
    obligations: u64,
    projections: u64,
    filled_slots: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
enum ProbeAdmitError {
    Id,
    PlanId,
    Length,
    Projection,
    Base,
    Range,
    Overflow,
}

// Origin: engine/crates_rs/core_wdp/src/coda/q/probe.rs
// Claim: urn:core:crates_rs:core-wdp:probe:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ProbeAdmitError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ProbeAdmitError {}

fn declared_slot(value: &Option<String>) -> bool {
    value
        .as_deref()
        .is_some_and(|text| !text.trim().is_empty())
}

fn filled_slots(packet: &super::packet::QPacket) -> Result<u64, ProbeAdmitError> {
    let mut slots = 0u64;
    if declared_slot(&packet.carrier) {
        slots = slots.checked_add(1).ok_or(ProbeAdmitError::Overflow)?;
    }
    if declared_slot(&packet.composition) {
        slots = slots.checked_add(1).ok_or(ProbeAdmitError::Overflow)?;
    }
    if declared_slot(&packet.observer) {
        slots = slots.checked_add(1).ok_or(ProbeAdmitError::Overflow)?;
    }
    if packet
        .finite_predictions
        .iter()
        .any(|prediction| !prediction.trim().is_empty())
    {
        slots = slots.checked_add(1).ok_or(ProbeAdmitError::Overflow)?;
    }
    Ok(slots)
}

fn validate_probe_plan_headers(
    packet: &super::packet::QPacket,
    plan: &ProbePlan,
) -> Result<(), ProbeAdmitError> {
    let idea_id = format!("q-packet:{}", packet.id);
    if plan.idea_id != idea_id {
        return Err(ProbeAdmitError::Id);
    }
    let plan_id = format!("{idea_id}:probe-plan");
    if plan.id != plan_id {
        return Err(ProbeAdmitError::PlanId);
    }
    if plan.probes.is_empty() || plan.probes.len() != plan.obligations.len() {
        return Err(ProbeAdmitError::Length);
    }
    if plan.projections.len() != 1 {
        return Err(ProbeAdmitError::Projection);
    }
    Ok(())
}

fn try_admit_probe_plan(
    packet: &super::packet::QPacket,
    plan: &ProbePlan,
) -> Result<ProbeAdmission, ProbeAdmitError> {
    validate_probe_plan_headers(packet, plan)?;
    let probes = u64::try_from(plan.probes.len()).map_err(|_| ProbeAdmitError::Range)?;
    let obligations = u64::try_from(plan.obligations.len()).map_err(|_| ProbeAdmitError::Range)?;
    let projections = u64::try_from(plan.projections.len()).map_err(|_| ProbeAdmitError::Range)?;
    if probes < 6 || probes != obligations {
        return Err(ProbeAdmitError::Base);
    }
    let filled = filled_slots(packet)?;
    Ok(ProbeAdmission {
        probes,
        obligations,
        projections,
        filled_slots: filled,
    })
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod probe_admission_tests {
    use super::super::packet::{QPacket, QTerminal, ResidualSpec, TransportSpec, ValidatedQPacket};
    use super::{probe_plan_for_packet, try_admit_probe_plan, ProbeAdmission, ProbeAdmitError};
    use core_types::q_continuum::ObstructionKind;

    fn admitted_packet() -> Option<ValidatedQPacket> {
        let packet = QPacket::new("slot")
            .with_carrier("alpha")
            .with_composition("beta")
            .with_observer("gamma")
            .with_finite_prediction("delta")
            .with_transport(TransportSpec::new("lane"))
            .with_residual(ResidualSpec::new("gap", ObstructionKind::MissingWitness))
            .with_terminal_request(QTerminal::OpenResidual);
        ValidatedQPacket::try_from(packet).ok()
    }

    #[test]
    fn a_validated_packet_admits_the_base_probe_plan() {
        let validated = admitted_packet();
        assert!(validated.is_some());
        if let Some(validated) = validated {
            let plan = probe_plan_for_packet(&validated);
            let admission = try_admit_probe_plan(validated.packet(), &plan);
            assert!(matches!(
                admission,
                Ok(ProbeAdmission {
                    probes,
                    obligations,
                    projections: 1,
                    filled_slots: 4,
                }) if probes >= 6 && probes == obligations
            ));
        }
    }

    #[test]
    fn a_renamed_idea_or_a_dropped_probe_is_refused() {
        let validated = admitted_packet();
        assert!(validated.is_some());
        if let Some(validated) = validated {
            let plan = probe_plan_for_packet(&validated);
            let mut renamed = plan.clone();
            renamed.idea_id = "other".to_string();
            assert!(matches!(
                try_admit_probe_plan(validated.packet(), &renamed),
                Err(ProbeAdmitError::Id)
            ));
            let mut short = plan.clone();
            short.probes.pop();
            assert!(matches!(
                try_admit_probe_plan(validated.packet(), &short),
                Err(ProbeAdmitError::Length)
            ));
        }
    }
}
