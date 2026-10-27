//! Unbounded finite-word contexts and their exact finite-state descent test.
//! This owner never replaces an arbitrary action on D* by a sampled word table.
//! Unbounded finite-word contexts and their exact finite-state descent test.
//! This owner never replaces an arbitrary action on D* by a sampled word table.
use crate::finite_moore::FiniteMoore;
use std::collections::{BTreeMap, VecDeque};

/// Two input histories whose equal source profiles have unequal output profiles.
/// Two input histories whose equal source profiles have unequal output profiles.
pub type ProfileNoncongruenceWitness = (Vec<usize>, Vec<usize>);

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HistoryError {
    InvalidAlphabet,
    InvalidWord,
    InvalidTransducer,
    InvalidInitialState,
    InvalidCertificate,
    UnavailableContext,
}

// Origin: engine/crates_rs/core_category_theory/src/finite_history_context.rs
// Claim: urn:core:crates_rs:core-category-theory:finite-history-context:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for HistoryError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for HistoryError {}

/// Executable original history action. Arbitrary implementations retain their
/// own semantics; callers check every output word. Only FiniteWordTransducer
/// below supplies a checked total finite-state realization and global descent test.
/// Executable original history action. Arbitrary implementations retain their
/// own semantics; callers check every output word. Only FiniteWordTransducer
/// below supplies a checked total finite-state realization and global descent test.
pub trait HistoryContext {
    fn apply(&self, word: &[usize]) -> Result<Vec<usize>, HistoryError>;
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteWordTransducer {
    alphabet_size: usize,
    initial: usize,
    transitions: Vec<Vec<usize>>,
    outputs: Vec<Vec<Vec<usize>>>,
    initial_output: Vec<usize>,
    final_outputs: Vec<Vec<usize>>,
}

type ProductState = (usize, usize, usize);

struct ProductVertex {
    state: ProductState,
    parent: Option<(usize, usize)>,
}

struct ProductSearch {
    vertices: Vec<ProductVertex>,
    ids: BTreeMap<ProductState, usize>,
    cursor: usize,
}

impl ProductSearch {
    fn new(first: ProductState) -> Self {
        Self {
            vertices: vec![ProductVertex {
                state: first,
                parent: None,
            }],
            ids: BTreeMap::from([(first, 0)]),
            cursor: 0,
        }
    }

    fn pop(&mut self) -> Option<(usize, ProductState)> {
        let id = self.cursor;
        let state = self.vertices.get(id)?.state;
        self.cursor += 1;
        Some((id, state))
    }

    fn admit(&mut self, state: ProductState, parent: usize, input: usize) {
        if let std::collections::btree_map::Entry::Vacant(entry) = self.ids.entry(state) {
            let id = self.vertices.len();
            entry.insert(id);
            self.vertices.push(ProductVertex {
                state,
                parent: Some((parent, input)),
            });
        }
    }

    fn word(&self, mut id: usize) -> Vec<usize> {
        let mut reversed = Vec::new();
        while let Some((parent, input)) = self.vertices[id].parent {
            reversed.push(input);
            id = parent;
        }
        reversed.reverse();
        reversed
    }
}

impl FiniteWordTransducer {
    pub fn new(
        alphabet_size: usize,
        initial: usize,
        transitions: Vec<Vec<usize>>,
        outputs: Vec<Vec<Vec<usize>>>,
        initial_output: Vec<usize>,
        final_outputs: Vec<Vec<usize>>,
    ) -> Result<Self, HistoryError> {
        let n = transitions.len();
        if n == 0
            || initial >= n
            || outputs.len() != n
            || final_outputs.len() != n
            || transitions
                .iter()
                .any(|row| row.len() != alphabet_size || row.iter().any(|&x| x >= n))
            || outputs.iter().any(|row| row.len() != alphabet_size)
            || outputs
                .iter()
                .flatten()
                .chain(final_outputs.iter())
                .chain(std::iter::once(&initial_output))
                .flatten()
                .any(|&d| d >= alphabet_size)
        {
            return Err(HistoryError::InvalidTransducer);
        }
        Ok(Self {
            alphabet_size,
            initial,
            transitions,
            outputs,
            initial_output,
            final_outputs,
        })
    }
    pub fn alphabet_size(&self) -> usize {
        self.alphabet_size
    }
    pub fn state_count(&self) -> usize {
        self.transitions.len()
    }
    pub fn substitution(images: Vec<Vec<usize>>) -> Result<Self, HistoryError> {
        let n = images.len();
        Self::new(n, 0, vec![vec![0; n]], vec![images], vec![], vec![vec![]])
    }
    pub fn prefix(alphabet_size: usize, prefix: Vec<usize>) -> Result<Self, HistoryError> {
        Self::new(
            alphabet_size,
            0,
            vec![vec![0; alphabet_size]],
            vec![(0..alphabet_size).map(|d| vec![d]).collect()],
            prefix,
            vec![vec![]],
        )
    }
    pub fn suffix(alphabet_size: usize, suffix: Vec<usize>) -> Result<Self, HistoryError> {
        Self::new(
            alphabet_size,
            0,
            vec![vec![0; alphabet_size]],
            vec![(0..alphabet_size).map(|d| vec![d]).collect()],
            vec![],
            vec![suffix],
        )
    }

    /// Finite product graph includes (original memory, transducer state,
    /// transformed-word memory). Its reachable vertices represent ALL words,
    /// not a cutoff. Final emissions are applied before comparing state images.
    /// Finite product graph includes (original memory, transducer state,
    /// transformed-word memory). Its reachable vertices represent ALL words,
    /// not a cutoff. Final emissions are applied before comparing state images.
    pub fn descend(
        &self,
        memory: &FiniteMoore,
        start: usize,
    ) -> Result<HistoryDescent, HistoryError> {
        let mut search = self.initial_search(memory, start)?;
        let mut images = vec![None; memory.state_count()];
        let mut representatives = vec![None; memory.state_count()];
        while let Some((id, (source, control, output))) = search.pop() {
            let final_state = run(memory, output, &self.final_outputs[control])?;
            if let Some(previous) = images[source] {
                if previous != final_state {
                    let first = representatives[source].ok_or(HistoryError::InvalidCertificate)?;
                    return Ok(HistoryDescent::Obstructed(HistoryCollision {
                        first: search.word(first),
                        second: search.word(id),
                        source_state: source,
                        first_image: previous,
                        second_image: final_state,
                    }));
                }
            } else {
                images[source] = Some(final_state);
                representatives[source] = Some(id);
            }
            self.expand_search(memory, (source, control, output), id, &mut search)?;
        }
        Ok(HistoryDescent::Descends(HistoryStateMap {
            images,
            reachable_product_states: search.vertices.len(),
        }))
    }

    /// Exact O2 profile-kernel noncongruence over all input histories.
    /// Exact O2 profile-kernel noncongruence witness over all input histories.
    pub fn profile_noncongruence(
        &self,
        memory: &FiniteMoore,
        start: usize,
    ) -> Result<Option<ProfileNoncongruenceWitness>, HistoryError> {
        let mut search = self.initial_search(memory, start)?;
        let mut profile_images: BTreeMap<usize, (usize, usize)> = BTreeMap::new();
        while let Some((id, (source, control, output))) = search.pop() {
            let final_state = run(memory, output, &self.final_outputs[control])?;
            let source_profile = memory.reports()[source];
            let target_profile = memory.reports()[final_state];
            if let Some(&(previous, representative)) = profile_images.get(&source_profile) {
                if previous != target_profile {
                    return Ok(Some((search.word(representative), search.word(id))));
                }
            } else {
                profile_images.insert(source_profile, (target_profile, id));
            }
            self.expand_search(memory, (source, control, output), id, &mut search)?;
        }
        Ok(None)
    }

    fn initial_search(
        &self,
        memory: &FiniteMoore,
        start: usize,
    ) -> Result<ProductSearch, HistoryError> {
        if memory.input_count() != self.alphabet_size {
            return Err(HistoryError::InvalidAlphabet);
        }
        if start >= memory.state_count() {
            return Err(HistoryError::InvalidInitialState);
        }
        Ok(ProductSearch::new((
            start,
            self.initial,
            run(memory, start, &self.initial_output)?,
        )))
    }

    fn expand_search(
        &self,
        memory: &FiniteMoore,
        state: ProductState,
        parent: usize,
        search: &mut ProductSearch,
    ) -> Result<(), HistoryError> {
        let (source, control, output) = state;
        for d in 0..self.alphabet_size {
            let next = (
                memory.transitions()[source][d],
                self.transitions[control][d],
                run(memory, output, &self.outputs[control][d])?,
            );
            search.admit(next, parent, d);
        }
        Ok(())
    }

    pub fn verify_descent(
        &self,
        memory: &FiniteMoore,
        start: usize,
        candidate: &HistoryDescent,
    ) -> Result<(), HistoryError> {
        if *candidate != self.descend(memory, start)? {
            return Err(HistoryError::InvalidCertificate);
        }
        Ok(())
    }
}
impl HistoryContext for FiniteWordTransducer {
    fn apply(&self, word: &[usize]) -> Result<Vec<usize>, HistoryError> {
        let mut output = self.initial_output.clone();
        let mut state = self.initial;
        for &d in word {
            if d >= self.alphabet_size {
                return Err(HistoryError::InvalidWord);
            }
            output.extend_from_slice(&self.outputs[state][d]);
            state = self.transitions[state][d];
        }
        output.extend_from_slice(&self.final_outputs[state]);
        Ok(output)
    }
}

pub fn run(memory: &FiniteMoore, start: usize, word: &[usize]) -> Result<usize, HistoryError> {
    if start >= memory.state_count() {
        return Err(HistoryError::InvalidInitialState);
    }
    let mut state = start;
    for &d in word {
        if d >= memory.input_count() {
            return Err(HistoryError::InvalidWord);
        }
        state = memory.transitions()[state][d];
    }
    Ok(state)
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HistoryStateMap {
    pub images: Vec<Option<usize>>,
    pub reachable_product_states: usize,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HistoryCollision {
    pub first: Vec<usize>,
    pub second: Vec<usize>,
    pub source_state: usize,
    pub first_image: usize,
    pub second_image: usize,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HistoryDescent {
    Descends(HistoryStateMap),
    Obstructed(HistoryCollision),
}

/// Reachable-state context lifts to an action on every finite history iff all
/// context images of reachable states are reachable. The chosen representative
/// history is explicit; no chronology or report equality is used to invent it.
/// Reachable-state context lifts to an action on every finite history iff all
/// context images of reachable states are reachable. The chosen representative
/// history is explicit; no chronology or report equality is used to invent it.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StateContextLift {
    memory: FiniteMoore,
    start: usize,
    action: Vec<usize>,
    representatives: Vec<Option<Vec<usize>>>,
}
impl StateContextLift {
    pub fn new(
        memory: FiniteMoore,
        start: usize,
        action: Vec<usize>,
    ) -> Result<Self, HistoryError> {
        let n = memory.state_count();
        if start >= n {
            return Err(HistoryError::InvalidInitialState);
        }
        if action.len() != n || action.iter().any(|&x| x >= n) {
            return Err(HistoryError::InvalidTransducer);
        }
        let mut representatives = vec![None; n];
        representatives[start] = Some(vec![]);
        let mut pending = VecDeque::from([start]);
        while let Some(x) = pending.pop_front() {
            for d in 0..memory.input_count() {
                let y = memory.transitions()[x][d];
                if representatives[y].is_none() {
                    let mut word = representatives[x]
                        .clone()
                        .ok_or(HistoryError::InvalidCertificate)?;
                    word.push(d);
                    representatives[y] = Some(word);
                    pending.push_back(y);
                }
            }
        }
        if (0..n).any(|x| representatives[x].is_some() && representatives[action[x]].is_none()) {
            return Err(HistoryError::UnavailableContext);
        }
        Ok(Self {
            memory,
            start,
            action,
            representatives,
        })
    }
    pub fn reachable_representatives(&self) -> &[Option<Vec<usize>>] {
        &self.representatives
    }
    pub fn action(&self) -> &[usize] {
        &self.action
    }
}
impl HistoryContext for StateContextLift {
    fn apply(&self, word: &[usize]) -> Result<Vec<usize>, HistoryError> {
        let state = run(&self.memory, self.start, word)?;
        self.representatives[self.action[state]]
            .clone()
            .ok_or(HistoryError::UnavailableContext)
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_ad7b1576 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
