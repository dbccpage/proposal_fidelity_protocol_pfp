//! WF44, exact certificate presets: check a certificate against a registered exact schema, and
//! check its types before any equation.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf44:v1
//!
//! The task names one of three schemas:
//!
//! * `coboundary_potential`: `phi`, a value per vertex, with `c` its coboundary on every edge.
//! * `l1_dual_circulation`: `f` per vertex and `r`, `z` per edge, with `r = w + delta f`, `z` a
//!   circulation (no net flow at any vertex), `|z| <= cap` on every edge, and
//!   `w . z = sum of cap |r|`. By weak duality `r` is then a nearest point to `w`.
//! * `canonical_rational`: `x`, the one solution of `A x = b`, each entry written in canonical
//!   form: an integer, or `p/q` in lowest terms with `q` above 1.
//!
//! The host records `no_float` (no number with a fraction or an exponent, and no text written
//! like one, anywhere in the certificate) and refuses a failure as `FLOAT_IN_CERTIFICATE`. It
//! then records `well_typed` (the reply names the task's schema, and the certificate has
//! exactly the schema's fields, each of the right shape with entries that are integers or text
//! `p/q`) and refuses a failure as `ILL_TYPED`. Only then are the schema's equations
//! evaluated, each as its own predicate, and the run is certified as `CERTIFICATE_VALID` when
//! all pass.
//!
//! Task: `schema`, and for the first `edges` (pairs of text) and `c`; for the second `edges`,
//! `w` and optionally `cap` (1 on every edge when absent); for the third `A` and `b` as in WF7.
//! Reply: `{"schema": name, "certificate": {...}}`.

use num_traits::{Signed, Zero};

use crate::datum::Datum;
use crate::exact::{classify_linear, rational, rationals, Rational, Solvability};

use super::labelled::{self, Labelled};
use super::wf07;
use super::{no_reply, refused, Checks, Family, Run, Stop, Verdict};

/// The registered schemas.
pub const SCHEMAS: [&str; 3] = [
    "coboundary_potential",
    "l1_dual_circulation",
    "canonical_rational",
];

pub const FAMILY: Family = Family {
    workflow: "WF44",
    name: "Exact certificate presets",
    host_check: "exact_certificate_presets",
    validate,
    walk,
};

/// What a task asks to have certified.
enum Preset {
    Coboundary {
        graph: Labelled,
        values: Vec<Rational>,
    },
    Dual {
        graph: Labelled,
        weights: Vec<Rational>,
        caps: Vec<Rational>,
    },
    Canonical {
        rows: Vec<Vec<Rational>>,
        right: Vec<Rational>,
    },
}

fn on_edges(task: &Datum, key: &str, graph: &Labelled) -> Result<Vec<Rational>, String> {
    task.get(key)
        .and_then(rationals)
        .filter(|values| values.len() == graph.graph.edges().len())
        .ok_or(format!("{key} must be one exact rational per edge"))
}

fn preset(task: &Datum) -> Result<Preset, String> {
    let schema = task.get("schema").and_then(Datum::as_text);
    let schema = schema.filter(|schema| SCHEMAS.contains(schema));
    let schema = schema.ok_or("unknown certificate schema")?;
    if schema == "canonical_rational" {
        let (rows, right) = wf07::system(task)?;
        return Ok(Preset::Canonical { rows, right });
    }
    let graph = task
        .get("edges")
        .and_then(labelled::read)
        .ok_or("edges must be a list of pairs of text")?;
    if schema == "coboundary_potential" {
        let values = on_edges(task, "c", &graph)?;
        return Ok(Preset::Coboundary { graph, values });
    }
    let weights = on_edges(task, "w", &graph)?;
    let caps = match task.get("cap") {
        Some(_) => on_edges(task, "cap", &graph)?,
        None => vec![Rational::from_integer(1.into()); weights.len()],
    };
    Ok(Preset::Dual {
        graph,
        weights,
        caps,
    })
}

fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    preset(task).map(|_| ())
}

/// Whether text is written like a decimal: an optional sign, then digits round a point, or
/// digits with an optional fraction and an exponent.
fn floatish(text: &str) -> bool {
    let body = text.strip_prefix(['-', '+']).unwrap_or(text);
    let digits = |part: &str| part.bytes().all(|byte| byte.is_ascii_digit());
    let pointed = |part: &str| {
        part.split_once('.')
            .is_some_and(|(whole, rest)| digits(whole) && digits(rest))
    };
    if pointed(body) {
        return true;
    }
    let Some((mantissa, exponent)) = body.split_once(['e', 'E']) else {
        return false;
    };
    let exponent = exponent.strip_prefix(['-', '+']).unwrap_or(exponent);
    let whole = mantissa
        .split_once('.')
        .map_or(mantissa, |(whole, _)| whole);
    let mantissa = !whole.is_empty() && (digits(mantissa) || pointed(mantissa));
    mantissa && !exponent.is_empty() && digits(exponent)
}

/// Whether a value holds a decimal number, or text written like one, at any depth.
fn has_float(value: &Datum) -> bool {
    match value {
        Datum::Decimal(_) => true,
        Datum::Text(text) => floatish(text),
        Datum::List(items) => items.iter().any(has_float),
        Datum::Map(entries) => entries.values().any(has_float),
        _ => false,
    }
}

/// The rational an entry denotes when it is typed as one: an integer, or text `p/q` whose
/// denominator does not start with 0.
fn typed(entry: &Datum) -> Option<Rational> {
    let padded = |text: &str| {
        text.split_once('/')
            .is_some_and(|(_, bottom)| bottom.starts_with('0'))
    };
    match entry {
        Datum::Text(text) if padded(text) => None,
        other => rational(other),
    }
}

/// A list of `count` typed entries.
fn vector(listed: &Datum, count: usize) -> Option<Vec<Rational>> {
    let entries: Option<Vec<Rational>> = listed.as_list()?.iter().map(typed).collect();
    entries.filter(|entries| entries.len() == count)
}

/// A typed entry under each vertex name and under nothing else.
fn vertex_map(graph: &Labelled, listed: &Datum) -> Option<Vec<Rational>> {
    graph
        .by_name(listed, typed)
        .filter(|_| graph.covers(listed))
}

/// The certificate's entries when it has exactly these fields.
fn fields<'c, const N: usize>(certificate: &'c Datum, names: [&str; N]) -> Option<[&'c Datum; N]> {
    let Datum::Map(entries) = certificate else {
        return None;
    };
    let found: Vec<&Datum> = names.iter().filter_map(|name| entries.get(*name)).collect();
    <[&Datum; N]>::try_from(found)
        .ok()
        .filter(|_| entries.len() == N)
}

/// A rational as canonical text: an integer, or `p/q` in lowest terms.
fn canonical(value: &Rational) -> String {
    if value.is_integer() {
        value.numer().to_string()
    } else {
        format!("{}/{}", value.numer(), value.denom())
    }
}

fn dot(left: &[Rational], right: &[Rational]) -> Rational {
    left.iter().zip(right).map(|(a, b)| a * b).sum()
}

/// The equations of a schema with whether each holds, in the order they are recorded.
type Equations = Vec<(&'static str, bool)>;

/// `coboundary_potential`: nothing unless the certificate is `phi`, a value on every vertex.
fn coboundary(graph: &Labelled, values: &[Rational], certificate: &Datum) -> Option<Equations> {
    let [phi] = fields(certificate, ["phi"])?;
    let potential = vertex_map(graph, phi)?;
    let exact = graph.graph.coboundary(&potential) == values;
    Some(vec![("coboundary_matches", exact)])
}

/// The net flow into every vertex is zero.
fn circulation(graph: &Labelled, flow: &[Rational]) -> bool {
    let mut net = vec![Rational::zero(); graph.names().len()];
    for (&(tail, head), amount) in graph.graph.edges().iter().zip(flow) {
        if let Some(at) = net.get_mut(tail) {
            *at -= amount;
        }
        if let Some(at) = net.get_mut(head) {
            *at += amount;
        }
    }
    net.iter().all(Zero::is_zero)
}

/// `l1_dual_circulation`: nothing unless the certificate is `f` on every vertex and `r`, `z` on
/// every edge.
fn dual(
    graph: &Labelled,
    weights: &[Rational],
    caps: &[Rational],
    certificate: &Datum,
) -> Option<Equations> {
    let [f, r, z] = fields(certificate, ["f", "r", "z"])?;
    let potential = vertex_map(graph, f)?;
    let residual = vector(r, weights.len())?;
    let flow = vector(z, weights.len())?;
    let lifted = graph.graph.coboundary(&potential);
    let expected = weights
        .iter()
        .zip(&lifted)
        .map(|(weight, step)| weight + step);
    let within = flow
        .iter()
        .zip(caps)
        .all(|(amount, cap)| amount.abs() <= *cap);
    let sizes: Vec<Rational> = residual.iter().map(Signed::abs).collect();
    Some(vec![
        (
            "residual_is_w_plus_Bf",
            expected.eq(residual.iter().cloned()),
        ),
        ("dual_is_circulation", circulation(graph, &flow)),
        ("dual_within_caps", within),
        ("duality_gap_zero", dot(weights, &flow) == dot(caps, &sizes)),
    ])
}

/// `canonical_rational`: nothing unless the certificate is `x`, a value for every unknown.
fn canonical_rational(
    rows: &[Vec<Rational>],
    right: &[Rational],
    certificate: &Datum,
) -> Option<Equations> {
    let [x] = fields(certificate, ["x"])?;
    let values = vector(x, rows.first().map_or(0, Vec::len))?;
    let solvability = classify_linear(rows, right).solvability;
    let written = x.as_list()?.iter().zip(&values);
    let plain = written.into_iter().all(|(entry, value)| match entry {
        Datum::Text(text) => *text == canonical(value),
        _ => true,
    });
    Some(vec![
        (
            "unique_solution",
            matches!(solvability, Solvability::Unique(_)),
        ),
        (
            "values_equal_solution",
            solvability == Solvability::Unique(values),
        ),
        ("canonical_form", plain),
    ])
}

impl Preset {
    fn name(&self) -> &'static str {
        match self {
            Preset::Coboundary { .. } => "coboundary_potential",
            Preset::Dual { .. } => "l1_dual_circulation",
            Preset::Canonical { .. } => "canonical_rational",
        }
    }

    /// The schema's equations for a certificate, or nothing when the certificate does not have
    /// exactly the schema's fields, each of the schema's type.
    fn equations(&self, certificate: &Datum) -> Option<Equations> {
        match self {
            Preset::Coboundary { graph, values } => coboundary(graph, values, certificate),
            Preset::Dual {
                graph,
                weights,
                caps,
            } => dual(graph, weights, caps, certificate),
            Preset::Canonical { rows, right } => canonical_rational(rows, right, certificate),
        }
    }
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let preset = preset(run.task).map_err(Stop::Malformed)?;
    let Some(reply) = run.ask("solve", run.prompt())? else {
        return Ok(no_reply());
    };
    let certificate = reply
        .get("certificate")
        .filter(|certificate| certificate.is_map())
        .ok_or_else(|| Stop::Malformed("certificate".to_owned()))?;
    if !checks.record("no_float", !has_float(certificate), &Datum::Null) {
        return Ok(refused("FLOAT_IN_CERTIFICATE", Datum::map([])));
    }
    let named = reply.get("schema").and_then(Datum::as_text) == Some(preset.name());
    let equations = preset.equations(certificate).filter(|_| named);
    checks.record("well_typed", equations.is_some(), reply);
    let Some(equations) = equations else {
        return Ok(refused("ILL_TYPED", Datum::map([])));
    };
    for (name, holds) in equations {
        checks.record(name, holds, certificate);
    }
    let detail = Datum::map([("schema", Datum::from(preset.name()))]);
    Ok(checks.judge("CERTIFICATE_VALID", detail))
}
