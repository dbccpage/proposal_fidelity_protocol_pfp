//! Executable reports for a declared finite selection of deduplicating admission
//! histories and continuations. This is not the nine-store passage model, a
//! closure computation, a physical carrier, or an authorization mechanism.
//! AuthorityEffect: None. See ppo/rust_crates/README.md#core-wdp-docs-native-report-runtime-md.

use crate::genesis_construction::{ConstructionError, ConstructionLimits, GenesisConstruction};
use crate::genesis_primitive_execution::{PrimitiveEvent, PrimitiveInstance};
use crate::genesis_questions::{
    Answer, History, Presentation, ProtectedQuestion, Question, QuestionLimits,
};
use core_category_theory::finite_question_family::{factor_tables, FiniteQuestionFamily};
use core_category_theory::finite_report_query::ReportQueryDecision;
use core_category_theory::finite_report_repair::{
    repair_report, replay_repair_prefix, verify_repair, RepairLimits,
};
use core_ooutwire_primitives::{
    event::Event,
    mark::{Mark, Pair},
    token::Token,
};
use core_types::AuthorityEffect;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;

pub const REQUEST_SCHEMA: &str = "core.genesis.report-request.v1";
pub const RESULT_SCHEMA: &str = "core.genesis.report-result.v1";
// The binary pins the original executable source, not a caller-supplied digest.
// The retained G01 copy is byte-identical to the retired Genesis paper source.
const SOURCE: &[u8] = include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"),
    "/../../../papers/021_recreated_demos_and_proposal_fidelity_evidence/code/native_genesis_g01/original/code/derivation/model.py"));
const OBSERVATION_SOURCE: &[u8] = include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"),
    "/../../../papers/021_recreated_demos_and_proposal_fidelity_evidence/code/native_genesis_g01/original/code/derivation/observe.py"));

pub fn source_sha256() -> String {
    let mut digest = Sha256::new();
    digest.update(b"core.genesis.source-bundle.v1\0");
    for source in [SOURCE, OBSERVATION_SOURCE] {
        digest.update((source.len() as u64).to_be_bytes());
        digest.update(source);
    }
    format!("{:x}", digest.finalize())
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct NamedHistory {
    pub id: String,
    pub events: Vec<PrimitiveEvent>,
}

/// Local indices refer to the lexicographically ordered realized profiles in
/// each proper context. At the full context they refer to original histories.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GlobalRequest {
    pub observed_columns: Vec<usize>,
    pub contexts: BTreeSet<u64>,
    pub cover: Vec<u64>,
    pub locals: Vec<usize>,
    pub fact_column: usize,
    pub work_limit: usize,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RepairAllowance {
    pub max_steps: usize,
    pub max_pair_checks: usize,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Request {
    pub schema_version: String,
    pub source_sha256: String,
    pub histories: Vec<NamedHistory>,
    pub questions: Vec<ProtectedQuestion>,
    /// First word must be empty. Only this supplied finite language is protected.
    pub continuations: Vec<NamedHistory>,
    pub report: Vec<String>,
    pub global: Option<GlobalRequest>,
    pub repair: Option<RepairAllowance>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct State {
    pub data: Vec<String>,
    pub forms: Vec<usize>,
    pub instances: Vec<PrimitiveInstance>,
    pub rules: Vec<usize>,
    pub requirements: Vec<(usize, usize)>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum Decision<R, A> {
    Decoder {
        entries: Vec<(R, A)>,
    },
    Collision {
        first: usize,
        second: usize,
        report: R,
        first_answer: A,
        second_answer: A,
    },
}

fn decision<R, A>(value: ReportQueryDecision<usize, R, A>) -> Decision<R, A> {
    match value {
        ReportQueryDecision::Factorable(c) => Decision::Decoder {
            entries: c.decoder.into_iter().collect(),
        },
        ReportQueryDecision::Collision(c) => Decision::Collision {
            first: c.first,
            second: c.second,
            report: c.report,
            first_answer: c.first_query,
            second_answer: c.second_query,
        },
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Operation {
    pub continuation: String,
    /// For each u in L: [h] -> (availability(u), profile_L(h u)),
    /// checked on every supplied h. Hence all u,v in L are replayed, even when
    /// uv is not itself in L. This does not assert closure under arbitrary words.
    pub decision: Decision<usize, Option<Vec<Answer>>>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum Fact {
    NoGlobalExtension,
    Undetermined { first: usize, second: usize },
    Unavailable,
    Certified { answer: Answer },
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GlobalResult {
    pub profiles: Vec<(u64, Vec<Vec<Answer>>)>,
    /// Complete fiber in the ORIGINAL declared history order, not quotient IDs.
    pub histories: Vec<usize>,
    pub fact: Fact,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RepairResult {
    /// Each triple is (first history, second history, separating column).
    pub steps: Vec<(usize, usize, usize)>,
    pub partitions: Vec<Vec<usize>>,
    pub ranks: Vec<usize>,
    /// Original histories and global request replayed initially and after EACH
    /// split. These results cannot acquire a source alternative by refinement.
    pub global_rechecks: Vec<Option<GlobalResult>>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ResultPacket {
    pub schema_version: String,
    pub authority_effect: AuthorityEffect,
    pub source_sha256: String,
    pub request_sha256: String,
    pub states: Vec<State>,
    /// Columns, in continuation-major order: availability, then every question.
    pub answers: Vec<Vec<Answer>>,
    pub profiles: Vec<Vec<Answer>>,
    pub class_of: Vec<usize>,
    pub report: Decision<String, Vec<Answer>>,
    pub operations: Vec<Operation>,
    pub global: Option<GlobalResult>,
    pub repair: Option<RepairResult>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, thiserror::Error)]
#[error("{code}: {detail}")]
#[serde(deny_unknown_fields)]
pub struct Refusal {
    pub code: String,
    pub detail: String,
}

fn refuse(code: &str, detail: impl std::fmt::Debug) -> Refusal {
    Refusal {
        code: code.into(),
        detail: format!("{detail:?}"),
    }
}

pub fn request_sha256(request: &Request) -> Result<String, Refusal> {
    let bytes = serde_json::to_vec(request).map_err(|e| refuse("WIRE", e))?;
    let mut digest = Sha256::new();
    digest.update(b"core.genesis.report-request.v1\0");
    digest.update(bytes);
    Ok(format!("{:x}", digest.finalize()))
}

fn native(event: &PrimitiveEvent) -> Event {
    match event {
        PrimitiveEvent::Supply { token } => Event::Supply(Token::new(token)),
        PrimitiveEvent::AdmitDatum { token } => Event::AdmitDatum(Token::new(token)),
        PrimitiveEvent::AdmitForm { arity } => Event::AdmitForm(*arity),
        PrimitiveEvent::AdmitInst { form, args } => {
            Event::AdmitInst(*form, args.iter().copied().map(Mark).collect())
        }
        PrimitiveEvent::AdmitRuleAll { form } => Event::AdmitRuleAll(*form),
        // Preserve order and malformed pairs. Pair::of would normalize/panic.
        PrimitiveEvent::Impose { i, j } => Event::Impose(Pair {
            i: Mark(*i),
            j: Mark(*j),
        }),
    }
}

fn validate_collection_bounds(request: &Request) -> Result<(), Refusal> {
    let width = request
        .continuations
        .len()
        .checked_mul(request.questions.len() + 1);
    let invalid_counts = request.histories.len() > 64
        || request.questions.len() > 15
        || request.continuations.is_empty()
        || request.continuations.len() > 8;
    let invalid_shape = width.is_none_or(|n| n > 64)
        || request.report.len() != request.histories.len()
        || !request.continuations[0].events.is_empty();
    if invalid_counts || invalid_shape {
        return Err(refuse(
            "BOUNDS",
            "64 histories/columns, 15 questions, 1..8 words starting with empty",
        ));
    }
    Ok(())
}

fn validate_continuation_ids(request: &Request) -> Result<(), Refusal> {
    let mut ids = BTreeSet::new();
    for word in &request.continuations {
        if word.id.trim().is_empty() || !ids.insert(&word.id) {
            return Err(refuse("IDENTITY", "duplicate or empty continuation id"));
        }
    }
    Ok(())
}

fn validate_words_and_events(request: &Request) -> Result<(), Refusal> {
    for word in request.histories.iter().chain(&request.continuations) {
        if word.id.len() > 128 || word.events.len() > 128 {
            return Err(refuse("BOUNDS", "history/word size"));
        }
        for event in &word.events {
            let valid = match event {
                PrimitiveEvent::Supply { token } | PrimitiveEvent::AdmitDatum { token } => {
                    token.len() <= 256
                }
                PrimitiveEvent::AdmitInst { args, .. } => args.len() <= 128,
                _ => true,
            };
            if !valid {
                return Err(refuse("BOUNDS", "event payload size"));
            }
        }
    }
    Ok(())
}

fn validate_questions_and_repair(request: &Request) -> Result<(), Refusal> {
    if request.report.iter().any(|x| x.len() > 128)
        || request.questions.iter().any(|q| q.id.len() > 128)
    {
        return Err(refuse("BOUNDS", "report/question identity size"));
    }
    for q in &request.questions {
        let bounded = match &q.question {
            Question::HasDatum(token) => token.len() <= 256,
            Question::Derivable(instance) => instance.args.len() <= 128,
            _ => true,
        };
        if !bounded {
            return Err(refuse("BOUNDS", "question payload size"));
        }
    }
    if let Some(r) = &request.repair {
        if r.max_steps > 64 || r.max_pair_checks > 1_000_000 {
            return Err(refuse("BOUNDS", "repair allowance"));
        }
    }
    Ok(())
}

fn validate(request: &Request) -> Result<(), Refusal> {
    if request.schema_version != REQUEST_SCHEMA {
        return Err(refuse("SCHEMA", "unsupported profile"));
    }
    if request.source_sha256 != source_sha256() {
        return Err(refuse(
            "SOURCE",
            "original source digest differs from compiled pin",
        ));
    }
    validate_collection_bounds(request)?;
    validate_continuation_ids(request)?;
    validate_words_and_events(request)?;
    validate_questions_and_repair(request)?;
    Ok(())
}

fn presentation(request: &Request) -> Result<Presentation, Refusal> {
    Presentation::new(
        request
            .histories
            .iter()
            .map(|h| History {
                id: h.id.clone(),
                events: h.events.iter().map(native).collect(),
            })
            .collect(),
        request.questions.clone(),
        QuestionLimits {
            max_histories: 64,
            max_questions: 15,
            max_answer_cells: 960,
            construction: ConstructionLimits {
                max_events: 384,
                ..Default::default()
            },
        },
    )
    .map_err(|e| refuse("ADMISSION", e))
}

fn extend(
    history: &GenesisConstruction,
    events: &[Event],
) -> Result<Option<GenesisConstruction>, Refusal> {
    match history.extend(events) {
        Ok(value) => Ok(Some(value)),
        Err(ConstructionError::Admission { .. } | ConstructionError::MissingLiteralRoot) => {
            Ok(None)
        }
        Err(error) => Err(refuse("REPLAY", error)),
    }
}

fn profile(
    history: &GenesisConstruction,
    words: &[Vec<Event>],
    questions: &[ProtectedQuestion],
) -> Result<Vec<Answer>, Refusal> {
    let mut row = Vec::new();
    for word in words {
        let next = extend(history, word)?;
        row.push(Answer::Boolean(next.is_some()));
        for q in questions {
            row.push(match &next {
                Some(h) => q.question.answer(h).map_err(|e| refuse("QUESTION", e))?,
                None => Answer::Unavailable,
            });
        }
    }
    Ok(row)
}

fn family(
    presentation: &Presentation,
    words: &[Vec<Event>],
) -> Result<FiniteQuestionFamily<Answer>, Refusal> {
    let rows = presentation
        .constructions()
        .iter()
        .map(|h| profile(h, words, presentation.questions()))
        .collect::<Result<_, _>>()?;
    FiniteQuestionFamily::new(words.len() * (presentation.questions().len() + 1), rows)
        .map_err(|e| refuse("FAMILY", e))
}

fn validate_global_request(
    family: &FiniteQuestionFamily<Answer>,
    request: &GlobalRequest,
) -> Result<(), Refusal> {
    let columns = &request.observed_columns;
    let invalid_columns = columns.is_empty()
        || columns.len() > 63
        || request.fact_column >= family.question_count()
        || columns.iter().copied().collect::<BTreeSet<_>>().len() != columns.len()
        || columns.iter().any(|&c| c >= family.question_count());
    let invalid_limits =
        request.contexts.len() > 32 || request.cover.len() > 32 || request.work_limit > 1_000_000;
    if invalid_columns || invalid_limits {
        return Err(refuse("GLOBAL_INPUT", "invalid columns or work allowance"));
    }
    Ok(())
}

fn resolve_global_fact(
    family: &FiniteQuestionFamily<Answer>,
    fact_column: usize,
    sections: &[usize],
) -> Fact {
    let Some(&first) = sections.first() else {
        return Fact::NoGlobalExtension;
    };
    let answer = &family.answers()[first][fact_column];
    if let Some(&second) = sections
        .iter()
        .find(|&&i| family.answers()[i][fact_column] != *answer)
    {
        Fact::Undetermined { first, second }
    } else if *answer == Answer::Unavailable {
        Fact::Unavailable
    } else {
        Fact::Certified {
            answer: answer.clone(),
        }
    }
}

fn global(
    family: &FiniteQuestionFamily<Answer>,
    request: &GlobalRequest,
) -> Result<GlobalResult, Refusal> {
    validate_global_request(family, request)?;
    let columns = &request.observed_columns;
    let observed = FiniteQuestionFamily::new(
        columns.len(),
        family
            .answers()
            .iter()
            .map(|row| columns.iter().map(|&c| row[c].clone()).collect())
            .collect(),
    )
    .map_err(|e| refuse("GLOBAL_INPUT", e))?;
    let site = observed
        .report_site(&request.contexts, request.work_limit)
        .map_err(|e| refuse("RESTRICTIONS", e))?;
    // report_site's conservative work bound dominates this finite fiber scan.
    let full = (1u64 << columns.len()) - 1;
    let fiber = site
        .presheaf()
        .descent_fiber(full, &request.cover, &request.locals)
        .map_err(|e| refuse("LOCAL_REPORTS", e))?;
    let fact = resolve_global_fact(family, request.fact_column, &fiber.global_sections);
    Ok(GlobalResult {
        profiles: site
            .profiles()
            .iter()
            .map(|(&k, v)| (k, v.clone()))
            .collect(),
        histories: fiber.global_sections,
        fact,
    })
}

fn requested_global(
    family: &FiniteQuestionFamily<Answer>,
    request: &Request,
) -> Result<Option<GlobalResult>, Refusal> {
    request
        .global
        .as_ref()
        .map(|g| global(family, g))
        .transpose()
}

fn evaluate_operations(
    presentation: &Presentation,
    words: &[Vec<Event>],
    continuations: &[NamedHistory],
    class_of: &[usize],
) -> Result<Vec<Operation>, Refusal> {
    let mut operations = Vec::new();
    for (index, word) in words.iter().enumerate() {
        let targets = presentation
            .constructions()
            .iter()
            .map(|h| {
                extend(h, word)?
                    .map(|next| profile(&next, words, presentation.questions()))
                    .transpose()
            })
            .collect::<Result<Vec<_>, Refusal>>()?;
        operations.push(Operation {
            continuation: continuations[index].id.clone(),
            decision: decision(
                factor_tables(class_of, &targets)
                    .map_err(|e| refuse("OPERATION", e))?
                    .decide(),
            ),
        });
    }
    Ok(operations)
}

fn evaluate_repair(
    request: &Request,
    family: &FiniteQuestionFamily<Answer>,
    words: &[Vec<Event>],
    allowance: &RepairAllowance,
) -> Result<RepairResult, Refusal> {
    let limits = RepairLimits {
        max_rows: 64,
        max_questions: 64,
        max_steps: allowance.max_steps,
        max_pair_checks: allowance.max_pair_checks,
    };
    let cert = repair_report(family, &request.report, limits).map_err(|e| refuse("REPAIR", e))?;
    verify_repair(family, &request.report, &cert, limits)
        .map_err(|e| refuse("REPAIR_REPLAY", e))?;
    let partitions = replay_repair_prefix(family, &request.report, &cert.steps, limits)
        .map_err(|e| refuse("REPAIR_REPLAY", e))?;
    let final_count = cert.class_of.iter().collect::<BTreeSet<_>>().len();
    let ranks = partitions
        .iter()
        .map(|p| final_count - p.iter().collect::<BTreeSet<_>>().len())
        .collect();
    let global_rechecks = partitions
        .iter()
        .map(|_| {
            // Replay the ORIGINAL source. No refined report is substituted for it.
            let original = self::presentation(request)?;
            requested_global(&self::family(&original, words)?, request)
        })
        .collect::<Result<Vec<_>, Refusal>>()?;
    Ok(RepairResult {
        steps: cert
            .steps
            .iter()
            .map(|s| (s.first, s.second, s.question))
            .collect(),
        partitions,
        ranks,
        global_rechecks,
    })
}

pub fn evaluate(request: &Request) -> Result<ResultPacket, Refusal> {
    validate(request)?;
    let presentation = presentation(request)?;
    let words: Vec<Vec<Event>> = request
        .continuations
        .iter()
        .map(|w| w.events.iter().map(native).collect())
        .collect();
    let family = family(&presentation, &words)?;
    let quotient = family.quotient();
    let report = decision(
        family
            .factor_report(&request.report)
            .map_err(|e| refuse("REPORT", e))?
            .decide(),
    );
    let operations = evaluate_operations(
        &presentation,
        &words,
        &request.continuations,
        &quotient.class_of,
    )?;
    let global_result = requested_global(&family, request)?;
    let repair = request
        .repair
        .as_ref()
        .map(|allowance| evaluate_repair(request, &family, &words, allowance))
        .transpose()?;
    let states = presentation
        .constructions()
        .iter()
        .map(|h| {
            let s = h.interpreted();
            State {
                data: s.data().to_vec(),
                forms: s.forms().to_vec(),
                instances: s.instances().iter().cloned().collect(),
                rules: s.rules().iter().copied().collect(),
                requirements: s.requirements().iter().copied().collect(),
            }
        })
        .collect();
    Ok(ResultPacket {
        schema_version: RESULT_SCHEMA.into(),
        authority_effect: AuthorityEffect::None,
        source_sha256: source_sha256(),
        request_sha256: request_sha256(request)?,
        states,
        answers: family.answers().to_vec(),
        profiles: quotient.profiles,
        class_of: quotient.class_of,
        report,
        operations,
        global: global_result,
        repair,
    })
}

/// Caller supplies the independently retained original request, not a request
/// extracted from the candidate. All native histories and global tasks rerun.
pub fn verify(expected: &Request, candidate: &ResultPacket) -> Result<(), Refusal> {
    if evaluate(expected)? != *candidate {
        return Err(refuse("CANDIDATE", "source-bound replay differs"));
    }
    Ok(())
}

// Origin: engine/crates_rs/core_wdp/src/genesis_report_runtime.rs
// Claim: urn:core:crates_rs:core-wdp:genesis-report-runtime:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests;
