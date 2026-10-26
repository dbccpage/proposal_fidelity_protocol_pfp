"""Bounded current braid tournament derived from the preserved Paper 022 source.

The unchanged Atlas referee checks finite SO/noise conditions, not target-gate
equivalence. Offline labels are configurations, never observed model runs.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import asdict, dataclass, replace
from fractions import Fraction
from importlib.resources import files
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
from uuid import uuid4

from omega_engine_pfp.infrastructure.pilot_matrix import (
    _scope,
    complete_pilot_turn,
    make_pilot_gateways,
    validate_pilot_gateways,
)
from omega_engine_woland.domain.providers.types import CandidateRequest, DecodingParamsV1

# The retained Atlas sources use sibling imports. Resolve their packaged owner,
# independently of cwd/Git; neither source is changed by this consumer.
MS_MAJORANA_CODE = Path(str(files("omega_engine_atlas").joinpath(
    "coda_atlas/F004_papers/009_ms_majorana/code")))
if not all((MS_MAJORANA_CODE / name).is_file() for name in (
        "majorana_braid_exact.py", "majorana_multiqubit_noise.py")):
    raise ValueError("MAJORANA_REFEREE_RESOURCE_UNAVAILABLE")
if str(MS_MAJORANA_CODE) not in sys.path:
    sys.path.insert(0, str(MS_MAJORANA_CODE))
from majorana_multiqubit_noise import (  # noqa: E402, I001
    LocalMajoranaNoise as LocalMajoranaNoise,
    MultiQubitBraidCircuit as MultiQubitBraidCircuit,
    MultiQubitNoisyBraidProposalPacket as MultiQubitNoisyBraidProposalPacket,
    MultiQubitNoisyBraidReceipt as MultiQubitNoisyBraidReceipt,
    MultiQubitNoisyBraidReferee as MultiQubitNoisyBraidReferee,
)

MODEL_8B = "meta-llama/llama-3.1-8b-instruct"
MODEL_70B = "meta-llama/llama-3.3-70b-instruct"
MODEL_GLM53 = "thudm/glm-5.3"
CANONICAL_TOURNAMENT_MODELS: Tuple[str, ...] = (MODEL_8B, MODEL_70B, MODEL_GLM53)
DEFAULT_NOISE_BUDGETS = (Fraction(1, 100), Fraction(1, 50), Fraction(1, 20), Fraction(1, 10))

@dataclass(frozen=True)
class ProposerStrategyConfig:
    """Configuration for a tournament proposer agent."""

    proposer_id: str
    model_name: str
    strategy_type: str  # "echo_mitigated", "direct_unmitigated", "targeted_compensation", "random_baseline"
    use_live_openrouter: bool = False


@dataclass(frozen=True)
class TournamentRoundResult:
    """Single round result in the tournament."""

    round_id: str
    num_qubits: int
    target_operation: str
    noise_budget: Fraction
    tolerance_epsilon: Fraction
    proposer_id: str
    model_name: str
    is_accepted: bool
    status_reason: str
    gate_count: int
    circuit_noise_defect: Fraction
    receipt_digest: str


@dataclass(frozen=True)
class ProposerLeaderboardEntry:
    """Aggregated tournament statistics for a single proposer."""

    proposer_id: str
    model_name: str
    strategy_type: str
    total_rounds: int
    accepted_rounds: int
    acceptance_rate: Fraction
    mean_noise_defect: Fraction
    min_defect: Fraction
    max_defect: Fraction
    rank: int


@dataclass(frozen=True)
class TournamentRunReceipt:
    """Unsigned content record for a finite Symbol Game braid tournament."""

    tournament_id: str
    num_qubits: int
    num_rounds: int
    noise_budgets: Tuple[Fraction, ...]
    models_evaluated: Tuple[str, ...]
    leaderboard: Tuple[ProposerLeaderboardEntry, ...]
    round_results: Tuple[TournamentRoundResult, ...]
    sha256_hash: str
    authority_effect: str = "None"

    def canonical_digest(self) -> str:
        """Deterministic SHA-256 hash of tournament receipt contents."""
        payload = {
            "tournament_id": self.tournament_id,
            "num_qubits": self.num_qubits,
            "num_rounds": self.num_rounds,
            "noise_budgets": [str(b) for b in self.noise_budgets],
            "models_evaluated": list(self.models_evaluated),
            "leaderboard": [
                {
                    "proposer_id": e.proposer_id,
                    "model_name": e.model_name,
                    "strategy_type": e.strategy_type,
                    "total_rounds": e.total_rounds,
                    "accepted_rounds": e.accepted_rounds,
                    "acceptance_rate": str(e.acceptance_rate),
                    "mean_noise_defect": str(e.mean_noise_defect),
                    "min_defect": str(e.min_defect),
                    "max_defect": str(e.max_defect),
                    "rank": e.rank,
                }
                for e in self.leaderboard
            ],
            "round_results": [
                {
                    "round_id": r.round_id,
                    "proposer_id": r.proposer_id,
                    "is_accepted": r.is_accepted,
                    "circuit_noise_defect": str(r.circuit_noise_defect),
                    "receipt_digest": r.receipt_digest,
                }
                for r in self.round_results
            ],
            "authority_effect": self.authority_effect,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def claim_hygiene_summary(self) -> str:
        return (f"Finite original-referee results for {self.tournament_id}; "
            f"observed models: {', '.join(self.models_evaluated) or 'none (deterministic)'}. "
            "Acceptance checks SO/noise conditions only, not target-operation equivalence. "
            "No physical-device, general reasoning, signature or superiority claim. AuthorityEffect: None.")


class BraidTournamentProposerAgent:
    """An original deterministic strategy or an explicitly accounted live proposer."""

    def __init__(self, config: ProposerStrategyConfig, *, gateway=None,
            max_output_tokens=1024, run_id=None) -> None:
        self.config = config
        self.gateway = gateway
        self.max_output_tokens = max_output_tokens
        self.run_id = run_id or uuid4().hex
        self.last_exchange = None
        self.last_attempt_id = None
        self._round_id = "standalone"

    def propose_schedule(self, round_id: str, num_qubits: int, target_operation: str,
            noise_couplings: Tuple[Tuple[int, int, Fraction], ...],
            tolerance_epsilon: Fraction) -> MultiQubitNoisyBraidProposalPacket:
        self._round_id = round_id
        self.last_exchange = None
        operations = self._synthesize_operations(num_qubits, target_operation, noise_couplings)
        return MultiQubitNoisyBraidProposalPacket(round_id=round_id,
            proposer_id=self.config.proposer_id, num_qubits=num_qubits,
            operations=operations, noise_couplings=noise_couplings,
            tolerance_epsilon=tolerance_epsilon)

    def _synthesize_operations(self, num_qubits, target_operation, noise_couplings):
        if self.config.use_live_openrouter:
            return self._query_openrouter(num_qubits, target_operation, noise_couplings)
        if self.config.strategy_type == "echo_mitigated":
            return self._build_echo_mitigated_schedule(num_qubits, target_operation)
        if self.config.strategy_type == "targeted_compensation":
            return self._build_targeted_compensation_schedule(num_qubits, target_operation, noise_couplings)
        if self.config.strategy_type == "random_baseline":
            return self._build_random_baseline_schedule(num_qubits)
        return self._build_direct_unmitigated_schedule(num_qubits, target_operation)

    def _query_openrouter(self, num_qubits, target_operation, noise_couplings):
        if self.gateway is None:
            raise ValueError("PFP_ACCOUNTED_GATEWAY_REQUIRED")
        prompt = (
            f"You are a topological quantum compilation agent in the Symbol Game.\n"
            f"Synthesize an adaptive braid schedule on {num_qubits} qubits (qubits 1..{num_qubits}, modes 1..{4 * num_qubits}).\n"
            f"Target operation: {target_operation}.\n"
            f"Active noise couplings: {[[a, b, str(c)] for a, b, c in noise_couplings]}.\n"
            f"Return JSON strictly with format: "
            f'{{"operations": [["hadamard", [1, 0]], ["phase", [1, 0]]]}}'
        )
        schema = {"type": "object", "additionalProperties": False,
            "required": ["operations"], "properties": {"operations": {
                "type": "array", "maxItems": 64, "items": {"type": "array",
                    "minItems": 2, "maxItems": 2, "prefixItems": [
                        {"type": "string"}, {"type": "array", "minItems": 2,
                            "maxItems": 2, "items": {"type": "integer"}}], "items": False}}}}
        request = CandidateRequest("Propose the supplied finite braid schedule.", prompt,
            decoding=DecodingParamsV1(temperature=0.0, response_format={
                "type": "json_schema", "json_schema": {"name": "braid_schedule",
                    "strict": True, "schema": schema}}))
        self.last_attempt_id = f"{self.run_id}:{self._round_id}:{self.config.proposer_id}"
        self.last_exchange = complete_pilot_turn(self.gateway, request,
            model=self.config.model_name, task_id=f"braid:{self.run_id}:{self._round_id}",
            attempt_id=self.last_attempt_id, max_tokens=self.max_output_tokens)
        exchange = self.last_exchange
        if not exchange["ok"] or exchange["stop"]:
            raise ValueError(exchange["error"] or "PFP_UNAVAILABLE")
        if exchange["attempt_state"] != "CompletedSettled":
            raise ValueError(exchange["attempt_state"] or "PFP_ACCOUNTING_UNSETTLED")
        data = json.loads(exchange["content"])
        return tuple((op, tuple(args)) for op, args in data["operations"])

    def _build_direct_unmitigated_schedule(
        self, num_qubits: int, target_operation: str
    ) -> Tuple[Tuple[str, Tuple[int, ...]], ...]:
        """Bare logical gate without echo pulses or commutation mitigation (1-indexed qubits)."""
        ops: List[Tuple[str, Tuple[int, ...]]] = []
        if target_operation in ("hadamard_q1", "hadamard_q0"):
            ops.append(("hadamard", (1, 0)))
        elif target_operation in ("phase_q1", "phase_q0"):
            ops.append(("phase", (1, 0)))
        elif target_operation in ("cnot_12", "cnot_01") and num_qubits >= 2:
            ops.append(("cnot", (1, 2)))
        elif target_operation == "bell_pair" and num_qubits >= 2:
            ops.append(("hadamard", (1, 0)))
            ops.append(("cnot", (1, 2)))
        else:
            ops.append(("phase", (1, 0)))
        return tuple(ops)


    def _build_echo_mitigated_schedule(
        self, num_qubits: int, target_operation: str
    ) -> Tuple[Tuple[str, Tuple[int, ...]], ...]:
        """Interleaved spin-echo braid sequences to cancel spectator drift."""
        ops: List[Tuple[str, Tuple[int, ...]]] = []
        if target_operation in ("hadamard_q1", "hadamard_q0"):
            # Echo sequence on qubit 1: phase(1) + phase(1, inv) cancels identity while keeping gauge tight
            ops.append(("phase", (1, 0)))
            ops.append(("phase", (1, 1)))
            ops.append(("hadamard", (1, 0)))
        elif target_operation in ("phase_q1", "phase_q0"):
            ops.append(("phase", (1, 0)))
        elif target_operation in ("cnot_12", "cnot_01") and num_qubits >= 2:
            ops.append(("cnot", (1, 2)))
        elif target_operation == "bell_pair" and num_qubits >= 2:
            ops.append(("hadamard", (1, 0)))
            ops.append(("cnot", (1, 2)))
        else:
            ops.append(("phase", (1, 0)))
        return tuple(ops)


    def _build_targeted_compensation_schedule(
        self,
        num_qubits: int,
        target_operation: str,
        noise_couplings: Tuple[Tuple[int, int, Fraction], ...],
    ) -> Tuple[Tuple[str, Tuple[int, ...]], ...]:
        """Targeted compensation targeting specific modes with high noise couplings."""
        ops: List[Tuple[str, Tuple[int, ...]]] = []
        # Sort couplings by magnitude
        sorted_couplings = sorted(noise_couplings, key=lambda c: abs(c[2]), reverse=True)
        if sorted_couplings:
            top_a, top_b, _ = sorted_couplings[0]
            # Add compensating localized elementary braids if valid
            if 1 <= top_a < 4 * num_qubits:
                ops.append(("elementary", (top_a, 0)))
                ops.append(("elementary", (top_a, 1)))

        if target_operation in ("hadamard_q1", "hadamard_q0"):
            ops.append(("hadamard", (1, 0)))
        elif target_operation in ("phase_q1", "phase_q0"):
            ops.append(("phase", (1, 0)))
        elif target_operation in ("cnot_12", "cnot_01") and num_qubits >= 2:
            ops.append(("cnot", (1, 2)))
        elif target_operation == "bell_pair" and num_qubits >= 2:
            ops.append(("hadamard", (1, 0)))
            ops.append(("cnot", (1, 2)))
        else:
            ops.append(("phase", (1, 0)))
        return tuple(ops)


    def _build_random_baseline_schedule(
        self, num_qubits: int
    ) -> Tuple[Tuple[str, Tuple[int, ...]], ...]:
        """Negative baseline: arbitrary elementary braid that perturbs the carrier."""
        # A single elementary braid on boundary mode
        return (("elementary", (1, 0)),)



class AdaptiveBraidTournament:
    """Serial finite rounds with one continuing accounted live allowance."""

    def __init__(self, tournament_id: str, num_qubits: int = 2,
            proposers: Optional[Sequence[ProposerStrategyConfig]] = None,
            referee: Optional[MultiQubitNoisyBraidReferee] = None, *,
            gateways=None, output_dir=None, max_rounds=4, max_output_tokens=1024,
            max_provider_calls=16, max_estimated_cost_microusd=None, env_file=None) -> None:
        self.tournament_id, self.num_qubits = tournament_id, num_qubits
        self.referee = referee or MultiQubitNoisyBraidReferee()
        self.proposers = list(proposers) if proposers is not None else [
            ProposerStrategyConfig("agent-llama-8b", MODEL_8B, "direct_unmitigated"),
            ProposerStrategyConfig("agent-llama-70b", MODEL_70B, "echo_mitigated"),
            ProposerStrategyConfig("agent-glm-5.3", MODEL_GLM53, "targeted_compensation"),
            ProposerStrategyConfig("agent-random-baseline", "random-negative-control", "random_baseline")]
        self.gateways = gateways
        self.output_dir = Path(output_dir) if output_dir is not None else None
        self.max_rounds, self.max_output_tokens = max_rounds, max_output_tokens
        self.max_provider_calls = max_provider_calls
        self.max_estimated_cost_microusd = max_estimated_cost_microusd
        self.env_file = env_file
        self.report = {}
        self._agents = []

    def _prepare(self, budgets, target_operation, tolerance_multiplier):
        if self.output_dir is not None and self.output_dir.exists():
            raise ValueError("OUTPUT_DIR_EXISTS")
        for name, value, maximum in (("max_rounds", self.max_rounds, 64),
                ("max_output_tokens", self.max_output_tokens, 3000),
                ("max_provider_calls", self.max_provider_calls, 64),
                ("num_qubits", self.num_qubits, 8)):
            if type(value) is not int or not 0 < value <= maximum:
                raise ValueError("INVALID_" + name.upper())
        if not budgets or len(budgets) > self.max_rounds or any(b < 0 for b in budgets):
            raise ValueError("INVALID_OR_UNBOUNDED_NOISE_BUDGETS")
        if tolerance_multiplier < 0 or not target_operation:
            raise ValueError("INVALID_TOURNAMENT_TASK")
        ids = [p.proposer_id for p in self.proposers]
        if not ids or len(ids) > 16 or len(set(ids)) != len(ids) or any(not i for i in ids):
            raise ValueError("INVALID_PROPOSER_IDS")
        models = tuple(dict.fromkeys(p.model_name for p in self.proposers if p.use_live_openrouter))
        cap = self.max_estimated_cost_microusd
        if cap is not None and (type(cap) is not int or not 0 < cap <= 50000):
            raise ValueError("INVALID_ESTIMATED_POLICY")
        if models and self.gateways is None and (cap is None or self.output_dir is None):
            raise ValueError("PFP_ACCOUNTED_POLICY_AND_OUTPUT_REQUIRED")
        if models and self.gateways is not None:
            validate_pilot_gateways(self.gateways, models, max_tokens=self.max_output_tokens)
            scope = _scope(self.gateways[models[0]], models[0], self.max_output_tokens)
            if scope[3] > self.max_provider_calls or (cap is not None and scope[2] > cap):
                raise ValueError("PFP_INJECTED_ALLOWANCE_EXCEEDS_REQUESTED_CAP")
        run_id = uuid4().hex
        if self.output_dir is not None:
            try:
                self.output_dir.mkdir(parents=True, exist_ok=False)
            except FileExistsError as exc:
                raise ValueError("OUTPUT_DIR_EXISTS") from exc
        if models and self.gateways is None:
            objective = json.dumps({"budgets": [str(b) for b in budgets],
                "operation": target_operation, "proposers": [asdict(p) for p in self.proposers],
                "qubits": self.num_qubits, "tolerance_multiplier": str(tolerance_multiplier)}, sort_keys=True)
            self.gateways = make_pilot_gateways(models, max_output_tokens=self.max_output_tokens,
                max_estimated_cost_microusd=cap, max_calls=self.max_provider_calls,
                accounting_path=self.output_dir / "accounting.sqlite3", env_file=self.env_file,
                run_id=run_id, objective_sha256=hashlib.sha256(objective.encode("utf-8")).hexdigest())
        self._agents = [BraidTournamentProposerAgent(config,
            gateway=self.gateways[config.model_name] if config.use_live_openrouter else None,
            max_output_tokens=self.max_output_tokens, run_id=run_id) for config in self.proposers]

    def run_sweep(self, noise_budgets: Sequence[Fraction | int | str],
            target_operation: str = "hadamard_q1",
            tolerance_multiplier: Fraction = Fraction(2, 1)) -> TournamentRunReceipt:
        if any(type(b) not in (Fraction, int, str) for b in noise_budgets):
            raise ValueError("EXACT_RATIONAL_NOISE_REQUIRED")
        if type(tolerance_multiplier) not in (Fraction, int, str):
            raise ValueError("EXACT_RATIONAL_TOLERANCE_REQUIRED")
        budgets_frac = tuple(Fraction(b) for b in noise_budgets)
        tolerance_multiplier = Fraction(tolerance_multiplier)
        self._prepare(budgets_frac, target_operation, tolerance_multiplier)
        round_results = []
        observations = []
        observed_models = []
        calls, known_cost, unknown_cost, stop_reason = 0, Fraction(0), False, None
        for round_idx, budget in enumerate(budgets_frac, 1):
            round_id = f"RND-{self.tournament_id}-{round_idx:03d}"
            tol = budget * tolerance_multiplier
            couplings = self._generate_couplings(self.num_qubits, budget, seed=round_idx)
            for agent in self._agents:
                if agent.config.use_live_openrouter and calls >= self.max_provider_calls:
                    stop_reason = "CALL_ALLOWANCE_EXHAUSTED"
                    break
                observation = dict(round_id=round_id, proposer_id=agent.config.proposer_id,
                    execution="live" if agent.config.use_live_openrouter else "deterministic",
                    exchange=None, judge_eligible=False, status_reason=None)
                failure = None
                try:
                    proposal = agent.propose_schedule(round_id, self.num_qubits,
                        target_operation, couplings, tol)
                except ValueError as exc:
                    failure = str(exc)
                exchange = agent.last_exchange
                if exchange is not None:
                    observation["exchange"] = exchange
                    claim = None
                    try:
                        claim = agent.gateway.action(agent.last_attempt_id)
                    except KeyError:
                        pass
                    attempted = (exchange["provider_wire"] is not None or
                        claim is not None and claim["state"] != "refused_before_dispatch")
                    if attempted:
                        calls += 1
                        cost = exchange["usage"].get("cost")
                        if cost is None:
                            unknown_cost = True
                        else:
                            known_cost += Fraction(str(cost))
                if failure:
                    observation["status_reason"] = failure
                    observations.append(observation)
                    stop_reason = failure
                    break
                receipt = self.referee.evaluate(proposal)
                observation.update(judge_eligible=True, status_reason=receipt.status_reason)
                observations.append(observation)
                if agent.config.use_live_openrouter and agent.config.model_name not in observed_models:
                    observed_models.append(agent.config.model_name)
                round_results.append(TournamentRoundResult(round_id=round_id,
                    num_qubits=self.num_qubits, target_operation=target_operation,
                    noise_budget=budget, tolerance_epsilon=tol,
                    proposer_id=agent.config.proposer_id, model_name=agent.config.model_name,
                    is_accepted=receipt.is_accepted, status_reason=receipt.status_reason,
                    gate_count=receipt.gate_count, circuit_noise_defect=receipt.circuit_noise_defect,
                    receipt_digest=receipt.sha256_hash))
            if stop_reason:
                break
        receipt = TournamentRunReceipt(tournament_id=self.tournament_id,
            num_qubits=self.num_qubits, num_rounds=len(budgets_frac), noise_budgets=budgets_frac,
            models_evaluated=tuple(observed_models), leaderboard=self._compute_leaderboard(round_results),
            round_results=tuple(round_results), sha256_hash="", authority_effect="None")
        receipt = replace(receipt, sha256_hash=receipt.canonical_digest())
        has_live = any(p.use_live_openrouter for p in self.proposers)
        live_results = sum(o["judge_eligible"] and o["execution"] == "live" for o in observations)
        deterministic_results = sum(
            o["judge_eligible"] and o["execution"] == "deterministic" for o in observations)
        if live_results and deterministic_results:
            evidence_grade = "MIXED_BOUND_MODEL_AND_DETERMINISTIC_ORIGINAL_REFEREE"
        elif live_results:
            evidence_grade = "BOUND_MODEL_ORIGINAL_REFEREE"
        elif deterministic_results:
            evidence_grade = "DETERMINISTIC_ORIGINAL_REFEREE"
        else:
            evidence_grade = "NO_REFEREE_RESULTS"
        self.report = dict(schema="pfp.braid-tournament.v1", authority_effect="None",
            evidence_grade=evidence_grade,
            judged_live_results=live_results, judged_deterministic_results=deterministic_results,
            scope="Finite SO/noise conditions; target-operation equivalence is not checked.",
            controls_honored="UNVERIFIED", actual_concurrency=1, provider_calls=calls,
            configured_models=[p.model_name for p in self.proposers], observed_models=observed_models,
            planned_results=len(budgets_frac) * len(self.proposers), completed_results=len(round_results),
            completed=stop_reason is None, stop_reason=stop_reason,
            max_output_tokens=self.max_output_tokens, max_provider_calls=self.max_provider_calls,
            financial_policy=("no_provider" if not has_live else
                "injected_accounted" if self.max_estimated_cost_microusd is None
                else "explicitly_estimated_not_vendor_liability_cap"),
            total_cost_usd=None if unknown_cost else float(known_cost),
            known_cost_subtotal_usd=float(known_cost), observations=observations,
            receipt=asdict(receipt))
        if self.output_dir is not None:
            (self.output_dir / "tournament.json").write_text(
                json.dumps(self.report, default=str, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        return receipt

    def _generate_couplings(
        self, num_qubits: int, budget: Fraction, seed: int
    ) -> Tuple[Tuple[int, int, Fraction], ...]:
        """Generates deterministic skew-symmetric coupling coordinates with bounded budget."""
        num_modes = 4 * num_qubits
        couplings: List[Tuple[int, int, Fraction]] = []
        # Create asymmetric stray couplings targeting modes 1 and 2
        couplings.append((1, 2, budget))
        for a in range(2, num_modes):
            b = a + 1
            coeff = Fraction((seed * a) % 3 + 1, 3) * budget
            couplings.append((a, b, coeff))
        return tuple(couplings)


    def _compute_leaderboard(
        self, results: List[TournamentRoundResult]
    ) -> Tuple[ProposerLeaderboardEntry, ...]:
        """Aggregates scores and ranks proposers by acceptance rate and mean defect."""
        by_proposer: Dict[str, List[TournamentRoundResult]] = {}
        for r in results:
            by_proposer.setdefault(r.proposer_id, []).append(r)

        entries: List[ProposerLeaderboardEntry] = []
        for prop_cfg in self.proposers:
            pid = prop_cfg.proposer_id
            rounds = by_proposer.get(pid, [])
            total = len(rounds)
            accepted = sum(1 for r in rounds if r.is_accepted)
            acc_rate = Fraction(accepted, total) if total > 0 else Fraction(0, 1)

            defects = [r.circuit_noise_defect for r in rounds]
            mean_defect = (
                sum(defects, Fraction(0, 1)) / Fraction(total, 1) if total > 0 else Fraction(0, 1)
            )
            min_defect = min(defects) if defects else Fraction(0, 1)
            max_defect = max(defects) if defects else Fraction(0, 1)

            entries.append(
                ProposerLeaderboardEntry(
                    proposer_id=pid,
                    model_name=prop_cfg.model_name,
                    strategy_type=prop_cfg.strategy_type,
                    total_rounds=total,
                    accepted_rounds=accepted,
                    acceptance_rate=acc_rate,
                    mean_noise_defect=mean_defect,
                    min_defect=min_defect,
                    max_defect=max_defect,
                    rank=0,  # assigned below
                )
            )

        # Sort: descending acceptance rate, then ascending mean defect
        entries.sort(key=lambda e: (-e.acceptance_rate, e.mean_noise_defect))

        ranked: List[ProposerLeaderboardEntry] = []
        for rank, e in enumerate(entries, 1):
            ranked.append(
                ProposerLeaderboardEntry(
                    proposer_id=e.proposer_id,
                    model_name=e.model_name,
                    strategy_type=e.strategy_type,
                    total_rounds=e.total_rounds,
                    accepted_rounds=e.accepted_rounds,
                    acceptance_rate=e.acceptance_rate,
                    mean_noise_defect=e.mean_noise_defect,
                    min_defect=e.min_defect,
                    max_defect=e.max_defect,
                    rank=rank,
                )
            )

        return tuple(ranked)


def run_canonical_tournament_demo() -> TournamentRunReceipt:
    """Execute the original deterministic schedules without attributing model runs."""
    tournament = AdaptiveBraidTournament("PFP-TOURNAMENT-DEMO-020")
    receipt = tournament.run_sweep(DEFAULT_NOISE_BUDGETS)
    print(receipt.claim_hygiene_summary())
    return receipt
