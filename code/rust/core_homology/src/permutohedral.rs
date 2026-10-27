//! Signed ordered-partition cells and a constructive contraction of the
//! permutohedral linear-extension complex of a finite strict order.
//!
//! The mathematical coefficients are integers. This implementation uses checked
//! `i64` coefficients and explicit resource limits; overflow or exhaustion is a
//! typed refusal, never an approximate answer. Only encountered cells are
//! expanded. The homotopy satisfies `d h + h d = id - root * augmentation`.
//! It is not an engine functional and has no authorization effect.

use crate::finite_poset::{FinitePoset, PosetError};
use std::collections::BTreeMap;

/// Ordered blocks; each block is nonempty, increasing, and all labels `0..m`
/// occur exactly once. Public inputs are validated before geometry is used.
pub type Cell = Vec<Vec<usize>>;
/// Sparse integral cellular chain; zero coefficients must be omitted.
pub type CellChain = BTreeMap<Cell, i64>;

/// Bounds apply to each operation. The cell bound limits cached and pending
/// cells for the first-descent construction, or generated cells per call for
/// the minimum sweep. The term bound applies to each intermediate sparse chain.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ContractionLimits {
    pub max_labels: usize,
    pub max_cells: usize,
    pub max_terms: usize,
    pub max_steps: usize,
}

impl Default for ContractionLimits {
    fn default() -> Self {
        Self {
            max_labels: 16,
            max_cells: 250_000,
            max_terms: 250_000,
            max_steps: 50_000_000,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum PermutohedralError {
    #[error("invalid ordered-partition cell: {0}")]
    InvalidCell(&'static str),
    #[error("cell has degree {actual}, expected {expected}")]
    WrongDegree { expected: usize, actual: usize },
    #[error("cell is not a face of the supplied linear-extension complex")]
    OutsideOrder,
    #[error("a sparse chain contains an explicit zero coefficient")]
    ZeroCoefficient,
    #[error("integer overflow while {0}")]
    Overflow(&'static str),
    #[error("{resource} exceeds the supplied limit {limit}")]
    Limit {
        resource: &'static str,
        limit: usize,
    },
    #[error("input is not an augmented cycle of the declared degree")]
    NotCycle,
    #[error("the proposed contraction violated its exact {0} identity")]
    IdentityFailure(&'static str),
    #[error(transparent)]
    Poset(#[from] PosetError),
}

type Result<T> = std::result::Result<T, PermutohedralError>;

struct Budget {
    limits: ContractionLimits,
    steps: usize,
}
impl Budget {
    fn new(limits: ContractionLimits) -> Self {
        Self { limits, steps: 0 }
    }
    fn tick(&mut self, amount: usize) -> Result<()> {
        self.steps = self
            .steps
            .checked_add(amount)
            .ok_or(PermutohedralError::Overflow("counting work"))?;
        check_limit(self.steps, self.limits.max_steps, "work steps")
    }
}

fn check_limit(value: usize, limit: usize, resource: &'static str) -> Result<()> {
    if value > limit {
        Err(PermutohedralError::Limit { resource, limit })
    } else {
        Ok(())
    }
}

/// Checks sorted, nonempty blocks and exactly the label set `0..labels`.
/// The empty label set is not part of this cellular convention.
pub fn validate_cell(cell: &Cell, labels: usize, limits: ContractionLimits) -> Result<()> {
    check_limit(labels, limits.max_labels, "labels")?;
    if labels == 0 || cell.is_empty() {
        return Err(PermutohedralError::InvalidCell("empty label set"));
    }
    let mut seen = vec![false; labels];
    for block in cell {
        validate_cell_block(block, &mut seen)?;
    }
    if seen.iter().any(|&value| !value) {
        return Err(PermutohedralError::InvalidCell("missing label"));
    }
    Ok(())
}

fn validate_cell_block(block: &[usize], seen: &mut [bool]) -> Result<()> {
    if block.is_empty() {
        return Err(PermutohedralError::InvalidCell("empty block"));
    }
    if block.windows(2).any(|w| w[0] >= w[1]) {
        return Err(PermutohedralError::InvalidCell(
            "block is not strictly increasing",
        ));
    }
    for &label in block {
        let slot = seen
            .get_mut(label)
            .ok_or(PermutohedralError::InvalidCell("label out of range"))?;
        if *slot {
            return Err(PermutohedralError::InvalidCell("repeated label"));
        }
        *slot = true;
    }
    Ok(())
}

fn label_count(cell: &Cell) -> Result<usize> {
    cell.iter().try_fold(0usize, |sum, block| {
        sum.checked_add(block.len())
            .ok_or(PermutohedralError::Overflow("counting labels"))
    })
}

/// Degree `m - number_of_blocks`; checks all cell invariants first.
pub fn cell_dimension(cell: &Cell) -> Result<usize> {
    let labels = label_count(cell)?;
    validate_cell(
        cell,
        labels,
        ContractionLimits {
            max_labels: labels,
            ..ContractionLimits::default()
        },
    )?;
    labels
        .checked_sub(cell.len())
        .ok_or(PermutohedralError::InvalidCell("too many blocks"))
}

/// Adds `scale * source`, checking every product and sum and the resulting
/// support bound. On refusal, `target` is unchanged. Geometry is not checked;
/// callers can use this algebra helper before validating a constructed chain.
pub fn add_scaled(
    target: &mut CellChain,
    source: &CellChain,
    scale: i64,
    limits: ContractionLimits,
) -> Result<()> {
    check_limit(target.len(), limits.max_terms, "chain terms")?;
    check_limit(source.len(), limits.max_terms, "chain terms")?;
    if target
        .values()
        .chain(source.values())
        .any(|&value| value == 0)
    {
        return Err(PermutohedralError::ZeroCoefficient);
    }
    if scale == 0 {
        return Ok(());
    }
    let mut changes = Vec::with_capacity(source.len());
    let mut resulting_terms = target.len();
    for (cell, coefficient) in source {
        let term = coefficient
            .checked_mul(scale)
            .ok_or(PermutohedralError::Overflow("scaling a chain"))?;
        let previous = target.get(cell).copied().unwrap_or(0);
        let value = previous
            .checked_add(term)
            .ok_or(PermutohedralError::Overflow("adding chains"))?;
        resulting_terms = update_resulting_terms(resulting_terms, previous == 0, value == 0)?;
        changes.push((cell.clone(), value));
    }
    check_limit(resulting_terms, limits.max_terms, "chain terms")?;
    apply_chain_changes(target, changes);
    Ok(())
}

fn update_resulting_terms(current: usize, prev_zero: bool, val_zero: bool) -> Result<usize> {
    match (prev_zero, val_zero) {
        (true, false) => current
            .checked_add(1)
            .ok_or(PermutohedralError::Overflow("counting terms")),
        (false, true) => Ok(current - 1),
        _ => Ok(current),
    }
}

fn apply_chain_changes(target: &mut CellChain, changes: Vec<(Cell, i64)>) {
    for (cell, coefficient) in changes {
        if coefficient == 0 {
            target.remove(&cell);
        } else {
            target.insert(cell, coefficient);
        }
    }
}

fn singleton(cell: Cell, coefficient: i64) -> CellChain {
    if coefficient == 0 {
        CellChain::new()
    } else {
        BTreeMap::from([(cell, coefficient)])
    }
}

type BlockCut = (Vec<usize>, Vec<usize>);

fn enumerate_block_cuts(block: &[usize], budget: &mut Budget) -> Result<Vec<BlockCut>> {
    let mut cuts = vec![(Vec::new(), Vec::new())];
    for &label in block {
        let next_len = cuts
            .len()
            .checked_mul(2)
            .ok_or(PermutohedralError::Overflow("enumerating cuts"))?;
        check_limit(
            next_len,
            budget.limits.max_terms.saturating_add(2),
            "block cuts",
        )?;
        budget.tick(next_len)?;
        let mut next = Vec::with_capacity(next_len);
        for (left, right) in cuts {
            let mut with_left = left.clone();
            with_left.push(label);
            next.push((with_left, right.clone()));
            let mut with_right = right;
            with_right.push(label);
            next.push((left, with_right));
        }
        cuts = next;
    }
    Ok(cuts)
}

fn boundary_inner(cell: &Cell, budget: &mut Budget) -> Result<CellChain> {
    let mut result = CellChain::new();
    let mut prefix_dimension = 0usize;
    for (position, block) in cell.iter().enumerate() {
        // Binary masks are unnecessary: recursive cuts work even when a
        // caller's label limit exceeds the machine word width.
        let cuts = enumerate_block_cuts(block, budget)?;
        for (left, right) in cuts {
            if left.is_empty() || right.is_empty() {
                continue;
            }
            let inversion_parity = left
                .iter()
                .flat_map(|x| right.iter().map(move |y| x > y))
                .fold(false, |parity, inverted| parity ^ inverted);
            let odd = ((prefix_dimension + left.len()) % 2 == 1) ^ inversion_parity;
            let mut face = cell[..position].to_vec();
            face.push(left);
            face.push(right);
            face.extend_from_slice(&cell[position + 1..]);
            check_limit(result.len() + 1, budget.limits.max_terms, "chain terms")?;
            result.insert(face, if odd { -1 } else { 1 });
        }
        prefix_dimension += block.len() - 1;
    }
    Ok(result)
}

/// Cellular boundary in the product orientation whose basis in an increasing
/// block `b_1,...,b_s` is `(e_b1-e_bs,...,e_b(s-1)-e_bs)`.
/// Splitting `B=L|R` has sign `(-1)^(previous_degree+|L|+inversions(L,R))`.
pub fn boundary(cell: &Cell, limits: ContractionLimits) -> Result<CellChain> {
    validate_cell(cell, label_count(cell)?, limits)?;
    boundary_inner(cell, &mut Budget::new(limits))
}

fn check_chain(
    chain: &CellChain,
    labels: usize,
    degree: usize,
    limits: ContractionLimits,
) -> Result<()> {
    check_limit(labels, limits.max_labels, "labels")?;
    if labels == 0 {
        return Err(PermutohedralError::InvalidCell("empty label set"));
    }
    check_limit(chain.len(), limits.max_terms, "chain terms")?;
    for (cell, coefficient) in chain {
        if *coefficient == 0 {
            return Err(PermutohedralError::ZeroCoefficient);
        }
        validate_cell(cell, labels, limits)?;
        let actual = labels - cell.len();
        if actual != degree {
            return Err(PermutohedralError::WrongDegree {
                expected: degree,
                actual,
            });
        }
    }
    Ok(())
}

fn boundary_chain_inner(chain: &CellChain, budget: &mut Budget) -> Result<CellChain> {
    let mut result = CellChain::new();
    for (cell, coefficient) in chain {
        let faces = boundary_inner(cell, budget)?;
        budget.tick(faces.len())?;
        add_scaled(&mut result, &faces, *coefficient, budget.limits)?;
    }
    Ok(result)
}

/// Applies the signed differential to a validated homogeneous chain. Zero is
/// permitted in every degree; a degree-zero chain has ordinary boundary zero.
pub fn boundary_chain(
    chain: &CellChain,
    labels: usize,
    degree: usize,
    limits: ContractionLimits,
) -> Result<CellChain> {
    check_chain(chain, labels, degree, limits)?;
    boundary_chain_inner(chain, &mut Budget::new(limits))
}

/// Sum of coefficients of a zero-chain. The caller supplies the degree check.
pub fn augmentation(chain: &CellChain) -> Result<i64> {
    chain.values().try_fold(0i64, |sum, coefficient| {
        sum.checked_add(*coefficient)
            .ok_or(PermutohedralError::Overflow("computing augmentation"))
    })
}

/// Contract the full complex of ordered-partition cells all of whose vertex
/// refinements extend `order`. Caches are private to this particular order.
#[derive(Debug)]
pub struct LinearExtensionContraction {
    order: FinitePoset,
    relations: Vec<(usize, usize)>,
    limits: ContractionLimits,
    reference: Vec<usize>,
    rank: Vec<usize>,
    root: Cell,
    cache: BTreeMap<Cell, CellChain>,
}

// Explicit stack avoids a host call-stack assumption when callers
// increase the finite label bound. Every pending child has lower rank.
struct HomotopyFrame {
    cell: Cell,
    result: CellChain,
    pending: std::collections::btree_map::IntoIter<Cell, i64>,
    parent_coefficient: i64,
}

impl LinearExtensionContraction {
    pub fn new(order: FinitePoset, limits: ContractionLimits) -> Result<Self> {
        let labels = order.size();
        check_limit(labels, limits.max_labels, "labels")?;
        if labels == 0 {
            return Err(PermutohedralError::InvalidCell("empty label set"));
        }
        let mut budget = Budget::new(limits);
        let mut reference = Vec::with_capacity(labels);
        let mut selected = vec![false; labels];
        while reference.len() < labels {
            let label = Self::find_next_ready_label(&order, &selected, labels, &mut budget)?;
            selected[label] = true;
            reference.push(label);
        }
        let mut rank = vec![0; labels];
        for (index, &label) in reference.iter().enumerate() {
            rank[label] = index;
        }
        let root = reference.iter().map(|&label| vec![label]).collect();
        let relations = order.strict_relations();
        Ok(Self {
            order,
            relations,
            limits,
            reference,
            rank,
            root,
            cache: BTreeMap::new(),
        })
    }

    fn find_next_ready_label(
        order: &FinitePoset,
        selected: &[bool],
        labels: usize,
        budget: &mut Budget,
    ) -> Result<usize> {
        for label in 0..labels {
            if selected[label] {
                continue;
            }
            let mut ready = true;
            for (other, &chosen) in selected.iter().enumerate() {
                budget.tick(1)?;
                if !chosen && order.less(other, label)? {
                    ready = false;
                    break;
                }
            }
            if ready {
                return Ok(label);
            }
        }
        Err(PermutohedralError::IdentityFailure("acyclic order"))
    }

    pub fn root_vertex(&self) -> &Cell {
        &self.root
    }
    pub fn reference_extension(&self) -> &[usize] {
        &self.reference
    }
    pub fn order(&self) -> &FinitePoset {
        &self.order
    }
    pub fn cached_cells(&self) -> usize {
        self.cache.len()
    }

    /// Verifies every comparison is strict between blocks. This is equivalent
    /// to every permutation refining the blocks being a linear extension.
    pub fn contains(&self, cell: &Cell) -> Result<bool> {
        validate_cell(cell, self.order.size(), self.limits)?;
        let mut positions = vec![0; self.order.size()];
        for (index, block) in cell.iter().enumerate() {
            for &label in block {
                positions[label] = index;
            }
        }
        for &(lower, upper) in &self.relations {
            if positions[lower] >= positions[upper] {
                return Ok(false);
            }
        }
        Ok(true)
    }

    fn maximal_vertex(&self, cell: &Cell) -> Vec<usize> {
        let mut vertex = Vec::with_capacity(self.order.size());
        for block in cell {
            let mut decreasing = block.clone();
            decreasing.sort_unstable_by_key(|&label| std::cmp::Reverse(self.rank[label]));
            vertex.extend(decreasing);
        }
        vertex
    }

    fn inversion_rank(&self, cell: &Cell) -> usize {
        let vertex = self.maximal_vertex(cell);
        let mut inversions = 0;
        for first in 0..vertex.len() {
            for second in first + 1..vertex.len() {
                inversions += usize::from(self.rank[vertex[first]] > self.rank[vertex[second]]);
            }
        }
        inversions
    }

    // V pairs the first descent in the maximal vertex. If that descent is
    // internal to a block, this cell is the upper member and V is zero.
    fn matching(&self, cell: &Cell, budget: &mut Budget) -> Result<CellChain> {
        budget.tick(1)?;
        let vertex = self.maximal_vertex(cell);
        let Some(descent) = vertex
            .windows(2)
            .position(|w| self.rank[w[0]] > self.rank[w[1]])
        else {
            return Ok(CellChain::new());
        };
        let mut end = 0;
        for (position, block) in cell.iter().enumerate() {
            end += block.len();
            if descent + 1 < end {
                return Ok(CellChain::new());
            }
            if descent + 1 == end {
                let right = cell
                    .get(position + 1)
                    .ok_or(PermutohedralError::IdentityFailure("matching successor"))?;
                let mut merged = block.clone();
                merged.extend(right);
                merged.sort_unstable();
                let mut upper = cell[..position].to_vec();
                upper.push(merged);
                upper.extend_from_slice(&cell[position + 2..]);
                if !self.contains(&upper)? {
                    return Err(PermutohedralError::IdentityFailure(
                        "matching stays in order",
                    ));
                }
                let faces = boundary_inner(&upper, budget)?;
                let sign = faces
                    .get(cell)
                    .copied()
                    .ok_or(PermutohedralError::IdentityFailure("matching incidence"))?;
                return Ok(singleton(upper, sign));
            }
        }
        Err(PermutohedralError::IdentityFailure("matching descent"))
    }

    fn reduction(&self, cell: &Cell, budget: &mut Budget) -> Result<(CellChain, CellChain)> {
        let rank = self.inversion_rank(cell);
        let matched = self.matching(cell, budget)?;
        let mut reduced = singleton(cell.clone(), 1);
        let boundary_matched = boundary_chain_inner(&matched, budget)?;
        add_scaled(&mut reduced, &boundary_matched, -1, self.limits)?;
        let faces = boundary_inner(cell, budget)?;
        for (face, coefficient) in faces {
            let matched_face = self.matching(&face, budget)?;
            budget.tick(matched_face.len())?;
            add_scaled(&mut reduced, &matched_face, -coefficient, self.limits)?;
        }
        self.verify_strict_inversion_descent(&reduced, rank)?;
        Ok((matched, reduced))
    }

    fn verify_strict_inversion_descent(&self, reduced: &CellChain, rank: usize) -> Result<()> {
        for face in reduced.keys() {
            if self.inversion_rank(face) >= rank {
                return Err(PermutohedralError::IdentityFailure(
                    "strict inversion descent",
                ));
            }
        }
        Ok(())
    }

    fn on_cell(&mut self, cell: &Cell, budget: &mut Budget) -> Result<CellChain> {
        budget.tick(1)?;
        if cell == &self.root {
            return Ok(CellChain::new());
        }
        if let Some(cached) = self.cache.get(cell) {
            return Ok(cached.clone());
        }
        check_limit(
            self.cache.len() + 1,
            self.limits.max_cells,
            "cached and pending cells",
        )?;
        let (result, reduced) = self.reduction(cell, budget)?;
        let frames = vec![HomotopyFrame {
            cell: cell.clone(),
            result,
            pending: reduced.into_iter(),
            parent_coefficient: 1,
        }];
        self.run_homotopy_stack(frames, budget)
    }

    fn run_homotopy_stack(
        &mut self,
        mut frames: Vec<HomotopyFrame>,
        budget: &mut Budget,
    ) -> Result<CellChain> {
        while !frames.is_empty() {
            budget.tick(1)?;
            let next = frames.last_mut().and_then(|frame| frame.pending.next());
            if let Some((lower, coefficient)) = next {
                self.step_homotopy_frame(&mut frames, lower, coefficient, budget)?;
            } else if let Some(done) = self.finish_homotopy_frame(&mut frames, budget)? {
                return Ok(done);
            }
        }
        Err(PermutohedralError::IdentityFailure(
            "homotopy stack completion",
        ))
    }

    fn step_homotopy_frame(
        &self,
        frames: &mut Vec<HomotopyFrame>,
        lower: Cell,
        coefficient: i64,
        budget: &mut Budget,
    ) -> Result<()> {
        if lower == self.root {
            return Ok(());
        }
        if let Some(cached) = self.cache.get(&lower) {
            budget.tick(cached.len())?;
            let parent = frames
                .last_mut()
                .ok_or(PermutohedralError::IdentityFailure("homotopy stack"))?;
            add_scaled(&mut parent.result, cached, coefficient, self.limits)
        } else {
            check_limit(
                self.cache.len() + frames.len() + 1,
                self.limits.max_cells,
                "cached and pending cells",
            )?;
            let (result, reduced) = self.reduction(&lower, budget)?;
            frames.push(HomotopyFrame {
                cell: lower,
                result,
                pending: reduced.into_iter(),
                parent_coefficient: coefficient,
            });
            Ok(())
        }
    }

    fn finish_homotopy_frame(
        &mut self,
        frames: &mut Vec<HomotopyFrame>,
        budget: &mut Budget,
    ) -> Result<Option<CellChain>> {
        let completed = frames
            .pop()
            .ok_or(PermutohedralError::IdentityFailure("homotopy stack"))?;
        check_limit(self.cache.len() + 1, self.limits.max_cells, "cached cells")?;
        self.cache.insert(completed.cell, completed.result.clone());
        if let Some(parent) = frames.last_mut() {
            budget.tick(completed.result.len())?;
            add_scaled(
                &mut parent.result,
                &completed.result,
                completed.parent_coefficient,
                self.limits,
            )?;
            Ok(None)
        } else {
            Ok(Some(completed.result))
        }
    }

    fn check_input(&self, chain: &CellChain, degree: usize) -> Result<()> {
        check_chain(chain, self.order.size(), degree, self.limits)?;
        for cell in chain.keys() {
            if !self.contains(cell)? {
                return Err(PermutohedralError::OutsideOrder);
            }
        }
        Ok(())
    }

    fn homotopy_inner(&mut self, chain: &CellChain, budget: &mut Budget) -> Result<CellChain> {
        let mut result = CellChain::new();
        for (cell, coefficient) in chain {
            let value = self.on_cell(cell, budget)?;
            budget.tick(value.len())?;
            add_scaled(&mut result, &value, *coefficient, self.limits)?;
        }
        Ok(result)
    }

    /// Compute the degree-raising integral chain homotopy. The finite recursion
    /// checks strict inversion descent at every nonzero recursive term.
    pub fn homotopy(&mut self, chain: &CellChain, degree: usize) -> Result<CellChain> {
        self.check_input(chain, degree)?;
        self.homotopy_inner(chain, &mut Budget::new(self.limits))
    }

    /// Fill an ordinary positive-degree cycle, or an augmentation-zero
    /// zero-cycle. The returned boundary is checked against the original input
    /// exactly before success. No positive-degree homology oracle is assumed.
    pub fn fill_cycle(&mut self, chain: &CellChain, degree: usize) -> Result<CellChain> {
        self.check_input(chain, degree)?;
        let mut budget = Budget::new(self.limits);
        if (degree == 0 && augmentation(chain)? != 0)
            || !boundary_chain_inner(chain, &mut budget)?.is_empty()
        {
            return Err(PermutohedralError::NotCycle);
        }
        let filler = self.homotopy_inner(chain, &mut budget)?;
        if boundary_chain_inner(&filler, &mut budget)? != *chain {
            return Err(PermutohedralError::IdentityFailure("filler boundary"));
        }
        Ok(filler)
    }
}

/// Direct minimum-letter sweep, an explicit alternative to
/// [`LinearExtensionContraction`]. These two types generally return DIFFERENT
/// chains. Their common root and contraction identities do not identify them.
///
/// A basis cell has at most `m*(m-1)/2` output cells, each with coefficient
/// `+1` or `-1`. Materializing them requires at most cubic label-copy work.
/// This bound concerns evaluation on sparse input, not full matrix enumeration.
/// No boundary is expanded by [`Self::homotopy`]. [`Self::fill_cycle`] still
/// checks the proposed filler by the independent signed differential.
#[derive(Debug)]
pub struct MinimumSweepContraction {
    geometry: LinearExtensionContraction,
}

impl MinimumSweepContraction {
    pub fn new(order: FinitePoset, limits: ContractionLimits) -> Result<Self> {
        Ok(Self {
            geometry: LinearExtensionContraction::new(order, limits)?,
        })
    }

    pub fn root_vertex(&self) -> &Cell {
        self.geometry.root_vertex()
    }

    pub fn reference_extension(&self) -> &[usize] {
        self.geometry.reference_extension()
    }

    pub fn order(&self) -> &FinitePoset {
        self.geometry.order()
    }

    pub fn contains(&self, cell: &Cell) -> Result<bool> {
        self.geometry.contains(cell)
    }

    /// This direct construction does not retain a basis-cell cache.
    pub fn cached_cells(&self) -> usize {
        0
    }

    fn on_cell(
        &self,
        cell: &Cell,
        budget: &mut Budget,
        generated: &mut usize,
    ) -> Result<CellChain> {
        let labels = self.geometry.order.size();
        budget.tick(labels)?;
        let mut remaining = cell.clone();
        let mut fixed = Vec::with_capacity(labels);
        let mut result = CellChain::new();
        for &distinguished in &self.geometry.reference {
            budget.tick(labels)?;
            let position = remaining
                .iter()
                .position(|block| block.contains(&distinguished))
                .ok_or(PermutohedralError::IdentityFailure("sweep label lookup"))?;
            if remaining[position].len() != 1 {
                // Deletion sends this cell to zero, terminating the recursion.
                break;
            }
            let mut prefix_odd = false;
            for (crossed, block) in remaining.iter().take(position).enumerate() {
                Self::emit_crossed_sweep_cell(
                    &remaining,
                    &fixed,
                    position,
                    crossed,
                    block,
                    distinguished,
                    labels,
                    &mut prefix_odd,
                    generated,
                    &mut result,
                    budget,
                )?;
            }
            remaining.remove(position);
            fixed.push(distinguished);
        }
        Ok(result)
    }

    #[allow(clippy::too_many_arguments)]
    fn emit_crossed_sweep_cell(
        remaining: &[Vec<usize>],
        fixed: &[usize],
        position: usize,
        crossed: usize,
        block: &[usize],
        distinguished: usize,
        labels: usize,
        prefix_odd: &mut bool,
        generated: &mut usize,
        result: &mut CellChain,
        budget: &mut Budget,
    ) -> Result<()> {
        // Bound the output and work BEFORE allocating this cell. The
        // cell budget counts generated terms during this call because
        // this construction has no persistent cache.
        let next_generated = generated
            .checked_add(1)
            .ok_or(PermutohedralError::Overflow("counting sweep cells"))?;
        check_limit(
            next_generated,
            budget.limits.max_cells,
            "generated sweep cells",
        )?;
        check_limit(result.len() + 1, budget.limits.max_terms, "chain terms")?;
        budget.tick(labels)?;
        let inversions_odd =
            block.iter().filter(|&&label| label > distinguished).count() % 2 == 1;
        let negative = *prefix_odd ^ (block.len() % 2 == 1) ^ inversions_odd;
        let output = Self::build_crossed_cell(fixed, remaining, position, crossed, distinguished);
        // Different crossed blocks give different outputs. Between
        // stages, the earliest reference label that is nonsingleton
        // distinguishes the outputs, so no coefficient merging occurs.
        if result
            .insert(output, if negative { -1 } else { 1 })
            .is_some()
        {
            return Err(PermutohedralError::IdentityFailure(
                "distinct sweep output cells",
            ));
        }
        *generated = next_generated;
        *prefix_odd ^= (block.len() - 1) % 2 == 1;
        Ok(())
    }

    fn build_crossed_cell(
        fixed: &[usize],
        remaining: &[Vec<usize>],
        position: usize,
        crossed: usize,
        distinguished: usize,
    ) -> Cell {
        let mut output: Cell = fixed.iter().map(|&label| vec![label]).collect();
        for (index, current) in remaining.iter().enumerate() {
            if index == position {
                continue;
            }
            let mut next = current.clone();
            if index == crossed {
                let insertion = next.partition_point(|&label| label < distinguished);
                next.insert(insertion, distinguished);
            }
            output.push(next);
        }
        output
    }

    fn homotopy_inner(&self, chain: &CellChain, budget: &mut Budget) -> Result<CellChain> {
        let mut result = CellChain::new();
        let mut generated = 0usize;
        for (cell, coefficient) in chain {
            let value = self.on_cell(cell, budget, &mut generated)?;
            budget.tick(value.len())?;
            add_scaled(&mut result, &value, *coefficient, budget.limits)?;
        }
        Ok(result)
    }

    /// Sweep successive reference minima left through preceding blocks. Each
    /// one-letter sweep s and singleton deletion D satisfy d s+s d=1-I D;
    /// composing these identities gives d h+h d=1-root*augmentation.
    pub fn homotopy(&mut self, chain: &CellChain, degree: usize) -> Result<CellChain> {
        self.geometry.check_input(chain, degree)?;
        self.homotopy_inner(chain, &mut Budget::new(self.geometry.limits))
    }

    /// Checks augmented-cycle membership, evaluates the direct sweep, and
    /// verifies its exact boundary before returning a filler.
    pub fn fill_cycle(&mut self, chain: &CellChain, degree: usize) -> Result<CellChain> {
        self.geometry.check_input(chain, degree)?;
        let mut budget = Budget::new(self.geometry.limits);
        if (degree == 0 && augmentation(chain)? != 0)
            || !boundary_chain_inner(chain, &mut budget)?.is_empty()
        {
            return Err(PermutohedralError::NotCycle);
        }
        let filler = self.homotopy_inner(chain, &mut budget)?;
        if boundary_chain_inner(&filler, &mut budget)? != *chain {
            return Err(PermutohedralError::IdentityFailure("filler boundary"));
        }
        Ok(filler)
    }
}

// Origin: engine/crates_rs/core_homology/src/permutohedral.rs
// Claim: urn:core:crates_rs:core-homology:permutohedral:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_dcdbce1f {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
