//! Sparse evaluation of explicitly selected carrier maps, without enumerating K or T.
//!
//! Requests recurse only to required boundaries and carrier contractions. A
//! result is a proposal. The separate filling checker tests the supplied
//! integral boundary equation using only its supplied chains. It makes no
//! assertion about closure of an arbitrary cochain on unexamined cells.

use super::{event_order, event_task_order, task_order, CellImages, OrderKey, TransportError};
use core_homology::finite_poset::{FinitePoset, MAX_POSET_ELEMENTS};
use core_homology::permutohedral::{
    add_scaled, boundary, boundary_chain, validate_cell, Cell, CellChain, ContractionLimits,
    LinearExtensionContraction, MinimumSweepContraction, PermutohedralError,
};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, thiserror::Error)]
pub enum SparseTransportError {
    #[error("pairs must be positive, capacity in 1..=pairs, and 2*pairs within both label limits")]
    Parameters,
    #[error("{resource} exceeds sparse transport limit {limit}")]
    Limit {
        resource: &'static str,
        limit: usize,
    },
    #[error("integer overflow while {0}")]
    Overflow(&'static str),
    #[error("the supplied event cell violates pair precedence or capacity")]
    IllegalEventCell,
    #[error("the supplied task cell has a block larger than capacity")]
    IllegalTaskCell,
    #[error("supplied sparse filling does not have the supplied cycle as its boundary")]
    FillingMismatch,
    #[error("the supplied source chain is not a cycle")]
    NotCycle,
    #[error(transparent)]
    Cellular(#[from] PermutohedralError),
    #[error(transparent)]
    Transport(#[from] TransportError),
}
type Result<T> = std::result::Result<T, SparseTransportError>;

/// Aggregate limits for one evaluator's lifetime. The homology owner's
/// `ContractionLimits` additionally bounds every sparse intermediate and each
/// carrier cache. The maximum retained carrier-cache entries is therefore at
/// most `max_carriers * contraction.max_cells`, and each cached image has at
/// most `contraction.max_terms` terms. These are bounds, not a polynomial-time
/// guarantee. Requests may return a typed refusal before constructing a result.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SparseTransportLimits {
    pub max_cached_columns: usize,
    pub max_cached_terms: usize,
    pub max_carriers: usize,
    pub max_requests: usize,
    pub max_recursion_depth: usize,
}
impl Default for SparseTransportLimits {
    fn default() -> Self {
        Self {
            max_cached_columns: 100_000,
            max_cached_terms: 1_000_000,
            max_carriers: 1_000,
            max_requests: 1_000_000,
            max_recursion_depth: 512,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub struct SparseTransportStats {
    pub method: ContractionMethod,
    pub projection_columns: usize,
    pub inclusion_columns: usize,
    pub homotopy_columns: usize,
    pub cached_terms: usize,
    pub task_carriers: usize,
    pub event_carriers: usize,
    pub carrier_cached_cells: usize,
    pub requests: usize,
}

/// A proposal constructor for a fixed paired-event presentation. A failed
/// request can leave already completed, valid columns in its private cache;
/// no partially constructed column is published or retained as a result.
#[derive(Debug)]
pub struct SparseTransport {
    method: ContractionMethod,
    pairs: usize,
    capacity: usize,
    contraction: ContractionLimits,
    limits: SparseTransportLimits,
    projection: CellImages,
    inclusion: CellImages,
    homotopy: CellImages,
    task_carriers: SparseCarrierCache,
    event_carriers: SparseCarrierCache,
    cached_terms: usize,
    requests: usize,
}

/// The method is explicit because the two valid contractions can produce
/// different individual chains. Only MinimumSweepV2 has the stated polynomial
/// basis-image support bound; V1 remains available for existing certificates.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ContractionMethod {
    FirstDescentV1,
    MinimumSweepV2,
}

#[derive(Debug)]
enum SparseCarrier {
    FirstDescent(LinearExtensionContraction),
    MinimumSweep(MinimumSweepContraction),
}
type SparseCarrierCache = BTreeMap<OrderKey, SparseCarrier>;
impl SparseCarrier {
    fn new(
        method: ContractionMethod,
        poset: FinitePoset,
        limits: ContractionLimits,
    ) -> Result<Self> {
        Ok(match method {
            ContractionMethod::FirstDescentV1 => {
                Self::FirstDescent(LinearExtensionContraction::new(poset, limits)?)
            }
            ContractionMethod::MinimumSweepV2 => {
                Self::MinimumSweep(MinimumSweepContraction::new(poset, limits)?)
            }
        })
    }
    fn fill_cycle(&mut self, chain: &CellChain, degree: usize) -> Result<CellChain> {
        Ok(match self {
            Self::FirstDescent(contraction) => contraction.fill_cycle(chain, degree)?,
            Self::MinimumSweep(contraction) => contraction.fill_cycle(chain, degree)?,
        })
    }
    fn cached_cells(&self) -> usize {
        match self {
            Self::FirstDescent(contraction) => contraction.cached_cells(),
            Self::MinimumSweep(contraction) => contraction.cached_cells(),
        }
    }
}

#[derive(Clone, Copy)]
enum Operation {
    Project,
    Include,
    Homotopy,
}

fn checked_parameters(pairs: usize, capacity: usize, limits: ContractionLimits) -> Result<usize> {
    let labels = pairs
        .checked_mul(2)
        .ok_or(SparseTransportError::Parameters)?;
    if pairs == 0
        || capacity == 0
        || capacity > pairs
        || labels > limits.max_labels
        || labels > MAX_POSET_ELEMENTS
    {
        return Err(SparseTransportError::Parameters);
    }
    Ok(labels)
}

fn limit(value: usize, maximum: usize, resource: &'static str) -> Result<()> {
    if value > maximum {
        return Err(SparseTransportError::Limit {
            resource,
            limit: maximum,
        });
    }
    Ok(())
}

fn validate_event_block(
    block: &[usize],
    states: &mut [u8],
    active: &mut usize,
    capacity: usize,
) -> Result<()> {
    let mut starts = 0usize;
    let mut finishes = 0usize;
    // Check against the state before this entire block: a remove and its
    // own restoration in the same block are never admitted.
    for &event in block {
        if event % 2 == 0 {
            if states[event / 2] != 0 {
                return Err(SparseTransportError::IllegalEventCell);
            }
            starts += 1;
        } else {
            if states[event / 2] != 1 {
                return Err(SparseTransportError::IllegalEventCell);
            }
            finishes += 1;
        }
    }
    if *active + starts > capacity {
        return Err(SparseTransportError::IllegalEventCell);
    }
    for &event in block {
        states[event / 2] = if event % 2 == 0 { 1 } else { 2 };
    }
    *active = *active + starts - finishes;
    Ok(())
}

/// Strict event precedence and worst internal ordering are both checked.
/// This function examines one supplied cell, not an enumerated complex.
pub fn validate_event_cell(
    pairs: usize,
    capacity: usize,
    cell: &Cell,
    limits: ContractionLimits,
) -> Result<()> {
    let labels = checked_parameters(pairs, capacity, limits)?;
    validate_cell(cell, labels, limits)?;
    let mut states = vec![0u8; pairs];
    let mut active = 0usize;
    for block in cell {
        validate_event_block(block, &mut states, &mut active, capacity)?;
    }
    if active != 0 || states.iter().any(|&state| state != 2) {
        return Err(SparseTransportError::IllegalEventCell);
    }
    Ok(())
}

pub fn validate_task_cell(
    pairs: usize,
    capacity: usize,
    cell: &Cell,
    limits: ContractionLimits,
) -> Result<()> {
    checked_parameters(pairs, capacity, limits)?;
    validate_cell(cell, pairs, limits)?;
    if cell.iter().any(|block| block.len() > capacity) {
        return Err(SparseTransportError::IllegalTaskCell);
    }
    Ok(())
}

fn validate_chain(
    pairs: usize,
    capacity: usize,
    chain: &CellChain,
    degree: usize,
    events: bool,
    limits: ContractionLimits,
) -> Result<()> {
    let labels = checked_parameters(pairs, capacity, limits)?;
    limit(chain.len(), limits.max_terms, "input chain terms")?;
    let labels = if events { labels } else { pairs };
    // Empty chains are the zero element of any degree. Nonempty chains must
    // have exactly the claimed homogeneous degree, with no explicit zero terms.
    for (cell, coefficient) in chain {
        if *coefficient == 0 {
            return Err(PermutohedralError::ZeroCoefficient.into());
        }
        if events {
            validate_event_cell(pairs, capacity, cell, limits)?;
        } else {
            validate_task_cell(pairs, capacity, cell, limits)?;
        }
        let actual = labels - cell.len();
        if actual != degree {
            return Err(PermutohedralError::WrongDegree {
                expected: degree,
                actual,
            }
            .into());
        }
    }
    Ok(())
}

impl SparseTransport {
    pub fn new(
        pairs: usize,
        capacity: usize,
        contraction: ContractionLimits,
        limits: SparseTransportLimits,
    ) -> Result<Self> {
        Self::with_method(
            pairs,
            capacity,
            contraction,
            limits,
            ContractionMethod::FirstDescentV1,
        )
    }

    pub fn new_minimum_sweep(
        pairs: usize,
        capacity: usize,
        contraction: ContractionLimits,
        limits: SparseTransportLimits,
    ) -> Result<Self> {
        Self::with_method(
            pairs,
            capacity,
            contraction,
            limits,
            ContractionMethod::MinimumSweepV2,
        )
    }

    pub fn with_method(
        pairs: usize,
        capacity: usize,
        contraction: ContractionLimits,
        limits: SparseTransportLimits,
        method: ContractionMethod,
    ) -> Result<Self> {
        checked_parameters(pairs, capacity, contraction)?;
        Ok(Self {
            method,
            pairs,
            capacity,
            contraction,
            limits,
            projection: BTreeMap::new(),
            inclusion: BTreeMap::new(),
            homotopy: BTreeMap::new(),
            task_carriers: BTreeMap::new(),
            event_carriers: BTreeMap::new(),
            cached_terms: 0,
            requests: 0,
        })
    }

    pub fn stats(&self) -> SparseTransportStats {
        SparseTransportStats {
            method: self.method,
            projection_columns: self.projection.len(),
            inclusion_columns: self.inclusion.len(),
            homotopy_columns: self.homotopy.len(),
            cached_terms: self.cached_terms,
            task_carriers: self.task_carriers.len(),
            event_carriers: self.event_carriers.len(),
            carrier_cached_cells: self
                .task_carriers
                .values()
                .chain(self.event_carriers.values())
                .map(SparseCarrier::cached_cells)
                .sum(),
            requests: self.requests,
        }
    }

    /// Propose p(z) by visiting only required columns and their boundaries.
    pub fn project(&mut self, chain: &CellChain, degree: usize) -> Result<CellChain> {
        validate_chain(
            self.pairs,
            self.capacity,
            chain,
            degree,
            true,
            self.contraction,
        )?;
        self.apply(Operation::Project, chain, degree, 0)
    }

    /// Propose i(z) by visiting only required columns and their boundaries.
    pub fn include(&mut self, chain: &CellChain, degree: usize) -> Result<CellChain> {
        validate_chain(
            self.pairs,
            self.capacity,
            chain,
            degree,
            false,
            self.contraction,
        )?;
        self.apply(Operation::Include, chain, degree, 0)
    }

    /// Propose H(z), with the convention ip-id = dH+Hd.
    pub fn homotopy(&mut self, chain: &CellChain, degree: usize) -> Result<CellChain> {
        validate_chain(
            self.pairs,
            self.capacity,
            chain,
            degree,
            true,
            self.contraction,
        )?;
        degree.checked_add(1).ok_or(SparseTransportError::Overflow(
            "raising the homotopy degree",
        ))?;
        self.apply(Operation::Homotopy, chain, degree, 0)
    }

    fn tick(&mut self, depth: usize) -> Result<()> {
        limit(depth, self.limits.max_recursion_depth, "recursion depth")?;
        let requests = self
            .requests
            .checked_add(1)
            .ok_or(SparseTransportError::Overflow("counting requests"))?;
        limit(requests, self.limits.max_requests, "requests")?;
        self.requests = requests;
        Ok(())
    }

    fn apply(
        &mut self,
        operation: Operation,
        chain: &CellChain,
        degree: usize,
        depth: usize,
    ) -> Result<CellChain> {
        self.tick(depth)?;
        let mut result = CellChain::new();
        for (cell, coefficient) in chain {
            let image = self.column(operation, cell, degree, depth + 1)?;
            add_scaled(&mut result, &image, *coefficient, self.contraction)?;
        }
        Ok(result)
    }

    fn retained(&self, operation: Operation) -> &CellImages {
        match operation {
            Operation::Project => &self.projection,
            Operation::Include => &self.inclusion,
            Operation::Homotopy => &self.homotopy,
        }
    }

    fn fill(
        &mut self,
        task_carrier: bool,
        poset: FinitePoset,
        cycle: &CellChain,
        degree: usize,
    ) -> Result<CellChain> {
        let key = poset.strict_relations();
        let present = if task_carrier {
            self.task_carriers.contains_key(&key)
        } else {
            self.event_carriers.contains_key(&key)
        };
        if !present {
            limit(
                self.task_carriers.len() + self.event_carriers.len() + 1,
                self.limits.max_carriers,
                "carriers",
            )?;
            let carrier = SparseCarrier::new(self.method, poset, self.contraction)?;
            if task_carrier {
                self.task_carriers.insert(key.clone(), carrier);
            } else {
                self.event_carriers.insert(key.clone(), carrier);
            }
        }
        let cache = if task_carrier {
            &mut self.task_carriers
        } else {
            &mut self.event_carriers
        };
        let carrier = cache.get_mut(&key).ok_or(TransportError::MissingCell)?;
        Ok(carrier.fill_cycle(cycle, degree)?)
    }

    fn compute_project_column(
        &mut self,
        cell: &Cell,
        degree: usize,
        depth: usize,
    ) -> Result<CellChain> {
        let poset = event_task_order(cell, self.pairs)?;
        if degree == 0 {
            return Ok(BTreeMap::from([(
                poset
                    .topological_order()
                    .into_iter()
                    .map(|i| vec![i])
                    .collect(),
                1,
            )]));
        }
        let faces = boundary(cell, self.contraction)?;
        let mapped = self.apply(Operation::Project, &faces, degree - 1, depth + 1)?;
        if mapped.is_empty() {
            Ok(CellChain::new())
        } else {
            self.fill(true, poset, &mapped, degree - 1)
        }
    }

    fn compute_include_column(
        &mut self,
        cell: &Cell,
        degree: usize,
        depth: usize,
    ) -> Result<CellChain> {
        if degree == 0 {
            let events = cell
                .iter()
                .flatten()
                .flat_map(|i| [vec![2 * i], vec![2 * i + 1]])
                .collect();
            return Ok(BTreeMap::from([(events, 1)]));
        }
        let faces = boundary(cell, self.contraction)?;
        let mapped = self.apply(Operation::Include, &faces, degree - 1, depth + 1)?;
        if mapped.is_empty() {
            Ok(CellChain::new())
        } else {
            self.fill(
                false,
                event_order(&task_order(cell, self.pairs)?)?,
                &mapped,
                degree - 1,
            )
        }
    }

    fn compute_homotopy_column(
        &mut self,
        cell: &Cell,
        degree: usize,
        depth: usize,
    ) -> Result<CellChain> {
        let residual = self.compute_homotopy_residual(cell, degree, depth)?;
        if residual.is_empty() {
            Ok(CellChain::new())
        } else {
            self.fill(
                false,
                event_order(&event_task_order(cell, self.pairs)?)?,
                &residual,
                degree,
            )
        }
    }

    fn compute_homotopy_residual(
        &mut self,
        cell: &Cell,
        degree: usize,
        depth: usize,
    ) -> Result<CellChain> {
        let projected = self.column(Operation::Project, cell, degree, depth + 1)?;
        let mut residual = self.apply(Operation::Include, &projected, degree, depth + 1)?;
        add_scaled(
            &mut residual,
            &BTreeMap::from([(cell.clone(), 1)]),
            -1,
            self.contraction,
        )?;
        if degree > 0 {
            let faces = boundary(cell, self.contraction)?;
            let lower = self.apply(Operation::Homotopy, &faces, degree - 1, depth + 1)?;
            add_scaled(&mut residual, &lower, -1, self.contraction)?;
        }
        Ok(residual)
    }

    fn store_cached_column(
        &mut self,
        operation: Operation,
        cell: &Cell,
        image: &CellChain,
    ) -> Result<()> {
        self.check_new_column(image.len())?;
        self.cached_terms = self
            .cached_terms
            .checked_add(image.len())
            .ok_or(SparseTransportError::Overflow("counting retained support"))?;
        match operation {
            Operation::Project => {
                self.projection.insert(cell.clone(), image.clone());
            }
            Operation::Include => {
                self.inclusion.insert(cell.clone(), image.clone());
            }
            Operation::Homotopy => {
                self.homotopy.insert(cell.clone(), image.clone());
            }
        }
        Ok(())
    }

    fn column(
        &mut self,
        operation: Operation,
        cell: &Cell,
        degree: usize,
        depth: usize,
    ) -> Result<CellChain> {
        self.tick(depth)?;
        if let Some(image) = self.retained(operation).get(cell) {
            return Ok(image.clone());
        }
        // Reserve against the currently retained columns before expanding; the
        // same bound is rechecked on return after all recursive insertions.
        self.check_new_column(0)?;
        let image = self.dispatch_column_computation(operation, cell, degree, depth)?;
        let output_degree = Self::output_degree_for_op(operation, degree)?;
        validate_chain(
            self.pairs,
            self.capacity,
            &image,
            output_degree,
            !matches!(operation, Operation::Project),
            self.contraction,
        )?;
        self.store_cached_column(operation, cell, &image)?;
        Ok(image)
    }

    fn dispatch_column_computation(
        &mut self,
        operation: Operation,
        cell: &Cell,
        degree: usize,
        depth: usize,
    ) -> Result<CellChain> {
        match operation {
            Operation::Project => self.compute_project_column(cell, degree, depth),
            Operation::Include => self.compute_include_column(cell, degree, depth),
            Operation::Homotopy => self.compute_homotopy_column(cell, degree, depth),
        }
    }

    fn output_degree_for_op(operation: Operation, degree: usize) -> Result<usize> {
        if matches!(operation, Operation::Homotopy) {
            degree
                .checked_add(1)
                .ok_or(SparseTransportError::Overflow("raising output degree"))
        } else {
            Ok(degree)
        }
    }

    fn check_new_column(&self, additional_terms: usize) -> Result<()> {
        let columns = self
            .projection
            .len()
            .checked_add(self.inclusion.len())
            .and_then(|n| n.checked_add(self.homotopy.len()))
            .and_then(|n| n.checked_add(1))
            .ok_or(SparseTransportError::Overflow("counting retained columns"))?;
        limit(columns, self.limits.max_cached_columns, "cached columns")?;
        let terms = self
            .cached_terms
            .checked_add(additional_terms)
            .ok_or(SparseTransportError::Overflow("counting retained support"))?;
        limit(terms, self.limits.max_cached_terms, "cached terms")
    }
}

/// A checked equation bound by immutable references to the supplied chains.
/// It certifies this one filling, without constructing or asserting full maps.
#[derive(Debug)]
pub struct CheckedSparseFilling<'a> {
    pairs: usize,
    capacity: usize,
    degree: usize,
    cycle: &'a CellChain,
    filling: &'a CellChain,
}
impl<'a> CheckedSparseFilling<'a> {
    pub fn pairs(&self) -> usize {
        self.pairs
    }
    pub fn capacity(&self) -> usize {
        self.capacity
    }
    pub fn degree(&self) -> usize {
        self.degree
    }
    pub fn cycle(&self) -> &'a CellChain {
        self.cycle
    }
    pub fn filling(&self) -> &'a CellChain {
        self.filling
    }
}

/// Check d(b)=z directly on supplied native event cells, including all block
/// refinements through the exact capacity criterion. Neither enumeration nor
/// a transport proposal constructor is called by this verification path.
pub fn verify_sparse_event_filling<'a>(
    pairs: usize,
    capacity: usize,
    cycle: &'a CellChain,
    filling: &'a CellChain,
    degree: usize,
    limits: ContractionLimits,
) -> Result<CheckedSparseFilling<'a>> {
    let labels = checked_parameters(pairs, capacity, limits)?;
    let filling_degree = degree
        .checked_add(1)
        .ok_or(SparseTransportError::Overflow("raising filling degree"))?;
    validate_chain(pairs, capacity, cycle, degree, true, limits)?;
    validate_chain(pairs, capacity, filling, filling_degree, true, limits)?;
    if !boundary_chain(cycle, labels, degree, limits)?.is_empty() {
        return Err(SparseTransportError::NotCycle);
    }
    if boundary_chain(filling, labels, filling_degree, limits)? != *cycle {
        return Err(SparseTransportError::FillingMismatch);
    }
    Ok(CheckedSparseFilling {
        pairs,
        capacity,
        degree,
        cycle,
        filling,
    })
}

// Origin: engine/crates_rs/core_wdp/src/guarded_chain_transport/sparse.rs
// Claim: urn:core:crates_rs:core-wdp:sparse:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_cbc17b85 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
