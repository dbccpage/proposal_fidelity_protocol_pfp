"""Wave 4 head-to-head parity harness for PFP vs. Anomalon EIS caller feedback.

Runs four deterministic offline probes against bounded synthetic packets and
compares the emitted metric vectors against an external target repository once
its matching ``screen_caller_turn`` seam is present.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from adversary.domain.evidence import CandidateCheckV1, CheckerVerdict
from adversary.domain.ports import CandidateCheckerPort
from adversary.domain.providers.types import CandidateRequest, CandidateResponse
from adversary.infrastructure.native import DefaultNativeOperationPort
from adversary.profile.profile_loader import load_adversary_council_profile
from adversary.runtime import build_adversary_runtime
from adversary.stage.domain import WorkPacketV1
from adversary.stage.infrastructure.default_adapters import (
    FileCemeteryAdapter,
    FixtureAgentTurnAdapter,
)
from adversary.use_cases import act_helpers
from adversary.use_cases.bout_service import execute_7act_adversary_bout
from operations.domain.rop.result import Ok

from eis.domain.external_admission import HumanAntiSkillAdmissionDecisionV1
from eis.domain.pharmacy_models import LearningEvidencePreimageV1
from eis.domain.pharmacy_search import rule_content_bytes
from eis.domain.pharmacy_seeder import record_reproduced_failure
from eis.use_cases.antibody_admission import admit_antibody_by_operator
from pciv.domain.lamarckian import (
    CochainResidualV1,
    LamarckianMutationReceiptV1,
    ReproducedFailureCaseV1,
)
from pciv.domain.models import ProtectedSpanV1
from pciv.use_cases.custody import ensure_caller_prompt_genome
from pciv.use_cases.immunity import resolve_civilization_immune_store
from pciv.use_cases.lamarckian_loop import (
    LamarckianReceiptStore,
    load_active_lineage_antibodies,
    spawn_antibody_constrained_child,
    verify_lineage_cure,
)
from pciv.use_cases.transitive_immunity import FixedPointLineageTaintEngineV1
from pfp.domain.value_objects.seat_turn import SeatTurnReplyV1
from pfp.infrastructure.task_turn import PfpTurnRefusal, complete_task_turn

from . import caller_feedback as cf

host_danger = cf.host_danger


def _sha256_ref(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


class _Wave4AcceptingHost:
    def execute_host_request(self, _request_bytes: bytes):
        return Ok(b'{"status":"ACCEPTED"}')


class _Wave4WildGateway:
    def complete(self, request, **_options):
        public = json.loads(request.user)
        payload = {
            **{k: public[k] for k in ("task_id", "attempt_id", "input_sha256")},
            "answer": "def bad():\n    return WAVE4_UNSAFE_TOKEN\n",
        }
        return (
            CandidateResponse(
                json.dumps(payload),
                "wave4-model",
                "openrouter",
                cost_usd=None,
                transport="live",
            ),
            None,
        )


@dataclass(frozen=True)
class _Wave4RejectingChecker(CandidateCheckerPort):
    pattern_marker: str = "WAVE4_UNSAFE_TOKEN"

    def check_candidate(
        self,
        *,
        run_key: str,
        objective: str,
        candidate_id: str,
        candidate_bytes: bytes,
        carrier_context: Any = None,
    ):
        _ = (run_key, objective, carrier_context)
        receipt_bytes = f'{{"passed":false,"reason":"{self.pattern_marker} rejected"}}'.encode()
        return Ok(
            CandidateCheckV1(
                verdict=CheckerVerdict.REJECTED,
                candidate_id=candidate_id,
                candidate_content_sha256=_sha256_ref(candidate_bytes),
                checker_id="host.public_smoke",
                checker_receipt_sha256=_sha256_ref(receipt_bytes),
                checker_receipt_bytes=receipt_bytes,
                reason=f"{self.pattern_marker} rejected",
            )
        )


def _seed_admitted_antibody(
    store: cf.BoundImmuneStoreV1,
    *,
    prompt_id: str,
    prompt_bytes: bytes,
    reply_bytes: bytes,
    target_pattern: str,
    positive_fixture: str,
    scope_level: str,
    admission_scope: str,
    decision_id: str,
) -> str:
    preimage = LearningEvidencePreimageV1(
        prompt_id=prompt_id,
        prompt_utf8_bytes=prompt_bytes,
        candidate_reply_bytes=reply_bytes,
        failure_class="Wave4Defect",
        failed_predicates=("wave4_guard",),
        checker_id="host.public_smoke",
        checker_output_bytes=b'{"passed":false,"reason":"wave4 defect"}',
    )
    ab = record_reproduced_failure(
        prompt_id=prompt_id,
        preimage=preimage,
        target_pattern=target_pattern,
        positive_fixture=positive_fixture,
        negative_fixture=reply_bytes.decode("utf-8"),
        run_id=f"run_{decision_id}",
        task_id=f"task_{decision_id}",
        scope_level=scope_level,
        producer_actor="proposer_seat",
        repository=store.catalog,
        registry=store.registry,
    )
    saved_rec = store.catalog.load_catalog()["antibodies"][ab.antibody_id]
    rule_digest = "sha256:" + hashlib.sha256(rule_content_bytes(saved_rec)).hexdigest()
    admit_antibody_by_operator(
        ab.antibody_id,
        HumanAntiSkillAdmissionDecisionV1(
            decision_id=decision_id,
            issuer="human_reviewer_1",
            rule_bytes_sha256=rule_digest,
            scope=admission_scope,
            receipt_sha256=_sha256_ref(decision_id.encode("utf-8")),
        ),
        catalog=store.catalog,
        self_panel=(positive_fixture,),
    )
    return ab.antibody_id


def _run_scenario_1_act3_and_wild_hold(root: Path) -> dict[str, Any]:
    store = resolve_civilization_immune_store(None, root, read_only=False)
    seed_prompt = b"Wave 4 seed prompt."
    seed_genome = ensure_caller_prompt_genome(seed_prompt, {"domain": "wave4.shared"})
    _seed_admitted_antibody(
        store,
        prompt_id=seed_genome.prompt_id,
        prompt_bytes=seed_prompt,
        reply_bytes=b"WAVE4_UNSAFE_TOKEN",
        target_pattern="WAVE4_UNSAFE_TOKEN",
        positive_fixture="def clean_wave4():\n    return 1\n",
        scope_level="civilization",
        admission_scope="global",
        decision_id="dec_w4_s1",
    )

    spy_calls: list[tuple[str, str]] = []
    real_screen = cf.screen_caller_turn

    def _spied_screen(req: cf.ImmuneScreenRequestV1, s: cf.BoundImmuneStoreV1, *, self_panel=None):
        verdict = real_screen(req, s, self_panel=self_panel)
        spy_calls.append((str(s.catalog.catalog_file), verdict.disposition))
        return verdict

    orig_cf = cf.screen_caller_turn
    orig_act = act_helpers.screen_caller_turn
    cf.screen_caller_turn = _spied_screen
    act_helpers.screen_caller_turn = _spied_screen
    wild_disposition = "NOT_RAISED"
    try:
        failing_judge = (("host.public_smoke", lambda _c, _a: (False, "WAVE4_UNSAFE_TOKEN rejected")),)
        try:
            complete_task_turn(
                _Wave4WildGateway(),
                CandidateRequest("Return clean implementation.", "Compute result."),
                task_id="wave4_wild",
                attempt_id="w4_01",
                checker_id="host.public_smoke",
                judges=failing_judge,
                require_checker=True,
                immune_store=store,
            )
        except PfpTurnRefusal as exc:
            wild_disposition = exc.checked["immune_verdict"]["disposition"]

        _, _, profile, _, _ = load_adversary_council_profile()
        rt = build_adversary_runtime(
            output_dir=root / "_intelligence",
            fixture_mode=False,
            host=_Wave4AcceptingHost(),
        )
        bad_code = "def swarm_bad():\n    return WAVE4_UNSAFE_TOKEN\n"
        turn_adapter = FixtureAgentTurnAdapter(
            canned_replies={
                ("act2_panel_debate", "seat_gauge_breaker"): SeatTurnReplyV1(
                    reply_text=bad_code,
                    machine_fields={"AUTHORITY_EFFECT": "None"},
                    residual_colour="Open",
                    authority_effect="None",
                    raw_bytes=bad_code.encode("utf-8"),
                )
            }
        )
        object.__setattr__(rt, "seat_port", turn_adapter)
        packet = WorkPacketV1(
            task_key="wave4_bout_s1",
            scene_id="act1_perception",
            objective="Return clean wave4 code",
            input_artifact_refs=(),
            acceptance_criteria=("Zero unsafe tokens",),
            budget_units=20,
            evaluator_epoch_id=_sha256_ref(b"wave4_epoch"),
        )
        bout_res = execute_7act_adversary_bout(
            profile,
            rt,
            packet,
            output_dir=root / "_intelligence" / "_adversary",
            repo_root=root,
            candidate_checker=_Wave4RejectingChecker(),
            immune_store=store,
            native_support=DefaultNativeOperationPort(),
        )
    finally:
        cf.screen_caller_turn = orig_cf
        act_helpers.screen_caller_turn = orig_act

    critique_calls = sum(1 for r in turn_adapter.invocation_log if r.seat_id == "seat_defect_hunter")
    return {
        "wild_disposition": wild_disposition,
        "bout_refusal_code": bout_res.unwrap_err().code if bout_res.is_err else "OK",
        "act4_critique_calls_when_held": critique_calls,
        "shared_screen_invocations": len(spy_calls),
        "single_catalog_shared": len({c[0] for c in spy_calls}) == 1,
    }


def _run_scenario_2_self_panel_gate(root: Path) -> dict[str, Any]:
    store = resolve_civilization_immune_store(None, root, read_only=False)
    owner_prompt = b"System: clean helper."
    owner_genome = ensure_caller_prompt_genome(owner_prompt, {"domain": "wave4.self"})
    clean_panel = ("def exact_sum(a: int, b: int) -> int:\n    return a + b\n",)
    preimage = LearningEvidencePreimageV1(
        prompt_id=owner_genome.prompt_id,
        prompt_utf8_bytes=owner_prompt,
        candidate_reply_bytes=clean_panel[0].encode("utf-8"),
        failure_class="AutoimmuneTest",
        failed_predicates=("broad_match",),
        checker_id="host.public_smoke",
        checker_output_bytes=b'{"passed":false,"reason":"broad pattern"}',
    )
    ab = record_reproduced_failure(
        prompt_id=owner_genome.prompt_id,
        preimage=preimage,
        target_pattern="exact_sum",
        positive_fixture="def other():\n    return 0\n",
        negative_fixture=clean_panel[0],
        run_id="run_w4_auto",
        task_id="task_w4_auto",
        producer_actor="proposer_seat",
        repository=store.catalog,
        registry=store.registry,
    )
    saved_rec = store.catalog.load_catalog()["antibodies"][ab.antibody_id]
    rule_digest = "sha256:" + hashlib.sha256(rule_content_bytes(saved_rec)).hexdigest()
    autoimmune_refused = False
    try:
        admit_antibody_by_operator(
            ab.antibody_id,
            HumanAntiSkillAdmissionDecisionV1(
                decision_id="dec_w4_auto",
                issuer="human_reviewer_1",
                rule_bytes_sha256=rule_digest,
                scope="global",
                receipt_sha256=_sha256_ref(b"dec_w4_auto"),
            ),
            catalog=store.catalog,
            self_panel=clean_panel,
        )
    except ValueError as exc:
        autoimmune_refused = "AUTOIMMUNE_RULE_REFUSED" in str(exc)

    stranger = ensure_caller_prompt_genome(b"Stranger prompt.", {"domain": "wave4.stranger"})
    forced = store.catalog.load_catalog()
    forced["antibodies"][ab.antibody_id]["pharmacy_status"] = "admitted"
    forced["antibodies"][ab.antibody_id]["revoked"] = False
    forced["antibodies"][ab.antibody_id].pop("thymus_receipt_sha256", None)
    forced.get("managed_projections", {}).pop(ab.antibody_id, None)
    store.catalog.catalog_file.write_text(json.dumps(forced), encoding="utf-8")

    verdict_clean = cf.screen_caller_turn(
        cf.ImmuneScreenRequestV1(
            lineage=cf.CallerLineageContextV1(prompt_id=stranger.prompt_id),
            prompt_utf8_bytes=b"Stranger prompt.",
            candidate_reply_bytes=clean_panel[0].encode("utf-8"),
            signal2_danger=None,
        ),
        store,
        self_panel=clean_panel,
    )
    verdict_forced = cf.screen_caller_turn(
        cf.ImmuneScreenRequestV1(
            lineage=cf.CallerLineageContextV1(prompt_id=stranger.prompt_id),
            prompt_utf8_bytes=b"Stranger prompt.",
            candidate_reply_bytes=clean_panel[0].encode("utf-8"),
            signal2_danger=host_danger("PUBLIC_CHECK_FAILED", "host.public_smoke", "unrelated danger"),
        ),
        store,
        self_panel=clean_panel,
    )
    return {
        "autoimmune_admission_refused": autoimmune_refused,
        "clean_panel_false_positives": len(verdict_forced.fired_antibody_ids),
        "stranger_disposition": verdict_clean.disposition,
    }


def _run_scenario_3_relapse_vs_cure(root: Path) -> dict[str, Any]:
    store = resolve_civilization_immune_store(None, root, read_only=False)
    parent_bytes = b"System: Core Rule.\nUser: Return clean ratio."
    span = ProtectedSpanV1(name="system_framing", start_byte=0, end_byte=18)
    parent_genome = ensure_caller_prompt_genome(
        parent_bytes,
        {"domain": "wave4.cure"},
        protected_spans=(span,),
    )
    failing_reply = b"def ratio():\n    return float(0.25)  # UNSAFE_FLOAT_CAST\n"
    ab_id = _seed_admitted_antibody(
        store,
        prompt_id=parent_genome.prompt_id,
        prompt_bytes=parent_bytes,
        reply_bytes=failing_reply,
        target_pattern=r"UNSAFE_FLOAT_CAST|float\(",
        positive_fixture="from fractions import Fraction\ndef ratio():\n    return Fraction(1, 4)\n",
        scope_level="prompt_line",
        admission_scope="prompt_line",
        decision_id="dec_w4_s3",
    )
    witness_sha = hashlib.sha256(b"w4_witness_float").hexdigest()
    child_genome, child_bytes, receipt = spawn_antibody_constrained_child(
        parent_genome=parent_genome,
        parent_prompt_bytes=parent_bytes,
        antibody=store.catalog.load_catalog()["antibodies"][ab_id],
        falsification_witness_sha256=witness_sha,
        cochain_residual=CochainResidualV1("1/2", "0/1", "0/1"),
        receipt_store=store.receipt_store,
    )
    case = ReproducedFailureCaseV1(
        case_id="case_w4_relapse",
        prompt_utf8_bytes=parent_bytes,
        parent_failing_reply_bytes=failing_reply,
        failure_class="Wave4Defect",
        witness_sha256=witness_sha,
    )
    cemetery = FileCemeteryAdapter(root / "cemetery")
    taint_relapse = FixedPointLineageTaintEngineV1()
    relapsed = verify_lineage_cure(
        parent_genome=parent_genome,
        child_genome=child_genome,
        parent_prompt_bytes=parent_bytes,
        child_prompt_bytes=child_bytes,
        mutation_receipt=receipt,
        reproducing_case=case,
        child_reply_bytes=failing_reply,
        child_host_danger=host_danger("PUBLIC_CHECK_FAILED", "host.public_smoke", "relapse"),
        held_out_passed=False,
        store=store,
        cemetery=cemetery,
        taint_engine=taint_relapse,
    )
    taint_cured = FixedPointLineageTaintEngineV1()
    cured = verify_lineage_cure(
        parent_genome=parent_genome,
        child_genome=child_genome,
        parent_prompt_bytes=parent_bytes,
        child_prompt_bytes=child_bytes,
        mutation_receipt=receipt,
        reproducing_case=case,
        child_reply_bytes=b"from fractions import Fraction\ndef ratio():\n    return Fraction(1, 4)\n",
        child_host_danger=None,
        held_out_passed=True,
        store=store,
        cemetery=cemetery,
        taint_engine=taint_cured,
    )
    return {
        "relapsed_status": relapsed.cure_status,
        "relapsed_tainted": taint_relapse.is_tainted(child_genome.prompt_id),
        "relapsed_headstones": len(list((root / "cemetery").glob("*.headstone.json"))),
        "cured_status": cured.cure_status,
        "cured_tainted": taint_cured.is_tainted(child_genome.prompt_id),
    }


def _run_scenario_4_12hop_attenuation(root: Path) -> dict[str, Any]:
    store = resolve_civilization_immune_store(None, root, read_only=False)
    seed_prompt = b"Hop zero prompt."
    g0 = ensure_caller_prompt_genome(seed_prompt, {"domain": "wave4.hops"})
    ab_id = _seed_admitted_antibody(
        store,
        prompt_id=g0.prompt_id,
        prompt_bytes=seed_prompt,
        reply_bytes=b"HOP_DEFECT",
        target_pattern="HOP_DEFECT",
        positive_fixture="def ok():\n    return 1\n",
        scope_level="prompt_line",
        admission_scope="prompt_line",
        decision_id="dec_w4_s4",
    )
    hop_store = LamarckianReceiptStore(root / "eis" / "antibodies" / "hops_12.jsonl")
    witness_sha = hashlib.sha256(b"w4_hop_witness").hexdigest()
    genomes = [g0]
    for gen in range(1, 13):
        prev_g = genomes[-1]
        next_g = ensure_caller_prompt_genome(
            f"Hop {gen} prompt.".encode(),
            {"domain": "wave4.hops", "generation": gen},
        )
        r = LamarckianMutationReceiptV1.create(
            parent_genome_id=prev_g.content_digest,
            child_genome_id=next_g.content_digest,
            falsification_witness_sha256=witness_sha,
            cochain_residual=CochainResidualV1("1/2", "0/1", "0/1"),
            antibody_id=ab_id if gen == 1 else f"{ab_id}_relay_{gen}",
            hop_distance=1,
        )
        hop_store.append(r, parent_prompt_id=prev_g.prompt_id, child_prompt_id=next_g.prompt_id)
        genomes.append(next_g)

    a10, _ = load_active_lineage_antibodies(genomes[10].prompt_id, hop_store, store.catalog)
    a11, _ = load_active_lineage_antibodies(genomes[11].prompt_id, hop_store, store.catalog)
    a12, _ = load_active_lineage_antibodies(genomes[12].prompt_id, hop_store, store.catalog)
    return {
        "weights_1_to_10": {
            str(h): LamarckianMutationReceiptV1.calculate_attenuation_weight(h) for h in range(1, 11)
        },
        "active_at_hop_10": any(item["antibody_id"] == ab_id for item in a10),
        "active_at_hop_11": any(item["antibody_id"] == ab_id for item in a11),
        "active_at_hop_12": any(item["antibody_id"] == ab_id for item in a12),
    }


def run_local_wave4_probe(work_dir: Path | None = None) -> dict[str, Any]:
    """Execute the four Wave 4 parity scenarios against this repository."""
    if work_dir is not None:
        base = Path(work_dir)
        base.mkdir(parents=True, exist_ok=True)
        return {
            "schema": "pfp.wave4-parity-vector.v1",
            "authority_effect": "None",
            "scenario_1_act3_and_wild_hold": _run_scenario_1_act3_and_wild_hold(base / "s1"),
            "scenario_2_self_panel_gate": _run_scenario_2_self_panel_gate(base / "s2"),
            "scenario_3_relapse_vs_cure": _run_scenario_3_relapse_vs_cure(base / "s3"),
            "scenario_4_12hop_attenuation": _run_scenario_4_12hop_attenuation(base / "s4"),
        }
    with tempfile.TemporaryDirectory(prefix="pfp-wave4-") as scratch:
        base = Path(scratch)
        return {
            "schema": "pfp.wave4-parity-vector.v1",
            "authority_effect": "None",
            "scenario_1_act3_and_wild_hold": _run_scenario_1_act3_and_wild_hold(base / "s1"),
            "scenario_2_self_panel_gate": _run_scenario_2_self_panel_gate(base / "s2"),
            "scenario_3_relapse_vs_cure": _run_scenario_3_relapse_vs_cure(base / "s3"),
            "scenario_4_12hop_attenuation": _run_scenario_4_12hop_attenuation(base / "s4"),
        }


def compare_wave4_vectors(
    pfp_report: Mapping[str, Any],
    target_report: Mapping[str, Any],
) -> dict[str, Any]:
    """Compare two Wave 4 metric vectors across all four scenarios."""
    mismatches: list[str] = []
    sections = (
        "scenario_1_act3_and_wild_hold",
        "scenario_2_self_panel_gate",
        "scenario_3_relapse_vs_cure",
        "scenario_4_12hop_attenuation",
    )
    for section in sections:
        left = pfp_report.get(section)
        right = target_report.get(section)
        if not isinstance(left, Mapping) or not isinstance(right, Mapping):
            mismatches.append(f"{section}:missing_section")
            continue
        for key, expected_val in left.items():
            actual_val = right.get(key)
            if actual_val != expected_val:
                mismatches.append(f"{section}.{key}: pfp={expected_val!r} target={actual_val!r}")
    return {
        "schema": "pfp.wave4-parity-comparison.v1",
        "authority_effect": "None",
        "parity_status": "MATCH" if not mismatches else "MISMATCH",
        "mismatches": mismatches,
        "pfp": dict(pfp_report),
        "target": dict(target_report),
    }


def _build_remote_pythonpath(target_repo: Path) -> str:
    candidates = [
        target_repo,
        target_repo / "ops",
        target_repo / "workflows" / "wf52_finite_qm_benchmark",
        target_repo / "src",
        target_repo / "packages",
    ]
    existing = [str(p) for p in candidates if p.is_dir()]
    return os.pathsep.join(existing or [str(target_repo)])


_REMOTE_PROBE_SNIPPET = (
    "import importlib, importlib.util, json, os, pathlib, sys\n"
    "target_root = pathlib.Path(os.environ['PFP_WAVE4_TARGET_ROOT']).resolve()\n"
    "errors = []\n"
    "for mod_name in ('pfp_core.wave4_parity_harness', 'omega_engine.wave4_parity_harness'):\n"
    "    try:\n"
    "        mod = importlib.import_module(mod_name)\n"
    "        mod_file = pathlib.Path(getattr(mod, '__file__', '')).resolve()\n"
    "        if mod_file.is_relative_to(target_root):\n"
    "            print(json.dumps(mod.run_local_wave4_probe(), sort_keys=True))\n"
    "            sys.exit(0)\n"
    "    except ImportError as exc:\n"
    "        errors.append(f'{mod_name}:{exc}')\n"
    "for cf_name in ('pfp_core.caller_feedback', 'omega_engine.caller_feedback'):\n"
    "    try:\n"
    "        cf_mod = importlib.import_module(cf_name)\n"
    "        cf_file = pathlib.Path(getattr(cf_mod, '__file__', '')).resolve()\n"
    "        if cf_file.is_relative_to(target_root) and hasattr(cf_mod, 'screen_caller_turn'):\n"
    "            pkg = cf_mod.__package__ or cf_name.rsplit('.', 1)[0]\n"
    "            h_name = f'{pkg}.wave4_parity_harness'\n"
    "            spec = importlib.util.spec_from_file_location(h_name, os.environ['PFP_WAVE4_HARNESS_FILE'])\n"
    "            h_mod = importlib.util.module_from_spec(spec)\n"
    "            sys.modules[h_name] = h_mod\n"
    "            spec.loader.exec_module(h_mod)\n"
    "            print(json.dumps(h_mod.run_local_wave4_probe(), sort_keys=True))\n"
    "            sys.exit(0)\n"
    "        errors.append(f'{cf_name}:outside_target:{cf_file}')\n"
    "    except ImportError as exc:\n"
    "        errors.append(f'{cf_name}:{exc}')\n"
    "print(json.dumps({'parity_status': 'TARGET_NOT_READY', "
    "'reason': 'SCREEN_CALLER_TURN_OR_WAVE4_HARNESS_ABSENT', 'details': errors}))\n"
    "sys.exit(2)\n"
)


def compare_against_repo(
    target_repo: Path,
    *,
    python_executable: str | None = None,
) -> dict[str, Any]:
    """Compare local Wave 4 metrics against another repo checkout once its seam lands."""
    pfp_report = run_local_wave4_probe()
    repo_path = Path(target_repo)
    if not repo_path.is_dir():
        return {
            "schema": "pfp.wave4-parity-comparison.v1",
            "authority_effect": "None",
            "parity_status": "TARGET_NOT_READY",
            "reason": f"TARGET_REPO_MISSING:{repo_path}",
            "pfp": pfp_report,
        }
    env = dict(os.environ)
    env["PYTHONPATH"] = _build_remote_pythonpath(repo_path)
    env["PFP_WAVE4_TARGET_ROOT"] = str(repo_path.resolve())
    env["CORE_INTELLIGENCE_ROOT"] = str(repo_path.resolve())
    env["PFP_WAVE4_HARNESS_FILE"] = str(Path(__file__).resolve())
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["CORE_CREDENTIAL_DISCOVERY"] = "off"
    exe = python_executable or sys.executable
    proc = subprocess.run(  # noqa: S603
        [exe, "-c", _REMOTE_PROBE_SNIPPET],
        cwd=str(repo_path),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return {
            "schema": "pfp.wave4-parity-comparison.v1",
            "authority_effect": "None",
            "parity_status": "TARGET_NOT_READY",
            "reason": (proc.stdout or proc.stderr).strip(),
            "pfp": pfp_report,
        }
    target_report = json.loads(proc.stdout.strip())
    return compare_wave4_vectors(pfp_report, target_report)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for local Wave 4 probing and cross-repo parity comparisons."""
    parser = argparse.ArgumentParser(description="Wave 4 EIS caller-feedback parity harness.")
    parser.add_argument("--probe-only", action="store_true", help="Emit local Wave 4 metrics JSON.")
    parser.add_argument("--compare-repo", type=Path, help="Target repo checkout to compare against.")
    parser.add_argument("--emit-json", type=Path, help="Optional file path to write JSON report.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.compare_repo is not None:
        report = compare_against_repo(args.compare_repo)
        exit_code = 0 if report.get("parity_status") == "MATCH" else 2
    else:
        report = run_local_wave4_probe()
        exit_code = 0

    rendered = json.dumps(report, sort_keys=True, indent=2)
    if args.emit_json is not None:
        args.emit_json.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return exit_code


__all__ = [
    "compare_against_repo",
    "compare_wave4_vectors",
    "main",
    "run_local_wave4_probe",
]


if __name__ == "__main__":
    raise SystemExit(main())
