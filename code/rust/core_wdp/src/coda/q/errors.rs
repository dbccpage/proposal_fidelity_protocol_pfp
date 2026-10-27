use std::fmt;

use thiserror::Error;

/// Mandatory Q packet fields.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum QPacketField {
    Carrier,
    Composition,
    Observer,
    FinitePredictions,
    Transport,
    Residual,
    TerminalRequest,
}

impl QPacketField {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Carrier => "carrier",
            Self::Composition => "composition",
            Self::Observer => "observer",
            Self::FinitePredictions => "finite_predictions",
            Self::Transport => "transport",
            Self::Residual => "residual",
            Self::TerminalRequest => "terminal_request",
        }
    }
}

impl fmt::Display for QPacketField {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

/// Typed Q validation/admission failures.
#[derive(Clone, Debug, PartialEq, Eq, Error)]
pub enum QError {
    #[error("missing mandatory Q packet field: {0}")]
    MissingMandatoryField(QPacketField),
    #[error("QHeld requires a named finite_shadow")]
    QHeldWithoutFiniteShadow,
    #[error("QHeld requires a refinement relation and convergence certificate route")]
    QHeldWithoutRefinementRoute,
    #[error("QHeld requires a live descent_trigger")]
    QHeldWithoutDescentTrigger,
    #[error("continuum claim without declared topology is refused")]
    ContinuumClaimWithoutTopology,
    #[error("candidate refused: no finite shadow was declared")]
    RefusedContinuumNoShadow,
    #[error("candidate requires an oracle/certificate route for convergence")]
    OracleNeededConvergence,
    #[error("candidate remains an open residual")]
    OpenResidual,
    #[error("real/complex QM transport requires an explicit composition rule")]
    CompositionRuleRequired,
    #[error("No-Genesis boundary violation (PCC.core_top): observer creation claimed without declared non-constant observable profile")]
    NoGenesisBoundaryViolation,
}


/// The seven mandatory Q packet tokens are nonempty and pairwise distinct.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct QFieldTokenWitness {
    count: u8,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum QFieldTokenError {
    CountMismatch { got: usize },
    EmptyToken { index: usize },
    DuplicateToken { index: usize },
    MissingToken { token: &'static str },
}

impl QFieldTokenWitness {
    const TOKENS: [&'static str; 7] = [
        "carrier",
        "composition",
        "observer",
        "finite_predictions",
        "transport",
        "residual",
        "terminal_request",
    ];

    pub fn admit(fields: &[QPacketField]) -> Result<Self, QFieldTokenError> {
        if fields.len() != Self::TOKENS.len() {
            return Err(QFieldTokenError::CountMismatch { got: fields.len() });
        }
        let mut seen: Vec<&str> = Vec::new();
        for (index, field) in fields.iter().enumerate() {
            let token = field.as_str();
            if token.is_empty() {
                return Err(QFieldTokenError::EmptyToken { index });
            }
            if seen.contains(&token) {
                return Err(QFieldTokenError::DuplicateToken { index });
            }
            seen.push(token);
        }
        for token in Self::TOKENS {
            if !seen.contains(&token) {
                return Err(QFieldTokenError::MissingToken { token });
            }
        }
        let count = u8::try_from(seen.len()).map_err(|_| QFieldTokenError::CountMismatch {
            got: seen.len(),
        })?;
        Ok(Self { count })
    }

    pub fn count(&self) -> u8 {
        self.count
    }
}

// Origin: engine/crates_rs/core_wdp/src/coda/q/errors.rs
// Claim: urn:core:crates_rs:core-wdp:errors:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn mandatory_q_tokens_are_seven_distinct_strings() {
        let fields = [
            QPacketField::Carrier,
            QPacketField::Composition,
            QPacketField::Observer,
            QPacketField::FinitePredictions,
            QPacketField::Transport,
            QPacketField::Residual,
            QPacketField::TerminalRequest,
        ];
        let admitted = QFieldTokenWitness::admit(&fields);
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|witness| witness.count()), Some(7));
        let mut duplicate = fields;
        duplicate[6] = QPacketField::Carrier;
        assert!(matches!(
            QFieldTokenWitness::admit(&duplicate),
            Err(QFieldTokenError::DuplicateToken { index: 6 })
        ));
    }
}
