//! WF29, checker synthesis scored by mutation kill rate: a proposed checker must accept every
//! valid case and reject enough of the sealed mutants.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf29:v1
//!
//! A case is `{"c": one value per edge, "phi": one value per vertex}` on the task's graph, and
//! it is valid when `phi` is a potential of `c`. A checker is a tree over five declared
//! predicates, joined by `["and", ...]`, `["or", ...]` and `["not", x]`, nested at most 6 deep.
//! It is data the host interprets. Nothing a reply sends is executed.
//!
//! * `c_length_matches`: `c` is a list with one entry per edge.
//! * `phi_covers_vertices`: `phi` is an object whose keys are exactly the vertex names.
//! * `coboundary_matches`: on every edge, `c` is `phi` at its head less `phi` at its tail.
//! * `cycle_sums_zero`: `c` is the coboundary of some potential.
//! * `phi_root_zero`: `phi` is zero at the first vertex the edges name.
//!
//! A predicate that cannot read what it needs from a case rejects the case, whatever the tree
//! around it says. `and` and `or` read their parts in order and stop at the first that decides.
//!
//! The run is certified as `CHECKER_ACCEPTED` when the checker rejects no valid case and the
//! share of mutants it rejects is at least `min_kill_rate`. With no mutants that share is 0.
//!
//! Task: `edges`, a list of pairs of text; `valid`, a list of cases; `min_kill_rate`, an exact
//! rational. Sealed: `mutants`, a list of cases. Reply: `{"checker": tree}`.

use num_bigint::BigInt;
use num_traits::Zero;

use crate::datum::Datum;
use crate::exact::{rational, rationals, Rational};

use super::labelled::{self, Labelled};
use super::{no_reply, Checks, Family, Run, Stop, Verdict};

/// The deepest a checker may nest.
pub const MAX_DEPTH: usize = 6;

/// The declared predicates, in the order the module header describes them.
pub const PREDICATES: [&str; 5] = [
    "c_length_matches",
    "phi_covers_vertices",
    "coboundary_matches",
    "cycle_sums_zero",
    "phi_root_zero",
];

pub const FAMILY: Family = Family {
    workflow: "WF29",
    name: "Checker synthesis scored by mutation kill rate",
    host_check: "mutation_kill_rate_with_valid_panel",
    validate,
    walk,
};

struct Panel<'t> {
    graph: Labelled,
    valid: &'t [Datum],
    mutants: &'t [Datum],
    bar: Rational,
}

fn panel<'t>(task: &'t Datum, sealed: &'t Datum) -> Result<Panel<'t>, String> {
    let graph = task
        .get("edges")
        .and_then(labelled::read)
        .ok_or("edges must be a list of pairs of text")?;
    let valid = task
        .get("valid")
        .and_then(Datum::as_list)
        .ok_or("valid must be a list of cases")?;
    let bar = task
        .get("min_kill_rate")
        .and_then(rational)
        .ok_or("min_kill_rate must be an exact rational")?;
    let mutants = match sealed.get("mutants") {
        Some(listed) => listed.as_list().ok_or("sealed mutants must be a list")?,
        None => &[],
    };
    Ok(Panel {
        graph,
        valid,
        mutants,
        bar,
    })
}

fn validate(task: &Datum, sealed: &Datum) -> Result<(), String> {
    panel(task, sealed).map(|_| ())
}

/// What one declared predicate says of a case. Nothing when it cannot read the case.
type Reads = fn(&Panel<'_>, &Datum) -> Option<bool>;

/// A checker: a declared predicate, or a tree of them.
enum Checker {
    Predicate(Reads),
    Not(Box<Checker>),
    All(Vec<Checker>),
    Any(Vec<Checker>),
}

/// The reading of a declared predicate, by its name.
fn declared(name: &str) -> Option<Reads> {
    let reads: Reads = match name {
        "c_length_matches" => length_matches,
        "phi_covers_vertices" => covers_vertices,
        "coboundary_matches" => coboundary_matches,
        "cycle_sums_zero" => cycle_sums_zero,
        "phi_root_zero" => root_zero,
        _ => return None,
    };
    Some(reads)
}

/// The operator and the parts of a tree that is not a predicate name.
fn operands(tree: &Datum) -> Option<(&str, &[Datum])> {
    match tree.as_list()?.split_first()? {
        (Datum::Text(operator), written) if !written.is_empty() => {
            let known = ["and", "or", "not"].contains(&operator.as_str());
            known.then_some((operator.as_str(), written))
        }
        _ => None,
    }
}

fn checker(tree: &Datum, depth: usize) -> Result<Checker, String> {
    if depth > MAX_DEPTH {
        return Err("checker too deep".to_owned());
    }
    if let Datum::Text(name) = tree {
        let known = declared(name).map(Checker::Predicate);
        return known.ok_or_else(|| format!("unknown predicate {}", tree.canonical()));
    }
    let (operator, written) =
        operands(tree).ok_or_else(|| format!("bad checker {}", tree.canonical()))?;
    let mut parts: Vec<Checker> = written
        .iter()
        .map(|part| checker(part, depth + 1))
        .collect::<Result<_, _>>()?;
    match (operator, parts.len()) {
        ("and", _) => Ok(Checker::All(parts)),
        ("or", _) => Ok(Checker::Any(parts)),
        (_, 1) => Ok(Checker::Not(Box::new(parts.remove(0)))),
        _ => Err("not takes one checker".to_owned()),
    }
}

/// The `phi` of a case, when it is an object.
fn phi(case: &Datum) -> Option<&Datum> {
    case.get("phi").filter(|phi| phi.is_map())
}

fn edge_count(panel: &Panel<'_>) -> usize {
    panel.graph.graph.edges().len()
}

fn length_matches(panel: &Panel<'_>, case: &Datum) -> Option<bool> {
    Some(case.get("c")?.as_list()?.len() == edge_count(panel))
}

fn covers_vertices(panel: &Panel<'_>, case: &Datum) -> Option<bool> {
    Some(panel.graph.covers(phi(case)?))
}

fn coboundary_matches(panel: &Panel<'_>, case: &Datum) -> Option<bool> {
    let potential = panel.graph.potential(phi(case)?)?;
    let listed = rationals(case.get("c")?)?;
    Some(panel.graph.graph.coboundary(&potential) == listed)
}

fn cycle_sums_zero(panel: &Panel<'_>, case: &Datum) -> Option<bool> {
    let edges = edge_count(panel);
    let values = rationals(case.get("c")?).filter(|values| values.len() == edges)?;
    Some(panel.graph.graph.defect(&values).is_zero())
}

fn root_zero(panel: &Panel<'_>, case: &Datum) -> Option<bool> {
    let root = panel.graph.names().first()?;
    Some(rational(phi(case)?.get(root)?)?.is_zero())
}

/// What a checker says of a case. Nothing when a predicate it reached could not read it.
fn says(panel: &Panel<'_>, checker: &Checker, case: &Datum) -> Option<bool> {
    match checker {
        Checker::Predicate(reads) => reads(panel, case),
        Checker::Not(part) => says(panel, part, case).map(|held| !held),
        Checker::All(parts) => {
            for part in parts {
                if !says(panel, part, case)? {
                    return Some(false);
                }
            }
            Some(true)
        }
        Checker::Any(parts) => {
            for part in parts {
                if says(panel, part, case)? {
                    return Some(true);
                }
            }
            Some(false)
        }
    }
}

/// How many of these cases the checker does not accept.
fn rejected(panel: &Panel<'_>, checker: &Checker, cases: &[Datum]) -> usize {
    let accepted = |case: &&Datum| says(panel, checker, case) == Some(true);
    cases.len() - cases.iter().filter(accepted).count()
}

/// A rational as a verdict writes it: an integer, or `p/q` in lowest terms.
fn plain(value: &Rational) -> Datum {
    if value.is_integer() {
        Datum::Int(value.numer().clone())
    } else {
        Datum::text(format!("{}/{}", value.numer(), value.denom()))
    }
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let panel = panel(run.task, run.sealed).map_err(Stop::Malformed)?;
    let Some(reply) = run.ask("solve", run.prompt())? else {
        return Ok(no_reply());
    };
    let tree = reply
        .get("checker")
        .ok_or_else(|| Stop::Malformed("checker required".to_owned()))?;
    let checker = checker(tree, 0).map_err(Stop::Malformed)?;
    let false_rejections = rejected(&panel, &checker, panel.valid);
    let killed = rejected(&panel, &checker, panel.mutants);
    let rate = if panel.mutants.is_empty() {
        Rational::zero()
    } else {
        Rational::new(BigInt::from(killed), BigInt::from(panel.mutants.len()))
    };
    checks.record(
        "no_false_rejection",
        false_rejections == 0,
        &Datum::from(false_rejections),
    );
    checks.record("kill_rate_meets_bar", rate >= panel.bar, &plain(&rate));
    let detail = Datum::map([
        ("kill_rate", plain(&rate)),
        ("false_rejections", Datum::from(false_rejections)),
        ("mutants", Datum::from(panel.mutants.len())),
    ]);
    Ok(checks.judge("CHECKER_ACCEPTED", detail))
}
