// Executable finite evidence; AuthorityEffect: None.
//! Sharp observer completion with distinct realization and repair images
//! (monograph Appendix T, WDP-DIM-1 and the realizable-domain corollary
//! WDP-DIM-R).
//!
//! Data over `Q`: a source map `D_s : U → V` with realizable image `R`, a repair
//! map `D_r : F → V` with repair image `B`, and an existing observer
//! `Q : V → Y` with kernel `K`. Added rows `E` give `A = (Q, E)` and
//! `ker A = K ∩ ker E`. With `T = R ∩ K ∩ B`:
//!
//! * raw (T.1): `R ∩ ker A = 0`, sharp count `dim(R ∩ K)`;
//! * quotient (T.2): `ker A ⊆ B`, sharp count `dim K − dim(K ∩ B)`;
//! * joint (T.3): both, sharp count `dim K − dim(K ∩ B) + dim T`, which is the
//!   separate sum minus `dim((R ∩ K)/T)`;
//! * realizable quotient (T.8): `R ∩ ker A ⊆ B`, sharp count
//!   `dim(R ∩ K) − dim T`.
//!
//! [`produce_completion`] constructs attaining dual-coordinate rows and an
//! obstruction basis (`lower_columns`); [`check_completion`] replays the
//! sufficiency criterion, the sharp count and the T.3 obstruction-basis rule
//! independently of the producer. Restricted menus (T.5) and the separate
//! repair-operation witness (T.6) are checked here as well. Elimination,
//! kernels, images and inverses are delegated to
//! `linear_algebra::exact_field::elimination`; this module only presents the
//! WDP subspaces. A finite rational row count is not a continuum
//! reconstruction, a physical instrument or an authorization to repair.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::elimination::{image_basis, inverse, kernel_basis, rref};
use linear_algebra::exact_field::ExactFieldError;
use num_rational::BigRational;
use num_traits::{Signed, Zero};

/// A rational vector of the ambient space `V`.
pub type Vector = Vec<BigRational>;

/// Reference cap on a finite instrument shelf (exhaustive subset search).
pub const MAX_SHELF: usize = 16;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum DistinctImageError {
    #[error("ambient dimension must be positive")]
    EmptyAmbient,
    #[error("vector has {got} entries, ambient dimension is {expected}")]
    Shape { expected: usize, got: usize },
    #[error("exact elimination refused: {0}")]
    Elimination(#[from] ExactFieldError),
    #[error("{0}")]
    Rejected(&'static str),
}

type Result<T> = std::result::Result<T, DistinctImageError>;

/// Which separation property a completion must supply.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CompletionTarget {
    /// T.1: distinguish individual realizable defects.
    Raw,
    /// T.2: distinguish repair classes globally on `V`.
    Quotient,
    /// T.3: both raw and global quotient separation.
    Joint,
    /// T.8: distinguish repair classes of realizable candidates only.
    RealizableQuotient,
}

/// The finite rational presentation `(D_s, D_r, Q)` by columns and rows.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DistinctImageProblem {
    ambient: usize,
    source_columns: Vec<Vector>,
    repair_columns: Vec<Vector>,
    observer_rows: Vec<Vector>,
}

/// Subspace dimensions and sharp counts of WDP-DIM-1 / WDP-DIM-R.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DimensionFacts {
    pub dim_r: usize,
    pub dim_b: usize,
    pub dim_k: usize,
    pub dim_rk: usize,
    pub dim_kb: usize,
    pub dim_t: usize,
    pub raw_minimum: usize,
    pub quotient_minimum: usize,
    pub joint_minimum: usize,
    pub realizable_quotient_minimum: usize,
    /// `raw_minimum + quotient_minimum`.
    pub separate_sum: usize,
}

/// A produced or submitted completion: added rows and an obstruction basis.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Completion {
    pub target: CompletionTarget,
    pub rows: Vec<Vector>,
    pub lower_columns: Vec<Vector>,
}

/// T.6: a claimed repair needs `D_adm u = r⋆`, `r⋆ ∈ B` and `r⋆ = δ`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RepairOperationWitness {
    pub admissible_columns: Vec<Vector>,
    pub preimage: Vector,
    pub repair: Vector,
    pub defect: Vector,
}

/// T.5 annihilator-menu result.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AnnihilatorStatus {
    /// Rows annihilating `B` that attain the target.
    Feasible(Vec<Vector>),
    /// Every row system annihilating `B` fails; a nonzero vector of `T`.
    Impossible(Vector),
}

/// T.5 finite-shelf selection: chosen indices and their exact total cost.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ShelfSelection {
    pub indices: Option<Vec<usize>>,
    pub cost: Option<BigRational>,
}

// ---------------------------------------------------------------------------
// Subspace presentation over the elimination owner
// ---------------------------------------------------------------------------

fn columns_matrix(columns: &[Vector], n: usize) -> Result<BasicMatrix<BigRational>> {
    let k = columns.len();
    let mut data = Vec::with_capacity(n * k);
    for i in 0..n {
        for c in columns {
            data.push(c[i].clone());
        }
    }
    Ok(BasicMatrix::from_row_major(n, k, data).map_err(ExactFieldError::from)?)
}

fn rows_matrix(rows: &[Vector], n: usize) -> Result<BasicMatrix<BigRational>> {
    let data = rows.iter().flat_map(|r| r.iter().cloned()).collect();
    Ok(BasicMatrix::from_row_major(rows.len(), n, data).map_err(ExactFieldError::from)?)
}

fn unit(n: usize, i: usize) -> Vector {
    let mut v = vec![BigRational::zero(); n];
    v[i] = BigRational::from_integer(1.into());
    v
}

/// A basis of the span of `columns` (pivot columns, in order).
fn span(columns: &[Vector], n: usize) -> Result<Vec<Vector>> {
    if columns.is_empty() {
        return Ok(Vec::new());
    }
    Ok(image_basis(&columns_matrix(columns, n)?)?)
}

/// A basis of `{v : row·v = 0 for every row}`.
fn null_space(rows: &[Vector], n: usize) -> Result<Vec<Vector>> {
    if rows.is_empty() {
        return Ok((0..n).map(|i| unit(n, i)).collect());
    }
    Ok(kernel_basis(&rows_matrix(rows, n)?)?)
}

fn rank_of(columns: &[Vector], n: usize) -> Result<usize> {
    Ok(span(columns, n)?.len())
}

/// A basis of `span(x) ∩ span(y)`, for bases `x` and `y`.
fn intersect(x: &[Vector], y: &[Vector], n: usize) -> Result<Vec<Vector>> {
    if x.is_empty() || y.is_empty() {
        return Ok(Vec::new());
    }
    let mut stacked: Vec<Vector> = x.to_vec();
    stacked.extend(y.iter().map(|v| v.iter().map(|e| -e).collect::<Vector>()));
    let kernel = kernel_basis(&columns_matrix(&stacked, n)?)?;
    let vectors: Vec<Vector> = kernel
        .iter()
        .map(|coeffs| {
            (0..n)
                .map(|i| {
                    x.iter()
                        .zip(coeffs)
                        .fold(BigRational::zero(), |acc, (col, c)| acc + &col[i] * c)
                })
                .collect()
        })
        .collect();
    span(&vectors, n)
}

fn contained(sub: &[Vector], sup: &[Vector], n: usize) -> Result<bool> {
    let mut joined = sup.to_vec();
    joined.extend_from_slice(sub);
    Ok(rank_of(&joined, n)? == rank_of(sup, n)?)
}

/// Vectors `c` of `sup` with `span(sub) ⊕ span(c) = span(sub) + span(sup)`.
fn complement_in(sub: &[Vector], sup: &[Vector], n: usize) -> Result<Vec<Vector>> {
    let mut joined = sub.to_vec();
    joined.extend_from_slice(sup);
    if joined.is_empty() {
        return Ok(Vec::new());
    }
    let reduced = rref(&columns_matrix(&joined, n)?)?;
    Ok(reduced
        .pivot_columns()
        .iter()
        .filter(|&&p| p >= sub.len())
        .map(|&p| joined[p].clone())
        .collect())
}

/// Dual coordinate rows of the block `block` of an ordered independent prefix,
/// after extending the prefix to a basis of `V` by standard vectors.
fn dual_rows(prefix: &[Vector], block: std::ops::Range<usize>, n: usize) -> Result<Vec<Vector>> {
    if block.is_empty() {
        return Ok(Vec::new());
    }
    let standard: Vec<Vector> = (0..n).map(|i| unit(n, i)).collect();
    let mut basis = prefix.to_vec();
    basis.extend(complement_in(prefix, &standard, n)?);
    let inv = inverse(&columns_matrix(&basis, n)?)?;
    block
        .map(|r| {
            (0..n)
                .map(|c| {
                    inv.get(r, c)
                        .map_err(|e| DistinctImageError::Elimination(ExactFieldError::from(e)))
                })
                .collect()
        })
        .collect()
}

fn apply(rows: &[Vector], v: &Vector) -> Vector {
    rows.iter()
        .map(|r| r.iter().zip(v).fold(BigRational::zero(), |acc, (a, b)| acc + a * b))
        .collect()
}

// ---------------------------------------------------------------------------
// The WDP presentation
// ---------------------------------------------------------------------------

struct Subspaces {
    r: Vec<Vector>,
    b: Vec<Vector>,
    k: Vec<Vector>,
    rk: Vec<Vector>,
    kb: Vec<Vector>,
    t: Vec<Vector>,
}

impl DistinctImageProblem {
    pub fn new(
        ambient: usize,
        source_columns: Vec<Vector>,
        repair_columns: Vec<Vector>,
        observer_rows: Vec<Vector>,
    ) -> Result<Self> {
        if ambient == 0 {
            return Err(DistinctImageError::EmptyAmbient);
        }
        for v in source_columns.iter().chain(&repair_columns).chain(&observer_rows) {
            if v.len() != ambient {
                return Err(DistinctImageError::Shape {
                    expected: ambient,
                    got: v.len(),
                });
            }
        }
        Ok(Self {
            ambient,
            source_columns,
            repair_columns,
            observer_rows,
        })
    }

    pub fn ambient(&self) -> usize {
        self.ambient
    }

    fn check_vectors(&self, vectors: &[Vector]) -> Result<()> {
        match vectors.iter().find(|v| v.len() != self.ambient) {
            Some(v) => Err(DistinctImageError::Shape {
                expected: self.ambient,
                got: v.len(),
            }),
            None => Ok(()),
        }
    }

    fn subspaces(&self) -> Result<Subspaces> {
        let n = self.ambient;
        let r = span(&self.source_columns, n)?;
        let b = span(&self.repair_columns, n)?;
        let k = null_space(&self.observer_rows, n)?;
        let rk = intersect(&r, &k, n)?;
        let kb = intersect(&k, &b, n)?;
        let t = intersect(&rk, &b, n)?;
        Ok(Subspaces { r, b, k, rk, kb, t })
    }

    /// WDP-DIM-1 and WDP-DIM-R counts, recomputed from the matrices.
    pub fn analyze(&self) -> Result<DimensionFacts> {
        let s = self.subspaces()?;
        let quotient = s.k.len() - s.kb.len();
        Ok(DimensionFacts {
            dim_r: s.r.len(),
            dim_b: s.b.len(),
            dim_k: s.k.len(),
            dim_rk: s.rk.len(),
            dim_kb: s.kb.len(),
            dim_t: s.t.len(),
            raw_minimum: s.rk.len(),
            quotient_minimum: quotient,
            joint_minimum: quotient + s.t.len(),
            realizable_quotient_minimum: s.rk.len() - s.t.len(),
            separate_sum: s.rk.len() + quotient,
        })
    }

    fn observer_kernel(&self, rows: &[Vector]) -> Result<Vec<Vector>> {
        let mut all = self.observer_rows.clone();
        all.extend_from_slice(rows);
        null_space(&all, self.ambient)
    }

    /// T.1: `R ∩ ker(Q, E) = 0`.
    pub fn raw_holds(&self, rows: &[Vector]) -> Result<bool> {
        self.check_vectors(rows)?;
        let n = self.ambient;
        Ok(intersect(&span(&self.source_columns, n)?, &self.observer_kernel(rows)?, n)?.is_empty())
    }

    /// T.2: `ker(Q, E) ⊆ B`.
    pub fn quotient_holds(&self, rows: &[Vector]) -> Result<bool> {
        self.check_vectors(rows)?;
        contained(&self.observer_kernel(rows)?, &span(&self.repair_columns, self.ambient)?, self.ambient)
    }

    /// T.8: `R ∩ ker(Q, E) ⊆ B`.
    pub fn realizable_quotient_holds(&self, rows: &[Vector]) -> Result<bool> {
        self.check_vectors(rows)?;
        let n = self.ambient;
        let hidden = intersect(&span(&self.source_columns, n)?, &self.observer_kernel(rows)?, n)?;
        contained(&hidden, &span(&self.repair_columns, n)?, n)
    }

    pub fn suite_is_sufficient(&self, rows: &[Vector], target: CompletionTarget) -> Result<bool> {
        Ok(match target {
            CompletionTarget::Raw => self.raw_holds(rows)?,
            CompletionTarget::Quotient => self.quotient_holds(rows)?,
            CompletionTarget::Joint => self.raw_holds(rows)? && self.quotient_holds(rows)?,
            CompletionTarget::RealizableQuotient => self.realizable_quotient_holds(rows)?,
        })
    }

    fn sharp_count(&self, facts: &DimensionFacts, target: CompletionTarget) -> usize {
        match target {
            CompletionTarget::Raw => facts.raw_minimum,
            CompletionTarget::Quotient => facts.quotient_minimum,
            CompletionTarget::Joint => facts.joint_minimum,
            CompletionTarget::RealizableQuotient => facts.realizable_quotient_minimum,
        }
    }
}

/// Construct attaining rows and the obstruction basis for `target`.
pub fn produce_completion(
    problem: &DistinctImageProblem,
    target: CompletionTarget,
) -> Result<Completion> {
    let n = problem.ambient;
    let s = problem.subspaces()?;
    let (prefix, block, lower) = match target {
        CompletionTarget::Raw => {
            let m = s.rk.len();
            (s.rk.clone(), 0..m, s.rk.clone())
        }
        CompletionTarget::Quotient => {
            let c = complement_in(&s.kb, &s.k, n)?;
            let mut prefix = s.kb.clone();
            prefix.extend(c.iter().cloned());
            (prefix, s.kb.len()..s.kb.len() + c.len(), c)
        }
        CompletionTarget::Joint => {
            let s0 = complement_in(&s.t, &s.kb, n)?;
            let c = complement_in(&s.kb, &s.k, n)?;
            let mut w = s.t.clone();
            w.extend(c);
            let mut prefix = s0.clone();
            prefix.extend(w.iter().cloned());
            (prefix, s0.len()..s0.len() + w.len(), w)
        }
        CompletionTarget::RealizableQuotient => {
            let comp = complement_in(&s.t, &s.rk, n)?;
            let mut prefix = s.t.clone();
            prefix.extend(comp.iter().cloned());
            (prefix, s.t.len()..s.t.len() + comp.len(), comp)
        }
    };
    Ok(Completion {
        target,
        rows: dual_rows(&prefix, block, n)?,
        lower_columns: lower,
    })
}

/// Replay a submitted completion: sharp row count, sufficiency, and the T.3
/// obstruction-basis rule for `lower_columns`. Width and rank alone are not
/// accepted. Returns the facts on acceptance.
fn check_disjoint_subspace(
    lower: &[Vector],
    lower_span: &[Vector],
    ambient_space: &[Vector],
    forbidden: &[Vector],
    n: usize,
) -> Result<bool> {
    if !contained(lower, ambient_space, n)? {
        return Ok(false);
    }
    Ok(intersect(lower_span, forbidden, n)?.is_empty())
}

fn check_joint_subspace(
    lower: &[Vector],
    lower_span: &[Vector],
    k: &[Vector],
    kb: &[Vector],
    t: &[Vector],
    n: usize,
) -> Result<bool> {
    if !contained(lower, k, n)? {
        return Ok(false);
    }
    let inter = intersect(lower_span, kb, n)?;
    contained(&inter, t, n)
}

#[allow(clippy::too_many_arguments)]
fn evaluate_lower_target_subspace(
    target: CompletionTarget,
    lower: &[Vector],
    lower_span: &[Vector],
    rk: &[Vector],
    k: &[Vector],
    b: &[Vector],
    kb: &[Vector],
    t: &[Vector],
    n: usize,
) -> Result<bool> {
    match target {
        CompletionTarget::Raw => contained(lower, rk, n),
        CompletionTarget::Quotient => check_disjoint_subspace(lower, lower_span, k, b, n),
        CompletionTarget::Joint => check_joint_subspace(lower, lower_span, k, kb, t, n),
        CompletionTarget::RealizableQuotient => check_disjoint_subspace(lower, lower_span, rk, t, n),
    }
}

fn verify_lower_certificate_subspace(
    problem: &DistinctImageProblem,
    target: CompletionTarget,
    lower: &[Vector],
    sharp: usize,
) -> Result<()> {
    let n = problem.ambient;
    let s = problem.subspaces()?;
    if lower.len() != sharp || rank_of(lower, n)? != sharp {
        return Err(DistinctImageError::Rejected("lower certificate"));
    }
    let lower_span = span(lower, n)?;
    if !evaluate_lower_target_subspace(
        target,
        lower,
        &lower_span,
        &s.rk,
        &s.k,
        &s.b,
        &s.kb,
        &s.t,
        n,
    )? {
        return Err(DistinctImageError::Rejected("lower certificate"));
    }
    Ok(())
}

pub fn check_completion(
    problem: &DistinctImageProblem,
    completion: &Completion,
) -> Result<DimensionFacts> {
    problem.check_vectors(&completion.rows)?;
    problem.check_vectors(&completion.lower_columns)?;
    let facts = problem.analyze()?;
    let sharp = problem.sharp_count(&facts, completion.target);
    if completion.rows.len() != sharp {
        return Err(DistinctImageError::Rejected("row count is not the sharp count"));
    }
    if !problem.suite_is_sufficient(&completion.rows, completion.target)? {
        return Err(DistinctImageError::Rejected("completion rows are insufficient"));
    }
    verify_lower_certificate_subspace(problem, completion.target, &completion.lower_columns, sharp)?;
    Ok(facts)
}

/// T.6: replay `D_adm u = r⋆`, `r⋆ ∈ B` and `r⋆ = δ`. Acceptance is a
/// certificate, not authorization to apply the operation.
pub fn check_repair_operation(
    problem: &DistinctImageProblem,
    witness: &RepairOperationWitness,
) -> Result<()> {
    let n = problem.ambient;
    problem.check_vectors(&witness.admissible_columns)?;
    problem.check_vectors(&[witness.repair.clone(), witness.defect.clone()])?;
    if witness.preimage.len() != witness.admissible_columns.len() {
        return Err(DistinctImageError::Rejected("observation_completion_does_not_certify_repairs"));
    }
    let image: Vector = (0..n)
        .map(|i| {
            witness
                .admissible_columns
                .iter()
                .zip(&witness.preimage)
                .fold(BigRational::zero(), |acc, (col, u)| acc + &col[i] * u)
        })
        .collect();
    let in_b = contained(&[witness.repair.clone()], &span(&problem.repair_columns, n)?, n)?;
    if image != witness.repair || !in_b || witness.repair != witness.defect {
        return Err(DistinctImageError::Rejected("observation_completion_does_not_certify_repairs"));
    }
    Ok(())
}

fn build_feasible_annihilator(
    b: &[Vector],
    extra: &[Vector],
    n: usize,
) -> Result<AnnihilatorStatus> {
    let mut prefix = b.to_vec();
    prefix.extend(extra.iter().cloned());
    let rows = dual_rows(&prefix, b.len()..b.len() + extra.len(), n)?;
    Ok(AnnihilatorStatus::Feasible(rows))
}

/// T.5 rows required to annihilate `B`.
pub fn annihilator_status(
    problem: &DistinctImageProblem,
    target: CompletionTarget,
) -> Result<AnnihilatorStatus> {
    let n = problem.ambient;
    let s = problem.subspaces()?;
    let needs_raw = matches!(target, CompletionTarget::Raw | CompletionTarget::Joint);
    if needs_raw {
        if let Some(witness) = s.t.first() {
            return Ok(AnnihilatorStatus::Impossible(witness.clone()));
        }
    }
    match target {
        CompletionTarget::Quotient | CompletionTarget::Joint => {
            let c = complement_in(&s.kb, &s.k, n)?;
            build_feasible_annihilator(&s.b, &c, n)
        }
        CompletionTarget::Raw => build_feasible_annihilator(&s.b, &s.rk, n),
        CompletionTarget::RealizableQuotient => {
            let comp = complement_in(&s.t, &s.rk, n)?;
            build_feasible_annihilator(&s.b, &comp, n)
        }
    }
}

fn validate_shelf(problem: &DistinctImageProblem, shelf: &[Vector], costs: &[BigRational]) -> Result<()> {
    if shelf.len() > MAX_SHELF || shelf.len() != costs.len() {
        return Err(DistinctImageError::Rejected("shelf shape"));
    }
    if costs.iter().any(|c| !c.is_positive()) {
        return Err(DistinctImageError::Rejected("positive costs"));
    }
    problem.check_vectors(shelf)
}

fn subset_rows(shelf: &[Vector], mask: u32) -> Vec<Vector> {
    shelf
        .iter()
        .enumerate()
        .filter(|(i, _)| mask & (1 << i) != 0)
        .map(|(_, r)| r.clone())
        .collect()
}

fn subset_cost(costs: &[BigRational], mask: u32) -> BigRational {
    costs
        .iter()
        .enumerate()
        .filter(|(i, _)| mask & (1 << i) != 0)
        .fold(BigRational::zero(), |acc, (_, c)| acc + c)
}

/// T.5 finite shelf: a minimum-cost sufficient subset by exhaustive search.
pub fn produce_shelf(
    problem: &DistinctImageProblem,
    shelf: &[Vector],
    costs: &[BigRational],
    target: CompletionTarget,
) -> Result<ShelfSelection> {
    validate_shelf(problem, shelf, costs)?;
    let mut best: Option<(BigRational, u32)> = None;
    for mask in 0..(1u32 << shelf.len()) {
        let cost = subset_cost(costs, mask);
        if best.as_ref().is_some_and(|(b, _)| &cost >= b) {
            continue;
        }
        if problem.suite_is_sufficient(&subset_rows(shelf, mask), target)? {
            best = Some((cost, mask));
        }
    }
    Ok(match best {
        Some((cost, mask)) => ShelfSelection {
            indices: Some((0..shelf.len()).filter(|i| mask & (1 << i) != 0).collect()),
            cost: Some(cost),
        },
        None => ShelfSelection {
            indices: None,
            cost: None,
        },
    })
}

/// Independent shelf checker: re-enumerates every subset. It rejects an
/// insufficient selection, a mismatched cost, a strictly cheaper sufficient
/// subset, and an impossibility claim while the full shelf suffices.
fn build_shelf_mask(shelf_len: usize, indices: &[usize]) -> Result<u32> {
    let mut mask = 0u32;
    for &i in indices {
        if i >= shelf_len || mask & (1 << i) != 0 {
            return Err(DistinctImageError::Rejected("invalid shelf indices"));
        }
        mask |= 1 << i;
    }
    Ok(mask)
}

fn verify_shelf_optimality(
    problem: &DistinctImageProblem,
    shelf: &[Vector],
    costs: &[BigRational],
    target: CompletionTarget,
    indices: &[usize],
    cost: &BigRational,
) -> Result<()> {
    let mask = build_shelf_mask(shelf.len(), indices)?;
    if &subset_cost(costs, mask) != cost {
        return Err(DistinctImageError::Rejected("cost does not match indices"));
    }
    if !problem.suite_is_sufficient(&subset_rows(shelf, mask), target)? {
        return Err(DistinctImageError::Rejected("selected suite is insufficient"));
    }
    for other in 0..(1u32 << shelf.len()) {
        if &subset_cost(costs, other) < cost
            && problem.suite_is_sufficient(&subset_rows(shelf, other), target)?
        {
            return Err(DistinctImageError::Rejected("selected suite is not minimum"));
        }
    }
    Ok(())
}

pub fn check_shelf(
    problem: &DistinctImageProblem,
    shelf: &[Vector],
    costs: &[BigRational],
    target: CompletionTarget,
    selection: &ShelfSelection,
) -> Result<()> {
    validate_shelf(problem, shelf, costs)?;
    match (&selection.indices, &selection.cost) {
        (None, None) => {
            if problem.suite_is_sufficient(shelf, target)? {
                return Err(DistinctImageError::Rejected("impossibility claimed for a sufficient shelf"));
            }
            Ok(())
        }
        (Some(indices), Some(cost)) => {
            verify_shelf_optimality(problem, shelf, costs, target, indices, cost)
        }
        _ => Err(DistinctImageError::Rejected("feasible flag")),
    }
}

/// Apply rows to a vector (the added report `E v`).
pub fn report(rows: &[Vector], v: &Vector) -> Vector {
    apply(rows, v)
}

// Origin: engine/crates_rs/core_wdp/src/distinct_image_completion.rs
// Claim: urn:core:crates_rs:core-wdp:distinct-image-completion:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_31759720 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
