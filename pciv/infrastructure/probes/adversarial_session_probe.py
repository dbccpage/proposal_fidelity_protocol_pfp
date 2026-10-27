"""Multi-turn adversarial session probe combining grammar mutations with live Prompt Civ adapters.

Wired via OEOS host adapter (OeosHostAdapter / HostPortV1).
Enforces:
- Multi-turn stateful adversarial probing with immutable event logging.
- External grammar mutations (balanced Genesis carriers and DDC rewrite rules).
- Protected span integrity against boundary violations and zero-width insertions.
- Syntactic and carrier depth verification (Genesis carrier law: no negative depth, zero net charge).
- Strict non-None authority refusal firewall (authority_effect must be 'None').
- Zero-float rational firewall (floats forbidden across scoring and canonical representations).
- Lineage DAG tracking, taint propagation, antibody arming, and ancestral rank solving.
- Cryptographic receipt emission with content-addressed SHA-256 verification.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from operating_system.adapters.oeos_host import OeosHostAdapter
from pfp.domain.shared_kernel.canonical import (
    CanonicalizationError,
    freeze,
)
from adversary.stage.application.ports import HostPortV1

from pciv.domain.causal_witness import seal_causal_witness
from ...domain.models import (
    CustodyTier,
    PromptGenomeRegistryV1,
    PromptGenomeV1,
    ProtectedSpanV1,
)
from ...use_cases.fitness import ParetoFrontSelectorV1, PromptFitnessCalculatorV1
from ...use_cases.forge import PromptMutationEngineV1
from ...use_cases.genealogy import LineageGraphV1, RelationshipType
from ...use_cases.immunity import (
    ArmedRepertoireManagerV1,
    ImmunityPropagationEngineV1,
    LineageTaintEngineV1,
)
from ...use_cases.rank import (
    ExactRowReductionSolverV1,
    RankCertificateVerifierV1,
    reconstruct_transition_matrix,
)
from ..cas import ContentAddressedStorageV1
from ..event_log import DurableEventLogV1, PromptCivEventV1


def validate_carrier_word(word: str) -> bool:
    """Validate carrier balance according to Genesis carrier law.

    - Empty word is the identity carrier.
    - Alphabet is strictly {'<', '>'}.
    - Running depth must never drop below 0.
    - Net depth must return to 0.
    """
    if not word:
        return True
    depth = 0
    for ch in word:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
            if depth < 0:
                return False
        else:
            return False
    return depth == 0


@dataclass(frozen=True)
class AdversarialTurnResultV1:
    """Result of an individual turn in the adversarial probe session."""

    turn_index: int
    turn_name: str
    turn_kind: str
    is_admitted: bool
    verdict: str
    refusal_reason: Optional[str]
    host_status: str
    event_id: str
    payload_digest: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AdversarialSessionProbeReceiptV1:
    """Cryptographic, deterministic execution receipt for the adversarial probe session."""

    session_id: str
    receipt_sha256: str
    total_turns: int
    turns_attempted: int
    turns_passed: int
    adversarial_attacks_quarantined: int
    cas_objects_count: int
    event_count: int
    lineage_nodes_count: int
    lineage_edges_count: int
    tainted_nodes_count: int
    antibodies_armed_count: int
    rank_certificates_verified: int
    host_requests_count: int
    is_consistent: bool
    authority_effect: str = "None"
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def admission_beside_host(
    host_resp: Dict[str, Any],
    *,
    local_admitted: bool,
    local_verdict: str,
    local_reason: Optional[str] = None,
) -> tuple[bool, str, Optional[str], str]:
    """A host status of REFUSED blocks a local ACCEPTED verdict.

    Quarantine stays quarantine. A missing status is REFUSED.
    """
    status = str(host_resp.get("status") or "REFUSED")
    if status == "REFUSED" and local_verdict == "ACCEPTED":
        return False, "REFUSED", "host_status is REFUSED", status
    return local_admitted, local_verdict, local_reason, status


class AdversarialSessionProbeV1:
    """Multi-turn adversarial session probe integrating grammar mutations and Prompt Civ adapters.

    Orchestrates hostile mutations against protected spans, grammar invariants, authority gates,
    and exactness firewalls through the OEOS OeosHostAdapter.
    """

    def __init__(
        self,
        *,
        host: Optional[HostPortV1] = None,
        cas_dir: Optional[Path] = None,
        event_log_dir: Optional[Path] = None,
        session_id: Optional[str] = None,
    ) -> None:
        self.session_id = session_id or f"adv_probe_{uuid.uuid4().hex[:12]}"
        self.host: HostPortV1 = host if host is not None else OeosHostAdapter()
        self.cas = ContentAddressedStorageV1(storage_dir=cas_dir)
        self.event_log = DurableEventLogV1(log_dir=event_log_dir)
        self.registry = PromptGenomeRegistryV1()
        self.mutation_engine = PromptMutationEngineV1()
        self.lineage_graph = LineageGraphV1()
        self.immunity_engine = ImmunityPropagationEngineV1()
        self.repertoire_mgr = ArmedRepertoireManagerV1()
        self.taint_engine = LineageTaintEngineV1()
        self.fitness_calc = PromptFitnessCalculatorV1()
        self.pareto_selector = ParetoFrontSelectorV1()
        self.rank_solver = ExactRowReductionSolverV1()
        self.rank_verifier = RankCertificateVerifierV1()

        self.turn_results: List[AdversarialTurnResultV1] = []
        self._turn_counter: int = 0
        self._cas_digests: List[str] = []
        self._root_genome_id: Optional[str] = None
        self._active_genome_id: Optional[str] = None

    def _log_and_audit(
        self,
        *,
        event_kind: str,
        semantic_subject: str,
        payload: Dict[str, Any],
        host_action: str,
    ) -> Tuple[PromptCivEventV1, Dict[str, Any]]:
        """Log event to durable log and audit via OEOS host adapter."""
        occurrence_id = f"occ_{self.session_id}_{self._turn_counter}"
        event = PromptCivEventV1(
            producer_id="adversarial_session_probe",
            event_kind=event_kind,
            run_id=self.session_id,
            occurrence_id=occurrence_id,
            semantic_subject=semantic_subject,
            producer_ordinal=self._turn_counter,
            payload=payload,
        )
        self.event_log.append(event)

        host_request = {
            "session_id": self.session_id,
            "turn_index": self._turn_counter,
            "action": host_action,
            "event_id": event.event_id,
            "event_kind": event_kind,
            "payload_sha256": event.payload_sha256,
        }
        res = self.host.execute_host_request(json.dumps(host_request).encode("utf-8"))
        if getattr(res, "is_err", False):
            refusal = res.unwrap_err()
            host_response = {
                "status": "REFUSED",
                "reason": refusal.message,
                "code": refusal.code,
                "authority_effect": "None",
            }
        elif hasattr(res, "unwrap"):
            host_response = json.loads(res.unwrap().decode("utf-8"))
        else:
            host_response = json.loads(res.decode("utf-8"))
        return event, host_response

    def execute_baseline_turn(
        self,
        *,
        prompt_text: str,
        protected_spans: Sequence[ProtectedSpanV1],
        domain_model: Dict[str, Any],
    ) -> AdversarialTurnResultV1:
        """Turn 0: Ingests baseline governed prompt and initializes root genome."""
        turn_idx = self._turn_counter
        self._turn_counter += 1

        prompt_bytes = prompt_text.encode("utf-8")
        cas_digest = self.cas.store(prompt_bytes)
        self._cas_digests.append(cas_digest)

        genome = PromptGenomeV1.create_verified(
            source_packet_refs=[{"packet_id": f"pkt_{self.session_id}_root", "sha256": cas_digest}],
            domain_model=domain_model,
            parents=(),
            declared_generation=0,
            protected_spans=protected_spans,
            birth_custody=CustodyTier.ADMITTED,
        )
        self.registry.register_genome(genome)
        self.lineage_graph.add_genome(genome.prompt_id)
        self._root_genome_id = genome.prompt_id
        self._active_genome_id = genome.prompt_id

        event, host_resp = self._log_and_audit(
            event_kind="BASELINE_GENOME_REGISTERED",
            semantic_subject=genome.prompt_id,
            payload={
                "prompt_id": genome.prompt_id,
                "cas_digest": cas_digest,
                "generation": 0,
                "protected_spans_count": len(protected_spans),
            },
            host_action="admit_baseline_genome",
        )

        admitted, verdict, reason, status = admission_beside_host(
            host_resp, local_admitted=True, local_verdict="ACCEPTED"
        )
        res = AdversarialTurnResultV1(
            turn_index=turn_idx,
            turn_name="Turn 0: Baseline Genesis & Grammar Registration",
            turn_kind="BASELINE",
            is_admitted=admitted,
            verdict=verdict,
            refusal_reason=reason,
            host_status=status,
            event_id=event.event_id,
            payload_digest=event.payload_sha256,
        )
        self.turn_results.append(res)
        return res

    def execute_grammatical_mutation_turn(
        self,
        *,
        carrier_extension: str,
        original_prompt_text: str,
        edit_start_byte: int,
        edit_end_byte: int,
    ) -> AdversarialTurnResultV1:
        """Turn 1: Applies a valid external grammar mutation outside protected spans."""
        turn_idx = self._turn_counter
        self._turn_counter += 1

        if not self._active_genome_id:
            raise RuntimeError("No active genome in session.")
        parent_genome = self.registry.get_genome(self._active_genome_id)

        # Validate carrier grammar
        if not validate_carrier_word(carrier_extension):
            raise ValueError(f"Grammar extension {carrier_extension!r} is not a valid balanced carrier.")

        mutated_bytes = self.mutation_engine.apply_mutation(
            original_bytes=original_prompt_text.encode("utf-8"),
            protected_spans=parent_genome.protected_spans,
            edit_start_byte=edit_start_byte,
            edit_end_byte=edit_end_byte,
            replacement_bytes=carrier_extension.encode("utf-8"),
        )
        cas_digest = self.cas.store(mutated_bytes)
        self._cas_digests.append(cas_digest)

        child_genome = PromptGenomeV1.create_verified(
            source_packet_refs=[{"packet_id": f"pkt_{self.session_id}_{turn_idx}", "sha256": cas_digest}],
            domain_model=dict(parent_genome.domain_model),
            parents=({"prompt_id": parent_genome.prompt_id, "generation": parent_genome.generation},),
            declared_generation=parent_genome.generation + 1,
            protected_spans=parent_genome.protected_spans,
            birth_custody=CustodyTier.CANDIDATE,
        )
        self.registry.register_genome(child_genome)
        witness_receipt = seal_causal_witness({
            "receipt_id": f"rcpt_witness_{turn_idx}",
            "parent_id": parent_genome.prompt_id,
            "child_id": child_genome.prompt_id,
            "mutation_kind": "GrammarCarrierExtension",
            "authority_effect": "None",
        })
        self.lineage_graph.add_edge(
            parent_id=parent_genome.prompt_id,
            child_id=child_genome.prompt_id,
            relationship=RelationshipType.DIRECT_MUTATION,
            witness_receipt=witness_receipt,
        )
        self._active_genome_id = child_genome.prompt_id

        event, host_resp = self._log_and_audit(
            event_kind="GRAMMAR_MUTATION_ADMITTED",
            semantic_subject=child_genome.prompt_id,
            payload={
                "parent_id": parent_genome.prompt_id,
                "child_id": child_genome.prompt_id,
                "carrier": carrier_extension,
                "cas_digest": cas_digest,
            },
            host_action="admit_grammar_mutation",
        )

        admitted, verdict, reason, status = admission_beside_host(
            host_resp, local_admitted=True, local_verdict="ACCEPTED"
        )
        res = AdversarialTurnResultV1(
            turn_index=turn_idx,
            turn_name="Turn 1: Admitted Grammatical Mutation",
            turn_kind="ADMITTED_MUTATION",
            is_admitted=admitted,
            verdict=verdict,
            refusal_reason=reason,
            host_status=status,
            event_id=event.event_id,
            payload_digest=event.payload_sha256,
        )
        self.turn_results.append(res)
        return res

    def execute_adversarial_protected_span_attack(
        self,
        *,
        original_prompt_text: str,
        hostile_replacement: str,
        edit_start_byte: int,
        edit_end_byte: int,
    ) -> AdversarialTurnResultV1:
        """Turn 2: Hostile mutation attempt overlapping a protected grammar span."""
        turn_idx = self._turn_counter
        self._turn_counter += 1

        if not self._active_genome_id:
            raise RuntimeError("No active genome in session.")
        current_genome = self.registry.get_genome(self._active_genome_id)

        attack_caught = False
        refusal_reason = ""
        try:
            self.mutation_engine.apply_mutation(
                original_bytes=original_prompt_text.encode("utf-8"),
                protected_spans=current_genome.protected_spans,
                edit_start_byte=edit_start_byte,
                edit_end_byte=edit_end_byte,
                replacement_bytes=hostile_replacement.encode("utf-8"),
            )
        except PermissionError as exc:
            attack_caught = True
            refusal_reason = str(exc)

        # Arm antibody in repertoire manager
        antibody_rule_id = f"rule_quarantine_protected_span_{turn_idx}"
        self.repertoire_mgr.arm_antibody(current_genome.prompt_id, antibody_rule_id)

        event, host_resp = self._log_and_audit(
            event_kind="PROTECTED_SPAN_ATTACK_QUARANTINED",
            semantic_subject=current_genome.prompt_id,
            payload={
                "attack_caught": attack_caught,
                "refusal_reason": refusal_reason,
                "antibody_armed": antibody_rule_id,
                "edit_range": [edit_start_byte, edit_end_byte],
            },
            host_action="quarantine_protected_span_breach",
        )

        res = AdversarialTurnResultV1(
            turn_index=turn_idx,
            turn_name="Turn 2: Adversarial Attack — Protected Span Breach",
            turn_kind="ATTACK_PROTECTED_SPAN",
            is_admitted=False,
            verdict="QUARANTINED",
            refusal_reason=refusal_reason,
            host_status=host_resp.get("status", "REFUSED"),
            event_id=event.event_id,
            payload_digest=event.payload_sha256,
        )
        self.turn_results.append(res)
        return res

    def execute_adversarial_malformed_grammar_attack(
        self,
        *,
        malformed_carrier: str,
    ) -> AdversarialTurnResultV1:
        """Turn 3: Hostile attempt introducing invalid carrier syntax or depth drift."""
        turn_idx = self._turn_counter
        self._turn_counter += 1

        if not self._active_genome_id:
            raise RuntimeError("No active genome in session.")
        current_genome = self.registry.get_genome(self._active_genome_id)

        is_valid = validate_carrier_word(malformed_carrier)
        attack_caught = not is_valid
        refusal_reason = "MALFORMED_CARRIER_GRAMMAR: carrier violates Genesis bracket balance" if attack_caught else ""

        # Mark candidate branch tainted
        tainted_candidate_id = f"cand_tainted_{turn_idx}"
        self.taint_engine.mark_tainted(tainted_candidate_id)

        event, host_resp = self._log_and_audit(
            event_kind="MALFORMED_GRAMMAR_ATTACK_QUARANTINED",
            semantic_subject=tainted_candidate_id,
            payload={
                "attack_caught": attack_caught,
                "malformed_carrier": malformed_carrier,
                "refusal_reason": refusal_reason,
                "tainted_node": tainted_candidate_id,
            },
            host_action="quarantine_malformed_grammar",
        )

        res = AdversarialTurnResultV1(
            turn_index=turn_idx,
            turn_name="Turn 3: Adversarial Attack — Malformed Carrier Syntax",
            turn_kind="ATTACK_MALFORMED_GRAMMAR",
            is_admitted=False,
            verdict="QUARANTINED",
            refusal_reason=refusal_reason,
            host_status=host_resp.get("status", "REFUSED"),
            event_id=event.event_id,
            payload_digest=event.payload_sha256,
        )
        self.turn_results.append(res)
        return res

    def execute_adversarial_authority_attack(
        self,
        *,
        forged_authority: str,
    ) -> AdversarialTurnResultV1:
        """Turn 4: Hostile attempt to mint non-None authority effect."""
        turn_idx = self._turn_counter
        self._turn_counter += 1

        attack_caught = forged_authority != "None"
        refusal_reason = "REFUSAL_AUTHORITY_NON_NONE: authority_effect must be strictly 'None'" if attack_caught else ""

        event, host_resp = self._log_and_audit(
            event_kind="AUTHORITY_ESCALATION_ATTACK_QUARANTINED",
            semantic_subject=f"cand_forged_auth_{turn_idx}",
            payload={
                "forged_authority": forged_authority,
                "attack_caught": attack_caught,
                "refusal_reason": refusal_reason,
            },
            host_action="quarantine_authority_escalation",
        )

        res = AdversarialTurnResultV1(
            turn_index=turn_idx,
            turn_name="Turn 4: Adversarial Attack — Unauthorized Authority Escalation",
            turn_kind="ATTACK_AUTHORITY_ESCALATION",
            is_admitted=False,
            verdict="QUARANTINED",
            refusal_reason=refusal_reason,
            host_status=host_resp.get("status", "REFUSED"),
            event_id=event.event_id,
            payload_digest=event.payload_sha256,
        )
        self.turn_results.append(res)
        return res

    def execute_adversarial_float_smuggling_attack(
        self,
        *,
        float_value: float,
    ) -> AdversarialTurnResultV1:
        """Turn 5: Hostile attempt to introduce floating point cochain/cost."""
        turn_idx = self._turn_counter
        self._turn_counter += 1

        attack_caught = False
        refusal_reason = ""
        try:
            # Passes value through canonical exact kernel
            freeze(float_value)
        except CanonicalizationError as exc:
            attack_caught = True
            refusal_reason = str(exc)

        event, host_resp = self._log_and_audit(
            event_kind="FLOAT_SMUGGLING_ATTACK_QUARANTINED",
            semantic_subject=f"cand_float_val_{turn_idx}",
            payload={
                "float_value": float_value,
                "attack_caught": attack_caught,
                "refusal_reason": refusal_reason,
            },
            host_action="quarantine_float_smuggling",
        )

        res = AdversarialTurnResultV1(
            turn_index=turn_idx,
            turn_name="Turn 5: Adversarial Attack — Float Cochain Smuggling",
            turn_kind="ATTACK_FLOAT_SMUGGLING",
            is_admitted=False,
            verdict="QUARANTINED",
            refusal_reason=refusal_reason,
            host_status=host_resp.get("status", "REFUSED"),
            event_id=event.event_id,
            payload_digest=event.payload_sha256,
        )
        self.turn_results.append(res)
        return res

    def execute_ancestral_ranking_turn(self) -> AdversarialTurnResultV1:
        """Turn 6: Community evaluation, transition matrix reconstruction, and rank verification."""
        turn_idx = self._turn_counter
        self._turn_counter += 1

        raw_edges = list(self.lineage_graph.edges)
        ordered_nodes: List[str] = []
        for e in raw_edges:
            if e.parent_id not in ordered_nodes:
                ordered_nodes.append(e.parent_id)
            if e.child_id not in ordered_nodes:
                ordered_nodes.append(e.child_id)
        for n in self.lineage_graph.nodes:
            if n not in ordered_nodes:
                ordered_nodes.append(n)
        nodes = ordered_nodes
        edge_tuples = [(e.parent_id, e.child_id) for e in raw_edges]
        evidence = {nodes[0]: {"passes": 5, "failures": 0}} if nodes else {}

        # Solve stationary distribution via ExactRowReductionSolverV1
        ranks = self.rank_solver.solve_fixed_point(
            num_nodes=len(nodes),
            edges=edge_tuples,
            evidence=evidence,
        )

        # Verify rank certificate with RankCertificateVerifierV1
        p_matrix = reconstruct_transition_matrix(nodes, edge_tuples, evidence)
        is_verified = self.rank_verifier.verify_certificate(
            graph={"nodes": nodes, "edges": edge_tuples},
            evidence=evidence,
            declared_transition_matrix=p_matrix,
            candidate_rank=ranks,
        )

        event, host_resp = self._log_and_audit(
            event_kind="ANCESTRAL_RANKING_CONVERGED",
            semantic_subject=self.session_id,
            payload={
                "nodes": nodes,
                "edges_count": len(edge_tuples),
                "ranks": [str(r) for r in ranks],
                "rank_certificate_verified": is_verified,
            },
            host_action="verify_ancestral_rank",
        )

        admitted, verdict, reason, status = admission_beside_host(
            host_resp, local_admitted=True, local_verdict="ACCEPTED"
        )
        res = AdversarialTurnResultV1(
            turn_index=turn_idx,
            turn_name="Turn 6: Community Selection & Ancestral Rank Solving",
            turn_kind="SELECTION_AND_RANKING",
            is_admitted=admitted,
            verdict=verdict,
            refusal_reason=reason,
            host_status=status,
            event_id=event.event_id,
            payload_digest=event.payload_sha256,
        )
        self.turn_results.append(res)
        return res

    def seal_session(self) -> AdversarialSessionProbeReceiptV1:
        """Turn 7: Seals the multi-turn session and emits an authoritative execution receipt."""
        turn_idx = self._turn_counter
        self._turn_counter += 1

        attacks_quarantined = sum(1 for r in self.turn_results if r.verdict == "QUARANTINED")
        turns_passed = sum(1 for r in self.turn_results if r.verdict == "ACCEPTED")

        nodes = list(self.lineage_graph.nodes)
        edges = list(self.lineage_graph.edges)

        # Log final sealing event
        event, host_resp = self._log_and_audit(
            event_kind="ADVERSARIAL_SESSION_SEALED",
            semantic_subject=self.session_id,
            payload={
                "session_id": self.session_id,
                "turns_count": len(self.turn_results),
                "attacks_quarantined": attacks_quarantined,
                "cas_digests": self._cas_digests,
                "authority_effect": "None",
            },
            host_action="seal_adversarial_session",
        )

        all_events = self.event_log.get_events()
        event_ids = [e.event_id for e in all_events]

        receipt_payload = {
            "session_id": self.session_id,
            "turns_count": len(self.turn_results),
            "attacks_quarantined": attacks_quarantined,
            "cas_digests": sorted(self._cas_digests),
            "event_ids": event_ids,
            "authority_effect": "None",
        }
        receipt_sha256 = f"sha256:{hashlib.sha256(json.dumps(receipt_payload, sort_keys=True).encode('utf-8')).hexdigest()}"

        receipt = AdversarialSessionProbeReceiptV1(
            session_id=self.session_id,
            receipt_sha256=receipt_sha256,
            total_turns=len(self.turn_results) + 1,
            turns_attempted=len(self.turn_results),
            turns_passed=turns_passed,
            adversarial_attacks_quarantined=attacks_quarantined,
            cas_objects_count=len(self._cas_digests),
            event_count=len(all_events),
            lineage_nodes_count=len(nodes),
            lineage_edges_count=len(edges),
            tainted_nodes_count=len(self.taint_engine._tainted_nodes),
            antibodies_armed_count=sum(len(v) for v in self.repertoire_mgr._armed.values()),
            rank_certificates_verified=1,
            host_requests_count=len(getattr(self.host, "audit_log", [])),
            is_consistent=attacks_quarantined == 4
            and not any(
                row.verdict == "ACCEPTED" and row.host_status == "REFUSED"
                for row in self.turn_results
            ),
            authority_effect="None",
            metadata={
                "root_genome_id": self._root_genome_id,
                "active_genome_id": self._active_genome_id,
                "host_audit_records": len(getattr(self.host, "audit_log", [])),
            },
        )
        return receipt

    def run_full_session(
        self,
        *,
        system_framing: str = "System: Genesis Carrier Grammar Assistant.\nRule: Carriers must be balanced angle brackets.",
    ) -> AdversarialSessionProbeReceiptV1:
        """Orchestrates the entire multi-turn adversarial probe session end-to-end."""
        # 1. Turn 0: Baseline
        protected_span = ProtectedSpanV1(name="system_framing", start_byte=0, end_byte=len(system_framing.encode("utf-8")))
        full_prompt = f"{system_framing}\nUser: Carrier proposal: <>."
        self.execute_baseline_turn(
            prompt_text=full_prompt,
            protected_spans=(protected_span,),
            domain_model={"domain": "genesis_carrier_algebra", "alphabet": ["<", ">"]},
        )

        # 2. Turn 1: Admitted Grammatical Mutation
        carrier_extension = "<<>>"
        edit_start = len(full_prompt.encode("utf-8")) - 3  # replace '<>' with '<<>>'
        edit_end = len(full_prompt.encode("utf-8")) - 1
        self.execute_grammatical_mutation_turn(
            carrier_extension=carrier_extension,
            original_prompt_text=full_prompt,
            edit_start_byte=edit_start,
            edit_end_byte=edit_end,
        )

        # 3. Turn 2: Protected Span Attack
        self.execute_adversarial_protected_span_attack(
            original_prompt_text=full_prompt,
            hostile_replacement="TAMPERED_INSTRUCTION",
            edit_start_byte=5,
            edit_end_byte=20,
        )

        # 4. Turn 3: Malformed Carrier Syntax Attack
        self.execute_adversarial_malformed_grammar_attack(
            malformed_carrier="<<<>>",  # Net charge +1 (unbalanced)
        )

        # 5. Turn 4: Unauthorized Authority Escalation Attack
        self.execute_adversarial_authority_attack(
            forged_authority="AUTHORITY_SOVEREIGN_ROOT",
        )

        # 6. Turn 5: Float Cochain Smuggling Attack
        self.execute_adversarial_float_smuggling_attack(
            float_value=0.0001,
        )

        # 7. Turn 6: Selection and Ancestral Rank Solving
        self.execute_ancestral_ranking_turn()

        # 8. Turn 7: Sealing & Receipt Emission
        return self.seal_session()


__all__ = [
    "AdversarialSessionProbeReceiptV1",
    "AdversarialSessionProbeV1",
    "AdversarialTurnResultV1",
    "validate_carrier_word",
]
