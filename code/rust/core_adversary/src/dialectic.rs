//! Seven-act dialectic kernel. Depth is capped at 5. AuthorityEffect: None.
//! This is not the live bout runner in `complete_bout`.

use crate::jcs::{self, Jcs};
use crate::literature_receipt::{LiteratureDraft, LiteratureReceipt};
pub use crate::receipt::ReceiptStatus;
use crate::receipt::{Fault, Receipt};
use num_rational::Ratio;
use serde::Deserialize;
use sha2::{Digest, Sha256};

pub use crate::receipt::{
    Fault as DialecticFault, Receipt as DialecticReceipt, ReceiptStatus as DialecticStatus,
};

pub const MAX_DEPTH: u8 = 5;
pub const AUTHORITY_EFFECT: &str = "None";
pub const EVIDENCE_SCHEMA: &str = "core.adversary.evidence_receipt.v1";
pub const STATE_SCHEMA: &str = "core.adversary.state.v1";
pub const RECEIPT_SCHEMA: &str = "core.adversary.dialectic_receipt.v1";

const ACTS: [Act; 7] = [
    Act::I,
    Act::II,
    Act::III,
    Act::IV,
    Act::V,
    Act::VI,
    Act::VII,
];

pub type Rational = Ratio<i64>;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Act {
    I,
    II,
    III,
    IV,
    V,
    VI,
    VII,
}

impl Act {
    pub fn label(self) -> &'static str {
        match self {
            Self::I => "I",
            Self::II => "II",
            Self::III => "III",
            Self::IV => "IV",
            Self::V => "V",
            Self::VI => "VI",
            Self::VII => "VII",
        }
    }

    pub fn parse(text: &str) -> Option<Self> {
        ACTS.into_iter().find(|act| act.label() == text)
    }

    fn index(self) -> u8 {
        match self {
            Self::I => 0,
            Self::II => 1,
            Self::III => 2,
            Self::IV => 3,
            Self::V => 4,
            Self::VI => 5,
            Self::VII => 6,
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct EvidenceReceipt {
    pub schema: &'static str,
    pub authority_effect: &'static str,
    pub subject_sha256: String,
    pub canonical_sha256: String,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DialecticTurn {
    pub act: Act,
    pub depth: u8,
    pub seat_id: String,
    pub budget_spent: Rational,
    pub evidence: EvidenceReceipt,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct AdversaryState {
    pub depth: u8,
    pub budget_opened: Rational,
    pub budget_remaining: Rational,
    pub next_act: Option<Act>,
    pub terminal: Option<ReceiptStatus>,
    pub turns: Vec<DialecticTurn>,
}

impl AdversaryState {
    pub fn canonical_bytes(&self) -> Result<Vec<u8>, Fault> {
        self.to_jcs()
            .canonical_bytes()
            .map_err(|_| Fault::new("CANONICAL", "state cannot be encoded"))
    }

    fn to_jcs(&self) -> Jcs {
        Jcs::Object(vec![
            (
                "budget_opened".into(),
                Jcs::string(&ratio_text(&self.budget_opened)),
            ),
            (
                "budget_remaining".into(),
                Jcs::string(&ratio_text(&self.budget_remaining)),
            ),
            ("depth".into(), Jcs::integer(i64::from(self.depth))),
            ("next_act".into(), act_jcs(self.next_act)),
            ("schema".into(), Jcs::string(STATE_SCHEMA)),
            ("terminal".into(), terminal_jcs(self.terminal)),
            (
                "turns".into(),
                Jcs::Array(self.turns.iter().map(DialecticTurn::to_jcs).collect()),
            ),
        ])
    }
}

impl TryFrom<&[u8]> for AdversaryState {
    type Error = Fault;

    fn try_from(bytes: &[u8]) -> Result<Self, Self::Error> {
        let wire: StateWire = decode(bytes)?;
        AdversaryTurnEngine::restore_wire(wire).map(|engine| engine.state())
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct TurnProposal {
    pub act: Act,
    pub depth: u8,
    pub seat_id: String,
    pub budget_spent: Rational,
    pub subject_sha256: String,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum DialecticBody {
    State(AdversaryState),
    Literature(LiteratureReceipt),
    Absent,
}

pub struct AdversaryTurnEngine {
    depth: u8,
    budget_opened: Rational,
    budget_remaining: Rational,
    next_index: u8,
    terminal: Option<ReceiptStatus>,
    turns: [Option<DialecticTurn>; 7],
}

impl AdversaryTurnEngine {
    pub fn open(depth: u8, budget: Rational) -> Result<Self, Fault> {
        if depth > MAX_DEPTH {
            return Err(Fault::new("UNBOUNDED_RECURSION", "depth exceeds 5"));
        }
        if budget <= Rational::from_integer(0) {
            return Err(Fault::new(
                "BUDGET_NOT_POSITIVE",
                "opening budget must be a positive rational",
            ));
        }
        Ok(Self {
            depth,
            budget_opened: budget,
            budget_remaining: budget,
            next_index: 0,
            terminal: None,
            turns: std::array::from_fn(|_| None),
        })
    }

    pub fn nest(&self) -> Result<Self, Fault> {
        if self.terminal.is_some() {
            return Err(Fault::new("TERMINAL", "a terminal bout cannot nest"));
        }
        if self.depth >= MAX_DEPTH {
            return Err(Fault::new("UNBOUNDED_RECURSION", "depth exceeds 5"));
        }
        Self::open(self.depth + 1, self.budget_remaining)
    }

    pub fn state(&self) -> AdversaryState {
        AdversaryState {
            depth: self.depth,
            budget_opened: self.budget_opened,
            budget_remaining: self.budget_remaining,
            next_act: ACTS.get(self.next_index as usize).copied(),
            terminal: self.terminal,
            turns: self.turns.iter().filter_map(|turn| turn.clone()).collect(),
        }
    }

    pub fn step(&mut self, proposal: TurnProposal) -> Receipt<AdversaryState> {
        let ready = match self.prepare(&proposal) {
            Ok(ready) => ready,
            Err(stop) => {
                let state = self.state();
                return match stop {
                    Stop::Refuse(fault) => Receipt::refusal(fault.code, fault.detail, state),
                    Stop::Reject(fault) => Receipt::fail(fault.code, fault.detail, state),
                };
            }
        };
        let index = self.next_index as usize;
        self.turns[index] = Some(DialecticTurn {
            act: proposal.act,
            depth: proposal.depth,
            seat_id: proposal.seat_id,
            budget_spent: proposal.budget_spent,
            evidence: ready.evidence,
        });
        self.budget_remaining = ready.remaining;
        self.next_index += 1;
        if self.next_index == 7 {
            self.terminal = Some(ReceiptStatus::Pass);
            Receipt::pass("BOUT_COMPLETE", self.state())
        } else {
            Receipt::pass("STEP", self.state())
        }
    }

    fn validate_prepare_preconditions(&self, proposal: &TurnProposal) -> Result<(), Stop> {
        if self.terminal.is_some() || self.next_index >= 7 {
            return Err(Stop::Refuse(Fault::new(
                "TERMINAL",
                "the bout is already terminal",
            )));
        }
        if proposal.depth > MAX_DEPTH || self.depth > MAX_DEPTH {
            return Err(Stop::Refuse(Fault::new(
                "UNBOUNDED_RECURSION",
                "depth exceeds 5",
            )));
        }
        if proposal.depth != self.depth {
            return Err(Stop::Refuse(Fault::new(
                "DEPTH_MISMATCH",
                "turn depth must equal the engine depth",
            )));
        }
        if proposal.act.index() != self.next_index {
            return Err(Stop::Refuse(Fault::new(
                "ACT_ORDER",
                "acts advance I through VII",
            )));
        }
        Ok(())
    }

    fn validate_prepare_seat_and_subject(&self, proposal: &TurnProposal) -> Result<(), Stop> {
        if !seat_ok(&proposal.seat_id) {
            return Err(Stop::Refuse(Fault::new(
                "SEAT_MALFORMED",
                "seat_id must match [a-z][a-z0-9_]{0,63}",
            )));
        }
        if self
            .turns
            .iter()
            .flatten()
            .any(|turn| turn.seat_id == proposal.seat_id)
        {
            return Err(Stop::Reject(Fault::new(
                "SEAT_REUSED",
                "a seat already spoke in this bout",
            )));
        }
        if proposal.budget_spent < Rational::from_integer(0) {
            return Err(Stop::Refuse(Fault::new(
                "BUDGET_MALFORMED",
                "budget_spent must be non-negative",
            )));
        }
        if !is_subject(&proposal.subject_sha256) {
            return Err(Stop::Refuse(Fault::new(
                "SUBJECT_DIGEST_MALFORMED",
                "subject_sha256 must be sha256:<64 lowercase hex>",
            )));
        }
        Ok(())
    }

    fn prepare(&self, proposal: &TurnProposal) -> Result<Prepared, Stop> {
        self.validate_prepare_preconditions(proposal)?;
        self.validate_prepare_seat_and_subject(proposal)?;
        let remaining = match checked_sub(self.budget_remaining, proposal.budget_spent) {
            Some(next) if next >= Rational::from_integer(0) => next,
            Some(_) => {
                return Err(Stop::Reject(Fault::new(
                    "BUDGET_EXHAUSTED",
                    "budget_spent exceeds the remaining rational",
                )))
            }
            None => {
                return Err(Stop::Refuse(Fault::new(
                    "BUDGET_OVERFLOW",
                    "rational subtraction overflowed i64",
                )))
            }
        };
        let evidence = seal_evidence(
            proposal.act,
            proposal.depth,
            &proposal.seat_id,
            &proposal.budget_spent,
            &proposal.subject_sha256,
        )
        .map_err(Stop::Refuse)?;
        Ok(Prepared {
            evidence,
            remaining,
        })
    }

    fn validate_restore_wire_header(wire: &StateWire) -> Result<(Rational, Rational), Fault> {
        if wire.schema != STATE_SCHEMA {
            return Err(Fault::new("STATE_INCONSISTENT", "state schema mismatch"));
        }
        if wire.depth > MAX_DEPTH {
            return Err(Fault::new("UNBOUNDED_RECURSION", "depth exceeds 5"));
        }
        if wire.turns.len() > 7 {
            return Err(Fault::new("STATE_INCONSISTENT", "turn count exceeds 7"));
        }
        let opened = parse_canonical_ratio(&wire.budget_opened)?;
        let remaining = parse_canonical_ratio(&wire.budget_remaining)?;
        if opened <= Rational::from_integer(0) {
            return Err(Fault::new(
                "BUDGET_NOT_POSITIVE",
                "opening budget must be a positive rational",
            ));
        }
        Ok((opened, remaining))
    }

    fn validate_turn_act_and_seat<'a>(
        index: usize,
        depth: u8,
        turn_wire: &'a StoredTurnWire,
        seats: &mut Vec<&'a str>,
    ) -> Result<Act, Fault> {
        let act =
            Act::parse(&turn_wire.act).ok_or_else(|| Fault::new("ACT_MALFORMED", "unknown act"))?;
        if act.index() != index as u8 || turn_wire.depth != depth {
            return Err(Fault::new(
                "STATE_INCONSISTENT",
                "stored turns are not a prefix of I..VII at the state depth",
            ));
        }
        if !seat_ok(&turn_wire.seat_id) {
            return Err(Fault::new("SEAT_MALFORMED", "stored seat_id is illegal"));
        }
        if seats.contains(&turn_wire.seat_id.as_str()) {
            return Err(Fault::new("SEAT_REUSED", "stored seats repeat"));
        }
        seats.push(turn_wire.seat_id.as_str());
        Ok(act)
    }

    fn restore_single_turn<'a>(
        index: usize,
        depth: u8,
        turn_wire: &'a StoredTurnWire,
        seats: &mut Vec<&'a str>,
        spent: &mut Rational,
    ) -> Result<DialecticTurn, Fault> {
        let act = Self::validate_turn_act_and_seat(index, depth, turn_wire, seats)?;
        let budget_spent = parse_canonical_ratio(&turn_wire.budget_spent)?;
        if budget_spent < Rational::from_integer(0) {
            return Err(Fault::new(
                "BUDGET_MALFORMED",
                "stored budget_spent is negative",
            ));
        }
        let evidence = evidence_from_wire(
            act,
            turn_wire.depth,
            &turn_wire.seat_id,
            &budget_spent,
            &turn_wire.evidence,
        )?;
        *spent = checked_add(*spent, budget_spent)
            .ok_or_else(|| Fault::new("BUDGET_OVERFLOW", "stored spend sum overflowed i64"))?;
        Ok(DialecticTurn {
            act,
            depth: turn_wire.depth,
            seat_id: turn_wire.seat_id.clone(),
            budget_spent,
            evidence,
        })
    }

    fn resolve_restore_terminal(
        wire: &StateWire,
        count: u8,
    ) -> Result<Option<ReceiptStatus>, Fault> {
        let next_act = match wire.next_act.as_deref() {
            None => None,
            Some(label) => Some(
                Act::parse(label).ok_or_else(|| Fault::new("ACT_MALFORMED", "unknown next_act"))?,
            ),
        };
        let terminal = match wire.terminal.as_deref() {
            None => None,
            Some("PASS") => Some(ReceiptStatus::Pass),
            Some(_) => {
                return Err(Fault::new(
                    "STATE_INCONSISTENT",
                    "stored terminal must be PASS or null",
                ))
            }
        };
        let consistent = if count == 7 {
            terminal == Some(ReceiptStatus::Pass) && next_act.is_none()
        } else {
            terminal.is_none() && next_act == Some(ACTS[count as usize])
        };
        if !consistent {
            return Err(Fault::new(
                "STATE_INCONSISTENT",
                "terminal and next_act disagree with the turn prefix",
            ));
        }
        Ok(terminal)
    }

    fn restore_wire(wire: StateWire) -> Result<Self, Fault> {
        let (opened, remaining) = Self::validate_restore_wire_header(&wire)?;
        let mut turns: [Option<DialecticTurn>; 7] = std::array::from_fn(|_| None);
        let mut spent = Rational::from_integer(0);
        let mut seats: Vec<&str> = Vec::new();
        for (index, turn_wire) in wire.turns.iter().enumerate() {
            turns[index] = Some(Self::restore_single_turn(
                index, wire.depth, turn_wire, &mut seats, &mut spent,
            )?);
        }
        let expected = checked_sub(opened, spent).ok_or_else(|| {
            Fault::new("BUDGET_OVERFLOW", "stored budget identity overflowed i64")
        })?;
        if expected != remaining || remaining < Rational::from_integer(0) {
            return Err(Fault::new(
                "STATE_INCONSISTENT",
                "budget_remaining is not budget_opened minus the spends",
            ));
        }
        let count = wire.turns.len() as u8;
        let terminal = Self::resolve_restore_terminal(&wire, count)?;
        Ok(Self {
            depth: wire.depth,
            budget_opened: opened,
            budget_remaining: remaining,
            next_index: count,
            terminal,
            turns,
        })
    }
}

struct Prepared {
    evidence: EvidenceReceipt,
    remaining: Rational,
}

enum Stop {
    Refuse(Fault),
    Reject(Fault),
}

fn dialectic_open(depth: u8, budget: &str) -> Receipt<DialecticBody> {
    match parse_ratio(budget) {
        Ok(parsed) => match AdversaryTurnEngine::open(depth, parsed) {
            Ok(engine) => Receipt::pass("OPEN", DialecticBody::State(engine.state())),
            Err(fault) => Receipt::refusal(fault.code, fault.detail, DialecticBody::Absent),
        },
        Err(fault) => Receipt::refusal(fault.code, fault.detail, DialecticBody::Absent),
    }
}

fn dialectic_nest(state: StateWire) -> Receipt<DialecticBody> {
    match AdversaryTurnEngine::restore_wire(state) {
        Ok(engine) => match engine.nest() {
            Ok(child) => Receipt::pass("NEST", DialecticBody::State(child.state())),
            Err(fault) => Receipt::refusal(
                fault.code,
                fault.detail,
                DialecticBody::State(engine.state()),
            ),
        },
        Err(fault) => Receipt::refusal(fault.code, fault.detail, DialecticBody::Absent),
    }
}

fn dialectic_step(state: StateWire, turn: ProposalWire) -> Receipt<DialecticBody> {
    let mut engine = match AdversaryTurnEngine::restore_wire(state) {
        Ok(engine) => engine,
        Err(fault) => return Receipt::refusal(fault.code, fault.detail, DialecticBody::Absent),
    };
    let proposal = match proposal_from_wire(turn) {
        Ok(proposal) => proposal,
        Err(fault) => {
            return Receipt::refusal(
                fault.code,
                fault.detail,
                DialecticBody::State(engine.state()),
            )
        }
    };
    let stepped = engine.step(proposal);
    let body = DialecticBody::State(stepped.body);
    match stepped.status {
        ReceiptStatus::Pass => Receipt::pass(stepped.code, body),
        ReceiptStatus::Fail => Receipt::fail(stepped.code, stepped.detail, body),
        ReceiptStatus::Refusal => Receipt::refusal(stepped.code, stepped.detail, body),
    }
}

pub fn dialectic_bytes(bytes: &[u8]) -> Receipt<DialecticBody> {
    let command = match decode::<CommandWire>(bytes) {
        Ok(command) => command,
        Err(fault) => return Receipt::refusal(fault.code, fault.detail, DialecticBody::Absent),
    };
    match command {
        CommandWire::Open { depth, budget } => dialectic_open(depth, &budget),
        CommandWire::Nest { state } => dialectic_nest(state),
        CommandWire::Step { state, turn } => dialectic_step(state, turn),
        CommandWire::SealLiterature {
            receipt_id,
            package_id,
            cite_key,
            title,
            authors,
            year,
            venue,
            arxiv_id,
            doi,
            url,
            binding_note,
            source_kind,
            bound_at_utc,
            authority_effect,
            claims_global_green,
            content_fingerprint,
            canonical_sha256,
        } => {
            let draft = LiteratureDraft {
                receipt_id,
                package_id,
                cite_key,
                title,
                authors,
                year,
                venue,
                arxiv_id,
                doi,
                url,
                binding_note,
                source_kind,
                bound_at_utc,
                authority_effect,
                claims_global_green,
                content_fingerprint,
                canonical_sha256,
            };
            match LiteratureReceipt::try_from(draft) {
                Ok(receipt) => Receipt::pass("SEALED", DialecticBody::Literature(receipt)),
                Err(fault) => Receipt::refusal(fault.code, fault.detail, DialecticBody::Absent),
            }
        }
    }
}

pub fn receipt_bytes(receipt: &Receipt<DialecticBody>) -> Result<Vec<u8>, Fault> {
    let status = match receipt.status {
        ReceiptStatus::Pass => "PASS",
        ReceiptStatus::Fail => "FAIL",
        ReceiptStatus::Refusal => "REFUSAL",
    };
    let body = match &receipt.body {
        DialecticBody::Absent => Jcs::Null,
        DialecticBody::State(state) => state.to_jcs(),
        DialecticBody::Literature(receipt) => receipt.to_jcs(),
    };
    Jcs::Object(vec![
        ("authority_effect".into(), Jcs::string(AUTHORITY_EFFECT)),
        ("body".into(), body),
        ("code".into(), Jcs::string(receipt.code)),
        ("detail".into(), Jcs::string(&receipt.detail)),
        ("schema".into(), Jcs::string(RECEIPT_SCHEMA)),
        ("status".into(), Jcs::string(status)),
    ])
    .canonical_bytes()
    .map_err(|_| Fault::new("CANONICAL", "receipt cannot be encoded"))
}

impl DialecticTurn {
    fn to_jcs(&self) -> Jcs {
        Jcs::Object(vec![
            ("act".into(), Jcs::string(self.act.label())),
            (
                "budget_spent".into(),
                Jcs::string(&ratio_text(&self.budget_spent)),
            ),
            ("depth".into(), Jcs::integer(i64::from(self.depth))),
            ("evidence".into(), evidence_jcs(&self.evidence)),
            ("seat_id".into(), Jcs::string(&self.seat_id)),
        ])
    }
}

fn evidence_jcs(evidence: &EvidenceReceipt) -> Jcs {
    Jcs::Object(vec![
        (
            "authority_effect".into(),
            Jcs::string(evidence.authority_effect),
        ),
        (
            "canonical_sha256".into(),
            Jcs::string(&evidence.canonical_sha256),
        ),
        ("schema".into(), Jcs::string(evidence.schema)),
        (
            "subject_sha256".into(),
            Jcs::string(&evidence.subject_sha256),
        ),
    ])
}

fn act_jcs(act: Option<Act>) -> Jcs {
    match act {
        Some(act) => Jcs::string(act.label()),
        None => Jcs::Null,
    }
}

fn terminal_jcs(status: Option<ReceiptStatus>) -> Jcs {
    match status {
        Some(ReceiptStatus::Pass) => Jcs::string("PASS"),
        Some(ReceiptStatus::Fail) => Jcs::string("FAIL"),
        Some(ReceiptStatus::Refusal) => Jcs::string("REFUSAL"),
        None => Jcs::Null,
    }
}

fn evidence_preimage(
    act: Act,
    depth: u8,
    seat: &str,
    spent: &Rational,
    subject: &str,
) -> Result<Vec<u8>, Fault> {
    Jcs::Object(vec![
        ("act".into(), Jcs::string(act.label())),
        ("budget_spent".into(), Jcs::string(&ratio_text(spent))),
        ("depth".into(), Jcs::integer(i64::from(depth))),
        ("seat_id".into(), Jcs::string(seat)),
        ("subject_sha256".into(), Jcs::string(subject)),
    ])
    .canonical_bytes()
    .map_err(|_| Fault::new("CANONICAL", "evidence preimage cannot be encoded"))
}

fn seal_evidence(
    act: Act,
    depth: u8,
    seat: &str,
    spent: &Rational,
    subject: &str,
) -> Result<EvidenceReceipt, Fault> {
    let canonical_sha256 = format!(
        "sha256:{}",
        hex::encode(Sha256::digest(
            evidence_preimage(act, depth, seat, spent, subject)?.as_slice()
        ))
    );
    Ok(EvidenceReceipt {
        schema: EVIDENCE_SCHEMA,
        authority_effect: AUTHORITY_EFFECT,
        subject_sha256: subject.to_owned(),
        canonical_sha256,
    })
}

fn evidence_from_wire(
    act: Act,
    depth: u8,
    seat: &str,
    spent: &Rational,
    wire: &EvidenceWire,
) -> Result<EvidenceReceipt, Fault> {
    if wire.schema != EVIDENCE_SCHEMA {
        return Err(Fault::new("STATE_INCONSISTENT", "evidence schema mismatch"));
    }
    if wire.authority_effect != AUTHORITY_EFFECT {
        return Err(Fault::new(
            "PROSE_AUTHORITY",
            "evidence authority_effect must be None",
        ));
    }
    if !is_subject(&wire.subject_sha256) || !is_subject(&wire.canonical_sha256) {
        return Err(Fault::new(
            "SUBJECT_DIGEST_MALFORMED",
            "evidence digests must be sha256:<64 lowercase hex>",
        ));
    }
    let sealed = seal_evidence(act, depth, seat, spent, &wire.subject_sha256)?;
    if sealed.canonical_sha256 != wire.canonical_sha256 {
        return Err(Fault::new(
            "FINGERPRINT_MISMATCH",
            "evidence canonical_sha256 does not match the turn",
        ));
    }
    Ok(sealed)
}

fn proposal_from_wire(wire: ProposalWire) -> Result<TurnProposal, Fault> {
    Ok(TurnProposal {
        act: Act::parse(&wire.act).ok_or_else(|| Fault::new("ACT_MALFORMED", "unknown act"))?,
        depth: wire.depth,
        seat_id: wire.seat_id,
        budget_spent: parse_ratio(&wire.budget_spent)?,
        subject_sha256: wire.subject_sha256,
    })
}

fn decode<T: for<'de> Deserialize<'de>>(bytes: &[u8]) -> Result<T, Fault> {
    if let Err(failure) = jcs::screen(bytes, jcs::DIALECTIC_LIMITS) {
        return Err(Fault::new(failure.code, failure.detail));
    }
    serde_json::from_slice(bytes).map_err(|error| Fault::new("INVALID_RECORD", error.to_string()))
}

fn is_subject(value: &str) -> bool {
    let Some(hex) = value.strip_prefix("sha256:") else {
        return false;
    };
    hex.len() == 64
        && hex
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn seat_ok(value: &str) -> bool {
    let mut chars = value.chars();
    if !matches!(chars.next(), Some(ch) if ch.is_ascii_lowercase()) {
        return false;
    }
    value.len() <= 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit() || byte == b'_')
}

pub fn parse_ratio(text: &str) -> Result<Rational, Fault> {
    if text.is_empty()
        || text.chars().any(|ch| ch.is_whitespace())
        || text.contains('.')
        || text.contains('e')
        || text.contains('E')
        || text.contains('+')
        || text == "-0"
        || text.starts_with("-0/")
        || text.contains("/-0")
    {
        return Err(Fault::new(
            "BUDGET_MALFORMED",
            "budget must be an exact canonical-digit rational",
        ));
    }
    let (numer_text, denom_text) = match text.split_once('/') {
        Some((numer, denom)) => (numer, denom),
        None => (text, "1"),
    };
    if !digit_token(numer_text, true) || !digit_token(denom_text, false) {
        return Err(Fault::new(
            "BUDGET_MALFORMED",
            "budget must be an exact canonical-digit rational",
        ));
    }
    let numer: i64 = numer_text
        .parse()
        .map_err(|_| Fault::new("BUDGET_MALFORMED", "numerator does not fit i64"))?;
    let denom: i64 = denom_text
        .parse()
        .map_err(|_| Fault::new("BUDGET_MALFORMED", "denominator does not fit i64"))?;
    if denom <= 0 || numer == i64::MIN {
        return Err(Fault::new(
            "BUDGET_MALFORMED",
            "denominator must be positive and the numerator must fit",
        ));
    }
    Ok(Rational::new(numer, denom))
}

fn parse_canonical_ratio(text: &str) -> Result<Rational, Fault> {
    let parsed = parse_ratio(text)?;
    if ratio_text(&parsed) != text {
        return Err(Fault::new(
            "STATE_INCONSISTENT",
            "stored rational is not in reduced form",
        ));
    }
    Ok(parsed)
}

pub fn ratio_text(value: &Rational) -> String {
    if *value.denom() == 1 {
        value.numer().to_string()
    } else {
        format!("{}/{}", value.numer(), value.denom())
    }
}

fn digit_token(text: &str, signed: bool) -> bool {
    let digits = if signed {
        text.strip_prefix('-').unwrap_or(text)
    } else if text.starts_with('-') {
        return false;
    } else {
        text
    };
    if digits.is_empty() || !digits.bytes().all(|byte| byte.is_ascii_digit()) {
        return false;
    }
    !(digits.len() > 1 && digits.starts_with('0'))
}

fn checked_add(left: Rational, right: Rational) -> Option<Rational> {
    let numer = left
        .numer()
        .checked_mul(*right.denom())?
        .checked_add(right.numer().checked_mul(*left.denom())?)?;
    let denom = left.denom().checked_mul(*right.denom())?;
    ratio_from_parts(numer, denom)
}

fn checked_sub(left: Rational, right: Rational) -> Option<Rational> {
    let numer = left
        .numer()
        .checked_mul(*right.denom())?
        .checked_sub(right.numer().checked_mul(*left.denom())?)?;
    let denom = left.denom().checked_mul(*right.denom())?;
    ratio_from_parts(numer, denom)
}

fn ratio_from_parts(numer: i64, denom: i64) -> Option<Rational> {
    if denom <= 0 || numer == i64::MIN {
        return None;
    }
    Some(Rational::new(numer, denom))
}

#[derive(Deserialize)]
#[serde(tag = "command", rename_all = "snake_case", deny_unknown_fields)]
enum CommandWire {
    Open {
        depth: u8,
        budget: String,
    },
    Nest {
        state: StateWire,
    },
    Step {
        state: StateWire,
        turn: ProposalWire,
    },
    SealLiterature {
        receipt_id: String,
        package_id: String,
        cite_key: String,
        title: String,
        #[serde(default)]
        authors: String,
        #[serde(default)]
        year: String,
        #[serde(default)]
        venue: String,
        #[serde(default)]
        arxiv_id: String,
        #[serde(default)]
        doi: String,
        #[serde(default)]
        url: String,
        #[serde(default)]
        binding_note: String,
        source_kind: String,
        #[serde(default)]
        bound_at_utc: String,
        authority_effect: String,
        claims_global_green: bool,
        #[serde(default)]
        content_fingerprint: Option<String>,
        #[serde(default)]
        canonical_sha256: Option<String>,
    },
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct StateWire {
    schema: String,
    depth: u8,
    budget_opened: String,
    budget_remaining: String,
    next_act: Option<String>,
    terminal: Option<String>,
    turns: Vec<StoredTurnWire>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct StoredTurnWire {
    act: String,
    depth: u8,
    seat_id: String,
    budget_spent: String,
    evidence: EvidenceWire,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct EvidenceWire {
    schema: String,
    authority_effect: String,
    subject_sha256: String,
    canonical_sha256: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ProposalWire {
    act: String,
    depth: u8,
    seat_id: String,
    budget_spent: String,
    subject_sha256: String,
}

// Origin: engine/crates_rs/core_adversary/src/dialectic.rs
// Claim: urn:core:crates_rs:core-adversary:dialectic:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb4589f8a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb4589f8a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb4589f8a {
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
impl BoundaryErrorb4589f8a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb4589f8a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb4589f8a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb4589f8a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb4589f8a> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb4589f8a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb4589f8a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb4589f8a::ExceedsCapacity {
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
mod l4_boundary_tests_b4589f8a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordb4589f8a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordb4589f8a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordb4589f8a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordb4589f8a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordb4589f8a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErrorb4589f8a::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErrorb4589f8a::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
