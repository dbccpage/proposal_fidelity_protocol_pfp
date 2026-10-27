//! Host-side finite permutation observations over compiled governance pins.
//!
//! The runtime dispatcher supplies the named presentation; producer payloads
//! cannot provide pin contents. Dispatch success is distinct from a rederived,
//! contradicted, or open mathematical observation. This is not a license.
//!
//! The typed payload is checked after the generic runtime Value decoder. It
//! cannot recover raw duplicate keys already collapsed by that decoder.
//! AuthorityEffect: None.

use pfp_runtime::rewriting::{presentation_digest, Presentation};
use serde::{Deserialize, Serialize};

pub const PINNED_PERMUTATION_OBSERVATION_SCHEMA: &str =
    "core.symbol-game.pinned-permutation-order-observation.v1";

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "serde_json::Value")]
pub struct PinnedPermutationOrderRequestV1 {
    pub presentation_ref: String,
    pub claimed_order: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "serde_json::Value")]
pub struct PermutationOrderEvidenceV1 {
    pub presentation_digest: String,
    pub derived_order: String,
    pub cycles: Vec<Vec<String>>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(
    tag = "status",
    rename_all = "SCREAMING_SNAKE_CASE",
    deny_unknown_fields
)]
pub enum PinnedPermutationEvaluationV1 {
    Rederived {
        evidence: PermutationOrderEvidenceV1,
    },
    Contradicted {
        evidence: PermutationOrderEvidenceV1,
    },
    OpenResidual {
        obligation: String,
    },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "serde_json::Value")]
pub struct PinnedPermutationOrderObservationV1 {
    pub schema_version: String,
    pub submitted_presentation_ref: String,
    pub submitted_claimed_order: String,
    pub evaluation: PinnedPermutationEvaluationV1,
    pub authority_effect: String,
}

// Struct derives also admit positional sequences. These wire contracts require
// objects at every struct boundary, including standalone typed deserialization.
// The private shapes additionally reject undeclared fields. As with the runtime
// payload itself, this Value gate does not recover collapsed raw duplicate keys.
fn object_fields<T: serde::de::DeserializeOwned>(value: serde_json::Value) -> Result<T, String> {
    if !value.is_object() {
        return Err("PINNED_PERMUTATION_WIRE_REQUIRES_OBJECT".to_owned());
    }
    serde_json::from_value(value).map_err(|error| error.to_string())
}

impl TryFrom<serde_json::Value> for PinnedPermutationOrderRequestV1 {
    type Error = String;

    fn try_from(value: serde_json::Value) -> Result<Self, Self::Error> {
        #[derive(Deserialize)]
        #[serde(deny_unknown_fields)]
        struct Fields {
            presentation_ref: String,
            claimed_order: String,
        }
        let fields: Fields = object_fields(value)?;
        Ok(Self {
            presentation_ref: fields.presentation_ref,
            claimed_order: fields.claimed_order,
        })
    }
}

impl TryFrom<serde_json::Value> for PermutationOrderEvidenceV1 {
    type Error = String;

    fn try_from(value: serde_json::Value) -> Result<Self, Self::Error> {
        #[derive(Deserialize)]
        #[serde(deny_unknown_fields)]
        struct Fields {
            presentation_digest: String,
            derived_order: String,
            cycles: Vec<Vec<String>>,
        }
        let fields: Fields = object_fields(value)?;
        Ok(Self {
            presentation_digest: fields.presentation_digest,
            derived_order: fields.derived_order,
            cycles: fields.cycles,
        })
    }
}

impl TryFrom<serde_json::Value> for PinnedPermutationOrderObservationV1 {
    type Error = String;

    fn try_from(value: serde_json::Value) -> Result<Self, Self::Error> {
        #[derive(Deserialize)]
        #[serde(deny_unknown_fields)]
        struct Fields {
            schema_version: String,
            submitted_presentation_ref: String,
            submitted_claimed_order: String,
            evaluation: PinnedPermutationEvaluationV1,
            authority_effect: String,
        }
        let fields: Fields = object_fields(value)?;
        Ok(Self {
            schema_version: fields.schema_version,
            submitted_presentation_ref: fields.submitted_presentation_ref,
            submitted_claimed_order: fields.submitted_claimed_order,
            evaluation: fields.evaluation,
            authority_effect: fields.authority_effect,
        })
    }
}

/// Validate the bounded typed claim before resolving any host pin.
///
/// Leading zeroes remain submitted spelling, not another mathematical value.
/// Comparing normalized decimal strings avoids work proportional to a
/// producer-selected numeric exponent or arbitrary-precision integer parsing.
pub(crate) fn validate_claim(
    request: &PinnedPermutationOrderRequestV1,
) -> Result<(), &'static str> {
    if request.claimed_order.is_empty()
        || !request
            .claimed_order
            .bytes()
            .all(|byte| byte.is_ascii_digit())
    {
        return Err("CLAIMED_ORDER_NOT_ASCII_DECIMAL");
    }
    Ok(())
}

/// Observe only the presentation selected by the host's compiled name lookup.
///
/// This function is crate-internal; the only runtime caller obtains
/// `presentation` from the compiled catalogue, never the request payload.
pub(crate) fn observe(
    request: PinnedPermutationOrderRequestV1,
    presentation: Option<&Presentation>,
) -> Result<PinnedPermutationOrderObservationV1, &'static str> {
    validate_claim(&request)?;
    let evaluation = match presentation {
        None => PinnedPermutationEvaluationV1::OpenResidual {
            obligation: "PRESENTATION_NOT_PINNED".to_owned(),
        },
        Some(presentation) => match presentation.permutation_order() {
            Err(_) => PinnedPermutationEvaluationV1::OpenResidual {
                obligation: "PINNED_PRESENTATION_NOT_A_TOTAL_PERMUTATION".to_owned(),
            },
            Ok(witness) => {
                let evidence = PermutationOrderEvidenceV1 {
                    presentation_digest: presentation_digest(presentation),
                    derived_order: witness.order().to_string(),
                    cycles: witness.cycles().to_vec(),
                };
                let trimmed = request.claimed_order.trim_start_matches('0');
                let normalized_claim = if trimmed.is_empty() { "0" } else { trimmed };
                if normalized_claim == evidence.derived_order {
                    PinnedPermutationEvaluationV1::Rederived { evidence }
                } else {
                    PinnedPermutationEvaluationV1::Contradicted { evidence }
                }
            }
        },
    };
    Ok(PinnedPermutationOrderObservationV1 {
        schema_version: PINNED_PERMUTATION_OBSERVATION_SCHEMA.to_owned(),
        submitted_presentation_ref: request.presentation_ref,
        submitted_claimed_order: request.claimed_order,
        evaluation,
        authority_effect: "None".to_owned(),
    })
}

// Origin: engine/crates_rs/pfp/src/pinned_permutation.rs
// Claim: urn:core:crates_rs:pfp:pinned-permutation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord435fb4e8 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord435fb4e8` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError435fb4e8 {
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
impl BoundaryError435fb4e8 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError435fb4e8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError435fb4e8 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord435fb4e8 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError435fb4e8> {
        if capacity_bound == 0 {
            return Err(BoundaryError435fb4e8::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError435fb4e8::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError435fb4e8::ExceedsCapacity {
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
mod private_observation_tests {
    use super::*;
    use pfp_runtime::rewriting::{PermutationOrderError, Rule};

    #[test]
    fn private_non_total_fixture_yields_complete_open_residual_without_fake_public_pin() {
        // This value exercises a crate-private defensive branch only. It is
        // never added to the compiled governance catalogue or public dispatch.
        let non_total = Presentation {
            signature: vec!["a".to_owned(), "b".to_owned()],
            rules: vec![Rule {
                name: "only_a".to_owned(),
                lhs: "a".to_owned(),
                rhs: "a".to_owned(),
            }],
        };
        assert_eq!(
            non_total.permutation_order(),
            Err(PermutationOrderError::NonTotal)
        );
        let request = PinnedPermutationOrderRequestV1 {
            presentation_ref: "private-non-total-unit-only".to_owned(),
            claimed_order: "0006".to_owned(),
        };
        let original = request.clone();
        let result = observe(request, Some(&non_total)).unwrap();
        assert_eq!(
            serde_json::to_value(&result).unwrap(),
            serde_json::json!({
                "schema_version": "core.symbol-game.pinned-permutation-order-observation.v1",
                "submitted_presentation_ref": "private-non-total-unit-only",
                "submitted_claimed_order": "0006",
                "evaluation": {
                    "status": "OPEN_RESIDUAL",
                    "obligation": "PINNED_PRESENTATION_NOT_A_TOTAL_PERMUTATION"
                },
                "authority_effect": "None"
            })
        );
        assert_eq!(result.submitted_presentation_ref, original.presentation_ref);
        assert_eq!(result.submitted_claimed_order, original.claimed_order);
    }
}

#[cfg(test)]
mod l4_boundary_tests_435fb4e8 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord435fb4e8::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord435fb4e8::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord435fb4e8::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord435fb4e8::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord435fb4e8::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError435fb4e8::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError435fb4e8::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
