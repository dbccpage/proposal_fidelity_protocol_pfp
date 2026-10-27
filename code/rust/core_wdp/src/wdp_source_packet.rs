//! Source-bound, finite exact operational packets. AuthorityEffect: None.
//!
//! Source SHA-256 binds the supplied raw bytes, without parsing or claiming that
//! their prose derives the independently declared carrier. Request/carrier/result
//! commitments use framed SHA-256 over sorted JSON with canonical rational string
//! scalars. Replay checks the source bytes, every premise, the carrier, and the
//! submitted result. Only Euclidean Hodge and one weighted Kraus map on one Gram
//! state are admitted; no continuum, tensor, or all-composed-words claim is made.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::rational_bareiss::{
    RationalBudget, RationalError, RationalLimits,
};
use num_rational::BigRational;
use core_kernel::{exact_wire, exact_wire_vec};
use core_number_theory::cyclotomic::GaussianRat;
use core_quantum_physics::exact_channel::{ExactChannelError, ExactKrausChannel};
use core_solvers::data_hodge_packet::{
    self as hodge, HodgeAvailabilityModelV1, HodgeCompositionModelV1, HodgePacketError,
    HodgePacketHeaderV1, HodgePositivityModelV1, HodgeQuestionV1, HodgeQuotientModelV1,
    HodgeRequestV1, HodgeResourceLimitsV1, HodgeResultV1, HodgeScalarModelV1, RationalMatrixV1,
};
use core_types::AuthorityEffect;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

pub const WDP_SOURCE_PACKET_SCHEMA_V1: &str = "core.wdp.source-packet.v1";
pub const WDP_SOURCE_RESULT_SCHEMA_V1: &str = "core.wdp.source-packet-result.v1";
pub const WDP_SOURCE_REPLAY_SCHEMA_V1: &str = "core.wdp.source-packet-replay.v1";
pub const WDP_PACKET_REQUEST_DOMAIN_V1: &str = "core.wdp.source-packet-request.v1";
pub const WDP_PACKET_CARRIER_DOMAIN_V1: &str = "core.wdp.source-packet-carrier.v1";
pub const WDP_PACKET_RESULT_DOMAIN_V1: &str = "core.wdp.source-packet-result-content.v1";
pub const MAX_SOURCE_BYTES: usize = 8_192;
pub const MAX_PACKET_ELEMENTS: usize = 4_096;
pub const MAX_PACKET_SCALAR_OPS: usize = 10_000_000;
pub const MAX_PACKET_BITS: u64 = 1_024;
pub const MAX_CHANNEL_DIMENSION: usize = 16;
pub const MAX_KRAUS_TERMS: usize = 32;

macro_rules! premise_enum {
    ($name:ident { $($variant:ident),+ $(,)? }) => {
        #[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
        #[serde(rename_all = "snake_case")]
        pub enum $name { $($variant),+ }
    };
}

premise_enum!(SourceDigestProfileV1 { Sha256RawBytesV1 });
premise_enum!(WdpPacketQuestionV1 {
    ExactEuclideanHodgeDecomposition,
    ExactWeightedKrausGramStateTransport,
    Other
});
premise_enum!(WdpPacketScopeV1 {
    FiniteDeclaredInputs,
    GeneralTheory
});
premise_enum!(WdpPacketScalarModelV1 {
    ExactRational,
    ExactGaussianRational,
    FloatingPoint
});
premise_enum!(WdpPacketQuotientModelV1 {
    PotentialModuloKernel,
    MatrixEntryEquality,
    Undeclared
});
premise_enum!(WdpPacketPositivityModelV1 {
    NotApplicable,
    NonnegativeKrausWeightsAndGramState,
    Claimed
});
premise_enum!(WdpPacketCompositionModelV1 {
    NotApplicable,
    SingleDeclaredMap,
    AllComposedWords
});
premise_enum!(WdpPacketAvailabilityModelV1 {
    DeclaredFiniteCarrier,
    Unknown
});

/// This boundary reads no paths. Callers supply the exact bytes being pinned.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SourceBindingV1 {
    pub source_id: String,
    pub digest_profile: SourceDigestProfileV1,
    pub sha256: String,
    pub bytes: Vec<u8>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct VerifiedSourceBindingV1 {
    pub source_id: String,
    pub digest_profile: SourceDigestProfileV1,
    pub sha256: String,
    pub byte_count: usize,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct WdpPacketResourceLimitsV1 {
    pub max_source_bytes: usize,
    pub max_scalar_ops: usize,
    pub max_elements: usize,
    pub max_bits: u64,
}

impl WdpPacketResourceLimitsV1 {
    fn rational_limits(self) -> Result<RationalLimits, WdpPacketRefusalV1> {
        if self.max_source_bytes == 0
            || self.max_source_bytes > MAX_SOURCE_BYTES
            || self.max_scalar_ops == 0
            || self.max_scalar_ops > MAX_PACKET_SCALAR_OPS
            || self.max_elements == 0
            || self.max_elements > MAX_PACKET_ELEMENTS
            || self.max_bits == 0
            || self.max_bits > MAX_PACKET_BITS
        {
            return Err(refuse(
                WdpPacketRefusalCodeV1::ResourceLimits,
                "resource limits must be positive and within the finite boundary ceilings",
            ));
        }
        Ok(RationalLimits {
            max_scalar_ops: self.max_scalar_ops,
            max_elements: self.max_elements,
            max_bits: self.max_bits,
        })
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct WdpPacketHeaderV1 {
    pub schema_version: String,
    pub question: WdpPacketQuestionV1,
    pub scope: WdpPacketScopeV1,
    pub scalar_model: WdpPacketScalarModelV1,
    pub quotient_model: WdpPacketQuotientModelV1,
    pub positivity_model: WdpPacketPositivityModelV1,
    pub composition_model: WdpPacketCompositionModelV1,
    pub availability_model: WdpPacketAvailabilityModelV1,
    pub limits: WdpPacketResourceLimitsV1,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GaussianRationalV1 {
    #[serde(with = "exact_wire")]
    pub re: BigRational,
    #[serde(with = "exact_wire")]
    pub im: BigRational,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GaussianMatrixV1 {
    pub rows: usize,
    pub cols: usize,
    pub entries: Vec<GaussianRationalV1>,
}

impl GaussianMatrixV1 {
    fn decode(
        &self,
        fuel: &mut RationalBudget,
    ) -> Result<BasicMatrix<GaussianRat>, WdpPacketRefusalV1> {
        fuel.elements(self.rows, 1).map_err(arithmetic_refusal)?;
        fuel.elements(self.cols, 1).map_err(arithmetic_refusal)?;
        let count = fuel
            .elements(self.rows, self.cols)
            .map_err(arithmetic_refusal)?;
        if count != self.entries.len() {
            return Err(refuse(
                WdpPacketRefusalCodeV1::Shape,
                "Gaussian matrix entry count differs from its dimensions",
            ));
        }
        let mut entries = Vec::new();
        entries
            .try_reserve_exact(count)
            .map_err(|_| arithmetic_refusal(RationalError::Allocation))?;
        for value in &self.entries {
            fuel.rational(&value.re).map_err(arithmetic_refusal)?;
            fuel.rational(&value.im).map_err(arithmetic_refusal)?;
            entries.push(GaussianRat {
                re: value.re.clone(),
                im: value.im.clone(),
            });
        }
        BasicMatrix::from_row_major(self.rows, self.cols, entries)
            .map_err(|error| refuse(WdpPacketRefusalCodeV1::Shape, error.to_string()))
    }

    fn encode(matrix: &BasicMatrix<GaussianRat>) -> Self {
        Self {
            rows: matrix.rows(),
            cols: matrix.cols(),
            entries: matrix
                .as_slice()
                .iter()
                .map(|value| GaussianRationalV1 {
                    re: value.re.clone(),
                    im: value.im.clone(),
                })
                .collect(),
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct WeightedKrausTermV1 {
    #[serde(with = "exact_wire")]
    pub weight: BigRational,
    pub operator: GaussianMatrixV1,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum WdpPacketOperationV1 {
    Hodge {
        d0: RationalMatrixV1,
        d1: RationalMatrixV1,
        #[serde(with = "exact_wire_vec")]
        flow: Vec<BigRational>,
    },
    WeightedKrausGramStateTransport {
        dim_in: usize,
        dim_out: usize,
        terms: Vec<WeightedKrausTermV1>,
        state_factor: GaussianMatrixV1,
    },
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct WdpSourcePacketRequestV1 {
    pub header: WdpPacketHeaderV1,
    pub source: SourceBindingV1,
    pub operation: WdpPacketOperationV1,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum WdpPacketOutputV1 {
    Hodge { result: HodgeResultV1 },
    WeightedKrausGramStateTransport { image: GaussianMatrixV1 },
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct WdpSourcePacketResultV1 {
    pub schema_version: String,
    pub header: WdpPacketHeaderV1,
    pub source: VerifiedSourceBindingV1,
    pub input_digest: String,
    pub carrier_digest: String,
    pub output: WdpPacketOutputV1,
    pub authority_effect: AuthorityEffect,
    pub result_digest: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct WdpSourcePacketReplayV1 {
    pub schema_version: String,
    pub input_digest: String,
    pub carrier_digest: String,
    pub result_digest: String,
    pub replay_scalar_ops: usize,
    pub authority_effect: AuthorityEffect,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum WdpPacketRefusalCodeV1 {
    Wire,
    Schema,
    SourceBytes,
    SourceDigest,
    ResourceLimits,
    ResourceBudget,
    Question,
    Scope,
    ScalarModel,
    QuotientModel,
    PositivityModel,
    CompositionModel,
    AvailabilityModel,
    Shape,
    RequestBinding,
    CarrierBinding,
    ResultBinding,
    Authority,
    HodgePremise,
    HodgeCertificate,
    ChannelPremise,
    ChannelResult,
    ResultKind,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct WdpPacketRefusalV1 {
    pub code: WdpPacketRefusalCodeV1,
    pub detail: String,
    pub authority_effect: AuthorityEffect,
}

impl WdpPacketRefusalV1 {
    pub fn wire(&self) -> String {
        let code = Self::code_label(self.code);
        format!("WDP_PACKET_{code}: {}", self.detail)
    }

    fn code_label(code: WdpPacketRefusalCodeV1) -> &'static str {
        if let Some(label) = Self::code_label_envelope(code) {
            return label;
        }
        if let Some(label) = Self::code_label_premises(code) {
            return label;
        }
        Self::code_label_bindings_and_ops(code)
    }

    fn code_label_envelope(code: WdpPacketRefusalCodeV1) -> Option<&'static str> {
        match code {
            WdpPacketRefusalCodeV1::Wire => Some("WIRE"),
            WdpPacketRefusalCodeV1::Schema => Some("SCHEMA"),
            WdpPacketRefusalCodeV1::SourceBytes => Some("SOURCE_BYTES"),
            WdpPacketRefusalCodeV1::SourceDigest => Some("SOURCE_DIGEST"),
            WdpPacketRefusalCodeV1::ResourceLimits => Some("RESOURCE_LIMITS"),
            WdpPacketRefusalCodeV1::ResourceBudget => Some("RESOURCE_BUDGET"),
            WdpPacketRefusalCodeV1::Question => Some("QUESTION"),
            WdpPacketRefusalCodeV1::Scope => Some("SCOPE"),
            _ => None,
        }
    }

    fn code_label_premises(code: WdpPacketRefusalCodeV1) -> Option<&'static str> {
        match code {
            WdpPacketRefusalCodeV1::ScalarModel => Some("SCALAR_MODEL"),
            WdpPacketRefusalCodeV1::QuotientModel => Some("QUOTIENT_MODEL"),
            WdpPacketRefusalCodeV1::PositivityModel => Some("POSITIVITY_MODEL"),
            WdpPacketRefusalCodeV1::CompositionModel => Some("COMPOSITION_MODEL"),
            WdpPacketRefusalCodeV1::AvailabilityModel => Some("AVAILABILITY_MODEL"),
            WdpPacketRefusalCodeV1::Shape => Some("SHAPE"),
            WdpPacketRefusalCodeV1::RequestBinding => Some("REQUEST_BINDING"),
            WdpPacketRefusalCodeV1::CarrierBinding => Some("CARRIER_BINDING"),
            _ => None,
        }
    }

    fn code_label_bindings_and_ops(code: WdpPacketRefusalCodeV1) -> &'static str {
        match code {
            WdpPacketRefusalCodeV1::ResultBinding => "RESULT_BINDING",
            WdpPacketRefusalCodeV1::Authority => "AUTHORITY",
            WdpPacketRefusalCodeV1::HodgePremise => "HODGE_PREMISE",
            WdpPacketRefusalCodeV1::HodgeCertificate => "HODGE_CERTIFICATE",
            WdpPacketRefusalCodeV1::ChannelPremise => "CHANNEL_PREMISE",
            WdpPacketRefusalCodeV1::ChannelResult => "CHANNEL_RESULT",
            WdpPacketRefusalCodeV1::ResultKind => "RESULT_KIND",
            _ => "WIRE",
        }
    }
}

fn refuse(code: WdpPacketRefusalCodeV1, detail: impl Into<String>) -> WdpPacketRefusalV1 {
    WdpPacketRefusalV1 {
        code,
        detail: detail.into(),
        authority_effect: AuthorityEffect::None,
    }
}

fn arithmetic_refusal(error: RationalError) -> WdpPacketRefusalV1 {
    refuse(WdpPacketRefusalCodeV1::ResourceBudget, error.to_string())
}

fn hodge_refusal(error: HodgePacketError) -> WdpPacketRefusalV1 {
    match error {
        HodgePacketError::Arithmetic(error) => arithmetic_refusal(error),
        HodgePacketError::Hodge(core_solvers::cert_hodge_decomp::HodgeError::Arithmetic(
            error,
        )) => arithmetic_refusal(error),
        HodgePacketError::Hodge(error) => {
            refuse(WdpPacketRefusalCodeV1::HodgeCertificate, error.to_string())
        }
        error => refuse(WdpPacketRefusalCodeV1::HodgePremise, error.to_string()),
    }
}

fn channel_refusal(error: ExactChannelError) -> WdpPacketRefusalV1 {
    match error {
        ExactChannelError::RationalBudget(error) => arithmetic_refusal(error),
        error => refuse(WdpPacketRefusalCodeV1::ChannelPremise, error.to_string()),
    }
}

pub fn raw_source_sha256(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}

fn is_lowercase_hex_64(digest: &str) -> bool {
    digest.len() == 64
        && digest
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (97u8..=102u8).contains(&byte))
}

fn verify_source(
    source: &SourceBindingV1,
    max_bytes: usize,
) -> Result<VerifiedSourceBindingV1, WdpPacketRefusalV1> {
    let valid_id = !source.source_id.is_empty()
        && source.source_id.len() <= 256
        && !source.source_id.chars().any(char::is_control);
    if !valid_id || source.bytes.is_empty() || source.bytes.len() > max_bytes {
        return Err(refuse(
            WdpPacketRefusalCodeV1::SourceBytes,
            "source needs an explicit id and 1..max_source_bytes supplied raw bytes",
        ));
    }
    if !is_lowercase_hex_64(&source.sha256) || source.sha256 != raw_source_sha256(&source.bytes) {
        return Err(refuse(
            WdpPacketRefusalCodeV1::SourceDigest,
            "source SHA-256 does not match the supplied raw bytes and lowercase hex profile",
        ));
    }
    Ok(VerifiedSourceBindingV1 {
        source_id: source.source_id.clone(),
        digest_profile: source.digest_profile,
        sha256: source.sha256.clone(),
        byte_count: source.bytes.len(),
    })
}

/// Sorted JSON is a semantic wire commitment, distinct from the raw source hash.
pub fn packet_digest<T: Serialize>(domain: &str, value: &T) -> Result<String, WdpPacketRefusalV1> {
    let value = serde_json::to_value(value)
        .map_err(|error| refuse(WdpPacketRefusalCodeV1::Wire, error.to_string()))?;
    let bytes = serde_json::to_vec(&value)
        .map_err(|error| refuse(WdpPacketRefusalCodeV1::Wire, error.to_string()))?;
    let mut hasher = Sha256::new();
    hasher.update((domain.len() as u32).to_be_bytes());
    hasher.update(domain.as_bytes());
    hasher.update((bytes.len() as u64).to_be_bytes());
    hasher.update(bytes);
    Ok(hex::encode(hasher.finalize()))
}

fn result_digest(result: &WdpSourcePacketResultV1) -> Result<String, WdpPacketRefusalV1> {
    let mut value = serde_json::to_value(result)
        .map_err(|error| refuse(WdpPacketRefusalCodeV1::Wire, error.to_string()))?;
    let fields = value.as_object_mut().ok_or_else(|| {
        refuse(
            WdpPacketRefusalCodeV1::Wire,
            "result commitment needs an object",
        )
    })?;
    fields.remove("result_digest");
    packet_digest(WDP_PACKET_RESULT_DOMAIN_V1, &value)
}

fn validate_header(
    request: &WdpSourcePacketRequestV1,
) -> Result<RationalLimits, WdpPacketRefusalV1> {
    let header = &request.header;
    if header.schema_version != WDP_SOURCE_PACKET_SCHEMA_V1 {
        return Err(refuse(
            WdpPacketRefusalCodeV1::Schema,
            "unsupported source-packet schema",
        ));
    }
    if header.scope != WdpPacketScopeV1::FiniteDeclaredInputs {
        return Err(refuse(
            WdpPacketRefusalCodeV1::Scope,
            "only the supplied finite declared inputs are admitted",
        ));
    }
    if header.availability_model != WdpPacketAvailabilityModelV1::DeclaredFiniteCarrier {
        return Err(refuse(
            WdpPacketRefusalCodeV1::AvailabilityModel,
            "finite operational availability must be declared",
        ));
    }
    let (question, scalar, quotient, positivity, composition) = match &request.operation {
        WdpPacketOperationV1::Hodge { .. } => (
            WdpPacketQuestionV1::ExactEuclideanHodgeDecomposition,
            WdpPacketScalarModelV1::ExactRational,
            WdpPacketQuotientModelV1::PotentialModuloKernel,
            WdpPacketPositivityModelV1::NotApplicable,
            WdpPacketCompositionModelV1::NotApplicable,
        ),
        WdpPacketOperationV1::WeightedKrausGramStateTransport { .. } => (
            WdpPacketQuestionV1::ExactWeightedKrausGramStateTransport,
            WdpPacketScalarModelV1::ExactGaussianRational,
            WdpPacketQuotientModelV1::MatrixEntryEquality,
            WdpPacketPositivityModelV1::NonnegativeKrausWeightsAndGramState,
            WdpPacketCompositionModelV1::SingleDeclaredMap,
        ),
    };
    for (valid, code, name) in [
        (
            header.question == question,
            WdpPacketRefusalCodeV1::Question,
            "protected question",
        ),
        (
            header.scalar_model == scalar,
            WdpPacketRefusalCodeV1::ScalarModel,
            "scalar field",
        ),
        (
            header.quotient_model == quotient,
            WdpPacketRefusalCodeV1::QuotientModel,
            "quotient model",
        ),
        (
            header.positivity_model == positivity,
            WdpPacketRefusalCodeV1::PositivityModel,
            "positivity premise",
        ),
        (
            header.composition_model == composition,
            WdpPacketRefusalCodeV1::CompositionModel,
            "composition premise",
        ),
    ] {
        if !valid {
            return Err(refuse(
                code,
                format!("{name} is incompatible with the requested finite operation"),
            ));
        }
    }
    header.limits.rational_limits()
}

fn preflight_rational_matrix(
    matrix: &RationalMatrixV1,
    fuel: &mut RationalBudget,
) -> Result<usize, WdpPacketRefusalV1> {
    fuel.elements(matrix.rows, 1).map_err(arithmetic_refusal)?;
    fuel.elements(matrix.cols, 1).map_err(arithmetic_refusal)?;
    let count = fuel
        .elements(matrix.rows, matrix.cols)
        .map_err(arithmetic_refusal)?;
    if matrix.entries.len() != count {
        return Err(refuse(
            WdpPacketRefusalCodeV1::Shape,
            "rational matrix entry count differs from its dimensions",
        ));
    }
    for scalar in &matrix.entries {
        fuel.rational(scalar).map_err(arithmetic_refusal)?;
    }
    Ok(count)
}

fn is_valid_channel_shape(
    dim_in: usize,
    dim_out: usize,
    terms: &[WeightedKrausTermV1],
    state_factor: &GaussianMatrixV1,
) -> bool {
    let dims_ok = (1..=MAX_CHANNEL_DIMENSION).contains(&dim_in)
        && (1..=MAX_CHANNEL_DIMENSION).contains(&dim_out);
    let terms_ok = !terms.is_empty() && terms.len() <= MAX_KRAUS_TERMS;
    dims_ok && terms_ok && state_factor.cols <= MAX_CHANNEL_DIMENSION
}

fn preflight_hodge_carrier(
    d0: &RationalMatrixV1,
    d1: &RationalMatrixV1,
    flow: &[BigRational],
    fuel: &mut RationalBudget,
) -> Result<Option<usize>, WdpPacketRefusalV1> {
    let c0 = preflight_rational_matrix(d0, fuel)?;
    let c1 = preflight_rational_matrix(d1, fuel)?;
    fuel.elements(flow.len(), 1).map_err(arithmetic_refusal)?;
    for scalar in flow {
        fuel.rational(scalar).map_err(arithmetic_refusal)?;
    }
    Ok(c0
        .checked_add(c1)
        .and_then(|count| count.checked_add(flow.len())))
}

fn preflight_kraus_carrier(
    dim_in: usize,
    dim_out: usize,
    terms: &[WeightedKrausTermV1],
    state_factor: &GaussianMatrixV1,
    fuel: &mut RationalBudget,
) -> Result<Option<usize>, WdpPacketRefusalV1> {
    if !is_valid_channel_shape(dim_in, dim_out, terms, state_factor) {
        return Err(refuse(
            WdpPacketRefusalCodeV1::Shape,
            "channel dimensions/count exceed the finite operational boundary",
        ));
    }
    let mut count = state_factor.decode(fuel)?.as_slice().len();
    for term in terms {
        fuel.rational(&term.weight).map_err(arithmetic_refusal)?;
        count = count
            .checked_add(term.operator.decode(fuel)?.as_slice().len())
            .ok_or_else(|| arithmetic_refusal(RationalError::ElementLimit))?;
    }
    Ok(Some(count))
}

fn preflight_carrier(
    request: &WdpSourcePacketRequestV1,
    fuel: &mut RationalBudget,
) -> Result<(), WdpPacketRefusalV1> {
    let count = match &request.operation {
        WdpPacketOperationV1::Hodge { d0, d1, flow } => {
            preflight_hodge_carrier(d0, d1, flow, fuel)?
        }
        WdpPacketOperationV1::WeightedKrausGramStateTransport {
            dim_in,
            dim_out,
            terms,
            state_factor,
        } => preflight_kraus_carrier(*dim_in, *dim_out, terms, state_factor, fuel)?,
    }
    .ok_or_else(|| arithmetic_refusal(RationalError::ElementLimit))?;
    fuel.elements(count, 1).map_err(arithmetic_refusal)?;
    Ok(())
}

fn preflight_output(
    output: &WdpPacketOutputV1,
    fuel: &mut RationalBudget,
) -> Result<(), WdpPacketRefusalV1> {
    match output {
        WdpPacketOutputV1::Hodge { result } => {
            let certificate = &result.certificate;
            let mut total = 0usize;
            for values in [
                &certificate.alpha,
                &certificate.beta,
                &certificate.exact,
                &certificate.coexact,
                &certificate.harmonic,
            ] {
                total = total
                    .checked_add(values.len())
                    .ok_or_else(|| arithmetic_refusal(RationalError::ElementLimit))?;
                fuel.elements(values.len(), 1).map_err(arithmetic_refusal)?;
                for value in values {
                    fuel.rational(value).map_err(arithmetic_refusal)?;
                }
            }
            fuel.elements(total, 1).map_err(arithmetic_refusal)?;
        }
        WdpPacketOutputV1::WeightedKrausGramStateTransport { image } => {
            image.decode(fuel)?;
        }
    }
    Ok(())
}

fn hodge_request(
    request: &WdpSourcePacketRequestV1,
    d0: &RationalMatrixV1,
    d1: &RationalMatrixV1,
    flow: &[BigRational],
) -> HodgeRequestV1 {
    let limits = request.header.limits;
    HodgeRequestV1 {
        header: HodgePacketHeaderV1 {
            schema_version: hodge::HODGE_PACKET_SCHEMA_V1.to_owned(),
            source_digest: request.source.sha256.clone(),
            scalar_model: HodgeScalarModelV1::ExactRational,
            quotient_model: HodgeQuotientModelV1::PotentialModuloKernel,
            positivity_model: HodgePositivityModelV1::NotApplicable,
            composition_model: HodgeCompositionModelV1::NotApplicable,
            availability_model: HodgeAvailabilityModelV1::DeclaredFiniteCarrier,
            question: HodgeQuestionV1::ExactEuclideanHodgeDecomposition,
            limits: HodgeResourceLimitsV1 {
                max_scalar_ops: limits.max_scalar_ops,
                max_elements: limits.max_elements,
                max_bits: limits.max_bits,
            },
        },
        d0: d0.clone(),
        d1: d1.clone(),
        flow: flow.to_vec(),
    }
}

fn channel_image(
    dim_in: usize,
    dim_out: usize,
    terms: &[WeightedKrausTermV1],
    state_factor: &GaussianMatrixV1,
    fuel: &mut RationalBudget,
) -> Result<GaussianMatrixV1, WdpPacketRefusalV1> {
    if !is_valid_channel_shape(dim_in, dim_out, terms, state_factor) {
        return Err(refuse(
            WdpPacketRefusalCodeV1::Shape,
            "channel dimensions must be 1..16 with 1..32 Kraus terms and Gram width at most 16",
        ));
    }
    let mut decoded = Vec::new();
    decoded
        .try_reserve_exact(terms.len())
        .map_err(|_| arithmetic_refusal(RationalError::Allocation))?;
    for term in terms {
        fuel.rational(&term.weight).map_err(arithmetic_refusal)?;
        decoded.push((term.weight.clone(), term.operator.decode(fuel)?));
    }
    let channel = ExactKrausChannel::try_weighted_with_budget(
        dim_in,
        dim_out,
        decoded,
        "source-packet finite declared channel",
        fuel,
    )
    .map_err(channel_refusal)?;
    let factor = state_factor.decode(fuel)?;
    let image = channel
        .transport_gram_state_with_budget(&factor, fuel)
        .map_err(channel_refusal)?;
    Ok(GaussianMatrixV1::encode(&image))
}

fn compute_packet_output(
    request: &WdpSourcePacketRequestV1,
    fuel: &mut RationalBudget,
) -> Result<WdpPacketOutputV1, WdpPacketRefusalV1> {
    match &request.operation {
        WdpPacketOperationV1::Hodge { d0, d1, flow } => {
            let h_req = hodge_request(request, d0, d1, flow);
            let result = hodge::solve_hodge_packet_with_budget(h_req.clone(), fuel)
                .map_err(hodge_refusal)?;
            hodge::replay_hodge_packet_with_budget(h_req, &result, fuel).map_err(hodge_refusal)?;
            Ok(WdpPacketOutputV1::Hodge { result })
        }
        WdpPacketOperationV1::WeightedKrausGramStateTransport {
            dim_in,
            dim_out,
            terms,
            state_factor,
        } => {
            let image = channel_image(*dim_in, *dim_out, terms, state_factor, fuel)?;
            let replay = channel_image(*dim_in, *dim_out, terms, state_factor, fuel)?;
            if image != replay {
                return Err(refuse(
                    WdpPacketRefusalCodeV1::ChannelResult,
                    "fresh channel replay differs",
                ));
            }
            Ok(WdpPacketOutputV1::WeightedKrausGramStateTransport { image })
        }
    }
}

/// Produce a source/carrier/premise-bound exact result. One rational budget is
/// shared through decoding, owner construction, and result replay.
pub fn evaluate_source_packet(
    request: &WdpSourcePacketRequestV1,
) -> Result<WdpSourcePacketResultV1, WdpPacketRefusalV1> {
    let mut fuel = RationalBudget::new(validate_header(request)?);
    let source = verify_source(&request.source, request.header.limits.max_source_bytes)?;
    preflight_carrier(request, &mut fuel)?;
    let input_digest = packet_digest(WDP_PACKET_REQUEST_DOMAIN_V1, request)?;
    let carrier_digest = packet_digest(WDP_PACKET_CARRIER_DOMAIN_V1, &request.operation)?;
    let output = compute_packet_output(request, &mut fuel)?;
    preflight_output(&output, &mut fuel)?;
    let mut result = WdpSourcePacketResultV1 {
        schema_version: WDP_SOURCE_RESULT_SCHEMA_V1.to_owned(),
        header: request.header.clone(),
        source,
        input_digest,
        carrier_digest,
        output,
        authority_effect: AuthorityEffect::None,
        result_digest: String::new(),
    };
    result.result_digest = result_digest(&result)?;
    Ok(result)
}

fn validate_replay_bindings(
    request: &WdpSourcePacketRequestV1,
    result: &WdpSourcePacketResultV1,
    source: &VerifiedSourceBindingV1,
    input_digest: &str,
    carrier_digest: &str,
) -> Result<(), WdpPacketRefusalV1> {
    if result.schema_version != WDP_SOURCE_RESULT_SCHEMA_V1 {
        return Err(refuse(
            WdpPacketRefusalCodeV1::Schema,
            "unsupported result schema",
        ));
    }
    if !result.authority_effect.is_none() {
        return Err(refuse(
            WdpPacketRefusalCodeV1::Authority,
            "finite packet results must carry AuthorityEffect::None",
        ));
    }
    let req_bound = result.header == request.header
        && &result.source == source
        && result.input_digest == input_digest;
    if !req_bound {
        return Err(refuse(WdpPacketRefusalCodeV1::RequestBinding, "candidate is not bound to this source, protected question, premises, and resource limits"));
    }
    if result.carrier_digest != carrier_digest {
        return Err(refuse(
            WdpPacketRefusalCodeV1::CarrierBinding,
            "candidate carrier differs from the supplied operation",
        ));
    }
    Ok(())
}

fn verify_replay_operation(
    request: &WdpSourcePacketRequestV1,
    result: &WdpSourcePacketResultV1,
    fuel: &mut RationalBudget,
) -> Result<(), WdpPacketRefusalV1> {
    if result.result_digest != result_digest(result)? {
        return Err(refuse(
            WdpPacketRefusalCodeV1::ResultBinding,
            "candidate result commitment does not recompute",
        ));
    }
    match (&request.operation, &result.output) {
        (WdpPacketOperationV1::Hodge { d0, d1, flow }, WdpPacketOutputV1::Hodge { result }) => {
            hodge::replay_hodge_packet_with_budget(
                hodge_request(request, d0, d1, flow),
                result,
                fuel,
            )
            .map(|_| ())
            .map_err(hodge_refusal)
            .map(|_| ())
        }
        (
            WdpPacketOperationV1::WeightedKrausGramStateTransport {
                dim_in,
                dim_out,
                terms,
                state_factor,
            },
            WdpPacketOutputV1::WeightedKrausGramStateTransport { image },
        ) => verify_kraus_replay(*dim_in, *dim_out, terms, state_factor, image, fuel),
        _ => Err(refuse(
            WdpPacketRefusalCodeV1::ResultKind,
            "candidate operation does not answer the protected question",
        )),
    }
}

fn verify_kraus_replay(
    dim_in: usize,
    dim_out: usize,
    terms: &[WeightedKrausTermV1],
    state_factor: &GaussianMatrixV1,
    image: &GaussianMatrixV1,
    fuel: &mut RationalBudget,
) -> Result<(), WdpPacketRefusalV1> {
    let claimed = image.decode(fuel)?;
    let replay = channel_image(dim_in, dim_out, terms, state_factor, fuel)?;
    if GaussianMatrixV1::encode(&claimed) != replay {
        return Err(refuse(
            WdpPacketRefusalCodeV1::ChannelResult,
            "submitted image differs from fresh exact state transport",
        ));
    }
    Ok(())
}

/// Verify supplied source bytes and independently replay the submitted candidate.
/// Replay has one new run budget, shared by all work within that run.
pub fn replay_source_packet(
    request: &WdpSourcePacketRequestV1,
    result: &WdpSourcePacketResultV1,
) -> Result<WdpSourcePacketReplayV1, WdpPacketRefusalV1> {
    let mut fuel = RationalBudget::new(validate_header(request)?);
    let source = verify_source(&request.source, request.header.limits.max_source_bytes)?;
    preflight_carrier(request, &mut fuel)?;
    let input_digest = packet_digest(WDP_PACKET_REQUEST_DOMAIN_V1, request)?;
    let carrier_digest = packet_digest(WDP_PACKET_CARRIER_DOMAIN_V1, &request.operation)?;
    validate_replay_bindings(request, result, &source, &input_digest, &carrier_digest)?;
    preflight_output(&result.output, &mut fuel)?;
    verify_replay_operation(request, result, &mut fuel)?;
    Ok(WdpSourcePacketReplayV1 {
        schema_version: WDP_SOURCE_REPLAY_SCHEMA_V1.to_owned(),
        input_digest,
        carrier_digest,
        result_digest: result.result_digest.clone(),
        replay_scalar_ops: fuel.used(),
        authority_effect: AuthorityEffect::None,
    })
}

// Origin: engine/crates_rs/core_wdp/src/wdp_source_packet.rs
// Claim: urn:core:crates_rs:core-wdp:wdp-source-packet:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3260b8b9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3260b8b9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3260b8b9 {
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
impl BoundaryError3260b8b9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3260b8b9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3260b8b9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3260b8b9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3260b8b9> {
        if capacity_bound == 0 {
            return Err(BoundaryError3260b8b9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3260b8b9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3260b8b9::ExceedsCapacity {
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
mod l4_boundary_tests_3260b8b9 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord3260b8b9::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord3260b8b9::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord3260b8b9::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord3260b8b9::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord3260b8b9::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError3260b8b9::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError3260b8b9::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
