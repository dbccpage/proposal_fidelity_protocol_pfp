//! WF39, authority firewall gate: accept a reply only when every guard of a fixed vector
//! passes.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf39:v1
//!
//! The task fixes a public cochain, `edges` and `c`, a `nonce` and the `registered_verifiers`.
//! The reply is a `payload`, which may carry only the witness `phi` (a potential, one exact
//! integer per vertex), and a `receipt`. The host replays the one verifier it has,
//! `exact.cochain_residual.v1`, on the task's own edges and values with the reply's `phi`, and
//! records, in this order:
//!
//! * `payload_bound_to_task`: the payload names only `edges`, `c` and `phi`, and any `edges`
//!   or `c` in it equal the task's. Refused as `PAYLOAD_NOT_BOUND_TO_TASK` when not.
//! * `authority_effect_none`: the receipt's `authority_effect` is `None` and it has no field
//!   beyond `authority_effect`, `verifier_id`, `payload_sha256`, `replay_sha256`, `claimed` and
//!   `nonce`. Refused as `AUTHORITY_ESCALATION`, naming the extra fields, when not.
//! * `witness_verifier_registered`: the receipt names the verifier, and the task registers it.
//! * `witness_bound_to_payload`: `payload_sha256` is the digest of the canonical form of
//!   `{edges, c, phi}`.
//! * `replay_hash`: `replay_sha256` is the digest of the replay, `{defect, residual}`.
//! * `replay_match`: `claimed` is the replay.
//! * `zero_defect`: the replay has defect zero.
//! * `fresh_nonce`: the receipt's `nonce` is the task's.
//!
//! The last six are recorded whether or not an earlier one held; without a registered verifier
//! there is no replay and the three that read it fail. The run is certified as
//! `ALL_GUARDS_PASS`; a refusal names the failed guards in `residual_evidence`.

use num_bigint::BigInt;
use num_traits::{Signed, Zero};

use crate::datum::Datum;
use crate::exact::Rational;

use super::cochain::{self, Named};
use super::reading::integers;
use super::{no_reply, refused, require, sha256_hex, Checks, Family, Run, Stop, Verdict};

pub const FAMILY: Family = Family {
    workflow: "WF39",
    name: "Authority firewall gate",
    host_check: "authority_guard_vector",
    validate,
    walk,
};

/// The one verifier the host can replay.
pub const VERIFIER: &str = "exact.cochain_residual.v1";

/// What a payload may name.
const PAYLOAD_FIELDS: [&str; 3] = ["edges", "c", "phi"];

/// What a receipt may name.
const RECEIPT_FIELDS: [&str; 6] = [
    "authority_effect",
    "verifier_id",
    "payload_sha256",
    "replay_sha256",
    "claimed",
    "nonce",
];

/// The effect a receipt may claim.
const NO_AUTHORITY: &str = "None";

/// What a task fixes.
struct Gate<'t> {
    named: Named,
    c: Vec<BigInt>,
    nonce: &'t Datum,
    registers_verifier: bool,
}

fn gate(task: &Datum) -> Result<Gate<'_>, String> {
    let nonce = task.get("nonce").filter(|nonce| nonce.as_text().is_some());
    let registered = task
        .get("registered_verifiers")
        .and_then(Datum::as_list)
        .ok_or("nonce and registered_verifiers required")?;
    let named = cochain::graph(task)?;
    let c = task
        .get("c")
        .and_then(integers)
        .filter(|c| c.len() == named.graph.edges().len())
        .ok_or("c must be one exact integer per edge")?;
    Ok(Gate {
        named,
        c,
        nonce: nonce.ok_or("nonce and registered_verifiers required")?,
        registers_verifier: registered
            .iter()
            .any(|entry| entry.as_text() == Some(VERIFIER)),
    })
}

fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    gate(task).map(|_| ())
}

fn names(listed: &[&str]) -> Datum {
    Datum::List(listed.iter().map(|name| Datum::from(*name)).collect())
}

/// The residual of the cochain against the payload's potential, and the sum of its sizes.
fn replay(gate: &Gate, phi: &Datum) -> Result<Datum, Stop> {
    let potential = integers(phi)
        .ok_or_else(|| Stop::Malformed("phi must be a list of exact integers".to_owned()))?;
    require(
        potential.len() == gate.named.graph.names().len(),
        "phi needs one integer per vertex 0..n-1",
    )?;
    let values: Vec<Rational> = gate.c.iter().cloned().map(Rational::from_integer).collect();
    let by_vertex = gate.named.potential(phi).map_err(Stop::Malformed)?;
    let residual: Vec<BigInt> = gate
        .named
        .graph
        .residual(&values, &by_vertex)
        .iter()
        .map(|entry| entry.numer().clone())
        .collect();
    let defect: BigInt = residual.iter().map(Signed::abs).sum();
    Ok(Datum::map([
        ("residual", Datum::from(residual)),
        ("defect", Datum::Int(defect)),
    ]))
}

/// The text of a field, when it is text.
fn text<'d>(object: &'d Datum, key: &str) -> Option<&'d str> {
    object.get(key).and_then(Datum::as_text)
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let gate = gate(run.task).map_err(Stop::Malformed)?;
    let Some(reply) = run.ask("solve", run.prompt())? else {
        return Ok(no_reply());
    };
    let (payload, receipt) = match (reply.get("payload"), reply.get("receipt")) {
        (Some(payload), Some(receipt)) if payload.is_map() && receipt.is_map() => {
            (payload, receipt)
        }
        _ => {
            return Err(Stop::Malformed(
                "payload and receipt objects required".to_owned(),
            ))
        }
    };
    let phi = payload.get("phi").cloned().unwrap_or(Datum::Null);
    let witnessed = Datum::map([
        (
            "edges",
            run.task.get("edges").cloned().unwrap_or(Datum::Null),
        ),
        ("c", run.task.get("c").cloned().unwrap_or(Datum::Null)),
        ("phi", phi.clone()),
    ]);
    let public = |key: &str| {
        payload
            .get(key)
            .is_none_or(|given| Some(given) == run.task.get(key))
    };
    let named_only = match payload {
        Datum::Map(entries) => entries
            .keys()
            .all(|key| PAYLOAD_FIELDS.contains(&key.as_str())),
        _ => false,
    };
    if !checks.record(
        "payload_bound_to_task",
        named_only && public("edges") && public("c"),
        payload,
    ) {
        let detail = Datum::map([("residual_evidence", names(&["payload_bound_to_task"]))]);
        return Ok(refused("PAYLOAD_NOT_BOUND_TO_TASK", detail));
    }
    let extra: Vec<Datum> = match receipt {
        Datum::Map(entries) => entries
            .keys()
            .filter(|key| !RECEIPT_FIELDS.contains(&key.as_str()))
            .map(|key| Datum::text(key.clone()))
            .collect(),
        _ => Vec::new(),
    };
    let effect = receipt
        .get("authority_effect")
        .cloned()
        .unwrap_or(Datum::Null);
    let evidence = Datum::map([
        ("effect", effect.clone()),
        ("extra", Datum::List(extra.clone())),
    ]);
    let none = effect.as_text() == Some(NO_AUTHORITY) && extra.is_empty();
    if !checks.record("authority_effect_none", none, &evidence) {
        let detail = Datum::map([
            ("escalating_fields", Datum::List(extra)),
            ("residual_evidence", names(&["authority"])),
        ]);
        return Ok(refused("AUTHORITY_ESCALATION", detail));
    }
    let verifier = receipt.get("verifier_id").cloned().unwrap_or(Datum::Null);
    let registered = verifier.as_text() == Some(VERIFIER) && gate.registers_verifier;
    checks.record("witness_verifier_registered", registered, &verifier);
    let bound =
        text(receipt, "payload_sha256") == Some(sha256_hex(&witnessed.canonical()).as_str());
    checks.record("witness_bound_to_payload", bound, &verifier);
    let replayed = if registered {
        Some(replay(&gate, &phi)?)
    } else {
        None
    };
    let shown = replayed.clone().unwrap_or(Datum::Null);
    let replay_hash = replayed.as_ref().is_some_and(|done| {
        text(receipt, "replay_sha256") == Some(sha256_hex(&done.canonical()).as_str())
    });
    checks.record("replay_hash", replay_hash, &verifier);
    let matches = replayed
        .as_ref()
        .is_some_and(|done| receipt.get("claimed") == Some(done));
    checks.record("replay_match", matches, &shown);
    let defect = replayed
        .as_ref()
        .and_then(|done| done.get("defect"))
        .and_then(Datum::as_int)
        .is_some_and(Zero::is_zero);
    checks.record("zero_defect", defect, &shown);
    let nonce = receipt.get("nonce").cloned().unwrap_or(Datum::Null);
    checks.record("fresh_nonce", &nonce == gate.nonce, &nonce);
    let failed = Datum::from(checks.failed());
    Ok(checks.judge(
        "ALL_GUARDS_PASS",
        Datum::map([("residual_evidence", failed)]),
    ))
}
