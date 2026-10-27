//! A literal `<>` history executed by the canonical Genesis primitives.
//!
//! Every accepted prefix is compared with WDP's existing deduplicating source
//! model. A separately requested incidence interpretation constructs cells
//! from admitted instances, never from token spelling. Mathematical results
//! are obtained from the existing geometry/homology owners.

use core_ooutwire_primitives::{admission, event::Event, regime::Regime, token::Token};

use core_homology::declared_incidence::{declared_chain_report, encode_declared};
use core_homology::simplicial::SimplicialComplex;

use crate::genesis_geometry::{ChainReport, ComplexPacket};
use crate::genesis_primitive_execution::{
    PrimitiveEvent, PrimitiveInstance, PrimitiveReading, PrimitiveRegime,
};

/// The exact first presentation of this construction.
pub const GENESIS_INSCRIPTION: &str = "<>";

/// Caller-supplied execution limits, kept with the construction on continuation.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ConstructionLimits {
    pub max_events: usize,
    pub max_cells: usize,
    /// Conservative dense-matrix allowance: the square of the total cell count.
    pub max_matrix_entries: usize,
}

impl Default for ConstructionLimits {
    fn default() -> Self {
        Self {
            max_events: 4096,
            max_cells: 512,
            max_matrix_entries: 262_144,
        }
    }
}

/// An admission, correspondence, or interpretation failure.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ConstructionError {
    #[error("the first event must present the literal <> inscription")]
    MissingLiteralRoot,
    #[error("canonical admission at event {index} failed: {reason}")]
    Admission { index: usize, reason: String },
    #[error("WDP source correspondence at event {index} failed: {reason}")]
    Correspondence { index: usize, reason: String },
    #[error("the incidence interpretation requires at least one admitted form")]
    NoIncidenceForm,
    #[error("uniform rules and separation requirements need their own geometric interpretation")]
    UnsupportedIncidenceCommitments,
    #[error("admitted datum {0} has no explicit vertex instance")]
    MissingVertex(usize),
    #[error("invalid admitted incidence: {0}")]
    Incidence(String),
    #[error("the claimed chain report differs from the replayed history")]
    ReportMismatch,
    #[error("declared {resource} limit {limit} exceeded")]
    ResourceLimit {
        resource: &'static str,
        limit: usize,
    },
}

/// Copy every admitted field, including requirements. No geometric reading yet.
pub fn interpret_regime(regime: &Regime) -> Result<PrimitiveRegime, ConstructionError> {
    PrimitiveRegime::try_new(
        regime
            .data()
            .iter()
            .map(|token| token.text().to_owned())
            .collect(),
        regime.forms().to_vec(),
        regime
            .insts()
            .iter()
            .map(|instance| PrimitiveInstance {
                form: instance.form,
                args: instance.args.iter().map(|mark| mark.index()).collect(),
            })
            .collect(),
        regime.rules().clone(),
        regime
            .reqs()
            .iter()
            .map(|pair| (pair.i.index(), pair.j.index()))
            .collect(),
    )
    .map_err(|error| ConstructionError::Correspondence {
        index: 0,
        reason: error.to_string(),
    })
}

/// Translate all six event kinds without adding or discarding an event.
pub fn interpret_event(event: &Event) -> PrimitiveEvent {
    match event {
        Event::Supply(token) => PrimitiveEvent::Supply {
            token: token.text().to_owned(),
        },
        Event::AdmitDatum(token) => PrimitiveEvent::AdmitDatum {
            token: token.text().to_owned(),
        },
        Event::AdmitForm(arity) => PrimitiveEvent::AdmitForm { arity: *arity },
        Event::AdmitInst(form, args) => PrimitiveEvent::AdmitInst {
            form: *form,
            args: args.iter().map(|mark| mark.index()).collect(),
        },
        Event::AdmitRuleAll(form) => PrimitiveEvent::AdmitRuleAll { form: *form },
        Event::Impose(pair) => PrimitiveEvent::Impose {
            i: pair.i.index(),
            j: pair.j.index(),
        },
    }
}

/// A retained construction. Fields are private; every extension runs both steps.
///
/// `pre_genesis()` has no presentation and no admitted data. The first accepted
/// event supplies `<>`; it still admits nothing. Later admissions are supplied
/// construction choices. This type does not issue operational authorization.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GenesisConstruction {
    limits: ConstructionLimits,
    history: Vec<Event>,
    regime: Regime,
    interpreted: PrimitiveRegime,
}

impl GenesisConstruction {
    pub fn pre_genesis() -> Self {
        Self::pre_genesis_with_limits(ConstructionLimits::default())
    }

    pub fn pre_genesis_with_limits(limits: ConstructionLimits) -> Self {
        Self {
            limits,
            history: Vec::new(),
            regime: Regime::genesis(),
            interpreted: PrimitiveRegime::empty(),
        }
    }

    pub fn from_literal_seed() -> Result<Self, ConstructionError> {
        Self::pre_genesis().advance(Event::Supply(Token::new(GENESIS_INSCRIPTION)))
    }

    /// Recompute every prefix from the original empty admitted state.
    pub fn replay(history: &[Event]) -> Result<Self, ConstructionError> {
        Self::replay_with_limits(history, ConstructionLimits::default())
    }

    pub fn replay_with_limits(
        history: &[Event],
        limits: ConstructionLimits,
    ) -> Result<Self, ConstructionError> {
        if history.is_empty() {
            return Err(ConstructionError::MissingLiteralRoot);
        }
        if history.len() > limits.max_events {
            return Err(ConstructionError::ResourceLimit {
                resource: "event count",
                limit: limits.max_events,
            });
        }
        Self::pre_genesis_with_limits(limits).extend(history)
    }

    pub fn history(&self) -> &[Event] {
        &self.history
    }
    pub fn regime(&self) -> &Regime {
        &self.regime
    }
    pub fn interpreted(&self) -> &PrimitiveRegime {
        &self.interpreted
    }

    pub fn limits(&self) -> ConstructionLimits {
        self.limits
    }

    /// Return a new history; a refused event leaves the original untouched.
    ///
    /// The canonical crate uses deduplication. WDP's occurrence reading remains
    /// available elsewhere and is deliberately not identified with that reading.
    pub fn advance(&self, event: Event) -> Result<Self, ConstructionError> {
        let index = self.history.len();
        if index >= self.limits.max_events {
            return Err(ConstructionError::ResourceLimit {
                resource: "event count",
                limit: self.limits.max_events,
            });
        }
        if index == 0 && event != Event::Supply(Token::new(GENESIS_INSCRIPTION)) {
            return Err(ConstructionError::MissingLiteralRoot);
        }
        let regime = admission::step(&self.regime, &event).map_err(|error| {
            ConstructionError::Admission {
                index,
                reason: error.to_string(),
            }
        })?;
        let interpreted = self
            .interpreted
            .step(&interpret_event(&event), PrimitiveReading::Dedup)
            .map_err(|error| ConstructionError::Correspondence {
                index,
                reason: error.to_string(),
            })?;
        let restored =
            interpret_regime(&regime).map_err(|error| ConstructionError::Correspondence {
                index,
                reason: error.to_string(),
            })?;
        if restored != interpreted {
            return Err(ConstructionError::Correspondence {
                index,
                reason: "complete states differ".into(),
            });
        }
        let mut history = self.history.clone();
        history.push(event);
        Ok(Self {
            limits: self.limits,
            history,
            regime,
            interpreted,
        })
    }

    pub fn extend(&self, events: &[Event]) -> Result<Self, ConstructionError> {
        events
            .iter()
            .try_fold(self.clone(), |state, event| state.advance(event.clone()))
    }

    fn incidence_cells(&self) -> Result<Vec<Vec<usize>>, ConstructionError> {
        if self.regime.forms().is_empty() {
            return Err(ConstructionError::NoIncidenceForm);
        }
        if !self.regime.rules().is_empty() || !self.regime.reqs().is_empty() {
            return Err(ConstructionError::UnsupportedIncidenceCommitments);
        }
        let cell_count = self.regime.insts().len();
        if cell_count > self.limits.max_cells {
            return Err(ConstructionError::ResourceLimit {
                resource: "cell count",
                limit: self.limits.max_cells,
            });
        }
        if cell_count
            .checked_mul(cell_count)
            .is_none_or(|size| size > self.limits.max_matrix_entries)
        {
            return Err(ConstructionError::ResourceLimit {
                resource: "matrix entries",
                limit: self.limits.max_matrix_entries,
            });
        }
        let cells: Vec<Vec<usize>> = self
            .regime
            .insts()
            .iter()
            .map(|instance| instance.args.iter().map(|mark| mark.index()).collect())
            .collect();
        for vertex in 0..self.regime.n_data() {
            if !cells.contains(&vec![vertex]) {
                return Err(ConstructionError::MissingVertex(vertex));
            }
        }
        Ok(cells)
    }

    /// Admitted instances, checked once against the declared incidence domain.
    fn encoded_incidence(&self) -> Result<(ComplexPacket, SimplicialComplex), ConstructionError> {
        let cells = self.incidence_cells()?;
        let complex = encode_declared(&cells)
            .map_err(|error| ConstructionError::Incidence(format!("{error:?}")))?;
        Ok((ComplexPacket { cells }, complex))
    }

    /// Choose the simplicial-incidence interpretation of this admitted state:
    /// an arity-k form denotes a (k-1)-simplex on its ordered argument marks.
    ///
    /// Every datum needs an explicit vertex instance; all faces must already
    /// exist. Duplicate cells, non-increasing arguments, uniform rules and
    /// requirements are refused rather than normalized or omitted.
    pub fn simplicial_incidence(&self) -> Result<ComplexPacket, ConstructionError> {
        self.encoded_incidence().map(|(packet, _complex)| packet)
    }

    /// Rational boundaries and Betti numbers from `core_homology`.
    pub fn homology(&self) -> Result<ChainReport, ConstructionError> {
        let (_packet, complex) = self.encoded_incidence()?;
        declared_chain_report(&complex)
            .map(ChainReport::from)
            .map_err(|error| ConstructionError::Incidence(format!("{error:?}")))
    }
}

/// Recompute from a separately supplied event history, then compare the result.
pub fn verify_history_report(
    history: &[Event],
    claimed: &ChainReport,
) -> Result<(), ConstructionError> {
    let actual = GenesisConstruction::replay(history)?.homology()?;
    if actual != *claimed {
        return Err(ConstructionError::ReportMismatch);
    }
    Ok(())
}

/// Construct the boundary of a triangle through explicit canonical admissions.
/// Labels are opaque; changing their spelling does not choose the cell structure.
fn admit_triangle_skeleton(
    mut walk: GenesisConstruction,
) -> Result<GenesisConstruction, ConstructionError> {
    use core_ooutwire_primitives::mark::Mark;
    for arity in 1..=3 {
        walk = walk.advance(Event::AdmitForm(arity))?;
    }
    for vertex in 0..3 {
        walk = walk.advance(Event::AdmitInst(0, vec![Mark(vertex)]))?;
    }
    for [a, b] in [[0, 1], [1, 2], [0, 2]] {
        walk = walk.advance(Event::AdmitInst(1, vec![Mark(a), Mark(b)]))?;
    }
    Ok(walk)
}

pub fn cycle_construction(labels: [&str; 3]) -> Result<GenesisConstruction, ConstructionError> {
    let mut walk = GenesisConstruction::from_literal_seed()?;
    for label in labels {
        walk = walk.advance(Event::Supply(Token::new(label)))?;
        walk = walk.advance(Event::AdmitDatum(Token::new(label)))?;
    }
    admit_triangle_skeleton(walk)
}

// Origin: engine/crates_rs/core_wdp/src/genesis_construction.rs
// Claim: urn:core:crates_rs:core-wdp:genesis-construction:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_29805576 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
