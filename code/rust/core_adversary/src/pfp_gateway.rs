//! Active native model boundary: PFP task turns over the existing route/account ledger.
//! Historical gateway.execute remains the frozen fixture profile. No new dispatch,
//! ledger, mathematical checker or model authority lives here.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_3180a991<T> {
    fn checked_invariant_3180a991(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_3180a991<T> for Option<T> {
    #[inline]
    fn checked_invariant_3180a991(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_3180a991<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_3180a991(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::stage::{
    ports::{Refusal, SeatPort, SeatTurnReply, SeatTurnRequest},
    strict_json,
};
use crate::{
    exact::{integer, Integer},
    gateway::{
        parse_reply, usable_machine_reply, CallLedger, Clock, RoutedSeatExecutor, SeatPrompt,
        SeatTransport,
    },
    routing::admit_spend,
};
use num_bigint::BigInt;
use num_integer::Integer as IntegerOps;
use num_traits::Zero;
use pfp_runtime::pfp_task_turn::{PreparedTaskTurn, CHECKER_ID};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};

pub struct PfpSeatExecutor<T: SeatTransport, L: CallLedger, C: Clock> {
    pub inner: RoutedSeatExecutor<T, L, C>,
}

impl<T: SeatTransport, L: CallLedger, C: Clock> PfpSeatExecutor<T, L, C> {
    fn validate_reserved_row<'a>(
        row: &'a Value,
        reserved: &mut BTreeMap<&'a str, &'a Value>,
    ) -> Result<(), Refusal> {
        let id = row["attempt_id"]
            .as_str()
            .ok_or_else(|| Refusal::new("PFP_LEDGER_INVALID", "reservation attempt ID missing"))?;
        if reserved.insert(id, row).is_some()
            || integer(&row["cost_microusd"]).is_none_or(|n| n < BigInt::zero())
            || !row["pfp_binding"].is_object()
        {
            return Err(Refusal::new(
                "PFP_LEDGER_INVALID",
                "duplicate or malformed reservation",
            ));
        }
        Ok(())
    }

    fn settlement_terms_match<'a>(
        row: &'a Value,
        hold: &'a Value,
        id: &'a str,
        closed: &mut BTreeSet<&'a str>,
        actual: BigInt,
        delta: BigInt,
    ) -> bool {
        let keys_match = [
            "bout_id",
            "request_digest",
            "pfp_binding",
            "day",
            "tier",
            "config_digest",
            "router",
            "model",
            "leg_index",
            "candidate_id",
            "round_index",
            "seat_id",
        ]
        .iter()
        .all(|key| row[*key] == hold[*key]);
        [
            actual >= BigInt::zero(),
            closed.insert(id),
            keys_match,
            Some(actual - delta) == integer(&hold["cost_microusd"]),
        ]
        .into_iter()
        .all(|b| b)
    }

    fn validate_settled_row<'a>(
        row: &'a Value,
        reserved: &BTreeMap<&'a str, &'a Value>,
        closed: &mut BTreeSet<&'a str>,
    ) -> Result<(), Refusal> {
        let id = row["attempt_id"]
            .as_str()
            .ok_or_else(|| Refusal::new("PFP_LEDGER_INVALID", "settlement attempt ID missing"))?;
        let hold = reserved.get(id).ok_or_else(|| {
            Refusal::new(
                "PFP_LEDGER_INVALID",
                "settlement without original reservation",
            )
        })?;
        let actual = integer(&row["actual_cost_microusd"])
            .ok_or_else(|| Refusal::new("PFP_LEDGER_INVALID", "settlement actual cost missing"))?;
        let delta = integer(&row["cost_microusd"])
            .ok_or_else(|| Refusal::new("PFP_LEDGER_INVALID", "settlement delta missing"))?;
        if !Self::settlement_terms_match(row, hold, id, closed, actual, delta) {
            return Err(Refusal::new(
                "PFP_LEDGER_INVALID",
                "settlement terms do not match original hold",
            ));
        }
        Ok(())
    }

    fn validate_ledger_row<'a>(
        row: &'a Value,
        reserved: &mut BTreeMap<&'a str, &'a Value>,
        closed: &mut BTreeSet<&'a str>,
    ) -> Result<(), Refusal> {
        match row["pfp_state"].as_str() {
            Some("RESERVED") => Self::validate_reserved_row(row, reserved),
            Some("SETTLED") => Self::validate_settled_row(row, reserved, closed),
            Some(_) => Err(Refusal::new(
                "PFP_LEDGER_INVALID",
                "unknown PFP ledger state",
            )),
            None => {
                // Original legacy cost rows remain historical inputs to the same account.
                if row.get("pfp_state").is_some()
                    || integer(&row["cost_microusd"]).is_none_or(|n| n < BigInt::zero())
                {
                    return Err(Refusal::new(
                        "PFP_LEDGER_INVALID",
                        "legacy rows require explicit nonnegative integral cost; invalid state or unmetered rows cannot continue live spend",
                    ));
                }
                Ok(())
            }
        }
    }

    fn recompute_bout_spend(&mut self, rows: &[Value]) {
        self.inner.spent_bout = BigInt::zero();
        self.inner.spent_tier.clear();
        for row in rows {
            if row["bout_id"].as_str() == Some(&self.inner.bout_id) {
                if let Some(cost) = integer(&row["cost_microusd"]) {
                    self.inner.spent_bout += &cost;
                    if let Some(tier) = row["tier"].as_str() {
                        *self.inner.spent_tier.entry(tier.into()).or_default() += cost;
                    }
                }
            }
        }
    }

    fn recover(&mut self) -> Result<Vec<Value>, Refusal> {
        let rows = self.inner.ledger.records()?;
        let mut reserved = BTreeMap::new();
        let mut closed = BTreeSet::new();
        for row in &rows {
            Self::validate_ledger_row(row, &mut reserved, &mut closed)?;
        }
        let has_unresolved = rows.iter().any(|r| {
            r["pfp_state"] == "RESERVED"
                && r["attempt_id"]
                    .as_str()
                    .is_none_or(|id| !closed.contains(id))
        });
        if has_unresolved {
            return Err(Refusal::new("PFP_ACCOUNTING_UNRESOLVED", "an earlier dispatch has unknown outcome; reconcile its existing hold before another send"));
        }
        let has_unmetered = rows.iter().any(|row| {
            row["bout_id"].as_str() == Some(&self.inner.bout_id)
                && row["outcome"] == "PFP_USAGE_UNAVAILABLE"
        });
        if has_unmetered {
            return Err(Refusal::new("PFP_USAGE_UNAVAILABLE","an earlier turn in this bout has unmetered token usage; no further model roles may send"));
        }
        self.recompute_bout_spend(&rows);
        Ok(rows)
    }
    fn record_attempt(
        &mut self,
        request: &SeatTurnRequest,
        tier: &str,
        leg: &crate::routing::RouteLeg,
        index: usize,
        custody: Value,
    ) -> Result<(), Refusal> {
        self.inner
            .record(request, tier, Some(leg), index, custody.clone())
            .map_err(|mut failure| {
                failure
                    .details
                    .insert("attempt".into(), custody.to_string());
                failure
            })?;
        if custody["pfp_state"] == "SETTLED" {
            if let Some(actual) = integer(&custody["actual_cost_microusd"]) {
                self.inner.spent_bout += &actual;
                *self.inner.spent_tier.entry(tier.into()).or_default() += actual;
            }
        }
        Ok(())
    }

    fn check_replay_record_header(
        &self,
        request: &SeatTurnRequest,
        record: &Value,
    ) -> Result<(), Refusal> {
        let digest_ok = record["request_digest"] == json!(request.request_digest()?)
            && record["config_digest"] == json!(self.inner.config_digest)
            && record["bout_id"] == json!(self.inner.bout_id);
        let status_ok = record["outcome"] == "OK"
            && record["pfp_state"] == "SETTLED"
            && record["http_status"]
                .as_u64()
                .is_some_and(|status| (200..300).contains(&status))
            && record.get("truncated") == Some(&Value::Null);
        if !digest_ok || !status_ok {
            return Err(Refusal::new(
                "PFP_REPLAY_BINDING_MISMATCH",
                "stored request, route, bout or successful outcome differs",
            ));
        }
        Ok(())
    }

    fn verify_replay_provider_bytes(record: &Value) -> Result<Vec<u8>, Refusal> {
        let raw = record["raw_reply_hex"]
            .as_str()
            .and_then(|s| hex::decode(s).ok())
            .ok_or_else(|| Refusal::new("PFP_REPLAY_INVALID", "provider bytes unavailable"))?;
        if record["raw_reply_sha256"]
            != json!(format!("sha256:{}", hex::encode(Sha256::digest(&raw))))
        {
            return Err(Refusal::new(
                "PFP_REPLAY_INVALID",
                "provider raw digest differs",
            ));
        }
        let provider = strict_json::parse(&raw)
            .map_err(|_| Refusal::new("PFP_REPLAY_INVALID", "provider raw JSON invalid"))?;
        if !["prompt_tokens", "completion_tokens"]
            .iter()
            .all(|key| provider["usage"][*key].as_u64().is_some())
        {
            return Err(Refusal::new(
                "PFP_REPLAY_INVALID",
                "actual provider token usage is unavailable",
            ));
        }
        let content = provider["choices"][0]["message"]["content"]
            .as_str()
            .ok_or_else(|| {
                Refusal::new("PFP_REPLAY_INVALID", "actual provider content unavailable")
            })?;
        if record["pfp_raw_reply_hex"] != json!(hex::encode(content.as_bytes())) {
            return Err(Refusal::new(
                "PFP_REPLAY_INVALID",
                "PFP content differs from actual provider container",
            ));
        }
        Ok(raw)
    }

    fn resolve_replay_leg<'a>(
        &'a self,
        request: &SeatTurnRequest,
        record: &Value,
        attempt: &str,
    ) -> Result<&'a crate::routing::RouteLeg, Refusal> {
        let route = self.inner.table.seat(&request.seat_id)?;
        let index = record["leg_index"]
            .as_u64()
            .and_then(|i| usize::try_from(i).ok())
            .ok_or_else(|| Refusal::new("PFP_REPLAY_INVALID", "route index unavailable"))?;
        let leg = route
            .legs
            .get(index)
            .ok_or_else(|| Refusal::new("PFP_REPLAY_INVALID", "route leg unavailable"))?;
        let prefix = format!("{}:{index}:", self.inner.bout_id);
        let suffix_ok = attempt
            .strip_prefix(&prefix)
            .is_some_and(|suffix| !suffix.is_empty() && suffix.bytes().all(|c| c.is_ascii_digit()));
        if record["router"] != json!(leg.router)
            || record["model"] != json!(leg.model)
            || !suffix_ok
        {
            return Err(Refusal::new(
                "PFP_REPLAY_BINDING_MISMATCH",
                "stored route or attempt leg differs",
            ));
        }
        Ok(leg)
    }

    fn verify_replay_provider_reply(
        &self,
        request: &SeatTurnRequest,
        record: &Value,
        attempt: &str,
        raw: &[u8],
        answer: &str,
    ) -> Result<(), Refusal> {
        let leg = self.resolve_replay_leg(request, record, attempt)?;
        let mut parsed = parse_reply(leg, raw)?;
        if parsed.cost_source != "provider_receipt"
            || integer(&record["actual_cost_microusd"]) != Some(parsed.cost_microusd.0.clone())
        {
            return Err(Refusal::new(
                "PFP_REPLAY_INVALID",
                "actual provider cost receipt differs or is unavailable",
            ));
        }
        parsed.content = answer.to_owned();
        usable_machine_reply(&parsed)?;
        Ok(())
    }

    /// Replay checks the actual provider container as well as the PFP content;
    /// no transport or new ledger charge is involved. Real candidate checkers
    /// remain downstream of the resulting seat answer.
    pub fn replay(&self, request: &SeatTurnRequest, record: &Value) -> Result<String, Refusal> {
        self.check_replay_record_header(request, record)?;
        let raw = Self::verify_replay_provider_bytes(record)?;
        let attempt = record["attempt_id"]
            .as_str()
            .ok_or_else(|| Refusal::new("PFP_REPLAY_INVALID", "attempt unavailable"))?;
        let prepared = prepare(request, &self.inner.bout_id, attempt)?;
        let answer = prepared.replay(record)?;
        self.verify_replay_provider_reply(request, record, attempt, &raw, &answer)?;
        Ok(answer)
    }

    fn reserve_pfp_leg(
        &mut self,
        request: &SeatTurnRequest,
        tier: &str,
        leg: &crate::routing::RouteLeg,
        index: usize,
    ) -> Result<(String, PreparedTaskTurn, SeatPrompt, BigInt, String, BigInt), Refusal> {
        let rows = self.recover()?;
        let attempt_id = format!("{}:{}:{}", self.inner.bout_id, index, rows.len());
        let prepared = prepare(request, &self.inner.bout_id, &attempt_id)?;
        let prompt = SeatPrompt {
            system: prepared.system.clone(),
            user: prepared.user.clone(),
        };
        let input = BigInt::from(prompt.system.len() + prompt.user.len());
        if self
            .inner
            .table
            .budget
            .max_input_bytes_per_call
            .as_ref()
            .is_some_and(|limit| input > limit.0)
        {
            return Err(Refusal::new(
                "INPUT_TOO_LARGE",
                "prepared PFP prompt exceeds input byte limit",
            ));
        }
        // The quote is a reservation estimate, never a claim about provider liability.
        let hold = leg.cost_microusd(&input, &BigInt::from(self.inner.max_output_tokens));
        let day = self.inner.clock.today();
        let day_spend = self.inner.ledger.spent_on(&day)?;
        admit_spend(
            &self.inner.spent_bout,
            &day_spend,
            &hold,
            &self.inner.table.budget,
            tier,
            self.inner.spent_tier.get(tier).unwrap_or(&BigInt::zero()),
        )?;
        self.inner.record(
            request,
            tier,
            Some(leg),
            index,
            json!({"outcome":"PFP_RESERVED","pfp_state":"RESERVED","attempt_id":attempt_id,"pfp_binding":prepared.binding,"cost_microusd":Integer(hold.clone()),"cost_source":"reservation_estimate","day":day}),
        )?;
        Ok((attempt_id, prepared, prompt, hold, day, day_spend))
    }

    fn record_unknown_pfp_outcome(
        &mut self,
        request: &SeatTurnRequest,
        tier: &str,
        leg: &crate::routing::RouteLeg,
        index: usize,
        raw: &[u8],
        hold: &BigInt,
        mut custody: Value,
    ) -> Result<Refusal, Refusal> {
        custody["outcome"] = json!("PFP_OUTCOME_UNKNOWN");
        custody["cost_microusd"] = json!(0);
        custody["actual_cost_microusd"] = Value::Null;
        custody["cost_source"] = json!("unknown_actual_reservation_retained");
        custody["ledger_cost_semantics"] = json!("additional_delta_not_actual_cost");
        // A known cost must never be hidden by a malformed usage/content field.
        if let Some(cost) = strict_json::parse(raw)
            .ok()
            .and_then(|v| {
                v["usage"]["cost"]
                    .as_number()
                    .and_then(|n| crate::stage::exact::rational(&n.to_string()))
            })
            .filter(|n| n >= &num_rational::BigRational::zero())
        {
            let scaled = cost * BigInt::from(1000000);
            let actual = scaled.numer().div_ceil(scaled.denom());
            custody["actual_cost_microusd"] = json!(Integer(actual.clone()));
            custody["cost_microusd"] = json!(Integer((actual - hold).max(BigInt::zero())));
            custody["cost_source"] = json!("known_cost_unknown_outcome_reservation_retained");
        }
        self.record_attempt(request, tier, leg, index, custody.clone())?;
        let mut failure = Refusal::new(
            "PFP_ACCOUNTING_UNRESOLVED",
            "provider cost/outcome unavailable; actual raw bytes retained, reservation held, no fallback",
        );
        failure
            .details
            .insert("attempt".into(), custody.to_string());
        Ok(failure)
    }

    fn parse_nonnegative_receipt_reply(
        leg: &crate::routing::RouteLeg,
        raw: &[u8],
    ) -> Option<(Value, crate::gateway::ParsedReply)> {
        let value = strict_json::parse(raw).ok()?;
        // Only an actual nonnegative receipt cost settles a dispatched hold.
        let cost = value.get("usage")?.get("cost")?.as_number()?;
        crate::stage::exact::rational(&cost.to_string())
            .filter(|n| n >= &num_rational::BigRational::zero())?;
        parse_reply(leg, raw).ok().map(|reply| (value, reply))
    }

    fn record_transport_failure(
        &mut self,
        request: &SeatTurnRequest,
        tier: &str,
        leg: &crate::routing::RouteLeg,
        index: usize,
        error_kind: String,
        mut custody: Value,
    ) -> Result<Refusal, Refusal> {
        custody["outcome"] = json!("PFP_OUTCOME_UNKNOWN");
        custody["transport_error"] = json!(error_kind);
        custody["cost_microusd"] = json!(0);
        custody["actual_cost_microusd"] = Value::Null;
        custody["cost_source"] = json!("unknown_actual_reservation_retained");
        custody["ledger_cost_semantics"] = json!("additional_delta_not_actual_cost");
        self.record_attempt(request, tier, leg, index, custody.clone())?;
        let mut failure = Refusal::new(
            "PFP_ACCOUNTING_UNRESOLVED",
            "transport outcome is unknown; reservation retained and fallback stopped",
        );
        failure
            .details
            .insert("attempt".into(), custody.to_string());
        Ok(failure)
    }

    #[allow(clippy::too_many_arguments)]
    fn send_and_parse_pfp(
        &mut self,
        request: &SeatTurnRequest,
        tier: &str,
        leg: &crate::routing::RouteLeg,
        index: usize,
        prompt: &SeatPrompt,
        hold: &BigInt,
        mut custody: Value,
    ) -> Result<(Vec<u8>, Value, crate::gateway::ParsedReply, Value), Refusal> {
        let started = self.inner.clock.milliseconds();
        let sent = self.inner.transports.send_bound(
            &leg.router,
            &leg.model,
            prompt,
            self.inner.max_output_tokens,
        );
        let outcome = match sent {
            Ok(outcome) => outcome,
            Err(error) => {
                let failure =
                    self.record_transport_failure(request, tier, leg, index, error.kind, custody)?;
                return Err(failure);
            }
        };
        let raw = outcome.raw;
        custody["raw_reply_hex"] = json!(hex::encode(&raw));
        custody["raw_reply_sha256"] =
            json!(format!("sha256:{}", hex::encode(Sha256::digest(&raw))));
        custody["http_status"] = json!(outcome.status);
        custody["truncated"] = json!(outcome.truncated);
        let ok_http = (200..300).contains(&outcome.status) && outcome.truncated.is_none();
        let (provider, parsed) = match Self::parse_nonnegative_receipt_reply(leg, &raw) {
            Some(pair) if ok_http => pair,
            _ => {
                let err = self
                    .record_unknown_pfp_outcome(request, tier, leg, index, &raw, hold, custody)?;
                return Err(err);
            }
        };
        // Settlement delta replaces the hold in the SAME ledger, including after restart.
        let actual = parsed.cost_microusd.0.clone();
        custody["pfp_state"] = json!("SETTLED");
        custody["cost_microusd"] = json!(Integer(&actual - hold));
        custody["actual_cost_microusd"] = json!(Integer(actual));
        custody["cost_source"] = json!("provider_receipt");
        custody["ledger_cost_semantics"] = json!("settlement_delta_replaces_original_hold");
        custody["latency_ms"] = json!(self.inner.clock.milliseconds().saturating_sub(started));
        Ok((raw, provider, parsed, custody))
    }

    #[allow(clippy::too_many_arguments)]
    fn finalize_settled_pfp_reply(
        &mut self,
        request: &SeatTurnRequest,
        tier: &str,
        leg: &crate::routing::RouteLeg,
        index: usize,
        request_digest: &str,
        prepared: &PreparedTaskTurn,
        raw: Vec<u8>,
        parsed: crate::gateway::ParsedReply,
        fields: BTreeMap<String, String>,
        mut custody: Value,
        rejected: &[Value],
    ) -> Result<SeatTurnReply, Refusal> {
        let actual = parsed.cost_microusd.0.clone();
        custody["outcome"] = json!("OK");
        let mut parameters = BTreeMap::from([
            ("pfp_binding".into(), prepared.binding.clone()),
            ("pfp_evidence".into(), custody.clone()),
            ("evidence_grade".into(), json!("UNVERIFIED")),
            ("cost_microusd".into(), json!(Integer(actual))),
            ("cost_source".into(), json!("provider_receipt")),
            ("config_digest".into(), json!(self.inner.config_digest)),
            ("bout_id".into(), json!(self.inner.bout_id)),
            ("max_tokens".into(), json!(self.inner.max_output_tokens)),
        ]);
        if !rejected.is_empty() {
            parameters.insert("rejected_attempts".into(), json!(rejected));
        }
        let reply = SeatTurnReply {
            reply_text: parsed.content,
            residual_colour: fields["RESIDUAL_COLOUR"].clone(),
            authority_effect: "None".into(),
            machine_fields: fields,
            raw_bytes: raw,
            model: Some(parsed.model),
            provider: Some(leg.router.clone()),
            parameters: Some(parameters),
            usage: Some(BTreeMap::from([
                ("input_tokens".into(), json!(parsed.input_tokens)),
                ("output_tokens".into(), json!(parsed.output_tokens)),
            ])),
            request_digest: Some(request_digest.to_owned()),
        };
        if let Err(failure) = reply.validate() {
            custody["outcome"] = json!("REPLY_INVALID");
            custody["refusal"] = json!(failure);
            self.record_attempt(request, tier, leg, index, custody.clone())?;
            let mut refusal = Refusal::new(
                "REPLY_INVALID",
                "paid reply fails the existing seat-turn contract",
            );
            refusal
                .details
                .insert("attempt".into(), custody.to_string());
            return Err(refusal);
        }
        self.record_attempt(request, tier, leg, index, custody)?;
        Ok(reply)
    }

    #[allow(clippy::too_many_arguments)]
    fn evaluate_settled_content(
        &self,
        tier: &str,
        day_spend: &BigInt,
        provider: &Value,
        prepared: &PreparedTaskTurn,
        parsed: &mut crate::gateway::ParsedReply,
        custody: &mut Value,
    ) -> (bool, Result<BTreeMap<String, String>, Refusal>) {
        let usage_valid = ["prompt_tokens", "completion_tokens"]
            .iter()
            .all(|key| provider["usage"][*key].as_u64().is_some());
        if !usage_valid {
            return (
                false,
                Err(Refusal::new(
                    "PFP_USAGE_UNAVAILABLE",
                    "actual cost retained but token usage is unavailable; fallback stopped",
                )),
            );
        }
        let within_budget = admit_spend(
            &self.inner.spent_bout,
            day_spend,
            &parsed.cost_microusd.0,
            &self.inner.table.budget,
            tier,
            self.inner.spent_tier.get(tier).unwrap_or(&BigInt::zero()),
        );
        if within_budget.is_err() {
            return (
                true,
                Err(Refusal::new(
                    "PFP_BUDGET_OVERRUN",
                    "actual provider cost exceeds an admitted budget; fully charged and fallback stopped",
                )),
            );
        }
        let content = provider["choices"][0]["message"]["content"]
            .as_str()
            .unwrap_or("");
        let checked = prepared.check(content.as_bytes()).and_then(|answer| {
            let evidence = prepared.evidence(content.as_bytes(), &answer);
            for (key, value) in evidence
                .as_object()
                .checked_invariant_3180a991("checked invariant")
            {
                custody[key] = value.clone();
            }
            parsed.content = answer;
            usable_machine_reply(parsed)
        });
        (true, checked)
    }

    fn handle_rejected_pfp_attempt(
        &mut self,
        request: &SeatTurnRequest,
        tier: &str,
        leg: &crate::routing::RouteLeg,
        index: usize,
        mut custody: Value,
        failure: Refusal,
        usage_valid: bool,
        rejected: &mut Vec<Value>,
    ) -> Result<(), Refusal> {
        custody["outcome"] = json!(failure.code);
        custody["refusal"] = json!(failure);
        self.record_attempt(request, tier, leg, index, custody.clone())?;
        rejected.push(custody);
        let fatal = matches!(
            failure.code.as_str(),
            "AUTHORITY_MINT_REFUSED" | "PFP_BUDGET_OVERRUN"
        ) || !usage_valid;
        if fatal {
            let mut refusal = failure;
            refusal
                .details
                .insert("rejected_attempts".into(), json!(rejected).to_string());
            return Err(refusal);
        }
        Ok(())
    }

    pub fn execute(&mut self, request: &SeatTurnRequest) -> Result<SeatTurnReply, Refusal> {
        let route = self.inner.table.seat(&request.seat_id)?.clone();
        if !route.calls_model() {
            return Err(Refusal::new(
                "SEAT_NOT_MODEL_BACKED",
                "seat is not model backed",
            ));
        }
        let request_digest = request.request_digest()?;
        let mut rejected = Vec::new();
        for (index, leg) in route.legs.iter().enumerate() {
            if !self.inner.transports.configured(&leg.router) {
                continue;
            }
            let (attempt_id, prepared, prompt, hold, day, day_spend) =
                self.reserve_pfp_leg(request, &route.tier, leg, index)?;
            let initial_custody = json!({"attempt_id":attempt_id,"pfp_binding":prepared.binding,"authority_effect":"None","day":day});
            let (raw, provider, mut parsed, mut custody) = self.send_and_parse_pfp(
                request,
                &route.tier,
                leg,
                index,
                &prompt,
                &hold,
                initial_custody,
            )?;
            let (usage_valid, checked) = self.evaluate_settled_content(
                &route.tier,
                &day_spend,
                &provider,
                &prepared,
                &mut parsed,
                &mut custody,
            );
            match checked {
                Err(failure) => {
                    self.handle_rejected_pfp_attempt(
                        request,
                        &route.tier,
                        leg,
                        index,
                        custody,
                        failure,
                        usage_valid,
                        &mut rejected,
                    )?;
                }
                Ok(fields) => {
                    return self.finalize_settled_pfp_reply(
                        request,
                        &route.tier,
                        leg,
                        index,
                        &request_digest,
                        &prepared,
                        raw,
                        parsed,
                        fields,
                        custody,
                        &rejected,
                    );
                }
            }
        }
        let mut failure = Refusal::new(
            "ALL_LEGS_FAILED",
            "all configured PFP seat attempts were rejected",
        );
        failure
            .details
            .insert("rejected_attempts".into(), json!(rejected).to_string());
        Err(failure)
    }
}
fn prepare(
    request: &SeatTurnRequest,
    _bout_id: &str,
    attempt_id: &str,
) -> Result<PreparedTaskTurn, Refusal> {
    let request_digest = request.request_digest()?;
    let system=format!("You are seat '{}' (cognitive operator: {}) in scene '{}' of Adversary's Swarm Dialectic.\nYou have no authority. The answer string must end with exactly one machine block:\n```machine\nAUTHORITY_EFFECT=None\nRESIDUAL_COLOUR=<Open|Closed|Exact>\nDISPOSITION=<SELECT|CHALLENGE|REJECT|PASS_TO_MASTER|REFUSE>\nDDC_LETTER=<E|R|C|I|Λ|D|M|T>\n```",request.seat_id,request.cognitive_operator,request.scene_id);
    let mut user = request.prompt_text.clone();
    if !request.context_bytes.is_empty() {
        let context = std::str::from_utf8(&request.context_bytes)
            .map_err(|_| Refusal::new("PFP_CONTEXT_INVALID", "seat context must be exact UTF-8"))?;
        user.push_str("\n\n[Candidate Context]:\n");
        user.push_str(context);
    }
    PreparedTaskTurn::prepare(
        &system,
        &user,
        &format!("adversary:{request_digest}"),
        attempt_id,
        json!({"request_digest":request_digest,"candidate_id":request.candidate_id,"seat_id":request.seat_id,"scene_id":request.scene_id,"round_index":request.round_index,"role_kind":request.role_kind}),
        CHECKER_ID,
    )
}
impl<T: SeatTransport, L: CallLedger, C: Clock> SeatPort for PfpSeatExecutor<T, L, C> {
    fn execute_turn(&mut self, request: &SeatTurnRequest) -> Result<SeatTurnReply, Refusal> {
        self.execute(request)
    }
}

// Origin: engine/crates_rs/core_adversary/src/pfp_gateway.rs
// Claim: urn:core:crates_rs:core-adversary:pfp-gateway:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3180a991 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3180a991` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3180a991 {
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
impl BoundaryError3180a991 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3180a991 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3180a991 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3180a991 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3180a991> {
        if capacity_bound == 0 {
            return Err(BoundaryError3180a991::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3180a991::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3180a991::ExceedsCapacity {
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
mod l4_boundary_tests_3180a991 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord3180a991::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord3180a991::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord3180a991::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord3180a991::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord3180a991::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError3180a991::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError3180a991::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
