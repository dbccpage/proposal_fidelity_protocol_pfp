"""Replay four falsifiers against the Woland gate as audited for Paper 009.

Paper 009's appendix applies the paper's own review protocol to the Woland
terminal gate. Each falsifier fixes an input, states the status a sound gate
must give, and records the status the audited code gives. This script replays
them on the audited commit: it extracts the needed packages with `git archive`
into a temporary directory and calls single act functions with a stub runtime
that has no emitters and no model port, so nothing is written and no model is
called. The package roots, which import the whole engine eagerly, are replaced
by bare namespace packages so only the modules under test run.

Usage, from the series directory:

    py -3.12 tools/replay_woland_gate_falsifiers.py            # print JSON
    py -3.12 tools/replay_woland_gate_falsifiers.py --write    # update the record
    py -3.12 tools/replay_woland_gate_falsifiers.py --check    # compare with it
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import io
import json
import subprocess
import sys
import tarfile
import tempfile
import types
from pathlib import Path

SERIES = Path(__file__).resolve().parents[1]
RECORD = SERIES / "verification" / "woland_gate_falsifiers.json"
AUDITED = "30609de2c3928238715375a9bac608256fa381d8"
C012_GATE = ("omega_engine_projects/mssn_sn_symgam/challenges/b_cohomology/"
             "c012_cellular_sheaf_h0_h1/governance/woland_gate.py")
PATHS = ("omega_engine/__init__.py", "omega_engine/kernel", "omega_engine_governance/__init__.py",
         "omega_engine_governance/contracts", "omega_engine_governance/domain/ingress",
         "omega_engine_woland", "omega_engine_woland", C012_GATE)
BARE = ("omega_engine_governance.domain", "omega_engine_woland", "omega_engine_woland.use_cases",
        "omega_engine_woland.infrastructure")


def sha(data: bytes | str) -> str:
    raw = data.encode("utf-8") if isinstance(data, str) else data
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def extract(dest: Path) -> None:
    root = subprocess.run(["git", "-C", str(SERIES), "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True, check=True).stdout.strip()
    tar = subprocess.run(["git", "-C", root, "archive", "--format=tar", AUDITED, *PATHS],
                         capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(tar)) as archive:
        archive.extractall(dest, filter="data")


def falsifiers(dest: Path) -> list[dict]:
    for name in BARE:
        module = types.ModuleType(name)
        module.__path__ = [str(dest.joinpath(*name.split(".")))]
        sys.modules[name] = module
    result_mod = importlib.import_module("omega_engine_operations.domain.rop.result")
    ports = importlib.import_module("omega_engine_woland.application.ports")
    run_swarm = importlib.import_module("omega_engine_woland.application.run_swarm")
    domain = importlib.import_module("omega_engine_woland.domain")
    network_mod = importlib.import_module("omega_engine_woland.domain.network")
    acts = importlib.import_module("omega_engine_woland.use_cases.act_helpers")
    if not Path(acts.__file__).resolve().is_relative_to(dest.resolve()):
        raise RuntimeError("act_helpers was not imported from the audited commit")

    runtime, network = run_swarm.SwarmRuntimeV1, network_mod.Network

    class Seat:
        """A critic seat that returns one fixed reply and asks to kill the candidate."""

        def __init__(self, text: str) -> None:
            self.text = text

        def execute_turn(self, request):
            return result_mod.Ok(ports.SeatTurnReplyV1(
                reply_text=self.text, machine_fields={"DISPOSITION": "KILL"}, raw_bytes=self.text.encode("utf-8")))

    def candidate(content: bytes):
        return domain.CandidateProposalV1(
            producer_agent_id="seat_azazello", work_packet_id=sha("packet"), artifact_refs=(sha(content),),
            prediction_receipt_id=sha("prediction"), nonclaims=("proposal only",))

    triangle = network(nodes=(0, 1, 2), edges=((0, 1), (1, 2), (2, 0)), faces=())
    cochain = {(0, 1): 1.0, (1, 2): 1.0, (2, 0): 1.0}
    out = []

    # F1. Input replacement: Act II, Act IV, Act II on the lifted carrier, Act VII.
    phi1, gamma2, *_ = acts.execute_act2_obstruction_identification(triangle, cochain).unwrap()
    fired, lifted, replaced, _t, _n = acts.execute_act4_gauge_break(
        runtime(), triangle, cochain, (), [{"content": "x"}], phi1, gamma2).unwrap()
    phi1_after, gamma2_after, *_ = acts.execute_act2_obstruction_identification(lifted, replaced).unwrap()
    status, _s, _p, authorized, _n = acts.execute_act7_authorization_gate(
        None, "f1", [candidate(b"x")], [], {}, phi1_after, gamma2_after).unwrap()
    out.append({
        "id": "F1", "defect": "input replacement",
        "input": "triangle, cochain (1, 1, 1) with cycle sum 3; default scorer; one candidate; no critique",
        "expected": "not AUTHORIZED: no potential removes a cycle sum of 3",
        "observed": status, "is_authorized": authorized,
        "trace": {"act2_before": [phi1, gamma2], "act4_fired": fired, "cochain_after_act4": sorted(set(replaced.values())),
                  "act2_after": [phi1_after, gamma2_after]},
    })

    # F2. Keyword adjudication: a counterexample without the keywords, and a negated keyword.
    for fid, text, must_block in (
        ("F2a", "Counterexample: the residual (0,0,3) has cycle sum 3, so the claimed repair is false.", True),
        ("F2b", "No defect found; the certificate checks.", False),
    ):
        payload = b"potential f=(0,1,2)"
        cand = candidate(payload)
        surviving, _d, _r, critiques, _c, _res, _n = acts.execute_act5_independent_witness(
            runtime(seat_port=Seat(text), max_critique_rounds=1), "f2", "repair", triangle, [cand], [],
            candidate_payloads={cand.candidate_id: payload}).unwrap()
        out.append({
            "id": fid, "defect": "keyword adjudication", "input": f"critic reply: {text!r}",
            "expected": "blocking" if must_block else "not blocking",
            "observed": "blocking" if critiques[0].blocking else "not blocking",
            "candidate_survives": bool(surviving),
        })

    # F3. Phantom evidence references in Act VII.
    status3, _s, proposal, _a, narrative = acts.execute_act7_authorization_gate(
        None, "f3", [candidate(b"x")], [], {}, 1.0, 0.0, dual_witness={"(0, 1)": "1"}, exact_phi1="1").unwrap()
    receipt = narrative.get("obstruction_non_vanishing_receipt", {})
    refs = list(proposal.evidence_refs)
    out.append({
        "id": "F3", "defect": "phantom evidence references",
        "input": "Act VII with no critique and a dual witness of 1 on edge (0, 1) only, which is not a circulation",
        "expected": "each evidence reference is the digest of stored bytes; receipt properties are computed",
        "observed": {
            "first_reference_is_sha256_of_run_key": refs[0] == sha("f3"),
            "receipt_annihilates_coboundary": receipt.get("annihilates_coboundary"),
            "receipt_norm_bounded": receipt.get("norm_bounded"),
        },
        "status": status3,
    })

    # F4. Templated challenge-gate receipts (the C012 copy of the gate).
    spec = importlib.util.spec_from_file_location("c012_woland_gate", dest / C012_GATE)
    gate = importlib.util.module_from_spec(spec)
    sys.modules["c012_woland_gate"] = gate
    spec.loader.exec_module(gate)
    novella = gate.generate_c011_novella("f4", "REFUSE", 0, 0, 5, 3.0, 1.0, {})
    steps = gate.generate_c011_dda_steps("f4", "REFUSE", 0, 5)
    out.append({
        "id": "F4", "defect": "templated receipts",
        "input": "C012 gate: verdict REFUSE, 0 cases, 0 passed, 5 defects",
        "expected": "no statement of repair, agreement or budget that the inputs do not support",
        "observed": {
            "novella_states_full_agreement": "100% concordance across all cases" in novella,
            "novella_states_budget_respected": "Total inference budget respected" in novella,
            "novella_default_claim_46_cases": "zero duality gap on all 46 judge cases" in novella,
            "novella_names_challenge_C011": "C011" in novella,
            "step_E_payload": [s["payload"] for s in steps if s["letter"] == "E"],
            "step_D_payload": [s["payload"] for s in steps if s["letter"] == "D"],
        },
    })
    return out


def replay() -> dict:
    sys.dont_write_bytecode = True
    saved_path, saved_modules = list(sys.path), dict(sys.modules)
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp)
        extract(dest)
        sys.path.insert(0, str(dest))
        try:
            rows = falsifiers(dest)
        finally:
            sys.path[:] = saved_path
            for name in set(sys.modules) - set(saved_modules):
                del sys.modules[name]
    return {
        "scope": "Four falsifiers replayed on the Woland gate at the audited commit; single act functions, "
                 "stub runtime without emitters or model port; no model is called and nothing is written.",
        "audited_commit": AUDITED,
        "falsifiers": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="write verification/woland_gate_falsifiers.json")
    mode.add_argument("--check", action="store_true", help="compare with verification/woland_gate_falsifiers.json")
    args = parser.parse_args()
    text = json.dumps(replay(), indent=2, ensure_ascii=False) + "\n"
    if args.write:
        RECORD.write_bytes(text.encode("utf-8"))
        print(f"wrote {RECORD.relative_to(SERIES).as_posix()}")
        return 0
    if args.check:
        if RECORD.read_bytes() != text.encode("utf-8"):
            print("woland_gate_falsifiers.json differs from the replay", file=sys.stderr)
            return 1
        print("woland_gate_falsifiers.json matches the replay")
        return 0
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
