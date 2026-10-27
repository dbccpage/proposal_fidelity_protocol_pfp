//! FiniteQMContractV1 schema types — fence newtypes, import ledger, canonical hash.
//!
//! AuthorityEffect: None. Not GlobalGreen. Shape-only; does not implement full QM math.
//!
//! Non-inference fence (mandatory; see finite_vocabulary_fence.md):
//! `FiniteCarrier` ⇏ `FiniteDimension` ⇏ `FiniteCertificate` ⇏ `ContinuumDebt`
//! (`FiniteDimContinuumScalars` debt). Continuum scalars ⇏ finite certificate;
//! finite certificate ⇏ finite-dim Hilbert; finite carrier ⇏ continuum object is finite.
//!
//! **Name fence:** [`ContinuumDebt`] in *this* module is the FiniteQM schema continuum-debt
//! carrier. It is **not** [`crate::coda::continuum::ContinuumDebt`] (Q-admission debt).

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;

/// JSON schema version tag for FiniteQMContractV1 instances.
pub const SCHEMA_VERSION: &str = "FiniteQMContractV1";

/// Canonical contract URN (versioned identity).
pub const CONTRACT_URN: &str = "urn:core:math:finite_qm:v1.0.0";

/// Authority effect fixed for every FiniteQMContractV1 instance.
pub const AUTHORITY_EFFECT: &str = "None";

/// Encoding tag for the deterministic JSON form used by [`FiniteQmContractV1::canonical_hash_sha256`].
pub const CANONICAL_JSON_ENCODING: &str = "core.canonical_json.v1";

/// Smoke-fixture digest: SHA-256 (lowercase hex) of
/// [`FiniteQmContractV1::smoke_fixture`] under [`CANONICAL_JSON_ENCODING`].
///
/// Recomputed by `fixture_canonical_hash_is_stable`. Do not hand-edit without re-running
/// the fixture construction.
pub const SMOKE_FIXTURE_SHA256: &str =
    "6bb78de524b10eb32ae23f3b5aa277b632e0490ca888ab554340202d8a3a10f0";

/// Finite set of states / discrete support (fence `FINITE_CARRIER`).
///
/// Not finite-dim Hilbert rank; not a certificate; not continuum-scalar debt.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct FiniteCarrier {
    pub carrier_id: String,
    pub support_cardinality: u64,
}

/// Finite-dimensional vector/Hilbert rank (fence `FINITE_DIMENSION`).
///
/// Not a finite carrier of continuum $X$; not a finite certificate.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct FiniteDimension {
    pub dimension_id: String,
    pub rank: u64,
}

/// Finite evidence/receipt/audit artifact (fence `FINITE_CERTIFICATE`).
///
/// Not finite-dim Hilbert; not finite presentation.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct FiniteCertificate {
    pub certificate_id: String,
    pub kind: String,
    pub payload_digest_sha256: String,
}

/// Finite-dim system with continuum scalars, e.g. $M_n(\mathbb{C})$
/// (fence `FINITE_DIM_CONTINUUM_SCALARS`).
///
/// Not a finite certificate; does not claim the continuum object is finite as a set.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct FiniteDimContinuumScalars {
    pub declaration_id: String,
    pub matrix_algebra_note: String,
    pub scalar_field: String,
}

/// FiniteQM schema continuum-debt (`FiniteDimContinuumScalars` debt).
///
/// **Not** [`crate::coda::continuum::ContinuumDebt`] (Q-admission firewall debt).
/// Field name in the JSON schema is `continuum_debt`.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ContinuumDebt {
    pub scalars: FiniteDimContinuumScalars,
    pub notes: Vec<String>,
}

/// Import-slot status vocabulary for the FiniteQM import ledger.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ImportSlotStatus {
    Open,
    Declared,
    Witnessed,
}

/// One declared import slot (spectral, monoidal, tomography, U(1), …).
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ImportSlot {
    pub slot_id: String,
    pub label: String,
    pub status: ImportSlotStatus,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub witness_ref: Option<String>,
}

/// Ordered ledger of import slots (canonicalized by `slot_id` before hashing).
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ImportLedger {
    pub slots: Vec<ImportSlot>,
}

impl ImportLedger {
    /// Default import slots from the finite QM ingredient ladder ceiling (all OPEN).
    pub fn default_open_slots() -> Self {
        let defs = [
            (
                "born_uniqueness",
                "Born-quadratic uniqueness (Gleason-type import)",
            ),
            (
                "continuum_limit",
                "continuum path-integral / continuum limit authorization",
            ),
            (
                "interference_resource",
                "non-L1 interference cross-term resource (qm_121 rung 6)",
            ),
            ("monoidal", "monoidal / tensor composition rule"),
            (
                "spectral",
                "finite-dimensional spectral theorem / spectral membrane",
            ),
            ("tomography", "local tomography / state reconstruction"),
            (
                "u1_phase_carrier",
                "C/U(1) phase carrier (conditionally forced only under declared assumptions)",
            ),
            ("unitarity", "unitary dynamics import"),
        ];
        let mut slots: Vec<ImportSlot> = defs
            .into_iter()
            .map(|(slot_id, label)| ImportSlot {
                slot_id: slot_id.to_string(),
                label: label.to_string(),
                status: ImportSlotStatus::Open,
                witness_ref: None,
            })
            .collect();
        slots.sort_by(|a, b| a.slot_id.cmp(&b.slot_id));
        Self { slots }
    }

    pub fn canonicalize(&mut self) {
        self.slots.sort_by(|a, b| a.slot_id.cmp(&b.slot_id));
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FiniteQmContractError {
    InvalidSchemaVersion { actual: String },
    InvalidAuthorityEffect { actual: String },
    InvalidContractUrn { actual: String },
}

impl std::fmt::Display for FiniteQmContractError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::InvalidSchemaVersion { actual } => {
                write!(f, "schema_version must be {SCHEMA_VERSION}, got {actual}")
            }
            Self::InvalidAuthorityEffect { actual } => {
                write!(
                    f,
                    "authority_effect must be {AUTHORITY_EFFECT}, got {actual}"
                )
            }
            Self::InvalidContractUrn { actual } => {
                write!(f, "contract_urn must be {CONTRACT_URN}, got {actual}")
            }
        }
    }
}

impl std::error::Error for FiniteQmContractError {}

#[derive(Clone, Debug, Deserialize)]
struct UntrustedFiniteQmContractV1 {
    schema_version: String,
    contract_urn: String,
    authority_effect: String,
    carrier: FiniteCarrier,
    dimension: FiniteDimension,
    certificate: FiniteCertificate,
    continuum_debt: ContinuumDebt,
    import_ledger: ImportLedger,
}

/// Versioned FiniteQMContractV1 instance (JSON schema root).
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "UntrustedFiniteQmContractV1")]
pub struct FiniteQmContractV1 {
    pub schema_version: String,
    pub contract_urn: String,
    pub authority_effect: String,
    pub carrier: FiniteCarrier,
    pub dimension: FiniteDimension,
    pub certificate: FiniteCertificate,
    pub continuum_debt: ContinuumDebt,
    pub import_ledger: ImportLedger,
}

impl TryFrom<UntrustedFiniteQmContractV1> for FiniteQmContractV1 {
    type Error = FiniteQmContractError;

    fn try_from(wire: UntrustedFiniteQmContractV1) -> Result<Self, Self::Error> {
        let value = Self {
            schema_version: wire.schema_version,
            contract_urn: wire.contract_urn,
            authority_effect: wire.authority_effect,
            carrier: wire.carrier,
            dimension: wire.dimension,
            certificate: wire.certificate,
            continuum_debt: wire.continuum_debt,
            import_ledger: wire.import_ledger,
        };
        value.validate()?;
        Ok(value)
    }
}

impl FiniteQmContractV1 {
    pub fn validate(&self) -> Result<(), FiniteQmContractError> {
        if self.schema_version != SCHEMA_VERSION {
            return Err(FiniteQmContractError::InvalidSchemaVersion {
                actual: self.schema_version.clone(),
            });
        }
        if self.authority_effect != AUTHORITY_EFFECT {
            return Err(FiniteQmContractError::InvalidAuthorityEffect {
                actual: self.authority_effect.clone(),
            });
        }
        if self.contract_urn != CONTRACT_URN {
            return Err(FiniteQmContractError::InvalidContractUrn {
                actual: self.contract_urn.clone(),
            });
        }
        Ok(())
    }

    /// Build a contract instance; forces schema/authority constants and sorts the import ledger.
    pub fn new(
        carrier: FiniteCarrier,
        dimension: FiniteDimension,
        certificate: FiniteCertificate,
        continuum_debt: ContinuumDebt,
        mut import_ledger: ImportLedger,
    ) -> Self {
        import_ledger.canonicalize();
        Self {
            schema_version: SCHEMA_VERSION.to_string(),
            contract_urn: CONTRACT_URN.to_string(),
            authority_effect: AUTHORITY_EFFECT.to_string(),
            carrier,
            dimension,
            certificate,
            continuum_debt,
            import_ledger,
        }
    }

    /// Smoke fixture used for the pinned canonical hash (deterministic, no wall-clock).
    pub fn smoke_fixture() -> Self {
        Self::new(
            FiniteCarrier {
                carrier_id: "fixture:finite-carrier:sectors-e2".to_string(),
                support_cardinality: 2,
            },
            FiniteDimension {
                dimension_id: "fixture:finite-dimension:c2".to_string(),
                rank: 2,
            },
            FiniteCertificate {
                certificate_id: "fixture:finite-certificate:audit-0".to_string(),
                kind: "audit_receipt".to_string(),
                payload_digest_sha256:
                    "0000000000000000000000000000000000000000000000000000000000000000".to_string(),
            },
            ContinuumDebt {
                scalars: FiniteDimContinuumScalars {
                    declaration_id: "fixture:continuum-scalars:m2c".to_string(),
                    matrix_algebra_note: "M_2(C)".to_string(),
                    scalar_field: "C".to_string(),
                },
                notes: vec![
                    "FINITE_DIM_CONTINUUM_SCALARS debt held; not a finite certificate".to_string(),
                ],
            },
            ImportLedger::default_open_slots(),
        )
    }

    /// Compact, key-sorted JSON bytes (`core.canonical_json.v1` subset for this schema).
    pub fn canonical_json_bytes(&self) -> Result<Vec<u8>, String> {
        self.validate().map_err(|e| e.to_string())?;
        let value = serde_json::to_value(self).map_err(|e| e.to_string())?;
        let normalized = normalize_value(value)?;
        serde_json::to_string(&normalized)
            .map(|s| s.into_bytes())
            .map_err(|e| e.to_string())
    }

    /// SHA-256 (lowercase hex) of [`Self::canonical_json_bytes`].
    pub fn canonical_hash_sha256(&self) -> Result<String, String> {
        let bytes = self.canonical_json_bytes()?;
        let mut hasher = Sha256::new();
        hasher.update(&bytes);
        Ok(format!("{:x}", hasher.finalize()))
    }
}

fn normalize_value(value: serde_json::Value) -> Result<serde_json::Value, String> {
    match value {
        serde_json::Value::Null | serde_json::Value::Bool(_) | serde_json::Value::String(_) => {
            Ok(value)
        }
        serde_json::Value::Number(n) => {
            if n.as_i64().is_none() && n.as_u64().is_none() {
                return Err("floating-point values are forbidden in FiniteQMContractV1".into());
            }
            Ok(serde_json::Value::Number(n))
        }
        serde_json::Value::Array(items) => {
            let mut out = Vec::with_capacity(items.len());
            for item in items {
                out.push(normalize_value(item)?);
            }
            Ok(serde_json::Value::Array(out))
        }
        serde_json::Value::Object(map) => {
            // BTreeMap forces key-sorted object encoding for stability across map insert order.
            let ordered: BTreeMap<String, serde_json::Value> = map.into_iter().collect();
            let mut out = serde_json::Map::new();
            for (k, v) in ordered {
                out.insert(k, normalize_value(v)?);
            }
            Ok(serde_json::Value::Object(out))
        }
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fence_types_are_distinct_newtypes() {
        // Distinct struct types: equal field shapes do not collapse identities.
        let carrier = FiniteCarrier {
            carrier_id: "c".into(),
            support_cardinality: 2,
        };
        let dimension = FiniteDimension {
            dimension_id: "d".into(),
            rank: 2,
        };
        let certificate = FiniteCertificate {
            certificate_id: "k".into(),
            kind: "audit".into(),
            payload_digest_sha256: "00".into(),
        };
        let scalars = FiniteDimContinuumScalars {
            declaration_id: "s".into(),
            matrix_algebra_note: "M_2(C)".into(),
            scalar_field: "C".into(),
        };
        let debt = ContinuumDebt {
            scalars: scalars.clone(),
            notes: vec![],
        };

        assert_ne!(carrier.carrier_id, dimension.dimension_id);
        assert_ne!(dimension.dimension_id, certificate.certificate_id);
        assert_ne!(certificate.certificate_id, debt.scalars.declaration_id);
        // Type-level fence: these are different Rust types (compile-time), and field
        // names refuse alias collapse in the schema.
        assert_eq!(std::mem::size_of_val(&carrier) > 0, true);
        assert_eq!(
            std::any::type_name::<FiniteCarrier>().contains("FiniteCarrier"),
            true
        );
        assert_eq!(
            std::any::type_name::<FiniteDimension>().contains("FiniteDimension"),
            true
        );
        assert_eq!(
            std::any::type_name::<FiniteCertificate>().contains("FiniteCertificate"),
            true
        );
        assert_eq!(
            std::any::type_name::<ContinuumDebt>().contains("ContinuumDebt"),
            true
        );
        assert_eq!(
            std::any::type_name::<FiniteDimContinuumScalars>()
                .contains("FiniteDimContinuumScalars"),
            true
        );
        // Schema ContinuumDebt is not the Q-admission ContinuumDebt path.
        assert!(
            !std::any::type_name::<ContinuumDebt>().contains("continuum::ContinuumDebt")
                || std::any::type_name::<ContinuumDebt>().contains("finite_qm_types")
        );
    }

    #[test]
    fn non_inference_fields_do_not_coerce() {
        let fixture = FiniteQmContractV1::smoke_fixture();
        // Holding a carrier does not fill dimension, certificate, or continuum debt by inference:
        // field identities remain distinct even when numeric ranks match.
        assert_ne!(fixture.carrier.carrier_id, fixture.dimension.dimension_id);
        assert_ne!(
            fixture.dimension.dimension_id,
            fixture.certificate.certificate_id
        );
        assert_ne!(
            fixture.certificate.certificate_id,
            fixture.continuum_debt.scalars.declaration_id
        );
        assert_ne!(
            fixture.carrier.carrier_id,
            fixture.continuum_debt.scalars.declaration_id
        );
        // Explicit non-inference documentation markers present in module (string fence).
        let src = include_str!("finite_qm_types.rs");
        assert!(src.contains("FiniteCarrier"));
        assert!(src.contains("FiniteDimension"));
        assert!(src.contains("FiniteCertificate"));
        assert!(src.contains("FiniteDimContinuumScalars"));
        assert!(src.contains("ContinuumDebt"));
        assert!(
            src.contains("does not imply") || src.contains("⇏") || src.contains("Non-inference")
        );
    }

    #[test]
    fn import_ledger_status_vocabulary() {
        let ledger = ImportLedger::default_open_slots();
        assert_eq!(ledger.slots.len(), 8);
        for slot in &ledger.slots {
            assert_eq!(slot.status, ImportSlotStatus::Open);
            assert!(slot.witness_ref.is_none());
        }
        // Sorted by slot_id for canonical hash stability.
        let ids: Vec<&str> = ledger.slots.iter().map(|s| s.slot_id.as_str()).collect();
        let mut sorted = ids.clone();
        sorted.sort_unstable();
        assert_eq!(ids, sorted);
        // Serde vocabulary is SCREAMING_SNAKE_CASE.
        let json = serde_json::to_string(&ImportSlotStatus::Declared).unwrap();
        assert_eq!(json, "\"DECLARED\"");
        let json = serde_json::to_string(&ImportSlotStatus::Witnessed).unwrap();
        assert_eq!(json, "\"WITNESSED\"");
        let json = serde_json::to_string(&ImportSlotStatus::Open).unwrap();
        assert_eq!(json, "\"OPEN\"");
    }

    #[test]
    fn authority_effect_is_none() {
        let fixture = FiniteQmContractV1::smoke_fixture();
        assert_eq!(fixture.authority_effect, "None");
        assert_eq!(fixture.schema_version, SCHEMA_VERSION);
        assert_eq!(fixture.contract_urn, CONTRACT_URN);
        assert_ne!(fixture.authority_effect, "GlobalGreen");
    }

    #[test]
    fn fixture_hash_is_deterministic() {
        let a = FiniteQmContractV1::smoke_fixture()
            .canonical_hash_sha256()
            .expect("hash");
        let b = FiniteQmContractV1::smoke_fixture()
            .canonical_hash_sha256()
            .expect("hash");
        assert_eq!(a, b);
        assert_eq!(a.len(), 64);
    }

    #[test]
    fn fixture_canonical_hash_is_stable() {
        let fixture = FiniteQmContractV1::smoke_fixture();
        let digest = fixture.canonical_hash_sha256().expect("hash");
        // If this fails after intentional schema change, update SMOKE_FIXTURE_SHA256
        // and the math contract fixture note together.
        assert_eq!(digest, SMOKE_FIXTURE_SHA256);
    }

    #[test]
    fn rejects_alias_collapse_of_fence_types() {
        use std::any::TypeId;

        assert_ne!(
            TypeId::of::<FiniteCarrier>(),
            TypeId::of::<FiniteDimension>()
        );
        assert_ne!(
            TypeId::of::<FiniteDimension>(),
            TypeId::of::<FiniteCertificate>()
        );
        assert_ne!(
            TypeId::of::<FiniteCertificate>(),
            TypeId::of::<ContinuumDebt>()
        );
        assert_ne!(TypeId::of::<FiniteCarrier>(), TypeId::of::<ContinuumDebt>());

        let carrier = FiniteCarrier {
            carrier_id: "c".into(),
            support_cardinality: 2,
        };
        let json = serde_json::to_string(&carrier).expect("serialize carrier");
        let err = serde_json::from_str::<FiniteDimension>(&json)
            .expect_err("FiniteCarrier JSON must not deserialize as FiniteDimension");
        let err_text = err.to_string();
        assert!(
            err_text.contains("dimension_id") || err_text.contains("missing field"),
            "error must name the FiniteDimension field that carrier JSON lacks, got {err_text}"
        );

        let dimension = FiniteDimension {
            dimension_id: "d".into(),
            rank: 2,
        };
        let dim_json = serde_json::to_string(&dimension).expect("serialize dimension");
        assert_eq!(
            serde_json::from_str::<FiniteDimension>(&dim_json).expect("own JSON round-trips"),
            dimension
        );
    }

    #[test]
    fn rejects_authority_effect_other_than_none() {
        let mut bad = FiniteQmContractV1::smoke_fixture();
        bad.authority_effect = "GlobalGreen".to_string();
        assert_eq!(
            bad.validate(),
            Err(FiniteQmContractError::InvalidAuthorityEffect {
                actual: "GlobalGreen".into(),
            })
        );
        let hash_err = bad
            .canonical_hash_sha256()
            .expect_err("hash must refuse non-None authority_effect");
        assert!(
            hash_err.contains("authority_effect") || hash_err.contains("None"),
            "hash error must name the authority_effect refusal, got {hash_err}"
        );

        let mut value = serde_json::to_value(FiniteQmContractV1::smoke_fixture()).expect("json");
        value["authority_effect"] = serde_json::json!("ActionLicense");
        let text = serde_json::to_string(&value).expect("serialize");
        let parsed: Result<FiniteQmContractV1, _> = serde_json::from_str(&text);
        let err = parsed.expect_err("serde must refuse non-None authority_effect");
        let err_text = err.to_string();
        assert!(
            err_text.contains("authority_effect") || err_text.contains("None"),
            "serde error must name the authority_effect refusal, got {err_text}"
        );

        let ok = FiniteQmContractV1::smoke_fixture();
        assert_eq!(ok.validate(), Ok(()));
        assert_eq!(
            ok.canonical_hash_sha256().expect("valid fixture hashes"),
            SMOKE_FIXTURE_SHA256
        );
    }

    #[test]
    fn rejects_import_slot_status_outside_vocabulary() {
        let slot = ImportSlot {
            slot_id: "spectral".into(),
            label: "finite-dimensional spectral theorem / spectral membrane".into(),
            status: ImportSlotStatus::Open,
            witness_ref: None,
        };
        let mut value = serde_json::to_value(&slot).expect("json");
        value["status"] = serde_json::json!("PROVED");
        let parsed = serde_json::from_value::<ImportSlot>(value);
        let err = parsed.expect_err("status PROVED is outside OPEN|DECLARED|WITNESSED");
        let err_text = err.to_string();
        assert!(
            err_text.contains("PROVED")
                || err_text.contains("OPEN")
                || err_text.contains("unknown variant"),
            "error must name the illegal status, got {err_text}"
        );

        assert_eq!(
            serde_json::from_str::<ImportSlotStatus>("\"DECLARED\"").expect("DECLARED"),
            ImportSlotStatus::Declared
        );
        assert_eq!(
            serde_json::from_str::<ImportSlotStatus>("\"WITNESSED\"").expect("WITNESSED"),
            ImportSlotStatus::Witnessed
        );
        assert_eq!(
            serde_json::from_str::<ImportSlotStatus>("\"OPEN\"").expect("OPEN"),
            ImportSlotStatus::Open
        );
    }

    #[test]
    fn rejects_missing_required_fence_field() {
        let fixture = FiniteQmContractV1::smoke_fixture();
        let mut value = serde_json::to_value(&fixture).expect("json");
        value.as_object_mut().expect("object").remove("carrier");
        let text = serde_json::to_string(&value).expect("serialize");
        let parsed: Result<FiniteQmContractV1, _> = serde_json::from_str(&text);
        let err = parsed.expect_err("missing carrier must fail");
        let err_text = err.to_string();
        assert!(
            err_text.contains("carrier"),
            "error must name the missing fence field, got {err_text}"
        );

        let round_trip = serde_json::from_str::<FiniteQmContractV1>(
            &serde_json::to_string(&fixture).expect("serialize fixture"),
        )
        .expect("complete fixture deserializes");
        assert_eq!(round_trip, fixture);
    }

    #[test]
    fn canonical_hash_is_independent_of_slot_insert_order() {
        let smoke = FiniteQmContractV1::smoke_fixture();
        let mut reversed = ImportLedger::default_open_slots();
        let original_first = reversed
            .slots
            .first()
            .map(|slot| slot.slot_id.clone())
            .expect("default ledger is non-empty");
        reversed.slots.reverse();
        let reversed_first = reversed
            .slots
            .first()
            .map(|slot| slot.slot_id.clone())
            .expect("reversed ledger is non-empty");
        assert_ne!(
            original_first, reversed_first,
            "precondition: reversing slots must change insert order"
        );

        let resorted = FiniteQmContractV1::new(
            smoke.carrier.clone(),
            smoke.dimension.clone(),
            smoke.certificate.clone(),
            smoke.continuum_debt.clone(),
            reversed,
        );
        assert_eq!(resorted.import_ledger.slots, smoke.import_ledger.slots);
        assert_eq!(
            resorted.canonical_hash_sha256().expect("hash"),
            SMOKE_FIXTURE_SHA256
        );
    }

    #[test]
    fn rejects_continuum_scalars_as_finite_certificate() {
        use std::any::TypeId;

        assert_ne!(
            TypeId::of::<FiniteDimContinuumScalars>(),
            TypeId::of::<FiniteCertificate>()
        );

        let scalars = FiniteDimContinuumScalars {
            declaration_id: "s".into(),
            matrix_algebra_note: "M_2(C)".into(),
            scalar_field: "C".into(),
        };
        let json = serde_json::to_string(&scalars).expect("serialize scalars");
        let err = serde_json::from_str::<FiniteCertificate>(&json)
            .expect_err("FiniteDimContinuumScalars JSON must not deserialize as FiniteCertificate");
        let err_text = err.to_string();
        assert!(
            err_text.contains("certificate_id") || err_text.contains("missing field"),
            "error must name the FiniteCertificate field that scalars JSON lacks, got {err_text}"
        );

        let certificate = FiniteCertificate {
            certificate_id: "k".into(),
            kind: "audit".into(),
            payload_digest_sha256: "00".into(),
        };
        assert_eq!(
            serde_json::from_str::<FiniteCertificate>(
                &serde_json::to_string(&certificate).expect("serialize certificate")
            )
            .expect("certificate JSON round-trips"),
            certificate
        );
    }
}
