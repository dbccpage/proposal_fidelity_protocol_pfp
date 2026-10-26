"""The base swarm's estate connections, checked by reading each estate's own store.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from omega_engine_epistemic_immune_system.domain.pharmacy_catalog import (
    PharmacyCatalogRepository,
)
from omega_engine_operations.domain.rop.result import Ok
from omega_engine_woland.domain.connection import EstateName
from omega_engine_woland.domain.estate_ports import (
    ROUTING_TERMINAL_BY_BOUT_STATUS,
    AntiSkillDecisionV1,
)
from omega_engine_woland.domain.instruction_ingress import instruction_request_digest
from omega_engine_woland.domain.models import WolandBoutRequestV1
from omega_engine_woland.domain.specialization import PortName
from omega_engine_woland.infrastructure.coda_adapter import CodaEvaluationAdapter
from omega_engine_woland.infrastructure.estates.null_estate import NullEstateAdapter
from omega_engine_woland.infrastructure.estates.oewas_anti_skill import OewasAntiSkillAdapter
from omega_engine_woland.runtime import build_woland_spine, build_woland_swarm
from omega_engine_woland.use_cases.anti_skill_predispatch import bout_dispatch_subject
from omega_engine_woland.use_cases.base_swarm.specializations import RESEARCH_PROFILE_V01
from omega_engine_woland.use_cases.base_swarm.woland_swarm import (
    SGT_TURN_SCHEMA,
    OmegaEngineWolandSwarm,
    bout_claim_subject,
)


def _research_woland(*, spine=None, **options):
    return build_woland_swarm(
        OmegaEngineWolandSwarm,
        specialization=RESEARCH_PROFILE_V01,
        spine=spine,
        **options,
    )


def test_spine_reuses_the_same_anti_skill_gate_at_service_ingress(tmp_path: Path) -> None:
    spine = build_woland_spine(tmp_path)
    assert spine.bout.service.anti_skill_gate is spine.anti_skill
    disconnected = build_woland_spine(
        tmp_path, disconnected_ports=frozenset({PortName.OEWAS_ANTI_SKILL})
    )
    assert disconnected.bout.service.anti_skill_gate is None


def test_production_anti_skill_adapter_pins_its_runtime_snapshot() -> None:
    gate = OewasAntiSkillAdapter()
    with pytest.raises(FrozenInstanceError):
        gate.runtime = None

#: Ports whose probe must observe a real effect on this workstation.
ALWAYS_CONNECTED = {
    PortName.NATIVE_BOUT,
    PortName.IMMUNE_ANTIBODIES,
    PortName.PROMPT_GENEALOGY,
    PortName.SGT_EMISSION,
    PortName.ENVELOPE_STORE,
    PortName.WOLAND_RUNTIME,
    PortName.SEAT_TRANSPORT,
}
#: Ports reported disconnected, each for a stated reason, until later work connects them.
DISCONNECTED_WITH_REASON = {
    PortName.LGGR_GLUING: "PYTHON_EVALUATOR",
    PortName.OEWAS_ANTI_SKILL: "NO_VERIFIED_RUNTIME",
}

SPINE_SLOTS = {
    "bout": PortName.NATIVE_BOUT,
    "coda": PortName.CODA_EVALUATION,
    "lggr": PortName.LGGR_GLUING,
    "immune": PortName.IMMUNE_ANTIBODIES,
    "genealogy": PortName.PROMPT_GENEALOGY,
    "anti_skill": PortName.OEWAS_ANTI_SKILL,
    "sgt": PortName.SGT_EMISSION,
    "envelopes": PortName.ENVELOPE_STORE,
}


def _snapshot(root: Path) -> dict[Path, bytes]:
    """Compare store content, not SQLite WAL/checkpoint physical representation."""
    result: dict[Path, bytes] = {}
    for path in root.rglob("*"):
        if not path.is_file() or path.name.endswith((".sqlite3-wal", ".sqlite3-shm")):
            continue
        if path.name.endswith(".sqlite3"):
            connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
            try:
                result[path] = "\n".join(connection.iterdump()).encode("utf-8")
            finally:
                connection.close()
        else:
            result[path] = path.read_bytes()
    return result


def test_probe_snapshot_still_detects_logical_sqlite_writes(tmp_path: Path) -> None:
    database = tmp_path / "state.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE events (value TEXT NOT NULL)")
    before = _snapshot(tmp_path)
    with sqlite3.connect(database) as connection:
        connection.execute("INSERT INTO events (value) VALUES ('changed')")
    assert _snapshot(tmp_path) != before


def test_the_matrix_reports_each_estate_from_an_observed_effect(tmp_path: Path) -> None:
    root, scratch = tmp_path / "root", tmp_path / "probe"
    root.mkdir()
    swarm = _research_woland(repo_root=root)
    before = _snapshot(root)
    receipts = {receipt.port: receipt for receipt in swarm.connection_matrix(str(scratch))}

    assert set(receipts) == set(PortName) - {PortName.OEWAS_LEARNING}
    assert {receipt.estate for receipt in receipts.values()} == set(EstateName)
    for port in ALWAYS_CONNECTED:
        assert receipts[port].connected, (port, receipts[port].detail)
        assert len(receipts[port].effect_digest) == 64
    for port, reason in DISCONNECTED_WITH_REASON.items():
        assert not receipts[port].connected
        assert receipts[port].detail.startswith(reason)
    coda_native = CodaEvaluationAdapter._find_coda_binary() is not None
    assert receipts[PortName.CODA_EVALUATION].connected is coda_native
    # Probes write only inside the scratch root, never into the live stores.
    after = _snapshot(root)
    assert after == before, {
        "added": sorted(str(path.relative_to(root)) for path in after.keys() - before.keys()),
        "removed": sorted(str(path.relative_to(root)) for path in before.keys() - after.keys()),
        "changed": sorted(
            str(path.relative_to(root))
            for path in before.keys() & after.keys()
            if before[path] != after[path]
        ),
    }


@pytest.mark.parametrize("slot", sorted(SPINE_SLOTS))
def test_a_null_adapter_disconnects_exactly_its_own_port(tmp_path: Path, slot: str) -> None:
    port = SPINE_SLOTS[slot]
    spine = build_woland_spine(tmp_path, disconnected_ports=frozenset({port}))
    for other, other_port in SPINE_SLOTS.items():
        adapter = getattr(spine, other)
        assert isinstance(adapter, NullEstateAdapter) is (other == slot)
        assert adapter.port is other_port
    probe = getattr(spine, slot).probe(str(tmp_path / "probe"))
    assert not probe.connected and probe.effect_digest is None


def _read_lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_bytes().splitlines()]


def test_a_fixture_bout_reaches_every_licensed_estate(tmp_path: Path) -> None:
    swarm = _research_woland(repo_root=tmp_path)
    result = swarm.run_bout("Connection test objective.", "spine-bout").unwrap()
    outcome = result.outcome
    assert result.routing_terminal == ROUTING_TERMINAL_BY_BOUT_STATUS[outcome.status]
    assert result.estate_residuals == ()
    # OEWAS: without a verified runtime the gate holds the claim at PRE_SEAL.
    assert result.seal_decision is not None
    assert (result.seal_decision.stage, result.seal_decision.disposition) == ("PRE_SEAL", "HOLD")

    custody = tmp_path / "_intelligence" / "_woland"
    (packet,) = _read_lines(custody / "sgt_packets.jsonl")
    assert packet["session_id"] == "spine-bout"
    assert packet["turn"]["schema"] == SGT_TURN_SCHEMA
    assert packet["turn"]["receipt_id"] == outcome.receipt_id
    (lineage,) = _read_lines(custody / "swarm_lineage.jsonl")
    assert lineage["payload"]["parent_run_key"] == "task:spine-bout"
    assert lineage["payload"]["child_run_key"] == f"bout:{outcome.receipt_id}"
    # A fixture bout is never composted into the pharmacy.
    assert result.composted_antibody_ids == ()
    assert not PharmacyCatalogRepository(tmp_path).catalog_file.exists()


class _ReplayBout:
    """Replays a recorded native outcome with blockers, as a live bout would report them."""

    def __init__(self, outcome) -> None:
        self.outcome = outcome

    def execute_bout(self, request):
        return Ok(self.outcome)


class _ClearDispatchHoldSealGate:
    """Test-only gate for exercising post-dispatch behavior without an active registry."""

    estate = EstateName.OEWAS
    port = PortName.OEWAS_ANTI_SKILL

    def evaluate(self, stage, subject):
        if stage == "PRE_DISPATCH":
            return Ok(AntiSkillDecisionV1(
                stage=stage,
                subject_id=subject["subject_id"],
                disposition="CLEAR",
                registry_id="sha256:" + "1" * 64,
                activation_profile_digest="sha256:" + "2" * 64,
                hit_ids=(),
                receipt_id="sha256:" + "3" * 64,
            ))
        return Ok(AntiSkillDecisionV1(
            stage=stage,
            subject_id="sha256:" + "0" * 64,
            disposition="HOLD",
            registry_id="",
            hit_ids=(),
            receipt_id="",
        ))


def test_live_base_swarm_holds_before_native_bout_without_active_profile(tmp_path: Path) -> None:
    class NativeSpy:
        calls = 0

        def execute_bout(self, request):
            self.calls += 1
            raise AssertionError("native bout ran before pre-dispatch clearance")

    built = _research_woland(repo_root=tmp_path)
    native = NativeSpy()
    swarm = _research_woland(spine=replace(built.spine, bout=native))

    result = swarm.run_bout("Connection test objective.", "held-before-native", fixture_mode=False)

    assert result.is_err
    assert result.unwrap_err().code == "ANTI_SKILL_PRE_DISPATCH_UNCLEARED"
    assert native.calls == 0


@pytest.mark.parametrize("defect", ("wrong_subject", "missing_profile", "wrong_stage"))
def test_unbound_predispatch_clear_cannot_execute(tmp_path: Path, defect: str) -> None:
    class NativeSpy:
        calls = 0

        def execute_bout(self, request):
            self.calls += 1
            raise AssertionError("native bout ran on an unbound anti-skill decision")

    class BadGate:
        estate = EstateName.OEWAS
        port = PortName.OEWAS_ANTI_SKILL

        def evaluate(self, stage, subject):
            good = _ClearDispatchHoldSealGate().evaluate(stage, subject).unwrap()
            changes = {
                "wrong_subject": {"subject_id": "sha256:" + "0" * 64},
                "missing_profile": {"activation_profile_digest": ""},
                "wrong_stage": {"stage": "PRE_SEAL"},
            }
            return Ok(replace(good, **changes[defect]))

    built = _research_woland(repo_root=tmp_path)
    native = NativeSpy()
    swarm = _research_woland(spine=replace(built.spine, bout=native, anti_skill=BadGate()))

    result = swarm.run_bout("Connection test objective.", "bad-dispatch", fixture_mode=False)

    assert result.is_err
    assert result.unwrap_err().code == "ANTI_SKILL_PRE_DISPATCH_UNCLEARED"
    assert native.calls == 0


def test_anti_skill_profile_binding_must_be_a_digest() -> None:
    with pytest.raises(ValueError, match="activation_profile_digest"):
        AntiSkillDecisionV1(
            stage="PRE_DISPATCH",
            subject_id="sha256:" + "0" * 64,
            disposition="CLEAR",
            registry_id="sha256:" + "1" * 64,
            activation_profile_digest="not-a-digest",
            hit_ids=(),
            receipt_id="sha256:" + "2" * 64,
        )


def test_pre_dispatch_subject_is_deterministic_and_full_request_bound() -> None:
    first = WolandBoutRequestV1("Objective A", "task_a", fixture_mode=False)
    same = WolandBoutRequestV1("Objective A", "task_a", fixture_mode=False)
    changed_objective = WolandBoutRequestV1("Objective B", "task_a", fixture_mode=False)
    changed_task = WolandBoutRequestV1("Objective A", "task_b", fixture_mode=False)
    changed_budget = WolandBoutRequestV1(
        "Objective A", "task_a", fixture_mode=False, compute_budget=101
    )
    changed_carrier = WolandBoutRequestV1(
        "Objective A", "task_a", fixture_mode=False, carrier_context={"pin": "other"}
    )
    changed_ablation = WolandBoutRequestV1(
        "Objective A", "task_a", fixture_mode=False, ablation_flags={"nocebo": True}
    )

    subject = bout_dispatch_subject("woland.research", first)
    assert subject.subject_id == bout_dispatch_subject("woland.research", same).subject_id
    assert subject.subject_id != bout_dispatch_subject("woland.research", changed_objective).subject_id
    assert subject.subject_id != bout_dispatch_subject("woland.research", changed_task).subject_id
    assert subject.subject_id != bout_dispatch_subject("woland.research", changed_budget).subject_id
    assert subject.subject_id != bout_dispatch_subject("woland.research", changed_carrier).subject_id
    assert subject.subject_id != bout_dispatch_subject("woland.research", changed_ablation).subject_id


def test_pre_seal_subject_binds_exact_request_and_native_receipt(tmp_path: Path) -> None:
    built = _research_woland(repo_root=tmp_path)
    outcome = built.run_bout("Connection test objective.", "seal-subject").unwrap().outcome
    request = WolandBoutRequestV1(
        "Connection test objective.", "seal-subject", fixture_mode=False,
        max_rounds=RESEARCH_PROFILE_V01.budget.max_rounds,
        compute_budget=RESEARCH_PROFILE_V01.budget.compute_budget,
    )
    subject = bout_claim_subject("woland.research", outcome, request)
    assert subject.evidence_scope == (
        f"request:{instruction_request_digest(request)}",
        f"woland_bout_receipt:{outcome.receipt_id}",
    )
    assert bout_claim_subject(
        "woland.research", replace(outcome, receipt_id="sha256:" + "f" * 64), request
    ).subject_id != subject.subject_id
    assert bout_claim_subject(
        "woland.research", outcome, replace(request, objective="Changed objective")
    ).subject_id != subject.subject_id


def test_non_content_addressed_live_receipt_cannot_reach_pre_seal_gate(tmp_path: Path) -> None:
    built = _research_woland(repo_root=tmp_path)
    fixture = built.run_bout("Connection test objective.", "bad-seal-fixture").unwrap().outcome
    accepted = replace(
        fixture, receipt_id="not-content-addressed", status="AUTHORIZED", is_authorized=True,
        terminal_verdict="PASS_TO_MASTER", checker_verdict="ACCEPTED",
        checker_receipt_sha256="sha256:" + "1" * 64,
        authorization_evidence="CHECKER_VERDICT_ONLY_NO_CARRIER_DECLARED",
    )

    class Gate:
        estate = EstateName.OEWAS
        port = PortName.OEWAS_ANTI_SKILL

        def evaluate(self, stage, subject):
            if stage == "PRE_SEAL":
                raise AssertionError("unbound native receipt reached pre-seal")
            return _ClearDispatchHoldSealGate().evaluate(stage, subject)

    swarm = _research_woland(spine=replace(
        built.spine, bout=_ReplayBout(accepted), anti_skill=Gate()
    ))
    result = swarm.run_bout(
        "Connection test objective.", "bad-seal-live", fixture_mode=False
    ).unwrap()
    assert result.routing_terminal == "RequiresLift"
    assert "ANTI_SKILL_PRE_SEAL_SUBJECT_INVALID" in {
        refusal.code for refusal in result.estate_residuals
    }


def test_live_bout_blockers_are_composted_as_candidates_only(tmp_path: Path) -> None:
    first = _research_woland(repo_root=tmp_path)
    recorded = first.run_bout("Connection test objective.", "spine-compost").unwrap().outcome
    blocked = replace(recorded, authorization_blockers=("CHECKER_UNBOUND", "FIXTURE_SEATS"))
    spine = replace(first.spine, bout=_ReplayBout(blocked), anti_skill=_ClearDispatchHoldSealGate())
    swarm = _research_woland(spine=spine)

    result = swarm.run_bout("Connection test objective.", "spine-compost-2", fixture_mode=False)
    composted = result.unwrap().composted_antibody_ids
    assert len(composted) == 2
    catalog = PharmacyCatalogRepository(tmp_path).load_catalog()["antibodies"]
    assert {catalog[ab_id]["pharmacy_status"] for ab_id in composted} == {"candidate"}
    guidance = swarm.spine.immune.admitted_guidance().unwrap()
    assert guidance.lines == ()


def test_a_disconnected_estate_is_a_residual_not_a_silent_skip(tmp_path: Path) -> None:
    swarm = _research_woland(
        repo_root=tmp_path,
        disconnected_ports=frozenset({PortName.PROMPT_GENEALOGY}),
    )
    result = swarm.run_bout("Connection test objective.", "spine-null").unwrap()
    assert [residual.code for residual in result.estate_residuals] == ["ESTATE_DISCONNECTED"]
    assert not (tmp_path / "_intelligence" / "_woland" / "swarm_lineage.jsonl").exists()


class _RefusingGate:
    """An anti-skill port whose verified registry refuses every subject."""

    estate = EstateName.OEWAS
    port = PortName.OEWAS_ANTI_SKILL

    def evaluate(self, stage, subject):
        return Ok(
            AntiSkillDecisionV1(
                stage=stage,
                subject_id="sha256:" + "0" * 64,
                disposition="REFUSE",
                registry_id="sha256:" + "1" * 64,
                hit_ids=("sha256:" + "2" * 64,),
                receipt_id="sha256:" + "3" * 64,
            )
        )

    def probe(self, scratch_root):
        raise AssertionError("not probed here")


def test_an_anti_skill_refusal_routes_to_refused_and_keeps_the_outcome(tmp_path: Path) -> None:
    built = _research_woland(repo_root=tmp_path)
    swarm = _research_woland(spine=replace(built.spine, anti_skill=_RefusingGate()))
    result = swarm.run_bout("Connection test objective.", "spine-refuse").unwrap()
    assert result.seal_decision.disposition == "REFUSE"
    assert result.routing_terminal == "Refused"
    assert result.outcome.status in ROUTING_TERMINAL_BY_BOUT_STATUS


def test_a_held_anti_skill_cannot_promote_an_authorized_native_bout(tmp_path: Path) -> None:
    built = _research_woland(repo_root=tmp_path)
    fixture_outcome = built.run_bout("Connection test objective.", "held-fixture").unwrap().outcome
    accepted = replace(
        fixture_outcome,
        status="AUTHORIZED",
        is_authorized=True,
        terminal_verdict="PASS_TO_MASTER",
        checker_verdict="ACCEPTED",
        checker_receipt_sha256="sha256:" + "1" * 64,
        authorization_evidence="CHECKER_VERDICT_ONLY_NO_CARRIER_DECLARED",
    )
    swarm = _research_woland(spine=replace(
        built.spine, bout=_ReplayBout(accepted), anti_skill=_ClearDispatchHoldSealGate()
    ))
    result = swarm.run_bout("Connection test objective.", "held-live", fixture_mode=False).unwrap()
    assert result.outcome.status == "AUTHORIZED"  # Preserve native evidence.
    assert result.seal_decision.disposition == "HOLD"
    assert result.routing_terminal == "RequiresLift"
    assert any(r.code == "ANTI_SKILL_CLEARANCE_MISSING" for r in result.estate_residuals)

    class UnboundClearGate:
        estate = EstateName.OEWAS
        port = PortName.OEWAS_ANTI_SKILL

        def evaluate(self, stage, subject):
            if stage == "PRE_DISPATCH":
                return _ClearDispatchHoldSealGate().evaluate(stage, subject)
            return Ok(AntiSkillDecisionV1(
                stage=stage, subject_id="sha256:" + "0" * 64,
                disposition="CLEAR", registry_id="", hit_ids=(), receipt_id="",
            ))

    unbound = _research_woland(
        spine=replace(built.spine, bout=_ReplayBout(accepted), anti_skill=UnboundClearGate())
    )
    unbound_result = unbound.run_bout(
        "Connection test objective.", "unbound-clear", fixture_mode=False
    ).unwrap()
    assert unbound_result.routing_terminal == "RequiresLift"


@pytest.mark.parametrize(
    "defect, expected_residual",
    (
        (None, None),
        ("wrong_subject", "ANTI_SKILL_PRE_SEAL_UNBOUND"),
        ("wrong_stage", "ANTI_SKILL_PRE_SEAL_UNBOUND"),
        ("profile_drift", "ANTI_SKILL_PROFILE_DRIFT"),
        ("registry_drift", "ANTI_SKILL_PROFILE_DRIFT"),
        ("finding", "ANTI_SKILL_CLEARANCE_MISSING"),
        ("untyped", "ANTI_SKILL_PRE_SEAL_INVALID"),
        ("raised", "ANTI_SKILL_PRE_SEAL_FAILED"),
    ),
)
def test_preseal_clear_must_bind_subject_and_dispatch_profile(
    tmp_path: Path, defect: str | None, expected_residual: str | None
) -> None:
    built = _research_woland(repo_root=tmp_path)
    fixture = built.run_bout("Connection test objective.", "seal-fixture").unwrap().outcome
    accepted = replace(
        fixture,
        status="AUTHORIZED",
        is_authorized=True,
        terminal_verdict="PASS_TO_MASTER",
        checker_verdict="ACCEPTED",
        checker_receipt_sha256="sha256:" + "1" * 64,
        authorization_evidence="CHECKER_VERDICT_ONLY_NO_CARRIER_DECLARED",
    )

    class Gate:
        estate = EstateName.OEWAS
        port = PortName.OEWAS_ANTI_SKILL

        def evaluate(self, stage, subject):
            if stage == "PRE_SEAL" and defect == "raised":
                raise RuntimeError("gate unavailable")
            if stage == "PRE_SEAL" and defect == "untyped":
                return Ok(None)
            changes = {
                "wrong_subject": {"subject_id": "sha256:" + "9" * 64},
                "wrong_stage": {"stage": "PRE_DISPATCH"},
                "profile_drift": {"activation_profile_digest": "sha256:" + "8" * 64},
                "registry_drift": {"registry_id": "sha256:" + "7" * 64},
                "finding": {"disposition": "FINDING"},
            }.get(defect if stage == "PRE_SEAL" else None, {})
            fields = {
                "stage": stage,
                "subject_id": subject["subject_id"],
                "disposition": "CLEAR",
                "registry_id": "sha256:" + "1" * 64,
                "activation_profile_digest": "sha256:" + "2" * 64,
                "hit_ids": (),
                "receipt_id": "sha256:" + "3" * 64,
            }
            fields.update(changes)
            return Ok(AntiSkillDecisionV1(**fields))

    swarm = _research_woland(spine=replace(built.spine, bout=_ReplayBout(accepted), anti_skill=Gate()))
    result = swarm.run_bout("Connection test objective.", "seal-live", fixture_mode=False).unwrap()
    assert result.dispatch_decision is not None
    assert result.dispatch_decision.stage == "PRE_DISPATCH"
    assert result.routing_terminal == ("CheckPassed" if defect is None else "RequiresLift")
    if expected_residual is not None:
        assert expected_residual in {item.code for item in result.estate_residuals}


def test_a_non_object_catalog_is_refused_not_raised(tmp_path: Path) -> None:
    catalog = PharmacyCatalogRepository.catalog_path(tmp_path)
    catalog.parent.mkdir(parents=True)
    catalog.write_text("[]", encoding="utf-8")
    spine = build_woland_spine(tmp_path)
    refused = spine.immune.admitted_guidance()
    assert refused.is_err and refused.unwrap_err().code == "OEEIS_CATALOG_UNREADABLE"


def test_envelope_publish_falls_back_when_hard_links_are_unsupported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from omega_engine_woland.infrastructure.estates import envelope_store

    def no_links(*_args, **_kwargs):
        raise OSError("hard links unsupported")

    monkeypatch.setattr(envelope_store.os, "link", no_links)
    path = tmp_path / "e.json"
    assert envelope_store._write_once(path, b"a").is_ok
    assert envelope_store._write_once(path, b"a").is_ok
    assert envelope_store._write_once(path, b"b").unwrap_err().code == "ENVELOPE_CONFLICT"
    assert path.read_bytes() == b"a"
    assert sorted(item.name for item in tmp_path.iterdir()) == ["e.json"]
