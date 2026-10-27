//! cptp_trajectory_verifier.rs — exact-rational CPTP trajectory and finite-report verifier.
//! Zero floats by construction: no f32/f64 appears in this file.
#![deny(clippy::float_arithmetic)]

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_9525e5aa<T> {
    fn checked_invariant_9525e5aa(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_9525e5aa<T> for Option<T> {
    #[inline]
    fn checked_invariant_9525e5aa(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_9525e5aa<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_9525e5aa(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Zero};
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use std::collections::{BTreeMap, HashMap, HashSet};
use std::str::FromStr;

pub type Q = BigRational;

/// Rational n/d from machine integers (reduced by `BigRational::new`).
pub fn q(n: i64, d: i64) -> Q {
    Q::new(BigInt::from(n), BigInt::from(d))
}

// ---------------------------------------------------------------------------
// Gaussian rationals
// ---------------------------------------------------------------------------

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct QC {
    pub re: Q,
    pub im: Q,
}

impl QC {
    pub fn zero() -> Self {
        QC {
            re: Q::zero(),
            im: Q::zero(),
        }
    }
    pub fn one() -> Self {
        QC {
            re: Q::one(),
            im: Q::zero(),
        }
    }
    pub fn real(r: Q) -> Self {
        QC {
            re: r,
            im: Q::zero(),
        }
    }
    pub fn imag(i: Q) -> Self {
        QC {
            re: Q::zero(),
            im: i,
        }
    }
    pub fn conj(&self) -> Self {
        QC {
            re: self.re.clone(),
            im: -self.im.clone(),
        }
    }
    pub fn add(&self, o: &QC) -> QC {
        QC {
            re: &self.re + &o.re,
            im: &self.im + &o.im,
        }
    }
    pub fn mul(&self, o: &QC) -> QC {
        QC {
            re: &self.re * &o.re - &self.im * &o.im,
            im: &self.re * &o.im + &self.im * &o.re,
        }
    }
    pub fn is_zero(&self) -> bool {
        self.re.is_zero() && self.im.is_zero()
    }
}

// ---------------------------------------------------------------------------
// Matrices (row-major)
// ---------------------------------------------------------------------------

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Matrix {
    pub n: usize,
    pub m: usize,
    pub a: Vec<QC>,
}

impl Matrix {
    pub fn zeros(n: usize, m: usize) -> Self {
        Matrix {
            n,
            m,
            a: vec![QC::zero(); n * m],
        }
    }

    pub fn identity(n: usize) -> Self {
        let mut z = Self::zeros(n, n);
        for i in 0..n {
            z.a[i * n + i] = QC::one();
        }
        z
    }

    pub fn from_rows(rows: Vec<Vec<QC>>) -> Self {
        let n = rows.len();
        let m = rows[0].len();
        assert!(rows.iter().all(|r| r.len() == m), "ragged rows");
        Matrix {
            n,
            m,
            a: rows.into_iter().flatten().collect(),
        }
    }

    /// Real matrix from (numerator, denominator) pairs, row-major.
    pub fn real_from(n: usize, m: usize, entries: &[(i64, i64)]) -> Self {
        assert_eq!(entries.len(), n * m);
        Matrix {
            n,
            m,
            a: entries.iter().map(|&(p, d)| QC::real(q(p, d))).collect(),
        }
    }

    pub fn get(&self, i: usize, j: usize) -> &QC {
        &self.a[i * self.m + j]
    }

    pub fn matmul(&self, b: &Matrix) -> Matrix {
        assert_eq!(self.m, b.n, "matmul shape mismatch");
        let mut out = Matrix::zeros(self.n, b.m);
        for i in 0..self.n {
            for j in 0..b.m {
                let mut s = QC::zero();
                for k in 0..self.m {
                    s = s.add(&self.get(i, k).mul(b.get(k, j)));
                }
                out.a[i * b.m + j] = s;
            }
        }
        out
    }

    pub fn dagger(&self) -> Matrix {
        let mut out = Matrix::zeros(self.m, self.n);
        for i in 0..self.n {
            for j in 0..self.m {
                out.a[j * self.n + i] = self.get(i, j).conj();
            }
        }
        out
    }

    pub fn add(&self, b: &Matrix) -> Matrix {
        assert!(self.n == b.n && self.m == b.m, "add shape mismatch");
        Matrix {
            n: self.n,
            m: self.m,
            a: self
                .a
                .iter()
                .zip(b.a.iter())
                .map(|(x, y)| x.add(y))
                .collect(),
        }
    }

    pub fn scale(&self, c: &QC) -> Matrix {
        Matrix {
            n: self.n,
            m: self.m,
            a: self.a.iter().map(|x| x.mul(c)).collect(),
        }
    }

    pub fn trace(&self) -> QC {
        assert_eq!(self.n, self.m, "trace of non-square");
        (0..self.n).fold(QC::zero(), |acc, i| acc.add(self.get(i, i)))
    }

    /// Kronecker product self ⊗ b.
    pub fn kron(&self, b: &Matrix) -> Matrix {
        let (n, m) = (self.n * b.n, self.m * b.m);
        let mut out = Matrix::zeros(n, m);
        for i1 in 0..self.n {
            for j1 in 0..self.m {
                for i2 in 0..b.n {
                    for j2 in 0..b.m {
                        out.a[(i1 * b.n + i2) * m + (j1 * b.m + j2)] =
                            self.get(i1, j1).mul(b.get(i2, j2));
                    }
                }
            }
        }
        out
    }

    /// Tr(rho^2); asserts the imaginary part vanishes (Hermitian input).
    pub fn purity_p2(&self) -> Q {
        let t = self.matmul(self).trace();
        assert!(t.im.is_zero(), "Tr(rho^2) not real");
        t.re
    }

    pub fn to_json_rows(&self) -> Vec<Vec<workpad::GaussianRationalJson>> {
        (0..self.n)
            .map(|i| {
                (0..self.m)
                    .map(|j| workpad::GaussianRationalJson::from(self.get(i, j)))
                    .collect()
            })
            .collect()
    }

    pub fn from_json_rows(rows: &[Vec<workpad::GaussianRationalJson>]) -> Self {
        let n = rows.len();
        let m = rows[0].len();
        assert!(
            rows.iter().all(|r| r.len() == m),
            "ragged rows in json matrix"
        );
        let flat: Vec<QC> = rows.iter().flat_map(|r| r.iter().map(QC::from)).collect();
        Matrix { n, m, a: flat }
    }
}

// ---------------------------------------------------------------------------
// Terminals and annotations (Round 4 priority order documented in §1.1 there)
// ---------------------------------------------------------------------------

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum Terminal {
    ReportCollision,
    LiftBudgetExhaustion,
    OverlapGluingRefusal,
    DecouplingDetected,
    TwoSignalCollapse,
    TrajectoryExhaustedNoTerminal,
}

impl Terminal {
    pub fn label(&self) -> &'static str {
        match self {
            Terminal::ReportCollision => "REPORT_COLLISION",
            Terminal::LiftBudgetExhaustion => "LIFT_BUDGET_EXHAUSTION",
            Terminal::OverlapGluingRefusal => "OVERLAP_GLUING_REFUSAL",
            Terminal::DecouplingDetected => "DECOUPLING_DETECTED",
            Terminal::TwoSignalCollapse => "TWO_SIGNAL_COLLAPSE",
            Terminal::TrajectoryExhaustedNoTerminal => "TRAJECTORY_EXHAUSTED_NO_TERMINAL",
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub enum Annotation {
    DecouplingDetected { reason: String },
    TwoSignalCollapse,
}

// ---------------------------------------------------------------------------
// Round 1: universe and report
// ---------------------------------------------------------------------------

pub trait Report {
    type Carrier: Eq + std::hash::Hash + Clone;
    fn report(&self, rho: &Matrix) -> Self::Carrier;
}

pub struct QuantumRelationalUniverse {
    pub dim: usize,
    pub povm: Vec<Matrix>,
}

impl QuantumRelationalUniverse {
    pub fn new(dim: usize, povm: Vec<Matrix>) -> Self {
        let s = povm
            .iter()
            .fold(Matrix::zeros(dim, dim), |acc, e| acc.add(e));
        assert_eq!(s, Matrix::identity(dim), "POVM does not sum to I");
        Self { dim, povm }
    }

    pub fn profile(&self, rho: &Matrix) -> Vec<Q> {
        self.povm
            .iter()
            .map(|e| {
                let t = rho.matmul(e).trace();
                assert!(t.im.is_zero(), "Tr(rho E) not real");
                t.re
            })
            .collect()
    }

    /// N+1 <= M+1 for the modal quantizer (Theorem Q.1).
    pub fn report_horizon_bound(&self) -> usize {
        self.povm.len() + 1
    }
}

impl Report for QuantumRelationalUniverse {
    type Carrier = usize; // modal quantizer: first argmax
    fn report(&self, rho: &Matrix) -> usize {
        let p = self.profile(rho);
        let mx = p
            .iter()
            .max()
            .checked_invariant_9525e5aa("empty POVM")
            .clone();
        p.iter()
            .position(|v| *v == mx)
            .checked_invariant_9525e5aa("checked invariant")
    }
}

// ---------------------------------------------------------------------------
// Round 2: channels, purity, budget
// ---------------------------------------------------------------------------

pub struct KrausChannel {
    pub kraus: Vec<Matrix>,
    /// Fresh ancilla qubits consumed (declared, A-LIFT.3). 0 => must be unital (A-LIFT.2).
    pub cost: u32,
}

impl KrausChannel {
    pub fn apply(&self, rho: &Matrix) -> Matrix {
        let mut out = Matrix::zeros(rho.n, rho.m);
        for a in &self.kraus {
            out = out.add(&a.matmul(rho).matmul(&a.dagger()));
        }
        out
    }

    fn sum_of(&self, f: impl Fn(&Matrix) -> Matrix) -> Matrix {
        let n = self.kraus[0].m;
        self.kraus
            .iter()
            .fold(Matrix::zeros(n, n), |acc, a| acc.add(&f(a)))
    }

    /// Σ A†A = I
    pub fn is_tp(&self) -> bool {
        let n = self.kraus[0].m;
        self.sum_of(|a| a.dagger().matmul(a)) == Matrix::identity(n)
    }

    /// Σ AA† = I
    pub fn is_unital(&self) -> bool {
        let n = self.kraus[0].n;
        self.sum_of(|a| a.matmul(&a.dagger())) == Matrix::identity(n)
    }
}

/// Round 2 Lemma Q.3 monitor: P2 must not increase on unital steps.
pub struct PurityMonitor {
    pub history: Vec<Q>,
}

impl PurityMonitor {
    pub fn new() -> Self {
        PurityMonitor { history: vec![] }
    }
    pub fn observe(&mut self, rho: &Matrix, step_unital: bool) {
        let p = rho.purity_p2();
        if let Some(last) = self.history.last() {
            if step_unital {
                assert!(p <= *last, "Lemma Q.3 violated: unital step increased P2");
            }
        }
        self.history.push(p);
    }
}

impl Default for PurityMonitor {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Clone, Debug)]
pub struct TrajectoryResult {
    pub terminal: Terminal,
    pub k_star: usize,
    pub purification_attempts: usize,
    pub p2_history: Vec<Q>, // P2 of each admitted state ρ_1, ρ_2, ...
    pub annotations: Vec<Annotation>,
}

/// Runs ρ_{k+1} = E_k(ρ_k), k = 1, 2, ...  (channels[idx] is step k = idx + 2).
///
/// `purification_claim == false`: the per-step claim is report-grounded strict
///   improvement; a collision or non-improvement is REPORT_COLLISION (Theorem Q.1).
/// `purification_claim == true`: the per-step claim is an entropy-decrease claim; budget-free
///   steps are neutral (no claim), budget-consuming steps decrement B; attempting a
///   purification with insufficient budget is LIFT_BUDGET_EXHAUSTION (Theorem Q.2).
/// In both modes every cost-0 channel is checked to be unital and to satisfy Lemma Q.3.
pub fn evaluate_cptp_trajectory<U: Report>(
    u: &U,
    gt: impl Fn(&U::Carrier, &U::Carrier) -> bool,
    rho0: &Matrix,
    channels: &[KrausChannel],
    budget: u32,
    purification_claim: bool,
) -> TrajectoryResult {
    let mut rho = rho0.clone();
    let mut b = budget;
    let mut seen: HashSet<U::Carrier> = HashSet::new();
    seen.insert(u.report(&rho));
    let mut p2_history = vec![rho.purity_p2()];
    let mut attempts = 0usize;

    for (idx, ch) in channels.iter().enumerate() {
        let k = idx + 2;
        assert!(ch.is_tp(), "channel at step {k} is not trace-preserving");
        let new = ch.apply(&rho);

        if ch.cost == 0 {
            assert!(
                ch.is_unital(),
                "budget-free channel at step {k} must be unital (A-LIFT.2)"
            );
            assert!(
                new.purity_p2() <= rho.purity_p2(),
                "Lemma Q.3 violated at step {k}"
            );
        } else {
            attempts += 1;
            if b < ch.cost {
                return TrajectoryResult {
                    terminal: Terminal::LiftBudgetExhaustion,
                    k_star: k,
                    purification_attempts: attempts,
                    p2_history,
                    annotations: vec![],
                };
            }
            b -= ch.cost;
        }

        if !purification_claim {
            let rn = u.report(&new);
            let ro = u.report(&rho);
            if seen.contains(&rn) || !gt(&rn, &ro) {
                return TrajectoryResult {
                    terminal: Terminal::ReportCollision,
                    k_star: k,
                    purification_attempts: attempts,
                    p2_history,
                    annotations: vec![],
                };
            }
            seen.insert(rn);
        }

        p2_history.push(new.purity_p2());
        rho = new;
    }

    TrajectoryResult {
        terminal: Terminal::TrajectoryExhaustedNoTerminal,
        k_star: channels.len() + 1,
        purification_attempts: attempts,
        p2_history,
        annotations: vec![],
    }
}

// ---------------------------------------------------------------------------
// Round 3: measurement nerve, gluing defect, GF(2) parity class, latency defect
// ---------------------------------------------------------------------------

pub struct SimplicialNerve {
    pub contexts: Vec<Vec<usize>>,
    /// support(ctx_index, local_section) -> bool
    pub support: Box<dyn Fn(usize, &[u8]) -> bool>,
}

impl SimplicialNerve {
    /// Edges (i,j), i<j, with nonempty context intersection.
    pub fn edges(&self) -> Vec<(usize, usize)> {
        let n = self.contexts.len();
        let mut out = vec![];
        for i in 0..n {
            for j in (i + 1)..n {
                if self.contexts[i]
                    .iter()
                    .any(|m| self.contexts[j].contains(m))
                {
                    out.push((i, j));
                }
            }
        }
        out
    }

    /// All {0,1}-sections of context i that are in the support.
    pub fn support_sections(&self, i: usize) -> Vec<Vec<u8>> {
        let len = self.contexts[i].len();
        (0..(1usize << len))
            .map(|bits| {
                (0..len)
                    .map(|p| ((bits >> p) & 1) as u8)
                    .collect::<Vec<u8>>()
            })
            .filter(|s| (self.support)(i, s))
            .collect()
    }

    /// Round 3 Def. 1.1: minimal total edge mismatch over all choices of support sections.
    /// Exhaustive mixed-radix enumeration (Cabello: 4^9 = 262144 choices).
    pub fn phi_glue(&self) -> usize {
        let secs: Vec<Vec<Vec<u8>>> = (0..self.contexts.len())
            .map(|i| self.support_sections(i))
            .collect();
        assert!(
            secs.iter().all(|s| !s.is_empty()),
            "a context has empty support"
        );

        // For each edge, positions of shared measurements in the two contexts.
        let shared: Vec<(usize, usize, Vec<(usize, usize)>)> = self
            .edges()
            .into_iter()
            .map(|(i, j)| {
                let (ci, cj) = (&self.contexts[i], &self.contexts[j]);
                let pairs = ci
                    .iter()
                    .enumerate()
                    .filter_map(|(pi, m)| cj.iter().position(|x| x == m).map(|pj| (pi, pj)))
                    .collect();
                (i, j, pairs)
            })
            .collect();

        let mut idx = vec![0usize; secs.len()];
        let mut best: Option<usize> = None;
        loop {
            let mism: usize = shared
                .iter()
                .map(|(i, j, pairs)| {
                    pairs
                        .iter()
                        .filter(|&&(pi, pj)| secs[*i][idx[*i]][pi] != secs[*j][idx[*j]][pj])
                        .count()
                })
                .sum();
            best = Some(best.map_or(mism, |b| b.min(mism)));
            if mism == 0 {
                return 0;
            }
            // increment mixed-radix counter
            let mut pos = 0;
            loop {
                if pos == idx.len() {
                    return best.checked_invariant_9525e5aa("checked invariant");
                }
                idx[pos] += 1;
                if idx[pos] < secs[pos].len() {
                    break;
                }
                idx[pos] = 0;
                pos += 1;
            }
        }
    }

    /// GF(2): is the all-ones context vector outside the row space of the
    /// context–ray incidence matrix? (Equivalently: the system "exactly-one parity"
    /// Σ_{r∈C} a(r) = 1 for all C has no solution; Round 3 Theorem Q.3(a).)
    pub fn parity_class_nonzero(&self) -> bool {
        let mut rays: Vec<usize> = self.contexts.iter().flatten().copied().collect();
        rays.sort_unstable();
        rays.dedup();
        let nc = rays.len();
        let mut rows: Vec<Vec<u8>> = self
            .contexts
            .iter()
            .map(|c| {
                let mut r = vec![0u8; nc + 1];
                for m in c {
                    r[rays
                        .binary_search(m)
                        .checked_invariant_9525e5aa("checked invariant")] = 1;
                }
                r[nc] = 1; // augmented column: all-ones target
                r
            })
            .collect();

        let mut piv = 0usize;
        for c in 0..nc {
            let Some(p) = (piv..rows.len()).find(|&i| rows[i][c] == 1) else {
                continue;
            };
            rows.swap(piv, p);
            let pivot_row = rows[piv].clone();
            for (i, row) in rows.iter_mut().enumerate() {
                if i != piv && row[c] == 1 {
                    for (x, y) in row.iter_mut().zip(pivot_row.iter()) {
                        *x ^= *y;
                    }
                }
            }
            piv += 1;
            if piv == rows.len() {
                break;
            }
        }
        rows.iter()
            .any(|r| r[..nc].iter().all(|&x| x == 0) && r[nc] == 1)
    }

    /// Prompt's Σ|d¹d⁰s|: identically zero (d¹∘d⁰ = 0); retained for parity assertion.
    pub fn prompt_d1d0_defect(&self) -> usize {
        0
    }
}

/// Φ₁(δ_k) on the coverage complex (Round 3 §2.1). `reports[node][k]` is node's report at
/// step k (index 0 is padding; steps are 1-based). A view with latency t at step k sees
/// the report at max(k - t, 1).
pub fn latency_defect(
    reports: &HashMap<usize, Vec<usize>>,
    coverage: &[(usize, usize)],
    latency: impl Fn(usize, usize, usize) -> usize,
    k: usize,
) -> usize {
    let mut d = 0;
    for &(a, b) in coverage {
        for (x, y) in [(a, b), (b, a)] {
            let t = latency(x, y, k);
            let s = if k > t { k - t } else { 1 };
            let r = &reports[&y];
            if r[s] != r[k] {
                d += 1;
            }
        }
    }
    d
}

// ---------------------------------------------------------------------------
// Round 2: certified rational enclosures
// ---------------------------------------------------------------------------

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RationalInterval {
    pub lo: Q,
    pub hi: Q,
}

impl RationalInterval {
    pub fn width(&self) -> Q {
        &self.hi - &self.lo
    }

    /// Enclosure of ln(q/p), 0 < p < q, via x = (q-p)/(q+p),
    /// ln(q/p) = 2 Σ_{k≥0} x^{2k+1}/(2k+1), truncated after k = n, with exact tail bound
    /// 0 < T_n ≤ 2 x^{2n+3} / ((2n+3)(1-x²)).
    pub fn ln_ratio(p: &Q, q: &Q, n: usize) -> Self {
        assert!(*p > Q::zero() && q > p, "ln_ratio requires 0 < p < q");
        let one = Q::one();
        let x = (q - p) / (q + p);
        assert!(x > Q::zero() && x < one);
        let x2 = &x * &x;
        let mut pow = x.clone(); // x^{2k+1}
        let mut acc = Q::zero();
        for k in 0..=n {
            let denom = Q::from_integer(BigInt::from((2 * k + 1) as i64));
            acc = acc + &pow / denom;
            pow = &pow * &x2;
        }
        // after the loop, pow = x^{2n+3}
        let two = Q::from_integer(BigInt::from(2));
        let lo = &two * acc;
        let two_n3 = Q::from_integer(BigInt::from((2 * n + 3) as i64));
        let tail = &two * &pow / (two_n3 * (&one - &x2));
        let hi = &lo + &tail;
        RationalInterval { lo, hi }
    }

    /// S_e(diag(spectrum)) = Σ p_i ln(1/p_i) with explicit series orders per nontrivial p_i.
    pub fn entropy_nats_diag_with_orders(spectrum: &[Q], orders: &[usize]) -> Self {
        let one = Q::one();
        let (mut lo, mut hi) = (Q::zero(), Q::zero());
        let mut oi = 0usize;
        for p in spectrum {
            assert!(*p >= Q::zero() && *p <= one);
            if p.is_zero() || *p == one {
                continue;
            }
            let iv = Self::ln_ratio(p, &one, orders[oi]);
            oi += 1;
            lo = lo + p * &iv.lo;
            hi = hi + p * &iv.hi;
        }
        assert_eq!(oi, orders.len(), "order count mismatch");
        RationalInterval { lo, hi }
    }

    /// Adaptive orders so that total width ≤ 2^-precision (exact comparison).
    pub fn entropy_nats_diag(spectrum: &[Q], precision: u32) -> Self {
        let one = Q::one();
        let total = spectrum.iter().fold(Q::zero(), |a, b| a + b);
        assert_eq!(total, one, "spectrum must sum to 1");
        let active = spectrum
            .iter()
            .filter(|p| !p.is_zero() && **p != one)
            .count();
        if active == 0 {
            return RationalInterval {
                lo: Q::zero(),
                hi: Q::zero(),
            };
        }
        let target = Q::new(
            BigInt::one(),
            BigInt::from(2).pow(precision) * BigInt::from(active as i64),
        );
        let (mut lo, mut hi) = (Q::zero(), Q::zero());
        for p in spectrum {
            if p.is_zero() || *p == one {
                continue;
            }
            let mut n = 1usize;
            loop {
                let iv = Self::ln_ratio(p, &one, n);
                let w = p * (&iv.hi - &iv.lo);
                if w <= target {
                    lo = lo + p * &iv.lo;
                    hi = hi + p * &iv.hi;
                    break;
                }
                n += 1;
            }
        }
        RationalInterval { lo, hi }
    }
}

// ---------------------------------------------------------------------------
// Standard quantum gates and projectors
// ---------------------------------------------------------------------------

pub fn half() -> QC {
    QC::real(q(1, 2))
}
pub fn pauli_x() -> Matrix {
    Matrix::real_from(2, 2, &[(0, 1), (1, 1), (1, 1), (0, 1)])
}
pub fn pauli_z() -> Matrix {
    Matrix::real_from(2, 2, &[(1, 1), (0, 1), (0, 1), (-1, 1)])
}
pub fn pauli_y() -> Matrix {
    Matrix::from_rows(vec![
        vec![QC::zero(), QC::imag(q(-1, 1))],
        vec![QC::imag(q(1, 1)), QC::zero()],
    ])
}
pub fn proj0() -> Matrix {
    Matrix::real_from(2, 2, &[(1, 1), (0, 1), (0, 1), (0, 1)])
}
pub fn proj1() -> Matrix {
    Matrix::real_from(2, 2, &[(0, 1), (0, 1), (0, 1), (1, 1)])
}
pub fn unitary(u: Matrix) -> KrausChannel {
    KrausChannel {
        kraus: vec![u],
        cost: 0,
    }
}

/// Bell projectors in basis |00>,|01>,|10>,|11>; kind: 0=Φ+,1=Φ-,2=Ψ+,3=Ψ-.
pub fn bell(kind: usize) -> Matrix {
    let (i, j, sgn) = match kind {
        0 => (0, 3, 1),
        1 => (0, 3, -1),
        2 => (1, 2, 1),
        3 => (1, 2, -1),
        _ => unreachable!(),
    };
    let mut m = Matrix::zeros(4, 4);
    m.a[i * 4 + i] = QC::real(q(1, 2));
    m.a[j * 4 + j] = QC::real(q(1, 2));
    m.a[i * 4 + j] = QC::real(q(sgn, 2));
    m.a[j * 4 + i] = QC::real(q(sgn, 2));
    m
}

// ---------------------------------------------------------------------------
// PFP Workpad Contract Schemas (Round 4 §3)
// ---------------------------------------------------------------------------

pub mod workpad {
    use super::*;

    /// Rational representation serialized strictly as "num/den" string (den > 0).
    #[derive(Clone, Debug, PartialEq, Eq, Hash)]
    pub struct RationalJson(pub Q);

    impl Serialize for RationalJson {
        fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
        where
            S: Serializer,
        {
            serializer.serialize_str(&format!("{}/{}", self.0.numer(), self.0.denom()))
        }
    }

    impl<'de> Deserialize<'de> for RationalJson {
        fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
        where
            D: Deserializer<'de>,
        {
            let s = String::deserialize(deserializer)?;
            let parts: Vec<&str> = s.split('/').collect();
            if parts.len() != 2 {
                return Err(serde::de::Error::custom("expected rational string num/den"));
            }
            let num = BigInt::from_str(parts[0]).map_err(serde::de::Error::custom)?;
            let den = BigInt::from_str(parts[1]).map_err(serde::de::Error::custom)?;
            if den <= BigInt::zero() {
                return Err(serde::de::Error::custom("denominator must be positive"));
            }
            Ok(RationalJson(BigRational::new(num, den)))
        }
    }

    #[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
    pub struct GaussianRationalJson {
        pub re: RationalJson,
        pub im: RationalJson,
    }

    impl From<&QC> for GaussianRationalJson {
        fn from(qc: &QC) -> Self {
            GaussianRationalJson {
                re: RationalJson(qc.re.clone()),
                im: RationalJson(qc.im.clone()),
            }
        }
    }

    impl From<&GaussianRationalJson> for QC {
        fn from(g: &GaussianRationalJson) -> Self {
            QC {
                re: g.re.0.clone(),
                im: g.im.0.clone(),
            }
        }
    }

    #[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
    #[serde(rename_all = "snake_case")]
    pub enum Pg3ClaimStatus {
        EvidenceOnly,
        Authorized,
        Rejected,
        Unresolved,
        Refused,
        NotAdmitted,
    }

    pub fn rational_determinant(m: &[Vec<Q>]) -> Q {
        let n = m.len();
        if n == 0 {
            return Q::one();
        }
        if n == 1 {
            return m[0][0].clone();
        }
        if n == 2 {
            return &m[0][0] * &m[1][1] - &m[0][1] * &m[1][0];
        }
        gaussian_elimination_determinant(m.to_vec())
    }

    fn gaussian_elimination_determinant(mut a: Vec<Vec<Q>>) -> Q {
        let n = a.len();
        let mut det = Q::one();
        for i in 0..n {
            let Some(pivot) = (i..n).find(|&p| !a[p][i].is_zero()) else {
                return Q::zero();
            };
            if pivot != i {
                a.swap(i, pivot);
                det = -det;
            }
            let pivot_val = a[i][i].clone();
            det = &det * &pivot_val;
            eliminate_below_pivot(&mut a, i, n, &pivot_val);
        }
        det
    }

    fn eliminate_below_pivot(a: &mut [Vec<Q>], i: usize, n: usize, pivot_val: &Q) {
        for j in (i + 1)..n {
            let factor = &a[j][i] / pivot_val;
            for k in i..n {
                let sub = &factor * &a[i][k];
                a[j][k] = &a[j][k] - &sub;
            }
        }
    }

    #[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
    pub struct PfpQubitPovmWorkpad {
        pub dim: usize,
        pub effects: Vec<Vec<Vec<GaussianRationalJson>>>,
        pub effect_traces: Vec<RationalJson>,
        pub sum_is_identity: bool,
        pub gram_matrix: Vec<Vec<RationalJson>>,
        pub gram_determinant: RationalJson,
        #[serde(skip_serializing_if = "Option::is_none")]
        pub quantizer: Option<String>,
        #[serde(rename = "report_capacity_N")]
        pub report_capacity_n: usize,
        pub horizon_bound: usize,
        pub claim_status: Pg3ClaimStatus,
    }

    impl PfpQubitPovmWorkpad {
        pub fn from_universe(u: &QuantumRelationalUniverse, claim_status: Pg3ClaimStatus) -> Self {
            let dim = u.dim;
            let effects: Vec<Vec<Vec<GaussianRationalJson>>> =
                u.povm.iter().map(|e| e.to_json_rows()).collect();
            let effect_traces: Vec<RationalJson> =
                u.povm.iter().map(|e| RationalJson(e.trace().re)).collect();
            let sum_is_identity = {
                let s = u
                    .povm
                    .iter()
                    .fold(Matrix::zeros(dim, dim), |acc, e| acc.add(e));
                s == Matrix::identity(dim)
            };
            let gram_q: Vec<Vec<Q>> = u
                .povm
                .iter()
                .map(|em| u.povm.iter().map(|en| em.matmul(en).trace().re).collect())
                .collect();
            let gram_determinant = RationalJson(rational_determinant(&gram_q));
            let gram_matrix: Vec<Vec<RationalJson>> = gram_q
                .into_iter()
                .map(|row| row.into_iter().map(RationalJson).collect())
                .collect();

            Self {
                dim,
                effects,
                effect_traces,
                sum_is_identity,
                gram_matrix,
                gram_determinant,
                quantizer: Some("modal".to_string()),
                report_capacity_n: u.povm.len(),
                horizon_bound: u.report_horizon_bound(),
                claim_status,
            }
        }

        pub fn to_json(&self) -> Result<String, serde_json::Error> {
            serde_json::to_string_pretty(self)
        }

        pub fn from_json(s: &str) -> Result<Self, serde_json::Error> {
            serde_json::from_str(s)
        }
    }

    #[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
    pub struct PfpPurityStep {
        pub k: usize,
        #[serde(rename = "P2")]
        pub p2: RationalJson,
        pub budget_after: u32,
        pub channel_unital: bool,
        pub channel_cost: u32,
        pub admitted: bool,
        #[serde(skip_serializing_if = "Option::is_none")]
        pub spectrum: Option<Vec<RationalJson>>,
    }

    #[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
    pub struct PfpPurityBudgetWorkpad {
        #[serde(rename = "B0")]
        pub b0: u32,
        pub steps: Vec<PfpPurityStep>,
        pub lemma_q3_checked: bool,
        pub terminal: Terminal,
        pub k_star: usize,
        pub claim_status: Pg3ClaimStatus,
    }

    impl PfpPurityBudgetWorkpad {
        pub fn from_trajectory(
            b0: u32,
            channels: &[KrausChannel],
            res: &TrajectoryResult,
            claim_status: Pg3ClaimStatus,
        ) -> Self {
            let mut steps = Vec::new();
            let mut rem_budget = b0;

            for (idx, ch) in channels.iter().enumerate() {
                let k = idx + 2;
                let channel_cost = ch.cost;
                let channel_unital = ch.is_unital();
                let admitted = rem_budget >= channel_cost;
                if admitted {
                    rem_budget -= channel_cost;
                }
                let p2_val = if idx + 1 < res.p2_history.len() {
                    res.p2_history[idx + 1].clone()
                } else {
                    res.p2_history.last().cloned().unwrap_or_else(|| q(0, 1))
                };

                steps.push(PfpPurityStep {
                    k,
                    p2: RationalJson(p2_val),
                    budget_after: rem_budget,
                    channel_unital,
                    channel_cost,
                    admitted,
                    spectrum: None,
                });

                if !admitted {
                    break;
                }
            }

            Self {
                b0,
                steps,
                lemma_q3_checked: true,
                terminal: res.terminal,
                k_star: res.k_star,
                claim_status,
            }
        }

        pub fn to_json(&self) -> Result<String, serde_json::Error> {
            serde_json::to_string_pretty(self)
        }

        pub fn from_json(s: &str) -> Result<Self, serde_json::Error> {
            serde_json::from_str(s)
        }
    }

    #[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
    pub struct PfpContextualityHolonomyWorkpad {
        pub contexts: Vec<Vec<usize>>,
        pub support_rule: String,
        pub edges: Vec<[usize; 2]>,
        #[serde(skip_serializing_if = "Option::is_none")]
        pub triple_overlaps: Option<usize>,
        pub phi_glue: usize,
        pub prompt_d1d0_defect: usize,
        pub parity_class_nonzero: bool,
        pub contextual_fraction_lower: RationalJson,
        #[serde(skip_serializing_if = "Option::is_none")]
        pub latency_defect_trace: Option<Vec<usize>>,
        pub terminal: Terminal,
        pub claim_status: Pg3ClaimStatus,
    }

    impl PfpContextualityHolonomyWorkpad {
        pub fn from_simplicial_nerve(
            nerve: &SimplicialNerve,
            cf_lower: Q,
            latency_trace: Option<Vec<usize>>,
            terminal: Terminal,
            claim_status: Pg3ClaimStatus,
        ) -> Self {
            let edges = nerve.edges().into_iter().map(|(i, j)| [i, j]).collect();
            let phi_glue = nerve.phi_glue();
            let parity_class_nonzero = nerve.parity_class_nonzero();
            let prompt_d1d0_defect = nerve.prompt_d1d0_defect();

            Self {
                contexts: nerve.contexts.clone(),
                support_rule: "exactly_one".to_string(),
                edges,
                triple_overlaps: None,
                phi_glue,
                prompt_d1d0_defect,
                parity_class_nonzero,
                contextual_fraction_lower: RationalJson(cf_lower),
                latency_defect_trace: latency_trace,
                terminal,
                claim_status,
            }
        }

        pub fn to_json(&self) -> Result<String, serde_json::Error> {
            serde_json::to_string_pretty(self)
        }

        pub fn from_json(s: &str) -> Result<Self, serde_json::Error> {
            serde_json::from_str(s)
        }
    }

    #[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
    pub struct PfpRationalIntervalWorkpad {
        pub spectrum: Vec<RationalJson>,
        #[serde(skip_serializing_if = "Option::is_none")]
        pub series_orders: Option<Vec<usize>>,
        pub precision_bits: u32,
        #[serde(rename = "L")]
        pub l: RationalJson,
        #[serde(rename = "U")]
        pub u: RationalJson,
        pub width: RationalJson,
        pub certified: bool,
        pub baker_applies: bool,
        #[serde(skip_serializing_if = "Option::is_none")]
        pub relation_lattice_trivial: Option<bool>,
        #[serde(skip_serializing_if = "Option::is_none")]
        pub decimal_sanity_check: Option<String>,
        pub claim_status: Pg3ClaimStatus,
    }

    impl PfpRationalIntervalWorkpad {
        pub fn from_interval(
            spectrum: &[Q],
            orders: Option<&[usize]>,
            precision_bits: u32,
            iv: &RationalInterval,
            claim_status: Pg3ClaimStatus,
        ) -> Self {
            let target_width = q(1, 1i64 << precision_bits);
            let certified = iv.width() <= target_width;
            let nontrivial_count = spectrum
                .iter()
                .filter(|p| !p.is_zero() && **p != q(1, 1))
                .count();
            let baker_applies = nontrivial_count >= 2;

            Self {
                spectrum: spectrum.iter().cloned().map(RationalJson).collect(),
                series_orders: orders.map(|o| o.to_vec()),
                precision_bits,
                l: RationalJson(iv.lo.clone()),
                u: RationalJson(iv.hi.clone()),
                width: RationalJson(iv.width()),
                certified,
                baker_applies,
                relation_lattice_trivial: None,
                decimal_sanity_check: None,
                claim_status,
            }
        }

        pub fn to_json(&self) -> Result<String, serde_json::Error> {
            serde_json::to_string_pretty(self)
        }

        pub fn from_json(s: &str) -> Result<Self, serde_json::Error> {
            serde_json::from_str(s)
        }
    }

    pub fn canonical_qubit_m2_povm_workpad() -> PfpQubitPovmWorkpad {
        let u = QuantumRelationalUniverse::new(2, vec![proj0(), proj1()]);
        PfpQubitPovmWorkpad::from_universe(&u, Pg3ClaimStatus::Authorized)
    }

    pub fn canonical_bell_panel_m4_povm_workpad() -> PfpQubitPovmWorkpad {
        let u = QuantumRelationalUniverse::new(4, vec![bell(0), bell(1), bell(2), bell(3)]);
        PfpQubitPovmWorkpad::from_universe(&u, Pg3ClaimStatus::EvidenceOnly)
    }

    pub fn canonical_purity_budget_workpad() -> PfpPurityBudgetWorkpad {
        let i2 = Matrix::identity(2);
        let depol = KrausChannel {
            kraus: vec![
                i2.scale(&half()).kron(&i2),
                pauli_x().scale(&half()).kron(&i2),
                pauli_y().scale(&half()).kron(&i2),
                pauli_z().scale(&half()).kron(&i2),
            ],
            cost: 0,
        };
        let a0 = Matrix::real_from(2, 2, &[(1, 1), (0, 1), (0, 1), (0, 1)]);
        let a1 = Matrix::real_from(2, 2, &[(0, 1), (1, 1), (0, 1), (0, 1)]);
        let damp_q2 = KrausChannel {
            kraus: vec![i2.kron(&a0), i2.kron(&a1)],
            cost: 1,
        };
        let damp_q1 = KrausChannel {
            kraus: vec![a0.kron(&i2), a1.kron(&i2)],
            cost: 1,
        };
        let damp_q1_again = KrausChannel {
            kraus: vec![a0.kron(&i2), a1.kron(&i2)],
            cost: 1,
        };

        let u = QuantumRelationalUniverse::new(4, vec![bell(0), bell(1), bell(2), bell(3)]);
        let chans = vec![depol, damp_q2, damp_q1, damp_q1_again];
        let res = evaluate_cptp_trajectory(&u, |_a, _b| true, &bell(3), &chans, 2, true);

        PfpPurityBudgetWorkpad::from_trajectory(2, &chans, &res, Pg3ClaimStatus::Authorized)
    }

    pub fn canonical_contextuality_holonomy_workpad() -> PfpContextualityHolonomyWorkpad {
        let contexts = vec![
            vec![0, 1, 2, 3],
            vec![0, 4, 5, 6],
            vec![7, 8, 2, 9],
            vec![7, 10, 5, 11],
            vec![1, 4, 12, 13],
            vec![8, 10, 12, 14],
            vec![3, 9, 15, 16],
            vec![6, 11, 15, 17],
            vec![13, 14, 16, 17],
        ];
        let nerve = SimplicialNerve {
            contexts,
            support: Box::new(|_i, s: &[u8]| s.iter().filter(|&&b| b == 1).count() == 1),
        };

        PfpContextualityHolonomyWorkpad::from_simplicial_nerve(
            &nerve,
            q(47, 125),
            Some(vec![0, 1, 1, 1]),
            Terminal::OverlapGluingRefusal,
            Pg3ClaimStatus::Authorized,
        )
    }

    pub fn canonical_rational_interval_workpad() -> PfpRationalIntervalWorkpad {
        let spec = [q(3, 5), q(2, 5)];
        let ad = RationalInterval::entropy_nats_diag_with_orders(&spec, &[2, 4]);
        PfpRationalIntervalWorkpad::from_interval(
            &spec,
            Some(&[2, 4]),
            15,
            &ad,
            Pg3ClaimStatus::Authorized,
        )
    }

    pub fn emit_canonical_workpads() -> BTreeMap<String, String> {
        let mut map = BTreeMap::new();
        map.insert(
            "qubit_m2_povm_workpad.json".to_string(),
            canonical_qubit_m2_povm_workpad()
                .to_json()
                .checked_invariant_9525e5aa("serialize qubit povm workpad"),
        );
        map.insert(
            "bell_panel_m4_povm_workpad.json".to_string(),
            canonical_bell_panel_m4_povm_workpad()
                .to_json()
                .checked_invariant_9525e5aa("serialize bell povm workpad"),
        );
        map.insert(
            "werner_purity_budget_workpad.json".to_string(),
            canonical_purity_budget_workpad()
                .to_json()
                .checked_invariant_9525e5aa("serialize purity budget workpad"),
        );
        map.insert(
            "cabello_contextuality_holonomy_workpad.json".to_string(),
            canonical_contextuality_holonomy_workpad()
                .to_json()
                .checked_invariant_9525e5aa("serialize contextuality workpad"),
        );
        map.insert(
            "rational_interval_workpad.json".to_string(),
            canonical_rational_interval_workpad()
                .to_json()
                .checked_invariant_9525e5aa("serialize interval workpad"),
        );
        map
    }

    pub fn emit_canonical_workpads_to_dir(
        dir: &std::path::Path,
    ) -> std::io::Result<Vec<std::path::PathBuf>> {
        std::fs::create_dir_all(dir)?;
        let workpads = emit_canonical_workpads();
        let mut paths = Vec::new();
        for (filename, content) in workpads {
            let path = dir.join(&filename);
            std::fs::write(&path, content)?;
            paths.push(path);
        }
        Ok(paths)
    }
}

// ---------------------------------------------------------------------------
// Witness test suite (expected values are the hand-derived Round 1–3 numbers)
// ---------------------------------------------------------------------------

// Origin: engine/crates_rs/core_quantum_physics/src/cptp_trajectory_verifier.rs
// Claim: urn:core:crates_rs:core-quantum-physics:cptp-trajectory-verifier:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9525e5aa {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9525e5aa` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9525e5aa {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError9525e5aa {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9525e5aa {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9525e5aa {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9525e5aa {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9525e5aa> {
        if capacity_bound == 0 {
            return Err(BoundaryError9525e5aa::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9525e5aa::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9525e5aa::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn qubit_m2_modal_collision_at_3() {
        // Π = {|0><0|, |1><1|}, modal report, order 1 ≻ 0; trajectory |0> -X-> |1> -X-> |0>.
        let u = QuantumRelationalUniverse::new(2, vec![proj0(), proj1()]);
        assert_eq!(u.report_horizon_bound(), 3);
        let gt = |a: &usize, b: &usize| *a == 1 && *b == 0;
        let chans = vec![unitary(pauli_x()), unitary(pauli_x())];
        let res = evaluate_cptp_trajectory(&u, gt, &proj0(), &chans, 0, false);
        assert_eq!(res.terminal, Terminal::ReportCollision);
        assert_eq!(res.k_star, 3);
        assert_eq!(res.terminal.label(), "REPORT_COLLISION");
    }

    #[test]
    fn bell_panel_m4_collision_at_5() {
        // Pauli frame on qubit 2: Φ+ -> Ψ+ -> Φ- -> Ψ- (reports 0,2,1,3), then collision.
        let u = QuantumRelationalUniverse::new(4, vec![bell(0), bell(1), bell(2), bell(3)]);
        let rank = |r: usize| match r {
            0 => 0,
            2 => 1,
            1 => 2,
            3 => 3,
            _ => unreachable!(),
        };
        let gt = move |a: &usize, b: &usize| rank(*a) > rank(*b);
        let i2 = Matrix::identity(2);
        let x2 = i2.kron(&pauli_x());
        let zx2 = i2.kron(&pauli_z().matmul(&pauli_x()));
        let chans = vec![
            unitary(x2.clone()), // k=2: Ψ+
            unitary(zx2),        // k=3: Φ-
            unitary(x2.clone()), // k=4: Ψ-
            unitary(x2),         // k=5: Φ- again -> collision
        ];
        let res = evaluate_cptp_trajectory(&u, gt, &bell(0), &chans, 0, false);
        assert_eq!(res.terminal, Terminal::ReportCollision);
        assert_eq!(res.k_star, 5);
        assert_eq!(res.k_star, u.report_horizon_bound());
    }

    #[test]
    fn werner_amplitude_damping_budget_2() {
        // ρ1 = |Ψ-><Ψ-|; k=2 full depolarizing on qubit 1 (unital, cost 0) -> I/4 (Werner p=0);
        // k=3 amplitude damping γ=1 on qubit 2 (cost 1) -> I/2 ⊗ |0><0|;
        // k=4 amplitude damping on qubit 1 (cost 1) -> |00><00|;
        // k=5 third purification attempt with B=0 -> LIFT_BUDGET_EXHAUSTION.
        let i2 = Matrix::identity(2);
        let depol = KrausChannel {
            kraus: vec![
                i2.scale(&half()).kron(&i2),
                pauli_x().scale(&half()).kron(&i2),
                pauli_y().scale(&half()).kron(&i2),
                pauli_z().scale(&half()).kron(&i2),
            ],
            cost: 0,
        };
        let a0 = Matrix::real_from(2, 2, &[(1, 1), (0, 1), (0, 1), (0, 1)]);
        let a1 = Matrix::real_from(2, 2, &[(0, 1), (1, 1), (0, 1), (0, 1)]);
        let damp_q2 = KrausChannel {
            kraus: vec![i2.kron(&a0), i2.kron(&a1)],
            cost: 1,
        };
        let damp_q1 = KrausChannel {
            kraus: vec![a0.kron(&i2), a1.kron(&i2)],
            cost: 1,
        };
        let damp_q1_again = KrausChannel {
            kraus: vec![a0.kron(&i2), a1.kron(&i2)],
            cost: 1,
        };
        assert!(depol.is_unital() && depol.is_tp());
        assert!(damp_q2.is_tp() && !damp_q2.is_unital());

        // Report layer is irrelevant in purification mode; use the Bell panel for a valid universe.
        let u = QuantumRelationalUniverse::new(4, vec![bell(0), bell(1), bell(2), bell(3)]);
        let res = evaluate_cptp_trajectory(
            &u,
            |_a: &usize, _b: &usize| true,
            &bell(3),
            &[depol, damp_q2, damp_q1, damp_q1_again],
            2,
            true,
        );
        assert_eq!(res.terminal, Terminal::LiftBudgetExhaustion);
        assert_eq!(res.k_star, 5);
        assert_eq!(res.purification_attempts, 3);
        assert_eq!(res.p2_history, vec![q(1, 1), q(1, 4), q(1, 2), q(1, 1)]);
    }

    #[test]
    fn dephasing_fixes_diag_3_5_2_5() {
        // Pinching Kraus {|0><0|,|1><1|} (same channel as ½(ρ + ZρZ)); unital; fixed point.
        let deph = KrausChannel {
            kraus: vec![proj0(), proj1()],
            cost: 0,
        };
        assert!(deph.is_tp() && deph.is_unital());
        let rho = Matrix::real_from(2, 2, &[(3, 5), (0, 1), (0, 1), (2, 5)]);
        let out = deph.apply(&rho);
        assert_eq!(out, rho);
        assert_eq!(rho.purity_p2(), q(13, 25));
        assert_eq!(out.purity_p2(), q(13, 25));
        let mut mon = PurityMonitor::new();
        mon.observe(&rho, false);
        mon.observe(&out, true); // Lemma Q.3 equality case; must not panic
    }

    #[test]
    fn cabello_phi_glue_is_1_parity_nonzero() {
        // Ray ids (Round 3 §1.4 table):
        // 0:0001 1:0010 2:1100 3:1-100 4:0100 5:1010 6:10-10 7:1-1-11 8:1-11-1 9:0011
        // 10:11-1-1 11:0101 12:1001 13:100-1 14:0110 15:111-1 16:11-11 17:1-111
        let contexts = vec![
            vec![0, 1, 2, 3],
            vec![0, 4, 5, 6],
            vec![7, 8, 2, 9],
            vec![7, 10, 5, 11],
            vec![1, 4, 12, 13],
            vec![8, 10, 12, 14],
            vec![3, 9, 15, 16],
            vec![6, 11, 15, 17],
            vec![13, 14, 16, 17],
        ];
        let nerve = SimplicialNerve {
            contexts,
            support: Box::new(|_i, s: &[u8]| s.iter().filter(|&&b| b == 1).count() == 1),
        };
        assert_eq!(nerve.edges().len(), 18);
        assert_eq!(nerve.phi_glue(), 1);
        assert!(nerve.parity_class_nonzero());
        assert_eq!(nerve.prompt_d1d0_defect(), 0);
    }

    #[test]
    fn two_node_tau1_refusal_at_2() {
        // π(1)=(1,1), π(2)=(2,1), π(3)=(2,2), π(4)=(1,2); coverage {(1,2)}; τ=1.
        let mut reports = HashMap::new();
        reports.insert(1usize, vec![0usize, 1, 2, 2, 1]);
        reports.insert(2usize, vec![0usize, 1, 1, 2, 2]);
        let cov = [(1usize, 2usize)];
        let tau1 = |_a: usize, _b: usize, _k: usize| 1usize;
        let tau0 = |_a: usize, _b: usize, _k: usize| 0usize;
        assert_eq!(latency_defect(&reports, &cov, tau1, 2), 1);
        assert_eq!(latency_defect(&reports, &cov, tau1, 3), 1);
        assert_eq!(latency_defect(&reports, &cov, tau1, 4), 1);
        assert_eq!(latency_defect(&reports, &cov, tau0, 2), 0);
        assert_eq!(latency_defect(&reports, &cov, tau0, 4), 0);
    }

    #[test]
    fn entropy_diag_3_5_2_5_enclosure() {
        let spec = [q(3, 5), q(2, 5)];
        // Round 2 §2.3 orders: n=2 for ln(5/3) (x=1/4), n=4 for ln(5/2) (x=3/7).
        let iv = RationalInterval::entropy_nats_diag_with_orders(&spec, &[2, 4]);
        assert_eq!(iv.lo, q(13904738765, 20661046784));
        assert_eq!(iv.hi, q(1911955961409, 2840893932800));
        assert_eq!(iv.width(), q(108762443, 5681787865600));
        assert!(iv.width() < q(1, 32768)); // < 2^-15
                                           // Sub-enclosures as recorded.
        let l53 = RationalInterval::ln_ratio(&q(3, 5), &q(1, 1), 2);
        assert_eq!(l53.lo, q(3923, 7680));
        assert_eq!(l53.hi, q(13731, 26880));
        let l52 = RationalInterval::ln_ratio(&q(2, 5), &q(1, 1), 4);
        assert_eq!(l52.lo, q(184874286, 201768035));
        assert_eq!(l52.hi, q(184874286, 201768035) + q(177147, 8877793540));
        // Adaptive enclosure must be certified at 15 bits and overlap the explicit one
        // (both contain S_e, so they must intersect).
        let ad = RationalInterval::entropy_nats_diag(&spec, 15);
        assert!(ad.width() <= q(1, 32768));
        assert!(ad.lo <= iv.hi && iv.lo <= ad.hi);
    }

    // -----------------------------------------------------------------------
    // Property-based test suite (random rational CPTP & varying budgets)
    // -----------------------------------------------------------------------

    use proptest::prelude::*;

    fn random_rational_density_matrix(
        a: i64,
        b: i64,
        c: i64,
        d: i64,
        s_num: u32,
        s_den: u32,
    ) -> Matrix {
        let (a, b, c, d) = if a == 0 && b == 0 && c == 0 && d == 0 {
            (1, 0, 0, 0)
        } else {
            (a, b, c, d)
        };
        let big_d = a * a + b * b + c * c + d * d;
        let s_den = if s_den == 0 { 1i64 } else { s_den as i64 };
        let s_num = (s_num as i64).min(s_den);
        let s = q(s_num, s_den);
        let rx = &s * q(2 * (a * d + b * c), big_d);
        let ry = &s * q(2 * (b * d - a * c), big_d);
        let rz = &s * q(a * a + b * b - c * c - d * d, big_d);

        let one = q(1, 1);
        let half = q(1, 2);
        let row0 = vec![
            QC::real(&half * (&one + &rz)),
            QC {
                re: &half * &rx,
                im: -&half * &ry,
            },
        ];
        let row1 = vec![
            QC {
                re: &half * &rx,
                im: &half * &ry,
            },
            QC::real(&half * (&one - &rz)),
        ];
        Matrix::from_rows(vec![row0, row1])
    }

    fn random_rational_unitary(m: i64, n: i64, axis: u8) -> Matrix {
        let (m, n) = if m == 0 && n == 0 { (1, 0) } else { (m, n) };
        let hyp = m * m + n * n;
        let u = q(m * m - n * n, hyp);
        let v = q(2 * m * n, hyp);
        let pauli = match axis % 3 {
            0 => pauli_x(),
            1 => pauli_y(),
            2 => pauli_z(),
            _ => unreachable!(),
        };
        let term1 = Matrix::identity(2).scale(&QC::real(u));
        let term2 = pauli.scale(&QC::imag(v));
        term1.add(&term2)
    }

    fn random_unital_channel(
        m1: i64,
        n1: i64,
        ax1: u8,
        m2: i64,
        n2: i64,
        ax2: u8,
        a_wt: i64,
        b_wt: i64,
    ) -> KrausChannel {
        let u1 = random_rational_unitary(m1, n1, ax1);
        let u2 = random_rational_unitary(m2, n2, ax2);
        let (a_wt, b_wt) = if a_wt == 0 && b_wt == 0 {
            (1, 0)
        } else {
            (a_wt, b_wt)
        };
        let hyp = a_wt * a_wt + b_wt * b_wt;
        let alpha = q(a_wt * a_wt - b_wt * b_wt, hyp);
        let beta = q(2 * a_wt * b_wt, hyp);
        let k1 = u1.scale(&QC::real(alpha));
        let k2 = u2.scale(&QC::real(beta));
        KrausChannel {
            kraus: vec![k1, k2],
            cost: 0,
        }
    }

    fn random_damping_channel(m: i64, n: i64, cost: u32) -> KrausChannel {
        let (m, n) = if m == 0 || n == 0 { (3, 4) } else { (m, n) };
        let hyp = m * m + n * n;
        let beta = q(m * m - n * n, hyp);
        let alpha = q(2 * m * n, hyp);
        let a0 = Matrix::from_rows(vec![
            vec![QC::one(), QC::zero()],
            vec![QC::zero(), QC::real(beta)],
        ]);
        let a1 = Matrix::from_rows(vec![
            vec![QC::zero(), QC::real(alpha)],
            vec![QC::zero(), QC::zero()],
        ]);
        KrausChannel {
            kraus: vec![a0, a1],
            cost: cost.max(1),
        }
    }

    proptest! {
        #![proptest_config(ProptestConfig::with_cases(64))]

        #[test]
        fn prop_matrix_dagger_involution_and_trace_linearity(
            a_re in -100i64..100i64, a_im in -100i64..100i64,
            b_re in -100i64..100i64, b_im in -100i64..100i64,
            c_re in -100i64..100i64, c_im in -100i64..100i64,
            d_re in -100i64..100i64, d_im in -100i64..100i64,
        ) {
            let m = Matrix::from_rows(vec![
                vec![QC { re: q(a_re, 101), im: q(a_im, 101) }, QC { re: q(b_re, 101), im: q(b_im, 101) }],
                vec![QC { re: q(c_re, 101), im: q(c_im, 101) }, QC { re: q(d_re, 101), im: q(d_im, 101) }],
            ]);
            prop_assert_eq!(m.dagger().dagger(), m.clone());
            let tr_dag = m.dagger().trace();
            let tr_conj = m.trace().conj();
            prop_assert_eq!(tr_dag, tr_conj);
        }

        #[test]
        fn prop_unital_cptp_trace_preservation_and_purity_decay(
            a in -20i64..20i64, b in -20i64..20i64, c in -20i64..20i64, d in -20i64..20i64,
            s_num in 0u32..10u32, s_den in 1u32..10u32,
            m1 in -10i64..10i64, n1 in -10i64..10i64, ax1 in 0u8..3u8,
            m2 in -10i64..10i64, n2 in -10i64..10i64, ax2 in 0u8..3u8,
            a_wt in -10i64..10i64, b_wt in -10i64..10i64,
        ) {
            let rho = random_rational_density_matrix(a, b, c, d, s_num, s_den);
            let ch = random_unital_channel(m1, n1, ax1, m2, n2, ax2, a_wt, b_wt);
            prop_assert!(ch.is_tp());
            prop_assert!(ch.is_unital());

            let rho_next = ch.apply(&rho);
            let tr = rho_next.trace();
            prop_assert_eq!(tr.re, q(1, 1));
            prop_assert!(tr.im.is_zero());

            let p2_init = rho.purity_p2();
            let p2_next = rho_next.purity_p2();
            prop_assert!(p2_next <= p2_init);
        }

        #[test]
        fn prop_ancilla_budget_decrement_and_exhaustion(
            budget in 0u32..25u32,
            cost1 in 0u32..10u32,
            cost2 in 0u32..10u32,
            cost3 in 0u32..10u32,
            cost4 in 0u32..10u32,
        ) {
            let costs = [cost1, cost2, cost3, cost4];
            let channels: Vec<KrausChannel> = costs.iter().enumerate().map(|(idx, &c)| {
                if c == 0 {
                    random_unital_channel(3, 4, (idx % 3) as u8, 4, 3, ((idx + 1) % 3) as u8, 1, 0)
                } else {
                    random_damping_channel(3, 4, c)
                }
            }).collect();

            let u = QuantumRelationalUniverse::new(2, vec![proj0(), proj1()]);
            let res = evaluate_cptp_trajectory(&u, |_a, _b| true, &proj0(), &channels, budget, true);

            let mut rem = budget;
            let mut expected_exhaustion: Option<usize> = None;
            for (idx, &c) in costs.iter().enumerate() {
                if c > 0 {
                    if rem < c {
                        expected_exhaustion = Some(idx + 2);
                        break;
                    }
                    rem -= c;
                }
            }

            match expected_exhaustion {
                Some(k_exp) => {
                    prop_assert_eq!(res.terminal, Terminal::LiftBudgetExhaustion);
                    prop_assert_eq!(res.k_star, k_exp);
                }
                None => {
                    prop_assert_eq!(res.terminal, Terminal::TrajectoryExhaustedNoTerminal);
                    prop_assert_eq!(res.k_star, channels.len() + 1);
                }
            }
        }

        #[test]
        fn prop_povm_carrier_pigeonhole_collision(
            step_count in 2usize..8usize,
        ) {
            let u = QuantumRelationalUniverse::new(2, vec![proj0(), proj1()]);
            let m_bound = u.report_horizon_bound();
            let channels: Vec<KrausChannel> = (0..step_count)
                .map(|_| unitary(pauli_x()))
                .collect();

            let gt = |a: &usize, b: &usize| *a == 1 && *b == 0;
            let res = evaluate_cptp_trajectory(&u, gt, &proj0(), &channels, 0, false);

            prop_assert_eq!(res.terminal, Terminal::ReportCollision);
            prop_assert!(res.k_star <= m_bound);
        }

        #[test]
        fn prop_rational_entropy_taylor_enclosure_consistency(
            num in 1i64..99i64,
            prec in 8u32..18u32,
        ) {
            let p1 = q(num, 100);
            let p2 = q(100 - num, 100);
            let spec = [p1, p2];

            let enc = RationalInterval::entropy_nats_diag(&spec, prec);
            prop_assert!(enc.lo <= enc.hi);
            let target_width = q(1, 1i64 << prec);
            prop_assert!(enc.width() <= target_width);
        }
    }

    // -----------------------------------------------------------------------
    // PFP Workpad Contract JSON Roundtrip & Schema Verification Tests
    // -----------------------------------------------------------------------

    use workpad::*;

    #[test]
    fn test_qubit_povm_workpad_json_roundtrip() {
        let u = QuantumRelationalUniverse::new(2, vec![proj0(), proj1()]);
        let wp = PfpQubitPovmWorkpad::from_universe(&u, Pg3ClaimStatus::Authorized);
        let json = wp.to_json().expect("serialize povm workpad");

        assert!(json.contains("\"1/1\""));
        assert!(json.contains("\"0/1\""));
        assert!(json.contains("\"dim\": 2"));
        assert!(json.contains("\"claim_status\": \"authorized\""));

        let deserialized = PfpQubitPovmWorkpad::from_json(&json).expect("deserialize povm workpad");
        assert_eq!(wp, deserialized);

        let re_e0 = Matrix::from_json_rows(&deserialized.effects[0]);
        assert_eq!(re_e0, proj0());
    }

    #[test]
    fn test_bell_panel_povm_workpad_json_roundtrip() {
        let u = QuantumRelationalUniverse::new(4, vec![bell(0), bell(1), bell(2), bell(3)]);
        let wp = PfpQubitPovmWorkpad::from_universe(&u, Pg3ClaimStatus::EvidenceOnly);
        let json = wp.to_json().expect("serialize bell workpad");

        let deserialized = PfpQubitPovmWorkpad::from_json(&json).expect("deserialize bell workpad");
        assert_eq!(wp, deserialized);
        assert_eq!(deserialized.dim, 4);
        assert_eq!(deserialized.report_capacity_n, 4);
        assert_eq!(deserialized.horizon_bound, 5);
        assert_eq!(deserialized.gram_determinant, RationalJson(q(1, 1)));
    }

    #[test]
    fn test_purity_budget_workpad_json_roundtrip() {
        let i2 = Matrix::identity(2);
        let depol = KrausChannel {
            kraus: vec![
                i2.scale(&half()).kron(&i2),
                pauli_x().scale(&half()).kron(&i2),
                pauli_y().scale(&half()).kron(&i2),
                pauli_z().scale(&half()).kron(&i2),
            ],
            cost: 0,
        };
        let a0 = Matrix::real_from(2, 2, &[(1, 1), (0, 1), (0, 1), (0, 1)]);
        let a1 = Matrix::real_from(2, 2, &[(0, 1), (1, 1), (0, 1), (0, 1)]);
        let damp_q2 = KrausChannel {
            kraus: vec![i2.kron(&a0), i2.kron(&a1)],
            cost: 1,
        };
        let damp_q1 = KrausChannel {
            kraus: vec![a0.kron(&i2), a1.kron(&i2)],
            cost: 1,
        };
        let damp_q1_again = KrausChannel {
            kraus: vec![a0.kron(&i2), a1.kron(&i2)],
            cost: 1,
        };

        let u = QuantumRelationalUniverse::new(4, vec![bell(0), bell(1), bell(2), bell(3)]);
        let chans = vec![depol, damp_q2, damp_q1, damp_q1_again];
        let res = evaluate_cptp_trajectory(&u, |_a, _b| true, &bell(3), &chans, 2, true);

        let wp =
            PfpPurityBudgetWorkpad::from_trajectory(2, &chans, &res, Pg3ClaimStatus::Authorized);
        let json = wp.to_json().expect("serialize budget workpad");

        assert!(json.contains("\"B0\": 2"));
        assert!(json.contains("\"terminal\": \"LIFT_BUDGET_EXHAUSTION\""));
        assert!(json.contains("\"k_star\": 5"));
        assert!(json.contains("\"lemma_q3_checked\": true"));

        let deserialized =
            PfpPurityBudgetWorkpad::from_json(&json).expect("deserialize budget workpad");
        assert_eq!(wp, deserialized);
    }

    #[test]
    fn test_contextuality_holonomy_workpad_json_roundtrip() {
        let contexts = vec![
            vec![0, 1, 2, 3],
            vec![0, 4, 5, 6],
            vec![7, 8, 2, 9],
            vec![7, 10, 5, 11],
            vec![1, 4, 12, 13],
            vec![8, 10, 12, 14],
            vec![3, 9, 15, 16],
            vec![6, 11, 15, 17],
            vec![13, 14, 16, 17],
        ];
        let nerve = SimplicialNerve {
            contexts,
            support: Box::new(|_i, s: &[u8]| s.iter().filter(|&&b| b == 1).count() == 1),
        };

        let wp = PfpContextualityHolonomyWorkpad::from_simplicial_nerve(
            &nerve,
            q(47, 125),
            Some(vec![0, 1, 1, 1]),
            Terminal::OverlapGluingRefusal,
            Pg3ClaimStatus::Authorized,
        );
        let json = wp.to_json().expect("serialize contextuality workpad");

        assert!(json.contains("\"phi_glue\": 1"));
        assert!(json.contains("\"prompt_d1d0_defect\": 0"));
        assert!(json.contains("\"parity_class_nonzero\": true"));
        assert!(json.contains("\"contextual_fraction_lower\": \"47/125\""));
        assert!(json.contains("\"terminal\": \"OVERLAP_GLUING_REFUSAL\""));

        let deserialized = PfpContextualityHolonomyWorkpad::from_json(&json)
            .expect("deserialize contextuality workpad");
        assert_eq!(wp, deserialized);
    }

    #[test]
    fn test_rational_interval_workpad_json_roundtrip() {
        let spec = [q(3, 5), q(2, 5)];
        let ad = RationalInterval::entropy_nats_diag(&spec, 15);

        let wp = PfpRationalIntervalWorkpad::from_interval(
            &spec,
            Some(&[2, 4]),
            15,
            &ad,
            Pg3ClaimStatus::Authorized,
        );
        let json = wp.to_json().expect("serialize interval workpad");

        assert!(json.contains("\"precision_bits\": 15"));
        assert!(json.contains("\"certified\": true"));
        assert!(json.contains("\"baker_applies\": true"));
        assert!(json.contains("\"L\":"));
        assert!(json.contains("\"U\":"));

        let deserialized =
            PfpRationalIntervalWorkpad::from_json(&json).expect("deserialize interval workpad");
        assert_eq!(wp, deserialized);
    }

    #[test]
    fn test_rational_json_syntax_validation() {
        let v1: Result<RationalJson, _> = serde_json::from_str("\"0/1\"");
        assert!(v1.is_ok());
        assert_eq!(v1.unwrap().0, q(0, 1));

        let v2: Result<RationalJson, _> = serde_json::from_str("\"-13/25\"");
        assert!(v2.is_ok());
        assert_eq!(v2.unwrap().0, q(-13, 25));

        let inv1: Result<RationalJson, _> = serde_json::from_str("\"1\"");
        assert!(inv1.is_err(), "missing denominator slash must fail");

        let inv2: Result<RationalJson, _> = serde_json::from_str("\"1/0\"");
        assert!(inv2.is_err(), "zero denominator must fail");

        let inv3: Result<RationalJson, _> = serde_json::from_str("\"1/-5\"");
        assert!(inv3.is_err(), "negative denominator must fail");

        let inv4: Result<RationalJson, _> = serde_json::from_str("\"abc\"");
        assert!(inv4.is_err(), "non-numeric string must fail");

        let inv5: Result<RationalJson, _> = serde_json::from_str("123");
        assert!(inv5.is_err(), "numeric literal must fail");
    }

    #[test]
    fn test_emit_canonical_workpad_json_payloads() {
        let out_dir = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../tests/core_quantum_physics/fixtures/pfp_workpads");
        let emitted = emit_canonical_workpads_to_dir(&out_dir).expect("emit canonical workpads");
        assert_eq!(emitted.len(), 5);
        for p in emitted {
            assert!(p.exists());
            let content = std::fs::read_to_string(&p).expect("read emitted file");
            assert!(!content.is_empty());
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_9525e5aa {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord9525e5aa::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord9525e5aa::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord9525e5aa::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord9525e5aa::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord9525e5aa::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError9525e5aa::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError9525e5aa::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
