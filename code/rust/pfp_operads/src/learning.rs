//! Ledger records the host writes itself: a failure it witnessed and a trial it scored.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:learning:v1
//!
//! A workflow does not tell the ledger that a reply failed, or how a rule did on a trial. It hands
//! the host the task's public input and each answer as the reply gave it, and the host judges every
//! answer itself (see [`crate::judge`]). What comes back is a record for `ledger append`, and the
//! ledger applies its own rules to it.

use serde::{Deserialize, Serialize};
use serde_json::value::RawValue;
use sha2::{Digest, Sha256};

use crate::judge::accepts;
use crate::ledger::Record;
use crate::Refusal;

/// The canon failure class of a reply whose exact task result the judge rejected.
pub const WRONG_RESULT: &str = "CounterfeitExactness";

/// The DDC letter the host adds to a failed reply's word: its own typed refusal.
pub const HOST_REFUSAL: &str = "M";

const EVIDENCE_DOMAIN: &str = "pfp.operads.failure-evidence.v1";

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct WitnessRequest<'a> {
    id: String,
    workflow: String,
    run: String,
    checker: String,
    /// The task's public input.
    #[serde(borrow)]
    case: &'a RawValue,
    /// The reply's task result, exactly as the reply gave it.
    #[serde(borrow)]
    answer: &'a RawValue,
    /// The DDC word of the reply, when it had one.
    #[serde(default)]
    reply_trace: String,
}

/// A failure the host saw for itself, as the record to append.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Witnessed {
    pub record: Record,
}

/// The SHA-256 that binds a failure record to the checker, the case and the answer it was seen on.
pub(crate) fn evidence(checker: &str, case: &RawValue, answer: &RawValue) -> String {
    let mut hasher = Sha256::new();
    for part in [EVIDENCE_DOMAIN, checker, case.get(), answer.get()] {
        hasher.update(part.as_bytes());
        hasher.update(b"\n");
    }
    hex::encode(hasher.finalize())
}

/// Judge one answer and, if the judge rejects it, write its failure record.
pub fn witness(text: &str) -> Result<Witnessed, Refusal> {
    let request: WitnessRequest = serde_json::from_str(text)
        .map_err(|error| Refusal::new("BAD_REQUEST", error.to_string()))?;
    if accepts(&request.checker, request.case, request.answer)? {
        return Err(Refusal::new(
            "NOT_A_FAILURE",
            format!("the judge accepts the answer recorded as {}", request.id),
        ));
    }
    Ok(Witnessed {
        record: Record::Failure {
            evidence_sha256: evidence(&request.checker, request.case, request.answer),
            id: request.id,
            workflow: request.workflow,
            run: request.run,
            failure_class: WRONG_RESULT.to_owned(),
            ddc_trace: request.reply_trace + HOST_REFUSAL,
        },
    })
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct TrialCase<'a> {
    id: String,
    #[serde(borrow)]
    case: &'a RawValue,
    /// The answer given without the rule.
    #[serde(borrow)]
    baseline: &'a RawValue,
    /// The answer given with the rule loaded.
    #[serde(borrow)]
    treated: &'a RawValue,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct TrialRequest<'a> {
    candidate: String,
    checker: String,
    #[serde(borrow)]
    cases: Vec<TrialCase<'a>>,
}

/// The judge's two verdicts on one held-out case.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct CaseVerdict {
    pub id: String,
    pub baseline: bool,
    pub treated: bool,
}

/// A trial the host scored, as the record to append, with the verdicts behind its counts.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Scored {
    pub record: Record,
    pub cases: Vec<CaseVerdict>,
}

fn count(cases: &[CaseVerdict], pick: fn(&CaseVerdict) -> bool) -> Result<u32, Refusal> {
    u32::try_from(cases.iter().filter(|case| pick(case)).count())
        .map_err(|_| Refusal::new("BAD_COUNT", "too many cases to count"))
}

/// Judge the baseline and the treated answer of every held-out case and write the trial record.
///
/// A clean-panel hit is a case the baseline answered correctly and the treated run did not: the
/// rule broke something that worked.
pub fn trial(text: &str) -> Result<Scored, Refusal> {
    let request: TrialRequest = serde_json::from_str(text)
        .map_err(|error| Refusal::new("BAD_REQUEST", error.to_string()))?;
    let mut cases = Vec::new();
    for case in &request.cases {
        cases.push(CaseVerdict {
            id: case.id.clone(),
            baseline: accepts(&request.checker, case.case, case.baseline)?,
            treated: accepts(&request.checker, case.case, case.treated)?,
        });
    }
    scored(request.candidate, cases)
}

/// The trial record of a rule, counted from the judge's verdicts on its held-out cases.
pub(crate) fn scored(candidate: String, cases: Vec<CaseVerdict>) -> Result<Scored, Refusal> {
    Ok(Scored {
        record: Record::Trial {
            candidate,
            held_out: cases.iter().map(|case| case.id.clone()).collect(),
            baseline_correct: count(&cases, |case| case.baseline)?,
            treated_correct: count(&cases, |case| case.treated)?,
            clean_panel_hits: count(&cases, |case| case.baseline && !case.treated)?,
        },
        cases,
    })
}
