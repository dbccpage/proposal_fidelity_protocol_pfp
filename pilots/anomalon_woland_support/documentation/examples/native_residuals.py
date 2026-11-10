"""Two public finite tasks through native consumers; no model/provider calls.

Run as a module from the repository. The inner bout is an explicitly labeled
fixture, not an IDE swarm or independent mathematical endorsement.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

from omega_engine_applications.wdp_products.kernel.adapter import (
    WdpCertificateChecker, declare_pilot_agent_loop_arena, pilot_agent_loop_certificate,
)
from omega_engine_applications.wdp_products.p1_abstention_governor.adapter import WdpAbstentionGovernor
from omega_engine_applications.wdp_products.p1_abstention_governor.contracts import GovernorReport
from omega_engine_operating_system.adapters.rust_host import RustSymbolGameHost
from omega_engine_woland.domain.swarm_models import ResearchTaskContractV1
from omega_engine_woland.runtime import build_woland_swarm
from omega_engine_woland.use_cases.base_swarm.specializations import RESEARCH_PROFILE_V01
from omega_engine_woland.use_cases.base_swarm.woland_swarm import OmegaEngineWolandSwarm


def exercise(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    swarm = build_woland_swarm(OmegaEngineWolandSwarm,
        specialization=RESEARCH_PROFILE_V01, repo_root=output)
    captures = []

    def capture(observed):
        captures.append({"args": list(observed["args"]), "exit_code": observed["exit_code"],
            "binary_sha256": sha256(Path(observed["args"][0]).read_bytes()).hexdigest(),
            **{key.removesuffix("_bytes")+"_hex": observed[key].hex()
               for key in ("stdin_bytes", "stdout_bytes", "stderr_bytes")}})

    governor = WdpAbstentionGovernor(WdpCertificateChecker(RustSymbolGameHost(process_observer=capture)))
    outcomes = []
    for index in (1, 2):
        task = f"woland-native-residual-public-{index}"
        carrier = {"vertices": ["a", "b"], "edges": [["a", "b"], ["b", "a"]],
            "matrices": [[["1", str(index-1)], ["0", "1"]], [["1", "0"], ["0", "1"]]],
            "cycle": [0, 1], "edge_threshold": "1", "cycle_threshold": "0"}
        contract = ResearchTaskContractV1(task, f"Evaluate supplied finite cochain/path number {index}; no global theorem.",
            "flat_rational_cochain_and_2x2_closed_path", "Reading_L", 8, "2026-10-16T00:00:00Z")
        result = swarm.run_research_envelope(contract, x_vector=[Fraction(index)],
            coboundary_d0=[[Fraction(2-index)]], coboundary_d1=[], lggr_carrier=carrier,
            local_evaluators={}, global_evaluator=0, fixture_mode=True, output_dir=str(output/task))
        if not result.is_ok:
            raise RuntimeError(result.error)
        envelope = result.value
        expected_phi1 = 0 if index == 1 else 2
        expected_delta = 0 if index == 1 else -1
        if envelope.coda_evaluation.phi1 != expected_phi1:
            raise RuntimeError(f"phi1 {envelope.coda_evaluation.phi1} != {expected_phi1}")
        if envelope.lggr_gluing.gluing_defect_delta != expected_delta:
            raise RuntimeError(
                f"gluing defect {envelope.lggr_gluing.gluing_defect_delta} != {expected_delta}"
            )
        model = declare_pilot_agent_loop_arena()
        model['task_id'] = task
        certificate = pilot_agent_loop_certificate(model)
        certificate['task_id'] = task
        report = governor.report(model, certificate, str(4-index), task_admits_impossibility=False)
        if not isinstance(report, GovernorReport):
            raise RuntimeError(report)
        expected_label = 'ResolvedWithinBudget' if index == 1 else 'Exhausted'
        if report.label.value != expected_label:
            raise RuntimeError(f"governor label {report.label.value} != {expected_label}")
        outcomes.append({"task": task, "envelope": envelope.to_dict(), "application": report.model_dump(mode='json')})
    bindings = [item['envelope']['coda_evaluation']['native_evidence']['binding'] for item in outcomes]
    if bindings[0]['source_id'] == bindings[1]['source_id']:
        raise RuntimeError("native consumers reused one source_id")
    if bindings[0]['candidate_id'] == bindings[1]['candidate_id']:
        raise RuntimeError("native consumers reused one candidate_id")
    result = {"schema_version": "woland.native-residual-example.v1", "tasks": outcomes,
        "application_native_captures": captures, "external_provider_dispatches": 0,
        "inner_bout_mode": "fixture; no model participation or authority", "authority_effect": "None"}
    (output/'results.json').write_text(json.dumps(result,default=str,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return {"status": "TWO_NATIVE_CONSUMERS_EXECUTED", "tasks": [x['task'] for x in outcomes],
        "results": str(output/'results.json'), "application_captures": len(captures),
        "external_provider_dispatches": 0, "authority_effect": "None"}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New output directory; never overwrites a run')
    print(json.dumps(exercise(parser.parse_args().output.resolve())))
