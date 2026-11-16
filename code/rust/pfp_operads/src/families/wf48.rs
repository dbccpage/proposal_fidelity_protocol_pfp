//! WF48, commit-reveal with a hostile mutation gate: an artifact is committed before it is
//! revealed, and two independent checkers must accept it and reject every hostile edit of it.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf48:v1
//!
//! The task is a public cochain, `edges` and `c`, and a `judge_manifest` that names two
//! `checkers`. The manifest is committed: `manifest_commitment` is the digest of a salt the host
//! keeps sealed, a zero byte and the canonical form of the manifest. The three registered
//! checkers each take a potential, one exact integer per vertex:
//!
//! * `residual.v1`: the cochain less the potential's coboundary is zero.
//! * `tree_integration.v1`: every cycle of the cochain sums to zero and the potential agrees
//!   with the integral of the cochain along a spanning forest, up to the value at vertex `0`.
//! * `length_only.v1`: the potential has a value for each vertex. It checks nothing else, which
//!   is why a manifest that names it cannot be certified.
//!
//! The host records `manifest_commitment_matches` and `two_independent_registered_checkers`
//! (two different names, both registered). If either fails the run ends there, refused under
//! the name of the first that failed, with nothing asked. Otherwise the proposer is asked for
//! a `commitment` alone, then for the reveal, an `artifact` (a potential) and the `salt` it
//! used. The commitment of a reveal is the digest of its salt, a zero byte and the canonical form
//! of its artifact.
//!
//! * `reveal_matches_commitment`: the commitment of the reveal is the one given. Refused as
//!   `ARTIFACT_CHANGED_AFTER_COMMIT` when not.
//! * for each checker in the manifest, in order, `NAME:accepts_artifact_and_gauge` (the checker
//!   accepts the artifact and the artifact with every entry raised by three) and
//!   `NAME:kills_every_mutant` (it rejects every mutant). The mutants are the artifact with each
//!   entry raised by one and lowered by one, with each unequal neighbouring pair swapped, and
//!   with its last entry left off. A potential of the wrong length is rejected.
//!
//! All held, the run is certified as `COMMIT_REVEAL_CERTIFIED` with `kills`, the number of
//! mutants each checker rejected out of the number tried.

use std::collections::BTreeMap;

use num_bigint::BigInt;
use num_traits::Zero;

use crate::datum::Datum;
use crate::exact::Rational;

use super::cochain::{self, Named};
use super::reading::{integers, integers_under, object};
use super::{refused, sha256_hex, Checks, Family, Run, Stop, Verdict, CERTIFIED_CODE, NO_REPLY};

pub const FAMILY: Family = Family {
    workflow: "WF48",
    name: "Commit-reveal with a hostile mutation gate",
    host_check: "dual_checker_mutation_suite",
    validate,
    walk,
};

/// What a task fixes.
struct Judge<'t> {
    named: Named,
    values: Vec<Rational>,
    manifest: &'t Datum,
    commitment: &'t str,
    checkers: &'t [Datum],
}

fn judge_of(task: &Datum) -> Result<Judge<'_>, String> {
    let named = cochain::graph(task)?;
    let c = task
        .get("c")
        .and_then(integers)
        .filter(|c| c.len() == named.graph.edges().len())
        .ok_or("c must be one exact integer per edge")?;
    let manifest = task
        .get("judge_manifest")
        .filter(|manifest| manifest.is_map())
        .ok_or("judge_manifest must name its checkers")?;
    let checkers = manifest
        .get("checkers")
        .and_then(Datum::as_list)
        .ok_or("judge_manifest must name its checkers")?;
    let commitment = task
        .get("manifest_commitment")
        .and_then(Datum::as_text)
        .ok_or("manifest_commitment must be text")?;
    Ok(Judge {
        named,
        values: c.into_iter().map(Rational::from_integer).collect(),
        manifest,
        commitment,
        checkers,
    })
}

fn validate(task: &Datum, sealed: &Datum) -> Result<(), String> {
    if let Some(salt) = sealed.get("manifest_salt") {
        salt.as_text().ok_or("manifest_salt must be text")?;
    }
    judge_of(task).map(|_| ())
}

/// The digest of a salt, a zero byte and the canonical form of an artifact.
fn commitment(salt: &str, artifact: &Datum) -> String {
    sha256_hex(&format!("{salt}\0{}", artifact.canonical()))
}

#[derive(Debug, Clone, Copy)]
enum Checker {
    Residual,
    TreeIntegration,
    LengthOnly,
}

fn checker(id: &Datum) -> Option<Checker> {
    match id.as_text()? {
        "residual.v1" => Some(Checker::Residual),
        "tree_integration.v1" => Some(Checker::TreeIntegration),
        "length_only.v1" => Some(Checker::LengthOnly),
        _ => None,
    }
}

/// One exact value per vertex, in vertex order, when the candidate has one for each.
fn potential(judge: &Judge, candidate: &[BigInt]) -> Option<Vec<Rational>> {
    let sized = candidate.len() == judge.named.graph.names().len();
    sized
        .then(|| judge.named.potential(&Datum::from(candidate.to_vec())).ok())
        .flatten()
}

/// Whether a checker accepts a candidate potential.
fn accepts(kind: Checker, judge: &Judge, candidate: &[BigInt]) -> bool {
    let graph = &judge.named.graph;
    match kind {
        Checker::LengthOnly => candidate.len() == graph.names().len(),
        Checker::Residual => potential(judge, candidate).is_some_and(|found| {
            let left = graph.residual(&judge.values, &found);
            left.iter().all(Zero::is_zero)
        }),
        Checker::TreeIntegration => {
            let Some(found) = potential(judge, candidate) else {
                return false;
            };
            if !graph.defect(&judge.values).is_zero() {
                return false;
            }
            let integral = graph.potential(&judge.values);
            let origin = judge.named.vertex(&Datum::from(0_usize));
            let ends = origin.and_then(|at| Some((found.get(at)?, integral.get(at)?)));
            ends.is_some_and(|(held, base)| {
                found
                    .iter()
                    .zip(&integral)
                    .all(|(here, there)| here - held == there - base)
            })
        }
    }
}

/// The hostile edits of an artifact: each entry raised and lowered by one, each unequal
/// neighbouring pair swapped, and the last entry left off.
fn mutants(artifact: &[BigInt]) -> Vec<Vec<BigInt>> {
    let mut found = Vec::new();
    for (at, value) in artifact.iter().enumerate() {
        for step in [1, -1] {
            let moved = artifact
                .iter()
                .take(at)
                .cloned()
                .chain([value + step])
                .chain(artifact.iter().skip(at + 1).cloned());
            found.push(moved.collect());
        }
    }
    for (at, pair) in artifact.windows(2).enumerate() {
        if let [left, right] = pair {
            if left != right {
                let swapped = artifact
                    .iter()
                    .take(at)
                    .cloned()
                    .chain([right.clone(), left.clone()])
                    .chain(artifact.iter().skip(at + 2).cloned());
                found.push(swapped.collect());
            }
        }
    }
    let shorter = artifact.len().saturating_sub(1);
    found.push(artifact.iter().take(shorter).cloned().collect());
    found
}

fn stopped(stage: &str) -> Verdict {
    refused(NO_REPLY, Datum::map([("stage", Datum::from(stage))]))
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let judge = judge_of(run.task).map_err(Stop::Malformed)?;
    let salt = run.sealed.get("manifest_salt").and_then(Datum::as_text);
    let named = Datum::List(judge.checkers.to_vec());
    let sealed = commitment(salt.unwrap_or(""), judge.manifest) == judge.commitment;
    checks.record("manifest_commitment_matches", sealed, &named);
    let panel: Vec<(&str, Checker)> = judge
        .checkers
        .iter()
        .filter_map(|id| Some((id.as_text()?, checker(id)?)))
        .collect();
    let two = judge.checkers.len() == 2
        && judge.checkers.first() != judge.checkers.get(1)
        && panel.len() == 2;
    checks.record("two_independent_registered_checkers", two, &named);
    if !checks.certified() {
        return Ok(checks.judge(CERTIFIED_CODE, Datum::map([])));
    }
    let prompt = format!("{}\nCommit H(salt || potential) only.", run.prompt());
    let Some(reply) = run.ask("commit", prompt)? else {
        return Ok(stopped("commit"));
    };
    let given = object(reply, "commit")?
        .get("commitment")
        .and_then(Datum::as_text)
        .ok_or_else(|| Stop::Malformed("commitment must be a hex string".to_owned()))?
        .to_owned();
    let prompt = format!(
        "{}\nCommitment recorded: {given}\nReveal now.",
        run.prompt()
    );
    let Some(reply) = run.ask("reveal", prompt)? else {
        return Ok(stopped("reveal"));
    };
    let reply = object(reply, "reveal")?;
    let artifact = integers_under(reply, "artifact")?;
    let revealed = reply
        .get("salt")
        .and_then(Datum::as_text)
        .ok_or_else(|| Stop::Malformed("salt must be a string".to_owned()))?;
    let reveal = commitment(revealed, &Datum::from(artifact.clone())) == given;
    if !checks.record("reveal_matches_commitment", reveal, &Datum::text(given)) {
        return Ok(refused("ARTIFACT_CHANGED_AFTER_COMMIT", Datum::map([])));
    }
    let gauge: Vec<BigInt> = artifact.iter().map(|value| value + 3).collect();
    let valid = [artifact.clone(), gauge];
    let hostile = mutants(&artifact);
    let mut kills: BTreeMap<String, Datum> = BTreeMap::new();
    for (id, kind) in panel {
        let rejected = valid
            .iter()
            .filter(|case| !accepts(kind, &judge, case))
            .count();
        let killed = hostile
            .iter()
            .filter(|case| !accepts(kind, &judge, case))
            .count();
        let score = Datum::text(format!("{killed}/{}", hostile.len()));
        checks.record(
            &format!("{id}:accepts_artifact_and_gauge"),
            rejected == 0,
            &score,
        );
        checks.record(
            &format!("{id}:kills_every_mutant"),
            killed == hostile.len(),
            &score,
        );
        kills.insert(id.to_owned(), score);
    }
    Ok(checks.judge(
        "COMMIT_REVEAL_CERTIFIED",
        Datum::map([("kills", Datum::Map(kills))]),
    ))
}
