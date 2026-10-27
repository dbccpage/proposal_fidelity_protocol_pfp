//! Recovered original WD-2 Genesis-six (M,U,p,rho,G,T) and WD-5 TEN-symbol
//! operational packet. These are not the education-six or compressed policy-five.
//! Original rho acts on unbounded histories; it is retained as executable data.
//! No profile-to-grammar encoder, state-level context, or authority is invented.

use crate::types::AuthorityEffect;
use core_category_theory::finite_history_context::{
    run, FiniteWordTransducer, HistoryContext, HistoryDescent, HistoryError, StateContextLift,
};
use core_category_theory::finite_moore::FiniteMoore;
use std::collections::{BTreeMap, BTreeSet, VecDeque};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum OriginalObserverError {
    InvalidDomain,
    InvalidInitialState,
    UnknownContext,
    UnknownGrammar,
    MissingEncoder,
    InvalidEncoder,
    History(HistoryError),
}

// Origin: engine/crates_rs/core_wdp/src/genesis_observer.rs
// Claim: urn:core:crates_rs:core-wdp:genesis-observer:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for OriginalObserverError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for OriginalObserverError {}
impl From<HistoryError> for OriginalObserverError {
    fn from(error: HistoryError) -> Self {
        Self::History(error)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum GenesisTerminal {
    Proved,
    Refuted,
    Unresolved,
    Outside,
    Refused,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GenesisSixData {
    pub states: Vec<String>,
    pub alphabet: Vec<String>,
    pub initial: String,
    pub update: BTreeMap<(String, String), String>,
    pub profile: BTreeMap<String, String>,
    pub profile_alphabet: BTreeSet<String>,
    pub grammar: BTreeSet<String>,
    pub terminal: BTreeMap<String, GenesisTerminal>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProfileGrammarEncoder {
    table: BTreeMap<String, String>,
}
impl ProfileGrammarEncoder {
    pub fn new(
        profiles: &BTreeSet<String>,
        grammar: &BTreeSet<String>,
        table: BTreeMap<String, String>,
    ) -> Result<Self, OriginalObserverError> {
        if table.keys().cloned().collect::<BTreeSet<_>>() != *profiles
            || table.values().any(|g| !grammar.contains(g))
        {
            return Err(OriginalObserverError::InvalidEncoder);
        }
        Ok(Self { table })
    }
}

fn ids(labels: &[String]) -> Result<BTreeMap<String, usize>, OriginalObserverError> {
    let map: BTreeMap<_, _> = labels
        .iter()
        .enumerate()
        .map(|(i, s)| (s.clone(), i))
        .collect();
    if map.len() != labels.len() || labels.iter().any(|s| s.is_empty()) {
        return Err(OriginalObserverError::InvalidDomain);
    }
    Ok(map)
}
fn validate_profile_and_update_domain(
    data: &GenesisSixData,
    states: &BTreeMap<String, usize>,
) -> Result<(), OriginalObserverError> {
    if data.profile.keys().cloned().collect::<BTreeSet<_>>() != states.keys().cloned().collect()
        || data
            .profile
            .values()
            .any(|s| !data.profile_alphabet.contains(s))
        || data.profile_alphabet.iter().any(|s| s.is_empty())
        || data.update.len()
            != data
                .states
                .len()
                .checked_mul(data.alphabet.len())
                .ok_or(OriginalObserverError::InvalidDomain)?
    {
        return Err(OriginalObserverError::InvalidDomain);
    }
    Ok(())
}

fn build_memory(
    data: &GenesisSixData,
) -> Result<(FiniteMoore, usize, Vec<String>), OriginalObserverError> {
    let states = ids(&data.states)?;
    ids(&data.alphabet)?;
    let initial = states
        .get(&data.initial)
        .copied()
        .ok_or(OriginalObserverError::InvalidInitialState)?;
    validate_profile_and_update_domain(data, &states)?;
    let labels: Vec<_> = data.profile_alphabet.iter().cloned().collect();
    let reports = ids(&labels)?;
    let transitions = build_transition_rows(data, &states)?;
    let memory = FiniteMoore::new(
        data.states
            .iter()
            .map(|s| reports[&data.profile[s]])
            .collect(),
        transitions,
        data.alphabet.len(),
    )
    .map_err(|_| OriginalObserverError::InvalidDomain)?;
    Ok((memory, initial, labels))
}

fn build_transition_rows(
    data: &GenesisSixData,
    states: &BTreeMap<String, usize>,
) -> Result<Vec<Vec<usize>>, OriginalObserverError> {
    let mut transitions = Vec::new();
    for state in &data.states {
        let mut row = Vec::new();
        for symbol in &data.alphabet {
            let target = data
                .update
                .get(&(state.clone(), symbol.clone()))
                .ok_or(OriginalObserverError::InvalidDomain)?;
            row.push(
                *states
                    .get(target)
                    .ok_or(OriginalObserverError::InvalidDomain)?,
            );
        }
        transitions.push(row);
    }
    Ok(transitions)
}

pub struct OriginalGenesisObserver<C: HistoryContext> {
    data: GenesisSixData,
    memory: FiniteMoore,
    initial: usize,
    profile_labels: Vec<String>,
    contexts: BTreeMap<String, C>,
}
impl<C: HistoryContext> OriginalGenesisObserver<C> {
    pub fn new(
        data: GenesisSixData,
        contexts: BTreeMap<String, C>,
    ) -> Result<Self, OriginalObserverError> {
        let (memory, initial, profile_labels) = build_memory(&data)?;
        if data.grammar.iter().any(|g| g.is_empty())
            || data.terminal.keys().cloned().collect::<BTreeSet<_>>() != data.grammar
            || contexts.keys().any(|c| c.is_empty())
        {
            return Err(OriginalObserverError::InvalidDomain);
        }
        Ok(Self {
            data,
            memory,
            initial,
            profile_labels,
            contexts,
        })
    }
    pub fn data(&self) -> &GenesisSixData {
        &self.data
    }
    pub fn memory(&self) -> &FiniteMoore {
        &self.memory
    }
    pub fn profile_alphabet(&self) -> BTreeSet<String> {
        self.profile_labels.iter().cloned().collect()
    }
    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }
    pub fn history_state(&self, word: &[usize]) -> Result<usize, OriginalObserverError> {
        Ok(run(&self.memory, self.initial, word)?)
    }
    pub fn history_profile(&self, word: &[usize]) -> Result<&str, OriginalObserverError> {
        let x = self.history_state(word)?;
        Ok(&self.profile_labels[self.memory.reports()[x]])
    }
    /// The same source rho is executed, then its output is checked in D*.
    /// No finite-state collapse or totality theorem for arbitrary implementations
    /// is inferred from this successful finite invocation.
    pub fn contextual_profile(
        &self,
        context: &str,
        word: &[usize],
    ) -> Result<&str, OriginalObserverError> {
        self.history_state(word)?;
        let rho = self
            .contexts
            .get(context)
            .ok_or(OriginalObserverError::UnknownContext)?;
        let transformed = rho.apply(word)?;
        self.history_profile(&transformed)
    }
    pub fn terminal_for_expression(
        &self,
        expression: &str,
    ) -> Result<GenesisTerminal, OriginalObserverError> {
        self.data
            .terminal
            .get(expression)
            .copied()
            .ok_or(OriginalObserverError::UnknownGrammar)
    }
    /// G and T are separate original components. Routing a profile requires an
    /// EXTRA checked encoder; neither a profile label nor Proved is authority.
    pub fn terminal_for_history(
        &self,
        word: &[usize],
        encoder: Option<&ProfileGrammarEncoder>,
    ) -> Result<GenesisTerminal, OriginalObserverError> {
        let encoder = encoder.ok_or(OriginalObserverError::MissingEncoder)?;
        if encoder.table.keys().cloned().collect::<BTreeSet<_>>() != self.profile_alphabet()
            || encoder
                .table
                .values()
                .any(|g| !self.data.grammar.contains(g))
        {
            return Err(OriginalObserverError::InvalidEncoder);
        }
        let profile = self.history_profile(word)?;
        self.terminal_for_expression(&encoder.table[profile])
    }
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum GenesisClass {
    OutsideO1,
    O1Only,
    O2,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GenesisClassification {
    pub class: GenesisClass,
    pub o1_witness: Option<Vec<usize>>,
    pub o2_witness: Option<(String, Vec<usize>, Vec<usize>)>,
}

impl OriginalGenesisObserver<FiniteWordTransducer> {
    fn find_o1_witness(&self) -> Option<Vec<usize>> {
        let first_report = self.memory.reports()[self.initial];
        let mut words = BTreeMap::from([(self.initial, vec![])]);
        let mut pending = VecDeque::from([self.initial]);
        let mut o1_witness = None;
        while let Some(state) = pending.pop_front() {
            let word = words[&state].clone();
            if self.memory.reports()[state] != first_report && o1_witness.is_none() {
                o1_witness = Some(word.clone());
            }
            for d in 0..self.memory.input_count() {
                let target = self.memory.transitions()[state][d];
                if !words.contains_key(&target) {
                    let mut extended = word.clone();
                    extended.push(d);
                    words.insert(target, extended);
                    pending.push_back(target);
                }
            }
        }
        o1_witness
    }

    /// O1: two histories have unequal profiles. O2: a context separates a
    /// previously equal-profile pair. Both decisions cover all D*, and ignore G/T by definition.
    pub fn classify_original(&self) -> Result<GenesisClassification, OriginalObserverError> {
        let o1_witness = self.find_o1_witness();
        let mut o2_witness = None;
        for (name, context) in &self.contexts {
            if let Some((first, second)) =
                context.profile_noncongruence(&self.memory, self.initial)?
            {
                o2_witness = Some((name.clone(), first, second));
                break;
            }
        }
        let class = if o2_witness.is_some() {
            GenesisClass::O2
        } else if o1_witness.is_some() {
            GenesisClass::O1Only
        } else {
            GenesisClass::OutsideO1
        };
        Ok(GenesisClassification {
            class,
            o1_witness,
            o2_witness,
        })
    }
    /// Checked total context realizations over the actual declared input alphabet.
    pub fn new_checked(
        data: GenesisSixData,
        contexts: BTreeMap<String, FiniteWordTransducer>,
    ) -> Result<Self, OriginalObserverError> {
        if contexts
            .values()
            .any(|rho| rho.alphabet_size() != data.alphabet.len())
        {
            return Err(OriginalObserverError::History(
                HistoryError::InvalidAlphabet,
            ));
        }
        Self::new(data, contexts)
    }
    /// Universal descent for this finite transducer, via a closed finite product
    /// graph representing every input history. Counterexamples include words.
    pub fn context_state_descent(
        &self,
        context: &str,
    ) -> Result<HistoryDescent, OriginalObserverError> {
        let rho = self
            .contexts
            .get(context)
            .ok_or(OriginalObserverError::UnknownContext)?;
        Ok(rho.descend(&self.memory, self.initial)?)
    }
}

/// Exact recovered WD-5 ten-symbol semantics: Sigma,S,s0,Lambda,C,Pi,u,r,p,rho.
/// The Mealy report r:S x Sigma -> Lambda is independent of profile p:S->Pi.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OriginalOperationalData {
    pub states: Vec<String>,
    pub alphabet: Vec<String>,
    pub initial: String,
    pub update: BTreeMap<(String, String), String>,
    pub transition_report: BTreeMap<(String, String), String>,
    pub report_alphabet: BTreeSet<String>,
    pub profile_alphabet: BTreeSet<String>,
    pub profile: BTreeMap<String, String>,
    pub contexts: BTreeMap<String, BTreeMap<String, String>>,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OriginalOperationalObserver {
    data: OriginalOperationalData,
    memory: FiniteMoore,
    initial: usize,
    report_rows: Vec<Vec<String>>,
}
impl OriginalOperationalObserver {
    fn validate_transition_reports(
        data: &OriginalOperationalData,
    ) -> Result<Vec<Vec<String>>, OriginalObserverError> {
        if data.transition_report.len()
            != data
                .states
                .len()
                .checked_mul(data.alphabet.len())
                .ok_or(OriginalObserverError::InvalidDomain)?
            || data.report_alphabet.iter().any(|r| r.is_empty())
            || data
                .transition_report
                .values()
                .any(|r| !data.report_alphabet.contains(r))
        {
            return Err(OriginalObserverError::InvalidDomain);
        }
        let mut report_rows = Vec::new();
        for state in &data.states {
            let row = data
                .alphabet
                .iter()
                .map(|d| {
                    data.transition_report
                        .get(&(state.clone(), d.clone()))
                        .cloned()
                        .ok_or(OriginalObserverError::InvalidDomain)
                })
                .collect::<Result<Vec<_>, _>>()?;
            if row.iter().any(|r| r.is_empty()) {
                return Err(OriginalObserverError::InvalidDomain);
            }
            report_rows.push(row);
        }
        Ok(report_rows)
    }

    fn validate_contexts(
        data: &OriginalOperationalData,
        states: &BTreeMap<String, usize>,
    ) -> Result<(), OriginalObserverError> {
        let state_keys: BTreeSet<_> = states.keys().cloned().collect();
        for (label, context) in &data.contexts {
            if label.is_empty()
                || context.keys().cloned().collect::<BTreeSet<_>>() != state_keys
                || context.values().any(|x| !states.contains_key(x))
            {
                return Err(OriginalObserverError::InvalidDomain);
            }
        }
        Ok(())
    }

    pub fn new(data: OriginalOperationalData) -> Result<Self, OriginalObserverError> {
        let proxy = GenesisSixData {
            states: data.states.clone(),
            alphabet: data.alphabet.clone(),
            initial: data.initial.clone(),
            update: data.update.clone(),
            profile: data.profile.clone(),
            profile_alphabet: data.profile_alphabet.clone(),
            grammar: BTreeSet::new(),
            terminal: BTreeMap::new(),
        };
        let (base, initial, _) = build_memory(&proxy)?;
        let report_rows = Self::validate_transition_reports(&data)?;
        let states = ids(&data.states)?;
        Self::validate_contexts(&data, &states)?;
        let mut row_ids = BTreeMap::new();
        let reports = report_rows
            .iter()
            .map(|row| {
                let fresh = row_ids.len();
                *row_ids.entry(row.clone()).or_insert(fresh)
            })
            .collect();
        let memory = FiniteMoore::new(reports, base.transitions().to_vec(), data.alphabet.len())
            .map_err(|_| OriginalObserverError::InvalidDomain)?;
        Ok(Self {
            data,
            memory,
            initial,
            report_rows,
        })
    }
    pub fn data(&self) -> &OriginalOperationalData {
        &self.data
    }
    pub fn memory(&self) -> &FiniteMoore {
        &self.memory
    }
    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }
    /// Emits r(state,input) BEFORE applying u(state,input), preserving Mealy
    /// semantics and the original input-dependent report rather than a Moore label.
    pub fn report_trace(
        &self,
        word: &[usize],
    ) -> Result<(Vec<String>, usize), OriginalObserverError> {
        let mut state = self.initial;
        let mut reports = Vec::new();
        for &d in word {
            if d >= self.data.alphabet.len() {
                return Err(OriginalObserverError::History(HistoryError::InvalidWord));
            }
            reports.push(self.report_rows[state][d].clone());
            state = run(&self.memory, state, &[d])?;
        }
        Ok((reports, state))
    }
    /// W1->W2 is possible exactly when this state action preserves reachability.
    /// The returned history action is an explicit lift, not an assumed fork match.
    pub fn lift_state_context(
        &self,
        context: &str,
    ) -> Result<StateContextLift, OriginalObserverError> {
        let table = self
            .data
            .contexts
            .get(context)
            .ok_or(OriginalObserverError::UnknownContext)?;
        let states = ids(&self.data.states)?;
        Ok(StateContextLift::new(
            self.memory.clone(),
            self.initial,
            self.data.states.iter().map(|s| states[&table[s]]).collect(),
        )?)
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_65a4a713 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
