//! WF12, mechanism-control arms: a mechanism arm against matched null and random controls on
//! the same items, and a rank certificate that explains every paired difference.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf12:v1
//!
//! The items are integer sums, graded by the host. Each of the four arms answers every item, one
//! question per arm. The paired effect of a pair of arms is, item by item, one when the second
//! passes and the first does not, minus one in the other case, and zero when both agree. The
//! reply to the last question is an integer rank per arm. It is accepted when every paired
//! total is the rank of the second arm less the rank of the first, which does not change when
//! every rank moves by the same amount.
//!
//! The controls are checked before anything is asked. The host records `null_control_is_zero`,
//! `random_norm_matches_mechanism` and `random_differs_from_mechanism`, in that order, and
//! refuses the run as `CONTROLS_UNMATCHED` if any failed. Then it records
//! `rank_differences_match_paired_totals` and certifies `ARMS_COMPARED` with the paired totals,
//! the ranks moved so the baseline is zero, and the residual of each pair.
//!
//! Task: `items`, a nonempty list of objects with `values`, a list of integers; and
//! `mechanism_vector`, `null_control_vector` and `random_control_vector`, lists of integers.

use num_bigint::BigInt;
use num_traits::Zero;

use crate::datum::Datum;

use super::reading::{integers, integers_under, object, squared_norm};
use super::{refused, require, Checks, Family, Run, Stop, Verdict, NO_REPLY};

pub const FAMILY: Family = Family {
    workflow: "WF12",
    name: "Mechanism-control arms",
    host_check: "integer_rank_difference_certificate",
    validate,
    walk,
};

/// The arms, in the order they are asked.
pub const ARMS: [&str; 4] = ["baseline", "mechanism", "null_control", "random_control"];

/// The pairs of arms compared, as positions in [`ARMS`]: the first arm, then the second.
pub const ARM_PAIRS: [(usize, usize); 4] = [(0, 1), (2, 1), (3, 1), (0, 2)];

/// What a task fixes: the three control vectors and the right answer to every item.
struct Panel {
    mechanism: Vec<BigInt>,
    null: Vec<BigInt>,
    random: Vec<BigInt>,
    truth: Vec<BigInt>,
}

fn vector(task: &Datum, key: &str) -> Result<Vec<BigInt>, String> {
    task.get(key)
        .and_then(integers)
        .ok_or_else(|| format!("{key} must be a list of exact integers"))
}

fn panel(task: &Datum) -> Result<Panel, String> {
    let items = task
        .get("items")
        .and_then(Datum::as_list)
        .filter(|items| !items.is_empty())
        .ok_or("items must be a nonempty list")?;
    let sum = |item: &Datum| {
        let values = item.get("values").and_then(integers);
        values.map(|values| values.into_iter().sum::<BigInt>())
    };
    let truth: Option<Vec<BigInt>> = items.iter().map(sum).collect();
    Ok(Panel {
        mechanism: vector(task, "mechanism_vector")?,
        null: vector(task, "null_control_vector")?,
        random: vector(task, "random_control_vector")?,
        truth: truth.ok_or("every item needs values, a list of exact integers")?,
    })
}

fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    panel(task).map(|_| ())
}

/// Record the three facts about the controls; the names of those that failed.
fn matched(panel: &Panel, checks: &mut Checks) -> (Vec<&'static str>, Datum) {
    let norms = Datum::map([
        ("mechanism", Datum::Int(squared_norm(&panel.mechanism))),
        ("random_control", Datum::Int(squared_norm(&panel.random))),
    ]);
    let same_length = |other: &[BigInt]| other.len() == panel.mechanism.len();
    let rows = [
        (
            "null_control_is_zero",
            same_length(&panel.null) && panel.null.iter().all(Zero::is_zero),
            Datum::from(panel.null.clone()),
        ),
        (
            "random_norm_matches_mechanism",
            same_length(&panel.random)
                && squared_norm(&panel.random) == squared_norm(&panel.mechanism),
            norms.clone(),
        ),
        (
            "random_differs_from_mechanism",
            panel.random != panel.mechanism,
            Datum::from(panel.random.clone()),
        ),
    ];
    let mut failed = Vec::new();
    for (name, held, evidence) in rows {
        if !checks.record(name, held, &evidence) {
            failed.push(name);
        }
    }
    (failed, norms)
}

/// The one reply per arm: whether each item was answered correctly.
fn graded(run: &mut Run, truth: &[BigInt]) -> Result<Result<Vec<Vec<bool>>, Verdict>, Stop> {
    let mut passes = Vec::new();
    for arm in ARMS {
        let stage = format!("arm:{arm}");
        let prompt = format!("{}\nArm: {arm}", run.prompt());
        let Some(reply) = run.ask(&stage, prompt)? else {
            return Ok(Err(refused(
                NO_REPLY,
                Datum::map([("arm", Datum::from(arm))]),
            )));
        };
        let answers = integers_under(object(reply, &stage)?, "answers")?;
        require(
            answers.len() == truth.len(),
            "every arm must answer the same items",
        )?;
        passes.push(answers.iter().zip(truth).map(|(a, t)| a == t).collect());
    }
    Ok(Ok(passes))
}

/// The ranks a certificate gives, one per arm and no other.
fn ranks(certificate: &Datum) -> Result<Vec<BigInt>, Stop> {
    let named = match certificate.get("ranks") {
        Some(Datum::Map(entries))
            if entries.len() == ARMS.len() && ARMS.iter().all(|arm| entries.contains_key(*arm)) =>
        {
            Some(entries)
        }
        _ => None,
    };
    let entries = named.ok_or_else(|| Stop::Malformed("one rank per arm".to_owned()))?;
    ARMS.iter()
        .map(|arm| {
            let rank = entries.get(*arm).and_then(Datum::as_int);
            rank.cloned()
                .ok_or_else(|| Stop::Malformed("rank must be an exact int".to_owned()))
        })
        .collect()
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let panel = panel(run.task).map_err(Stop::Malformed)?;
    let (failed, norms) = matched(&panel, checks);
    if !failed.is_empty() {
        let detail = Datum::map([("failed", Datum::from(failed)), ("squared_norms", norms)]);
        return Ok(refused("CONTROLS_UNMATCHED", detail));
    }
    let passes = match graded(run, &panel.truth)? {
        Ok(passes) => passes,
        Err(stopped) => return Ok(stopped),
    };
    let effect = |&(first, second): &(usize, usize)| -> BigInt {
        let paired = passes[first].iter().zip(&passes[second]);
        paired
            .map(|(before, after)| i64::from(*after) - i64::from(*before))
            .sum::<i64>()
            .into()
    };
    let totals: Vec<BigInt> = ARM_PAIRS.iter().map(effect).collect();
    let prompt = format!("{}\nReport integer arm ranks.", run.prompt());
    let Some(reply) = run.ask("certificate", prompt)? else {
        let detail = Datum::map([("arm", Datum::from("certificate"))]);
        return Ok(refused(NO_REPLY, detail));
    };
    let ranks = ranks(object(reply, "certificate")?)?;
    let residual: Vec<BigInt> = ARM_PAIRS
        .iter()
        .zip(&totals)
        .map(|(&(first, second), total)| total - (&ranks[second] - &ranks[first]))
        .collect();
    checks.record(
        "rank_differences_match_paired_totals",
        residual.iter().all(Zero::is_zero),
        &Datum::from(residual.clone()),
    );
    let pair_name =
        |&(first, second): &(usize, usize)| format!("{}->{}", ARMS[first], ARMS[second]);
    let paired = ARM_PAIRS
        .iter()
        .zip(&totals)
        .map(|(pair, total)| (pair_name(pair), Datum::Int(total.clone())));
    let moved = ARMS
        .iter()
        .zip(&ranks)
        .map(|(arm, rank)| ((*arm).to_owned(), Datum::Int(rank - &ranks[0])));
    let detail = Datum::Map(
        [
            ("paired_totals", Datum::Map(paired.collect())),
            ("gauge_fixed_ranks", Datum::Map(moved.collect())),
            ("residual", Datum::from(residual)),
        ]
        .into_iter()
        .map(|(key, value)| (key.to_owned(), value))
        .collect(),
    );
    Ok(checks.judge("ARMS_COMPARED", detail))
}
