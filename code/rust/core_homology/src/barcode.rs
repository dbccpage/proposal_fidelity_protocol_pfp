//! Barcode view over a persistence diagram (interval representation).
//!
//! AuthorityEffect: None. Shell / best-effort computational topology.
//! Not PROVED; not GlobalGreen.

use crate::persistence_diagram::{PersistenceDiagram, PersistencePoint};
use num_rational::BigRational;
use serde::{Deserialize, Serialize};

/// One barcode interval [birth, death) or [birth, ∞).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Bar {
    pub birth: BigRational,
    pub death: Option<BigRational>,
    pub dimension: usize,
}

impl From<&PersistencePoint> for Bar {
    fn from(p: &PersistencePoint) -> Self {
        Self {
            birth: p.birth.clone(),
            death: p.death.clone(),
            dimension: p.dimension,
        }
    }
}

/// Logical barcode: view over a diagram as intervals.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Barcode {
    pub bars: Vec<Bar>,
}

impl Barcode {
    pub fn from_diagram(diagram: &PersistenceDiagram) -> Self {
        Self {
            bars: diagram.points.iter().map(Bar::from).collect(),
        }
    }

    pub fn len(&self) -> usize {
        self.bars.len()
    }

    pub fn is_empty(&self) -> bool {
        self.bars.is_empty()
    }
}


/// A finite bar has strictly positive exact persistence. An essential bar has no death.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AdmittedBar {
    dimension: usize,
    essential: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BarAdmitError {
    NonPositivePersistence,
}

// Origin: engine/crates_rs/core_homology/src/barcode.rs
// Claim: urn:core:crates_rs:core-homology:barcode:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for BarAdmitError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for BarAdmitError {}

impl AdmittedBar {
    pub fn admit(bar: &Bar) -> Result<Self, BarAdmitError> {
        if let Some(death) = &bar.death {
            let persistence = death.clone() - bar.birth.clone();
            if persistence <= BigRational::from_integer(0.into()) {
                return Err(BarAdmitError::NonPositivePersistence);
            }
        }
        Ok(Self {
            dimension: bar.dimension,
            essential: bar.death.is_none(),
        })
    }

    pub fn dimension(&self) -> usize {
        self.dimension
    }

    pub fn essential(&self) -> bool {
        self.essential
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::persistence_diagram::PersistencePoint;

    #[test]
    fn barcode_from_empty_diagram() {
        let d = PersistenceDiagram::new(vec![]);
        assert!(Barcode::from_diagram(&d).is_empty());
    }

    #[test]
    fn barcode_preserves_dim() {
        let d = PersistenceDiagram::new(vec![PersistencePoint::finite(
            BigRational::from_integer(0.into()),
            BigRational::from_integer(1.into()),
            1,
        )]);
        let b = Barcode::from_diagram(&d);
        assert_eq!(b.bars[0].dimension, 1);
    }

    #[test]
    fn finite_bar_persistence_is_positive() {
        let finite = Bar {
            birth: BigRational::from_integer(0.into()),
            death: Some(BigRational::from_integer(2.into())),
            dimension: 1,
        };
        let admitted = AdmittedBar::admit(&finite);
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|witness| witness.dimension()), Some(1));
        let degenerate = Bar {
            birth: BigRational::from_integer(2.into()),
            death: Some(BigRational::from_integer(2.into())),
            dimension: 0,
        };
        assert!(matches!(
            AdmittedBar::admit(&degenerate),
            Err(BarAdmitError::NonPositivePersistence)
        ));
    }

}
