//! The operad laws, checked on structure, cost and behaviour over a finite panel.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:laws:v1
//!
//! * Sequential associativity: `θ ∘_i (φ ∘_j ψ) = (θ ∘_i φ) ∘_{i+j} ψ`.
//! * Parallel associativity, `i < k`: `(θ ∘_k ψ) ∘_i φ = (θ ∘_i φ) ∘_{k + |φ| - 1} ψ`.
//! * Unit: `id ∘_0 θ = θ = θ ∘_i id`, after identity nodes are removed.
//! * Composition is evaluation: running `θ ∘_i φ` equals running `φ` first and feeding its value
//!   to `θ`, and the cost of the composite is the sum of the two costs.
//! * Symmetry: an operation declared `Symmetric` gives the same output when two neighbouring
//!   inputs of one colour are swapped.
//!
//! Two terms agree when they return the same value, or refuse with the same code, on every panel
//! assignment, their costs are equal, and their normal forms are equal.

use std::collections::BTreeMap;

use serde::Serialize;

use crate::term::{Colour, Operation, Term, Value, Variant};
use crate::Refusal;

/// The most pairs of terms one battery compares before it refuses.
pub const MAX_CHECKS: u64 = 100_000;

/// Sample values for each colour.
#[derive(Debug, Clone, Default)]
pub struct Panel(BTreeMap<Colour, Vec<Value>>);

impl Panel {
    pub fn insert(&mut self, colour: Colour, samples: Vec<Value>) {
        self.0.insert(colour, samples);
    }

    /// One input vector per round: leaf `l` in round `k` takes sample `(k + l) mod n` of its colour.
    pub fn assignments(&self, leaves: &[&Colour]) -> Result<Vec<Vec<Value>>, Refusal> {
        let mut columns = Vec::with_capacity(leaves.len());
        for colour in leaves {
            match self.0.get(*colour) {
                Some(samples) if !samples.is_empty() => columns.push(samples),
                _ => {
                    return Err(Refusal::new(
                        "NO_SAMPLES",
                        format!("the panel has no {} value", colour.name()),
                    ))
                }
            }
        }
        let rounds = columns
            .iter()
            .map(|samples| samples.len())
            .max()
            .unwrap_or(1);
        Ok((0..rounds)
            .map(|round| {
                columns
                    .iter()
                    .enumerate()
                    // In bounds: the index is reduced modulo the column's nonzero length.
                    .map(|(leaf, samples)| samples[(round + leaf) % samples.len()].clone())
                    .collect()
            })
            .collect())
    }
}

/// What a term does on one input vector: a value, or the code it refuses with.
fn outcome(term: &Term, inputs: &[Value]) -> Result<Value, &'static str> {
    term.eval(inputs).map_err(|refusal| refusal.code)
}

/// `None` when the two terms agree; otherwise the first difference found: in value, cost or tree.
pub fn compare(left: &Term, right: &Term, panel: &Panel) -> Result<Option<String>, Refusal> {
    for inputs in panel.assignments(&left.leaves())? {
        if outcome(left, &inputs) != outcome(right, &inputs) {
            return Ok(Some(format!("the two sides differ on inputs {inputs:?}")));
        }
    }
    if left.cost()? != right.cost()? {
        return Ok(Some("the two sides have different costs".to_owned()));
    }
    if left.normalise() != right.normalise() {
        return Ok(Some("the two sides are different trees".to_owned()));
    }
    Ok(None)
}

/// Run `inner` on its share of the inputs, then run `outer` with that value in input `slot`.
/// `None` when either run refuses or the inputs do not cover both terms.
fn in_two_steps(outer: &Term, slot: usize, inner: &Term, inputs: &[Value]) -> Option<Value> {
    let end = slot + inner.leaves().len();
    let value = inner.eval(inputs.get(slot..end)?).ok()?;
    let mut fed = inputs.get(..slot)?.to_vec();
    fed.push(value);
    fed.extend_from_slice(inputs.get(end..)?);
    outer.eval(&fed).ok()
}

/// `None` when running `outer ∘_slot inner` equals running `inner` first and feeding `outer`, and
/// costs add. A refusal equals any refusal here: the two runs may meet their refusals in a
/// different order.
pub fn composition_defect(
    outer: &Term,
    slot: usize,
    inner: &Term,
    panel: &Panel,
) -> Result<Option<String>, Refusal> {
    let whole = outer.substitute(slot, inner)?;
    if outer.cost()?.checked_add(inner.cost()?) != Some(whole.cost()?) {
        return Ok(Some(
            "the cost of the composite is not the sum of the parts".to_owned(),
        ));
    }
    for inputs in panel.assignments(&whole.leaves())? {
        if whole.eval(&inputs).ok() != in_two_steps(outer, slot, inner, &inputs) {
            return Ok(Some(format!(
                "the composite and the two-step run differ on inputs {inputs:?}"
            )));
        }
    }
    Ok(None)
}

/// Both bracketings of `θ ∘_i φ ∘_j ψ`.
pub fn sequential(
    theta: &Operation,
    i: usize,
    phi: &Operation,
    j: usize,
    psi: &Operation,
) -> Result<(Term, Term), Refusal> {
    let (theta, phi, psi) = (Term::corolla(theta), Term::corolla(phi), Term::corolla(psi));
    let left = theta.substitute(i, &phi.substitute(j, &psi)?)?;
    let right = theta.substitute(i, &phi)?.substitute(i + j, &psi)?;
    Ok((left, right))
}

/// Both orders of plugging `φ` into input `i` and `ψ` into input `k` of `θ`, for `i < k`.
pub fn parallel(
    theta: &Operation,
    i: usize,
    phi: &Operation,
    k: usize,
    psi: &Operation,
) -> Result<(Term, Term), Refusal> {
    if i >= k {
        return Err(Refusal::new(
            "SLOT_ORDER",
            "parallel composition needs i < k",
        ));
    }
    let shifted = k + phi.sources().len() - 1;
    let (theta, phi, psi) = (Term::corolla(theta), Term::corolla(phi), Term::corolla(psi));
    let left = theta.substitute(k, &psi)?.substitute(i, &phi)?;
    let right = theta.substitute(i, &phi)?.substitute(shifted, &psi)?;
    Ok((left, right))
}

/// One failed law instance.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Violation {
    pub law: &'static str,
    pub operations: Vec<String>,
    pub slots: Vec<usize>,
    pub detail: String,
}

/// How many instances of each law were checked, and every one that failed.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize)]
pub struct LawReport {
    pub sequential: u64,
    pub parallel: u64,
    pub unit: u64,
    pub composition: u64,
    pub symmetry: u64,
    pub violations: Vec<Violation>,
    #[serde(skip)]
    limit: u64,
}

impl LawReport {
    pub fn holds(&self) -> bool {
        self.violations.is_empty()
    }

    /// The pairs of terms compared so far (symmetry checks are bounded by the operations' arity).
    fn compared(&self) -> u64 {
        self.sequential + self.parallel + self.unit
    }

    fn record(
        &mut self,
        law: &'static str,
        operations: &[&Operation],
        slots: &[usize],
        sides: (Term, Term),
        panel: &Panel,
    ) -> Result<(), Refusal> {
        if self.compared() >= self.limit {
            return Err(Refusal::new(
                "BATTERY_TOO_LARGE",
                format!("more than {} law instances", self.limit),
            ));
        }
        match law {
            "sequential_associativity" => self.sequential += 1,
            "parallel_associativity" => self.parallel += 1,
            "unit" => self.unit += 1,
            _ => self.symmetry += 1,
        }
        if let Some(detail) = compare(&sides.0, &sides.1, panel)? {
            self.violations.push(Violation {
                law,
                operations: operations
                    .iter()
                    .map(|operation| operation.name().to_owned())
                    .collect(),
                slots: slots.to_vec(),
                detail,
            });
        }
        Ok(())
    }
}

/// The operations whose target fits input `slot` of `theta`.
fn fitting<'a>(
    operations: &'a [Operation],
    theta: &'a Operation,
    slot: usize,
) -> impl Iterator<Item = &'a Operation> {
    operations
        .iter()
        .filter(move |candidate| theta.sources().get(slot) == Some(candidate.target()))
}

fn check_composition(
    report: &mut LawReport,
    theta: &Operation,
    slot: usize,
    phi: &Operation,
    panel: &Panel,
) -> Result<(), Refusal> {
    report.composition += 1;
    if let Some(detail) =
        composition_defect(&Term::corolla(theta), slot, &Term::corolla(phi), panel)?
    {
        report.violations.push(Violation {
            law: "composition",
            operations: vec![theta.name().to_owned(), phi.name().to_owned()],
            slots: vec![slot],
            detail,
        });
    }
    Ok(())
}

fn check_units(report: &mut LawReport, theta: &Operation, panel: &Panel) -> Result<(), Refusal> {
    let term = Term::corolla(theta);
    let outer = Term::corolla(&Operation::identity(theta.target())).substitute(0, &term)?;
    report.record("unit", &[theta], &[], (outer, term.clone()), panel)?;
    for (slot, colour) in theta.sources().iter().enumerate() {
        let inner = term.substitute(slot, &Term::corolla(&Operation::identity(colour)))?;
        report.record("unit", &[theta], &[slot], (inner, term.clone()), panel)?;
    }
    Ok(())
}

fn check_symmetry(report: &mut LawReport, theta: &Operation, panel: &Panel) -> Result<(), Refusal> {
    if theta.variant() != Variant::Symmetric {
        return Ok(());
    }
    let term = Term::corolla(theta);
    for (slot, pair) in theta.sources().windows(2).enumerate() {
        let [left, right] = pair else { continue };
        if left != right {
            continue;
        }
        report.symmetry += 1;
        for inputs in panel.assignments(&term.leaves())? {
            let mut swapped = inputs.clone();
            // In bounds: `inputs` holds one value per source, and `slot + 1` indexes a source.
            swapped.swap(slot, slot + 1);
            if outcome(&term, &inputs) != outcome(&term, &swapped) {
                report.violations.push(Violation {
                    law: "symmetry",
                    operations: vec![theta.name().to_owned()],
                    slots: vec![slot, slot + 1],
                    detail: format!("swapping the two inputs changes the output on {inputs:?}"),
                });
                break;
            }
        }
    }
    Ok(())
}

/// Check every law instance the operations admit, on the panel.
pub fn run_battery(operations: &[Operation], panel: &Panel) -> Result<LawReport, Refusal> {
    run_battery_within(operations, panel, MAX_CHECKS)
}

/// [`run_battery`] with a caller-chosen bound on the number of law instances.
pub fn run_battery_within(
    operations: &[Operation],
    panel: &Panel,
    limit: u64,
) -> Result<LawReport, Refusal> {
    let mut report = LawReport {
        limit,
        ..LawReport::default()
    };
    for theta in operations {
        check_units(&mut report, theta, panel)?;
        check_symmetry(&mut report, theta, panel)?;
        for i in 0..theta.sources().len() {
            for phi in fitting(operations, theta, i) {
                check_composition(&mut report, theta, i, phi, panel)?;
                for j in 0..phi.sources().len() {
                    for psi in fitting(operations, phi, j) {
                        let sides = sequential(theta, i, phi, j, psi)?;
                        report.record(
                            "sequential_associativity",
                            &[theta, phi, psi],
                            &[i, j],
                            sides,
                            panel,
                        )?;
                    }
                }
                for k in i + 1..theta.sources().len() {
                    for psi in fitting(operations, theta, k) {
                        let sides = parallel(theta, i, phi, k, psi)?;
                        report.record(
                            "parallel_associativity",
                            &[theta, phi, psi],
                            &[i, k],
                            sides,
                            panel,
                        )?;
                    }
                }
            }
        }
    }
    Ok(report)
}
