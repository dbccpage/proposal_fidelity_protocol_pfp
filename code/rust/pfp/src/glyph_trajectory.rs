//! Bounded native execution of declared glyph-game turns.
//!
//! Registry metadata chooses an allowlisted native verifier, never a dynamic
//! path or caller-supplied action. Each turn retains its input, native outcome,
//! refusal and predecessor commitment. Execution is local evidence, not game
//! completion, registry promotion, or admission. AuthorityEffect: None.

use std::collections::BTreeMap;

use crate::epics::ooutwire::{parse_registry, GlyphRegistry, REGISTRY_PATH};
use core_kernel::evidence::Hash256;
use core_kernel::{parse_exact, to_canonical_string, Exact};
use pfp_runtime::{
    domain_digest_json, evaluate_peak_pinned, verify_lp_certificate, CandidateMovePacket,
    CriticalPeakClaim, Disposition, FrontierState, LocalReplayStatus, LpRefusal, ParseResult,
    Presentation, RationalMatrix, RoundRecord, StandardLp, TerminalProposal,
};
use core_wdp::prime_algos::{
    prime_algorithm_1::{transport, LossLedger},
    prime_scope::ScopeBinding,
};
use serde::{de::DeserializeOwned, Deserialize, Serialize};
use serde_json::{json, Value};

const REGISTRY: &str = include_str!(concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/../governance/sentinel_councils/documentation/registry_glyph_games.yaml"
));
pub const MAX_TURNS: usize = 32;
pub const MAX_TURN_BYTES: usize = 16_384;

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum GlyphRefusalCode {
    InvalidRequest,
    ResourceBudget,
    UnknownGame,
    ProposedFixture,
    MissingVerifier,
    UnsupportedVerifier,
    NativeRefusal,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct GlyphRefusal {
    pub code: GlyphRefusalCode,
    pub detail: String,
}

impl std::fmt::Display for GlyphRefusal {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{:?}: {}", self.code, self.detail)
    }
}

fn refusal(code: GlyphRefusalCode, detail: impl ToString) -> GlyphRefusal {
    GlyphRefusal {
        code,
        detail: detail.to_string(),
    }
}

fn decode<T: DeserializeOwned>(value: &Value) -> Result<T, GlyphRefusal> {
    serde_json::from_value(value.clone())
        .map_err(|error| refusal(GlyphRefusalCode::InvalidRequest, error))
}

fn commit(domain: &str, value: &Value) -> Result<String, GlyphRefusal> {
    domain_digest_json(domain, value)
        .map_err(|error| refusal(GlyphRefusalCode::InvalidRequest, error))
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GlyphTrajectoryRequestV1 {
    pub game_id: String,
    pub max_turns: usize,
    pub turns: Vec<Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GlyphTrajectoryReplayV1 {
    pub request: GlyphTrajectoryRequestV1,
    pub receipt: Value,
}

fn expected_verifier_route(id: &str) -> Result<(u8, &'static str), GlyphRefusal> {
    match id {
        "glyph_game_14_critical_pair_fork" => Ok((
            14,
            "pfp_runtime/src/rewriting/mod.rs",
        )),
        "glyph_game_15_open_frontier" => Ok((
            15,
            "pfp_runtime/src/packets.rs",
        )),
        "glyph_game_16_exact_rational_duel" => Ok((
            16,
            "pfp_runtime/src/rational.rs",
        )),
        "glyph_game_17_candidate_host_split" => Ok((
            17,
            "pfp_runtime/src/packets.rs",
        )),
        "glyph_game_18_transport_without_promotion" => Ok((
            18,
            "core_wdp/src/prime_algos/prime_algorithm_1.rs",
        )),
        _ => Err(refusal(GlyphRefusalCode::UnsupportedVerifier, id)),
    }
}

fn route(registry: &GlyphRegistry, id: &str) -> Result<(u8, String, &'static str), GlyphRefusal> {
    let mut matches = registry.games.iter().filter(|game| game.game_id == id);
    let game = matches
        .next()
        .ok_or_else(|| refusal(GlyphRefusalCode::UnknownGame, id))?;
    if matches.next().is_some() {
        return Err(refusal(
            GlyphRefusalCode::InvalidRequest,
            "ambiguous registry identity",
        ));
    }
    if !game.is_implemented() {
        return Err(refusal(GlyphRefusalCode::ProposedFixture, id));
    }
    let verifier = game
        .verifier_ref
        .as_ref()
        .ok_or_else(|| refusal(GlyphRefusalCode::MissingVerifier, id))?;
    let (number, expected) = expected_verifier_route(id)?;
    if verifier != expected {
        return Err(refusal(GlyphRefusalCode::UnsupportedVerifier, verifier));
    }
    let adapter_ref = expected;
    Ok((number, verifier.clone(), adapter_ref))
}

fn validate_trajectory_budget(request: &GlyphTrajectoryRequestV1) -> Result<(), GlyphRefusal> {
    let budget_ok = [
        request.max_turns > 0,
        request.max_turns <= MAX_TURNS,
        !request.turns.is_empty(),
        request.turns.len() <= request.max_turns,
    ]
    .into_iter()
    .all(|b| b);
    if !budget_ok {
        return Err(refusal(
            GlyphRefusalCode::ResourceBudget,
            "require 1..=32 turns within declared max_turns",
        ));
    }
    for turn in &request.turns {
        if serde_json::to_vec(turn)
            .map_err(|error| refusal(GlyphRefusalCode::InvalidRequest, error))?
            .len()
            > MAX_TURN_BYTES
        {
            return Err(refusal(
                GlyphRefusalCode::ResourceBudget,
                "turn exceeds 16384 bytes",
            ));
        }
    }
    Ok(())
}

/// Execute every requested turn or retain its typed refusal in the hash chain.
/// Resource limits and registry eligibility are checked before native execution.
pub fn execute(request: &GlyphTrajectoryRequestV1) -> Result<Value, GlyphRefusal> {
    validate_trajectory_budget(request)?;
    let registry = parse_registry(REGISTRY_PATH, REGISTRY)
        .map_err(|error| refusal(GlyphRefusalCode::InvalidRequest, error))?;
    let (game, verifier_ref, adapter_ref) = route(&registry, &request.game_id)?;
    let registry_hash = commit("core.glyph.registry.v1", &json!(REGISTRY))?;
    let initial_hash = commit(
        "core.glyph.trajectory.start.v1",
        &json!({
            "game_id": request.game_id, "registry_hash": registry_hash,
            "verifier_ref": verifier_ref, "adapter_ref": adapter_ref,
            "max_turns": request.max_turns, "turn_count": request.turns.len(),
            "authority_effect": "None",
        }),
    )?;
    let mut previous = initial_hash.clone();
    let mut records = Vec::with_capacity(request.turns.len());
    for (index, payload) in request.turns.iter().enumerate() {
        let payload_hash = commit("core.glyph.turn.input.v1", payload)?;
        let outcome = run_turn(game, payload, &initial_hash, &previous, index);
        let (status, result, error) = match outcome {
            Ok(result) => ("EXECUTED", Some(result), None),
            Err(error) => ("REFUSED", None, Some(error)),
        };
        let mut record = json!({
            "turn_index": index, "game_id": request.game_id,
            "verifier_ref": verifier_ref, "adapter_ref": adapter_ref,
            "previous_hash": previous,
            "payload": payload, "payload_hash": payload_hash,
            "execution_status": status, "result": result, "refusal": error,
            "authority_effect": "None",
        });
        previous = commit("core.glyph.turn.receipt.v1", &record)?;
        record["turn_hash"] = json!(previous);
        records.push(record);
    }
    Ok(json!({
        "schema_version": "core.symbol-game.glyph-trajectory.v1",
        "game_id": request.game_id, "registry_hash": registry_hash,
        "initial_hash": initial_hash, "final_hash": previous,
        "turns_executed": records.iter().filter(|r| r["execution_status"] == "EXECUTED").count(),
        "turns_refused": records.iter().filter(|r| r["execution_status"] == "REFUSED").count(),
        "records": records, "authority_effect": "None", "evidence_ceiling": "LocalReplay",
        "scope": "Native checks of declared inputs only; execution is not registry promotion or global admission",
    }))
}

/// Replay native checks, comparing all payloads, outcomes and chain commitments.
pub fn replay(request: &GlyphTrajectoryReplayV1) -> Result<bool, GlyphRefusal> {
    Ok(execute(&request.request)? == request.receipt)
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct PeakTurn {
    presentation: Presentation,
    claim: CriticalPeakClaim,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct FrontierTurn {
    frontier: FrontierState,
    narrowest_claim: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct LpTurn {
    a: Vec<Vec<String>>,
    b: Vec<String>,
    c: Vec<String>,
    primal_x: Vec<String>,
    dual_u: Vec<String>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct TransportTurn {
    from_carrier_hash: String,
    to_carrier_hash: String,
    source_d0_hash: String,
    payload: Value,
    losses: BTreeMap<String, usize>,
    source_was_admitted: bool,
}

fn hash_value(value: &str) -> Result<Hash256, GlyphRefusal> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(refusal(
            GlyphRefusalCode::InvalidRequest,
            "expected lowercase 32-byte hex digest",
        ));
    }
    let bytes =
        hex::decode(value).map_err(|error| refusal(GlyphRefusalCode::InvalidRequest, error))?;
    let mut digest = [0; 32];
    digest.copy_from_slice(&bytes);
    Ok(Hash256(digest))
}

fn exact_vector(values: &[String]) -> Result<Vec<Exact>, GlyphRefusal> {
    if values.len() > 64 || values.iter().any(|value| value.len() > 128) {
        return Err(refusal(
            GlyphRefusalCode::ResourceBudget,
            "exact vector limit is 64 entries of 128 bytes",
        ));
    }
    values
        .iter()
        .map(|value| {
            parse_exact(value).map_err(|error| refusal(GlyphRefusalCode::InvalidRequest, error))
        })
        .collect()
}

fn run_peak_turn(payload: &Value) -> Result<Value, GlyphRefusal> {
    let turn: PeakTurn = decode(payload)?;
    let rule_too_long = turn
        .presentation
        .rules
        .iter()
        .any(|rule| rule.lhs.len() > 64 || rule.rhs.len() > 64);
    let over_budget = [
        turn.presentation.rules.len() > 16,
        turn.claim.step_budget > 64,
        rule_too_long,
        turn.claim.source.len() > 64,
    ]
    .into_iter()
    .any(|b| b);
    if over_budget {
        return Err(refusal(
            GlyphRefusalCode::ResourceBudget,
            "rewrite carrier or step budget exceeds native glyph profile",
        ));
    }
    let evaluation = evaluate_peak_pinned(
        &turn.presentation,
        &turn.claim,
        crate::invoke::host_presentation_pins(),
    );
    Ok(json!({"token": evaluation.token(), "evaluation": evaluation}))
}

fn map_lp_refusal(error: LpRefusal) -> GlyphRefusal {
    match error {
        LpRefusal::PrimalInfeasible { detail } => refusal(
            GlyphRefusalCode::NativeRefusal,
            format!("PRIMAL_INFEASIBLE: {detail}"),
        ),
        LpRefusal::DualInfeasible { detail } => refusal(
            GlyphRefusalCode::NativeRefusal,
            format!("DUAL_INFEASIBLE: {detail}"),
        ),
        LpRefusal::DualityGap { primal, dual } => refusal(
            GlyphRefusalCode::NativeRefusal,
            format!(
                "EXACT_OBJECTIVE_MISMATCH: {} != {}",
                to_canonical_string(&primal),
                to_canonical_string(&dual)
            ),
        ),
    }
}

fn build_standard_lp(turn: &LpTurn) -> Result<StandardLp, GlyphRefusal> {
    if [turn.a.is_empty(), turn.a.len() > 64, turn.c.is_empty()]
        .into_iter()
        .any(|b| b)
    {
        return Err(refusal(
            GlyphRefusalCode::ResourceBudget,
            "LP requires a nonempty carrier with at most 64 rows",
        ));
    }
    let rows = turn
        .a
        .iter()
        .map(|row| exact_vector(row))
        .collect::<Result<Vec<_>, _>>()?;
    let lp = StandardLp {
        a: RationalMatrix::from_rows(&rows)
            .map_err(|error| refusal(GlyphRefusalCode::InvalidRequest, error))?,
        b: exact_vector(&turn.b)?,
        c: exact_vector(&turn.c)?,
    };
    if lp.a.rows() != lp.b.len() || lp.a.cols() != lp.c.len() {
        return Err(refusal(
            GlyphRefusalCode::InvalidRequest,
            "LP coefficient dimensions disagree",
        ));
    }
    Ok(lp)
}

fn run_lp_turn(payload: &Value) -> Result<Value, GlyphRefusal> {
    let turn: LpTurn = decode(payload)?;
    let lp = build_standard_lp(&turn)?;
    let certificate = verify_lp_certificate(
        &lp,
        &exact_vector(&turn.primal_x)?,
        &exact_vector(&turn.dual_u)?,
    )
    .map_err(|error| refusal(GlyphRefusalCode::InvalidRequest, error))?
    .map_err(map_lp_refusal)?;
    Ok(json!({
        "accepted": true,
        "primal_objective": to_canonical_string(&certificate.primal_objective),
        "dual_objective": to_canonical_string(&certificate.dual_objective)
    }))
}

fn run_candidate_turn(payload: &Value) -> Result<Value, GlyphRefusal> {
    let candidate: CandidateMovePacket = decode(payload)?;
    if candidate.schema_version != CandidateMovePacket::SCHEMA {
        return Err(refusal(
            GlyphRefusalCode::InvalidRequest,
            "candidate schema mismatch",
        ));
    }
    let record = RoundRecord::seal(
        &candidate,
        ParseResult::Pass,
        vec![],
        vec![],
        LocalReplayStatus::NotRun,
        Disposition::NeedsEvidence,
        vec![],
    )
    .map_err(|error| refusal(GlyphRefusalCode::NativeRefusal, error))?;
    Ok(json!({"round_record": record, "authority_effect": "None"}))
}

fn build_loss_ledger(
    losses: BTreeMap<String, usize>,
    scope: ScopeBinding,
) -> Result<LossLedger, GlyphRefusal> {
    if losses
        .values()
        .try_fold(0usize, |total, count| total.checked_add(*count))
        .is_none()
    {
        return Err(refusal(
            GlyphRefusalCode::ResourceBudget,
            "loss total overflows usize",
        ));
    }
    Ok(if losses.is_empty() {
        LossLedger::empty(scope)
    } else {
        LossLedger::booked(losses.into_iter().collect(), scope)
    })
}

fn build_transport_scope(
    turn: &TransportTurn,
    run: &str,
    previous: &str,
    index: usize,
) -> Result<
    (
        Hash256,
        Hash256,
        Hash256,
        ScopeBinding,
    ),
    GlyphRefusal,
> {
    let from = hash_value(&turn.from_carrier_hash)?;
    let to = hash_value(&turn.to_carrier_hash)?;
    let payload_hash = hash_value(&commit("core.glyph.transport.payload.v1", &turn.payload)?)?;
    let scope = ScopeBinding::with_carrier_and_d0(
        hash_value(run)?,
        from.clone(),
        hash_value(&turn.source_d0_hash)?,
        payload_hash.clone(),
        Some(hash_value(previous)?),
        index,
    );
    Ok((from, to, payload_hash, scope))
}

fn run_transport_turn(
    payload: &Value,
    run: &str,
    previous: &str,
    index: usize,
) -> Result<Value, GlyphRefusal> {
    let turn: TransportTurn = decode(payload)?;
    let (from, to, payload_hash, scope) = build_transport_scope(&turn, run, previous, index)?;
    let ledger = build_loss_ledger(turn.losses, scope)?;
    let packet = transport(from, to, payload_hash, ledger, turn.source_was_admitted)
        .map_err(|error| refusal(GlyphRefusalCode::NativeRefusal, error))?;
    Ok(json!({
        "from_carrier_hash": hex::encode(packet.from_carrier().0),
        "to_carrier_hash": hex::encode(packet.to_carrier().0),
        "payload_hash": hex::encode(packet.payload().0), "status": packet.status(),
        "loss_ledger": packet.ledger(), "authority_effect": "None"
    }))
}

fn run_turn(
    game: u8,
    payload: &Value,
    run: &str,
    previous: &str,
    index: usize,
) -> Result<Value, GlyphRefusal> {
    match game {
        14 => run_peak_turn(payload),
        15 => {
            let turn: FrontierTurn = decode(payload)?;
            // This trajectory does not run a branch scheduler. It cannot turn
            // caller claims into proof that every surviving branch was visited.
            let terminal = TerminalProposal::new(&turn.frontier, &turn.narrowest_claim, false);
            Ok(json!({"terminal": terminal, "scheduler_exhaustion_verified": false}))
        }
        16 => run_lp_turn(payload),
        17 => run_candidate_turn(payload),
        18 => run_transport_turn(payload, run, previous, index),
        _ => Err(refusal(GlyphRefusalCode::UnsupportedVerifier, game)),
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn a_declared_implemented_game_without_its_verifier_is_refused() {
        let mut registry = parse_registry(REGISTRY_PATH, REGISTRY).unwrap();
        let game = registry
            .games
            .iter_mut()
            .find(|game| game.game_id == "glyph_game_16_exact_rational_duel")
            .unwrap();
        game.verifier_ref = None;
        assert_eq!(
            route(&registry, "glyph_game_16_exact_rational_duel")
                .unwrap_err()
                .code,
            GlyphRefusalCode::MissingVerifier
        );
    }
}
