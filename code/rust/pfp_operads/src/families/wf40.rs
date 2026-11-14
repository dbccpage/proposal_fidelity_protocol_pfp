//! WF40, restart boundary after exhausted repair: when repair ends without a fit, take the one
//! boundary action the measured values admit.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf40:v1
//!
//! The task is a graph with faces (closed walks) and a measured rational value `c` on every
//! edge. Repair proposes a value `phi` on every vertex in the WF20 loop; an attempt is accepted
//! when `c` is exactly the coboundary of `phi`. If the loop ends without that, the host shows
//! the receipts of the failed attempts and asks for one boundary action. Which action is
//! admissible is fixed by `c` alone:
//!
//! * `c` sums to something other than zero round a face (unclosed): `refusal`, naming such a
//!   face. Certified as the typed refusal `UNCLOSED_COCHAIN`.
//! * every face sum is zero but `c` is no coboundary (closed, not exact): `lift`, giving `phi`,
//!   `k` and an edge value `h` with zero face sums such that `c = d(phi) + k h`.
//! * `c` is a coboundary (exact): `restart`, with a seed of exactly the task's `edges`, `faces`
//!   and `c` and some of the receipts shown. The repair loop then runs once more on that seed
//!   and must end accepted. A seed that keeps the graph and faces and changes `c` is a new
//!   problem and is refused as `NEW_PROBLEM_NOT_REPAIR`.
//!
//! A receipt is the SHA-256 digest of the canonical JSON of the spec's digest, the attempt's
//! number and its residual.
//!
//! Task: `edges`, a list of `[u, v]` pairs whose vertices are `0..n-1`; `c`, one exact rational
//! per edge; `faces`, a list of closed walks, each a list of `[edge, sign]` with sign 1 or -1;
//! and optionally `max_attempts`, 1 to 5 (default 5).

use num_bigint::BigInt;
use num_traits::{Signed, Zero};

use crate::datum::Datum;
use crate::exact::{rational, rationals, show, Rational};
use crate::graph::{walk_sum, Graph, Step};

use super::attempts::{limit, Assessment};
use super::wf20::{derive, Halt, Loop, LOOP_LIMIT};
use super::{
    no_reply, refused, sha256_hex, typed_refusal, Checks, Family, Run, Stop, Verdict,
    CERTIFIED_CODE,
};

/// The boundary actions, in the order the host looks for them.
pub const ACTIONS: [&str; 3] = ["refusal", "lift", "restart"];

pub const FAMILY: Family = Family {
    workflow: "WF40",
    name: "Restart boundary after exhausted repair",
    host_check: "cochain_trichotomy_boundary",
    validate,
    walk,
};

/// The task as the host reads it.
struct Complex {
    graph: Graph,
    /// The number of each vertex in the graph, by the vertex's name.
    numbered: Vec<usize>,
    values: Vec<Rational>,
    faces: Vec<Vec<Step>>,
}

fn step(entry: &Datum, edges: usize) -> Option<Step> {
    let [edge, sign] = entry.as_list()? else {
        return None;
    };
    let edge = edge.as_count().filter(|&edge| edge < edges)?;
    let sign = match sign.as_int()? {
        sign if *sign == BigInt::from(1) => 1,
        sign if *sign == BigInt::from(-1) => -1,
        _ => return None,
    };
    Some((edge, sign))
}

/// Whether a walk ends where it began: each vertex is entered as often as it is left.
fn closed(graph: &Graph, walk: &[Step]) -> bool {
    let mut balance = vec![0i64; graph.names().len()];
    for &(edge, sign) in walk {
        if let Some(&(from, to)) = graph.edges().get(edge) {
            balance[to] += i64::from(sign);
            balance[from] -= i64::from(sign);
        }
    }
    balance.iter().all(|&net| net == 0)
}

fn complex(task: &Datum) -> Result<Complex, String> {
    let graph = task
        .get("edges")
        .and_then(Graph::read)
        .ok_or("edges must be a list of pairs of exact integers")?;
    if !graph.is_numbered() {
        return Err("vertices must be 0..n-1".to_owned());
    }
    let numbered = (0..graph.names().len())
        .filter_map(|name| graph.vertex(&BigInt::from(name)))
        .collect();
    let values = task
        .get("c")
        .and_then(rationals)
        .filter(|values| values.len() == graph.edges().len())
        .ok_or("c must be one exact rational per edge")?;
    let faces: Vec<Vec<Step>> = task
        .get("faces")
        .and_then(Datum::as_list)
        .ok_or("faces must be a list")?
        .iter()
        .map(|face| {
            let steps = face.as_list()?.iter();
            steps.map(|entry| step(entry, values.len())).collect()
        })
        .collect::<Option<_>>()
        .ok_or("each face is a list of [edge, sign] with the edge in range and sign 1 or -1")?;
    if !faces.iter().all(|face| closed(&graph, face)) {
        return Err("every face must be a closed cycle".to_owned());
    }
    Ok(Complex {
        graph,
        numbered,
        values,
        faces,
    })
}

fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    complex(task)?;
    limit(task, LOOP_LIMIT, LOOP_LIMIT).map(|_| ())
}

/// A rational as the residual writes it: an integer bare, anything else as `p/q`.
fn plain(value: &Rational) -> String {
    if value.is_integer() {
        value.numer().to_string()
    } else {
        show(value)
    }
}

fn digest(value: &Datum) -> String {
    sha256_hex(&value.canonical())
}

impl Complex {
    /// One rational per vertex from a reply, in the graph's vertex order.
    fn potential(&self, listed: Option<&Datum>, name: &str) -> Result<Vec<Rational>, String> {
        let listed = listed
            .and_then(Datum::as_list)
            .ok_or_else(|| format!("{name} list required"))?;
        if listed.len() != self.numbered.len() {
            return Err("one potential per vertex".to_owned());
        }
        let by_name: Vec<Rational> = listed
            .iter()
            .map(rational)
            .collect::<Option<_>>()
            .ok_or_else(|| format!("{name} must be an int or a p/q string"))?;
        let mut potential = vec![Rational::zero(); by_name.len()];
        for (value, &vertex) in by_name.into_iter().zip(&self.numbered) {
            potential[vertex] = value;
        }
        Ok(potential)
    }

    /// The finding on one proposed potential. The residual gives the size of the misfit and the
    /// edges that are off, never a value.
    fn assess(&self, reply: &Datum) -> Result<Assessment, String> {
        let potential = self.potential(reply.get("phi"), "phi")?;
        let left = self.graph.residual(&self.values, &potential);
        let misfit: Rational = left.iter().map(Signed::abs).sum();
        let off: Vec<usize> = (0..left.len())
            .filter(|&edge| !left[edge].is_zero())
            .collect();
        Ok(Assessment {
            accepted: misfit.is_zero(),
            measure: Datum::text(show(&misfit)),
            residual: Datum::map([
                ("defect_l1", Datum::text(plain(&misfit))),
                ("off_edges", Datum::from(off)),
            ]),
        })
    }

    fn face_sums_vanish(&self, values: &[Rational]) -> bool {
        self.faces
            .iter()
            .all(|face| walk_sum(face, values).is_zero())
    }

    /// One repair loop over this graph: the task put to the model, the text before each stage
    /// name, and the number of attempts.
    fn turn<'t>(&'t self, task: &'t Datum, prefix: &'t str, limit: usize) -> Loop<'t> {
        Loop {
            task,
            graph: &self.graph,
            prefix,
            limit,
        }
    }

    /// Which of the three cases the measured values are, and the action that case admits.
    fn class(&self) -> (&'static str, &'static str) {
        if !self.face_sums_vanish(&self.values) {
            ("unclosed", "refusal")
        } else if self.graph.defect(&self.values).is_zero() {
            ("exact", "restart")
        } else {
            ("closed_non_exact", "lift")
        }
    }
}

/// The parts of the task a restart must carry unchanged.
fn spec(task: &Datum) -> Datum {
    let part = |key: &str| task.get(key).cloned().unwrap_or(Datum::Null);
    Datum::map([
        ("edges", part("edges")),
        ("faces", part("faces")),
        ("c", part("c")),
    ])
}

fn receipts(task: &Datum, trail: &[Datum]) -> Vec<Datum> {
    let spec = digest(&spec(task));
    let part = |row: &Datum, key: &str| row.get(key).cloned().unwrap_or(Datum::Null);
    trail
        .iter()
        .map(|row| {
            Datum::text(digest(&Datum::map([
                ("spec", Datum::text(spec.clone())),
                ("attempt", part(row, "attempt")),
                ("residual", part(row, "residual")),
            ])))
        })
        .collect()
}

fn with(detail: &Datum, entries: Vec<(&str, Datum)>) -> Datum {
    let mut map = match detail {
        Datum::Map(map) => map.clone(),
        _ => Default::default(),
    };
    for (key, value) in entries {
        map.insert(key.to_owned(), value);
    }
    Datum::Map(map)
}

/// Refused under the name of the first predicate that failed, with this detail.
fn failed(checks: &Checks, detail: Datum) -> Verdict {
    refused(&checks.judge(CERTIFIED_CODE, Datum::Null).code, detail)
}

fn refusal(
    complex: &Complex,
    body: &Datum,
    checks: &mut Checks,
    detail: Datum,
) -> Result<Verdict, String> {
    let named = body.get("face").ok_or("face must be an exact int")?;
    if named.as_int().is_none() {
        return Err("face must be an exact int".to_owned());
    }
    let (face, walk) = named
        .as_count()
        .and_then(|face| Some((face, complex.faces.get(face)?)))
        .ok_or("face index out of range")?;
    let sum = walk_sum(walk, &complex.values);
    checks.record(
        "face_witness_nonzero",
        !sum.is_zero(),
        &Datum::text(show(&sum)),
    );
    if checks.certified() {
        let detail = with(&detail, vec![("face", Datum::from(face))]);
        return Ok(typed_refusal("UNCLOSED_COCHAIN", detail));
    }
    Ok(failed(checks, detail))
}

fn lift(
    complex: &Complex,
    body: &Datum,
    checks: &mut Checks,
    detail: Datum,
) -> Result<Verdict, String> {
    let edges = complex.values.len();
    let witness = body
        .get("h")
        .and_then(Datum::as_list)
        .filter(|witness| witness.len() == edges)
        .ok_or("h is an edge cochain")?
        .iter()
        .map(rational)
        .collect::<Option<Vec<_>>>()
        .ok_or("h must be an int or a p/q string")?;
    let potential = complex.potential(body.get("phi"), "phi")?;
    let scale = body
        .get("k")
        .and_then(rational)
        .ok_or("k must be an int or a p/q string")?;
    let delta = complex.graph.defect(&complex.values);
    checks.record(
        "lift_authorised_by_positive_delta",
        delta.is_positive(),
        &Datum::text(show(&delta)),
    );
    let written =
        |values: &[Rational]| Datum::List(values.iter().map(|v| Datum::text(show(v))).collect());
    checks.record(
        "preservation_witness_closed",
        complex.face_sums_vanish(&witness),
        &written(&witness),
    );
    let fit: Vec<Rational> = complex
        .graph
        .coboundary(&potential)
        .into_iter()
        .zip(&witness)
        .map(|(explained, held)| explained + &scale * held)
        .collect();
    checks.record(
        "lift_reproduces_claims",
        fit == complex.values,
        &written(&fit),
    );
    Ok(checks.judge("LIFT_AUTHORISED", detail))
}

/// The checks on a restart seed. The receipts the seed keeps when every check passed.
fn seed<'r>(
    task: &Datum,
    body: &'r Datum,
    shown: &[Datum],
    checks: &mut Checks,
) -> Result<Result<&'r Datum, &'static str>, String> {
    let Some(Datum::Map(seed)) = body.get("seed") else {
        return Err("restart needs a seed".to_owned());
    };
    let spec = spec(task);
    let keys: Vec<&str> = seed.keys().map(String::as_str).collect();
    checks.record(
        "seed_only_spec_and_receipts",
        keys == ["receipts", "spec"],
        &Datum::from(keys),
    );
    let carried = seed.get("spec").unwrap_or(&Datum::Null);
    let same = |key: &str| carried.is_map() && carried.get(key) == spec.get(key);
    if same("edges") && same("faces") && !same("c") {
        checks.record("claim_set_unchanged", false, carried);
        return Ok(Err("NEW_PROBLEM_NOT_REPAIR"));
    }
    checks.record(
        "seed_spec_immutable",
        *carried == spec,
        &Datum::text(digest(&spec)),
    );
    let kept = seed.get("receipts").unwrap_or(&Datum::Null);
    let verified = kept
        .as_list()
        .is_some_and(|kept| !kept.is_empty() && kept.iter().all(|receipt| shown.contains(receipt)));
    checks.record("receipts_verified", verified, &Datum::List(shown.to_vec()));
    Ok(Ok(kept))
}

/// The one boundary action a reply takes, with its body. A verdict instead when the reply takes
/// none or several.
fn chosen<'r>(
    reply: &'r Datum,
    checks: &mut Checks,
) -> Result<Result<(&'static str, &'r Datum), Verdict>, String> {
    if !reply.is_map() {
        return Err("boundary reply must be an object".to_owned());
    }
    let taken: Vec<&'static str> = ACTIONS
        .into_iter()
        .filter(|action| reply.get(action).is_some())
        .collect();
    let one = checks.record(
        "exactly_one_action",
        taken.len() == 1,
        &Datum::from(taken.clone()),
    );
    let (Some(&action), true) = (taken.first(), one) else {
        let detail = Datum::map([("actions", Datum::from(taken))]);
        return Ok(Err(refused("NOT_EXACTLY_ONE_ACTION", detail)));
    };
    let body = reply
        .get(action)
        .filter(|body| body.is_map())
        .ok_or_else(|| format!("{action} must be an object"))?;
    Ok(Ok((action, body)))
}

/// The task a restart runs on: the spec, the receipts the seed kept, and the task's statement
/// and attempt limit.
fn fresh(task: &Datum, kept: &Datum) -> Datum {
    let statement = task.get("statement").cloned().unwrap_or(Datum::text(""));
    let mut entries = vec![("refusal_receipts", kept.clone()), ("statement", statement)];
    if let Some(stated) = task.get("max_attempts") {
        entries.push(("max_attempts", stated.clone()));
    }
    with(&spec(task), entries)
}

/// What a restart is checked against: the task as read, its attempt limit, and the receipts
/// the host showed.
struct Boundary<'c> {
    complex: &'c Complex,
    limit: usize,
    shown: &'c [Datum],
}

impl Boundary<'_> {
    /// Check the seed, then run the repair loop once more on it.
    fn restart(
        &self,
        run: &mut Run,
        checks: &mut Checks,
        body: &Datum,
        detail: Datum,
    ) -> Result<Verdict, Stop> {
        let task = run.task;
        let kept = match seed(task, body, self.shown, checks).map_err(Stop::Malformed)? {
            Err(code) => return Ok(refused(code, detail)),
            Ok(_) if !checks.certified() => return Ok(failed(checks, detail)),
            Ok(kept) => kept,
        };
        let fresh = fresh(task, kept);
        let assess = |reply: &Datum| self.complex.assess(reply);
        let turn = self.complex.turn(&fresh, "restart:", self.limit);
        let restart = derive(run, &turn, None, &assess)?;
        checks.record(
            "restart_certified",
            restart.halt == Halt::Certificate,
            &Datum::from(restart.halt.name()),
        );
        let attempts = vec![("restart_attempts", Datum::from(restart.trail.len()))];
        Ok(checks.judge("RESTART_REPAIRED", with(&detail, attempts)))
    }
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let task = run.task;
    let complex = complex(task).map_err(Stop::Malformed)?;
    let limit = limit(task, LOOP_LIMIT, LOOP_LIMIT).map_err(Stop::Malformed)?;
    let assess = |reply: &Datum| complex.assess(reply);
    let repair = derive(run, &complex.turn(task, "", limit), None, &assess)?;
    if matches!(repair.halt, Halt::Certificate | Halt::Scope) {
        checks.record(
            "repaired_within_limit",
            repair.halt == Halt::Certificate,
            &Datum::from(repair.halt.name()),
        );
        let detail = Datum::map([("attempts", Datum::from(repair.trail.len()))]);
        return Ok(checks.judge("REPAIRED", detail));
    }
    let shown = receipts(task, &repair.trail);
    let prompt = format!(
        "{}\nRefusal receipts: {}",
        run.prompt(),
        Datum::List(shown.clone()).canonical()
    );
    let Some(reply) = run.ask("boundary", prompt)? else {
        return Ok(no_reply());
    };
    let (action, body) = match chosen(reply, checks).map_err(Stop::Malformed)? {
        Ok(chosen) => chosen,
        Err(verdict) => return Ok(verdict),
    };
    let (class, admitted) = complex.class();
    let delta = plain(&complex.graph.defect(&complex.values));
    let detail = Datum::map([
        ("cochain_class", Datum::from(class)),
        ("delta", Datum::text(delta)),
        ("action", Datum::from(action)),
    ]);
    checks.record("action_matches_trichotomy", action == admitted, &detail);
    let boundary = Boundary {
        complex: &complex,
        limit,
        shown: &shown,
    };
    match action {
        "refusal" => refusal(&complex, body, checks, detail).map_err(Stop::Malformed),
        "lift" => lift(&complex, body, checks, detail).map_err(Stop::Malformed),
        _ => boundary.restart(run, checks, body, detail),
    }
}
