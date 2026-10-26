"""Recover a fixed historical Genesis slice and replay its actual verifier flaws.

This is byte recovery and finite harness replay, never a Genesis mathematics solver.
No provider, Lean, Cargo, or external 19L57G1 process is invoked.
"""

from __future__ import annotations

import argparse
import ast
import dataclasses
import hashlib
import json
import re
import subprocess
import sys
import types
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any

PAPER = Path(__file__).resolve().parents[1]
COMMIT = "5e5e64e441da1c357179b6979daa9f780dcc36b4"
TREE = "e955f8014523b5cab13843a94fbd1191402a63c0"
DELETION_COMMIT = "6ab48c9c1ff04ff96a12878de557d3b5d5746b82"
SOURCE_PREFIX = "omega_engine_projects/mssn_sn_symgam/challenges/k_genesis_19l57g1/"
RECOVERED_PREFIX = "docs/history_recovery/recovered_sources/"
MANIFEST_PATH = PAPER / "docs/history_recovery/recovery_manifest.json"
PINS = {
    "g01_reading_f_nonuniqueness_lean.md": "6b24aed76c44a61e458d629b4867b1e0c562395d",
    "g02_cut_census_general_formula.md": "1f7eeb72736005181ba78e07ab06b1bfc46ac11b",
    "g03_g4_finite_check_replay.md": "8c39f569b7fc68351bf36fbec23c1c89a227d28f",
    "g04_x3_first_demand_iso_invariance.md": "4dd539f5788ae17830f3af868a631e933360abb4",
    "g05_x1_decidable_demand_procedure.md": "02467ffaa43f124ebcf6fd331310d0a153b52231",
    "g06_ns10_commuting_square_closure.md": "476b4c6c818133fab972c9ab7954dd4dcc29da95",
    "g07_mu2_branch_fan_widths.md": "54f73cf0f22f8e0c28dbc458eb2dd3a975aa9a2e",
    "g08_alpha_engine_live_injection_gates.md": "871abefb51087896deecd8390ceff1bb447978fe",
    "g09_alpha_engine_python_driver_refinement.md": "15a4a00d207d56f95c6dd2d3a1b3999ff0463330",
    "g10_alpha_engine_symbol_game_proposer.md": "f8d27615ff6ba2102d1a8dd7f06165fa7bcf2f08",
    "g11_m114_solver_adapter_wiring.md": "1a50efd5186cc4d87ba0a237b79bc97ddcabe15f",
    "g12_parked_audit_prop_wrappers.md": "f210ed70ccb1eeff4bf588b1a5b31e3b4b58bd1b",
    "g13_genesis_crosswalk_native_ports.md": "d510bcd27706bbb5819c3fcee758c005eca6f93b",
    "g14_ob1_endogenous_demand_generator_search.md": "79572ee1576d51c33a4d7bb7da457c09cacba40f",
    "g15_unboundedness_engine_driver.md": "aef7528dcc73573d83a95a4b556a2df51f6fe9bb",
    "g16_tied_minima_census_beyond_bounds.md": "2f33e9478585be9df1e588d58e6f5d7dabb679e1",
    "g17_second_derivation_challenges_3_5.md": "68ea6c34fda732ed3c1ad40f656e95c637d30e86",
    "g18_x6_definability_census_rows.md": "9a7ebefda6eca7d0e1f52c1a2eae6023e8b0ff37",
    "g19_ns5_proof_relevant_cell_calculus.md": "eb999cfff2479a54a1f319793f64c52d2ed4e182",
    "g20_h3v7n5qf_closed_forms.md": "bd8ef38292568ac38e6433ea2d1a86f35351ef10",
    "g21_h3v7n5qf_cr2_reachability_criterion.md": "49e2d949854a3e503bcf22148bd1c92d6f033027",
    "g22_h3v7n5qf_a_perform_lower_bound.md": "156bd833c73ad5648904c238d7a0a445e9c6e7a3",
    "g23_h3v7n5qf_choice_free_reproofs.md": "6178272a5c72d1a4954d5c63108882bf6ea317c4",
    "g24_genesis_h3_seed_edit_ablation_bench.md": "4f1ee499e786c76f0928fa5f028d0d43bc78b6dc",
    "g25_genesis_as_omega_foundation_crosswalk.md": "e25836268929cec11b974abea1a45d2a120681d5",
    "run_genesis_suite.py": "e5b305e4c7b3fe530d1c0d94ac5b4653a3d6a34e",
    "results/genesis_master_report.json": "38bc64dd3b2254e9af9bf0bd9df5435e2dd1509a",
    "results/genesis_receipt.json": "1c77c28a41be54f6a19aa39742b862acff5f0b17",
}
SELECTED_DEFINITIONS = {
    "ChallengeSpec", "parse_challenge_file", "DangerGate", "LeanVerifier",
    "ArtifactVerifier", "build_genesis_prompt", "parse_llm_json",
}


class RecoveryError(ValueError):
    """A missing pin or corrupt byte cannot become replay evidence."""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf8")


def paper_path(paper: Path, relative: str) -> Path:
    parts = PurePosixPath(relative)
    if parts.is_absolute() or ".." in parts.parts or "\\" in relative or ":" in relative:
        raise RecoveryError("UNSAFE_RECOVERED_PATH")
    root = paper.resolve()
    path = root.joinpath(*parts.parts)
    if not path.resolve().is_relative_to(root):
        raise RecoveryError("RECOVERED_PATH_ESCAPES_PAPER")
    if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != root.parent):
        raise RecoveryError("RECOVERED_PATH_IS_SYMLINK")
    return path


def _git(repository: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repository.resolve()), *args], capture_output=True, check=False,
    )
    if result.returncode:
        raise RecoveryError("GIT_OBJECT_UNAVAILABLE: " + result.stderr.decode("utf8", "replace"))
    return result.stdout


def recover(repository: Path, paper: Path = PAPER) -> dict[str, Any]:
    """Read only these 28 declared blobs; never infer replacements or normalize bytes."""
    if _git(repository, "rev-parse", COMMIT + "^{tree}").decode().strip() != TREE:
        raise RecoveryError("HISTORICAL_TREE_PIN_MISMATCH")
    prepared = []
    for name, pin in sorted(PINS.items()):
        path = SOURCE_PREFIX + name
        actual = _git(repository, "rev-parse", COMMIT + ":" + path).decode().strip()
        if actual != pin:
            raise RecoveryError("COMMIT_PATH_BLOB_MISMATCH: " + path)
        data = _git(repository, "cat-file", "blob", pin)
        if git_blob(data) != pin:
            raise RecoveryError("RAW_GIT_BLOB_MISMATCH: " + path)
        target = paper_path(paper, RECOVERED_PREFIX + name)
        if target.exists() and target.read_bytes() != data:
            raise RecoveryError("EXISTING_RECOVERED_BYTES_DIFFER: " + name)
        prepared.append((name, data, target))
    entries = []
    for name, data, target in prepared:
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_bytes(data)
        entries.append({
            "source_relative_path": SOURCE_PREFIX + name,
            "recovered_relative_path": RECOVERED_PREFIX + name,
            "source_commit": COMMIT, "git_blob": PINS[name],
            "sha256": sha(data), "byte_count": len(data),
            "custody": "RECOVERED_HISTORICAL_GIT_BLOB_SEPARATE_FROM_CURRENT_SNAPSHOT",
        })
    manifest = {
        "schema": "paper011.historical_recovery.v1", "authority_effect": "None",
        "source_commit": COMMIT, "source_tree": TREE, "deletion_commit": DELETION_COMMIT,
        "file_count": len(entries), "total_bytes": sum(e["byte_count"] for e in entries),
        "entries": entries,
        "scope": "28 declared Genesis sources; excludes bulk PFP source snapshot and sealed 19L57G1 text",
    }
    target = paper_path(paper, "docs/history_recovery/recovery_manifest.json")
    if target.exists() and target.read_bytes() != canonical(manifest):
        raise RecoveryError("EXISTING_RECOVERY_MANIFEST_DIFFERS")
    target.write_bytes(canonical(manifest))
    verify_recovery(target, paper)
    return manifest


def verify_recovery(manifest_path: Path = MANIFEST_PATH, paper: Path = PAPER) -> dict[str, bytes]:
    manifest = json.loads(manifest_path.read_bytes())
    if (manifest.get("schema") != "paper011.historical_recovery.v1"
            or manifest.get("source_commit") != COMMIT or manifest.get("source_tree") != TREE):
        raise RecoveryError("RECOVERY_IDENTITY_MISMATCH")
    entries = manifest.get("entries")
    if not isinstance(entries, list) or len(entries) != len(PINS):
        raise RecoveryError("RECOVERY_FILE_SET_MISMATCH")
    recovered = {}
    for entry in entries:
        source = entry.get("source_relative_path", "")
        if not source.startswith(SOURCE_PREFIX):
            raise RecoveryError("RECOVERY_SOURCE_PATH_MISMATCH")
        name = source[len(SOURCE_PREFIX):]
        if (name not in PINS or name in recovered or entry.get("source_commit") != COMMIT
                or entry.get("git_blob") != PINS[name]
                or entry.get("recovered_relative_path") != RECOVERED_PREFIX + name):
            raise RecoveryError("RECOVERY_BLOB_OR_PATH_IDENTITY_MISMATCH")
        raw = paper_path(paper, entry["recovered_relative_path"]).read_bytes()
        if (git_blob(raw) != PINS[name] or sha(raw) != entry.get("sha256")
                or len(raw) != entry.get("byte_count")):
            raise RecoveryError("RECOVERED_BYTES_MISMATCH: " + name)
        recovered[name] = raw
    if (set(recovered) != set(PINS) or manifest.get("file_count") != len(PINS)
            or manifest.get("total_bytes") != sum(map(len, recovered.values()))):
        raise RecoveryError("RECOVERY_FILE_SET_OR_COUNT_MISMATCH")
    return recovered


class UnboundGroundTruth:
    """Explicit absent historical external artifact capability, with an access trace."""

    def __init__(self, accesses: list[str], path: str = "19L57G1_NOT_BOUND") -> None:
        self.accesses, self.path = accesses, path

    def __truediv__(self, name: str) -> UnboundGroundTruth:
        return UnboundGroundTruth(self.accesses, self.path + "/" + name)

    def exists(self) -> bool:
        self.accesses.append(self.path)
        return False


class BlockedProcesses:
    @staticmethod
    def run(*args: Any, **kwargs: Any) -> Any:
        raise RecoveryError("LEAN_PROCESS_CAPABILITY_NOT_BOUND_FOR_HISTORICAL_SNIPPETS")


def preserved_harness(raw: bytes) -> tuple[types.ModuleType, dict[str, Any]]:
    if git_blob(raw) != PINS["run_genesis_suite.py"]:
        raise RecoveryError("HARNESS_SOURCE_BLOB_MISMATCH")
    tree = ast.parse(raw, filename="historical/run_genesis_suite.py")
    selected = [node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))
                and node.name in SELECTED_DEFINITIONS]
    if {node.name for node in selected} != SELECTED_DEFINITIONS:
        raise RecoveryError("HISTORICAL_DEFINITION_SET_MISMATCH")
    accesses: list[str] = []
    module = types.ModuleType("paper011_preserved_genesis")
    module.__dict__.update({
        "re": re, "json": json, "Path": Path, "Any": Any,
        "dataclass": dataclasses.dataclass, "subprocess": BlockedProcesses,
        "GENESIS_REPO_PATH": UnboundGroundTruth(accesses),
    })
    # Whole original definitions, unchanged; top-level .env/sys.path/provider setup excluded.
    body = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
                           *selected], type_ignores=[])
    ast.fix_missing_locations(body)
    prior = sys.modules.get(module.__name__)
    sys.modules[module.__name__] = module
    try:
        exec(compile(body, "historical/run_genesis_suite.py", "exec"), module.__dict__)
    finally:
        if prior is None:
            sys.modules.pop(module.__name__, None)
        else:
            sys.modules[module.__name__] = prior
    journal = {
        "harness_sha256": sha(raw), "git_blob": PINS["run_genesis_suite.py"],
        "selected_definitions": [
            {"name": node.name, "start_line": node.lineno, "end_line": node.end_lineno,
             "ast_sha256": sha(ast.dump(node, include_attributes=False).encode())}
            for node in selected
        ],
        "definition_bodies_modified": False,
        "excluded_top_level": ["environment loading", "sys.path mutation", "provider/budget runner"],
        "injected_capabilities": {"external_ground_truth": "UNBOUND", "subprocess": "BLOCKED"},
        "external_ground_truth_accesses": accesses,
    }
    return module, journal


def report_custody(recovered: dict[str, bytes]) -> tuple[dict[str, Any], dict[str, Any]]:
    raw = recovered["results/genesis_master_report.json"]
    report = json.loads(raw)
    receipt = json.loads(recovered["results/genesis_receipt.json"])
    if sha(raw) != receipt.get("sha256"):
        raise RecoveryError("HISTORICAL_RECEIPT_REPORT_DIGEST_MISMATCH")
    rows = report.get("results", [])
    expected = {f"G{i:02}" for i in range(1, 26)}
    ids = [r.get("challenge_id") for r in rows]
    if len(ids) != 25 or set(ids) != expected or report.get("total_challenges") != 25:
        raise RecoveryError("HISTORICAL_CHALLENGE_CENSUS_MISMATCH")
    return report, receipt


def section_span(text: str, section: int) -> dict[str, Any]:
    pattern = rf"^##\s+{section}\.\s+([^\n]+)\n(.*?)(?=^##|\Z)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    if not match:
        raise RecoveryError(f"REQUIRED_SPEC_SECTION_MISSING: {section}")
    return {"start_line": text[:match.start()].count("\n") + 1,
            "end_line": text[:match.end()].count("\n") + 1,
            "section_heading": match.group(1), "text": match.group(2).strip()}


def replay(manifest_path: Path = MANIFEST_PATH, paper: Path = PAPER) -> dict[str, Any]:
    recovered = verify_recovery(manifest_path, paper)
    report, historical_receipt = report_custody(recovered)
    original, journal = preserved_harness(recovered["run_genesis_suite.py"])
    historical_rows = {row["challenge_id"]: row for row in report["results"]}
    rows = []
    for name in sorted(n for n in PINS if n.startswith("g")):
        spec_path = paper_path(paper, RECOVERED_PREFIX + name)
        spec = original.parse_challenge_file(spec_path)
        cid = spec.challenge_id
        old = historical_rows[cid]
        prompt = original.build_genesis_prompt(spec)
        access_start = len(journal["external_ground_truth_accesses"])
        report_input = canonical(old)
        derived_result = original.ArtifactVerifier.verify_challenge(spec, json.loads(report_input))
        controls = []
        for label, payload in [
            ("EMPTY_RESPONSE", {}),
            ("WRONG_TASK_UNPROVED_CHECKED", {"challenge_id": "G99", "relation": "CHECKED",
                                          "status": "SOLVED", "formal_derivation_or_data": "deliberately false"}),
            ("UNKNOWN_WITH_NO_PROOF", {"challenge_id": cid, "relation": "OPEN", "status": "UNKNOWN"}),
        ]:
            raw = canonical(payload)
            parsed = original.parse_llm_json(raw.decode("utf8"))
            result = original.ArtifactVerifier.verify_challenge(spec, parsed)
            controls.append({"control": label, "actual_input_utf8": raw.decode("utf8"),
                             "input_sha256": sha(raw), "actual_artifact_verifier_output": result,
                             "incorrect_verification_reproduced": result.get("verified") is True})
        text = recovered[name].decode("utf8")
        external_refs = sorted(set(re.findall(r"`(19L57G1:[^`\n]+)`", text)))
        rows.append({
            "challenge_id": cid, "title": spec.title, "spec_path": RECOVERED_PREFIX + name,
            "spec_sha256": sha(recovered[name]), "spec_git_blob": PINS[name],
            "original_parser_replayed": True,
            "reconstructed_prompt_sha256": sha(prompt.encode("utf8")),
            "reconstructed_prompt_declares_identity_false_by_construction":
                "is FALSE BY CONSTRUCTION" in prompt,
            "formal_problem": section_span(text, 3), "output_contract": section_span(text, 4),
            "capability_gate": section_span(text, 9), "external_references_in_spec": external_refs,
            "historical_relation_label": old["relation"], "historical_status_label": old["status"],
            "historical_lean_metadata": old["lean_verification"],
            "historical_saved_artifact_verification": old["artifact_verification"],
            "report_derived_input_sha256": sha(report_input),
            "report_derived_verifier_output": derived_result,
            "external_ground_truth_accesses_during_row": journal["external_ground_truth_accesses"][access_start:],
            "controls": controls,
            "artifact_checker_flaw_reproduced": all(c["incorrect_verification_reproduced"] for c in controls),
            "execution_outcome": "ORIGINAL_HARNESS_FALSIFIER_REPLAYED_POSITIVE_COMPUTATION_UNRESOLVED",
            "actual_original_raw_response_bytes": "NOT_PERSISTED_BY_ORIGINAL_HARNESS",
            "historical_lean_snippet_bytes": "NOT_PERSISTED" if old["lean_verification"].get("present")
                else "NO_SNIPPET_REPORTED",
            "historical_external_19L57G1_sources": "NOT_INCLUDED_IN_RECOVERED_SUITE",
            "positive_obligation_satisfied": False, "mathematical_certificate_replayed": False,
            "planned_multi_arm_model_study_recreated": False,
        })
    danger_controls = []
    for label, raw, parsed, expectation in [
        ("DECLARED_IDENTITY_ASSERTION", "This proves that DDC letters are derived from 19L57G1.", None, False),
        ("NEUTRAL_LANGUAGE", "The two vocabularies remain separately declared.", None, True),
        ("CHECKED_WITHOUT_PROOF_OR_DATA", "{}", {"relation": "CHECKED"}, False),
        ("NONSENSE_DATA_ACCEPTED", "{}", {"relation": "CHECKED", "formal_derivation_or_data": "nonsense"}, True),
        ("DIRECT_IDENTITY_MISSED", "A datum is a DDC letter.", None, True),
        ("QUOTED_NEGATIVE_FALSE_POSITIVE", "The report rejects the phrase identical to 19L57G1.", None, False),
    ]:
        output = original.DangerGate.audit(raw, parsed)
        danger_controls.append({"control": label, "text": raw, "parsed": parsed,
                                "input_sha256": sha(canonical({"text": raw, "parsed": parsed})),
                                "actual_output": output, "expected_original_clean": expectation,
                                "original_behavior_reproduced": output[0] is expectation})
    lean_controls = []
    for code in [None, "", "-- sorry inside a comment", "admit", "unsafe def x := 1", "partial def x := 1"]:
        result = original.LeanVerifier.check_snippet(code)
        lean_controls.append({"actual_code": code, "actual_output": result,
                              "process_invoked": False,
                              "expected_original_result_observed": result.get("compiles") is not True})
    wrapped = '```json\n{"relation":"OPEN","status":"UNKNOWN"}\n```'
    wrapped_result = original.parse_llm_json(wrapped)
    relations = Counter(row["historical_relation_label"] for row in rows)
    checked = [r for r in rows if r["historical_relation_label"] == "CHECKED"]
    summary = {
        "schema": "paper011.genesis_history_replay.v1", "authority_effect": "None",
        "status": "FINITE_ORIGINAL_HARNESS_FALSIFIERS_WITH_UNRESOLVED_POSITIVE_OBLIGATIONS",
        "source_commit": COMMIT, "recovery_manifest_sha256": sha(manifest_path.read_bytes()),
        "historical_report_sha256": sha(recovered["results/genesis_master_report.json"]),
        "historical_receipt": historical_receipt,
        "findings_note_receipt_id": "REC_GENESIS_SUITE_1790611114",
        "retained_receipt_id_matches_findings_note":
            historical_receipt["receipt_id"] == "REC_GENESIS_SUITE_1790611114",
        "historical_claim_label_census": dict(relations), "challenge_count": len(rows),
        "artifact_mutations_replayed": sum(len(r["controls"]) for r in rows),
        "incorrect_artifact_verifications_reproduced": sum(
            c["incorrect_verification_reproduced"] for r in rows for c in r["controls"]),
        "historical_checked_lean": {
            "claimed_checked": len(checked),
            "reported_compiled": sum(r["historical_lean_metadata"].get("compiles") is True for r in checked),
            "reported_timeout": sum("timed out" in r["historical_lean_metadata"].get("error", "") for r in checked),
            "reported_failed_without_timeout": sum(
                r["historical_lean_metadata"].get("compiles") is False
                and "timed out" not in r["historical_lean_metadata"].get("error", "") for r in checked),
            "reported_absent": sum(r["historical_lean_metadata"].get("present") is False for r in checked),
            "snippets_recompiled_now": 0,
        },
        "historical_raw_response_bytes_retained": False, "historical_lean_snippet_bytes_retained": False,
        "source_journal": journal, "rows": rows, "danger_gate_controls": danger_controls,
        "lean_lexical_controls": lean_controls,
        "json_wrapper_control": {"actual_input_utf8": wrapped, "actual_output": wrapped_result,
                                 "non_rfc8259_wrapper_accepted_by_original_parser": not wrapped_result.get("parse_error", False)},
        "all_25_positive_obligations_satisfied": False,
        "unresolved": [
            "Actual raw provider responses and submitted Lean snippets were not persisted by the original harness.",
            "The 25 challenge specifications require distinct pinned programs, data/proofs, or native actions, absent from this recovered suite.",
            "19L57G1 sealed sources and its clean statement/axiom checks are not copied or run here.",
            "Harness bug replay and historical self-label accounting do not satisfy any challenge capability gate.",
        ],
    }
    if not all(c["original_behavior_reproduced"] for c in danger_controls):
        raise RecoveryError("ORIGINAL_DANGER_BEHAVIOR_DRIFT")
    if summary["incorrect_artifact_verifications_reproduced"] != 75:
        raise RecoveryError("ORIGINAL_ARTIFACT_VERIFIER_BEHAVIOR_DRIFT")
    verify_recovery(manifest_path, paper)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["recover", "replay", "verify"])
    parser.add_argument("--repository", type=Path)
    args = parser.parse_args()
    if args.action == "recover":
        if args.repository is None:
            parser.error("recover requires an explicitly declared --repository")
        result = recover(args.repository)
        print(json.dumps({"recovered_files": result["file_count"], "raw_bytes": result["total_bytes"]}))
    elif args.action == "verify":
        files = verify_recovery()
        report_custody(files)
        print(json.dumps({"custody_verified": True, "files": len(files)}))
    else:
        result = replay()
        out = paper_path(PAPER, "docs/history_recovery/genesis_replay.json")
        out.write_bytes(canonical(result))
        receipt = {"schema": "paper011.genesis_replay_custody.v1", "authority_effect": "None",
                   "recovery_manifest_sha256": result["recovery_manifest_sha256"],
                   "code_sha256": sha(Path(__file__).read_bytes()),
                   "result_sha256": sha(out.read_bytes()), "result_path": out.relative_to(PAPER).as_posix(),
                   "scope": "Byte custody and original-harness finite falsifiers; no mathematical verification"}
        paper_path(PAPER, "docs/history_recovery/replay_receipt.json").write_bytes(canonical(receipt))
        print(json.dumps({"challenges": result["challenge_count"],
                          "incorrect_verifications_reproduced": result["incorrect_artifact_verifications_reproduced"],
                          "positive_obligations_satisfied": 0, "result_sha256": receipt["result_sha256"]}))


if __name__ == "__main__":
    main()
