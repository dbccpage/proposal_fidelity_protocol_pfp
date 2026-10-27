"""Recover the cited original Demo 2 source and audit retained dialogue custody.

The imported sign-gauge algorithm supplies its original restricted certificate.
No Hamiltonian-to-native-functional adapter or new mathematical solver is defined.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.abc
import importlib.util
import io
import json
import re
import stat
import subprocess
import sys
import types
import unittest
from collections import Counter
from pathlib import Path

COMMIT = "6f649c611c2b751db4abf4cba541bf2403575590"
DEMO = "research/mssn_sn_tower/demos/demo_2/"
PREFIX = "paper011_recovered_demo2"
BRIDGE = "pfp/domain/bridge/"
PAPER = Path(__file__).absolute().parents[1]
TRACES = (
    "demo2_r1_stoquastic_1790206738.jsonl",
    "demo2_r1_stoquastic_1790206756.jsonl",
    "demo2_r1_stoquastic_1790206807.jsonl",
    "demo2_r2_freefermion_1790207127.jsonl",
    "demo2_r2_freefermion_1790207175.jsonl",
    "demo2_r3_attractive_hubbard_1790207676.jsonl",
    "demo2_r3_attractive_hubbard_1790207968.jsonl",
    "demo2_r4_repulsive_hubbard_1790207568.jsonl",
    "demo2_r5_chatgpt_frustrated_triangular.jsonl",
    "demo2_r5_deepseek_frustrated_triangular.jsonl",
    "demo2_r5_frustrated_triangular_1790208154.jsonl",
)
GIT_PATHS = (
    tuple(
        DEMO + name
        for name in (
            "run_demo2.py",
            "sign_switching.py",
            "meron_witness.py",
            "bqnf_zero.py",
            "certificate_gate.py",
            "test_run_demo2_r1.py",
            "test_run_demo2_r2.py",
            "test_sign_switching.py",
        )
    )
    + tuple(DEMO + "traces/" + name for name in TRACES)
    + (
        BRIDGE + "symbol_game_dialogue.py",
        BRIDGE + "symbol_game_models.py",
    )
)
LOCAL_MODULES = {
    "sign_switching",
    "meron_witness",
    "bqnf_zero",
    "certificate_gate",
    "run_demo2",
    "test_run_demo2_r1",
    "test_run_demo2_r2",
    "test_sign_switching",
    "symbol_game_dialogue",
    "symbol_game_models",
}
STANDARD_IMPORTS = {
    "__future__",
    "argparse",
    "collections",
    "dataclasses",
    "decimal",
    "fractions",
    "hashlib",
    "io",
    "itertools",
    "json",
    "os",
    "pathlib",
    "re",
    "sys",
    "time",
    "typing",
    "unittest",
    "urllib.request",
}


class RecoveryError(ValueError):
    pass


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def regular(path: Path) -> bytes:
    for item in reversed((path, *path.parents)):
        info = item.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise RecoveryError("REDIRECTED_INPUT: " + str(item))
    if not stat.S_ISREG(path.lstat().st_mode):
        raise RecoveryError("REGULAR_FILE_REQUIRED: " + str(path))
    return path.read_bytes()


def git_bytes(repo: Path, relative: str) -> tuple[bytes, str]:
    raw = subprocess.run(
        ["git", "cat-file", "blob", COMMIT + ":" + relative],
        cwd=repo,
        check=True,
        capture_output=True,
    ).stdout
    oid = (
        subprocess.run(
            ["git", "rev-parse", COMMIT + ":" + relative],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        .stdout.decode("ascii")
        .strip()
    )
    return raw, oid


def adapt(raw: bytes, name: str) -> tuple[ast.Module, dict]:
    """Leave algorithm nodes intact; remove enumerated initialization effects only."""
    tree = ast.parse(raw)
    lines = raw.splitlines(keepends=True)
    journal = {"module": name, "source_sha256": digest(raw), "removed": [], "imports": []}
    retained = []
    is_runner = name == "run_demo2"
    is_test = name.startswith("test_")
    allowed_remove = {"DEMO_DIR", "ROOT", "env_file"} if is_runner else {"_DEMO_DIR"}
    for node in tree.body:
        reason = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in allowed_remove:
                reason = "filesystem/path initialization excluded from offline composition"
        elif isinstance(node, ast.If):
            if (
                isinstance(node.test, ast.Compare)
                and ast.unparse(node.test) == "__name__ == '__main__'"
            ):
                reason = "CLI dispatch excluded; explicit offline gates invoked"
            elif is_runner and node.lineno in {36, 44, 48, 53}:
                reason = "stdout wrapper, sys.path insertion, or .env loading excluded"
            elif is_test and ast.unparse(node.test).startswith("str(_DEMO_DIR) not in sys.path"):
                reason = "test sys.path insertion excluded"
            else:
                raise RecoveryError("UNDECLARED_TOP_LEVEL_SIDE_EFFECT")
        if isinstance(node, ast.ImportFrom):
            original = ast.unparse(node)
            if node.module == "pfp.domain":
                if {alias.name for alias in node.names} != {"PacketEnvelopeV2"}:
                    raise RecoveryError("UNDECLARED_ENGINE_IMPORT")
                reason = "deferred annotation only; no packet constructor or admission invoked"
            elif node.module in LOCAL_MODULES:
                node.module = PREFIX + "." + node.module
                node.level = 0
            elif node.module not in STANDARD_IMPORTS:
                raise RecoveryError("UNDECLARED_IMPORT: " + str(node.module))
            journal["imports"].append(
                {"original": original, "adapted": None if reason else ast.unparse(node)}
            )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in LOCAL_MODULES:
                    alias.asname = alias.asname or alias.name
                    alias.name = PREFIX + "." + alias.name
                elif alias.name not in STANDARD_IMPORTS:
                    raise RecoveryError("UNDECLARED_IMPORT: " + alias.name)
            journal["imports"].append({"adapted": ast.unparse(node)})
        if reason:
            span = b"".join(lines[node.lineno - 1 : node.end_lineno])
            journal["removed"].append(
                {
                    "start_line": node.lineno,
                    "end_line": node.end_lineno,
                    "raw_span_sha256": digest(span),
                    "raw_span_hex": span.hex(),
                    "reason": reason,
                }
            )
        else:
            retained.append(node)
    tree.body = retained
    ast.fix_missing_locations(tree)
    journal["adapted_ast_sha256"] = digest(ast.dump(tree, include_attributes=False).encode())
    journal["adapted_source_sha256"] = digest((ast.unparse(tree) + "\n").encode())
    return tree, journal


class RecoveredLoader(importlib.abc.Loader):
    def __init__(self, path: Path, expected: str, name: str, journal: list, output: Path):
        self.path, self.expected, self.name, self.journal, self.output = (
            path,
            expected,
            name,
            journal,
            output,
        )

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        raw = regular(self.path)
        if digest(raw) != self.expected:
            raise RecoveryError("SOURCE_DIGEST_MISMATCH")
        tree, item = adapt(raw, self.name)
        self.journal.append(item)
        module.__file__ = str(self.path)
        (self.output / (self.name + ".py")).write_bytes((ast.unparse(tree) + "\n").encode())
        exec(compile(tree, str(self.path), "exec"), module.__dict__)
        if regular(self.path) != raw:
            raise RecoveryError("SOURCE_DRIFT_DURING_IMPORT")


class RecoveredFinder(importlib.abc.MetaPathFinder):
    def __init__(self, root: Path, pins: dict, journal: list, output: Path):
        self.root, self.pins, self.journal, self.output = root, pins, journal, output

    def find_spec(self, fullname, path=None, target=None):
        if not fullname.startswith(PREFIX + "."):
            return None
        name = fullname.removeprefix(PREFIX + ".")
        if name not in LOCAL_MODULES:
            raise RecoveryError("UNDECLARED_RECOVERED_MODULE")
        relative = (BRIDGE if name.startswith("symbol_game_") else DEMO) + name + ".py"
        loader = RecoveredLoader(
            self.root / relative, self.pins[relative], name, self.journal, self.output
        )
        return importlib.util.spec_from_file_location(fullname, self.root / relative, loader=loader)


def source_span(raw: bytes, line: int, end: int | None = None) -> dict:
    data = b"".join(raw.splitlines(keepends=True)[line - 1 : end or line])
    return {
        "line": line,
        "end_line": end or line,
        "raw_span_sha256": digest(data),
        "raw_span_hex": data.hex(),
    }


def verify_capture(repo: Path, output: Path, manifest: list) -> None:
    expected = {row["path"] for row in manifest}
    actual = {
        p.relative_to(output / "source_files").as_posix()
        for p in (output / "source_files").rglob("*")
        if p.is_file()
    }
    if actual != expected:
        raise RecoveryError("INCOMPLETE_CAPTURE_INVENTORY")
    for row in manifest:
        raw, oid = git_bytes(repo, row["path"])
        if oid != row["git_blob_oid"] or digest(raw) != row["sha256"]:
            raise RecoveryError("GIT_OBJECT_CUSTODY_MISMATCH")
        if regular(output / "source_files" / row["path"]) != raw:
            raise RecoveryError("CAPTURE_DIGEST_MISMATCH")


def parse_rounds(raw: bytes) -> list[dict]:
    text = raw.decode("utf-8")
    starts = list(re.finditer(r"^### Round (\d+): Packet `([^`]+)`", text, re.M))
    rounds = []
    for i, match in enumerate(starts):
        body = text[match.start() : starts[i + 1].start() if i + 1 < len(starts) else len(text)]
        score = re.search(
            r"Host Obstruction Score:.*?Phi_1 = ([\d.]+).*?gamma_2 = ([\d.]+).*?Active Count: `(\d+)`",
            body,
        )
        beats = list(
            re.finditer(r"^##### Round \d+ Beat (\d+): (\w+) \(([^)]+)\)\s*\n", body, re.M)
        )
        roles = []
        for j, beat in enumerate(beats):
            remaining = body[beat.end() : beats[j + 1].start() if j + 1 < len(beats) else len(body)]
            end = remaining.find("»")
            if end == -1:
                raise RecoveryError("MISSING_DIALOGUE_TERMINATOR")
            roles.append(
                {
                    "speaker": beat.group(2),
                    "operator": beat.group(3),
                    "text": remaining[: end + 1].strip(),
                }
            )
        if [r["speaker"] for r in roles] != [
            "Gauge Breaker",
            "Defect Hunter",
            "Bare Metal Anchor",
            "Overconfidence Probe",
            "Resilience",
            "Punchlist",
            "Truth Repair",
            "Adversary",
        ]:
            raise RecoveryError("COMPLETE_ORIGINAL_ROLE_ORDER_REQUIRED")
        if score is None:
            raise RecoveryError("RETAINED_SCORE_REQUIRED")
        rounds.append(
            {
                "round": int(match.group(1)),
                "task_id": match.group(2),
                "body": body,
                "span": source_span(
                    raw,
                    text[: match.start()].count("\n") + 1,
                    text[: match.start() + len(body)].count("\n") + 1,
                ),
                "displayed_score": {
                    "phi_1": float(score.group(1)),
                    "gamma_2": float(score.group(2)),
                    "active_count": int(score.group(3)),
                },
                "roles": roles,
            }
        )
    return rounds


def narrative_packet_checks(raw: bytes, packet_raw: bytes) -> list[dict]:
    rows = [json.loads(line) for line in packet_raw.splitlines() if line.strip()]
    rounds = parse_rounds(raw)
    if len(rounds) != len(rows):
        raise RecoveryError("NARRATIVE_PACKET_CARDINALITY_MISMATCH")
    result = []
    for number, (round_, row) in enumerate(zip(rounds, rows)):
        packet = row["packet"]
        if round_["task_id"] != packet["task_id"]:
            raise RecoveryError("MISSING_CORRESPONDING_PACKET")
        if row["packet_id"] != packet["packet_id"]:
            raise RecoveryError("OUTER_PACKET_ID_MISMATCH")
        if number and packet["parent_event_id"] != rows[number - 1]["packet"]["packet_id"]:
            raise RecoveryError("PARENT_EVENT_MISMATCH")
        audit_id = re.search(r"• Packet ID: `([^`]+)` bound", round_["body"]).group(1)
        state_prefix = re.search(r"Initial State Hash: `([a-f0-9]+)\.\.\.`", round_["body"]).group(
            1
        )
        instruction = re.search(r"Compile child packet `([^`]+)`", round_["body"])
        exact_action = "**Action Taken:** `EXACT_REPAIR`" in round_["body"]
        score = round_["displayed_score"]
        result.append(
            {
                "round": round_["round"],
                "packet_id": packet["packet_id"],
                "task_id": packet["task_id"],
                "narrative_span": round_["span"],
                "packet_row_span": source_span(packet_raw, number + 1),
                "eight_roles": [role["speaker"] for role in round_["roles"]],
                "audit_id_is_packet_id": audit_id == packet["packet_id"],
                "audit_id_is_task_alias": audit_id == packet["task_id"],
                "state_prefix_matches": packet["initial_state_hash"].startswith(state_prefix),
                "source_digest": packet.get("source_digest"),
                "child_instruction": instruction.group(1) if instruction else None,
                "actual_next_task": rows[number + 1]["packet"]["task_id"]
                if number + 1 < len(rows)
                else None,
                "child_instruction_matches": instruction.group(1)
                == rows[number + 1]["packet"]["task_id"]
                if instruction and number + 1 < len(rows)
                else None,
                "child_instruction_without_emitted_child": instruction is not None
                and number + 1 == len(rows),
                "exact_action_with_nonzero_displayed_obstruction": exact_action
                and (score["phi_1"] != 0 or score["gamma_2"] != 0 or score["active_count"] != 0),
                "native_measurement_verified": False,
            }
        )
    return result


def stdlib_inventory() -> dict:
    base = Path(sys.base_prefix)
    paths = [Path(sys.executable), base / "python312.dll"]
    paths += list((base / "DLLs").glob("*.pyd")) + list((base / "DLLs").glob("*.dll"))
    paths += [p for p in (base / "Lib").rglob("*.py") if "site-packages" not in p.parts]
    return {str(p): digest(regular(p)) for p in sorted(set(paths)) if p.exists()}


def run(repo: Path, output: Path) -> dict:
    if output.exists():
        raise RecoveryError("FRESH_OUTPUT_REQUIRED")
    output.mkdir(parents=True)
    (output / "adapted_sources").mkdir()
    cache = output / "empty_bytecode_cache"
    if sys.pycache_prefix != str(cache):
        raise RecoveryError("STARTUP_FRESH_BYTECODE_CACHE_REQUIRED")
    cache.mkdir()
    if any(cache.iterdir()):
        raise RecoveryError("EMPTY_BYTECODE_CACHE_REQUIRED")
    sys.pycache_prefix, sys.dont_write_bytecode = str(cache), True
    if not sys.flags.dont_write_bytecode:
        raise RecoveryError("INTERPRETER_B_FLAG_REQUIRED")
    own_pin = digest(regular(Path(__file__)))
    runtime = stdlib_inventory()
    manifest, pins = [], {}
    for relative in sorted(GIT_PATHS, key=lambda s: s.encode("utf-8")):
        raw, oid = git_bytes(repo, relative)
        path = output / "source_files" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        pins[relative] = digest(raw)
        manifest.append(
            {"path": relative, "sha256": digest(raw), "git_blob_oid": oid, "size": len(raw)}
        )
    verify_capture(repo, output, manifest)
    (output / "capture_manifest.json").write_bytes(
        canonical(
            {"source_commit": COMMIT, "files": manifest, "source_rechecked_before_execution": True}
        )
        + b"\n"
    )
    journal = []
    package = types.ModuleType(PREFIX)
    package.__path__ = []
    sys.modules[PREFIX] = package
    finder = RecoveredFinder(output / "source_files", pins, journal, output / "adapted_sources")
    sys.meta_path.insert(0, finder)
    import urllib.request

    original_urlopen = urllib.request.urlopen

    def denied_network(*args, **kwargs):
        raise RecoveryError("OFFLINE_NETWORK_BOUNDARY")

    urllib.request.urlopen = denied_network
    try:
        runner = __import__(PREFIX + ".run_demo2", fromlist=["*"])
        positive = runner.run_scripted_r1()
        if (
            positive["terminal"] != "RestrictedSignGaugeRepair"
            or positive["bqnf_phi1_zero"] is not None
        ):
            raise RecoveryError("ORIGINAL_POSITIVE_CONTROL_FAILED")
        test_results = []
        for name in ("test_run_demo2_r1", "test_run_demo2_r2", "test_sign_switching"):
            module = __import__(PREFIX + "." + name, fromlist=["*"])
            stream = io.StringIO()
            result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
                unittest.defaultTestLoader.loadTestsFromModule(module)
            )
            (output / (name + "_stream.txt")).write_bytes(stream.getvalue().encode())
            test_results.append(
                {
                    "module": name,
                    "tests_run": result.testsRun,
                    "failures": len(result.failures),
                    "errors": len(result.errors),
                    "successful": result.wasSuccessful(),
                }
            )
            if not result.wasSuccessful():
                raise RecoveryError("ORIGINAL_SOURCE_CONTROLS_FAILED")
        replays = []
        for name in TRACES:
            trace = output / "source_files" / DEMO / "traces" / name
            rows = [json.loads(line) for line in trace.read_bytes().splitlines() if line.strip()]
            actual = (
                runner.run_replay_r1(trace)
                if name.startswith("demo2_r1_")
                else runner.replay_r2(trace)
                if name.startswith("demo2_r2_")
                else None
            )
            replays.append(
                {
                    "trace": DEMO + "traces/" + name,
                    "row_count": len(rows),
                    "raw_response_count": sum(type(r.get("raw")) is str for r in rows),
                    "source_event_hashes": [
                        digest(line) for line in trace.read_bytes().splitlines()
                    ],
                    "actual_replay": actual,
                    "verification": "ORIGINAL_GATE_REPLAY"
                    if actual
                    else "RETAINED_RAW_EVENTS_ONLY",
                }
            )
        checks = dialogue_audit(repo, output, pins, journal)
        verify_capture(repo, output, manifest)
        if stdlib_inventory() != runtime or digest(regular(Path(__file__))) != own_pin:
            raise RecoveryError("RUNTIME_OR_RUNNER_DRIFT")
        receipt = {
            "schema": "paper011.original-recovery.v1",
            "provenance": "SOURCE_RECREATION",
            "source_commit": COMMIT,
            "capture_manifest": manifest,
            "runner_sha256": own_pin,
            "stdlib_runtime_files": runtime,
            "startup_pycache_prefix": str(cache),
            "interpreter_B_flag": bool(sys.flags.dont_write_bytecode),
            "source_adaptations": journal,
            "restricted_TFI_positive": positive,
            "original_source_tests": test_results,
            "historical_trace_replays": replays,
            "original_R2_hopping": {k: str(v) for k, v in runner.HOPPING.items()},
            "dialogue_audit": checks,
            "native_phi_certificate": None,
            "physical_admission": False,
            "authority_effect": "None",
            "custody_closed": True,
        }
        receipt["self_sha256"] = digest(canonical(receipt))
        (output / "receipt.json").write_bytes(canonical(receipt) + b"\n")
        return receipt
    finally:
        urllib.request.urlopen = original_urlopen
        sys.meta_path.remove(finder)


def dialogue_audit(repo: Path, output: Path, pins: dict, journal: list) -> dict:
    # Decode historical metadata through the original domain owner, without packet admission.
    root = "pfp/domain/"
    inputs = []
    modules = {}
    for name, relative in (
        ("exceptions", root + "exceptions.py"),
        ("canonical", root + "shared_kernel/canonical.py"),
    ):
        raw = regular(repo / relative)
        tree = ast.parse(raw)
        for node in tree.body:
            if isinstance(node, ast.ImportFrom) and node.module == "exceptions":
                node.level, node.module = 0, "paper011_recovery_exceptions"
        module = types.ModuleType("paper011_recovery_" + name)
        module.__file__ = str(repo / relative)
        sys.modules[module.__name__] = module
        exec(
            compile(ast.fix_missing_locations(tree), str(repo / relative), "exec"), module.__dict__
        )
        modules[name] = module
        inputs.append({"path": relative, "sha256": digest(raw), "raw_bytes_hex": raw.hex()})
    models = __import__(PREFIX + ".symbol_game_models", fromlist=["*"])
    dialogue = __import__(PREFIX + ".symbol_game_dialogue", fromlist=["*"])
    joins, comparisons = [], []
    for md in sorted((repo / "_intelligence/symbol_game/runs").glob("09232026_*/*_uns_trace.md")):
        if not any(stamp in md.name for stamp in ("042645", "052200", "060218")):
            continue
        companion = list(md.parent.glob("*_packets_*.jsonl"))
        if len(companion) != 1:
            raise RecoveryError("ONE_COMPANION_LEDGER_REQUIRED")
        raw, ledger = regular(md), regular(companion[0])
        for path, data in ((md, raw), (companion[0], ledger)):
            inputs.append(
                {
                    "path": path.relative_to(repo).as_posix(),
                    "sha256": digest(data),
                    "raw_bytes_hex": data.hex(),
                }
            )
        rounds = parse_rounds(raw)
        rows = [json.loads(line) for line in ledger.splitlines()]
        payloads = [
            modules["canonical"].thaw(
                modules["canonical"].canonical_unwire(row["packet"]["payload"])
            )
            for row in rows
        ]
        checked = narrative_packet_checks(raw, ledger)
        for i, (round_, check) in enumerate(zip(rounds, checked)):
            check["narrative_path"] = md.relative_to(repo).as_posix()
            check["ledger_path"] = companion[0].relative_to(repo).as_posix()
            joins.append(check)
            supplied = payloads[i + 1] if i + 1 < len(payloads) else None
            metadata = supplied["score"] if supplied else round_["displayed_score"]
            score = models.ObstructionScore(
                **{k: metadata[k] for k in ("phi_1", "gamma_2", "active_count")}
            )
            prior_meta = supplied.get("prior_score") if supplied else payloads[i].get("score")
            prior = (
                models.ObstructionScore(
                    **{k: prior_meta[k] for k in ("phi_1", "gamma_2", "active_count")}
                )
                if prior_meta
                else None
            )
            packet = types.SimpleNamespace(
                task_id=rows[i]["packet"]["task_id"],
                initial_state_hash=rows[i]["packet"]["initial_state_hash"],
            )
            candidate = supplied["candidate"] if supplied else None
            rendered = dialogue.SymbolGameDialogueArguer.generate_round_debate(
                packet, candidate, score, prior, round_["round"]
            )
            for expected, actual in zip(round_["roles"], rendered):
                candidate_dependent = expected["speaker"] == "Gauge Breaker" and score.phi_1 > 0
                comparisons.append(
                    {
                        "path": check["narrative_path"],
                        "round": round_["round"],
                        "speaker": expected["speaker"],
                        "retained_text_sha256": digest(expected["text"].encode()),
                        "actual_rendered_text": actual.dialogue,
                        "text_equal": actual.dialogue == expected["text"]
                        if not candidate_dependent
                        else None,
                        "candidate_dependent_text_excluded": candidate_dependent,
                        "score_source": "child_packet_canonical_metadata"
                        if supplied
                        else "rounded_narrative_values",
                        "native_measurement_verified": False,
                    }
                )
    for item in inputs:
        if digest(regular(repo / item["path"])) != item["sha256"]:
            raise RecoveryError("ACTUAL_INPUT_DRIFT")
    (output / "actual_dialogue_inputs.jsonl").write_bytes(
        b"".join(canonical(item) + b"\n" for item in inputs)
    )
    return {
        "joins": joins,
        "original_source_template_comparisons": comparisons,
        "input_hashes": [{k: v for k, v in row.items() if k != "raw_bytes_hex"} for row in inputs],
        "text_comparison_census": dict(Counter(str(row["text_equal"]) for row in comparisons)),
        "scope": "Historical metadata and narrative synchronization; no current packet admission, native carrier evaluation, or historical model-call authentication",
        "missing_original_native_inputs": [
            "Every historical round's exact d0/d1/residual and replayable native certificate",
            "Complete final AST candidate source; retained narrative truncates its proposal payload",
            "Source-event binding to the actual historical generator/evaluator bytes",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = run(args.engine_root.absolute(), args.output.absolute())
    print(
        json.dumps(
            {
                "custody_closed": receipt["custody_closed"],
                "source_files": len(receipt["capture_manifest"]),
                "original_test_count": sum(
                    r["tests_run"] for r in receipt["original_source_tests"]
                ),
                "self_sha256": receipt["self_sha256"],
                "dialogue_comparisons": receipt["dialogue_audit"]["text_comparison_census"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
