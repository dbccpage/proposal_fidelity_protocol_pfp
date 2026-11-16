//! WF36, guarded staged slot materialisation: fill the empty edge slots of a cochain so every
//! cycle sums to zero, behind a guard that must be complete, then give a potential.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf36:v1
//!
//! The cycle matrix `S` has one row for each fundamental cycle of the task's graph. A value on
//! every edge is the coboundary of a value on every vertex exactly when `S c` is zero, and
//! `S c` is the syndrome the host uses for the verdict, for the retry prompt and for the record.
//!
//! The host records, in this order:
//!
//! * `guard_complete`: the guard rows, by default every row, have the rank of `S`. A guard
//!   that fails is refused as `PARTIAL_GUARD`, with a vector the guard misses that `S` does not
//!   (the chord of the first row the guard leaves out) and the syndrome of each side.
//! * `abstention_matches_rank_test`: only when the first or second reply abstains. The edges
//!   with a slot can be filled exactly when the rank of the slot columns of `S` equals the rank
//!   with the column of what the fixed values already leave over. A false abstention is refused
//!   as `FALSE_ABSTENTION`, a true one is a typed refusal `ABSTAIN_NOT_MATERIALISABLE`; both
//!   carry the two ranks.
//! * `guard_green_within_one_retry`: the syndrome of the first fill is zero, or of the second,
//!   which is asked with the first syndrome in its prompt. Refused as `GUARD_RED_AFTER_RETRY`
//!   with every syndrome.
//! * `stage2_potential_explains_slots`: the potential the third reply gives, one exact integer
//!   per vertex, explains the filled cochain. `MATERIALISED` after one fill and
//!   `MATERIALISED_AFTER_RETRY` after two, with the syndromes and the residual.
//!
//! A step with no reply stops the run as `NO_ADMISSIBLE_REPLY` naming the stage.
//!
//! Task: `edges`, as in [`super::cochain`] (a nonempty list of pairs of integers whose vertices
//! are named `0..n-1`); `values`, one exact integer or `null` for each edge; and optionally
//! `guard_rows`, integers that each name a row of `S`.

use std::collections::BTreeSet;

use num_bigint::BigInt;
use num_traits::Zero;

use crate::datum::Datum;
use crate::exact::{rank, Rational};
use crate::graph::Graph;

use super::cochain::{self, Named};
use super::reading::{integers, object};
use super::{refused, require, typed_refusal, Checks, Family, Run, Stop, Verdict, NO_REPLY};

pub const FAMILY: Family = Family {
    workflow: "WF36",
    name: "Guarded staged slot materialisation",
    host_check: "exact_cochain_check",
    validate,
    walk,
};

/// What a task fixes: the graph, the cycle matrix, the guard, and the value on each edge.
struct Slots {
    named: Named,
    /// One row per fundamental cycle, one signed entry per edge.
    cycles: Vec<Vec<BigInt>>,
    guard: Vec<usize>,
    /// The fixed value of each edge; nothing where there is a slot.
    values: Vec<Option<BigInt>>,
}

fn cycle_matrix(graph: &Graph) -> Vec<Vec<BigInt>> {
    graph
        .fundamental_cycles()
        .iter()
        .map(|cycle| {
            let mut row = vec![BigInt::zero(); graph.edges().len()];
            for &(edge, sign) in cycle {
                row[edge] += i64::from(sign);
            }
            row
        })
        .collect()
}

fn rationals_of(rows: &[Vec<BigInt>]) -> Vec<Vec<Rational>> {
    let lift = |row: &Vec<BigInt>| row.iter().cloned().map(Rational::from_integer).collect();
    rows.iter().map(lift).collect()
}

fn slots(task: &Datum) -> Result<Slots, String> {
    let named = cochain::graph(task)?;
    let cycles = cycle_matrix(&named.graph);
    let value = |entry: &Datum| match entry {
        Datum::Null => Some(None),
        other => other.as_int().map(|number| Some(number.clone())),
    };
    let values: Option<Vec<Option<BigInt>>> = task
        .get("values")
        .and_then(Datum::as_list)
        .filter(|values| values.len() == named.graph.edges().len())
        .and_then(|values| values.iter().map(value).collect());
    let guard = match task.get("guard_rows") {
        None => Some((0..cycles.len()).collect()),
        Some(listed) => cochain::indices(listed, cycles.len()),
    };
    Ok(Slots {
        named,
        guard: guard.ok_or("guard_rows must be rows of the cycle matrix")?,
        values: values.ok_or("values must be one exact integer or null per edge")?,
        cycles,
    })
}

fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    slots(task).map(|_| ())
}

/// `S c`: the sum of each cycle's signed values.
fn syndrome(rows: &[Vec<BigInt>], values: &[BigInt]) -> Vec<BigInt> {
    let dot = |row: &Vec<BigInt>| {
        row.iter()
            .zip(values)
            .map(|(sign, value)| sign * value)
            .sum()
    };
    rows.iter().map(dot).collect()
}

/// The ranks that say whether the slots can be filled, as the two numbers of the rank test.
fn fill_ranks(slots: &Slots) -> (usize, usize) {
    let open: Vec<usize> = (0..slots.values.len())
        .filter(|&edge| slots.values[edge].is_none())
        .collect();
    let fixed: Vec<BigInt> = slots
        .values
        .iter()
        .map(|value| value.clone().unwrap_or_default())
        .collect();
    let columns: Vec<Vec<BigInt>> = slots
        .cycles
        .iter()
        .map(|row| open.iter().map(|&edge| row[edge].clone()).collect())
        .collect();
    let augmented: Vec<Vec<BigInt>> = columns
        .iter()
        .zip(&slots.cycles)
        .map(|(row, cycle)| {
            let left: BigInt = cycle
                .iter()
                .zip(&fixed)
                .map(|(sign, value)| sign * value)
                .sum();
            row.iter().cloned().chain([-left]).collect()
        })
        .collect();
    (
        rank(&rationals_of(&columns)),
        rank(&rationals_of(&augmented)),
    )
}

fn numbers(values: &[BigInt]) -> Datum {
    Datum::from(values.to_vec())
}

fn list_of(rows: &[Vec<BigInt>]) -> Datum {
    Datum::List(rows.iter().map(|row| numbers(row)).collect())
}

fn rank_detail(ranks: (usize, usize)) -> Datum {
    Datum::map([
        ("rank_S_slots", Datum::from(ranks.0)),
        ("rank_augmented", Datum::from(ranks.1)),
    ])
}

/// The edges a guard misses: refused with the first missed chord as a vector `S` sees and the
/// guard does not.
fn partial_guard(slots: &Slots, guard_rows: &BTreeSet<usize>) -> Option<Verdict> {
    let missed = (0..slots.cycles.len()).find(|row| !guard_rows.contains(row))?;
    let chord = *slots.named.graph.forest().chords.get(missed)?;
    let mut witness = vec![BigInt::zero(); slots.values.len()];
    *witness.get_mut(chord)? = BigInt::from(1);
    let guarded: Vec<Vec<BigInt>> = slots
        .guard
        .iter()
        .filter_map(|&row| slots.cycles.get(row).cloned())
        .collect();
    Some(refused(
        "PARTIAL_GUARD",
        Datum::map([
            ("kernel_witness", numbers(&witness)),
            ("guard_syndrome", numbers(&syndrome(&guarded, &witness))),
            ("full_syndrome", numbers(&syndrome(&slots.cycles, &witness))),
        ]),
    ))
}

/// The value on every edge once a reply has filled the slots; else the run stops as malformed.
fn filled(slots: &Slots, reply: &Datum) -> Result<Vec<BigInt>, Stop> {
    let open: Vec<usize> = (0..slots.values.len())
        .filter(|&edge| slots.values[edge].is_none())
        .collect();
    let given = match reply.get("slots") {
        Some(Datum::Map(entries)) => Some(entries),
        _ => None,
    };
    let keys: BTreeSet<String> = open.iter().map(ToString::to_string).collect();
    let exact = given.filter(|entries| {
        entries.len() == keys.len() && keys.iter().all(|key| entries.contains_key(key))
    });
    let entries = exact.ok_or_else(|| Stop::Malformed("one slot per null edge".to_owned()))?;
    slots
        .values
        .iter()
        .enumerate()
        .map(|(edge, fixed)| match fixed {
            Some(value) => Ok(value.clone()),
            None => entries
                .get(&edge.to_string())
                .and_then(Datum::as_int)
                .cloned()
                .ok_or_else(|| Stop::Malformed("slot must be an exact int".to_owned())),
        })
        .collect()
}

/// What the first stage came to: a fill whose syndrome is zero, or the verdict that ended the run.
enum Stage {
    Filled(Vec<BigInt>, Vec<Vec<BigInt>>),
    Ended(Verdict),
}

fn first_stage(
    run: &mut Run,
    slots: &Slots,
    ranks: (usize, usize),
    checks: &mut Checks,
) -> Result<Stage, Stop> {
    let mut prompt = run.prompt();
    let mut syndromes: Vec<Vec<BigInt>> = Vec::new();
    let mut last = Vec::new();
    for attempt in 0..2 {
        let stage = format!("stage1:{attempt}");
        let Some(reply) = run.ask(&stage, prompt.clone())? else {
            let detail = Datum::map([("stage", Datum::text(stage))]);
            return Ok(Stage::Ended(refused(NO_REPLY, detail)));
        };
        let reply = object(reply, &stage)?;
        if matches!(reply.get("abstain"), Some(Datum::Bool(true))) {
            let fillable = ranks.0 == ranks.1;
            if !checks.record(
                "abstention_matches_rank_test",
                !fillable,
                &rank_detail(ranks),
            ) {
                return Ok(Stage::Ended(refused(
                    "FALSE_ABSTENTION",
                    rank_detail(ranks),
                )));
            }
            let detail = rank_detail(ranks);
            return Ok(Stage::Ended(typed_refusal(
                "ABSTAIN_NOT_MATERIALISABLE",
                detail,
            )));
        }
        last = filled(slots, reply)?;
        syndromes.push(syndrome(&slots.cycles, &last));
        let green = syndromes
            .last()
            .is_some_and(|row| row.iter().all(Zero::is_zero));
        if green {
            break;
        }
        let shown = numbers(syndromes.last().map_or(&[][..], Vec::as_slice));
        prompt = format!("{}\nGuard syndrome: {}", run.prompt(), shown.canonical());
    }
    let green = syndromes
        .last()
        .is_some_and(|row| row.iter().all(Zero::is_zero));
    let evidence = list_of(&syndromes);
    if !checks.record("guard_green_within_one_retry", green, &evidence) {
        let detail = Datum::map([("syndromes", evidence)]);
        return Ok(Stage::Ended(refused("GUARD_RED_AFTER_RETRY", detail)));
    }
    Ok(Stage::Filled(last, syndromes))
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let slots = slots(run.task).map_err(Stop::Malformed)?;
    let guard_rows: BTreeSet<usize> = slots.guard.iter().copied().collect();
    let guarded: Vec<Vec<Rational>> = rationals_of(
        &slots
            .guard
            .iter()
            .filter_map(|&row| slots.cycles.get(row).cloned())
            .collect::<Vec<_>>(),
    );
    let complete = rank(&guarded) == rank(&rationals_of(&slots.cycles));
    let listed = Datum::from(
        guard_rows
            .iter()
            .copied()
            .map(BigInt::from)
            .collect::<Vec<_>>(),
    );
    if !checks.record("guard_complete", complete, &listed) {
        let verdict = partial_guard(&slots, &guard_rows);
        return Ok(verdict.unwrap_or_else(|| refused("PARTIAL_GUARD", Datum::map([]))));
    }
    let ranks = fill_ranks(&slots);
    let (c, syndromes) = match first_stage(run, &slots, ranks, checks)? {
        Stage::Filled(c, syndromes) => (c, syndromes),
        Stage::Ended(verdict) => return Ok(verdict),
    };
    let prompt = format!("{}\nSlots: {}", run.prompt(), numbers(&c).canonical());
    let Some(reply) = run.ask("stage2", prompt)? else {
        return Ok(refused(
            NO_REPLY,
            Datum::map([("stage", Datum::from("stage2"))]),
        ));
    };
    let reply = object(reply, "stage2")?;
    let phi = reply
        .get("potential")
        .filter(|listed| integers(listed).is_some());
    let vertices = slots.named.graph.names().len();
    let given = phi
        .map(Datum::as_list)
        .filter(|given| given.map(<[Datum]>::len) == Some(vertices));
    require(
        given.is_some(),
        "potential needs one integer per vertex 0..n-1",
    )?;
    let potential = phi
        .map(|listed| slots.named.potential(listed))
        .transpose()
        .map_err(Stop::Malformed)?
        .unwrap_or_default();
    let values: Vec<Rational> = c.iter().cloned().map(Rational::from_integer).collect();
    let residual: Vec<BigInt> = slots
        .named
        .graph
        .residual(&values, &potential)
        .iter()
        .map(|entry| entry.numer().clone())
        .collect();
    checks.record(
        "stage2_potential_explains_slots",
        residual.iter().all(Zero::is_zero),
        &numbers(&residual),
    );
    let code = if syndromes.len() == 1 {
        "MATERIALISED"
    } else {
        "MATERIALISED_AFTER_RETRY"
    };
    let detail = Datum::map([
        ("syndromes", list_of(&syndromes)),
        ("residual", numbers(&residual)),
    ]);
    Ok(checks.judge(code, detail))
}
