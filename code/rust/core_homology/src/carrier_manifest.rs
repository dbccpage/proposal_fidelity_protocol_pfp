//! Carrier manifest: serializable evidence of carrier identity.

use crate::carrier::Carrier;
use crate::errors::HomologicalError;
use crate::hashing::{
    hash_carrier_manifest, hash_cochain_witness, hash_matrix, hash_weights, Hash256,
};
use serde::{Deserialize, Serialize};

/// The manifest schema version currently emitted.
///
/// **v1 → v2 (ADR-001).** v1 carried a single `coefficient_semantics: "Rational64"`
/// string that conflated two different things: the mathematical domain the
/// coefficients live in, and the machine representation carrying them. Under
/// ADR-001 the representation widened to `BigRational` while the domain stayed ℚ,
/// so a single field can no longer describe the carrier honestly. v2 splits them.
///
/// A v1 record is **not** comparable to a v2 manifest of the same carrier, and
/// worse, v1 does not say which side of the transition it is on: at the merged
/// base `hash_carrier_manifest` already appended `b"BigRational"` under the v1
/// tag, so v1 was emitted both before and after the representation widened.
/// [`CarrierManifest::from_slice`] therefore refuses v1 as ambiguous rather than
/// reinterpreting it.
pub const CARRIER_MANIFEST_VERSION: u32 = 2;

/// The mathematical domain the carrier's coefficients live in.
///
/// Distinct from [`CarrierManifest::coefficient_representation`]: widening the
/// representation from `Ratio<i64>` to `Ratio<BigInt>` does **not** change the
/// domain — both represent ℚ. Recording only one of the two is what made the v1
/// receipt false after ADR-001.
pub const COEFFICIENT_DOMAIN: &str = "Q";

/// The machine representation carrying those coefficients.
pub const COEFFICIENT_REPRESENTATION: &str = "BigRational";

/// A verified manifest identifying a specific carrier configuration.
///
/// # Why the fields are private and there is no `Deserialize`
///
/// A manifest is a **receipt**: downstream code reads
/// [`Self::coefficient_representation`] and treats it as a fact about the carrier.
/// If the type could be deserialized directly, that fact would be whatever the
/// bytes said. Constructing one with `coefficient_representation: "Rational64"`
/// while every hash in it was computed over `BigRational` would produce a receipt
/// that is internally consistent to every consumer and false.
///
/// So the only two ways to obtain this type are [`Self::from_carrier`], which
/// computes every field, and [`Self::from_slice`], which parses into a private
/// unverified wire form and then checks it. Deriving `Deserialize` here would
/// reopen exactly the hole the v1 → v2 split was made to close.
///
/// ```compile_fail
/// # use core_homology::carrier_manifest::CarrierManifest;
/// // There is deliberately no `Deserialize` impl: the verified type cannot be
/// // conjured from bytes, only from a carrier or through the checked parser.
/// let _: CarrierManifest = serde_json::from_str("{}").unwrap();
/// ```
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct CarrierManifest {
    manifest_version: u32,
    carrier_hash: Hash256,
    d0_hash: Hash256,
    d1_hash: Hash256,
    weights_hash: Hash256,
    witness_hash: Hash256,
    provenance_hash: Hash256,
    /// The mathematical domain — ℚ. Unchanged by ADR-001.
    coefficient_domain: String,
    /// The machine representation — `BigRational` since ADR-001.
    coefficient_representation: String,
    c0_dim: usize,
    c1_dim: usize,
    c2_dim: usize,
    rank_d0: usize,
    dim_q1: usize,
    dim_h1: usize,
}

/// The unverified wire form. Private, and never handed to a caller.
///
/// Field names and order mirror [`CarrierManifest`]'s `Serialize` output so a
/// round trip is byte-identical. Nothing may read this directly — every field is
/// attacker-controlled until [`CarrierManifest::from_slice`] has checked it.
#[derive(Deserialize)]
struct CarrierManifestWire {
    manifest_version: u32,
    carrier_hash: Hash256,
    d0_hash: Hash256,
    d1_hash: Hash256,
    weights_hash: Hash256,
    witness_hash: Hash256,
    provenance_hash: Hash256,
    coefficient_domain: String,
    coefficient_representation: String,
    c0_dim: usize,
    c1_dim: usize,
    c2_dim: usize,
    rank_d0: usize,
    dim_q1: usize,
    dim_h1: usize,
}

impl CarrierManifest {
    /// The schema version this record was verified against.
    pub fn manifest_version(&self) -> u32 {
        self.manifest_version
    }
    /// Hash binding the dimensions, boundary maps, weights, domain and
    /// representation together. Recomputed and compared by [`Self::from_slice`].
    pub fn carrier_hash(&self) -> &Hash256 {
        &self.carrier_hash
    }
    pub fn d0_hash(&self) -> &Hash256 {
        &self.d0_hash
    }
    pub fn d1_hash(&self) -> &Hash256 {
        &self.d1_hash
    }
    pub fn weights_hash(&self) -> &Hash256 {
        &self.weights_hash
    }
    pub fn witness_hash(&self) -> &Hash256 {
        &self.witness_hash
    }
    pub fn provenance_hash(&self) -> &Hash256 {
        &self.provenance_hash
    }
    /// The mathematical domain — always [`COEFFICIENT_DOMAIN`] for an accepted
    /// record.
    pub fn coefficient_domain(&self) -> &str {
        &self.coefficient_domain
    }
    /// The machine representation — always [`COEFFICIENT_REPRESENTATION`] for an
    /// accepted record.
    pub fn coefficient_representation(&self) -> &str {
        &self.coefficient_representation
    }
    pub fn c0_dim(&self) -> usize {
        self.c0_dim
    }
    pub fn c1_dim(&self) -> usize {
        self.c1_dim
    }
    pub fn c2_dim(&self) -> usize {
        self.c2_dim
    }
    pub fn rank_d0(&self) -> usize {
        self.rank_d0
    }
    pub fn dim_q1(&self) -> usize {
        self.dim_q1
    }
    pub fn dim_h1(&self) -> usize {
        self.dim_h1
    }
}

/// Why a stored manifest could not be accepted.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ManifestCompatibilityError {
    /// A v1 manifest cannot be interpreted, because v1 spans a representation
    /// change that its own version number does not distinguish.
    ///
    /// This variant was previously named `PreAdr001` and claimed v1 hashes were
    /// computed under `Rational64` tags. **That was false.** At the merged base
    /// `hash_carrier_manifest` already appended `b"BigRational"` under the v1 tag,
    /// so a v1 record may have been written either before the widening (a
    /// `Rational64` payload) or after it but before the manifest split (a
    /// `BigRational` payload). The version number does not say which, and no
    /// amount of inspection recovers it — which is precisely why v1 is refused
    /// rather than migrated.
    #[error(
        "carrier manifest v{found} is ambiguous across the ADR-001 transition (current \
         v{current}): v1 was emitted both before and after the representation widened, and \
         the record does not say which; recompute from the carrier rather than migrating it"
    )]
    AmbiguousLegacyV1 { found: u32, current: u32 },

    /// A version this build does not know about.
    #[error("unknown carrier manifest version {found} (current v{current})")]
    UnknownVersion { found: u32, current: u32 },

    /// The record declares a coefficient domain this build does not compute in.
    #[error("carrier manifest declares coefficient domain {found:?}, expected {expected:?}")]
    DomainMismatch { found: String, expected: String },

    /// The record declares a machine representation this build does not compute in.
    /// Accepting it would let a caller read `Rational64` off a receipt whose hashes
    /// were taken over `BigRational`.
    #[error(
        "carrier manifest declares coefficient representation {found:?}, expected \
         {expected:?}; the hashes in this record were not computed in {found:?}"
    )]
    RepresentationMismatch { found: String, expected: String },

    /// `carrier_hash` does not match a recomputation from the record's own fields,
    /// so at least one of them was altered after the hash was taken.
    #[error(
        "carrier manifest hash mismatch: recorded {recorded}, recomputed {recomputed} from \
         the record's own dimensions, boundary-map hashes and weights hash"
    )]
    CarrierHashMismatch {
        recorded: String,
        recomputed: String,
    },

    #[error("malformed manifest: {0}")]
    Malformed(String),
}

impl CarrierManifest {
    /// Compute the manifest for a given carrier.
    pub fn from_carrier(carrier: &Carrier) -> Result<Self, HomologicalError> {
        let d0_hash = hash_matrix(carrier.d0());
        let d1_hash = hash_matrix(carrier.d1());
        let weights_hash = hash_weights(carrier.weights());
        let provenance_hash = carrier.complex().witness.provenance_hash.clone();
        let witness_hash = hash_cochain_witness(
            carrier.complex().witness.d0_shape,
            carrier.complex().witness.d1_shape,
            &provenance_hash,
        );

        let carrier_hash = hash_carrier_manifest(
            carrier.c0_dim(),
            carrier.c1_dim(),
            carrier.c2_dim(),
            &d0_hash,
            &d1_hash,
            &weights_hash,
        );

        let rank_d0 = carrier.rank_d0()?;
        let dim_q1 = carrier.dim_q1()?;
        let dim_h1 = carrier.dim_h1()?;

        Ok(Self {
            manifest_version: CARRIER_MANIFEST_VERSION,
            carrier_hash,
            d0_hash,
            d1_hash,
            weights_hash,
            witness_hash,
            provenance_hash,
            coefficient_domain: COEFFICIENT_DOMAIN.to_string(),
            coefficient_representation: COEFFICIENT_REPRESENTATION.to_string(),
            c0_dim: carrier.c0_dim(),
            c1_dim: carrier.c1_dim(),
            c2_dim: carrier.c2_dim(),
            rank_d0,
            dim_q1,
            dim_h1,
        })
    }

    /// Parse and **verify** a stored manifest.
    ///
    /// Parsing alone is not acceptance. The wire form is attacker-controlled, so
    /// four things are checked before a [`CarrierManifest`] exists at all:
    ///
    /// 1. **Version** is exactly [`CARRIER_MANIFEST_VERSION`]. v1 is refused as
    ///    [`ManifestCompatibilityError::AmbiguousLegacyV1`] — never migrated.
    /// 2. **Domain** equals [`COEFFICIENT_DOMAIN`].
    /// 3. **Representation** equals [`COEFFICIENT_REPRESENTATION`]. Without this,
    ///    a record could declare `Rational64` while carrying hashes taken over
    ///    `BigRational`, and every consumer downstream would believe the label.
    /// 4. **`carrier_hash` is recomputed** from the record's own dimensions,
    ///    boundary-map hashes and weights hash, and compared. This is what makes
    ///    (2) and (3) load-bearing rather than cosmetic: an attacker who edits a
    ///    dimension or a component hash to match a forged label still fails here.
    ///
    /// The recomputation is *internal consistency*, not proof that the record
    /// describes any particular carrier — for that, compare against
    /// [`Self::from_carrier`] on the carrier in hand.
    pub fn from_slice(bytes: &[u8]) -> Result<Self, ManifestCompatibilityError> {
        let wire: CarrierManifestWire = serde_json::from_slice(bytes)
            .map_err(|e| ManifestCompatibilityError::Malformed(e.to_string()))?;

        match wire.manifest_version {
            CARRIER_MANIFEST_VERSION => {}
            1 => {
                return Err(ManifestCompatibilityError::AmbiguousLegacyV1 {
                    found: 1,
                    current: CARRIER_MANIFEST_VERSION,
                })
            }
            other => {
                return Err(ManifestCompatibilityError::UnknownVersion {
                    found: other,
                    current: CARRIER_MANIFEST_VERSION,
                })
            }
        }

        if wire.coefficient_domain != COEFFICIENT_DOMAIN {
            return Err(ManifestCompatibilityError::DomainMismatch {
                found: wire.coefficient_domain,
                expected: COEFFICIENT_DOMAIN.to_string(),
            });
        }
        if wire.coefficient_representation != COEFFICIENT_REPRESENTATION {
            return Err(ManifestCompatibilityError::RepresentationMismatch {
                found: wire.coefficient_representation,
                expected: COEFFICIENT_REPRESENTATION.to_string(),
            });
        }

        // `hash_carrier_manifest` folds in the domain and representation constants
        // of THIS build, so the checks above and this recomputation reinforce each
        // other: the labels must match the constants, and the hash must match the
        // structure those constants were folded into.
        let recomputed = hash_carrier_manifest(
            wire.c0_dim,
            wire.c1_dim,
            wire.c2_dim,
            &wire.d0_hash,
            &wire.d1_hash,
            &wire.weights_hash,
        );
        if recomputed != wire.carrier_hash {
            return Err(ManifestCompatibilityError::CarrierHashMismatch {
                recorded: wire.carrier_hash.to_hex(),
                recomputed: recomputed.to_hex(),
            });
        }

        Ok(Self {
            manifest_version: wire.manifest_version,
            carrier_hash: wire.carrier_hash,
            d0_hash: wire.d0_hash,
            d1_hash: wire.d1_hash,
            weights_hash: wire.weights_hash,
            witness_hash: wire.witness_hash,
            provenance_hash: wire.provenance_hash,
            coefficient_domain: wire.coefficient_domain,
            coefficient_representation: wire.coefficient_representation,
            c0_dim: wire.c0_dim,
            c1_dim: wire.c1_dim,
            c2_dim: wire.c2_dim,
            rank_d0: wire.rank_d0,
            dim_q1: wire.dim_q1,
            dim_h1: wire.dim_h1,
        })
    }
}

// Origin: engine/crates_rs/core_homology/src/carrier_manifest.rs
// Claim: urn:core:crates_rs:core-homology:carrier-manifest:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod adr001_manifest_tests {
    use super::*;
    use crate::finite_directed_graph::{DirectedGraphBuilder, TheoremProvenance as GraphProv};
    use crate::graph_carrier::graph_carrier;
    use crate::scalar::q;

    fn triangle_carrier() -> Carrier {
        let gp = GraphProv {
            verification_source: "manifest_test".to_string(),
        };
        let g = DirectedGraphBuilder::from_anonymous(3, vec![(0, 1), (1, 2), (0, 2)], gp).unwrap();
        let prov =
            crate::cochain_complex::TheoremProvenance::new("manifest_test".to_string()).unwrap();
        graph_carrier(&g, &[(0, 1, 2)], vec![q(1); 3], prov).unwrap()
    }

    /// Serialize, tamper with one field, reserialize.
    fn tampered(field: &str, value: serde_json::Value) -> Vec<u8> {
        let m = CarrierManifest::from_carrier(&triangle_carrier()).unwrap();
        let mut json: serde_json::Value = serde_json::to_value(&m).unwrap();
        assert!(
            json.get(field).is_some(),
            "test premise broken — {field} is not a wire field"
        );
        json[field] = value;
        serde_json::to_vec(&json).unwrap()
    }

    /// The receipt must name the domain that is actually in use. Before this change
    /// it said "Rational64" while `Q` was `BigRational` — a false authority receipt.
    #[test]
    fn manifest_declares_the_representation_actually_in_use() {
        let m = CarrierManifest::from_carrier(&triangle_carrier()).unwrap();
        assert_eq!(m.manifest_version(), 2);
        assert_eq!(m.coefficient_domain(), "Q");
        assert_eq!(m.coefficient_representation(), "BigRational");
        assert_ne!(
            m.coefficient_representation(),
            "Rational64",
            "the v1 receipt claimed Rational64 after the widening; that must not recur"
        );
    }

    /// Domain and representation are separate fields precisely because ADR-001
    /// changed one without changing the other.
    #[test]
    fn domain_and_representation_are_distinct_fields() {
        let m = CarrierManifest::from_carrier(&triangle_carrier()).unwrap();
        assert_ne!(
            m.coefficient_domain(),
            m.coefficient_representation(),
            "conflating these is what made v1 false; they must stay separable"
        );
    }

    /// **The forgery the previous version of this parser accepted.** Relabelling the
    /// representation left `carrier_hash` untouched, because the hash folds in this
    /// build's constants rather than the parsed strings — so the record stayed
    /// internally consistent to every downstream consumer, and false.
    #[test]
    fn relabelled_representation_is_refused() {
        let bytes = tampered(
            "coefficient_representation",
            serde_json::json!("Rational64"),
        );
        match CarrierManifest::from_slice(&bytes) {
            Err(ManifestCompatibilityError::RepresentationMismatch { found, expected }) => {
                assert_eq!(found, "Rational64");
                assert_eq!(expected, "BigRational");
            }
            other => panic!("a relabelled receipt must be refused, got {other:?}"),
        }
    }

    #[test]
    fn relabelled_domain_is_refused() {
        let bytes = tampered("coefficient_domain", serde_json::json!("R"));
        assert!(matches!(
            CarrierManifest::from_slice(&bytes),
            Err(ManifestCompatibilityError::DomainMismatch { .. })
        ));
    }

    /// The hash recomputation is what stops a forger who edits the *structure* to
    /// match a label rather than the label to match the structure.
    #[test]
    fn edited_dimension_is_caught_by_the_hash_recomputation() {
        let bytes = tampered("c1_dim", serde_json::json!(99));
        match CarrierManifest::from_slice(&bytes) {
            Err(ManifestCompatibilityError::CarrierHashMismatch {
                recorded,
                recomputed,
            }) => assert_ne!(recorded, recomputed),
            other => panic!("expected a hash mismatch, got {other:?}"),
        }
    }

    #[test]
    fn edited_component_hash_is_caught_by_the_hash_recomputation() {
        let bytes = tampered("d0_hash", serde_json::to_value([7u8; 32]).unwrap());
        assert!(matches!(
            CarrierManifest::from_slice(&bytes),
            Err(ManifestCompatibilityError::CarrierHashMismatch { .. })
        ));
    }

    #[test]
    fn forged_carrier_hash_is_refused() {
        let bytes = tampered("carrier_hash", serde_json::to_value([0u8; 32]).unwrap());
        assert!(matches!(
            CarrierManifest::from_slice(&bytes),
            Err(ManifestCompatibilityError::CarrierHashMismatch { .. })
        ));
    }

    /// A v1 record is refused rather than reinterpreted — and the reason is
    /// ambiguity, not a known-wrong tag. See [`ManifestCompatibilityError`].
    #[test]
    fn v1_manifest_is_refused_as_ambiguous_not_migrated() {
        let bytes = tampered("manifest_version", serde_json::json!(1));
        match CarrierManifest::from_slice(&bytes) {
            Err(ManifestCompatibilityError::AmbiguousLegacyV1 {
                found: 1,
                current: 2,
            }) => {}
            other => panic!("expected a typed v1 refusal, got {other:?}"),
        }
    }

    #[test]
    fn unknown_future_version_is_refused() {
        let bytes = tampered("manifest_version", serde_json::json!(99));
        assert!(matches!(
            CarrierManifest::from_slice(&bytes),
            Err(ManifestCompatibilityError::UnknownVersion { found: 99, .. })
        ));
    }

    /// The version gate runs before the field checks, so a v1 record does not get
    /// to fail on a label instead — the refusal names the real problem.
    #[test]
    fn version_is_checked_before_the_field_labels() {
        let m = CarrierManifest::from_carrier(&triangle_carrier()).unwrap();
        let mut json: serde_json::Value = serde_json::to_value(&m).unwrap();
        json["manifest_version"] = serde_json::json!(1);
        json["coefficient_representation"] = serde_json::json!("Rational64");
        let bytes = serde_json::to_vec(&json).unwrap();
        assert!(matches!(
            CarrierManifest::from_slice(&bytes),
            Err(ManifestCompatibilityError::AmbiguousLegacyV1 { .. })
        ));
    }

    #[test]
    fn current_version_round_trips() {
        let m = CarrierManifest::from_carrier(&triangle_carrier()).unwrap();
        let bytes = serde_json::to_vec(&m).unwrap();
        assert_eq!(CarrierManifest::from_slice(&bytes).unwrap(), m);
    }

    /// The wire form must stay field-for-field identical to what the verified type
    /// serializes, or the checked parser silently stops seeing part of the record.
    #[test]
    fn wire_form_covers_every_serialized_field() {
        let m = CarrierManifest::from_carrier(&triangle_carrier()).unwrap();
        let json: serde_json::Value = serde_json::to_value(&m).unwrap();
        let emitted: Vec<&String> = json.as_object().unwrap().keys().collect();

        // Dropping any single field must make the wire parse fail, which is only
        // true if the DTO requires all of them.
        for key in &emitted {
            let mut trimmed = json.clone();
            trimmed.as_object_mut().unwrap().remove(key.as_str());
            let bytes = serde_json::to_vec(&trimmed).unwrap();
            assert!(
                matches!(
                    CarrierManifest::from_slice(&bytes),
                    Err(ManifestCompatibilityError::Malformed(_))
                ),
                "dropping {key} was tolerated — the wire DTO has drifted from the \
                 serialized form and no longer checks that field"
            );
        }
        assert_eq!(emitted.len(), 15, "field count changed; revisit the checks");
    }
}
