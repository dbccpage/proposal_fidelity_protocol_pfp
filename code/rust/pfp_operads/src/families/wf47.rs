//! WF47, resumable bounded frontier search: a sign-gauge search in fixed batches, each batch a
//! sealed checkpoint, resumed only by replaying the chain from its start.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf47:v1
//!
//! The task is a graph with a sign, 1 or -1, on every edge. A gauge gives every vertex a sign
//! so that each edge's sign is the product of the signs at its ends. Candidates are numbered:
//! the first vertex of `basis` is +1, and the bits of the number, highest first, say which of
//! the other basis vertices are -1. Candidates are tried in order, `batch` at a time.
//!
//! A reply is a chain of checkpoints, one per batch from the first. The host recomputes every
//! batch itself and refuses the chain at the first rule it breaks, in this order: it starts at
//! index 0; indices are contiguous; it extends the chain of the session before, unchanged; every
//! record carries the digest of the presentation; every seal is the hash of the seal before it
//! and the record; batches are the host's, and no record follows the batch that tries the last
//! candidate; the spend is the candidates tried so far; status and gauge are the host's;
//! nothing follows a batch that found a gauge; and the candidates new to this session are
//! within `session_evals`.
//!
//! The run is certified as `GAUGE_VERIFIED` when the last batch found a gauge. When every
//! candidate was tried and none is a gauge, some fundamental cycle has an odd number of -1
//! edges, and the run ends as the typed refusal `RESTRICTED_OBSTRUCTION` naming those cycles.
//! A search that stops before either is refused as `SEARCH_INCOMPLETE`.
//!
//! Task: `edges`, a nonempty list of pairs on vertices `0..n-1`, n at most 16; `signs`, 1 or
//! -1 per edge; `basis`, the vertices in some order; `representation`, any value; and `batch`,
//! `max_sessions` (at most 64) and `session_evals`, positive exact integers.

use num_bigint::BigInt;
use num_traits::{One, Signed};

use crate::datum::Datum;

use super::cochain::{self, Named};
use super::{no_reply, refused, sha256_hex, typed_refusal, Checks, Family, Run, Stop, Verdict};

/// The most vertices a task may have. The host tries up to 2^(n-1) candidates itself.
pub const MAX_VERTICES: usize = 16;

/// The most sessions a task may allow.
pub const MAX_SESSIONS: usize = 64;

pub const FAMILY: Family = Family {
    workflow: "WF47",
    name: "Resumable bounded frontier search",
    host_check: "sign_gauge_checkpoint_chain",
    validate,
    walk,
};

struct Search {
    named: Named,
    /// Whether each edge's sign is -1.
    negative: Vec<bool>,
    /// The graph's number of each basis vertex, in basis order.
    basis: Vec<usize>,
    /// Candidates per batch, never more than there are candidates.
    batch: usize,
    sessions: usize,
    session_evals: BigInt,
    /// The digest of the presentation: edges, signs, basis and representation.
    key: String,
}

/// What the host finds for one batch.
#[derive(Debug, Clone, PartialEq, Eq)]
struct Batch {
    start: usize,
    end: usize,
    /// The first gauge in the batch, when there is one.
    gauge: Option<usize>,
}

fn positive<'t>(task: &'t Datum, key: &str) -> Result<&'t BigInt, String> {
    task.get(key)
        .and_then(Datum::as_int)
        .filter(|stated| stated.is_positive())
        .ok_or_else(|| format!("{key} must be a positive exact int"))
}

fn search(task: &Datum) -> Result<Search, String> {
    let named = cochain::graph(task)?;
    let vertices = named.graph.names().len();
    if vertices > MAX_VERTICES {
        return Err(format!("at most {MAX_VERTICES} vertices"));
    }
    let sign = |sign: &Datum| match sign.as_int()? {
        sign if sign.is_one() => Some(false),
        sign if *sign == BigInt::from(-1) => Some(true),
        _ => None,
    };
    let negative: Vec<bool> = task
        .get("signs")
        .and_then(Datum::as_list)
        .filter(|signs| signs.len() == named.graph.edges().len())
        .and_then(|signs| signs.iter().map(sign).collect())
        .ok_or("signs must be 1 or -1, one per edge")?;
    let basis: Vec<usize> = task
        .get("basis")
        .and_then(Datum::as_list)
        .and_then(|basis| basis.iter().map(|name| named.vertex(name)).collect())
        .ok_or("basis must list every vertex once")?;
    let mut listed = basis.clone();
    listed.sort_unstable();
    if listed != (0..vertices).collect::<Vec<_>>() {
        return Err("basis must list every vertex once".to_owned());
    }
    let part = |key: &str| task.get(key).cloned();
    let presentation = Datum::map([
        ("edges", part("edges").unwrap_or(Datum::Null)),
        ("signs", part("signs").unwrap_or(Datum::Null)),
        ("basis", part("basis").unwrap_or(Datum::Null)),
        (
            "representation",
            part("representation").ok_or("representation required")?,
        ),
    ]);
    let total = 1usize << (vertices - 1);
    let batch = positive(task, "batch")?;
    let sessions = positive(task, "max_sessions")?;
    Ok(Search {
        negative,
        basis,
        batch: usize::try_from(batch).map_or(total, |batch| batch.min(total)),
        sessions: usize::try_from(sessions)
            .ok()
            .filter(|&sessions| sessions <= MAX_SESSIONS)
            .ok_or(format!("max_sessions must be at most {MAX_SESSIONS}"))?,
        session_evals: positive(task, "session_evals")?.clone(),
        key: sha256_hex(&presentation.canonical()),
        named,
    })
}

fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    search(task).map(|_| ())
}

impl Search {
    /// The number of candidates: every sign pattern with the first basis vertex at +1.
    fn total(&self) -> usize {
        1 << (self.basis.len() - 1)
    }

    /// Whether candidate `number` gives every edge the product of the signs at its ends.
    fn is_gauge(&self, number: usize) -> bool {
        let bits = self.basis.len() - 1;
        let mut minus = vec![false; self.basis.len()];
        for (place, &vertex) in self.basis.iter().skip(1).enumerate() {
            if let Some(sign) = minus.get_mut(vertex) {
                *sign = (number >> (bits - 1 - place)) & 1 == 1;
            }
        }
        let at = |vertex: usize| minus.get(vertex).copied().unwrap_or(false);
        let edges = self.named.graph.edges().iter().zip(&self.negative);
        edges
            .into_iter()
            .all(|(&(from, to), &negative)| (at(from) != at(to)) == negative)
    }

    /// The batch that starts at candidate `start`.
    fn batch(&self, start: usize) -> Batch {
        let end = start.saturating_add(self.batch).min(self.total());
        Batch {
            start,
            end,
            gauge: (start..end).find(|&number| self.is_gauge(number)),
        }
    }

    /// The batches a chain of this many records must be, one after another from candidate 0.
    fn batches(&self, records: usize) -> Vec<Batch> {
        let mut batches: Vec<Batch> = Vec::with_capacity(records);
        for _ in 0..records {
            let start = batches.last().map_or(0, |before| before.end);
            batches.push(self.batch(start));
        }
        batches
    }

    /// The seal of each record: the hash of the seal before it and the record without its seal,
    /// starting from the hash of the presentation key.
    fn seals(&self, chain: &[Datum]) -> Vec<Datum> {
        let mut seal = sha256_hex(&Datum::text(self.key.as_str()).canonical());
        let sealed = chain.iter().map(|record| {
            let body = match record {
                Datum::Map(fields) => fields
                    .iter()
                    .filter(|(field, _)| field.as_str() != "seal")
                    .map(|(field, value)| (field.clone(), value.clone()))
                    .collect(),
                _ => Default::default(),
            };
            seal = sha256_hex(&format!("{seal}{}", Datum::Map(body).canonical()));
            Datum::text(seal.as_str())
        });
        sealed.collect()
    }

    /// The first custody rule a chain breaks, if any.
    fn broken(&self, chain: &[Datum], wants: &[Batch], prior: &[Datum]) -> Option<&'static str> {
        let field = |record: &Datum, key: &str| record.get(key).cloned().unwrap_or(Datum::Null);
        let pairs = || chain.iter().zip(wants);
        let every = |key: &str, value: &dyn Fn(usize, &Batch) -> Datum| {
            pairs()
                .enumerate()
                .all(|(index, (record, want))| field(record, key) == value(index, want))
        };
        let status = |want: &Batch| match want.gauge {
            Some(_) => "verified",
            None => "unknown",
        };
        let gauge = |want: &Batch| want.gauge.map_or(Datum::Null, Datum::from);
        let before = wants.len().saturating_sub(1);
        let resumed = prior.len().checked_sub(1).and_then(|at| wants.get(at));
        let done = resumed.map_or(0, |batch| batch.end);
        let new = wants.last().map_or(0, |last| last.end).saturating_sub(done);
        let rules: [(&'static str, &dyn Fn() -> bool); 10] = [
            ("RESUME_NOT_REPLAYED_FROM_ZERO", &|| {
                chain
                    .first()
                    .is_some_and(|first| field(first, "index") == Datum::from(0usize))
            }),
            ("CHAIN_NOT_CONTIGUOUS", &|| {
                every("index", &|index, _| Datum::from(index))
            }),
            ("RESUME_DIVERGES_FROM_CHECKPOINT", &|| {
                prior.is_empty() || (chain.len() > prior.len() && chain.starts_with(prior))
            }),
            ("PRESENTATION_KEY_CHANGED", &|| {
                every("key", &|_, _| Datum::text(self.key.as_str()))
            }),
            ("SEAL_MISMATCH", &|| {
                let seals = self.seals(chain);
                every("seal", &|index, _| {
                    seals.get(index).cloned().unwrap_or(Datum::Null)
                })
            }),
            ("BATCH_NOT_LEXICOGRAPHIC", &|| {
                wants.iter().all(|want| want.start < want.end)
                    && every("start", &|_, want| Datum::from(want.start))
                    && every("end", &|_, want| Datum::from(want.end))
            }),
            ("BUDGET_RESET", &|| {
                every("spent", &|_, want| Datum::from(want.end))
            }),
            ("STATUS_NOT_RECOMPUTED", &|| {
                every("status", &|_, want| Datum::from(status(want)))
                    && every("gauge", &|_, want| gauge(want))
            }),
            ("SEARCH_CONTINUED_AFTER_VERIFIED", &|| {
                wants.iter().take(before).all(|want| want.gauge.is_none())
            }),
            ("SESSION_BUDGET_EXCEEDED", &|| {
                BigInt::from(new) <= self.session_evals
            }),
        ];
        rules
            .iter()
            .find(|(_, holds)| !holds())
            .map(|(code, _)| *code)
    }

    /// The numbers of the fundamental cycles with an odd number of -1 edges.
    fn frustrated(&self) -> Vec<usize> {
        let cycles = self.named.graph.fundamental_cycles();
        let odd = |cycle: &Vec<(usize, i8)>| {
            let minus = cycle
                .iter()
                .filter(|step| self.negative.get(step.0) == Some(&true));
            minus.count() % 2 == 1
        };
        (0..cycles.len())
            .filter(|&number| cycles.get(number).is_some_and(odd))
            .collect()
    }
}

/// The chain of checkpoints a reply gives.
fn chain(reply: &Datum) -> Result<&[Datum], String> {
    reply
        .get("checkpoints")
        .and_then(Datum::as_list)
        .filter(|chain| !chain.is_empty() && chain.iter().all(Datum::is_map))
        .ok_or_else(|| "checkpoints must be a nonempty list of records".to_owned())
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let search = search(run.task).map_err(Stop::Malformed)?;
    let mut prior: &[Datum] = &[];
    let mut last: Option<Batch> = None;
    for session in 0..search.sessions {
        let (stage, note) = match prior.last() {
            None => ("search".to_owned(), String::new()),
            Some(record) => {
                let seal = record.get("seal").and_then(Datum::as_text).unwrap_or("");
                let note = format!("\nResume after seal {seal} at index {}.", prior.len());
                (format!("resume:{session}"), note)
            }
        };
        let Some(reply) = run.ask(&stage, run.prompt() + &note)? else {
            break;
        };
        let chain = chain(reply).map_err(Stop::Malformed)?;
        let wants = search.batches(chain.len());
        if let Some(code) = search.broken(chain, &wants, prior) {
            checks.record(&code.to_lowercase(), false, &Datum::List(chain.to_vec()));
            let detail = Datum::map([("session", Datum::from(session))]);
            return Ok(refused(code, detail));
        }
        prior = chain;
        last = wants.last().cloned();
        if last
            .as_ref()
            .is_some_and(|last| last.gauge.is_some() || last.end == search.total())
        {
            break;
        }
    }
    let (Some(last), Some(record)) = (last, prior.last()) else {
        return Ok(no_reply());
    };
    let seal = record.get("seal").cloned().unwrap_or(Datum::Null);
    checks.record("checkpoint_chain_valid", true, &seal);
    let checkpoints = ("checkpoints", Datum::from(prior.len()));
    if let Some(gauge) = last.gauge {
        let found = Datum::from(gauge);
        checks.record("gauge_balances_every_edge", search.is_gauge(gauge), &found);
        return Ok(checks.judge(
            "GAUGE_VERIFIED",
            Datum::map([("gauge", found), checkpoints]),
        ));
    }
    if last.end < search.total() {
        let detail = Datum::map([("suffix", Datum::from(last.end)), checkpoints]);
        return Ok(refused("SEARCH_INCOMPLETE", detail));
    }
    let odd = search.frustrated();
    let listed = Datum::from(odd.clone());
    if !checks.record("frustrated_cycle_witness", !odd.is_empty(), &listed) {
        return Ok(refused("EXHAUSTED_WITHOUT_OBSTRUCTION", Datum::map([])));
    }
    let detail = Datum::map([("frustrated_cycles", listed), checkpoints]);
    Ok(typed_refusal("RESTRICTED_OBSTRUCTION", detail))
}
