"""Per-act execution helpers for the 7-Act Adversary Swarm bout.

Each function encapsulates one act's logic and returns a typed Result or tuple.

Evidence discipline (the terminal gate reads nothing else):

* Act I parses the declared carrier into exact rationals or refuses. A carrier
  with a missing or misspelled key is a typed refusal, never a default carrier.
* Act II returns an ``ObstructionMeasurementV1``: exact Phi1 and Gamma2 behind a
  verified certificate, or ``NOT_MEASURED`` with the reason.
* Act IV's lift transports the input cochain: original edges keep their values
  and only the new bridge edges start at zero. It never replaces the cochain.
* Act V reads a critic's typed ``critique`` JSON block. Prose keywords decide
  nothing; an unparsable critique is ``MALFORMED`` and blocks its candidate.
* Act VII authorizes only on an exact joint zero (``Fraction`` equality, no
  tolerance) together with an ``ACCEPTED`` challenge-checker verdict bound to
  the candidate's content digest and the checker receipt digest.

AuthorityEffect: None.
"""

from __future__ import annotations

import ast
import datetime
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any

from operations.domain.rop.result import Err, Ok, Refusal, Result
from pfp.domain.value_objects.seat_turn import SeatTurnRequestV1
from adversary.domain.evidence import (
    CRITIQUE_REPLY_CONTRACT,
    CandidateCheckV1,
    CheckerVerdict,
    CritiqueStatus,
    ObstructionMeasurementV1,
    canonical_rational,
    parse_exact_rational,
    parse_structured_critique,
)
from adversary.domain.native import NativeOperationPort
from adversary.domain.native import invoke as native_invoke
from adversary.domain.network import Network
from adversary.domain.ports import (
    CandidateCheckerPort,
    CochainScoringPort,
    NullCandidateCheckerAdapter,
    NullCochainScoringAdapter,
)
from adversary.stage.application.emission import (
    build_intelligence_event,
    compute_sbe_metrics,
    emit_event,
)
from adversary.stage.application.run_swarm import SwarmRuntimeV1
from adversary.stage.domain import (
    AUTHORITY_EFFECT_NONE,
    AntibodyEntryV1,
    CandidateProposalV1,
    CandidateSelectionProposalV1,
    CemeteryHeadstoneV1,
    ChallengeV1,
    DdaLetter,
    DdaStepV1,
    GenealogyEntryV1,
)
from adversary.use_cases.cemetery_regression import (
    AdmittedAntibodyReader,
    screen_known_regressions,
)

_LOCUS = "adversary.use_cases.act_helpers"

#: Keys a carrier may use. Any other key that *looks* like a carrier key (see
#: ``_CARRIER_LIKE``) -- ``cochain``, ``initial_cochains``, ``vertices``,
#: ``tetrahedron`` ... -- also declares a carrier, and is then refused as
#: unknown, instead of silently leaving the bout without a carrier.
CARRIER_KEYS = frozenset(
    {"nodes", "edges", "faces", "cochains", "tetrahedra", "four_simplices", "regge_spacetime"}
)
REQUIRED_CARRIER_KEYS = ("nodes", "edges", "cochains")
_CARRIER_LIKE = re.compile(
    r"(initial_)?(node|vert|edge|face|cochain|cell|simpl|tetra|four_simpl|regge)",
    re.IGNORECASE,
)

#: Two candidates whose synthetic SBE diagnostics differ by less than this
#: (exact l1 distance over entropy_bits and purity) count as stagnant.
STAGNATION_SBE_THRESHOLD = Fraction(1, 20)

CARRIER_DECLARED = "DECLARED"
CARRIER_NOT_DECLARED = "NOT_DECLARED"
CARRIER_STATUSES = frozenset({CARRIER_DECLARED, CARRIER_NOT_DECLARED})

#: The evidence path recorded when Act VII authorizes. Exactly one applies.
EVIDENCE_CHECKER_ONLY = "CHECKER_VERDICT_ONLY_NO_CARRIER_DECLARED"
EVIDENCE_CHECKER_AND_CARRIER = "CHECKER_VERDICT_AND_EXACT_ZERO_CARRIER"


def _digest(data: str | bytes) -> str:
    """Produce a prefixed SHA-256 hex digest from string or bytes."""
    raw = data.encode("utf-8") if isinstance(data, str) else data
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _canonical_json_digest(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    )
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _timestamp(now_utc: str | None) -> str:
    return now_utc or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _refuse(code: str, message: str) -> Err[Refusal]:
    return Err(Refusal(code, message, _LOCUS))


def _parse_cochain_key(k: Any) -> tuple[Any, ...]:
    """Parse edge cochain key from tuple, list, or JSON string representation.

    Handles:
    - (0, 1) or [0, 1] -> (0, 1)
    - "[0, 1]" or "(0, 1)" -> (0, 1)
    - "0, 1" or "0,1" -> (0, 1)
    - "0->1" -> (0, 1)
    - '("u", "v")' or 'u, v' -> ('u', 'v')
    """
    if isinstance(k, (tuple, list)):
        return tuple(k)
    if isinstance(k, str):
        try:
            val = ast.literal_eval(k)
            if isinstance(val, (tuple, list)):
                return tuple(val)
        except (ValueError, SyntaxError):
            pass
        cleaned = k.strip().lstrip("([{\"'").rstrip(")]}\"'")
        sep = "," if "," in cleaned else ("->" if "->" in cleaned else None)
        if sep:
            parts = [p.strip().strip("'\"") for p in cleaned.split(sep)]
            conv: list[Any] = []
            for p in parts:
                try:
                    conv.append(int(p))
                except ValueError:
                    conv.append(p)
            return tuple(conv)
        parts = cleaned.split()
        if len(parts) == 2:
            conv = []
            for p in parts:
                try:
                    conv.append(int(p))
                except ValueError:
                    conv.append(p)
            return tuple(conv)
        return (k,)
    return tuple(k) if hasattr(k, "__iter__") and not isinstance(k, (str, bytes)) else (k,)


def _node_label(value: Any) -> Any:
    """Admit an int or nonempty string node label; floats and bools collide with ints."""
    if type(value) is int or (type(value) is str and value.strip()):
        return value
    raise TypeError(f"node labels must be ints or nonempty strings, got {value!r}")


def _parse_carrier(
    carrier_context: Mapping[str, Any] | None,
    *,
    native_support: NativeOperationPort,
) -> Result[tuple[Network, dict[tuple[Any, Any], Fraction], str, int], Refusal]:
    """Decode the native exact carrier into the retained immutable Python DTOs."""
    if carrier_context is not None and not isinstance(carrier_context, Mapping):
        return _refuse("ADVERSARY_CARRIER_MALFORMED", "carrier_context must be a mapping")
    wire = dict(carrier_context) if carrier_context is not None else None
    if wire is not None and isinstance(wire.get("cochains"), Mapping):
        wire["cochains"] = {
            str(key) if not isinstance(key, str) else key: canonical_rational(item)
            if type(item) is Fraction
            else item
            for key, item in wire["cochains"].items()
        }
    parsed = native_invoke(native_support,
        "carrier", carrier_json=json.dumps(wire, ensure_ascii=False) if wire is not None else None
    )
    if isinstance(parsed, Err):
        return parsed
    result = parsed.value
    return Ok(
        (
            Network(**result["network"]),
            {tuple(item["edge"]): Fraction(item["value"]) for item in result["cochain"]},
            result["carrier_status"],
            result["implicit_zero_edges"],
        )
    )


def execute_act1_carrier_framing(
    rt: SwarmRuntimeV1,
    run_key: str,
    objective: str,
    carrier_context: Mapping[str, Any] | None = None,
    *,
    now_utc: str = "",
    native_support: NativeOperationPort,
) -> Result[
    tuple[
        Network,
        dict[tuple[Any, Any], Fraction],
        list[AntibodyEntryV1],
        dict[str, Any],
        dict[str, Any],
    ],
    Refusal,
]:
    """Act I: Intake & Carrier Framing — exact carrier parse and antibody loading."""
    parsed = _parse_carrier(carrier_context, native_support=native_support)
    if parsed.is_err:
        return Err(parsed.unwrap_err())
    carrier_network, initial_cochain, carrier_status, implicit_zero_edges = parsed.unwrap()

    active_antibodies: list[AntibodyEntryV1] = []
    if rt.emitters and rt.emitters.antibodies:
        ab_res = rt.emitters.antibodies.load_antibodies(objective)
        if ab_res.is_ok:
            active_antibodies = list(ab_res.unwrap())

    prompt_sbe = compute_sbe_metrics(objective, dim=28)
    timestamp = _timestamp(now_utc)

    if rt.emitters:
        act1_event, act1_bytes = build_intelligence_event(
            ie_id=_digest(f"{run_key}:act1"),
            actor_id="actor_thanatos_procurator",
            actor_kind="SWARM_SEAT",
            event_kind="COMM",
            source_system="oeas.act1",
            session_id=run_key,
            payload={
                "act": "I",
                "title": "Catalyst & Perception",
                "objective": objective,
                "active_antibodies": [ab.to_dict() for ab in active_antibodies],
                "carrier_status": carrier_status,
                "forge_sbe": prompt_sbe,
            },
        )
        act1_emit_res = emit_event(
            act1_event,
            act1_bytes,
            rt.emitters,
            dda_step=DdaStepV1(
                letter=DdaLetter.C,
                before_class="UnindexedPrompt",
                after_class="PerceivedCatalyst",
                carrier_hash=_digest(b"carrier"),
                witness_hash=_digest(objective),
                receipt_sha256=_digest(act1_bytes),
                timestamp=timestamp,
            ),
        )
        if act1_emit_res.is_err:
            return Err(act1_emit_res.unwrap_err())

    narrative = {
        "act_number": "I",
        "title": "Catalyst & Perception",
        "body": (
            f"Prompt ingested: '{objective}'. Loaded {len(active_antibodies)} active "
            f"antibodies from compost history. Carrier {carrier_status}"
            + (
                f" ({len(carrier_network.edges)} edges, {implicit_zero_edges} "
                "left unassigned and recorded as zero)."
                if carrier_status == CARRIER_DECLARED
                else "; no carrier measurement is possible."
            )
        ),
        "carrier_status": carrier_status,
        "implicit_zero_edges": implicit_zero_edges,
    }
    return Ok((carrier_network, initial_cochain, active_antibodies, prompt_sbe, narrative))


def execute_act2_obstruction_identification(
    carrier_network: Network,
    initial_cochain: Mapping[tuple[Any, Any], Any],
    *,
    ablation_flags: Mapping[str, bool] | None = None,
    cochain_adapter: CochainScoringPort | None = None,
    rt: SwarmRuntimeV1 | None = None,
    run_key: str = "",
    now_utc: str | None = None,
) -> Result[tuple[ObstructionMeasurementV1, dict[str, Any]], Refusal]:
    """Act II: Obstruction Identification — delegate to the scoring port and emit R."""
    if not carrier_network.nodes:
        measurement = ObstructionMeasurementV1.not_measured(
            "NO_CARRIER_DECLARED: the bout declared no carrier to measure",
            backend="carrier_validation",
        )
    else:
        adapter = cochain_adapter or NullCochainScoringAdapter()
        res = adapter.identify_obstructions(
            carrier_network, initial_cochain, ablation_flags=ablation_flags
        )
        if res.is_err:
            return Err(res.unwrap_err())
        measurement = res.unwrap()
        if type(measurement) is not ObstructionMeasurementV1:
            return _refuse(
                "ADVERSARY_SCORER_CONTRACT_VIOLATION",
                "the cochain scorer must return an exact ObstructionMeasurementV1",
            )

    if measurement.is_measured:
        body = (
            f"Exact measurement: Phi1={measurement.phi1_text()}, "
            f"Gamma2={measurement.gamma2_text()}, active defects={measurement.defect_count}, "
            f"certificate verified by {measurement.backend}."
        )
    else:
        body = f"NOT_MEASURED ({measurement.backend}): {measurement.reason}"
    narrative = {
        "act_number": "II",
        "title": "Obstruction Identification",
        "body": body,
        "measurement": measurement.to_dict(),
    }

    if rt is not None and rt.emitters:
        act2_event, act2_bytes = build_intelligence_event(
            ie_id=_digest(f"{run_key}:act2"),
            actor_id="actor_aletheia_procurator",
            actor_kind="SWARM_SEAT",
            event_kind="COMM",
            source_system="oeas.act2",
            session_id=run_key,
            payload={
                "act": "II",
                "title": "Obstruction Identification",
                "measurement": measurement.to_dict(),
            },
        )
        act2_emit_res = emit_event(
            act2_event,
            act2_bytes,
            rt.emitters,
            dda_step=DdaStepV1(
                letter=DdaLetter.R,
                before_class="PerceivedCatalyst",
                after_class="ActiveObstruction",
                carrier_hash=_digest(b"carrier"),
                witness_hash=_digest(str(list(measurement.active_obstructions))),
                receipt_sha256=_digest(act2_bytes),
                timestamp=_timestamp(now_utc),
                phi_1=measurement.phi1 if measurement and measurement.is_measured else None,
                gamma_2=measurement.gamma2 if measurement and measurement.is_measured else None,
            ),
        )
        if act2_emit_res.is_err:
            return Err(act2_emit_res.unwrap_err())

    return Ok((measurement, narrative))


def _seat_turn(rt: Any, request: SeatTurnRequestV1) -> Result[Any, Refusal]:
    if not getattr(rt, "seat_port", None):
        return _refuse("NO_SEAT_PORT", "SeatPort missing")
    return rt.seat_port.execute_turn(request)


def _reply_provenance(reply: Any) -> dict[str, Any]:
    provenance = reply.provenance() if hasattr(reply, "provenance") else {}
    return {
        "model": provenance.get("model") or "NOT_REPORTED",
        "provider": provenance.get("provider") or "NOT_REPORTED",
        "parameters": provenance.get("parameters"),
        "usage": provenance.get("usage"),
        "request_digest": provenance.get("request_digest"),
    }


def execute_act3_candidate_proposal_generation(
    rt: SwarmRuntimeV1,
    pkt_id: str,
    run_key: str,
    objective: str,
    measurement: ObstructionMeasurementV1 | None = None,
    active_obstructions: Sequence[str] = (),
    *,
    now_utc: str = "",
) -> Result[
    tuple[
        list[CandidateProposalV1],
        list[dict[str, Any]],
        list[CemeteryHeadstoneV1],
        dict[str, Any],
    ],
    Refusal,
]:
    """Act III: Candidate Proposal Generation — Multi-candidate proposals from seat_gauge_breaker."""
    del measurement, active_obstructions
    candidates: list[CandidateProposalV1] = []
    candidates_data: list[dict[str, Any]] = []
    dead_candidates: list[CemeteryHeadstoneV1] = []

    for cand_idx in range(rt.max_candidate_budget):
        cand_id = f"cand_{cand_idx + 1}"
        turn_req = SeatTurnRequestV1(
            scene_id="act2_panel_debate",
            seat_id="seat_gauge_breaker",
            prompt_text=f"Generate candidate {cand_idx + 1} for objective: '{objective}'.",
            cognitive_operator="Nine-Dot Surprise & Playful Comedy (E_surprise)",
            candidate_id=cand_id,
            round_index=0,
        )
        turn_res = _seat_turn(rt, turn_req)
        if turn_res.is_err:
            return Err(turn_res.unwrap_err())
        reply = turn_res.unwrap()
        provenance = _reply_provenance(reply)

        if not reply.reply_text.strip() or reply.authority_effect != AUTHORITY_EFFECT_NONE:
            headstone = CemeteryHeadstoneV1(
                candidate_id=cand_id,
                run_key=run_key,
                scene_id="act2_panel_debate",
                cause_of_death="CHEAP_GATE_FAILED: Empty response or authority violation",
                killing_seat_id="seat_syntax_prefilter",
                evidence_refs=(),
                candidate_payload_sha256=_digest(reply.raw_bytes),
                round_index=0,
            )
            dead_candidates.append(headstone)
            candidates_data.append(
                {
                    "candidate_id": "",
                    "candidate_request_id": cand_id,
                    "candidate_proposal": None,
                    "capture_status": "CHEAP_GATE_FAILED",
                    **provenance,
                    "content": reply.reply_text,
                    "raw_reply_sha256": _digest(reply.raw_bytes),
                    "raw_reply_hex": reply.raw_bytes.hex(),
                    "producer_seat_id": "seat_gauge_breaker",
                    "machine_fields": dict(reply.machine_fields),
                    "residual_colour": reply.residual_colour,
                    "reported_authority_effect": reply.authority_effect,
                    "authority_effect": AUTHORITY_EFFECT_NONE,
                    "verification_status": "NOT_RUN",
                }
            )
            if rt.emitters and rt.emitters.cemetery:
                cemetery_res = rt.emitters.cemetery.record_headstone(headstone)
                if cemetery_res.is_err:
                    return Err(cemetery_res.unwrap_err())
            continue

        cand_content = reply.reply_text
        cand_artifact_ref = _digest(cand_content)
        cand_receipt_id = _digest(cand_id.encode("utf-8") + b"\0" + reply.raw_bytes)
        cand_obj = CandidateProposalV1(
            producer_agent_id="seat_gauge_breaker",
            work_packet_id=pkt_id,
            artifact_refs=(cand_artifact_ref,),
            prediction_receipt_id=cand_receipt_id,
            nonclaims=(
                "Candidate generation only.",
                "AuthorityEffect is strictly None.",
            ),
            authority_effect=AUTHORITY_EFFECT_NONE,
        )
        candidates.append(cand_obj)
        candidates_data.append(
            {
                "candidate_id": cand_obj.candidate_id,
                "candidate_proposal": cand_obj.to_dict(),
                "capture_status": "PROPOSED",
                "candidate_request_id": cand_id,
                "prediction_receipt_id": cand_receipt_id,
                **provenance,
                "content": cand_content,
                "content_sha256": cand_artifact_ref,
                "raw_reply_sha256": _digest(reply.raw_bytes),
                "raw_reply_hex": reply.raw_bytes.hex(),
                "producer_seat_id": "seat_gauge_breaker",
                "machine_fields": dict(reply.machine_fields),
                "residual_colour": reply.residual_colour,
                "reported_authority_effect": reply.authority_effect,
                "authority_effect": AUTHORITY_EFFECT_NONE,
                "verification_status": "NOT_RUN",
            }
        )
    if rt.emitters:
        act3_event, act3_bytes = build_intelligence_event(
            ie_id=_digest(f"{run_key}:act3"),
            actor_id="actor_dianoia_first_curator",
            actor_kind="SWARM_SEAT",
            event_kind="COMM",
            source_system="oeas.act3",
            session_id=run_key,
            payload={
                "act": "III",
                "title": "Candidate Proposal Generation",
                "candidates_count": len(candidates),
            },
        )
        act3_emit_res = emit_event(
            act3_event,
            act3_bytes,
            rt.emitters,
            dda_step=DdaStepV1(
                letter=DdaLetter.C,
                before_class="ActiveObstruction",
                after_class="CandidateProposed",
                carrier_hash=_digest(b"carrier"),
                witness_hash=_digest(str([c.candidate_id for c in candidates])),
                receipt_sha256=_digest(act3_bytes),
                timestamp=_timestamp(now_utc),
            ),
        )
        if act3_emit_res.is_err:
            return Err(act3_emit_res.unwrap_err())

    narrative = {
        "act_number": "III",
        "title": "Candidate Proposal Generation",
        "body": f"Generated {len(candidates)} candidate proposal(s); {len(dead_candidates)} rejected by cheap gate.",
    }
    return Ok((candidates, candidates_data, dead_candidates, narrative))


def _sbe_point(text: str) -> tuple[Fraction, Fraction] | None:
    """The (entropy_bits, purity) point of the synthetic SBE diagnostic, exactly."""
    metrics = compute_sbe_metrics(text, dim=28)
    if metrics.get("measurement_status") != "DETERMINISTIC_SYNTHETIC_DIAGNOSTIC":
        return None
    try:
        return Fraction(metrics["entropy_bits"]), Fraction(metrics["purity"])
    except (KeyError, TypeError, ValueError):
        return None


def _sbe_distance(candidates_data: Sequence[Mapping[str, Any]]) -> Fraction | None:
    """Exact l1 distance between the first two candidates' SBE points, or None."""
    first = _sbe_point(str(candidates_data[0].get("content", "")))
    second = _sbe_point(str(candidates_data[1].get("content", "")))
    if first is None or second is None:
        return None
    return abs(first[0] - second[0]) + abs(first[1] - second[1])


def _fresh_bridge_label(nodes: Sequence[Any]) -> int:
    """Node 9 when free (the nine-dot label), else the next unused integer."""
    used = set(nodes)
    label = 9
    while label in used:
        label += 1
    return label


def execute_act4_gauge_break(
    rt: SwarmRuntimeV1,
    carrier_network: Network,
    initial_cochain: Mapping[tuple[Any, Any], Any],
    candidates: Sequence[CandidateProposalV1],
    candidates_data: Sequence[dict[str, Any]],
    measurement: ObstructionMeasurementV1,
    *,
    ablation_flags: Mapping[str, bool] | None = None,
    run_key: str = "",
    now_utc: str = "",
) -> Result[
    tuple[bool, Network, dict[tuple[Any, Any], Any], dict[str, Any], dict[str, Any]],
    Refusal,
]:
    """Act IV: 9-Dot Gauge Break & Carrier Lift that transports the cochain.

    Stagnation requires a measured open obstruction. With two or more candidates
    it also requires their synthetic SBE points (``entropy_bits``, ``purity``,
    the keys ``compute_sbe_metrics`` actually returns) to lie within
    ``STAGNATION_SBE_THRESHOLD`` of each other.

    The lift adds a bridge node and edges from it. The returned cochain keeps
    every original edge's value; only the new bridge edges start at zero. A
    transported cochain cannot lower Phi1 or Gamma2 (Gamma2 is gauge invariant
    and every new face adds a nonnegative term), so a lift is never a way to
    clear an obstruction.
    """
    del candidates
    obstructed = measurement.has_open_obstruction()
    sbe_delta: Fraction | None = None
    if len(candidates_data) >= 2:
        sbe_delta = _sbe_distance(candidates_data)
        stagnant = bool(
            obstructed and sbe_delta is not None and sbe_delta < STAGNATION_SBE_THRESHOLD
        )
    else:
        stagnant = obstructed

    no_gauge = bool(ablation_flags and ablation_flags.get("no_gauge_change"))
    no_split = bool(ablation_flags and ablation_flags.get("no_carrier_split"))

    asd_telemetry: dict[str, Any] = {
        "sbe_delta": None if sbe_delta is None else canonical_rational(sbe_delta),
        "sbe_threshold": canonical_rational(STAGNATION_SBE_THRESHOLD),
        "measurement_status": measurement.status.value,
        "phi1": measurement.phi1_text(),
        "gamma2": measurement.gamma2_text(),
        "stagnant": stagnant,
        "no_gauge_change_ablated": no_gauge,
        "no_carrier_split_ablated": no_split,
    }

    if no_gauge or no_split or not stagnant:
        gauge_break_triggered = False
        lifted_network = carrier_network
        updated_cochain = dict(initial_cochain)
        if no_gauge:
            body_text = "Act IV 9-dot gauge break suppressed: no_gauge_change ablated (locked gauge coordinates xi=0)."
        elif no_split:
            body_text = "Act IV carrier dimensional lift suppressed: no_carrier_split ablated (single carrier framing locked)."
        elif not obstructed:
            body_text = (
                "No measured open obstruction: carrier framing maintained under standard gauge."
            )
        else:
            body_text = "Carrier framing maintained under standard gauge: no stagnation detected."
        narrative = {
            "act_number": "IV",
            "title": "Gauge Stability",
            "body": body_text,
        }
    else:
        gauge_break_triggered = True
        turn_req = SeatTurnRequestV1(
            scene_id="act4_sandbox",
            seat_id="seat_primal_dual",
            prompt_text="Execute 9-dot gauge break and orthogonal carrier lift on stagnant carrier complex.",
            cognitive_operator="Placebo & Hopeful Generative Envelope (E_placebo)",
        )
        if getattr(rt, "seat_port", None):
            turn_res = rt.seat_port.execute_turn(turn_req)
            if turn_res.is_err:
                return Err(turn_res.unwrap_err())
            asd_telemetry["gauge_break_reply_sha256"] = _digest(turn_res.unwrap().raw_bytes)

        bridge = _fresh_bridge_label(carrier_network.nodes)
        lifted_nodes = tuple(carrier_network.nodes) + (bridge,)
        new_edges: list[tuple[Any, Any]] = []
        for u, v in carrier_network.edges[:2]:
            for edge in ((u, bridge), (v, bridge)):
                rev = (edge[1], edge[0])
                if (
                    edge not in carrier_network.edges
                    and rev not in carrier_network.edges
                    and edge not in new_edges
                    and rev not in new_edges
                ):
                    new_edges.append(edge)
        lifted_edges = tuple(carrier_network.edges) + tuple(new_edges)
        new_faces = tuple((u, v, bridge) for u, v in carrier_network.edges[:2])
        lifted_faces = tuple(carrier_network.faces) + new_faces
        lifted_network = Network(
            nodes=lifted_nodes,
            edges=lifted_edges,
            faces=lifted_faces,
            tetrahedra=carrier_network.tetrahedra,
            four_simplices=carrier_network.four_simplices,
        )
        # Transport, never replacement: every original edge keeps its value.
        updated_cochain = {
            edge: initial_cochain.get(edge, Fraction(0)) for edge in carrier_network.edges
        }
        for edge in new_edges:
            updated_cochain[edge] = Fraction(0)
        asd_telemetry["lift"] = {
            "bridge_node": bridge,
            "new_edges": [list(edge) for edge in new_edges],
            "transported_edges": len(carrier_network.edges),
            "rule": "original edges keep their values; only new bridge edges start at zero",
        }
        narrative = {
            "act_number": "IV",
            "title": "9-Dot Gauge Break",
            "body": (
                f"Act IV 9-dot gauge break executed: lifted carrier with bridge node {bridge}; "
                "the input cochain was transported unchanged onto the original edges."
            ),
        }

    if rt is not None and getattr(rt, "emitters", None):
        act4_event, act4_bytes = build_intelligence_event(
            ie_id=_digest(f"{run_key}:act4"),
            actor_id="actor_dianoia_second_curator",
            actor_kind="SWARM_SEAT",
            event_kind="COMM",
            source_system="oeas.act4",
            session_id=run_key,
            payload={
                "act": "IV",
                "title": "Gauge Break & Carrier Splitting",
                "gauge_break_triggered": gauge_break_triggered,
            },
        )
        letter = DdaLetter.LAMBDA if gauge_break_triggered else DdaLetter.C
        act4_emit_res = emit_event(
            act4_event,
            act4_bytes,
            rt.emitters,
            dda_step=DdaStepV1(
                letter=letter,
                before_class="CandidateProposed",
                after_class="CarrierExpanded" if gauge_break_triggered else "CandidateProposed",
                carrier_hash=_digest(b"lifted_carrier" if gauge_break_triggered else b"carrier"),
                witness_hash=_digest(json.dumps(asd_telemetry, sort_keys=True)),
                receipt_sha256=_digest(act4_bytes),
                timestamp=_timestamp(now_utc),
            ),
        )
        if act4_emit_res.is_err:
            return Err(act4_emit_res.unwrap_err())

    return Ok(
        (
            gauge_break_triggered,
            lifted_network,
            updated_cochain,
            asd_telemetry,
            narrative,
        )
    )


#: A challenge statement is a bounded summary. The full counterexample text is
#: kept, unabridged, in the critique record and the raw reply bytes.
STATEMENT_EXCERPT_CHARS = 1024


def _bounded(text: str) -> str:
    """The text itself when short, else a digest-labelled excerpt of it."""
    if (
        len(text) <= STATEMENT_EXCERPT_CHARS
        and len(text.encode("utf-8")) <= 4 * STATEMENT_EXCERPT_CHARS
    ):
        return text
    excerpt = text[:STATEMENT_EXCERPT_CHARS].rstrip()
    return (
        f"[{len(text.encode('utf-8'))} bytes, {_digest(text)}; excerpt follows, "
        f"full text in the critique record] {excerpt}"
    )


def execute_act5_independent_witness(
    rt: SwarmRuntimeV1,
    run_key: str,
    objective: str,
    carrier_network: Network | None = None,
    candidates: Sequence[CandidateProposalV1] = (),
    dead_candidates: Sequence[CemeteryHeadstoneV1] = (),
    candidate_payloads: Mapping[str, bytes] | None = None,
    *,
    ablation_flags: Mapping[str, bool] | None = None,
    now_utc: str = "",
    native_support: NativeOperationPort,
) -> Result[
    tuple[
        list[CandidateProposalV1],
        list[CemeteryHeadstoneV1],
        int,
        list[ChallengeV1],
        list[dict[str, Any]],
        dict[str, str],
        dict[str, Any],
    ],
    Refusal,
]:
    """Act V: Independent Witness Evaluation — typed critiques and countermodel search.

    The sixth element of the returned tuple maps each critiqued candidate id to
    ``BLOCKING``, ``NON_BLOCKING`` or ``MALFORMED`` (its latest critique).
    """
    del carrier_network
    surviving_candidates = list(candidates)
    accumulated_dead = list(dead_candidates)
    critiques: list[ChallengeV1] = []
    critiques_data: list[dict[str, Any]] = []
    critique_verdicts: dict[str, str] = {}
    round_count = 0

    no_independent = bool(ablation_flags and ablation_flags.get("no_independent_witness"))
    critic_seat_id = "seat_gauge_breaker" if no_independent else "seat_defect_hunter"

    while round_count < rt.max_critique_rounds and surviving_candidates:
        round_count += 1
        killed_in_round = False
        for cand in list(surviving_candidates):
            payload = (candidate_payloads or {}).get(cand.candidate_id)
            if type(payload) is not bytes:
                return _refuse(
                    "ADVERSARY_CANDIDATE_PAYLOAD_MISSING",
                    "A critique requires the exact candidate content bytes",
                )
            if _digest(payload) not in cand.artifact_refs:
                return _refuse(
                    "ADVERSARY_CANDIDATE_PAYLOAD_MISMATCH",
                    "Critique content does not match the candidate artifact digest",
                )
            turn_req = SeatTurnRequestV1(
                scene_id="act2_panel_debate",
                seat_id=critic_seat_id,
                prompt_text=(
                    f"Adversarially critique candidate {cand.candidate_id} for objective: "
                    f"'{objective}'. Identify boundary defects, unhandled overflow, and "
                    f"missing type bounds. {CRITIQUE_REPLY_CONTRACT}"
                ),
                cognitive_operator="Lefschetz Fibration & Destructive Adversarial Dialectic (E_adversary)",
                candidate_id=cand.candidate_id,
                round_index=round_count,
                context_bytes=payload,
            )
            turn_res = _seat_turn(rt, turn_req)
            if turn_res.is_err:
                return Err(turn_res.unwrap_err())
            reply = turn_res.unwrap()

            critique = parse_structured_critique(reply.reply_text, native_support=native_support)
            if critique.status is CritiqueStatus.MALFORMED:
                verdict = "MALFORMED"
                statement = f"MALFORMED_CRITIQUE: {critique.parse_error}"
            elif critique.blocking:
                verdict = "BLOCKING"
                statement = "Counterexample: " + _bounded(critique.counterexample)
            else:
                verdict = "NON_BLOCKING"
                statement = (
                    "Non-blocking critique: " + _bounded(critique.counterexample)
                    if critique.counterexample
                    else "Non-blocking critique without a counterexample."
                )
            critique_verdicts[cand.candidate_id] = verdict

            chal_evidence_ref = _digest(reply.raw_bytes)
            challenge = ChallengeV1(
                candidate_id=cand.candidate_id,
                critic_agent_id=critic_seat_id,
                trust_domain="LefschetzDialectic",
                challenge_kind=critique.challenge_kind,
                statement=statement,
                evidence_refs=(chal_evidence_ref,),
                blocking=critique.blocking,
                authority_effect=AUTHORITY_EFFECT_NONE,
            )
            critiques.append(challenge)
            critiques_data.append(
                {
                    "candidate_id": cand.candidate_id,
                    "candidate_content_sha256": _digest(payload),
                    "machine_fields": dict(reply.machine_fields),
                    "residual_colour": reply.residual_colour,
                    "reported_authority_effect": reply.authority_effect,
                    "authority_effect": AUTHORITY_EFFECT_NONE,
                    "body": reply.reply_text,
                    "raw_reply_sha256": _digest(reply.raw_bytes),
                    "raw_reply_hex": reply.raw_bytes.hex(),
                    **_reply_provenance(reply),
                    "critique": critique.to_dict(),
                    "critique_verdict": verdict,
                    "verification_status": "NOT_RUN",
                    "challenge": challenge.to_dict(),
                }
            )

            if challenge.blocking and reply.machine_fields.get("DISPOSITION") == "KILL":
                critic_name = critic_seat_id.removeprefix("seat_").upper()
                headstone = CemeteryHeadstoneV1(
                    candidate_id=cand.candidate_id,
                    run_key=run_key,
                    scene_id="act2_panel_debate",
                    cause_of_death=f"KILLED_BY_{critic_name}: {statement}",
                    killing_seat_id=critic_seat_id,
                    evidence_refs=challenge.evidence_refs,
                    candidate_payload_sha256=_digest(payload),
                    round_index=round_count,
                )
                accumulated_dead.append(headstone)
                if rt.emitters and rt.emitters.cemetery:
                    cemetery_res = rt.emitters.cemetery.record_headstone(headstone)
                    if cemetery_res.is_err:
                        return Err(cemetery_res.unwrap_err())
                surviving_candidates.remove(cand)
                killed_in_round = True
                break

        if not killed_in_round:
            break

    witness_body = (
        f"Conducted {round_count} critique round(s) via {critic_seat_id}. "
        f"{len(surviving_candidates)} surviving candidate(s); "
        f"{sum(1 for v in critique_verdicts.values() if v == 'MALFORMED')} malformed critique(s) block their candidates."
    )
    if no_independent:
        witness_body += " Independent witness ablated: proposer self-evaluated candidates."
    narrative = {
        "act_number": "V",
        "title": "Independent Witness Evaluation",
        "body": witness_body,
    }

    if rt.emitters:
        act5_event, act5_bytes = build_intelligence_event(
            ie_id=_digest(f"{run_key}:act5"),
            actor_id="actor_aletheia_second_curator",
            actor_kind="SWARM_SEAT",
            event_kind="COMM",
            source_system="oeas.act5",
            session_id=run_key,
            payload={
                "act": "V",
                "title": "Independent Witness Evaluation",
                "surviving_count": len(surviving_candidates),
                "critiques_count": len(critiques),
                "critique_verdicts": dict(critique_verdicts),
            },
        )
        act5_emit_res = emit_event(
            act5_event,
            act5_bytes,
            rt.emitters,
            dda_step=DdaStepV1(
                letter=DdaLetter.D,
                before_class="CarrierExpanded",
                after_class="CandidatesWitnessed",
                carrier_hash=_digest(b"carrier"),
                witness_hash=_digest(str([c.candidate_id for c in surviving_candidates])),
                receipt_sha256=_digest(act5_bytes),
                timestamp=_timestamp(now_utc),
            ),
        )
        if act5_emit_res.is_err:
            return Err(act5_emit_res.unwrap_err())

    return Ok(
        (
            surviving_candidates,
            accumulated_dead,
            round_count,
            critiques,
            critiques_data,
            critique_verdicts,
            narrative,
        )
    )


def execute_candidate_checks(
    checker: CandidateCheckerPort | None,
    run_key: str,
    objective: str,
    candidates: Sequence[CandidateProposalV1],
    candidate_payloads: Mapping[str, bytes],
    carrier_context: Mapping[str, Any] | None,
    *,
    rt: SwarmRuntimeV1 | None = None,
    measurement: ObstructionMeasurementV1 | None = None,
    carrier_state_hash: str | None = None,
    now_utc: str = "",
) -> Result[dict[str, CandidateCheckV1], Refusal]:
    """Ask the challenge checker for a typed verdict on each surviving candidate.

    Every returned check must name the candidate and its exact content digest;
    a check about other bytes is a refusal, not evidence.
    """
    port = checker or NullCandidateCheckerAdapter()
    checks: dict[str, CandidateCheckV1] = {}
    for candidate in candidates:
        payload = candidate_payloads.get(candidate.candidate_id)
        if type(payload) is not bytes:
            return _refuse(
                "ADVERSARY_CANDIDATE_PAYLOAD_MISSING",
                "A checker verdict requires the exact candidate content bytes",
            )
        result = port.check_candidate(
            run_key=run_key,
            objective=objective,
            candidate_id=candidate.candidate_id,
            candidate_bytes=payload,
            carrier_context=carrier_context,
        )
        if result.is_err:
            return Err(result.unwrap_err())
        check = result.unwrap()
        if type(check) is not CandidateCheckV1:
            return _refuse(
                "ADVERSARY_CHECKER_CONTRACT_VIOLATION",
                "the candidate checker must return an exact CandidateCheckV1",
            )
        if not check.binds(candidate.candidate_id, candidate.artifact_refs):
            return _refuse(
                "ADVERSARY_CHECKER_BINDING_MISMATCH",
                "the checker verdict names a different candidate or different content bytes",
            )
        checks[candidate.candidate_id] = check
        if rt is not None and rt.emitters:
            if carrier_state_hash is None:
                return _refuse(
                    "ADVERSARY_DDC_CARRIER_REQUIRED",
                    "checker emission requires the measured active carrier digest",
                )
            # R audits a checker result. Acceptance alone is never an E repair.
            payload_record = check.to_dict()
            check_digest = _canonical_json_digest(payload_record)
            event, event_bytes = build_intelligence_event(
                ie_id=check_digest,
                # Council audit accountability only; checker_id and its receipt
                # identify machine verification. This persona grants no authority.
                actor_id="actor_aletheia_procurator",
                actor_kind="SWARM_SEAT",
                event_kind="COMM",
                source_system="oeas.candidate_check",
                session_id=run_key,
                payload=payload_record,
            )
            emitted = emit_event(
                event,
                event_bytes,
                rt.emitters,
                dda_step=DdaStepV1(
                    letter=DdaLetter.R,
                    before_class="CandidateProposed",
                    after_class=f"Checker_{check.verdict.value}",
                    carrier_hash=carrier_state_hash,
                    witness_hash=check.checker_receipt_sha256 or check_digest,
                    receipt_sha256=check_digest,
                    timestamp=_timestamp(now_utc),
                    phi_1=measurement.phi1 if measurement and measurement.is_measured else None,
                    gamma_2=measurement.gamma2 if measurement and measurement.is_measured else None,
                ),
            )
            if emitted.is_err:
                return Err(emitted.unwrap_err())
    return Ok(checks)


def execute_act6_residual_ledger(
    rt: SwarmRuntimeV1,
    surviving_candidates: Sequence[CandidateProposalV1],
    dead_candidates: Sequence[CemeteryHeadstoneV1],
    critiques: Sequence[ChallengeV1],
    critique_verdicts: Mapping[str, str],
    measurement: ObstructionMeasurementV1,
    *,
    ablation_flags: Mapping[str, bool] | None = None,
    run_key: str = "",
    now_utc: str = "",
) -> Result[tuple[dict[str, Any], int, dict[str, Any]], Refusal]:
    """Act VI: Residual Ledger Declaration — typed residual ledger, compost antibodies, I step."""
    del surviving_candidates
    antibodies_recorded = 0
    if dead_candidates and rt.emitters and rt.emitters.antibodies:
        for dead in dead_candidates:
            antibody_res = rt.emitters.antibodies.record_failure(
                failure_pattern=dead.cause_of_death,
                constraint_rule=f"Disallow pattern causing {dead.cause_of_death}",
            )
            if antibody_res.is_err:
                return Err(antibody_res.unwrap_err())
            antibodies_recorded += 1

    if ablation_flags and ablation_flags.get("no_residual_ledger"):
        residual_ledger: dict[str, Any] = {}
    else:
        if measurement.is_exact_joint_zero():
            status = "CLEARED"
        elif measurement.is_measured:
            status = "BOUNDED_RESIDUAL"
        else:
            status = "NOT_MEASURED"
        residual_ledger = {
            "unresolved_challenges": [c.challenge_id for c in critiques if not c.blocking],
            "blocking_challenges": [c.challenge_id for c in critiques if c.blocking],
            "malformed_critiques": sorted(
                cid for cid, verdict in critique_verdicts.items() if verdict == "MALFORMED"
            ),
            "carrier_measurement": measurement.to_dict(),
            "status": status,
            "residual_declared": True,
        }

    narrative = {
        "act_number": "VI",
        "title": "Residual Ledger Declaration",
        "body": (
            f"Residual ledger status: {residual_ledger.get('status', 'ABLATED')}. "
            f"Accumulated {antibodies_recorded} antibody update(s)."
        ),
    }

    if rt.emitters:
        act6_event, act6_bytes = build_intelligence_event(
            ie_id=_digest(f"{run_key}:act6"),
            actor_id="actor_logos_secretary",
            actor_kind="SWARM_SEAT",
            event_kind="COMM",
            source_system="oeas.act6",
            session_id=run_key,
            payload={
                "act": "VI",
                "title": "Residual Ledger Declaration",
                "antibodies_recorded": antibodies_recorded,
            },
        )
        act6_emit_res = emit_event(
            act6_event,
            act6_bytes,
            rt.emitters,
            dda_step=DdaStepV1(
                letter=DdaLetter.I,
                before_class="CandidatesWitnessed",
                after_class="LedgerIntegrated",
                carrier_hash=_digest(b"carrier"),
                witness_hash=_digest(json.dumps(residual_ledger, sort_keys=True)),
                receipt_sha256=_digest(act6_bytes),
                timestamp=_timestamp(now_utc),
            ),
        )
        if act6_emit_res.is_err:
            return Err(act6_emit_res.unwrap_err())

    return Ok((residual_ledger, antibodies_recorded, narrative))


def _exact_regge_open(value: Any) -> bool:
    """True unless a Regge defect is absent (``None``) or exactly zero.

    A value that is not exact -- a float, NaN, a bool, unparsable text -- is
    treated as open: an unmeasurable deficit is not a closed one.
    """
    if value is None:
        return False
    try:
        return parse_exact_rational(value) != 0
    except (TypeError, ValueError):
        return True


def _regge_text(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return canonical_rational(parse_exact_rational(value))
    except (TypeError, ValueError):
        return f"INEXACT:{value!r}"


def execute_act7_authorization_gate(
    rt: SwarmRuntimeV1 | None,
    run_key: str,
    surviving_candidates: Sequence[CandidateProposalV1],
    critiques: Sequence[ChallengeV1],
    residual_ledger: Mapping[str, Any],
    measurement: ObstructionMeasurementV1,
    *,
    candidate_checks: Mapping[str, CandidateCheckV1] | None = None,
    carrier_context: Mapping[str, Any] | None = None,
    ablation_flags: Mapping[str, bool] | None = None,
    delta2_defect: Any | None = None,
    delta3_defect: Any | None = None,
    regge_converged: bool | None = None,
    carrier_status: str = CARRIER_DECLARED,
    critique_verdicts: Mapping[str, str] | None = None,
    fixture_seats: bool = True,
    now_utc: str = "",
) -> Result[
    tuple[str, str, CandidateSelectionProposalV1, bool, dict[str, Any]],
    Refusal,
]:
    """Act VII: Terminal Authorization Gate.

    ``AUTHORIZED`` always requires an eligible candidate (no blocking or
    malformed critique, no REJECTED checker verdict), an ``ACCEPTED`` checker
    verdict bound to that candidate's content digest and to the checker
    receipt digest, and no protected mutation, refuted zero claim, or open
    Regge deficit. Then, by ``carrier_status``:

    * ``DECLARED`` -- the carrier must also be an exact joint zero
      (``Phi1 == 0 and Gamma2 == 0`` as ``Fraction`` behind a verified
      certificate). Evidence path ``CHECKER_VERDICT_AND_EXACT_ZERO_CARRIER``.
    * ``NOT_DECLARED`` -- the bout declared no carrier at all (many Symbol
      Game answers have no cochain), so the bound checker receipt is the
      evidence. Evidence path ``CHECKER_VERDICT_ONLY_NO_CARRIER_DECLARED``.

    A missing or malformed carrier never reaches this act: Act I refuses it.
    The default is ``DECLARED``, the stricter path. Ablation flags never
    authorize: an ablated gate reports ``ABLATED_WOULD_AUTHORIZE`` at most.

    The selected candidate must also have been critiqued, with its latest
    critique ``NON_BLOCKING`` in ``critique_verdicts`` (a KILL ends a critique
    round early, so a candidate can survive uncritiqued). When no verdicts are
    supplied, no candidate counts as critiqued.

    Seats count as canned (``fixture_seats``) unless the caller passes exactly
    ``fixture_seats=False``, as the bout does for live seats; an otherwise
    authorizable gate over canned seats reports ``FIXTURE_ONLY``, because
    canned replies never authorize.
    """
    if type(measurement) is not ObstructionMeasurementV1:
        return _refuse(
            "ADVERSARY_SCORER_CONTRACT_VIOLATION",
            "Act VII requires an exact ObstructionMeasurementV1",
        )
    if carrier_status not in CARRIER_STATUSES or (
        carrier_status == CARRIER_NOT_DECLARED and measurement.is_measured
    ):
        return _refuse(
            "ADVERSARY_CARRIER_STATUS_INVALID",
            "carrier_status must be DECLARED or NOT_DECLARED, and an undeclared "
            "carrier cannot carry a measurement",
        )
    carrier_required = carrier_status == CARRIER_DECLARED
    checks = dict(candidate_checks or {})
    for candidate_id, check in checks.items():
        if type(check) is not CandidateCheckV1 or check.candidate_id != candidate_id:
            return _refuse(
                "ADVERSARY_CHECKER_CONTRACT_VIOLATION",
                "candidate checks must be exact CandidateCheckV1 values keyed by candidate id",
            )

    rejected_ids = {
        cid for cid, check in checks.items() if check.verdict is CheckerVerdict.REJECTED
    }
    blocked_candidate_ids = {c.candidate_id for c in critiques if c.blocking} | rejected_ids
    selected_candidate = next(
        (c for c in surviving_candidates if c.candidate_id not in blocked_candidate_ids),
        None,
    )
    selected_cand = selected_candidate.candidate_id if selected_candidate else ""
    check = checks.get(selected_cand) if selected_cand else None
    checker_bound = bool(
        check is not None
        and selected_candidate is not None
        and check.binds(selected_cand, selected_candidate.artifact_refs)
    )
    checker_accepted = bool(checker_bound and check is not None and check.can_authorize)
    verdicts = dict(critique_verdicts or {})
    critiqued = bool(selected_cand) and verdicts.get(selected_cand) == "NON_BLOCKING"
    # Fail closed: only an exact False declares live (non-fixture) seats.
    fixture_seats = fixture_seats is not False

    no_auth = bool(ablation_flags and ablation_flags.get("no_authorization_boundary"))
    no_wit = bool(ablation_flags and ablation_flags.get("no_independent_witness"))
    no_res = bool(ablation_flags and ablation_flags.get("no_residual_ledger"))

    has_protected_mutation = bool(
        carrier_context
        and (
            carrier_context.get("protected_edges")
            or carrier_context.get("protected_boundaries")
            or carrier_context.get("trap_type") == "irreversible_mutation"
        )
    )
    has_adversarial_zero_claim = bool(
        carrier_context
        and (
            carrier_context.get("adversarial_zero_claim")
            or carrier_context.get("zero_claim")
            or carrier_context.get("claims_zero_defect")
        )
    )

    evidence_receipts: dict[str, dict[str, Any]] = {}
    obstruction_receipt: dict[str, Any] | None = None
    if measurement.is_measured and measurement.phi1 is not None and measurement.phi1 > 0:
        obstruction_receipt = {
            "receipt_type": "OBSTRUCTION_NON_VANISHING_RECEIPT",
            "run_key": run_key,
            "backend": measurement.backend,
            "certificate_verified": measurement.certificate_verified,
            "dual_witness": [[edge, canonical_rational(v)] for edge, v in measurement.dual_witness],
            "phi1": measurement.phi1_text(),
            "gamma2": measurement.gamma2_text(),
            "adversarial_zero_claim_refuted": has_adversarial_zero_claim,
        }
        evidence_receipts[_canonical_json_digest(obstruction_receipt)] = obstruction_receipt

    delta2_open = _exact_regge_open(delta2_defect)
    delta3_open = _exact_regge_open(delta3_defect)
    has_regge_deficit = delta2_open or delta3_open
    regge_receipt: dict[str, Any] | None = None
    if has_regge_deficit:
        regge_receipt = {
            "receipt_type": "REGGE_SPACETIME_DEFICIT_RECEIPT",
            "run_key": run_key,
            "delta2_defect": _regge_text(delta2_defect),
            "delta3_defect": _regge_text(delta3_defect),
            "bianchi_closure": not delta2_open,
            "spacetime_closure": not delta3_open,
            "regge_converged": regge_converged is True,
            "adversarial_zero_claim_refuted": has_adversarial_zero_claim,
        }
        evidence_receipts[_canonical_json_digest(regge_receipt)] = regge_receipt

    blockers: list[str] = []
    if not selected_cand:
        blockers.append("NO_ELIGIBLE_CANDIDATE")
    if carrier_required and not measurement.is_measured:
        blockers.append("CARRIER_NOT_MEASURED")
    elif carrier_required and not measurement.is_exact_joint_zero():
        blockers.append("OPEN_OBSTRUCTION")
    if has_regge_deficit:
        blockers.append("REGGE_DEFICIT_OPEN")
    if selected_cand:
        if check is None:
            blockers.append("CHECKER_NOT_RUN")
        elif not checker_bound:
            blockers.append("CHECKER_UNBOUND")
        elif not checker_accepted:
            blockers.append(f"CHECKER_{check.verdict.value}")
        if not critiqued:
            blockers.append("CANDIDATE_NOT_CRITIQUED_NON_BLOCKING")
    if fixture_seats:
        blockers.append("FIXTURE_SEATS")
    if has_protected_mutation:
        blockers.append("PROTECTED_MUTATION")
    if has_adversarial_zero_claim and (obstruction_receipt or regge_receipt):
        blockers.append("ADVERSARIAL_ZERO_CLAIM_REFUTED")

    if has_protected_mutation and not no_auth:
        status, disposition = "REFUSED", "HOLD"
    elif has_adversarial_zero_claim and (obstruction_receipt or regge_receipt) and not no_auth:
        status, disposition = "REFUSED", "HOLD"
    elif not selected_cand:
        status, disposition = "REFUSED", "HOLD"
    elif no_auth or no_wit:
        # An ablated gate is an experiment arm. It may report what the gate
        # would have let through, but only an ACCEPTED, bound checker verdict
        # counts even then, and nothing is authorized.
        if checker_accepted and critiqued:
            status, disposition = "ABLATED_WOULD_AUTHORIZE", "SELECT"
        else:
            status, disposition = "REFUSED", "HOLD"
    elif carrier_required and not measurement.is_measured:
        status, disposition = "NOT_MEASURED", "SELECT"
    elif measurement.has_open_obstruction() or has_regge_deficit:
        if no_res:
            status, disposition = "REFUSED", "HOLD"
        else:
            status, disposition = "BOUNDED_RESIDUAL", "SELECT"
    elif checker_accepted and critiqued and fixture_seats:
        status, disposition = "FIXTURE_ONLY", "SELECT"
    elif checker_accepted and critiqued:
        status, disposition = "AUTHORIZED", "SELECT"
    else:
        status, disposition = "NOT_MEASURED", "SELECT"

    is_authorized = status == "AUTHORIZED"
    authorization_evidence: str | None = None
    if is_authorized:
        authorization_evidence = (
            EVIDENCE_CHECKER_AND_CARRIER if carrier_required else EVIDENCE_CHECKER_ONLY
        )
    if disposition == "HOLD":
        selected_cand = ""

    epoch_id = _digest(run_key)
    evidence_refs = list(dict.fromkeys(c.challenge_id for c in critiques))
    if check is not None and check.checker_receipt_sha256 is not None:
        evidence_refs.append(check.checker_receipt_sha256)
    evidence_refs.extend(evidence_receipts)
    evidence_refs = list(dict.fromkeys(evidence_refs)) or [epoch_id]

    verdict_proposal = CandidateSelectionProposalV1(
        selector_agent_id="agent_manuscript_truth",
        evaluator_epoch_id=epoch_id,
        frontier_candidate_ids=tuple(c.candidate_id for c in surviving_candidates),
        selected_candidate_id=selected_cand,
        disposition=disposition,
        evidence_refs=tuple(evidence_refs),
        nonclaims=(
            "Selection is a candidate proposal only.",
            "AuthorityEffect is strictly None.",
        ),
        authority_effect=AUTHORITY_EFFECT_NONE,
    )

    body_msg = (
        f"Manuscript Truth rendered decision: status={status}, is_authorized={is_authorized} "
        f"(selected: {selected_cand or 'none'}; carrier {carrier_status}; "
        f"evidence path: {authorization_evidence or 'none'}). "
        f"Blockers: {', '.join(blockers) or 'none'}."
    )
    if obstruction_receipt is not None and has_adversarial_zero_claim:
        body_msg += f" Refuted adversarial zero-claim via exact dual witness: Phi1={obstruction_receipt['phi1']} > 0."
    if regge_receipt is not None and has_adversarial_zero_claim:
        body_msg += (
            " Refuted adversarial zero-claim via Regge deficit: "
            f"delta2={regge_receipt['delta2_defect']}, delta3={regge_receipt['delta3_defect']}."
        )

    narrative: dict[str, Any] = {
        "act_number": "VII",
        "title": "Terminal Authorization Gate",
        "body": body_msg,
        "authorization_blockers": blockers,
        "authorization_evidence": authorization_evidence,
        "carrier_status": carrier_status,
        "checker_verdict": check.verdict.value if check is not None else "NOT_MEASURED",
        "checker_receipt_sha256": check.checker_receipt_sha256 if check is not None else None,
        "evidence_receipts": evidence_receipts,
    }
    if obstruction_receipt is not None:
        narrative["obstruction_non_vanishing_receipt"] = obstruction_receipt
    if regge_receipt is not None:
        narrative["regge_spacetime_deficit_receipt"] = regge_receipt

    if rt is not None and rt.emitters:
        terminal = status in (
            "AUTHORIZED",
            "BOUNDED_RESIDUAL",
            "NOT_MEASURED",
            "FIXTURE_ONLY",
            "ABLATED_WOULD_AUTHORIZE",
        )
        act7_event, act7_bytes = build_intelligence_event(
            ie_id=_digest(f"{run_key}:act7"),
            actor_id="actor_nous_procurator",
            actor_kind="SWARM_AGENT",
            event_kind="TERMINAL" if terminal else "REFUSAL",
            source_system="oeas.act7",
            session_id=run_key,
            payload={
                "act": "VII",
                "title": "Terminal Authorization Gate",
                "status": status,
                "is_authorized": is_authorized,
                "authorization_blockers": blockers,
            },
        )
        act7_emit_res = emit_event(
            act7_event,
            act7_bytes,
            rt.emitters,
            dda_step=DdaStepV1(
                letter=DdaLetter.T if terminal else DdaLetter.M,
                before_class="LedgerIntegrated",
                after_class="TerminalVerdict",
                carrier_hash=_digest(b"carrier"),
                witness_hash=_digest(verdict_proposal.selected_candidate_id or status),
                receipt_sha256=_digest(act7_bytes),
                timestamp=_timestamp(now_utc),
            ),
        )
        if act7_emit_res.is_err:
            return Err(act7_emit_res.unwrap_err())

    return Ok((status, selected_cand, verdict_proposal, is_authorized, narrative))


def execute_act3_epistemic_sieve(
    objective: str,
    candidates: Sequence[CandidateProposalV1],
    candidates_data: Sequence[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Act III: Epistemic Sieve — Calculates synthetic SBE purity trajectory."""
    sieve_disposition = "PASS" if candidates else "HOLD"
    survivor_ids = {c.candidate_id for c in candidates}
    surviving_data = [item for item in candidates_data if item["candidate_id"] in survivor_ids]
    selected_code = surviving_data[0]["content"] if surviving_data else ""
    sieve_sbe = compute_sbe_metrics(objective + " " + selected_code, dim=28)

    narrative = {
        "act_number": "III",
        "title": "Epistemic Sieve",
        "body": (
            f"Adversary Epistemic Sieve recorded disposition: {sieve_disposition}. "
            "SBE values are deterministic synthetic diagnostics, not verification."
        ),
    }
    return sieve_sbe, narrative


def execute_act4_sandbox_verification(
    rt: SwarmRuntimeV1,
    candidates: Sequence[CandidateProposalV1] = (),
    candidate_payloads: Mapping[str, bytes] | None = None,
    *,
    cemetery: Any | None = None,
    antibody_store: Any | None = None,
    repo_root: Path | str | None = None,
    ablation_flags: Mapping[str, bool] | None = None,
    admitted_antibody_reader: AdmittedAntibodyReader | None = None,
) -> Result[tuple[str, dict[str, Any]], Refusal]:
    """Act IV: Sandbox — Primal Dual seat execution after the cemetery screen."""
    screened = screen_known_regressions(
        rt,
        candidates,
        candidate_payloads,
        cemetery=cemetery,
        antibody_store=antibody_store,
        repo_root=repo_root,
        ablation_flags=ablation_flags,
        admitted_antibody_reader=admitted_antibody_reader,
    )
    if screened.is_err:
        return Err(screened.unwrap_err())

    # Proceed to Primal Dual sandbox seat turn if no cemetery regression or antibody match
    sandbox_turn = SeatTurnRequestV1(
        scene_id="act4_sandbox",
        seat_id="seat_primal_dual",
        prompt_text="Execute orthogonal safety, non-termination, and security audit on candidate artifacts.",
        cognitive_operator="Placebo & Hopeful Generative Envelope (E_placebo)",
    )
    sandbox_res = _seat_turn(rt, sandbox_turn)
    if sandbox_res.is_err:
        return Err(sandbox_res.unwrap_err())
    sandbox_reply = sandbox_res.unwrap()
    sandbox_disposition = str(sandbox_reply.machine_fields.get("DISPOSITION", "UNATTESTED")).upper()

    narrative = {
        "act_number": "IV",
        "title": "Sandbox",
        "body": (
            f"Primal Dual seat reported `{sandbox_disposition}`: "
            f"{sandbox_reply.reply_text[:120]}. This is not an independent safety verification."
        ),
    }
    return Ok((sandbox_disposition, narrative))


def execute_act5_terminal_verdict(
    rt: SwarmRuntimeV1,
    run_key: str,
    candidates: Sequence[CandidateProposalV1],
    critiques: Sequence[ChallengeV1],
) -> tuple[str, str, CandidateSelectionProposalV1, dict[str, Any]]:
    """Act V: Propose the first candidate without an applicable blocking challenge.

    The critique seat's optional KILL disposition controls cemetery recording,
    not selection eligibility. Blocking challenges remain effective for their
    exact candidate ID even if a later critique is nonblocking. The complete
    frontier and challenge references remain in the proposal for replay.
    """
    blocked_candidate_ids = {
        challenge.candidate_id for challenge in critiques if challenge.blocking
    }
    selected_cand = next(
        (
            candidate.candidate_id
            for candidate in candidates
            if candidate.candidate_id not in blocked_candidate_ids
        ),
        "",
    )
    if selected_cand:
        terminal_verdict = (
            "PROPOSED_FOR_EXTERNAL_ADMISSION" if rt.request_external_admission else "COMPOSTED"
        )
        disposition = "SELECT"
    else:
        terminal_verdict = "COMPOSTED"
        disposition = "HOLD"

    epoch_id = _digest(run_key)
    selected_digest = selected_cand if selected_cand else ""
    frontier_digests = tuple(c.candidate_id for c in candidates)

    verdict_proposal = CandidateSelectionProposalV1(
        selector_agent_id="agent_manuscript_truth",
        evaluator_epoch_id=epoch_id,
        frontier_candidate_ids=frontier_digests,
        selected_candidate_id=selected_digest,
        disposition=disposition,
        evidence_refs=tuple(dict.fromkeys(c.challenge_id for c in critiques)) or (epoch_id,),
        nonclaims=(
            "Selection is a candidate proposal only.",
            "AuthorityEffect is strictly None.",
        ),
        authority_effect=AUTHORITY_EFFECT_NONE,
    )

    narrative = {
        "act_number": "V",
        "title": "Terminal Verdict",
        "body": f"Manuscript Truth rendered terminal verdict: `{terminal_verdict}` (selected candidate: {selected_cand or 'none'}).",
    }
    return terminal_verdict, selected_cand, verdict_proposal, narrative


def execute_act6_intern_report(
    rt: SwarmRuntimeV1,
    dead_candidates: Sequence[CemeteryHeadstoneV1],
) -> Result[tuple[int, dict[str, Any]], Refusal]:
    """Act VI: Intern's Report — Integrity audit and antibody accumulation."""
    antibodies_recorded = 0
    if dead_candidates and rt.emitters and rt.emitters.antibodies:
        for dead in dead_candidates:
            antibody_res = rt.emitters.antibodies.record_failure(
                failure_pattern=dead.cause_of_death,
                constraint_rule=f"Disallow pattern causing {dead.cause_of_death}",
            )
            if antibody_res.is_err:
                return Err(antibody_res.unwrap_err())
            antibodies_recorded += 1

    narrative = {
        "act_number": "VI",
        "title": "Intern's Report",
        "body": (
            f"Intern capture summary: {antibodies_recorded} antibody update(s) "
            "completed without a reported sink error. No independent integrity audit was run."
        ),
    }
    return Ok((antibodies_recorded, narrative))


def execute_act7_crystallization(
    rt: SwarmRuntimeV1,
    run_key: str,
    terminal_verdict: str,
    dead_candidates: Sequence[CemeteryHeadstoneV1],
) -> Result[tuple[str, dict[str, Any]], Refusal]:
    """Act VII: Crystallization / Re-entry — Backdoor Auditor seal or guided mutation genealogy."""
    consecration_state = (
        "PROPOSED_FOR_EXTERNAL_ADMISSION"
        if rt.request_external_admission and terminal_verdict == "PROPOSED_FOR_EXTERNAL_ADMISSION"
        else "COMPOSTED_WITH_REENTRY_GUIDANCE"
    )
    if terminal_verdict == "COMPOSTED" and rt.emitters and rt.emitters.genealogy:
        genealogy_entry = GenealogyEntryV1(
            parent_run_key=run_key,
            child_run_key=f"{run_key}_reentry_1",
            structural_deficiencies=tuple(
                dict.fromkeys(dead.cause_of_death for dead in dead_candidates)
            )
            or ("No viable candidate survived adversarial debate",),
            concrete_fixes=("Revise candidate typing and bound proofs",),
            next_run_guidance="Incorporate composted antibodies into Act I perception DAG.",
            re_entry_reason="COMPOST_GUIDED_MUTATION",
        )
        genealogy_res = rt.emitters.genealogy.record_lineage(genealogy_entry)
        if genealogy_res.is_err:
            return Err(genealogy_res.unwrap_err())

    narrative = {
        "act_number": "VII",
        "title": "Crystallization / Re-entry",
        "body": (
            "Backdoor Auditor completed the candidate capture. "
            f"Non-authoritative status: `{consecration_state}`. Sealed 7-Act novella."
        ),
    }
    return Ok((consecration_state, narrative))


__all__ = [
    "CARRIER_DECLARED",
    "CARRIER_KEYS",
    "CARRIER_NOT_DECLARED",
    "CARRIER_STATUSES",
    "EVIDENCE_CHECKER_AND_CARRIER",
    "EVIDENCE_CHECKER_ONLY",
    "REQUIRED_CARRIER_KEYS",
    "STAGNATION_SBE_THRESHOLD",
    "execute_act1_carrier_framing",
    "execute_act2_obstruction_identification",
    "execute_act3_candidate_proposal_generation",
    "execute_act3_epistemic_sieve",
    "execute_act4_gauge_break",
    "execute_act4_sandbox_verification",
    "execute_act5_independent_witness",
    "execute_act5_terminal_verdict",
    "execute_act6_intern_report",
    "execute_act6_residual_ledger",
    "execute_act7_authorization_gate",
    "execute_act7_crystallization",
    "execute_candidate_checks",
]
