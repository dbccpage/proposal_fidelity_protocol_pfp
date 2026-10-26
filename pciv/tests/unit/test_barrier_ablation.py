"""Ablation matrix executes six production boundary checks on typed attacks."""
import hashlib
import json

from omega_engine_epistemic_immune_system.domain.danger_gate import (
    Signal1Match,
    Signal2Danger,
    TwoSignalDangerGate,
)
from omega_engine_operating_system.adapters.packet_seat import PacketSeatAdapterV1
from omega_engine_operating_system.adapters.prompt_civ.ablation import (
    BARRIERS,
    barrier_ablation_matrix,
)
from omega_engine_operating_system.adapters.prompt_civ.custody import PromptCustodyLedgerV1
from omega_engine_operating_system.adapters.prompt_civ.domain import (
    DomainPlacementV1,
    hard_domain_eligible,
)
from omega_engine_operating_system.adapters.prompt_civ.record import (
    CustodyTier,
    PromptGenomeV1,
)
from omega_engine_operations.tests.prompt_civilization.test_prompt_custody import (
    TestHostVerifier,
    decision,
)
from omega_engine_woland.domain.circuit import (
    WolandSevenActCircuit,
    validate_woland_swarm_composition,
)
from omega_engine_woland.infrastructure.native import DefaultNativeOperationPort
from omega_engine_woland.runtime import build_woland_runtime
from omega_engine_woland.stage.application.swarm_runtime import execute_circuit
from omega_engine_woland.stage.domain import WorkPacketV1
from omega_engine_woland.stage.domain.topology import SwarmCompositionV1
from omega_engine_woland.use_cases.bout_service import create_woland_circuit_runner


def test_single_and_pair_ablations_record_which_real_barriers_are_load_bearing(tmp_path):
    verifier = TestHostVerifier()
    ledger = PromptCustodyLedgerV1(tmp_path / "custody.sqlite", verifier)
    admitted = PromptGenomeV1([{"sha256": "admitted"}], {})
    unreviewed = PromptGenomeV1([{"sha256": "unreviewed"}], {})
    ledger.submit_candidate(admitted, "proposer")
    ledger.apply(admitted, decision(verifier, admitted, CustodyTier.REVIEWED, "review"))
    ledger.apply(admitted, decision(verifier, admitted, CustodyTier.ADMITTED, "admit"))
    fixtures = {name: name for name in BARRIERS}
    runtime = build_woland_runtime(output_dir=tmp_path / "bout", fixture_mode=True)
    packet = WorkPacketV1(
        task_key="barrier_ablation_fixture", scene_id="act1_perception",
        objective="Evaluate the local barrier fixture", input_artifact_refs=(),
        acceptance_criteria=("Record all seven acts",), budget_units=50,
        evaluator_epoch_id="sha256:" + hashlib.sha256(b"barrier-fixture-epoch").hexdigest(),
    )
    complete_gate = execute_circuit(WolandSevenActCircuit(
        run_id=packet.task_key, input_packet=packet, profile=runtime.profile,
        acts_runner=create_woland_circuit_runner(runtime, output_dir=tmp_path / "bout", fixture_seats=True, native_support=DefaultNativeOperationPort()),
    ))
    refused_gate = WolandSevenActCircuit(fail_preflight=True).execute()
    assert complete_gate.is_completed_gated_run is True

    def composition(attack):
        return validate_woland_swarm_composition(SwarmCompositionV1(
            swarm_ancestry=["omega.generic.swarm.v1"] if attack == "composition" else ["omega.woland.swarm.v1"],
            required_skills=["/woland"], runtime="omega.woland.runtime.v1",
            operating_system="omega.oeos.host.v1", llm_protocol="omega.symbol_game.protocol.v2",
        ))

    def two_signal(attack):
        match = Signal1Match(detector_id="detector", matched_locus="task", match_signature="bad")
        danger = Signal2Danger.derive_from_signal1_match(match) if attack == "two_signal" else Signal2Danger(
            source="host_os_audit", danger_kind="UNAUTHORIZED_FILE_WRITE_ATTEMPT", witness_digest="sha256:host",
        )
        TwoSignalDangerGate().evaluate_conjunction(signal1=match, signal2=danger)
        return True

    def custody(attack):
        ledger.approved(unreviewed if attack == "custody" else admitted, "math")
        return True

    seat = PacketSeatAdapterV1(storage_dir=tmp_path / "seat")

    def packet_seat(attack):
        # The actual packet adapter refuses before provider invocation for the
        # oversized fixture; successful controls use its local fixture transport.
        seat.prepare_and_send(body="x" * (seat.BODY_LIMIT_BYTES + 1) if attack == "packet_seat" else "fixture")
        return True

    guards = {
        "packet_seat": packet_seat,
        "composition": composition,
        "gate_receipt": lambda attack: (refused_gate if attack == "gate_receipt" else complete_gate).is_completed_gated_run,
        "two_signal": two_signal,
        "custody": custody,
        "scope": lambda attack: hard_domain_eligible(
            DomainPlacementV1("placement", "digest", "math", ("math",), "ADMITTED_LOCAL"),
            "medicine" if attack == "scope" else "math",
        ),
    }
    report = barrier_ablation_matrix(fixtures, guards)
    (tmp_path / "ablation.json").write_text(json.dumps(report, sort_keys=True, indent=2), encoding="utf-8")
    assert len(report["trials"]) == 22 * 6
    for trial in report["trials"]:
        assert trial["accepted"] is (trial["fixture_id"] in trial["disabled"])
    assert report["report_only"] is True
    assert report["authority_effect"] == "None"
    ledger.close()
