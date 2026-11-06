//! §4 — the replica-extensive hierarchy RE1–RE5, audited exhaustively on a
//! declared finite exact grid, with the two countermodels: dropping RE3
//! (the `ℓ²` diagnostic keeps RE5 and breaks additivity) and dropping RE5
//! (the scaled sum `c·Σ j_e`, `c ≠ 1`, keeps additivity and breaks
//! calibration).
//!
//! Replicates `replica_hierarchy.py`.  Ledger D1/D3/D4 (nine grid points,
//! all five axioms for the unweighted sum; the weighted sum keeps RE3 and
//! RE4 and fails RE5), D2/D5 (RE3 and RE5 identities), D6 (countermodels).
//!
//! The `ℓ²` countermodel produces surds.  The Python engine compares them
//! in a canonical form with interval arithmetic; here a `Surd` is a finite
//! sum `Σ bᵢ√cᵢ` with squarefree radicands, and its sign is decided
//! exactly by recursive squaring.  The recursion is bounded by a declared
//! depth and refuses beyond it — the fixture needs three terms.
//!
//! The estate's reading: the audit is an *exhaustion* certificate over the
//! declared grid (`⊢ᴱ`, L10 — exhaustive over a declared finite space or a
//! conditional scope, never a third thing); the countermodels are what the
//! estate calls countermodels; the hierarchy's general independence is
//! not claimed by any of it.

use std::collections::BTreeMap;
use std::fmt;

use super::matrix::combinations;
use super::rational::{q, Rational};
use crate::certificate::{Bound, Certificate, SpaceId};

/// The declared recursion depth for surd sign decisions.
pub const SURD_DEPTH: usize = 12;

/// A finite sum `Σ bᵢ √cᵢ` with squarefree integer radicands; `c = 1` is
/// the rational part.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Surd {
    terms: BTreeMap<i128, Rational>,
}

fn squarefree(n: i128) -> (i128, i128) {
    // n = outside² · radicand
    assert!(n >= 0, "square roots of negative values are not supported");
    let (mut outside, mut radicand, mut remaining) = (1i128, 1i128, n);
    let mut f = 2i128;
    while f * f <= remaining {
        if remaining % f == 0 {
            let mut count = 0;
            while remaining % f == 0 {
                remaining /= f;
                count += 1;
            }
            outside *= f.pow((count / 2) as u32);
            if count % 2 == 1 {
                radicand *= f;
            }
        }
        f += 1;
    }
    if remaining > 1 {
        radicand *= remaining;
    }
    (outside, radicand)
}

impl Surd {
    /// A rational.
    pub fn rational(r: Rational) -> Surd {
        let mut terms = BTreeMap::new();
        if !r.is_zero() {
            terms.insert(1, r);
        }
        Surd { terms }
    }

    /// Zero.
    pub fn zero() -> Surd {
        Surd { terms: BTreeMap::new() }
    }

    /// `√r` for `r ≥ 0`, reduced: `√8 = 2√2`, `√(9/4) = 3/2`.
    pub fn sqrt(r: Rational) -> Surd {
        assert!(r >= Rational::ZERO, "square roots of negative values are not supported");
        if r.is_zero() {
            return Surd::zero();
        }
        let (p, d) = (r.numerator(), r.denominator());
        let (outside, radicand) = squarefree(p * d);
        Surd::term(Rational::new(outside, d), radicand)
    }

    fn term(coefficient: Rational, radicand: i128) -> Surd {
        let mut terms = BTreeMap::new();
        if !coefficient.is_zero() {
            terms.insert(radicand, coefficient);
        }
        Surd { terms }
    }

    /// Is zero.
    pub fn is_zero(&self) -> bool {
        self.terms.values().all(|c| c.is_zero())
    }

    /// The rational value, if there is no radical part.
    pub fn as_rational(&self) -> Option<Rational> {
        let nonzero: Vec<(&i128, &Rational)> = self.terms.iter().filter(|(_, c)| !c.is_zero()).collect();
        match nonzero.len() {
            0 => Some(Rational::ZERO),
            1 if *nonzero[0].0 == 1 => Some(*nonzero[0].1),
            _ => None,
        }
    }

    /// Sum.
    pub fn add(&self, o: &Surd) -> Surd {
        let mut terms = self.terms.clone();
        for (k, c) in &o.terms {
            let v = terms.get(k).copied().unwrap_or(Rational::ZERO) + *c;
            if v.is_zero() {
                terms.remove(k);
            } else {
                terms.insert(*k, v);
            }
        }
        Surd { terms }
    }

    /// Difference.
    pub fn sub(&self, o: &Surd) -> Surd {
        self.add(&o.scale(q(-1)))
    }

    /// Scalar multiple.
    pub fn scale(&self, c: Rational) -> Surd {
        if c.is_zero() {
            return Surd::zero();
        }
        Surd { terms: self.terms.iter().map(|(k, v)| (*k, *v * c)).collect() }
    }

    /// Product.
    pub fn mul(&self, o: &Surd) -> Surd {
        let mut out = Surd::zero();
        for (ka, ca) in &self.terms {
            for (kb, cb) in &o.terms {
                let (outside, radicand) = squarefree(ka * kb);
                out = out.add(&Surd::term(*ca * *cb * q(outside), radicand));
            }
        }
        out
    }

    fn sign_at(&self, depth: usize) -> i128 {
        assert!(depth < SURD_DEPTH, "surd sign decision beyond the declared depth {SURD_DEPTH}");
        let terms: Vec<(i128, Rational)> = self.terms.iter().filter(|(_, c)| !c.is_zero()).map(|(k, c)| (*k, *c)).collect();
        match terms.len() {
            0 => 0,
            1 => terms[0].1.signum(),
            _ => {
                let a = Surd::term(terms[0].1, terms[0].0);
                let b = Surd { terms: terms[1..].iter().copied().collect() };
                let (sa, sb) = (a.sign_at(depth + 1), b.sign_at(depth + 1));
                if sa == 0 {
                    return sb;
                }
                if sb == 0 || sa == sb {
                    return sa;
                }
                // Opposite signs: the larger square decides.
                let d = a.mul(&a).sub(&b.mul(&b)).sign_at(depth + 1);
                if d > 0 {
                    sa
                } else if d < 0 {
                    sb
                } else {
                    0
                }
            }
        }
    }

    /// Sign, decided exactly: −1, 0, or 1.
    pub fn sign(&self) -> i128 {
        self.sign_at(0)
    }

    /// `self ≥ 0`.
    pub fn is_nonnegative(&self) -> bool {
        self.sign() >= 0
    }

    /// `self > o`.
    pub fn gt(&self, o: &Surd) -> bool {
        self.sub(o).sign() > 0
    }
}

impl fmt::Display for Surd {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.is_zero() {
            return write!(f, "0");
        }
        let parts: Vec<String> = self
            .terms
            .iter()
            .filter(|(_, c)| !c.is_zero())
            .map(|(k, c)| if *k == 1 { c.to_string() } else if *c == Rational::ONE { format!("sqrt({k})") } else { format!("{c}*sqrt({k})") })
            .collect();
        write!(f, "{}", parts.join(" + "))
    }
}

/// A point of the diagnostic domain: edge → exact vector.
pub type Point = BTreeMap<String, Vec<Rational>>;

/// A local gauge `j_e`.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Gauge {
    /// `|x|` on a one-coordinate fiber.
    Absolute,
}

impl Gauge {
    /// Evaluate.
    pub fn eval(self, v: &[Rational]) -> Rational {
        match self {
            Gauge::Absolute => {
                assert_eq!(v.len(), 1, "absolute_gauge expects one coordinate");
                v[0].abs()
            }
        }
    }
}

/// A diagnostic family `J(edges, point)`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Diagnostic {
    /// `Σ_e |x_e|`.
    UnweightedL1,
    /// `Σ_e w_e |x_e|`, weights positive.
    WeightedL1(BTreeMap<String, Rational>),
    /// The exact `p = 2` drop-RE3 countermodel `√(Σ_e |x_e|²)`.
    LpCounterexample,
    /// The drop-RE5 countermodel `c·Σ_e |x_e|`, `c > 0`, `c ≠ 1`.
    ScaledSum(Rational),
}

impl Diagnostic {
    /// Weighted sum, validated.
    pub fn weighted(weights: BTreeMap<String, Rational>) -> Result<Diagnostic, String> {
        if weights.values().any(|w| *w <= Rational::ZERO) {
            return Err("weights must be strictly positive".into());
        }
        Ok(Diagnostic::WeightedL1(weights))
    }

    /// Scaled sum, validated.
    pub fn scaled(scale: Rational) -> Result<Diagnostic, String> {
        if scale <= Rational::ZERO || scale == Rational::ONE {
            return Err("the RE5 countermodel needs c>0 and c!=1".into());
        }
        Ok(Diagnostic::ScaledSum(scale))
    }

    /// Evaluate on the given edges of a point.
    pub fn eval(&self, edges: &[String], point: &Point) -> Result<Surd, String> {
        let gauge = Gauge::Absolute;
        match self {
            Diagnostic::UnweightedL1 => Ok(Surd::rational(edges.iter().fold(Rational::ZERO, |a, e| a + gauge.eval(&point[e])))),
            Diagnostic::WeightedL1(w) => {
                let missing: Vec<&String> = edges.iter().filter(|e| !w.contains_key(*e)).collect();
                if !missing.is_empty() {
                    return Err(format!("missing weights for {missing:?}"));
                }
                Ok(Surd::rational(edges.iter().fold(Rational::ZERO, |a, e| a + w[e] * gauge.eval(&point[e]))))
            }
            Diagnostic::LpCounterexample => Ok(Surd::sqrt(edges.iter().fold(Rational::ZERO, |a, e| a + gauge.eval(&point[e]).pow(2)))),
            Diagnostic::ScaledSum(c) => Ok(Surd::rational(*c * edges.iter().fold(Rational::ZERO, |a, e| a + gauge.eval(&point[e])))),
        }
    }
}

/// One failed axiom with the point that failed it.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct AxiomCounterexample {
    /// `RE1`…`RE5`.
    pub axiom: String,
    /// What failed.
    pub detail: String,
}

/// Finite exhaustive result over the declared sample grid.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ReplicaAxiomAudit {
    /// Number of full grid points.
    pub checked_points: usize,
    /// The homogeneity scalars actually inspected.
    pub checked_scalars: Vec<Rational>,
    /// RE1: faithful convex gauge (codomain, zero, homogeneity, subadditivity).
    pub re1_global_gauge: bool,
    /// RE2: equal local magnitudes give equal diagnostics.
    pub re2_local_magnitude_sufficiency: bool,
    /// RE3: additivity over every nontrivial bipartition of every union.
    pub re3_disjoint_replica_additivity: bool,
    /// RE4: type-preserving edge swaps.
    pub re4_edge_exchange_symmetry: bool,
    /// RE5: singleton calibration `J({e}) = j_e`.
    pub re5_singleton_calibration: bool,
    /// The first failure found for each failed axiom.
    pub counterexamples: Vec<AxiomCounterexample>,
}

impl ReplicaAxiomAudit {
    /// All five hold.
    pub fn all_axioms(&self) -> bool {
        self.re1_global_gauge && self.re2_local_magnitude_sufficiency && self.re3_disjoint_replica_additivity && self.re4_edge_exchange_symmetry && self.re5_singleton_calibration
    }

    /// The exhaustion certificate this audit is: the grid was the space.
    pub fn certificate(&self, family_name: &str) -> Certificate {
        Certificate::Exhaustion {
            space: SpaceId(format!("RE1-RE5 grid audit of {family_name}")),
            bound: Bound(format!("{} full points, all bipartitions, scalars ({})", self.checked_points, self.checked_scalars.iter().map(ToString::to_string).collect::<Vec<_>>().join(","))),
            searched: self.checked_points,
        }
    }
}

/// Pointwise exact identity derived from checked RE premises.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ReplicaConclusionCertificate {
    /// The edges.
    pub edge_order: Vec<String>,
    /// `J(all)`.
    pub diagnostic_value: Surd,
    /// `Σ_e J({e})`.
    pub singleton_sum: Surd,
    /// `Σ_e j_e`.
    pub local_gauge_sum: Rational,
    /// `J(all) = Σ_e J({e})`.
    pub singleton_decomposition_holds: bool,
    /// `J({e}) = j_e` for all `e`.
    pub singleton_calibration_holds: bool,
    /// Both, and hence `J(all) = Σ_e j_e`.
    pub unweighted_conclusion_holds: bool,
}

/// A diagnostic family, local gauges, and declared edge-type orbits.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct FiniteDiagnosticFamily {
    /// The edges, in declared order.
    pub edges: Vec<String>,
    /// Edge → gauge.
    pub gauges: BTreeMap<String, Gauge>,
    /// The diagnostic.
    pub diagnostic: Diagnostic,
    /// Edge → type (swaps are checked within a type).
    pub edge_types: BTreeMap<String, String>,
}

/// Edge → sample vectors.
pub type Samples = BTreeMap<String, Vec<Vec<Rational>>>;

impl FiniteDiagnosticFamily {
    /// Build and validate.
    pub fn new(edges: Vec<String>, gauges: BTreeMap<String, Gauge>, diagnostic: Diagnostic, edge_types: Option<BTreeMap<String, String>>) -> Result<FiniteDiagnosticFamily, String> {
        if edges.is_empty() {
            return Err("a diagnostic family needs at least one edge".into());
        }
        let mut s = edges.clone();
        s.sort();
        s.dedup();
        if s.len() != edges.len() {
            return Err("edge identifiers must be unique".into());
        }
        if gauges.keys().cloned().collect::<Vec<_>>() != s {
            return Err("each edge needs exactly one local gauge".into());
        }
        let edge_types = edge_types.unwrap_or_else(|| edges.iter().map(|e| (e.clone(), e.clone())).collect());
        if edge_types.keys().cloned().collect::<Vec<_>>() != s {
            return Err("edge_types must cover exactly the declared edges".into());
        }
        Ok(FiniteDiagnosticFamily { edges, gauges, diagnostic, edge_types })
    }

    /// `J(subset, point)`.
    pub fn evaluate(&self, subset: &[String], point: &Point) -> Result<Surd, String> {
        if !subset.iter().all(|e| self.edges.contains(e)) {
            return Err("diagnostic subset contains an unknown edge".into());
        }
        let mut keys: Vec<&String> = point.keys().collect();
        keys.sort();
        let mut sub: Vec<&String> = subset.iter().collect();
        sub.sort();
        if keys != sub {
            return Err("point domain must equal the diagnostic subset".into());
        }
        self.diagnostic.eval(subset, point)
    }

    fn all_points(ordered: &[String], samples: &Samples) -> Vec<Point> {
        let mut points: Vec<Point> = vec![Point::new()];
        for e in ordered {
            let mut next = Vec::new();
            for p in &points {
                for v in &samples[e] {
                    let mut np = p.clone();
                    np.insert(e.clone(), v.clone());
                    next.push(np);
                }
            }
            points = next;
        }
        points
    }

    /// Exhaustively audit RE1–RE5 on a declared finite exact grid.
    pub fn audit(&self, samples: &Samples, scalars: &[Rational]) -> Result<ReplicaAxiomAudit, String> {
        let mut keys: Vec<&String> = samples.keys().collect();
        keys.sort();
        let mut edges: Vec<&String> = self.edges.iter().collect();
        edges.sort();
        if keys != edges || self.edges.iter().any(|e| samples[e].is_empty()) {
            return Err("sample grids must be nonempty and cover every edge".into());
        }
        if scalars.is_empty() || scalars.iter().any(|s| *s < Rational::ZERO) {
            return Err("homogeneity scalars must be nonempty and nonnegative".into());
        }
        let mut counters = Vec::new();
        let full_points = Self::all_points(&self.edges, samples);
        let all = self.edges.clone();

        // RE1
        let mut re1 = true;
        let mut point_values: Vec<Surd> = Vec::new();
        let zero_point: Point = self.edges.iter().map(|e| (e.clone(), vec![Rational::ZERO; samples[e][0].len()])).collect();
        let zero_value = self.evaluate(&all, &zero_point)?;
        if !zero_value.is_nonnegative() {
            re1 = false;
            counters.push(AxiomCounterexample { axiom: "RE1".into(), detail: format!("codomain violation at zero: J={zero_value}") });
        } else if !zero_value.is_zero() {
            re1 = false;
            counters.push(AxiomCounterexample { axiom: "RE1".into(), detail: "J(0) != 0".into() });
        }
        if re1 {
            'points: for p in &full_points {
                let value = self.evaluate(&all, p)?;
                if !value.is_nonnegative() {
                    re1 = false;
                    counters.push(AxiomCounterexample { axiom: "RE1".into(), detail: format!("codomain violation J={value} at {p:?}") });
                    break;
                }
                point_values.push(value.clone());
                if value.is_zero() != (*p == zero_point) {
                    re1 = false;
                    counters.push(AxiomCounterexample { axiom: "RE1".into(), detail: format!("faithfulness failed at {p:?}") });
                    break;
                }
                for &s in scalars {
                    let scaled: Point = p.iter().map(|(e, v)| (e.clone(), v.iter().map(|x| *x * s).collect())).collect();
                    let sv = self.evaluate(&all, &scaled)?;
                    if !sv.is_nonnegative() {
                        re1 = false;
                        counters.push(AxiomCounterexample { axiom: "RE1".into(), detail: format!("codomain violation J={sv} at scaled point {p:?}, lambda={s}") });
                        break 'points;
                    }
                    if !sv.sub(&value.scale(s)).is_zero() {
                        re1 = false;
                        counters.push(AxiomCounterexample { axiom: "RE1".into(), detail: format!("positive homogeneity failed at {p:?}, lambda={s}") });
                        break 'points;
                    }
                }
            }
        }
        if re1 {
            'pairs: for (li, left) in full_points.iter().enumerate() {
                for (ri, right) in full_points.iter().enumerate() {
                    let summed: Point = left.iter().map(|(e, v)| (e.clone(), v.iter().zip(&right[e]).map(|(a, b)| *a + *b).collect())).collect();
                    let lhs = self.evaluate(&all, &summed)?;
                    if !lhs.is_nonnegative() {
                        re1 = false;
                        counters.push(AxiomCounterexample { axiom: "RE1".into(), detail: format!("codomain violation J={lhs} at sum {left:?}+{right:?}") });
                        break 'pairs;
                    }
                    let rhs = point_values[li].add(&point_values[ri]);
                    if lhs.gt(&rhs) {
                        re1 = false;
                        counters.push(AxiomCounterexample { axiom: "RE1".into(), detail: format!("subadditivity failed at {left:?}, {right:?}") });
                        break 'pairs;
                    }
                }
            }
        }

        // RE2
        let mut re2 = true;
        're2: for pair in combinations(full_points.len(), 2) {
            let (left, right) = (&full_points[pair[0]], &full_points[pair[1]]);
            let lm: Vec<Rational> = self.edges.iter().map(|e| self.gauges[e].eval(&left[e])).collect();
            let rm: Vec<Rational> = self.edges.iter().map(|e| self.gauges[e].eval(&right[e])).collect();
            if lm == rm && !self.evaluate(&all, left)?.sub(&self.evaluate(&all, right)?).is_zero() {
                re2 = false;
                counters.push(AxiomCounterexample { axiom: "RE2".into(), detail: format!("equal magnitudes differed at {left:?}, {right:?}") });
                break 're2;
            }
        }

        // RE3: every unique nontrivial bipartition of every declared union.
        let mut re3 = true;
        're3: for union_size in 2..=self.edges.len() {
            for union_idx in combinations(self.edges.len(), union_size) {
                let union: Vec<String> = union_idx.iter().map(|&i| self.edges[i].clone()).collect();
                let union_points = Self::all_points(&union, samples);
                let anchor = &union[0];
                for left_size in 1..union.len() {
                    for left_idx in combinations(union.len(), left_size) {
                        let left: Vec<String> = left_idx.iter().map(|&i| union[i].clone()).collect();
                        if !left.contains(anchor) {
                            continue;
                        }
                        let right: Vec<String> = union.iter().filter(|e| !left.contains(e)).cloned().collect();
                        for p in &union_points {
                            let lp: Point = left.iter().map(|e| (e.clone(), p[e].clone())).collect();
                            let rp: Point = right.iter().map(|e| (e.clone(), p[e].clone())).collect();
                            let defect = self.evaluate(&union, p)?.sub(&self.evaluate(&left, &lp)?).sub(&self.evaluate(&right, &rp)?);
                            if !defect.is_zero() {
                                re3 = false;
                                counters.push(AxiomCounterexample { axiom: "RE3".into(), detail: format!("disjoint additivity defect {defect} on union {union:?} for {left:?}|{right:?}") });
                                break 're3;
                            }
                        }
                    }
                }
            }
        }

        // RE4: pairwise swaps inside a declared type orbit.
        let mut re4 = true;
        're4: for i in 0..self.edges.len() {
            for j in i + 1..self.edges.len() {
                let (le, re) = (&self.edges[i], &self.edges[j]);
                if self.edge_types[le] != self.edge_types[re] {
                    continue;
                }
                for p in &full_points {
                    let mut swapped = p.clone();
                    swapped.insert(le.clone(), p[re].clone());
                    swapped.insert(re.clone(), p[le].clone());
                    if !self.evaluate(&all, p)?.sub(&self.evaluate(&all, &swapped)?).is_zero() {
                        re4 = false;
                        counters.push(AxiomCounterexample { axiom: "RE4".into(), detail: format!("type-preserving swap {le}<->{re} failed") });
                        break 're4;
                    }
                }
            }
        }

        // RE5: exact singleton calibration.
        let mut re5 = true;
        're5: for e in &self.edges {
            for v in &samples[e] {
                let single = vec![e.clone()];
                let dv = self.evaluate(&single, &Point::from([(e.clone(), v.clone())]))?;
                let gv = self.gauges[e].eval(v);
                if !dv.sub(&Surd::rational(gv)).is_zero() {
                    re5 = false;
                    counters.push(AxiomCounterexample { axiom: "RE5".into(), detail: format!("singleton {e} has J={dv}, j={gv}") });
                    break 're5;
                }
            }
        }

        Ok(ReplicaAxiomAudit {
            checked_points: full_points.len(),
            checked_scalars: scalars.to_vec(),
            re1_global_gauge: re1,
            re2_local_magnitude_sufficiency: re2,
            re3_disjoint_replica_additivity: re3,
            re4_edge_exchange_symmetry: re4,
            re5_singleton_calibration: re5,
            counterexamples: counters,
        })
    }

    /// Recompute the RE3 and RE3+RE5 conclusions at one exact point.
    pub fn conclusion_certificate(&self, point: &Point) -> Result<ReplicaConclusionCertificate, String> {
        let mut keys: Vec<&String> = point.keys().collect();
        keys.sort();
        let mut edges: Vec<&String> = self.edges.iter().collect();
        edges.sort();
        if keys != edges {
            return Err("point must cover the full edge family".into());
        }
        let value = self.evaluate(&self.edges, point)?;
        let mut singles = Vec::new();
        for e in &self.edges {
            singles.push(self.evaluate(std::slice::from_ref(e), &Point::from([(e.clone(), point[e].clone())]))?);
        }
        let singleton_sum = singles.iter().fold(Surd::zero(), |a, s| a.add(s));
        let local_sum = self.edges.iter().fold(Rational::ZERO, |a, e| a + self.gauges[e].eval(&point[e]));
        let calibration = self.edges.iter().zip(&singles).all(|(e, s)| s.sub(&Surd::rational(self.gauges[e].eval(&point[e]))).is_zero());
        let decomposition = value.sub(&singleton_sum).is_zero();
        Ok(ReplicaConclusionCertificate {
            edge_order: self.edges.clone(),
            unweighted_conclusion_holds: decomposition && calibration && value.sub(&Surd::rational(local_sum)).is_zero(),
            diagnostic_value: value,
            singleton_sum,
            local_gauge_sum: local_sum,
            singleton_decomposition_holds: decomposition,
            singleton_calibration_holds: calibration,
        })
    }
}

/// The receipt grid: edges `e1, e2`, samples `{-1, 0, 1}` on each, both
/// of type `same`.
pub fn receipt_samples() -> (Vec<String>, BTreeMap<String, Gauge>, BTreeMap<String, String>, Samples) {
    let edges = vec!["e1".to_string(), "e2".to_string()];
    let gauges = edges.iter().map(|e| (e.clone(), Gauge::Absolute)).collect();
    let types = edges.iter().map(|e| (e.clone(), "same".to_string())).collect();
    let samples = edges.iter().map(|e| (e.clone(), vec![vec![q(-1)], vec![q(0)], vec![q(1)]])).collect();
    (edges, gauges, types, samples)
}

/// The default homogeneity scalars `(0, 1, 2)`.
pub fn default_scalars() -> Vec<Rational> {
    vec![q(0), q(1), q(2)]
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::alpha_projection_obstruction::rational::r;

    #[test]
    fn surds_reduce_and_compare_exactly() {
        assert_eq!(Surd::sqrt(q(8)).to_string(), "2*sqrt(2)");
        assert_eq!(Surd::sqrt(r(9, 4)).as_rational(), Some(r(3, 2)));
        assert_eq!(Surd::sqrt(q(2)).mul(&Surd::sqrt(q(2))).as_rational(), Some(q(2)));
        // sqrt(5) < 1 + sqrt(2)
        let lhs = Surd::sqrt(q(5));
        let rhs = Surd::rational(q(1)).add(&Surd::sqrt(q(2)));
        assert!(!lhs.gt(&rhs));
        assert!(rhs.gt(&lhs));
        // sqrt(2) - 2 < 0
        assert_eq!(Surd::sqrt(q(2)).sub(&Surd::rational(q(2))).sign(), -1);
        assert_eq!(Surd::sqrt(q(2)).sub(&Surd::sqrt(q(2))).sign(), 0);
    }

    /// D1/D3/D4: nine points; the unweighted sum passes all five; the
    /// weighted sum keeps RE3, RE4 and fails RE5.
    #[test]
    fn the_unweighted_sum_passes_all_five_and_the_weighted_sum_fails_re5() {
        let (edges, gauges, types, samples) = receipt_samples();
        let unweighted = FiniteDiagnosticFamily::new(edges.clone(), gauges.clone(), Diagnostic::UnweightedL1, Some(types.clone())).unwrap();
        let a = unweighted.audit(&samples, &default_scalars()).unwrap();
        assert_eq!(a.checked_points, 9);
        assert!(a.all_axioms(), "{:?}", a.counterexamples);
        assert_eq!(a.certificate("unweighted").kind(), crate::certificate::CertKind::Exhaustion);
        let weights = edges.iter().map(|e| (e.clone(), q(2))).collect();
        let weighted = FiniteDiagnosticFamily::new(edges.clone(), gauges.clone(), Diagnostic::weighted(weights).unwrap(), Some(types.clone())).unwrap();
        let w = weighted.audit(&samples, &default_scalars()).unwrap();
        assert!(w.re3_disjoint_replica_additivity && w.re4_edge_exchange_symmetry && !w.re5_singleton_calibration);
        assert_eq!(w.counterexamples[0].axiom, "RE5");
    }

    /// D6: `ℓ²` breaks RE3 and keeps RE5; the scaled sum keeps RE3 and
    /// breaks RE5.
    #[test]
    fn the_two_countermodels_break_exactly_one_axiom_each() {
        let (edges, gauges, types, samples) = receipt_samples();
        let lp = FiniteDiagnosticFamily::new(edges.clone(), gauges.clone(), Diagnostic::LpCounterexample, Some(types.clone())).unwrap();
        let a = lp.audit(&samples, &default_scalars()).unwrap();
        assert!(!a.re3_disjoint_replica_additivity && a.re5_singleton_calibration);
        assert!(a.re1_global_gauge && a.re2_local_magnitude_sufficiency && a.re4_edge_exchange_symmetry, "{:?}", a.counterexamples);
        let scaled = FiniteDiagnosticFamily::new(edges, gauges, Diagnostic::scaled(q(2)).unwrap(), Some(types)).unwrap();
        let s = scaled.audit(&samples, &default_scalars()).unwrap();
        assert!(s.re3_disjoint_replica_additivity && !s.re5_singleton_calibration);
        assert!(Diagnostic::scaled(q(1)).is_err());
        assert!(Diagnostic::weighted(BTreeMap::from([("e".to_string(), q(0))])).is_err());
    }

    /// D2/D5: the singleton decomposition and calibration at one point.
    #[test]
    fn the_conclusion_certificate_holds_pointwise_for_the_unweighted_sum() {
        let (edges, gauges, types, _) = receipt_samples();
        let f = FiniteDiagnosticFamily::new(edges, gauges, Diagnostic::UnweightedL1, Some(types)).unwrap();
        let p = Point::from([("e1".to_string(), vec![q(-3)]), ("e2".to_string(), vec![r(1, 2)])]);
        let c = f.conclusion_certificate(&p).unwrap();
        assert!(c.singleton_decomposition_holds && c.singleton_calibration_holds && c.unweighted_conclusion_holds);
        assert_eq!(c.local_gauge_sum, r(7, 2));
        assert_eq!(c.diagnostic_value.as_rational(), Some(r(7, 2)));
    }
}
