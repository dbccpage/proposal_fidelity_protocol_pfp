"""Replay original synthetic dialogue inputs from the commit introducing the traces.

Only source assignments and score branches are executed. No constructor, packet
compiler, emitter, model, controller, or mathematical solver is invoked.
"""

from __future__ import annotations

import argparse
import ast
import copy
import dataclasses
import hashlib
import importlib.util
import json
import subprocess
import sys
import types
from pathlib import Path

ORIGINAL = "a76ad617a666820db649685b53602a423d766c12"
SOURCE = "pfp/use_cases/symbol_game_runner.py"
PAPER = Path(__file__).absolute().parents[1]


def helper():
    spec = importlib.util.spec_from_file_location(
        "paper011_original_recovery_helper",
        Path(__file__).with_name("aggregate_original_recovery_v1.py"),
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def target(node):
    return (
        node.targets[0].id
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        else None
    )


def extract(raw: bytes, name: str, max_steps: int, score_owner) -> tuple[list, dict]:
    if type(max_steps) is not int or not 1 <= max_steps <= (
        6 if name == "run_refactoring_packet" else 4
    ):
        raise ValueError("ORIGINAL_BOUNDED_STEP_RANGE_REQUIRED")
    tree = ast.parse(raw)
    owner = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "SymbolGameRunnerUseCase"
    )
    method = next(
        node for node in owner.body if isinstance(node, ast.FunctionDef) and node.name == name
    )
    loop = next(
        node
        for node in method.body
        if isinstance(node, ast.For) and ast.unparse(node.target) == "step_idx"
    )
    if ast.unparse(loop.iter) != "range(max_steps)":
        raise ValueError("ORIGINAL_LOOP_REQUIRED")
    pre_names = (
        {"phi_progression", "gamma_progression", "active_progression"}
        if name == "run_refactoring_packet"
        else {"current_score"}
    )
    selected = [node for node in method.body if target(node) in pre_names]
    body_names = (
        {"step_num", "cur_score", "prior_score", "candidate", "is_last"}
        if name == "run_refactoring_packet"
        else {"step_num", "candidate", "is_last"}
    )
    body = [node for node in loop.body if target(node) in body_names]
    if name == "run_problem":
        branch = next(
            node
            for node in loop.body
            if isinstance(node, ast.If) and ast.unparse(node.test) == "step_idx == max_steps - 1"
        )
        if any(target(node) != "next_score" for node in branch.body + branch.orelse):
            raise ValueError("ORIGINAL_SCORE_BRANCH_REQUIRED")
        body.insert(2, branch)
    terminal_branch = next(
        node
        for node in loop.body
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.UnaryOp)
        and ast.unparse(node.test) == "not is_last"
    )
    terminal = copy.deepcopy(terminal_branch)
    terminal.body = [node for node in terminal.body if target(node) in {"action_taken", "status"}]
    terminal.orelse = [
        node for node in terminal.orelse if target(node) in {"action_taken", "status"}
    ]
    if len(terminal.body) != 2 or len(terminal.orelse) != 2:
        raise ValueError("ORIGINAL_TERMINAL_ASSIGNMENTS_REQUIRED")
    body.append(terminal)
    score = "cur_score" if name == "run_refactoring_packet" else "next_score"
    prior = "prior_score" if name == "run_refactoring_packet" else "current_score"
    capture = ast.parse(
        f"_capture(step_num, candidate, {score}, {prior}, action_taken, status)"
    ).body[0]
    body.append(capture)
    if name == "run_problem":
        body.append(next(node for node in loop.body if target(node) == "current_score"))
    executed_loop = copy.deepcopy(loop)
    executed_loop.body = body
    selected.append(executed_loop)
    program = ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[]))
    # Allow only the calls present in this closed source projection plus capture.
    for call in (node for node in ast.walk(program) if isinstance(node, ast.Call)):
        if not isinstance(call.func, ast.Name) or call.func.id not in {
            "range",
            "tuple",
            "max",
            "ObstructionScore",
            "_capture",
        }:
            raise ValueError("SIDE_EFFECT_CALL_REFUSED")
    result = []

    def capture(step, candidate, current, prior_score, action, status):
        result.append(
            {
                "step": step,
                "candidate": candidate,
                "score": current,
                "prior_score": prior_score,
                "source_action": action,
                "source_status": status,
            }
        )

    namespace = {"max_steps": max_steps, "ObstructionScore": score_owner, "_capture": capture}
    exec(compile(program, "<source-bound-original-progression>", "exec"), namespace)
    lines = raw.splitlines(keepends=True)
    method_raw = b"".join(lines[method.lineno - 1 : method.end_lineno])
    identities = {
        "method": name,
        "start_line": method.lineno,
        "end_line": method.end_lineno,
        "raw_span_sha256": hashlib.sha256(method_raw).hexdigest(),
        "raw_span_hex": method_raw.hex(),
        "extracted_ast_sha256": hashlib.sha256(
            ast.dump(program, include_attributes=False).encode()
        ).hexdigest(),
        "extracted_source": ast.unparse(program),
        "transport_changes": [
            "Select original score/candidate assignments and score/terminal branches",
            "Omit packet construction, scene invocation, persistence and controller orchestration",
            "Append observation capture and retain original current_score update",
        ],
        "max_steps": max_steps,
    }
    return result, identities


def run(repo: Path, baseline: Path, output: Path):
    if output.exists():
        raise ValueError("FRESH_OUTPUT_REQUIRED")
    cache = output / "empty_bytecode_cache"
    if (
        sys.pycache_prefix is None
        or Path(sys.pycache_prefix) != cache
        or not sys.flags.dont_write_bytecode
    ):
        raise ValueError("FRESH_STARTUP_CACHE_REQUIRED")
    output.mkdir(parents=True)
    cache.mkdir()
    sys.dont_write_bytecode = True
    h = helper()
    own_pin = h.digest(h.regular(Path(__file__)))
    helper_pin = h.digest(h.regular(Path(h.__file__)))
    runtime = h.stdlib_inventory()
    receipt_raw = h.regular(baseline / "receipt.json")
    receipt = json.loads(receipt_raw)
    self_hash = receipt.pop("self_sha256")
    if h.digest(h.canonical(receipt)) != self_hash or receipt["custody_closed"] is not True:
        raise ValueError("CLOSED_BASELINE_REQUIRED")
    h.verify_capture(repo, baseline, receipt["capture_manifest"])
    source_raw = subprocess.run(
        ["git", "cat-file", "blob", ORIGINAL + ":" + SOURCE],
        cwd=repo,
        check=True,
        capture_output=True,
    ).stdout
    original_blob = (
        subprocess.run(
            ["git", "rev-parse", ORIGINAL + ":" + SOURCE], cwd=repo, check=True, capture_output=True
        )
        .stdout.decode()
        .strip()
    )
    (output / "original_symbol_game_runner.py").write_bytes(source_raw)
    journal = []
    (output / "adapted_sources").mkdir()
    package = types.ModuleType(h.PREFIX)
    package.__path__ = []
    sys.modules[h.PREFIX] = package
    pins = {row["path"]: row["sha256"] for row in receipt["capture_manifest"]}
    finder = h.RecoveredFinder(baseline / "source_files", pins, journal, output / "adapted_sources")
    sys.meta_path.insert(0, finder)
    try:
        models = __import__(h.PREFIX + ".symbol_game_models", fromlist=["*"])
        dialogue = __import__(h.PREFIX + ".symbol_game_dialogue", fromlist=["*"])
        codec = __import__(h.PREFIX + ".canonical", fromlist=["*"])
        results, projections = [], []
        inputs = [
            json.loads(line)
            for line in h.regular(baseline / "actual_dialogue_inputs.jsonl").splitlines()
        ]
        input_map = {item["path"]: bytes.fromhex(item["raw_bytes_hex"]) for item in inputs}
        for item in inputs:
            if h.regular(repo / item["path"]) != input_map[item["path"]]:
                raise ValueError("BASELINE_INPUT_DRIFT")
        for path, raw in input_map.items():
            if not path.endswith("_uns_trace.md"):
                continue
            rounds = h.parse_rounds(raw)
            ledger_path = next(
                p for p in input_map if Path(p).parent == Path(path).parent and p.endswith(".jsonl")
            )
            rows = [json.loads(line) for line in input_map[ledger_path].splitlines()]
            payloads = [
                h.historical_metadata(codec.thaw(codec.canonical_unwire(row["packet"]["payload"])))
                for row in rows
            ]
            method = "run_refactoring_packet" if "code_refactoring" in path else "run_problem"
            stages, identity = extract(source_raw, method, len(rounds), models.ObstructionScore)
            projections.append({"narrative_path": path, **identity})
            for i, (stage, round_) in enumerate(zip(stages, rounds)):
                packet = types.SimpleNamespace(
                    task_id=rows[i]["packet"]["task_id"],
                    initial_state_hash=rows[i]["packet"]["initial_state_hash"],
                )
                rendered = dialogue.SymbolGameDialogueArguer.generate_round_debate(
                    packet, stage["candidate"], stage["score"], stage["prior_score"], stage["step"]
                )
                comparable = payloads[i + 1] if i + 1 < len(rows) else None
                serialized_score = dataclasses.asdict(stage["score"])
                display = round_["displayed_score"]
                if any(serialized_score[key] != display[key] for key in display):
                    raise ValueError("ORIGINAL_SCORE_DISPLAY_MISMATCH")
                if comparable and (
                    comparable["candidate"] != stage["candidate"]
                    or any(comparable["score"][key] != serialized_score[key] for key in display)
                ):
                    raise ValueError("ORIGINAL_CANDIDATE_LEDGER_MISMATCH")
                for expected, actual in zip(round_["roles"], rendered):
                    results.append(
                        {
                            "path": path,
                            "round": stage["step"],
                            "speaker": actual.speaker,
                            "source_candidate": stage["candidate"],
                            "source_score": serialized_score,
                            "source_prior_score": dataclasses.asdict(stage["prior_score"])
                            if stage["prior_score"]
                            else None,
                            "source_action": stage["source_action"],
                            "source_status": stage["source_status"],
                            "source_is_exact": stage["score"].is_exact,
                            "source_strictly_improves": stage["score"].strictly_improves(
                                stage["prior_score"]
                            )
                            if stage["prior_score"]
                            else None,
                            "actual_text": actual.dialogue,
                            "retained_text_sha256": h.digest(expected["text"].encode()),
                            "text_equal": actual.dialogue == expected["text"],
                            "native_measurement_verified": False,
                        }
                    )
        if len(results) != 120 or not all(row["text_equal"] for row in results):
            raise ValueError("COMPLETE_ORIGINAL_TEMPLATE_COMPARISONS_FAILED")
        h.verify_capture(repo, baseline, receipt["capture_manifest"])
        for item in inputs:
            if h.regular(repo / item["path"]) != input_map[item["path"]]:
                raise ValueError("ACTUAL_INPUT_DRIFT")
        if (
            source_raw
            != subprocess.run(
                ["git", "cat-file", "blob", ORIGINAL + ":" + SOURCE],
                cwd=repo,
                check=True,
                capture_output=True,
            ).stdout
            or h.regular(output / "original_symbol_game_runner.py") != source_raw
        ):
            raise ValueError("ORIGINAL_SOURCE_DRIFT")
        if (
            h.stdlib_inventory() != runtime
            or h.digest(h.regular(Path(__file__))) != own_pin
            or h.digest(h.regular(Path(h.__file__))) != helper_pin
        ):
            raise ValueError("RUNTIME_OR_MACHINERY_DRIFT")
        final = {
            "schema": "paper011.original-source-progression.v1",
            "source_commit": ORIGINAL,
            "source_path": SOURCE,
            "source_sha256": h.digest(source_raw),
            "source_git_blob_oid": original_blob,
            "baseline_self_sha256": self_hash,
            "baseline_raw_sha256": h.digest(receipt_raw),
            "runner_sha256": own_pin,
            "helper_sha256": helper_pin,
            "source_adaptations": journal,
            "original_source_projections": projections,
            "all_role_comparisons": results,
            "positive_comparison_count": 120,
            "runtime_files": runtime,
            "custody_closed": True,
            "source_recreation_only": True,
            "native_measurement_verified": False,
            "physical_or_mathematical_admission": False,
            "authority_effect": "None",
        }
        final["self_sha256"] = h.digest(h.canonical(final))
        (output / "receipt.json").write_bytes(h.canonical(final) + b"\n")
        return final
    finally:
        sys.meta_path.remove(finder)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine-root", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.engine_root.absolute(), args.baseline.absolute(), args.output.absolute())
    print(
        json.dumps(
            {
                "custody_closed": result["custody_closed"],
                "matched_original_beats": result["positive_comparison_count"],
                "self_sha256": result["self_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
