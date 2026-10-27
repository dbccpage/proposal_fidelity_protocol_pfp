//! Host-side byte binding, independent of the frozen single-artifact parity cases.
use core_adversary::stage::ddc::DdcStep;
use core_adversary::stage::emission::{Clock, DdcSink, EmitterSuite};
use core_adversary::stage::packets::CandidateProposal;
use core_adversary::stage::ports::Refusal;
use core_adversary::authorization::AuthorizationTime;
use core_adversary::candidate_checks::{execute_candidate_checks, CandidateChecksInput};
use core_adversary::checker_ports::{CandidateCheckRequest, CandidateCheckerPort};
use core_adversary::evidence::{sha256_ref, CandidateCheck, CandidateCheckInput, CheckerVerdict};
use serde_json::json;
use std::collections::BTreeMap;

const PAYLOAD: &[u8] = b"candidate-a";
const OTHER_ARTIFACT: &[u8] = b"candidate-b";
const VERDICTS: [CheckerVerdict; 3] = [
    CheckerVerdict::Accepted,
    CheckerVerdict::Rejected,
    CheckerVerdict::NotMeasured,
];

struct FrozenClock;
impl Clock for FrozenClock {
    fn timestamp_utc(&self) -> String {
        "2026-10-05T12:00:00Z".into()
    }
}

struct PinnedChecker {
    verdict: CheckerVerdict,
    digest: String,
    calls: usize,
}
impl CandidateCheckerPort for PinnedChecker {
    fn check_candidate(
        &mut self,
        request: &CandidateCheckRequest<'_>,
    ) -> Result<CandidateCheck, Refusal> {
        self.calls += 1;
        let receipt = serde_json::to_vec(&json!({
            "verdict": self.verdict,
            "candidate_content_sha256": self.digest,
        }))
        .map_err(|error| Refusal::new("TEST_RECEIPT_INVALID", error.to_string()))?;
        let measured = self.verdict != CheckerVerdict::NotMeasured;
        CandidateCheck::new(CandidateCheckInput {
            verdict: self.verdict,
            candidate_id: request.candidate_id.into(),
            candidate_content_sha256: self.digest.clone(),
            checker_id: "custody-test-checker".into(),
            checker_receipt_sha256: measured.then(|| sha256_ref(&receipt)),
            checker_receipt_bytes: if measured { receipt } else { Vec::new() },
            reason: "injected verdict for byte-binding regression".into(),
        })
    }
}

#[derive(Default)]
struct CountingSink {
    calls: usize,
}
impl DdcSink for CountingSink {
    fn record_step(&mut self, _: &DdcStep) -> Result<String, Refusal> {
        self.calls += 1;
        Ok("recorded".into())
    }
}

fn candidate(artifacts: &[&[u8]]) -> Result<CandidateProposal, serde_json::Error> {
    serde_json::from_value(json!({
        "producer_agent_id": "seat_gauge_breaker",
        "work_packet_id": sha256_ref(b"packet"),
        "artifact_refs": artifacts.iter().map(|bytes| sha256_ref(bytes)).collect::<Vec<_>>(),
        "prediction_receipt_id": sha256_ref(b"prediction"),
        "nonclaims": ["proposal only"],
        "authority_effect": "None",
        "schema_version": "core.oeas.candidate-proposal.v1",
    }))
}

fn execute(
    candidate: &CandidateProposal,
    payload: &[u8],
    checker: Option<&mut dyn CandidateCheckerPort>,
    sink: &mut CountingSink,
) -> Result<BTreeMap<String, CandidateCheck>, Refusal> {
    let payloads = BTreeMap::from([(candidate.candidate_id().clone(), payload.to_vec())]);
    let carrier_hash = sha256_ref(b"measured-carrier");
    let mut emitters = EmitterSuite {
        ddc: Some(sink),
        ..EmitterSuite::default()
    };
    execute_candidate_checks(
        checker,
        &CandidateChecksInput {
            run_key: "custody-test",
            objective: "bind the check to the submitted bytes",
            candidates: std::slice::from_ref(candidate),
            candidate_payloads: &payloads,
            carrier_context: None,
            measurement: None,
            carrier_state_hash: Some(&carrier_hash),
            now_utc: "2026-10-05T12:00:00Z",
        },
        Some(&mut emitters),
        &AuthorizationTime {
            event_clock: &FrozenClock,
            dda_timestamp: "2026-10-05 12:00:00 UTC",
        },
    )
}

#[test]
fn uncommitted_payload_is_refused_before_checker_or_emission(
) -> Result<(), Box<dyn std::error::Error>> {
    let candidate = candidate(&[PAYLOAD])?;
    let mut checker = PinnedChecker {
        verdict: CheckerVerdict::Accepted,
        digest: sha256_ref(PAYLOAD),
        calls: 0,
    };
    let mut sink = CountingSink::default();
    let error = execute(&candidate, b"mutated bytes", Some(&mut checker), &mut sink)
        .expect_err("uncommitted bytes must not reach the checker");
    assert_eq!(error.code, "ADVERSARY_CANDIDATE_PAYLOAD_MISMATCH");
    assert_eq!(checker.calls, 0);
    assert_eq!(sink.calls, 0);
    Ok(())
}

#[test]
fn multi_artifact_verdict_must_name_the_bytes_submitted() -> Result<(), Box<dyn std::error::Error>>
{
    let candidate = candidate(&[PAYLOAD, OTHER_ARTIFACT])?;
    for verdict in VERDICTS {
        let mut checker = PinnedChecker {
            verdict,
            digest: sha256_ref(OTHER_ARTIFACT),
            calls: 0,
        };
        let mut sink = CountingSink::default();
        let error = execute(&candidate, PAYLOAD, Some(&mut checker), &mut sink)
            .expect_err("a referenced artifact is not necessarily the submitted artifact");
        assert_eq!(error.code, "ADVERSARY_CHECKER_BINDING_MISMATCH");
        assert_eq!(checker.calls, 1);
        assert_eq!(sink.calls, 0);
    }
    Ok(())
}

#[test]
fn multi_artifact_verdict_for_submitted_bytes_is_retained() -> Result<(), Box<dyn std::error::Error>>
{
    let candidate = candidate(&[PAYLOAD, OTHER_ARTIFACT])?;
    for verdict in VERDICTS {
        let mut checker = PinnedChecker {
            verdict,
            digest: sha256_ref(PAYLOAD),
            calls: 0,
        };
        let mut sink = CountingSink::default();
        let checks = execute(&candidate, PAYLOAD, Some(&mut checker), &mut sink)?;
        let check = checks
            .get(candidate.candidate_id())
            .ok_or("missing check")?;
        assert_eq!(checks.len(), 1);
        assert_eq!(check.verdict(), verdict);
        assert_eq!(check.candidate_content_sha256(), sha256_ref(PAYLOAD));
        assert_eq!(checker.calls, 1);
        assert_eq!(sink.calls, 1);
    }
    Ok(())
}

#[test]
fn null_checker_still_requires_committed_bytes() -> Result<(), Box<dyn std::error::Error>> {
    let candidate = candidate(&[PAYLOAD])?;
    let mut sink = CountingSink::default();
    let error = execute(&candidate, b"mutated bytes", None, &mut sink)
        .expect_err("disabling the checker does not disable payload custody");
    assert_eq!(error.code, "ADVERSARY_CANDIDATE_PAYLOAD_MISMATCH");
    assert_eq!(sink.calls, 0);
    let checks = execute(&candidate, PAYLOAD, None, &mut sink)?;
    let check = checks
        .get(candidate.candidate_id())
        .ok_or("missing check")?;
    assert_eq!(check.verdict(), CheckerVerdict::NotMeasured);
    assert_eq!(sink.calls, 1);
    Ok(())
}

// Origin: engine/crates_rs/tests/core_adversary/candidate_check_custody.rs
// Claim: urn:core:crates_rs:tests:candidate-check-custody:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
