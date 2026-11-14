//! A model turn as a workflow run stores it, read by the host.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:turns:v1
//!
//! Every runnable workflow keeps each model turn as a folder that holds `task.json`, the task the
//! turn was given, and `receipt.json`, the host's reading of the reply. A caller hands both files
//! over unread. The host finds the checker, the public input and the reply's task result in them,
//! judges the result itself (see [`crate::judge`]) and writes the ledger record:
//!
//! * [`witness_turn`]: the failure record of a turn whose result the judge rejects. Its id names
//!   the case by content, `c<hash>@<run>`, so the ledger can tell when a later trial reuses it.
//! * [`trial_turns`]: the trial record of a rule from pairs of turns on held-out cases. A pair
//!   counts only when both turns have the same case and their seeds are exactly what the ledger
//!   loads onto one base seed: the baseline with the admitted rules, the treated turn with the
//!   rule under trial added (see [`crate::loading`]).

use serde::Deserialize;
use serde_json::value::RawValue;
use sha2::{Digest, Sha256};

use crate::judge::{accepts, reference};
use crate::learning::{
    evidence, scored, CaseVerdict, Scored, Witnessed, HOST_REFUSAL, WRONG_RESULT,
};
use crate::ledger::{Ledger, Record};
use crate::loading::{render, rules_of};
use crate::Refusal;

const CASE_DOMAIN: &str = "pfp.operads.case.v1";

/// How many hex digits of a case's hash its name carries.
pub const CASE_DIGITS: usize = 16;

/// The fields the host reads from a turn's `task.json`.
#[derive(Deserialize)]
struct Task<'a> {
    checker: String,
    seed_prompt: String,
    #[serde(borrow)]
    input: &'a RawValue,
}

#[derive(Deserialize)]
struct Check<'a> {
    #[serde(borrow, default)]
    answer: Option<&'a RawValue>,
}

/// The fields the host reads from a turn's `receipt.json`.
#[derive(Deserialize)]
struct Receipt<'a> {
    workflow_id: String,
    #[serde(borrow, default)]
    check: Option<Check<'a>>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Turn<'a> {
    #[serde(borrow)]
    task: Task<'a>,
    #[serde(borrow)]
    receipt: Receipt<'a>,
}

#[derive(Deserialize)]
struct Move {
    op: String,
}

/// A full-slot reply names its task result and its DDC moves; a bare reply is the task result.
#[derive(Deserialize)]
struct Envelope<'a> {
    #[serde(borrow, default)]
    task_result: Option<&'a RawValue>,
    #[serde(default)]
    ddc_moves: Vec<Move>,
}

struct Reply<'a> {
    result: &'a RawValue,
    trace: String,
}

fn reply(answer: &RawValue) -> Result<Reply<'_>, Refusal> {
    if !answer.get().starts_with('{') {
        return Ok(Reply {
            result: answer,
            trace: String::new(),
        });
    }
    let envelope: Envelope = serde_json::from_str(answer.get())
        .map_err(|error| Refusal::new("BAD_TURN", format!("the stored answer: {error}")))?;
    Ok(Reply {
        result: envelope.task_result.unwrap_or(answer),
        trace: envelope
            .ddc_moves
            .iter()
            .map(|step| step.op.as_str())
            .collect(),
    })
}

impl Turn<'_> {
    fn answer(&self) -> Option<&RawValue> {
        self.receipt.check.as_ref().and_then(|check| check.answer)
    }

    /// The name of the turn's case: the checker and the integers it reads, hashed.
    fn case(&self) -> Result<String, Refusal> {
        let mut hasher = Sha256::new();
        for part in [CASE_DOMAIN, self.task.checker.as_str()] {
            hasher.update(part.as_bytes());
            hasher.update(b"\n");
        }
        for value in reference(&self.task.checker, self.task.input)?.values {
            hasher.update(value.to_string().as_bytes());
            hasher.update(b",");
        }
        let digest = hex::encode(hasher.finalize());
        Ok(format!("c{}", &digest[..CASE_DIGITS]))
    }

    /// Whether the judge accepts the turn's task result. A turn without an answer is not correct.
    fn correct(&self) -> Result<bool, Refusal> {
        match self.answer() {
            Some(answer) => accepts(&self.task.checker, self.task.input, reply(answer)?.result),
            None => Ok(false),
        }
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct WitnessTurnRequest<'a> {
    /// The caller's name for the turn, such as `run-7/agent-2`.
    run: String,
    #[serde(borrow)]
    turn: Turn<'a>,
}

/// Judge a stored turn and, if the judge rejects its task result, write its failure record.
pub fn witness_turn(text: &str) -> Result<Witnessed, Refusal> {
    let request: WitnessTurnRequest = serde_json::from_str(text)
        .map_err(|error| Refusal::new("BAD_REQUEST", error.to_string()))?;
    let turn = &request.turn;
    let case = turn.case()?;
    let Some(answer) = turn.answer() else {
        return Err(Refusal::new(
            "NO_ANSWER",
            format!("the receipt of {} holds no checked answer", request.run),
        ));
    };
    let reply = reply(answer)?;
    if accepts(&turn.task.checker, turn.task.input, reply.result)? {
        return Err(Refusal::new(
            "NOT_A_FAILURE",
            format!("the judge accepts the answer of {}", request.run),
        ));
    }
    Ok(Witnessed {
        record: Record::Failure {
            id: format!("{case}@{}", request.run),
            workflow: turn.receipt.workflow_id.clone(),
            evidence_sha256: evidence(&turn.task.checker, turn.task.input, answer),
            failure_class: WRONG_RESULT.to_owned(),
            ddc_trace: reply.trace + HOST_REFUSAL,
            run: request.run,
        },
    })
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Pair<'a> {
    #[serde(borrow)]
    baseline: Turn<'a>,
    #[serde(borrow)]
    treated: Turn<'a>,
    /// The seed both turns were loaded from.
    base_seed_prompt: String,
    /// The ledger state both turns were loaded at.
    ledger_head: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct TrialTurnsRequest<'a> {
    candidate: String,
    #[serde(borrow)]
    cases: Vec<Pair<'a>>,
}

fn mismatch(code: &'static str, case: &str, what: &str) -> Refusal {
    Refusal::new(code, format!("case {case}: {what}"))
}

impl Pair<'_> {
    /// The judge's verdicts on the pair, once the host has seen that it is a fair pair.
    fn verdict(&self, ledger: &Ledger, candidate: &str) -> Result<CaseVerdict, Refusal> {
        let id = self.baseline.case()?;
        if self.treated.case()? != id {
            return Err(mismatch(
                "PAIR_MISMATCH",
                &id,
                "the two turns are not the same case",
            ));
        }
        let then = ledger.at(&self.ledger_head)?;
        let admitted = render(&self.base_seed_prompt, then.head(), &rules_of(&then, None)?);
        if self.baseline.task.seed_prompt != admitted {
            return Err(mismatch(
                "BASELINE_SEED_MISMATCH",
                &id,
                "the baseline seed is not the base seed with the admitted rules",
            ));
        }
        let with_rule = render(
            &self.base_seed_prompt,
            then.head(),
            &rules_of(&then, Some(candidate))?,
        );
        if self.treated.task.seed_prompt != with_rule {
            return Err(mismatch(
                "TREATED_SEED_MISMATCH",
                &id,
                "the treated seed is not the base seed with the rule under trial added",
            ));
        }
        Ok(CaseVerdict {
            id,
            baseline: self.baseline.correct()?,
            treated: self.treated.correct()?,
        })
    }
}

/// Judge both turns of every held-out pair and write the trial record of the rule.
pub fn trial_turns(ledger: &str, text: &str) -> Result<Scored, Refusal> {
    let ledger = Ledger::from_lines(ledger)?;
    let request: TrialTurnsRequest = serde_json::from_str(text)
        .map_err(|error| Refusal::new("BAD_REQUEST", error.to_string()))?;
    let mut cases = Vec::new();
    for pair in &request.cases {
        cases.push(pair.verdict(&ledger, &request.candidate)?);
    }
    scored(request.candidate, cases)
}
