"""End-to-end integration runner and receipt generator for Prompt Civilization.

Connects CAS, durable event logging, lineage tracking, ancestral ranking,
immunity propagation, and projection crash recovery under OEOS.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from fractions import Fraction
from itertools import islice
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..domain.models import (
    CustodyTier,
    PromptGenomeRegistryV1,
    PromptGenomeV1,
    PromptViewEngineV1,
    ProtectedSpanV1,
)
from ..infrastructure.cas import ContentAddressedStorageV1
from ..infrastructure.event_log import DurableEventLogV1, PromptCivEventV1
from ..infrastructure.persistence import PromptCivProjectionEngineV1
from .backfill import PromptCivBackfillEngineV1
from .e2e import PromptCivE2EFixtureV1
from .fitness import ParetoFrontSelectorV1, PromptFitnessCalculatorV1
from pciv.domain.causal_witness import (
    PLACEHOLDER_WITNESS,
    seal_causal_witness,
)
from .genealogy import LineageGraphV1, RelationshipType
from .immunity import ArmedRepertoireManagerV1, ImmunityPropagationEngineV1
from .rank import AncestralRankCalculatorV1, RankCertificateVerifierV1


@dataclass(frozen=True)
class PromptCivIntegrationReceiptV1:
    """Cryptographic, deterministic execution receipt for Prompt Civ integration runs."""

    receipt_id: str
    receipt_sha256: str
    event_count: int
    cas_objects_count: int
    genomes_count: int
    occurrences_count: int
    lineage_edges_count: int
    rank_certificates_verified: int
    antibodies_armed_count: int
    recovered_projections_count: int
    is_consistent: bool
    authority_effect: str = "None"
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PromptCivIntegrationRunnerV1:
    """Executes end-to-end integration runs across prompt civ adapter layers."""

    def __init__(
        self,
        intelligence_root: Optional[Path] = None,
        event_log_dir: Optional[Path] = None,
        cas_dir: Optional[Path] = None,
    ) -> None:
        self.intelligence_root = intelligence_root or Path("_ic")
        self.cas = ContentAddressedStorageV1(storage_dir=cas_dir)
        self.event_log = DurableEventLogV1(log_dir=event_log_dir)
        self.registry = PromptGenomeRegistryV1()
        self.view_engine = PromptViewEngineV1()
        self.lineage_graph = LineageGraphV1()
        self.rank_calc = AncestralRankCalculatorV1()
        self.rank_verifier = RankCertificateVerifierV1()
        self.immunity_engine = ImmunityPropagationEngineV1()
        self.repertoire_mgr = ArmedRepertoireManagerV1()
        self.fitness_calc = PromptFitnessCalculatorV1()
        self.pareto_selector = ParetoFrontSelectorV1()
        self.projection_engine = PromptCivProjectionEngineV1()
        self.e2e_fixture = PromptCivE2EFixtureV1()

    def run_simulated_integration(self) -> PromptCivIntegrationReceiptV1:
        """Executes a comprehensive simulated integration run verifying end-to-end receipt generation."""
        # 1. CAS Ingestion: Store prompt source bytes
        root_prompt_bytes = b"System: You are a formal verification assistant.\nUser: Prove exactness."
        root_cas_digest = self.cas.store(root_prompt_bytes)

        child_prompt_bytes = b"System: You are a formal verification assistant with L1 defect bound.\nUser: Prove exactness."
        child_cas_digest = self.cas.store(child_prompt_bytes)

        # 2. Genome Registration with Protected Spans
        root_span = ProtectedSpanV1(name="system_framing", start_byte=0, end_byte=48)
        root_genome = PromptGenomeV1.create_verified(
            source_packet_refs=[{"packet_id": "pkt_root", "sha256": root_cas_digest}],
            domain_model={"domain": "formal_verification", "target": "ExactRat"},
            parents=(),
            declared_generation=0,
            protected_spans=(root_span,),
            birth_custody=CustodyTier.ADMITTED,
        )
        self.registry.register_genome(root_genome)

        child_genome = PromptGenomeV1.create_verified(
            source_packet_refs=[{"packet_id": "pkt_child", "sha256": child_cas_digest}],
            domain_model={"domain": "formal_verification", "target": "ExactRat"},
            parents=({"prompt_id": root_genome.prompt_id, "generation": 0},),
            declared_generation=1,
            protected_spans=(root_span,),
            birth_custody=CustodyTier.CANDIDATE,
        )
        self.registry.register_genome(child_genome)

        # 3. Durable Event Log Ingestion
        event_root_created = PromptCivEventV1(
            producer_id="oeos_sim",
            event_kind="GenomeRegistered",
            run_id="run_sim_001",
            occurrence_id="occ_root",
            semantic_subject=root_genome.prompt_id,
            producer_ordinal=1,
            payload={"prompt_id": root_genome.prompt_id, "cas_digest": root_cas_digest},
        )
        self.event_log.append_event(event_root_created)

        # Execution Occurrences & Event Logging
        occ_1 = self.registry.record_execution(
            prompt_id=root_genome.prompt_id,
            session_id="sess_001",
            input_packet_id="inp_001",
            output_packet_id="out_001",
        )
        event_occ_1 = PromptCivEventV1(
            producer_id="oeos_sim",
            event_kind="ExecutionPass",
            run_id="run_sim_001",
            occurrence_id=occ_1.occurrence_id,
            semantic_subject=root_genome.prompt_id,
            producer_ordinal=2,
            payload={"prompt_id": root_genome.prompt_id, "status": "PASS"},
        )
        self.event_log.append_event(event_occ_1)

        occ_2 = self.registry.record_execution(
            prompt_id=child_genome.prompt_id,
            session_id="sess_001",
            input_packet_id="inp_002",
            output_packet_id="out_002",
        )
        event_occ_2 = PromptCivEventV1(
            producer_id="oeos_sim",
            event_kind="ExecutionPass",
            run_id="run_sim_001",
            occurrence_id=occ_2.occurrence_id,
            semantic_subject=child_genome.prompt_id,
            producer_ordinal=3,
            payload={"prompt_id": child_genome.prompt_id, "status": "PASS"},
        )
        self.event_log.append_event(event_occ_2)

        # 4. Lineage Graph & Witnessed Mutation
        placeholder = {
            "receipt_id": "rcpt_witness_001",
            "receipt_sha256": PLACEHOLDER_WITNESS,
            "authority_effect": "None",
        }
        try:
            self.lineage_graph.add_edge(
                parent_id=root_genome.prompt_id,
                child_id=child_genome.prompt_id,
                relationship=RelationshipType.DIRECT_MUTATION,
                witness_receipt=placeholder,
            )
        except ValueError as exc:
            if "CAUSAL_WITNESS_REQUIRED" not in str(exc):
                raise
        else:
            raise RuntimeError("placeholder witness was accepted as a causal edge")
        witness_receipt = seal_causal_witness(
            {
                "receipt_id": "rcpt_witness_001",
                "parent_id": root_genome.prompt_id,
                "child_id": child_genome.prompt_id,
                "authority_effect": "None",
            }
        )
        self.lineage_graph.add_edge(
            parent_id=root_genome.prompt_id,
            child_id=child_genome.prompt_id,
            relationship=RelationshipType.DIRECT_MUTATION,
            witness_receipt=witness_receipt,
        )

        # 5. Ancestral Rank Calculation & Transition Matrix Reconstruction
        # Root (P) lifted by Child (C) with pass fraction 9/10
        rank_score = self.rank_calc.compute_inverse_rank(
            parent_id=root_genome.prompt_id,
            child_id=child_genome.prompt_id,
            child_pass_fraction=Fraction(9, 10),
        )
        assert rank_score == Fraction(17, 20) * Fraction(9, 10) + Fraction(3, 20)

        # Reconstructed matrix verification
        nodes = [root_genome.prompt_id, child_genome.prompt_id]
        bound_graph = {"nodes": nodes, "edges": [(root_genome.prompt_id, child_genome.prompt_id)]}
        evidence = {child_genome.prompt_id: {"passes": 9, "failures": 1}}
        # P<- has entry at [child_idx][parent_idx] = 9/10
        declared_matrix = [
            [Fraction(0, 1), Fraction(0, 1)],
            [Fraction(9, 10), Fraction(0, 1)],
        ]
        self.rank_verifier.verify_certificate(
            graph=bound_graph,
            evidence=evidence,
            declared_transition_matrix=declared_matrix,
            candidate_rank=[rank_score, Fraction(1, 2)],
        )

        # 6. Immunity Acquisition & Propagation
        acq_event = {
            "acquisition_id": "acq_001",
            "rule_id": "rule_exact_arithmetic",
            "target_prompt_id": child_genome.prompt_id,
        }
        propagated_nodes = self.immunity_engine.propagate_backward(
            acquisition=acq_event,
            current_prompt_id=child_genome.prompt_id,
        )
        for node in propagated_nodes:
            self.repertoire_mgr.arm_antibody(node, "rule_exact_arithmetic")

        armed_before = self.repertoire_mgr.get_armed_repertoire(child_genome.prompt_id, ledger_revision=1)
        assert "rule_exact_arithmetic" in armed_before

        # 7. Projection Replay & Consistency Verification
        self.projection_engine.record_event(
            {"event_id": event_occ_1.event_id, "kind": "ExecutionPass", "prompt_id": root_genome.prompt_id}
        )
        self.projection_engine.record_event(
            {"event_id": event_occ_2.event_id, "kind": "ExecutionPass", "prompt_id": child_genome.prompt_id}
        )
        recovered = self.projection_engine.recover_from_crash()

        # 8. Cryptographic Receipt Synthesis
        receipt_payload = {
            "event_count": self.event_log.event_count(),
            "cas_objects_count": 2,
            "genomes_count": self.registry.total_genome_count(),
            "occurrences_count": 2,
            "lineage_edges_count": 1,
            "rank_certificates_verified": 1,
            "antibodies_armed_count": len(armed_before),
            "recovered_projections_count": len(recovered),
            "is_consistent": recovered.is_consistent,
            "authority_effect": "None",
        }
        canonical_raw = json.dumps(receipt_payload, sort_keys=True).encode("utf-8")
        receipt_sha = "sha256:" + hashlib.sha256(canonical_raw).hexdigest()
        receipt_id = f"rcpt_prompt_civ_sim_{hashlib.sha256(canonical_raw).hexdigest()[:16]}"

        return PromptCivIntegrationReceiptV1(
            receipt_id=receipt_id,
            receipt_sha256=receipt_sha,
            event_count=receipt_payload["event_count"],
            cas_objects_count=receipt_payload["cas_objects_count"],
            genomes_count=receipt_payload["genomes_count"],
            occurrences_count=receipt_payload["occurrences_count"],
            lineage_edges_count=receipt_payload["lineage_edges_count"],
            rank_certificates_verified=receipt_payload["rank_certificates_verified"],
            antibodies_armed_count=receipt_payload["antibodies_armed_count"],
            recovered_projections_count=receipt_payload["recovered_projections_count"],
            is_consistent=receipt_payload["is_consistent"],
            authority_effect="None",
            metadata={"simulation_mode": True, "root_genome": root_genome.prompt_id},
        )

    def run_live_integration(self) -> PromptCivIntegrationReceiptV1:
        """Executes an integration run against checked-in intelligence event logs and records."""
        # 1. Run backfill engine over checked-in intelligence roots
        backfill_engine = PromptCivBackfillEngineV1(intelligence_root=self.intelligence_root)
        backfill_receipt = backfill_engine.run_backfill()

        # 2. Ingest checked-in genealogy JSONL records if present
        genealogy_candidates = [
            self.intelligence_root / "nara/permanent_records/prompt_genealogy.jsonl",
            self.intelligence_root / "nara/permanent_records/darpa/adversary/prompt_genealogy.jsonl",
            self.intelligence_root / "darpa/adversary/prompt_genealogy.jsonl",
        ]
        genealogy_path = next((p for p in genealogy_candidates if p.exists()), genealogy_candidates[-1])
        genealogy_records: List[Dict[str, Any]] = []
        if genealogy_path.exists():
            with open(genealogy_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            genealogy_records.append(json.loads(line))
                        except Exception:
                            pass

        # 3. Ingest checked-in unified packets JSONL if present
        packets_path = self.intelligence_root / "nara/legacy/unified_oe_packets.jsonl"
        packet_count = 0
        if packets_path.exists():
            with open(packets_path, "rb") as f:
                for ordinal, raw in enumerate(islice(f, 20), 1):
                    raw_digest = self.cas.store(raw)
                    packet_count += 1
                    try:
                        pkt_data = json.loads(raw)
                        if not isinstance(pkt_data, dict):
                            raise ValueError("packet must be an object")
                    except (ValueError, UnicodeDecodeError):
                        pkt_data = {}
                        error_kind = "MALFORMED_PACKET"
                    else:
                        error_kind = None
                    event = PromptCivEventV1(
                        producer_id="unified_packet_ingest",
                        event_kind="PacketObserved",
                        run_id=pkt_data.get("run_id", "run_unknown"),
                        occurrence_id=f"occ_{ordinal}",
                        semantic_subject=pkt_data.get("packet_id", f"pkt_{ordinal}"),
                        producer_ordinal=ordinal,
                        payload={
                            "packet_id": pkt_data.get("packet_id"), "raw_digest": raw_digest,
                            "error_kind": error_kind,
                        },
                    )
                    self.event_log.append_event(event)
                    if pkt_data.get("prompt_id"):
                        self.projection_engine.record_event({
                            "kind": "PacketObserved", "prompt_id": pkt_data["prompt_id"],
                        })

        # 4. Replay projections
        recovered = self.projection_engine.recover_from_crash()

        # 5. Synthesize integration receipt
        receipt_payload = {
            "backfill_sha256": backfill_receipt.receipt_sha256,
            "antibodies_indexed": backfill_receipt.antibodies_indexed,
            "antibodies_refused": backfill_receipt.antibodies_refused,
            "genealogy_records_ingested": len(genealogy_records),
            "packets_ingested": min(packet_count, 20),
            "recovered_projections": len(recovered),
            "is_consistent": recovered.is_consistent,
            "authority_effect": "None",
        }
        canonical_raw = json.dumps(receipt_payload, sort_keys=True).encode("utf-8")
        receipt_sha = "sha256:" + hashlib.sha256(canonical_raw).hexdigest()
        receipt_id = f"rcpt_prompt_civ_live_{hashlib.sha256(canonical_raw).hexdigest()[:16]}"

        return PromptCivIntegrationReceiptV1(
            receipt_id=receipt_id,
            receipt_sha256=receipt_sha,
            event_count=self.event_log.event_count(),
            cas_objects_count=min(packet_count, 20),
            genomes_count=self.registry.total_genome_count(),
            occurrences_count=0,
            lineage_edges_count=0,
            rank_certificates_verified=0,
            antibodies_armed_count=0,
            recovered_projections_count=len(recovered),
            is_consistent=recovered.is_consistent,
            authority_effect="None",
            metadata=receipt_payload,
        )


def main() -> None:
    """CLI runner executing live and simulated integration runs."""
    runner = PromptCivIntegrationRunnerV1()
    sim_receipt = runner.run_simulated_integration()
    print("=== Simulated Integration Receipt ===")
    print(json.dumps(sim_receipt.to_dict(), indent=2))

    live_receipt = runner.run_live_integration()
    print("\n=== Live Intelligence Integration Receipt ===")
    print(json.dumps(live_receipt.to_dict(), indent=2))


if __name__ == "__main__":
    main()

PromptCivIntegrationHarnessV1 = PromptCivIntegrationRunnerV1
