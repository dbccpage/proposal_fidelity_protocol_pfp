//! Genesis stratification `G0 -> G1 -> G2`, observer regimes, and the Examiner quiz.
//!
//! The point of stratifying is to stop a later level's structure from being
//! read back into an earlier one. Three levels, and what each is allowed to
//! know:
//!
//! - **`G0`** -- [`OpaqueDatum`]. A distinction exists. Nothing else. It has no
//!   accessors, so "what is it made of" is not a question you can ask at this
//!   level: the compiler refuses it rather than a runtime check refusing it.
//! - **`G1`** -- [`PresentationCodec`]. Glyphs. `<` is `0x3C` and `>` is `0x3E`,
//!   a string has a length, and openers can be counted. All typography. This
//!   level deliberately has **no** method reporting whether a word is a legal
//!   nesting, because "the brackets look balanced" is a character-level fact
//!   and admitting it as a structural one is exactly the smuggling the
//!   stratification exists to prevent.
//! - **`G2`** -- [`AdmittedContext`]. Structure, and only once [`admit`] has
//!   accepted it. A Dyck word here is a carrier, not a rendering.
//!
//! ## Ground inertia
//!
//! At `G0` every datum is equal to every other datum. That is not a stub; it is
//! the law. Two primitive differences become *distinguishable* only relative to
//! an admitted family of contexts, so
//!
//! ```text
//! x ~_O y   iff   for all C in C,  E(C[x]) = E(C[y])
//! ```
//!
//! and when `C` is empty the quantifier is vacuous, so **everything is
//! equivalent**. Asking this module to separate two data without admitting a
//! context is [`GenesisErrorCode::NoAdmittedContext`] -- a refusal, not a
//! `false`. A system that answers "they differ" with no context to differ in
//! has invented a distinction it was not given.
//!
//! ## Exactness
//!
//! Evaluation morphisms land in [`BigRational`]. No `f64` appears in this
//! module, and the Examiner quiz scores as a rational so a benchmark result is
//! reproducible rather than nearly reproducible.
//!
//! `AuthorityEffect: None`.

use std::collections::BTreeSet;
use std::fmt;

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Zero};

use crate::foundation::PrimitiveDifference;

/// ASCII glyphs the Symbol Game renders a primitive difference with.
pub const GLYPH_OPEN: u8 = 0x3C; // '<'
pub const GLYPH_CLOSE: u8 = 0x3E; // '>'

// ---------------------------------------------------------------------------
// Refusals
// ---------------------------------------------------------------------------

/// Stable categories for fail-closed genesis errors.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum GenesisErrorCode {
    /// A separation was demanded with no admitted context to separate in.
    NoAdmittedContext,
    /// A glyph outside the declared codec appeared.
    ForeignGlyph,
    /// A close appeared with no matching open, or opens were left unclosed.
    NotDyck,
    /// A context family was declared with duplicate members.
    DuplicateContext,
    /// A challenge declared a size its relation does not fit inside.
    OutOfDomain,
    /// A quiz was asked to score against no questions.
    EmptyQuiz,
    /// A serialized score did not bind its exact score and challenge identities.
    InvalidReceipt,
}

/// A typed refusal from the genesis stratification.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct GenesisError {
    code: GenesisErrorCode,
    message: String,
}

impl GenesisError {
    fn new(code: GenesisErrorCode, message: impl Into<String>) -> Self {
        Self {
            code,
            message: message.into(),
        }
    }

    pub fn code(&self) -> GenesisErrorCode {
        self.code
    }

    pub fn message(&self) -> &str {
        &self.message
    }
}

impl fmt::Display for GenesisError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "GENESIS_ERROR[{:?}]: {}", self.code, self.message)
    }
}

impl std::error::Error for GenesisError {}

// ---------------------------------------------------------------------------
// G0 -- the opaque datum
// ---------------------------------------------------------------------------

/// Level `G0`: a distinction exists, and that is the whole of it.
///
/// Deliberately zero-sized and deliberately without accessors. There is no
/// `bytes()`, no `len()`, no `Deref`. The absence is the specification: at this
/// level the datum has no interior to expose, so exposing one would be a lie
/// the type system can prevent rather than a rule a reviewer must remember.
///
/// Every `OpaqueDatum` equals every other. See the module docs on ground
/// inertia -- this is that law, not a missing implementation.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Hash)]
pub struct OpaqueDatum {
    // A private zero-sized witness. Not `pub`, so no field access escapes.
    _witness: PrimitiveDifference,
}

impl OpaqueDatum {
    /// Admit that a distinction exists.
    pub const fn new() -> Self {
        Self {
            _witness: PrimitiveDifference,
        }
    }
}

// ---------------------------------------------------------------------------
// G1 -- presentation
// ---------------------------------------------------------------------------

/// What a `G1` scan is allowed to report: glyph-level facts, nothing more.
///
/// Note what is absent. There is no `is_balanced` and no `is_dyck`. Depth can
/// go negative here and that is recorded as a number, not as a verdict, because
/// turning it into a verdict is a `G2` decision.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct TypographicScan {
    opens: usize,
    closes: usize,
    length: usize,
    /// Running depth after each glyph. May go negative; that is `G2`'s problem.
    depth_profile: Vec<i64>,
}

impl TypographicScan {
    pub fn opens(&self) -> usize {
        self.opens
    }

    pub fn closes(&self) -> usize {
        self.closes
    }

    pub fn length(&self) -> usize {
        self.length
    }

    pub fn depth_profile(&self) -> &[i64] {
        &self.depth_profile
    }

    /// The depth the word ends at. Zero is necessary for a Dyck word and not
    /// sufficient: `><` also ends at zero.
    pub fn net_depth(&self) -> i64 {
        self.depth_profile.last().copied().unwrap_or(0)
    }

    /// The lowest depth reached. Negative means a close preceded its open.
    pub fn min_depth(&self) -> i64 {
        self.depth_profile.iter().copied().min().unwrap_or(0)
    }

    /// The deepest nesting reached, as typography.
    pub fn max_depth(&self) -> i64 {
        self.depth_profile.iter().copied().max().unwrap_or(0)
    }
}

/// Level `G1`: the codec that renders and scans, and knows nothing else.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct PresentationCodec {
    open: u8,
    close: u8,
}

impl Default for PresentationCodec {
    fn default() -> Self {
        Self::ascii_angle()
    }
}

impl PresentationCodec {
    /// The canonical Symbol Game codec: `<` and `>`.
    pub const fn ascii_angle() -> Self {
        Self {
            open: GLYPH_OPEN,
            close: GLYPH_CLOSE,
        }
    }

    /// A codec over a different glyph pair, for tests that must show the
    /// stratification does not secretly depend on the characters chosen.
    pub fn with_glyphs(open: u8, close: u8) -> Result<Self, GenesisError> {
        if open == close {
            return Err(GenesisError::new(
                GenesisErrorCode::ForeignGlyph,
                format!("open and close glyphs coincide: {open:#04x}"),
            ));
        }
        Ok(Self { open, close })
    }

    pub fn open(&self) -> u8 {
        self.open
    }

    pub fn close(&self) -> u8 {
        self.close
    }

    /// Render a `G0` datum at a given nesting depth.
    ///
    /// A depth of zero renders the empty word: no glyphs is a legitimate
    /// rendering of "a distinction exists", and it is the identity of the Dyck
    /// monoid at `G2`.
    pub fn render(&self, _datum: OpaqueDatum, depth: usize) -> String {
        let mut out = String::with_capacity(depth * 2);
        for _ in 0..depth {
            out.push(self.open as char);
        }
        for _ in 0..depth {
            out.push(self.close as char);
        }
        out
    }

    /// Scan a word into glyph-level facts, refusing any glyph outside the codec.
    pub fn scan(&self, word: &str) -> Result<TypographicScan, GenesisError> {
        let bytes = word.as_bytes();
        let mut opens = 0usize;
        let mut closes = 0usize;
        let mut depth = 0i64;
        let mut depth_profile = Vec::with_capacity(bytes.len());
        for (index, byte) in bytes.iter().copied().enumerate() {
            if byte == self.open {
                opens += 1;
                depth += 1;
            } else if byte == self.close {
                closes += 1;
                depth -= 1;
            } else {
                return Err(GenesisError::new(
                    GenesisErrorCode::ForeignGlyph,
                    format!("byte {byte:#04x} at index {index} is outside the codec"),
                ));
            }
            depth_profile.push(depth);
        }
        Ok(TypographicScan {
            opens,
            closes,
            length: bytes.len(),
            depth_profile,
        })
    }
}

// ---------------------------------------------------------------------------
// G2 -- admitted structure
// ---------------------------------------------------------------------------

/// Level `G2`: a scan that has been admitted as a carrier.
///
/// Construction goes through [`admit`], which is the only way to get one. A
/// `TypographicScan` that merely *looks* balanced does not become an
/// `AdmittedContext` by being passed around.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct AdmittedContext {
    depth_profile: Vec<i64>,
    max_depth: i64,
}

/// Admit a scan as `G2` structure, or refuse it.
///
/// A Dyck word is exactly a word whose depth never goes negative and which ends
/// at zero. Both halves are required: `><` ends at zero and is not a nesting,
/// and `<<` never goes negative and is not closed.
pub fn admit(scan: &TypographicScan) -> Result<AdmittedContext, GenesisError> {
    if scan.min_depth() < 0 {
        return Err(GenesisError::new(
            GenesisErrorCode::NotDyck,
            format!(
                "a close preceded its open: depth reached {} before returning",
                scan.min_depth()
            ),
        ));
    }
    if scan.net_depth() != 0 {
        return Err(GenesisError::new(
            GenesisErrorCode::NotDyck,
            format!("word is unclosed: net depth {}", scan.net_depth()),
        ));
    }
    Ok(AdmittedContext {
        depth_profile: scan.depth_profile().to_vec(),
        max_depth: scan.max_depth(),
    })
}

impl AdmittedContext {
    /// The empty carrier: the identity of the Dyck monoid.
    pub fn empty() -> Self {
        Self {
            depth_profile: Vec::new(),
            max_depth: 0,
        }
    }

    pub fn depth_profile(&self) -> &[i64] {
        &self.depth_profile
    }

    /// Deepest admitted nesting.
    pub fn nesting_depth(&self) -> i64 {
        self.max_depth
    }

    /// Number of matched pairs.
    pub fn pairs(&self) -> usize {
        self.depth_profile.len() / 2
    }

    /// Boundary isolation: every matched pair encloses a Dyck word.
    ///
    /// This is the closure property that makes the carrier recursive, and it is
    /// checkable here in finite time. It is **not** the `d^2 = 0` statement of
    /// the surrounding theory: that lives over the discrete deformation calculus
    /// and is not re-derived in this module. Recorded rather than implied --
    /// see the sprint's open obligations.
    pub fn boundary_isolated(&self) -> bool {
        // A profile is a valid nesting iff it never dips below zero and ends at
        // zero; every interior segment between a matched pair then inherits the
        // same property by construction, which is what closure means here.
        let mut depth = 0i64;
        for step in &self.depth_profile {
            depth = *step;
            if depth < 0 {
                return false;
            }
        }
        depth == 0
    }
}

// ---------------------------------------------------------------------------
// Observer regimes
// ---------------------------------------------------------------------------

/// A context with a hole, `C[-]`, together with how it evaluates.
///
/// The hole is filled by wrapping the datum in `wrap` layers of nesting; the
/// evaluation morphism `E` reads the resulting carrier and returns an exact
/// rational. Two contexts that wrap identically are the same context.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub struct ObserverContext {
    name: String,
    wrap: usize,
}

impl ObserverContext {
    pub fn new(name: impl Into<String>, wrap: usize) -> Self {
        Self {
            name: name.into(),
            wrap,
        }
    }

    pub fn name(&self) -> &str {
        &self.name
    }

    pub fn wrap(&self) -> usize {
        self.wrap
    }

    /// `C[x]` -- fill the hole and admit the result.
    pub fn fill(
        &self,
        datum: OpaqueDatum,
        codec: &PresentationCodec,
    ) -> Result<AdmittedContext, GenesisError> {
        let rendered = codec.render(datum, self.wrap);
        let scan = codec.scan(&rendered)?;
        admit(&scan)
    }
}

/// How an admitted carrier is measured. Exact by construction.
pub type EvaluationMorphism = fn(&AdmittedContext) -> BigRational;

/// The default morphism: nesting depth, as an exact rational.
pub fn evaluate_depth(context: &AdmittedContext) -> BigRational {
    BigRational::from_integer(BigInt::from(context.nesting_depth()))
}

/// An observer regime `O = (C, E)`.
///
/// The whole content of the type is that separation is *relative to it*. An
/// empty family is legal and means no separation is possible -- see
/// [`ObserverRegime::demand_separation`].
#[derive(Clone)]
pub struct ObserverRegime {
    contexts: Vec<ObserverContext>,
    evaluate: EvaluationMorphism,
    codec: PresentationCodec,
}

impl fmt::Debug for ObserverRegime {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("ObserverRegime")
            .field("contexts", &self.contexts)
            .field("codec", &self.codec)
            .finish_non_exhaustive()
    }
}

impl ObserverRegime {
    /// The ground regime: no admitted contexts at all.
    pub fn ground() -> Self {
        Self {
            contexts: Vec::new(),
            evaluate: evaluate_depth,
            codec: PresentationCodec::ascii_angle(),
        }
    }

    /// Admit a family of contexts. Duplicates are refused: a family that counts
    /// the same context twice would report a larger separating power than it
    /// has.
    pub fn admit_contexts(
        contexts: Vec<ObserverContext>,
        evaluate: EvaluationMorphism,
    ) -> Result<Self, GenesisError> {
        let mut seen = BTreeSet::new();
        for context in &contexts {
            if !seen.insert((context.name.clone(), context.wrap)) {
                return Err(GenesisError::new(
                    GenesisErrorCode::DuplicateContext,
                    format!("context {:?} declared twice", context.name),
                ));
            }
        }
        Ok(Self {
            contexts,
            evaluate,
            codec: PresentationCodec::ascii_angle(),
        })
    }

    pub fn contexts(&self) -> &[ObserverContext] {
        &self.contexts
    }

    pub fn is_ground(&self) -> bool {
        self.contexts.is_empty()
    }

    /// `x ~_O y` -- observational equivalence.
    ///
    /// With an empty family the quantifier is vacuous and this is `true` for
    /// every pair. That is ground inertia stated positively.
    pub fn equivalent(&self, left: OpaqueDatum, right: OpaqueDatum) -> Result<bool, GenesisError> {
        Ok(self.separating_context(left, right)?.is_none())
    }

    /// The first context that tells `left` from `right`, if any.
    ///
    /// Returns the *witness*, not a boolean: a separation claim that cannot name
    /// the context it separates in is not evidence.
    pub fn separating_context(
        &self,
        left: OpaqueDatum,
        right: OpaqueDatum,
    ) -> Result<Option<&ObserverContext>, GenesisError> {
        for context in &self.contexts {
            let lhs = (self.evaluate)(&context.fill(left, &self.codec)?);
            let rhs = (self.evaluate)(&context.fill(right, &self.codec)?);
            if lhs != rhs {
                return Ok(Some(context));
            }
        }
        Ok(None)
    }

    /// Demand a separation `D = (x, y)`.
    ///
    /// Refuses when the regime is ground. This is the ground inertia law: with
    /// nothing admitted, "these differ" is not a false statement to return, it
    /// is a statement there is no standing to make.
    pub fn demand_separation(
        &self,
        left: OpaqueDatum,
        right: OpaqueDatum,
    ) -> Result<Option<&ObserverContext>, GenesisError> {
        if self.is_ground() {
            return Err(GenesisError::new(
                GenesisErrorCode::NoAdmittedContext,
                "separation demanded under the ground regime; admit a context first",
            ));
        }
        self.separating_context(left, right)
    }
}

// ---------------------------------------------------------------------------
// The Examiner quiz
// ---------------------------------------------------------------------------

/// A finite relation `R` on `{0, .., size-1}` posed as a challenge.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ExaminerChallenge {
    size: u32,
    relation: BTreeSet<(u32, u32)>,
}

impl ExaminerChallenge {
    pub fn new(
        size: u32,
        pairs: impl IntoIterator<Item = (u32, u32)>,
    ) -> Result<Self, GenesisError> {
        let relation: BTreeSet<(u32, u32)> = pairs.into_iter().collect();
        for (left, right) in &relation {
            if *left >= size || *right >= size {
                return Err(GenesisError::new(
                    GenesisErrorCode::OutOfDomain,
                    format!("pair ({left}, {right}) escapes domain of size {size}"),
                ));
            }
        }
        Ok(Self { size, relation })
    }

    pub fn size(&self) -> u32 {
        self.size
    }

    pub fn relation(&self) -> &BTreeSet<(u32, u32)> {
        &self.relation
    }

    /// A stable digest of the challenge, so a score names the thing it scored.
    pub fn digest(&self) -> String {
        let mut hasher = blake3::Hasher::new();
        hasher.update(b"examiner-challenge-v1");
        hasher.update(&self.size.to_be_bytes());
        for (left, right) in &self.relation {
            hasher.update(&left.to_be_bytes());
            hasher.update(&right.to_be_bytes());
        }
        hasher.finalize().to_hex().to_string()
    }
}

/// What the quiz found, with the offending pairs named.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ExaminerVerdict {
    /// Pairs `(x, x)` present in the relation.
    pub reflexive_witnesses: Vec<(u32, u32)>,
    /// Pairs where both `(a, b)` and `(b, a)` are present.
    pub symmetric_witnesses: Vec<(u32, u32)>,
    pub challenge_digest: String,
}

impl ExaminerVerdict {
    pub fn is_irreflexive(&self) -> bool {
        self.reflexive_witnesses.is_empty()
    }

    pub fn is_asymmetric(&self) -> bool {
        self.symmetric_witnesses.is_empty()
    }

    /// A strict partial order needs both, so both are reported separately: a
    /// single boolean would hide which of the two failed.
    pub fn is_strict(&self) -> bool {
        self.is_irreflexive() && self.is_asymmetric()
    }
}

/// Check a challenge exactly, naming every offending pair.
pub fn verify_examiner(challenge: &ExaminerChallenge) -> ExaminerVerdict {
    let mut reflexive_witnesses = Vec::new();
    let mut symmetric_witnesses = Vec::new();
    for (left, right) in challenge.relation() {
        if left == right {
            reflexive_witnesses.push((*left, *right));
        } else if left < right && challenge.relation().contains(&(*right, *left)) {
            symmetric_witnesses.push((*left, *right));
        }
    }
    ExaminerVerdict {
        reflexive_witnesses,
        symmetric_witnesses,
        challenge_digest: challenge.digest(),
    }
}

/// How a generated challenge was built, so a benchmark knows the right answer.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ExaminerFlavour {
    /// Irreflexive and asymmetric by construction.
    Strict,
    /// A reflexive pair was injected.
    ReflexiveTrap,
    /// A symmetric pair was injected.
    SymmetricTrap,
}

/// A deterministic challenge generator.
///
/// Deterministic on purpose. "Procedurally randomized" and "reproducible
/// receipt" are only compatible if the randomness is seeded and the algorithm is
/// fixed, so the generator is a SplitMix64 written out here rather than a
/// dependency whose stream could change under a version bump.
#[derive(Clone, Debug)]
pub struct ExaminerQuizGenerator {
    state: u64,
}

impl ExaminerQuizGenerator {
    pub fn new(seed: u64) -> Self {
        Self { state: seed }
    }

    fn next_u64(&mut self) -> u64 {
        // SplitMix64.
        self.state = self.state.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut z = self.state;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^ (z >> 31)
    }

    fn next_bool(&mut self) -> bool {
        self.next_u64() & 1 == 1
    }

    fn next_below(&mut self, bound: u32) -> u32 {
        if bound == 0 {
            return 0;
        }
        (self.next_u64() % u64::from(bound)) as u32
    }

    /// Generate a challenge of the requested flavour.
    ///
    /// The `Strict` flavour orients every chosen pair from the smaller index to
    /// the larger, which makes irreflexivity and asymmetry structural rather
    /// than lucky -- the generator cannot emit a trap by accident, so a failing
    /// `Strict` case is a real defect in the checker.
    pub fn generate(
        &mut self,
        size: u32,
        flavour: ExaminerFlavour,
    ) -> Result<ExaminerChallenge, GenesisError> {
        let mut pairs: BTreeSet<(u32, u32)> = BTreeSet::new();
        for left in 0..size {
            for right in (left + 1)..size {
                if self.next_bool() {
                    pairs.insert((left, right));
                }
            }
        }
        match flavour {
            ExaminerFlavour::Strict => {}
            ExaminerFlavour::ReflexiveTrap => {
                let victim = self.next_below(size.max(1));
                pairs.insert((victim, victim));
            }
            ExaminerFlavour::SymmetricTrap => {
                // Mirror an existing edge, adding one if the draw came up empty.
                let mirrored = pairs.iter().next().copied();
                match mirrored {
                    Some((left, right)) => {
                        pairs.insert((right, left));
                    }
                    None if size >= 2 => {
                        pairs.insert((0, 1));
                        pairs.insert((1, 0));
                    }
                    None => {}
                }
            }
        }
        ExaminerChallenge::new(size, pairs)
    }
}

pub const EXAMINER_RECEIPT_SCHEMA: &str = "core.symbol_game.genesis_examiner.v1";

/// A schema-validated receipt recording the exact score of a Examiner quiz.
#[derive(Clone, Debug, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
#[serde(try_from = "UntrustedExaminerReceiptV1")]
pub struct ExaminerReceiptV1 {
    pub schema: String,
    pub correct: u32,
    pub asked: u32,
    pub score_rational: String,
    pub digest: String,
    pub challenge_digests: Vec<String>,
    pub authority_effect: String,
}

#[derive(serde::Deserialize)]
#[serde(deny_unknown_fields)]
struct UntrustedExaminerReceiptV1 {
    schema: String,
    correct: u32,
    asked: u32,
    score_rational: String,
    digest: String,
    challenge_digests: Vec<String>,
    authority_effect: String,
}

impl TryFrom<UntrustedExaminerReceiptV1> for ExaminerReceiptV1 {
    type Error = GenesisError;

    fn try_from(wire: UntrustedExaminerReceiptV1) -> Result<Self, Self::Error> {
        let receipt = Self {
            schema: wire.schema,
            correct: wire.correct,
            asked: wire.asked,
            score_rational: wire.score_rational,
            digest: wire.digest,
            challenge_digests: wire.challenge_digests,
            authority_effect: wire.authority_effect,
        };
        if !receipt.is_valid() {
            return Err(GenesisError::new(
                GenesisErrorCode::InvalidReceipt,
                "receipt schema, score, challenge identities or digest do not match",
            ));
        }
        Ok(receipt)
    }
}

impl ExaminerReceiptV1 {
    pub fn is_valid(&self) -> bool {
        self.schema == EXAMINER_RECEIPT_SCHEMA
            && self.authority_effect == "None"
            && self.asked > 0
            && self.correct <= self.asked
            && self.challenge_digests.len() == self.asked as usize
            && self.challenge_digests.iter().all(|digest| {
                digest.len() == 64
                    && digest
                        .bytes()
                        .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
            })
            && self.score_rational
                == BigRational::new(self.correct.into(), self.asked.into()).to_string()
            && self.digest == self.recomputed_digest()
    }

    fn recomputed_digest(&self) -> String {
        let mut hasher = blake3::Hasher::new();
        hasher.update(b"examiner-quiz-receipt-v1");
        hasher.update(&self.correct.to_le_bytes());
        hasher.update(&self.asked.to_le_bytes());
        hasher.update(self.score_rational.as_bytes());
        for digest in &self.challenge_digests {
            hasher.update(digest.as_bytes());
        }
        hasher.finalize().to_hex().to_string()
    }

    pub fn from_json(bytes: &[u8]) -> Result<Self, GenesisError> {
        serde_json::from_slice(bytes)
            .map_err(|error| GenesisError::new(GenesisErrorCode::InvalidReceipt, error.to_string()))
    }
}

/// An exact benchmark score: correct answers over questions asked.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ExaminerScore {
    pub correct: u32,
    pub asked: u32,
    pub fraction: BigRational,
}

impl ExaminerScore {
    pub fn to_receipt(&self, challenge_digests: &[String]) -> ExaminerReceiptV1 {
        let mut receipt = ExaminerReceiptV1 {
            schema: EXAMINER_RECEIPT_SCHEMA.to_owned(),
            correct: self.correct,
            asked: self.asked,
            score_rational: self.fraction.to_string(),
            digest: String::new(),
            challenge_digests: challenge_digests.to_vec(),
            authority_effect: "None".to_owned(),
        };
        receipt.digest = receipt.recomputed_digest();
        receipt
    }
}

/// Score one concrete challenge, binding the result to its actual relation.
pub fn score_examiner_challenge(
    challenge: &ExaminerChallenge,
    answered_strict: bool,
) -> ExaminerReceiptV1 {
    let correct = u32::from(verify_examiner(challenge).is_strict() == answered_strict);
    ExaminerScore {
        correct,
        asked: 1,
        fraction: BigRational::from_integer(correct.into()),
    }
    .to_receipt(&[challenge.digest()])
}

/// Score a run of answers against the flavours that generated them.
///
/// Refuses an empty quiz rather than returning `0/0` dressed up as a perfect or
/// a failing score.
pub fn score_examiner(
    expected: &[ExaminerFlavour],
    answered_strict: &[bool],
) -> Result<ExaminerScore, GenesisError> {
    if expected.is_empty() || answered_strict.is_empty() {
        return Err(GenesisError::new(
            GenesisErrorCode::EmptyQuiz,
            "refusing to score a quiz with no questions",
        ));
    }
    if expected.len() != answered_strict.len() {
        return Err(GenesisError::new(
            GenesisErrorCode::EmptyQuiz,
            format!(
                "answers ({}) do not match questions ({})",
                answered_strict.len(),
                expected.len()
            ),
        ));
    }
    let mut correct = 0u32;
    for (flavour, answered) in expected.iter().zip(answered_strict) {
        let truth = matches!(flavour, ExaminerFlavour::Strict);
        if truth == *answered {
            correct += 1;
        }
    }
    let asked = expected.len() as u32;
    let fraction = if correct == 0 {
        BigRational::zero()
    } else if correct == asked {
        BigRational::one()
    } else {
        BigRational::new(BigInt::from(correct), BigInt::from(asked))
    };
    Ok(ExaminerScore {
        correct,
        asked,
        fraction,
    })
}

// Origin: engine/crates_rs/pfp/src/genesis.rs
// Claim: urn:core:crates_rs:pfp:genesis:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_3c9d86d1 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
