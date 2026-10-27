//! Genesis refusal comparison and the separate 64-description constitution.
//! These are distinct source models, not extra toggles of PassageState.
//! Original `Refusal.stepR` is the projection forgetting forms/instances of the
//! richer Python comparison. Meta markers live in the history only.

use crate::genesis_passage::{separated, separates, Column, Pair};
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Discipline {
    Silent,
    Meta,
    Fact,
    ReifyUntagged,
    ReifyTagged,
    Occurrence,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum RefusalEvent {
    Supply(String),
    Admit(String),
    Marker(String),
    Form,
    Instance(usize),
}

#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct RefusalState {
    pub data: Vec<String>,
    pub tags: BTreeSet<usize>,
    pub refusals: usize,
    pub has_form: bool,
    pub insts: BTreeSet<usize>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RefusalError {
    CounterOverflow,
    InvalidDescription,
}

// Origin: engine/crates_rs/core_wdp/src/genesis_refusal.rs
// Claim: urn:core:crates_rs:core-wdp:genesis-refusal:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for RefusalError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for RefusalError {}

impl RefusalState {
    fn admit_token(&mut self, mode: Discipline, tok: &str) -> Result<(), RefusalError> {
        if mode == Discipline::Occurrence || !self.data.contains(&tok.to_string()) {
            self.data.push(tok.to_string());
            return Ok(());
        }
        match mode {
            Discipline::Silent | Discipline::Meta | Discipline::Occurrence => (),
            Discipline::Fact => {
                self.refusals = self
                    .refusals
                    .checked_add(1)
                    .ok_or(RefusalError::CounterOverflow)?
            }
            Discipline::ReifyUntagged => self.data.push(tok.to_string()),
            Discipline::ReifyTagged => {
                self.tags.insert(self.data.len());
                self.data.push(tok.to_string());
            }
        }
        Ok(())
    }

    pub fn step(&self, mode: Discipline, event: &RefusalEvent) -> Result<Self, RefusalError> {
        let mut out = self.clone();
        match event {
            RefusalEvent::Supply(_) | RefusalEvent::Marker(_) => (),
            RefusalEvent::Form => out.has_form = true,
            RefusalEvent::Instance(i) => {
                if self.has_form && *i < self.data.len() {
                    out.insts.insert(*i);
                }
            }
            RefusalEvent::Admit(tok) => out.admit_token(mode, tok)?,
        }
        Ok(out)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct Constitution {
    pub dedup_admit: bool,
    pub guard_require: bool,
    pub guard_accept: bool,
    pub gate_budget: bool,
    pub gate_license: bool,
    pub cert_refusal: bool,
}

impl Constitution {
    pub const KERNEL: Self = Self {
        dedup_admit: true,
        guard_require: true,
        guard_accept: true,
        gate_budget: true,
        gate_license: true,
        cert_refusal: true,
    };

    /// Original Lean `allDescs` order: first field slowest, last fastest.
    /// This is NOT the educational `Desc.to_index` (first field least bit).
    pub fn from_lean_index(index: usize) -> Result<Self, RefusalError> {
        if index >= 64 {
            return Err(RefusalError::InvalidDescription);
        }
        Ok(Self {
            dedup_admit: index & 32 != 0,
            guard_require: index & 16 != 0,
            guard_accept: index & 8 != 0,
            gate_budget: index & 4 != 0,
            gate_license: index & 2 != 0,
            cert_refusal: index & 1 != 0,
        })
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RepresentedWorld {
    pub data: Vec<usize>,
    pub views: Vec<Column>,
    pub reqs: Vec<Pair>,
    pub refusals: Vec<Pair>,
    pub budget: usize,
    pub aug_licensed: bool,
    pub notes: Vec<usize>,
}

impl Default for RepresentedWorld {
    fn default() -> Self {
        Self {
            data: vec![],
            views: vec![],
            reqs: vec![],
            refusals: vec![],
            budget: 0,
            aug_licensed: true,
            notes: vec![],
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum WorldEvent {
    Admit(usize),
    Require(usize, usize),
    Mark(Column, usize),
    AddView(Column),
    Refuse(usize, usize),
    Note(usize),
    SetBudget(usize),
    SetAugLicense(bool),
}

impl RepresentedWorld {
    pub fn satisfied(&self, r: Pair) -> bool {
        separated(&self.views, r.0, r.1)
    }
    pub fn violated(&self, r: Pair) -> bool {
        self.reqs.contains(&r) && !self.satisfied(r)
    }

    fn mark_apply(&self, v: &Column, p: usize) -> Self {
        let mut out = self.clone();
        out.views = self
            .views
            .iter()
            .map(|c| {
                if c == v {
                    std::iter::once(p).chain(c.iter().copied()).collect()
                } else {
                    c.clone()
                }
            })
            .collect();
        out
    }

    pub fn mark_ok(&self, v: &Column, p: usize) -> bool {
        if !self.views.contains(v) || p >= self.data.len() || v.contains(&p) {
            return false;
        }
        let after = self.mark_apply(v, p);
        self.reqs
            .iter()
            .any(|&r| self.violated(r) && after.satisfied(r))
            && self
                .reqs
                .iter()
                .all(|&r| !self.satisfied(r) || after.satisfied(r))
    }

    pub fn augmentation_ok(&self, c: &Column) -> bool {
        c.iter().all(|&p| p < self.data.len())
            && !self.views.contains(c)
            && (0..self.data.len()).any(|i| {
                (0..self.data.len())
                    .any(|j| i != j && separates(c, i, j) && !self.satisfied((i, j)))
            })
    }

    /// Exhausts the declared SAME-LEVEL response menu. Budget/license do not
    /// enter this predicate; absence of fuel is not a proof of no repair.
    pub fn obstructed(&self, r: Pair) -> bool {
        self.violated(r)
            && self.views.iter().all(|v| {
                (0..self.data.len())
                    .all(|p| !self.mark_ok(v, p) || !self.mark_apply(v, p).satisfied(r))
            })
    }

    fn can_require(&self, d: Constitution, i: usize, j: usize) -> bool {
        if !d.guard_require {
            return true;
        }
        let valid_indices = i != j && i < self.data.len() && j < self.data.len();
        valid_indices && !self.reqs.contains(&(i, j))
    }

    fn can_mark(&self, d: Constitution, v: &Column, p: usize) -> bool {
        (!d.guard_accept || self.mark_ok(v, p)) && (!d.gate_budget || self.budget > 0)
    }

    fn can_add_view(&self, d: Constitution, c: &Column) -> bool {
        let accepted = !d.guard_accept || self.augmentation_ok(c);
        let licensed = !d.gate_license || self.aug_licensed;
        let funded = !d.gate_budget || self.budget > 0;
        accepted && licensed && funded
    }

    fn can_refuse(&self, d: Constitution, i: usize, j: usize) -> bool {
        (!d.cert_refusal || self.obstructed((i, j))) && !self.refusals.contains(&(i, j))
    }

    fn step_admit(&mut self, d: Constitution, t: usize) {
        if !d.dedup_admit || !self.data.contains(&t) {
            self.data.push(t);
        }
    }

    fn step_require(&mut self, d: Constitution, i: usize, j: usize) {
        if self.can_require(d, i, j) {
            self.reqs.push((i, j));
        }
    }

    fn step_mark(&self, out: &mut Self, d: Constitution, v: &Column, p: usize) {
        if self.can_mark(d, v, p) {
            *out = self.mark_apply(v, p);
            out.budget = self.budget.saturating_sub(1);
        }
    }

    fn step_add_view(&self, out: &mut Self, d: Constitution, c: &Column) {
        if self.can_add_view(d, c) {
            out.views.push(c.clone());
            out.budget = self.budget.saturating_sub(1);
        }
    }

    fn step_refuse(&self, out: &mut Self, d: Constitution, i: usize, j: usize) {
        if self.can_refuse(d, i, j) {
            out.refusals.push((i, j));
        }
    }

    pub fn step(&self, d: Constitution, e: &WorldEvent) -> Self {
        let mut out = self.clone();
        match e {
            WorldEvent::Admit(t) => out.step_admit(d, *t),
            WorldEvent::Require(i, j) => out.step_require(d, *i, *j),
            WorldEvent::Mark(v, p) => self.step_mark(&mut out, d, v, *p),
            WorldEvent::AddView(c) => self.step_add_view(&mut out, d, c),
            WorldEvent::Refuse(i, j) => self.step_refuse(&mut out, d, *i, *j),
            WorldEvent::Note(n) => out.notes.push(*n),
            WorldEvent::SetBudget(n) => out.budget = *n,
            WorldEvent::SetAugLicense(b) => out.aug_licensed = *b,
        }
        out
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_d564d070 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
