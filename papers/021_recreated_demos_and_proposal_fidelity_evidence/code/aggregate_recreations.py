"""Offline replay of all thirteen findings aggregate families through pinned algorithms.

No mathematical solver is defined here. Historical recounts, finite computations,
negative controls, and outstanding original obligations stay separate.
"""

from __future__ import annotations

import argparse
import ast
import copy
import dataclasses
import hashlib
import importlib.abc
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

PAPER = Path(__file__).absolute().parents[1]
ATLAS = "omega_engine_atlas/coda_atlas/omega_engine_pfp/"
P001 = ATLAS + "001_pfp_discrete_cochain_retraction_and_toy_involutions/"
P004 = ATLAS + "004_pfp_native_verification_and_evidence_custody/"
P006 = ATLAS + "006_pfp_epistemic_immune_system_and_cemetery_dag_mining/"
P008 = ATLAS + "008_pfp_mssn_tower_challenges_and_retraction_benchmarks/"
P009 = ATLAS + "009_pfp_adversarial_dialectics_and_terminal_reality_gates/"
P010 = ATLAS + "010_pfp_holonomy_checks_and_model_pilots/"
FSP = "omega_engine_projects/fsp/meron_sign_problem/code/"
PFP = (
    "omega_engine_education/documentation/030_the_symbol_game_proposal_fidelity_protocol_pfp/demos/"
)
AGGREGATES = (
    "FSP_BLIND_CLUSTER_RECOVERY",
    "MUB6_AFFINE_PHASE_ANSATZ",
    "AST_REFACTORING_RETRACTION",
    "SPECIMEN_MT000_REDUCTION",
    "UNIFIED_PACKET_STREAMS",
    "EIGHT_BEAT_DIALOGUE",
    "RETRACTION_CONDITIONING",
    "ANTIMORPHISM_FARM",
    "FSP_PHYSICS_RETRACTIONS",
    "PAIRED_ADVERSARIAL_DEBATE",
    "DISCRETE_GEOMETRY_PROBES",
    "PHARMACY_CATALOG",
    "CHALLENGE_MUTATION_SUITES",
)
EXTRA_FILES = (
    "omega_engine_pfp/controllers/symbol_game_controller.py",
    "omega_engine_operating_system/python/adapters/rust_host/theory_requests.py",
    PFP + "demos/demos_runner.py",
    FSP + "meron_schema.sql",
    FSP + "prompt_builder.py",
    FSP + "antibody_miner.py",
    P008 + "code/retraction_benchmark_runner.py",
    P008 + "code/tests/test_008_source_bound_examples.py",
    P008 + "docs/source_archive/source_index.json",
    P008 + "docs/source_archive/c005_working_report.md",
    P004 + "code/l1_symbol_game_governor.py",
    "omega_engine_providers/adapters/native_functional.py",
    P009 + "code/triangle_cycle_sum.py",
    P009 + "code/review_counts.py",
    P001 + "code/certificate_gate.py",
    P001 + "code/exact_fock_gap.py",
    P010 + "code/holonomy.py",
    "omega_engine_projects/mub6/code/conj2_symbolic_verification/test_karlsson_conj2.py",
    *(
        P010 + "code/data/c017/" + name + ".json"
        for name in (
            "pois_01",
            "base_01",
            "base_02",
            "base_03",
            "base_13",
            "model_claims",
            "provenance",
        )
    ),
)


class AggregateReplayError(ValueError):
    pass


UNASSERTED = object()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def strict_equal(actual, expected) -> bool:
    if type(actual) is not type(expected):
        return False
    if type(actual) is dict:
        return set(actual) == set(expected) and all(
            strict_equal(actual[key], expected[key]) for key in actual
        )
    if type(actual) in (list, tuple):
        return len(actual) == len(expected) and all(
            strict_equal(left, right) for left, right in zip(actual, expected)
        )
    return actual == expected


def local_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def empty_cache_configuration(
    prefix: Path, *, activate: bool = False, worker: bool = False
) -> dict:
    """Refuse existing bytecode and redirected cache paths before source imports."""
    if not prefix.is_absolute():
        raise AggregateReplayError("ABSOLUTE_BYTECODE_CACHE_REQUIRED")
    for path in reversed((prefix, *prefix.parents)):
        info = path.lstat()
        if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
            raise AggregateReplayError("REGULAR_BYTECODE_CACHE_DIRECTORY_REQUIRED")
        if getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise AggregateReplayError("REDIRECTED_BYTECODE_CACHE_REFUSED")
    if any(prefix.iterdir()):
        raise AggregateReplayError("EMPTY_BYTECODE_CACHE_REQUIRED")
    if activate:
        sys.pycache_prefix = str(prefix)
        sys.dont_write_bytecode = True
    if sys.pycache_prefix != str(prefix) or not sys.dont_write_bytecode:
        raise AggregateReplayError("FRESH_BYTECODE_CACHE_CONFIGURATION_REQUIRED")
    if worker and not sys.flags.dont_write_bytecode:
        raise AggregateReplayError("WORKER_INTERPRETER_B_FLAG_REQUIRED")
    return {
        "pycache_prefix": str(prefix),
        "initial_cache_entries": [],
        "dont_write_bytecode": sys.dont_write_bytecode,
        "interpreter_dont_write_bytecode_flag": bool(sys.flags.dont_write_bytecode),
        "regular_unredirected_cache_directory": True,
    }


def jsonable(value):
    if dataclasses.is_dataclass(value):
        return jsonable(dataclasses.asdict(value))
    if isinstance(value, Fraction):
        return str(value)
    if type(value) is float:
        return {"inexact_float_repr": repr(value)}
    if type(value) is dict:
        return {str(key): jsonable(item) for key, item in value.items()}
    if type(value) in (tuple, list):
        return [jsonable(item) for item in value]
    if value is None or type(value) in (str, int, bool):
        return value
    return {"type": type(value).__name__, "repr": repr(value)}


class Context:
    def __init__(self, capability: dict, output: Path, inventory: dict, replay):
        self.capability, self.output, self.inventory, self.replay = (
            capability,
            output,
            inventory,
            replay,
        )
        self.engine = Path(capability["engine_root"])
        self.sources = local_module("paper011_aggregate_custody", "source_custody.py")
        self.journal: list[dict] = []
        self.observations: list[dict] = []
        self.read_paths: set[str] = set()
        self.modules: dict[str, object] = {}

    def read(self, relative: str) -> bytes:
        if relative not in self.capability["files"]:
            raise AggregateReplayError("UNPINNED_INPUT: " + relative)
        data = self.sources._read_regular(self.engine, relative)
        if digest(data) != self.capability["files"][relative]:
            raise AggregateReplayError("INPUT_BYTES_CHANGED: " + relative)
        if relative not in self.read_paths:
            self.read_paths.add(relative)
            with (self.output / "actual_inputs.jsonl").open("ab") as stream:
                stream.write(
                    canonical({"path": relative, "sha256": digest(data), "bytes_hex": data.hex()})
                    + b"\n"
                )
        return data

    def data(self, relative: str):
        return self.replay.load(self.read(relative))

    def module(self, relative: str, name: str | None = None):
        name = name or "paper011_aggregate_" + digest(relative.encode())[:16]
        if name in self.modules:
            return self.modules[name]
        self.read(relative)
        path = self.engine / relative
        spec = importlib.util.spec_from_file_location(
            name, path, loader=self.replay.SourceLoader(path, self.engine, self.journal)
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        self.modules[name] = module
        return module

    def paths(self, family: str, suffix: str = "") -> list[str]:
        row = next(row for row in self.inventory["aggregate_demo_families"] if row["id"] == family)
        return [
            item["path"]
            for item in row["authoritative_sources"]
            if item["availability"] == "PRESENT" and item["path"].endswith(suffix)
        ]

    def observe(
        self, family: str, name: str, actual, *, expected=UNASSERTED, grade="FINITE_COMPUTATION"
    ) -> bool | None:
        asserted = expected is not UNASSERTED
        passed = strict_equal(actual, expected) if asserted else None
        self.observations.append(
            {
                "family": family,
                "name": name,
                "grade": grade,
                "actual": jsonable(actual),
                "expected": jsonable(expected) if asserted else None,
                "asserted": asserted,
                "passed": passed,
                "verification_status": "CONTROL_PASSED"
                if passed is True
                else "CONTROL_FAILED"
                if passed is False
                else "OBSERVATION_ONLY",
            }
        )
        return passed


class PinnedWolandFinder(importlib.abc.MetaPathFinder):
    """Resolve only the explicitly pinned the city owner, retaining source custody."""

    def __init__(self, ctx: Context):
        self.ctx = ctx

    def find_spec(self, fullname, path=None, target=None):
        if fullname != "omega_engine_woland" and not fullname.startswith("omega_engine_woland."):
            return None
        base = self.ctx.engine.joinpath(*fullname.split("."))
        initial = base / "__init__.py"
        candidate = initial if base.is_dir() else base.with_suffix(".py")
        relative = candidate.relative_to(self.ctx.engine).as_posix()
        self.ctx.read(relative)
        return importlib.util.spec_from_file_location(
            fullname,
            candidate,
            loader=self.ctx.replay.SourceLoader(candidate, self.ctx.engine, self.ctx.journal),
            submodule_search_locations=[str(base)] if candidate == initial else None,
        )


def original_ast_fixture(raw: bytes) -> tuple[dict, dict]:
    """Execute the original literal method with a capture-only composition callback."""
    tree = ast.parse(raw)
    matches = [
        node
        for cls in tree.body
        if isinstance(cls, ast.ClassDef) and cls.name == "SymbolGameController"
        for node in cls.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_live_ast_refactoring_specimen"
    ]
    if len(matches) != 1:
        raise AggregateReplayError("EXACT_ORIGINAL_AST_FIXTURE_METHOD_REQUIRED")
    method = matches[0]
    if (
        method.decorator_list
        or len(method.args.args) != 1
        or method.args.args[0].arg != "self"
        or method.args.posonlyargs
        or method.args.kwonlyargs
        or method.args.defaults
        or method.args.vararg
        or method.args.kwarg
    ):
        raise AggregateReplayError("SIDE_EFFECT_FREE_AST_FIXTURE_SIGNATURE_REQUIRED")
    body = list(method.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body.pop(0)
    stage_names = ["step_" + str(index) + "_sources" for index in range(1, 5)]
    if len(body) != 6:
        raise AggregateReplayError("LITERAL_FOUR_STAGE_AST_FIXTURE_REQUIRED")
    for node, name in zip(body[:4], stage_names):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            raise AggregateReplayError("LITERAL_FOUR_STAGE_AST_FIXTURE_REQUIRED")
        if not isinstance(node.targets[0], ast.Name) or node.targets[0].id != name:
            raise AggregateReplayError("ORIGINAL_AST_STAGE_ASSIGNMENT_REQUIRED")
        try:
            sources = ast.literal_eval(node.value)
        except (ValueError, TypeError) as exc:
            raise AggregateReplayError("LITERAL_AST_MODULE_SOURCES_REQUIRED") from exc
        if type(sources) is not dict or len(sources) != 3 or any(
            type(key) is not str or type(value) is not str for key, value in sources.items()
        ):
            raise AggregateReplayError("THREE_ORIGINAL_AST_MODULES_REQUIRED")
    progression, final = body[4:]
    if (
        not isinstance(progression, ast.Assign)
        or len(progression.targets) != 1
        or not isinstance(progression.targets[0], ast.Name)
        or progression.targets[0].id != "progression"
        or not isinstance(progression.value, ast.List)
        or [getattr(value, "id", None) for value in progression.value.elts] != stage_names
        or not isinstance(final, ast.Return)
        or not isinstance(final.value, ast.Call)
    ):
        raise AggregateReplayError("ORIGINAL_AST_PROGRESSION_CALLBACK_REQUIRED")
    call = final.value
    if (
        ast.unparse(call.func) != "self.use_case.run_live_ast_refactoring"
        or len(call.args) != 1
        or not isinstance(call.args[0], ast.Name)
        or call.args[0].id != "progression"
        or [keyword.arg for keyword in call.keywords] != ["task_id", "problem_title"]
        or any(not isinstance(keyword.value, ast.Constant) for keyword in call.keywords)
    ):
        raise AggregateReplayError("ORIGINAL_AST_PROGRESSION_CALLBACK_REQUIRED")
    namespace = {}
    extracted = "from __future__ import annotations\n" + ast.unparse(method) + "\n"
    exec(compile(extracted, "<pinned-original-ast-fixture-method>", "exec"), namespace)

    class CaptureOnly:
        def run_live_ast_refactoring(self, progression, *, task_id, problem_title):
            return {
                "progression": progression,
                "task_id": task_id,
                "problem_title": problem_title,
            }

    composition = type("CaptureComposition", (), {})()
    composition.use_case = CaptureOnly()
    fixture = namespace[method.name](composition)
    span = b"".join(raw.splitlines(keepends=True)[method.lineno - 1 : method.end_lineno])
    return fixture, {
        "method": method.name,
        "source_line": method.lineno,
        "source_end_line": method.end_lineno,
        "original_method_bytes_hex": span.hex(),
        "original_method_sha256": digest(span),
        "extracted_method_sha256": digest(extracted.encode("utf-8")),
        "composition": "Original method calls capture-only run_live_ast_refactoring callback; no controller constructor, provider or emitter is executed.",
    }


class BoundNativeFunctionalPort:
    """Exact transport composition; both evaluation and replay stay native."""

    def __init__(self, host, builders, receipt_type):
        self.host, self.builders, self.receipt_type = host, builders, receipt_type
        self.calls = []

    def invoke(self, action: str, payload: dict) -> dict:
        outcome = self.host.invoke_runtime(action, payload)
        if outcome.is_ok is not True:
            raise AggregateReplayError("NATIVE_FUNCTIONAL_TRANSPORT_REFUSED: " + repr(outcome))
        envelope = outcome.unwrap()
        if type(envelope) is not dict or envelope.get("success") is not True:
            raise AggregateReplayError("NATIVE_FUNCTIONAL_ACTION_REFUSED: " + repr(envelope))
        if type(envelope.get("result")) is not dict:
            raise AggregateReplayError("NATIVE_FUNCTIONAL_RESULT_REQUIRED")
        return envelope["result"]

    def replay(self, request: dict, receipt: dict) -> dict:
        built = self.builders.functional_verify_payload(request, receipt)
        if built.is_ok is not True:
            raise AggregateReplayError("EXACT_FUNCTIONAL_VERIFY_PAYLOAD_REQUIRED")
        return self.invoke("functional_verify", built.unwrap())

    def evaluate_functional(self, d0, d1, residual):
        built = self.builders.functional_evaluate_payload(d0, d1, residual)
        if built.is_ok is not True:
            raise AggregateReplayError("EXACT_FUNCTIONAL_EVALUATE_PAYLOAD_REQUIRED")
        request = built.unwrap()
        receipt = self.invoke("functional_evaluate", request)
        verified = self.replay(request, receipt)
        if verified.get("accepted") is not True or verified.get("mismatched_fields") != []:
            raise AggregateReplayError("NATIVE_FUNCTIONAL_CERTIFICATE_REPLAY_REQUIRED")
        self.calls.append({"request": request, "receipt": receipt, "verification": verified})
        return self.receipt_type(
            phi1=Fraction(receipt["phi1"]),
            gamma2=Fraction(receipt["gamma2"]),
            diagnostic_class=receipt["diagnostic_class"],
            input_digest=receipt["input_digest"],
            dual_witness=tuple(Fraction(value) for value in receipt["dual_witness"]),
            primal_residual=tuple(Fraction(value) for value in receipt["primal_residual"]),
            success=True,
            authority_effect="None",
        )


def explicit_control_outcome(observations: list[dict], family: str) -> dict:
    controls = [
        row for row in observations if row["family"] == family and row.get("asserted") is True
    ]
    return {
        "asserted_controls": len(controls),
        "passed_controls": sum(row.get("passed") is True for row in controls),
        "failed_controls": sum(row.get("passed") is not True for row in controls),
        "observation_only_records": sum(
            row["family"] == family and row.get("asserted") is not True for row in observations
        ),
        "all_explicit_controls_passed": bool(controls)
        and all(row.get("passed") is True for row in controls),
    }


def bind_import_journal_root(rows: list[dict], source_root: str) -> list[dict]:
    if source_root != PFP:
        raise AggregateReplayError("IMPORT_JOURNAL_SOURCE_ROOT_NOT_DECLARED")
    bound = []
    for row in rows:
        relative = row.get("path")
        if (
            type(relative) is not str
            or not relative
            or ":" in relative
            or "\\" in relative
            or any(part in {"", ".", ".."} for part in relative.split("/"))
        ):
            raise AggregateReplayError("IMPORT_JOURNAL_PATH_ESCAPE")
        bound.append(
            {
                **row,
                "path": source_root + relative,
                "source_relative_path": relative,
                "declared_import_root": source_root,
            }
        )
    return bound


def meron(ctx: Context, family: str) -> dict:
    model = ctx.module(FSP + "meron_exact_model.py", "meron_exact_model")
    oracle_module = ctx.module(FSP + "oracle.py", "oracle")
    problem = ctx.module(FSP + "blind_problem.py", "blind_problem")
    prompts = ctx.module(FSP + "prompt_builder.py", "prompt_builder")
    miner_module = ctx.module(FSP + "antibody_miner.py", "antibody_miner")
    ctx.read(FSP + "meron_schema.sql")
    oracle = oracle_module.BlindClusterOracle()
    measured = {
        "graphs": oracle.total_subgraphs,
        "configurations": oracle.total_configurations,
        "negative": oracle.negative_configurations,
        "zero_charge": oracle.zero_charge_subgraphs,
        "cancelling": oracle.cancelling_subgraphs,
        "signed_partition": oracle.signed_partition,
        "reduced_partition": oracle.reduced_partition,
        "transfer_trace": oracle.independent_transfer_trace,
    }
    ok = ctx.observe(
        family,
        "independent_orbit_and_transfer_counts",
        measured,
        expected={
            "graphs": 256,
            "configurations": 1296,
            "negative": 192,
            "zero_charge": 199,
            "cancelling": 57,
            "signed_partition": "912",
            "reduced_partition": "912",
            "transfer_trace": "912",
        },
    )
    defects = model.meron_model_defects(oracle._con)
    ctx.observe(family, "relational_model_defects", defects)
    packet = problem.generate_blind_problem_packet()
    miner = miner_module.AntibodyMiner(oracle)
    report = ctx.data(FSP + "results/master_evaluation_report.json")
    rescored = []
    for arm, cells in report["arms"].items():
        for model_name, cell in cells.items():
            rounds = cell.get("history", [cell])
            for index, turn in enumerate(rounds, 1):
                raw = turn.get("raw_response", turn.get("raw_text"))
                source = "retained_response" if type(raw) is str else "retained_parsed_json"
                if type(raw) is not str:
                    raw = json.dumps(turn.get("parsed", {}))
                result, _ = miner.evaluate_and_mine(raw, [])
                rescored.append(
                    {
                        "arm": arm,
                        "model": model_name,
                        "round": index,
                        "response_source": source,
                        "actual_response_bytes_hex": raw.encode("utf-8").hex(),
                        "current_score": result["score"],
                        "historical_score": turn.get("score"),
                        "derivation_verified": False,
                    }
                )
    ctx.observe(
        family,
        "all_retained_arm_observations",
        rescored,
        grade="HISTORICAL_RECOUNT_WITH_CURRENT_RUBRIC",
    )
    leaks = []
    for name, prompt in (
        ("arm1", prompts.build_prompt_arm1_constrained_decoding(packet)),
        ("arm2", prompts.build_prompt_arm2_attention_masking(packet)),
        ("arm3", prompts.build_prompt_arm3_hieroglyphics(packet)),
    ):
        problem.assert_lexical_hygiene(prompt)
        leaks.append(
            {
                "arm": name,
                "prompt_bytes_hex": prompt.encode("utf-8").hex(),
                "lexical_pass": True,
                "answer_determined_by_1296_and_19_over_27": "19/27" in prompt and "1,296" in prompt,
            }
        )
    ok &= ctx.observe(
        family,
        "lexical_hygiene_does_not_remove_answer",
        all(row["answer_determined_by_1296_and_19_over_27"] for row in leaks),
        expected=True,
        grade="NEGATIVE_CONTROL",
    )
    ctx.observe(
        family,
        "actual_reconstructed_prompts",
        leaks,
        grade="RECONSTRUCTED_INPUTS_NOT_PROVIDER_ATTESTATION",
    )
    oracle._con.close()
    return {
        "finite_computation_passed": bool(ok),
        "retained_observations": len(rescored),
        "remaining": [
            "Historical rubric checks fields and keywords rather than proof validity; no blind model-discovery or immune-efficacy claim."
        ],
    }


def mub(ctx: Context, family: str) -> dict:
    module = ctx.module(
        "omega_engine_projects/mub6/code/conj2_symbolic_verification/test_karlsson_conj2.py"
    )
    x, y = module.symbols("x y", nonzero=True)
    matrix = module.displayed_affine_ansatz(x, y)
    values = [
        {
            "magnitude": magnitude,
            "pattern": pattern,
            "value": str(module.signed_laurent_sum(matrix, pattern)),
        }
        for magnitude in (1, 3)
        for pattern in module.sign_patterns(magnitude)
    ]
    passed = ctx.observe(
        family,
        "all_40_symbolic_signed_laurent_sums",
        all(row["value"] == "0" for row in values),
        expected=True,
    )
    ctx.observe(family, "actual_symbolic_results", values)
    broken = matrix.copy()
    broken[1, 1] = 1
    failures = module.verify_magnitude(broken, 1)
    passed &= ctx.observe(
        family,
        "broken_column_pair_detected",
        bool(failures),
        expected=True,
        grade="NEGATIVE_CONTROL",
    )
    fixture = "omega_engine/crates_rs/omega_mub/artifacts/mub6_conj2_verification.json"
    ctx.observe(
        family,
        "retained_native_fixture",
        ctx.data(fixture),
        grade="HISTORICAL_FIXTURE_NOT_FRESH_NATIVE_EXECUTION",
    )
    return {
        "finite_computation_passed": bool(passed),
        "remaining": [
            "Displayed affine ansatz only; fresh native MUB verifier run and source-to-binary build receipt are separate obligations."
        ],
    }


def packets(ctx: Context, family: str) -> dict:
    from omega_engine_pfp.domain.entities.packet_envelope import PacketEnvelopeV2

    files = ctx.paths(family, ".jsonl")
    rows, groups = [], defaultdict(list)
    for path in files:
        for number, line in enumerate(ctx.read(path).splitlines(), 1):
            if not line.strip():
                continue
            item = ctx.replay.load(line)
            groups[item.get("run_id", "UNKNOWN")].append(item)
            packet = item.get("packet")
            if type(packet) is not dict:
                rows.append(
                    {"path": path, "line": number, "packet_status": "TRACE_RECORD_WITHOUT_PACKET"}
                )
                continue
            try:
                current = PacketEnvelopeV2.from_dict(packet)
                decoded = jsonable(current.payload)
                rows.append(
                    {
                        "path": path,
                        "line": number,
                        "packet_id": current.packet_id,
                        "packet_status": "CURRENT_TRANSPORT_VERIFIED",
                        "payload": decoded,
                    }
                )
            except Exception as exc:
                rows.append(
                    {
                        "path": path,
                        "line": number,
                        "packet_status": "CURRENT_TRANSPORT_REFUSED",
                        "reason": str(exc),
                    }
                )
    ctx.observe(
        family,
        "every_bound_stream_record",
        rows,
        grade="HISTORICAL_RECOUNT_AND_CURRENT_TRANSPORT_CHECK",
    )
    transitions = [
        {
            "run_id": run,
            "rows": len(items),
            "adjacent_transitions": max(0, len(items) - 1),
            "carrier_ids": sorted({item.get("carrier_id", "UNKNOWN") for item in items}),
        }
        for run, items in sorted(groups.items())
    ]
    ctx.observe(family, "current_stream_transition_census", transitions, grade="HISTORICAL_RECOUNT")
    # A fresh positive transport computation checks the current codec separately
    # from any historical score or untrusted terminal label.
    from omega_engine_pfp.domain.packet_codec import PacketCodec

    positive = PacketCodec.seal(
        {"original_family": family, "preserved_carrier": "finite_transport_control"},
        "paper011_aggregate_transport",
    )
    clean = PacketCodec.verify(positive)[0]
    tampered = copy.deepcopy(positive)
    tampered["payload"]["preserved_carrier"] = "changed"
    caught = PacketCodec.verify(tampered)[0] is False
    passed = ctx.observe(
        family,
        "fresh_bound_packet_and_payload_corruption",
        {"clean_verified": clean, "corruption_rejected": caught},
        expected={"clean_verified": True, "corruption_rejected": True},
    )
    return {
        "finite_computation_passed": passed,
        "retained_records": len(rows),
        "current_transport_verified": sum(
            row["packet_status"] == "CURRENT_TRANSPORT_VERIFIED" for row in rows
        ),
        "remaining": [
            "Transport identity and historical transition recount do not certify AST edits, strict rational descent, closure, or exact repair on the original carrier."
        ],
    }


def original_live_ast(ctx: Context, family: str) -> dict:
    """Replay the retained four-stage source fixture with a native injected port."""
    source_path = "omega_engine_pfp/controllers/symbol_game_controller.py"
    fixture, extraction = original_ast_fixture(ctx.read(source_path))
    if any(
        name == "omega_engine_woland" or name.startswith("omega_engine_woland.")
        for name in sys.modules
    ):
        raise AggregateReplayError("PRELOADED_WOLAND_SOURCE_CUSTODY_UNAVAILABLE")
    finder = PinnedWolandFinder(ctx)
    sys.meta_path.insert(0, finder)
    try:
        from omega_engine_woland.domain.cochain.metrics_evaluator import ASTMetricsEvaluator
        from omega_engine_woland.domain.ports import FunctionalEvaluationReceiptV1
        from omega_engine_operating_system.python.adapters.rust_host import theory_requests
        from omega_engine_operating_system.python.adapters.rust_host.ffi import RustSymbolGameHost

        host = RustSymbolGameHost(binary=Path(ctx.capability["binaries"]["symbol_game"]["path"]))
        port = BoundNativeFunctionalPort(host, theory_requests, FunctionalEvaluationReceiptV1)
        evaluator = ASTMetricsEvaluator(evaluator_port=port)
        controls = [
            ctx.observe(
                family,
                "original_live_ast_callback_and_complete_input_scope",
                {
                    "task_id": fixture["task_id"],
                    "stage_count": len(fixture["progression"]),
                    "module_counts": [len(stage) for stage in fixture["progression"]],
                },
                expected={
                    "task_id": "live_ast_refactor_clean_arch",
                    "stage_count": 4,
                    "module_counts": [3, 3, 3, 3],
                },
            )
        ]
        ctx.observe(
            family,
            "original_live_ast_source_and_capture_composition",
            {"source_path": source_path, "source_sha256": digest(ctx.read(source_path)), **fixture, **extraction},
            grade="PINNED_ORIGINAL_METHOD_AND_ORIGINAL_CALLBACK_INPUTS",
        )
        stages = []
        for index, sources in enumerate(fixture["progression"]):
            source_state = copy.deepcopy(sources)
            calls_before = len(port.calls)
            report = evaluator.evaluate_sources(sources)
            if len(port.calls) != calls_before + 1:
                raise AggregateReplayError("ONE_NATIVE_AST_EVALUATION_PER_ORIGINAL_STAGE_REQUIRED")
            call = port.calls[-1]
            damaged = copy.deepcopy(call["receipt"])
            damaged["phi1"] = str(Fraction(damaged["phi1"]) + 1)
            rejected_certificate = port.replay(call["request"], damaged)
            changed_request = copy.deepcopy(call["request"])
            if not changed_request["residual"]:
                raise AggregateReplayError("ORIGINAL_AST_EDGE_COORDINATES_REQUIRED")
            changed_request["residual"][0] = str(Fraction(changed_request["residual"][0]) + 1)
            rejected_state = port.replay(changed_request, call["receipt"])
            native = call["receipt"]
            controls.append(
                ctx.observe(
                    family,
                    "original_live_ast_stage_" + str(index + 1) + "_native_and_corruption_controls",
                    {
                        "source_inputs_unchanged": strict_equal(sources, source_state),
                        "native_certificate_replayed": call["verification"]["accepted"],
                        "report_uses_actual_native_receipt": report.evidence_sha256 == native["input_digest"],
                        "damaged_certificate_accepted": rejected_certificate["accepted"],
                        "changed_input_state_accepted": rejected_state["accepted"],
                        "active_defects": report.active_obstruction_count,
                        "source_report_is_exact": report.is_exact,
                        "second_stage_repairs": native["second_stage_repairs"],
                    },
                    expected={
                        "source_inputs_unchanged": True,
                        "native_certificate_replayed": True,
                        "report_uses_actual_native_receipt": True,
                        "damaged_certificate_accepted": False,
                        "changed_input_state_accepted": False,
                        "active_defects": [2, 2, 1, 0][index],
                        "source_report_is_exact": index == 3,
                        "second_stage_repairs": "none",
                    },
                )
            )
            stages.append(
                {
                    "stage": index + 1,
                    "original_module_sources": sources,
                    "source_state_sha256": digest(canonical(sources)),
                    "original_dependency_nodes": list(evaluator.complex.graph.nodes),
                    "original_dependency_edges": list(evaluator.complex.graph.edges),
                    "source_report": report,
                    "native_request_and_receipt": call,
                    "damaged_certificate": damaged,
                    "damaged_certificate_verdict": rejected_certificate,
                    "changed_input_state": changed_request,
                    "changed_input_state_verdict": rejected_state,
                }
            )
        # A cycle-row corruption is a changed carrier, and is refused as such.
        invalid_carrier = copy.deepcopy(port.calls[0]["request"])
        invalid_carrier["d1"]["rows"][0][0] = str(
            Fraction(invalid_carrier["d1"]["rows"][0][0]) + 1
        )
        refused = host.invoke_runtime("functional_evaluate", invalid_carrier)
        if refused.is_ok is not True:
            raise AggregateReplayError("INVALID_CARRIER_NATIVE_OUTCOME_REQUIRED")
        refusal = refused.unwrap()
        controls.append(
            ctx.observe(
                family,
                "original_live_ast_changed_cycle_carrier_refused",
                {
                    "native_success": refusal.get("success"),
                    "chain_law_refusal": "CHAIN_LAW_VIOLATED" in str(refusal.get("error")),
                },
                expected={"native_success": False, "chain_law_refusal": True},
                grade="NEGATIVE_NATIVE_CARRIER_CONTROL",
            )
        )
        ctx.observe(
            family,
            "all_original_live_ast_states_matrices_and_native_evidence",
            {
                "task_id": fixture["task_id"],
                "stages": stages,
                "changed_cycle_carrier": invalid_carrier,
                "changed_cycle_carrier_outcome": refusal,
                "carrier_changes_between_source_stages": True,
                "historical_three_session_scores_reproduced": False,
            },
            grade="ORIGINAL_FOUR_STAGE_AST_NATIVE_COMPUTATION_WITH_RESIDUAL_STAGES",
        )
        return {
            "finite_computation_passed": all(control is True for control in controls),
            "original_task_id": fixture["task_id"],
            "original_source_stages_executed": len(stages),
            "native_stage_metrics": [
                {
                    "stage": row["stage"],
                    "phi1": row["native_request_and_receipt"]["receipt"]["phi1"],
                    "gamma2": row["native_request_and_receipt"]["receipt"]["gamma2"],
                    "active_defects": row["source_report"].active_obstruction_count,
                    "is_exact": row["source_report"].is_exact,
                }
                for row in stages
            ],
            "remaining": [
                "Original four-stage live_ast_refactor_clean_arch source fixture only; it does not reproduce the three historical score-only AST packet sessions or specimen lambda/seeds.",
                "Each source stage constructs its own dependency carrier. No same-carrier strict descent, behavioral equivalence of the edited programs, general AST repair, or model discovery is established.",
            ],
        }
    finally:
        sys.meta_path.remove(finder)


def dialogue(ctx: Context, family: str) -> dict:
    names = next(
        row["members"] for row in ctx.inventory["aggregate_demo_families"] if row["id"] == family
    )
    rows = []
    for path in ctx.paths(family, ".md"):
        text = ctx.read(path).decode("utf-8")
        found = re.findall(r"^##### Round (\d+) Beat (\d+): (\w+)", text, re.MULTILINE)
        groups = defaultdict(list)
        for round_id, beat, role in found:
            groups[round_id].append((int(beat), role))
        for round_id, roles in sorted(groups.items()):
            rows.append(
                {
                    "path": path,
                    "round": int(round_id),
                    "actual_roles": roles,
                    "all_eight_in_order": roles == list(enumerate(names, 1)),
                }
            )
    passed = ctx.observe(
        family,
        "all_retained_round_role_orders",
        bool(rows) and all(row["all_eight_in_order"] for row in rows),
        expected=True,
        grade="HISTORICAL_NARRATIVE_RECOUNT",
    )
    ctx.observe(family, "round_observations", rows, grade="HISTORICAL_NARRATIVE_RECOUNT")
    return {
        "finite_computation_passed": passed,
        "retained_rounds": len(rows),
        "remaining": [
            "Narrative role agreement is no mathematical certificate; original per-round packet/evaluation synchronization must retain its native carrier obligations."
        ],
    }


def original_k4_sources(ctx: Context):
    governor = ctx.module(P004 + "code/l1_symbol_game_governor.py", "l1_symbol_game_governor")
    topology = ctx.module(
        PFP + "demos/mssn/k4_higher_rank_verification.py",
        ctx.replay.LOCAL_PREFIX + ".demos.mssn.k4_higher_rank_verification",
    )
    return governor, topology, topology.TOPOLOGY_K4_STANDARD


def exact_move_claims(move: dict) -> dict:
    claims = move.get("proposed_claims")
    if type(claims) is not dict:
        raise AggregateReplayError("CUT_CLAIMS_OBJECT_REQUIRED")
    translated = {}
    for edge, value in claims.items():
        if type(edge) is not str or len(edge.split("->")) != 2 or type(value) is not int:
            raise AggregateReplayError("EXACT_DIRECTED_INTEGER_CLAIM_REQUIRED")
        translated[tuple(edge.split("->"))] = value
    return translated


def replay_k4_rows(ctx: Context, rows: list[dict], spec, governor, runner, policy: str) -> dict:
    gov = governor.L1SymbolGameGovernor(spec.to_constraint_graph())
    actual_turns = []
    source_valid = True
    for row in rows:
        transport = ctx.output / "native_transport_calls.jsonl"
        native_start = transport.stat().st_size if transport.exists() else 0
        raw = row.get("raw_response")
        if type(raw) is not str:
            raise AggregateReplayError("RAW_PROVIDER_RESPONSE_MISSING")
        move = ctx.replay.load(raw.encode("utf-8"))
        if type(move) is not dict:
            raise AggregateReplayError("RAW_MOVE_OBJECT_REQUIRED")
        matches = strict_equal(move, row["parsed_move"])
        source_valid &= matches
        before = gov.primary_obstruction()
        transformed_claims = None
        omitted_edges = []
        if move.get("move_type") == "ASSERT":
            if type(move.get("value")) is not int:
                raise AggregateReplayError("EXACT_ASSERT_VALUE_REQUIRED")
            verdict = gov.step_assert(move["u"], move["v"], move["value"])
        elif move.get("move_type") == "CUT":
            claims = exact_move_claims(move)
            omitted_edges = [
                "->".join(edge.key) for edge in gov.graph.edges if edge.key not in claims
            ]
            if policy == "DOCUMENTED_HISTORICAL_ZERO_FILL":
                transformed_claims = {edge.key: claims.get(edge.key, 0) for edge in gov.graph.edges}
                transformed_claims.update(claims)
                claims = transformed_claims
            verdict = gov.step_cut(proposed_claims=claims)
        elif move.get("move_type") == "VERIFY":
            verdict = gov.step_verify(move.get("obligation", "ZERO_OBSTRUCTION"))
        else:
            raise AggregateReplayError(
                "RETAINED_MOVE_PROTOCOL_UNSUPPORTED: " + str(move.get("move_type"))
            )
        after = gov.primary_obstruction()
        actual_turns.append(
            {
                "turn": row["turn"],
                "raw_response_sha256": digest(raw.encode("utf-8")),
                "raw_move": move,
                "raw_matches_retained_parsed_move": matches,
                "transformed_claims": {
                    "->".join(edge): value for edge, value in transformed_claims.items()
                }
                if transformed_claims is not None
                else None,
                "omitted_declared_edges": omitted_edges,
                "admitted_zero_fill_fidelity_loss": bool(omitted_edges)
                and transformed_claims is not None
                and verdict.admitted is True,
                "phi1_before": str(before),
                "actual_verdict": jsonable(verdict),
                "phi1_after": str(after),
                "native_transport_byte_span": [native_start, transport.stat().st_size],
                "actual_post_claims": {
                    "->".join(edge): str(value) for edge, value in gov.edge_claims.items()
                },
                "historical_functional_claims": row.get("unverified_functional_claims"),
            }
        )
    native_final_start = transport.stat().st_size
    final_phi, gauge = governor.compute_phi1(gov.graph, gov.claims_cochain())
    final_edges = [(edge.u, edge.v, gov.edge_claims.get(edge.key, 0)) for edge in gov.graph.edges]
    instance = runner.GraphInstance(
        "retained_k4_terminal", list(spec.vertices), final_edges, "", ""
    )
    potential_checked = (
        runner.verify_potential(instance, {vertex: int(value) for vertex, value in gauge.items()})
        if final_phi == 0 and all(value.denominator == 1 for value in gauge.values())
        else None
    )
    shared_edges = (("a", "b"), ("b", "c"), ("d", "a"))
    shared_preserved = all(
        gov.edge_claims.get(edge) == spec.ground_claims[edge] for edge in shared_edges
    )
    return {
        "policy": policy,
        "raw_source_valid": source_valid,
        "policy_equivalence": "UNCHANGED_CURRENT_GOVERNOR"
        if policy == "CURRENT_COMPLETE_CUT"
        else "DOCUMENTED_POLICY_EMULATION_NOT_EXECUTION_OF_MISSING_HISTORICAL_SCRIPT",
        "turns": actual_turns,
        "final_phi1": str(final_phi),
        "native_minimizing_gauge": jsonable(gauge),
        "final_native_transport_byte_span": [native_final_start, transport.stat().st_size],
        "final_potential_checked": potential_checked,
        "terminal_zero": final_phi == 0,
        "original_shared_edges_preserved": shared_preserved,
        "faithful_shared_edge_repair": final_phi == 0 and shared_preserved,
        "provider_authentication": "NOT_ESTABLISHED_BY_CONTENT_HASH",
    }


def retained_conditioning(ctx: Context, family: str, runner) -> dict:
    governor, _, spec = original_k4_sources(ctx)
    index = ctx.data(P008 + "docs/source_archive/source_index.json")
    cells = []
    for entry in index["entries"]:
        if "/k4_traces/" not in entry["path"]:
            continue
        path = P008 + entry["path"]
        raw = ctx.read(path)
        if digest(raw) != entry["sha256"] or len(raw) != entry["bytes"]:
            raise AggregateReplayError("ARCHIVED_CONDITIONING_SOURCE_CHANGED: " + path)
        physical = raw.splitlines(keepends=True)
        rows = [ctx.replay.load(line) for line in physical]
        model = rows[0]["model"]
        condition = re.search(r"instruct_(.*?)_\d+\.jsonl$", path).group(1)
        if any(row["model"] != model or row["task_id"] != rows[0]["task_id"] for row in rows):
            raise AggregateReplayError("TRACE_IDENTITY_CHANGED_WITHIN_CELL")
        cells.append(
            {
                "path": path,
                "source_sha256": digest(raw),
                "physical_line_sha256": [digest(line) for line in physical],
                "model": model,
                "condition": condition,
                "trace_denominator": 1,
                "current_strict": replay_k4_rows(
                    ctx, rows, spec, governor, runner, "CURRENT_COMPLETE_CUT"
                ),
                "historical_policy_emulation": replay_k4_rows(
                    ctx, rows, spec, governor, runner, "DOCUMENTED_HISTORICAL_ZERO_FILL"
                ),
            }
        )
    census = Counter((cell["model"], cell["condition"]) for cell in cells)
    source_checks = (
        len(cells) == 8
        and len(census) == 8
        and all(count == 1 for count in census.values())
        and all(
            cell[policy]["raw_source_valid"] is True
            and (
                cell[policy]["terminal_zero"] is False
                or cell[policy]["final_potential_checked"] is True
            )
            for cell in cells
            for policy in ("current_strict", "historical_policy_emulation")
        )
    )
    passed = ctx.observe(
        family,
        "eight_raw_trace_cells_and_terminal_certificates",
        bool(source_checks),
        expected=True,
    )
    ctx.observe(
        family,
        "every_source_bound_raw_turn_both_named_policies",
        cells,
        grade="NATIVE_MATH_WITH_EXPLICIT_HISTORICAL_POLICY_EMULATION",
    )
    return {
        "controls_passed": passed,
        "cells": cells,
        "trace_count": len(cells),
        "raw_turns": sum(len(cell["current_strict"]["turns"]) for cell in cells),
    }


def c005_controls(ctx: Context, family: str, runner) -> dict:
    folder = PFP + "challenges/a_mechanism/c005_hosted_decode_controls/"
    cases = ctx.module(folder + "cases.py").get_hidden_base_cases()
    cases = [case for case in cases if case["kind"] == "consistency"]
    checkers = ctx.module(folder + "checkers.py")
    native = ctx.module("omega_engine_providers/adapters/native_functional.py")
    records = []
    for case in cases:
        nodes = sorted({node for u, v, _ in case["edges"] for node in (u, v)})
        instance = runner.GraphInstance(case["case_id"], nodes, case["edges"], "", "")
        cert = runner.host_certificate(instance)
        transport = ctx.output / "native_transport_calls.jsonl"
        native_start = transport.stat().st_size if transport.exists() else 0
        phi1, native_gauge = native.compute_graph_phi1(
            nodes,
            [(u, v, 1) for u, v, _ in case["edges"]],
            {(u, v): value for u, v, value in case["edges"]},
        )
        checked = (
            runner.verify_potential(instance, cert["potential"])
            if cert["verdict"] == "CONSISTENT"
            else runner.verify_inconsistency_witness(instance, cert["dual_witness_walk"])
        )
        label = "CONSISTENT" if cert["verdict"] == "CONSISTENT" else "INCONSISTENT"
        native_label = "CONSISTENT" if phi1 == 0 else "INCONSISTENT"
        result = checkers.verify_consistency_certificate(
            case["edges"], case["expected_verdict"], case["expected_certificate"]
        )
        records.append(
            {
                "actual_generated_case": case,
                "actual_host_certificate": cert,
                "certificate_checked": checked,
                "native_phi1": str(phi1),
                "native_minimizing_gauge": jsonable(native_gauge),
                "native_label_matches_checked_host": native_label == label,
                "native_transport_byte_span": [native_start, transport.stat().st_size],
                "actual_C005_checker_result": jsonable(result),
                "label_matches_checked_host": label == case["expected_verdict"],
            }
        )
    control_ok = len(records) == 50 and all(
        record["certificate_checked"] is True
        and record["native_label_matches_checked_host"] is True
        and record["label_matches_checked_host"] is True
        and record["actual_C005_checker_result"]["is_valid"] is True
        for record in records
    )
    passed = ctx.observe(
        family,
        "current_C005_50_case_labels_and_reference_certificates",
        bool(control_ok),
        expected=True,
    )
    ctx.observe(
        family,
        "current_C005_actual_cases_and_certificate_results",
        records,
        grade="FRESH_REFERENCE_CONTROL_NO_RETAINED_MODEL_OUTPUTS",
    )
    original_sources = {
        name: digest(ctx.read(folder + name))
        for name in ("benchmark_3arm_scratchpad.py", "benchmark_arm4_hybrid.py", "pipeline.json")
    }
    report = ctx.read(P008 + "docs/source_archive/c005_working_report.md")
    ctx.observe(
        family,
        "C005_original_model_run_replay_obligation",
        {
            "report_sha256": digest(report),
            "source_sha256": original_sources,
            "historical_runs": [
                {
                    "run": "three_arm",
                    "denominator": 50,
                    "counts": {"arm1": 25, "arm2": 36, "arm3": 19},
                },
                {"run": "hybrid", "denominator": 50, "counts": {"arm2": 38, "arm4": 4}},
            ],
            "counts_evidence": "TRANSCRIBED_FROM_RETAINED_REPORT_NOT_RESCORED",
            "historical_per_case_rows": "UNAVAILABLE",
            "historical_raw_provider_responses": "UNAVAILABLE",
            "historical_model_accuracy_recomputed": None,
            "score_contract": "Checker is_valid AND verdict equals independently bound ground truth; hybrid also requires correct canary residual",
            "midpoint_37_of_50": "NO_RETAINED_RUN_PRODUCED_THIS_COUNT",
        },
        grade="HISTORICAL_REPORT_AND_SCORER_CONTRACT_ONLY",
    )
    consistent = next(case for case in cases if case["expected_verdict"] == "CONSISTENT")
    wrong_label = checkers.verify_consistency_certificate(consistent["edges"], "INCONSISTENT", {})
    passed &= ctx.observe(
        family,
        "C005_checker_alone_accepts_wrong_negative_label",
        wrong_label.is_valid,
        expected=True,
        grade="DEMONSTRATED_NEED_FOR_EXTERNAL_GROUND_TRUTH_MATCH",
    )
    return {
        "controls_passed": passed,
        "reference_cases": len(records),
        "historical_model_rescoring": "MISSING_PER_CASE_AND_RAW_RESPONSE_BYTES",
    }


def conditioning(ctx: Context, family: str) -> dict:
    runner = ctx.module(P008 + "code/retraction_benchmark_runner.py")
    records = []
    passed = True
    for condition in runner.CONDITIONS:
        for receipt in runner.run_benchmark(
            condition, model="EXPLICIT_OFFLINE_STUB", client=runner.OfflineStubClient()
        ):
            value = dataclasses.asdict(receipt)
            identity_ok = runner.receipt_digest(receipt) == receipt.digest_sha256
            instance = runner.GraphInstance(**value["instance"])
            cert = value["host_certificate"]
            certificate_ok = (
                runner.verify_potential(instance, cert["potential"])
                if cert["verdict"] == "CONSISTENT"
                else runner.verify_inconsistency_witness(instance, cert["dual_witness_walk"])
            )
            passed &= identity_ok and certificate_ok
            records.append(
                {
                    "actual_receipt": value,
                    "digest_replayed": identity_ok,
                    "certificate_replayed": certificate_ok,
                }
            )
    ctx.observe(family, "all_four_six_case_offline_conditions", bool(passed), expected=True)
    ctx.observe(
        family,
        "actual_prompt_reply_instance_certificates",
        records,
        grade="OFFLINE_STUB_AND_EXACT_ORACLE_CONTROL",
    )
    retained = []
    for path in ctx.paths(family, ".jsonl"):
        data = [ctx.replay.load(line) for line in ctx.read(path).splitlines() if line.strip()]
        retained.append(
            {
                "path": path,
                "rows": len(data),
                "raw_reply_fields_present": sum(
                    any("response" in key or "raw" in key for key in row) for row in data
                ),
            }
        )
    ctx.observe(
        family, "all_retained_conditioning_trace_census", retained, grade="HISTORICAL_RECOUNT"
    )
    trace_replay = retained_conditioning(ctx, family, runner)
    c005 = c005_controls(ctx, family, runner)
    passed &= trace_replay["controls_passed"] is True and c005["controls_passed"] is True
    return {
        "finite_computation_passed": bool(passed),
        "offline_receipts": len(records),
        "retained_K4_raw_trace_cells": trace_replay["trace_count"],
        "retained_K4_raw_turns": trace_replay["raw_turns"],
        "C005_reference_cases": c005["reference_cases"],
        "remaining": [
            "Historical K4 zero-fill is an explicit documented-policy emulation through current native mathematics; the unretained original benchmark script and its loop-count rule are not executed.",
            "C005 original model runs cannot be rescored without their missing per-case rows and raw responses; current 50-case reference controls do not establish historical model accuracy.",
            "Historical model authenticity and a causal intervention estimate are not established by response content hashes or assisted repair prompts.",
        ],
    }


def retained_immune_controls(ctx: Context, family: str) -> bool:
    """Replay the retained bench on original patterns with explicit current defaults."""
    from omega_engine_epistemic_immune_system.domain import ClonalSelectionEngine, DetectorRule

    original = ctx.module(PFP + "demos/antimorphism_farm/immune_bench.py")
    panel = original.CLEAN_PHYSICS_SELF_PANEL
    entries = ctx.data(P006 + "code/fixtures/pharmacy_catalog_52cb5457f6c4.json")["antibodies"]
    rules = tuple(
        DetectorRule(entry["antibody_id"], entry["failure_class"], entry["target_pattern"])
        for _, entry in sorted(entries.items())
    )
    ctx.observe(
        family,
        "retained_catalog_to_current_detector_binding",
        {
            "panel": panel,
            "rules": rules,
            "retained_metadata": entries,
            "binding": "ORIGINAL_CATALOG_ID_FAILURE_CLASS_AND_PATTERN_WITH_UNCHANGED_CURRENT_DETECTOR_DEFAULTS",
            "historical_detector_thresholds": "NOT_RETAINED_IN_CATALOG",
            "catalog_admission_or_activation_changes": 0,
        },
        grade="EXPLICIT_FINITE_EXPERIMENT_BINDING",
    )
    report = original.AntimorphismImmuneBench(panel).screen_candidate_rules(rules)
    separate = []
    for index, fixture in enumerate(panel):
        current = original.AntimorphismImmuneBench((fixture,)).screen_candidate_rules(rules)
        separate.append({"panel_index": index, "fixture": fixture, "report": current})
    full_consistency = all(
        outcome.is_admitted is all(cell["report"].results[index].is_admitted for cell in separate)
        for index, outcome in enumerate(report.results)
    )
    controls = [
        ctx.observe(
            family,
            "original_bench_full_panel_and_each_excerpt",
            {
                "catalog_rules": report.total_rules_evaluated,
                "panel_excerpts": len(separate),
                "individual_rule_excerpt_evaluations": sum(
                    cell["report"].total_rules_evaluated for cell in separate
                ),
                "full_and_individual_admissions_agree": full_consistency,
                "non_refusal_panel_tolerant_catalog_rule_present": report.admitted_rules > 0,
                "report_census_matches_actual_results": report.admitted_rules
                == sum(result.is_admitted for result in report.results)
                and report.purged_rules == sum(not result.is_admitted for result in report.results),
            },
            expected={
                "catalog_rules": 61,
                "panel_excerpts": 6,
                "individual_rule_excerpt_evaluations": 366,
                "full_and_individual_admissions_agree": True,
                "non_refusal_panel_tolerant_catalog_rule_present": True,
                "report_census_matches_actual_results": True,
            },
        )
    ]
    ctx.observe(
        family, "actual_full_and_single_excerpt_reports", {"full": report, "single": separate}
    )
    for parent in rules:
        child = original.AntimorphismImmuneBench.mutate_and_mature(
            parent,
            re.escape(parent.match_pattern) + " PAPER011_VARIANT",
            parent.rule_id + "_variant",
        )
        controls.append(
            ctx.observe(
                family,
                "original_clonal_child_contract_" + parent.rule_id,
                {
                    "changed_pattern": child.match_pattern != parent.match_pattern,
                    "generation": child.generation,
                    "matcher_id": child.matcher_id,
                    "target_epitope": child.target_epitope,
                    "idle_limit": child.half_life_runs,
                    "affinity": child.affinity_score,
                    "initial_idle": child.runs_idle,
                    "initial_active": child.is_active,
                },
                expected={
                    "changed_pattern": True,
                    "generation": parent.generation + 1,
                    "matcher_id": parent.matcher_id,
                    "target_epitope": parent.target_epitope,
                    "idle_limit": parent.half_life_runs,
                    "affinity": parent.affinity_score,
                    "initial_idle": 0,
                    "initial_active": True,
                },
            )
        )
        states = [child]
        for _ in range(child.half_life_runs):
            states.append(original.AntimorphismImmuneBench.age_repertoire((states[-1],))[0])
        controls.append(
            ctx.observe(
                family,
                "original_idle_limit_transition_" + parent.rule_id,
                {
                    "idle_counters": [state.runs_idle for state in states],
                    "active_states": [state.is_active for state in states],
                    "active_filtered_at_limit": len(
                        ClonalSelectionEngine.filter_active_repertoire((states[-1],))
                    ),
                },
                expected={
                    "idle_counters": list(range(child.half_life_runs + 1)),
                    "active_states": [True] * child.half_life_runs + [False],
                    "active_filtered_at_limit": 0,
                },
            )
        )
        restored = ClonalSelectionEngine.stimulate(states[-1], affinity_boost=1)
        child_rescreen = original.AntimorphismImmuneBench(panel).screen_candidate_rules((child,))
        controls.append(
            ctx.observe(
                family,
                "literal_child_passes_actual_original_panel_" + parent.rule_id,
                {"admitted": child_rescreen.admitted_rules, "purged": child_rescreen.purged_rules},
                expected={"admitted": 1, "purged": 0},
            )
        )
        controls.append(
            ctx.observe(
                family,
                "original_stimulation_resets_idle_" + parent.rule_id,
                {
                    "idle": restored.runs_idle,
                    "active": restored.is_active,
                    "affinity": restored.affinity_score,
                },
                expected={"idle": 0, "active": True, "affinity": child.affinity_score + 1},
            )
        )
        ctx.observe(
            family,
            "actual_child_decay_and_rescreen_" + parent.rule_id,
            {
                "parent": parent,
                "child": child,
                "states": states,
                "stimulated": restored,
                "child_requires_fresh_panel_screen": child_rescreen,
            },
        )
    # A mutation inherits no tolerance certificate from its catalog parent.
    for index, excerpt in enumerate(panel):
        mutant = original.AntimorphismImmuneBench.mutate_and_mature(
            rules[0], re.escape(excerpt[:24]), "paper011_panel_cross_reactive_" + str(index)
        )
        result = original.AntimorphismImmuneBench((excerpt,)).screen_candidate_rules((mutant,))
        controls.append(
            ctx.observe(
                family,
                "panel_cross_reactive_child_rejected_" + str(index),
                {"admitted": result.admitted_rules, "purged": result.purged_rules},
                expected={"admitted": 0, "purged": 1},
            )
        )
        ctx.observe(family, "actual_cross_reactive_result_" + str(index), result)
    return all(value is True for value in controls)


def immune(ctx: Context, family: str) -> dict:
    from omega_engine_epistemic_immune_system.domain.thymus import ThymusGate
    from omega_engine_epistemic_immune_system.domain.value_objects import DetectorRule

    panel = (
        "Known valid candidate: exact finite signed pairs.",
        "A checked finite carrier has no universal claim.",
    )
    gate = ThymusGate(panel)
    specific = DetectorRule("paper011_specific", "unbacked_authority", "SELF_CERTIFIED_UNIVERSAL")
    autoimmune = DetectorRule("paper011_autoimmune", "bad_scope", "finite")
    good, bad = gate.evaluate_rule(specific), gate.evaluate_rule(autoimmune)
    passed = ctx.observe(
        family,
        "actual_matcher_positive_tolerance_and_autoimmune_control",
        {
            "specific_admitted_on_panel": good.is_admitted,
            "autoimmune_rejected": not bad.is_admitted,
        },
        expected={"specific_admitted_on_panel": True, "autoimmune_rejected": True},
    )
    ctx.observe(family, "actual_thymus_results", [good, bad])
    historical = []
    for path in ctx.paths(family, ".jsonl"):
        for number, raw in enumerate(ctx.read(path).splitlines(), 1):
            if raw.strip():
                row = ctx.replay.load(raw)
                historical.append(
                    {
                        "path": path,
                        "line": number,
                        "mode": row.get("mode"),
                        "probe_id": row.get("probe_id"),
                        "findings": row.get("classification", {}).get("findings"),
                        "raw_response_present": type(row.get("raw_response")) is str,
                    }
                )
    ctx.observe(family, "every_retained_harvest_row", historical, grade="HISTORICAL_RECOUNT")
    original_controls = retained_immune_controls(ctx, family)
    return {
        "finite_computation_passed": passed is True and original_controls is True,
        "remaining": [
            "Original catalog patterns are projected to DetectorRule with unchanged current defaults because historical detector thresholds are not retained; no catalog admission or activation is changed.",
            "Six-excerpt matcher, child rescreen and idle-counter controls establish no 28-probe study, global detector effectiveness, affinity-driven selection, exponential half-life, or historical model-call authenticity.",
        ],
    }


def physics(ctx: Context, family: str) -> dict:
    module = ctx.module(P001 + "code/certificate_gate.py")
    ctx.module(P001 + "code/exact_fock_gap.py", "exact_fock_gap")
    matrix = [
        [-1, "-1/2", "-1/2", 0],
        ["-1/2", 1, 0, "-1/2"],
        ["-1/2", 0, 1, "-1/2"],
        [0, "-1/2", "-1/2", -1],
    ]
    hopping = [[0, -1, 0, -1], [-1, 0, -1, 0], [0, -1, 0, -1], [-1, 0, -1, 0]]
    fixtures = [
        ("2site_TFI_J1_h0.5", "tfim", {"hamiltonian_matrix": matrix}, {"route": "positivity"}),
        (
            "4site_tightbinding_bipartite_t1",
            "free_fermion",
            {"U": 0, "h_up": hopping, "h_down": hopping},
            {"representation": "determinant"},
        ),
        (
            "2site_attractive_hubbard_t1_u_minus2",
            "attractive_hubbard",
            {
                "U": -2,
                "h_up": [[0, -1], [-1, 0]],
                "h_down": [[0, -1], [-1, 0]],
                "mu_up": 0,
                "mu_down": 0,
            },
            {"representation": "determinant"},
        ),
        (
            "2site_repulsive_hubbard_t1_u2",
            "repulsive_hubbard",
            {"U": 2, "h_up": [[0, -1], [-1, 0]], "h_down": [[0, -1], [-1, 0]]},
            {"representation": "determinant"},
        ),
        (
            "3site_triangular_plaquette_hubbard_t1_u2",
            "c3_triangular",
            {"t": 1, "U": 2, "beta": Fraction(1, 4), "mu": 0},
            {
                "move_type": "OPEN_SIGN_OBSTRUCTION",
                "obstruction_witness": {"type": "c3_integrated_path_gap"},
            },
        ),
    ]
    results = []
    for name, kind, parameters, proposal in fixtures:
        gate = module.BqnfCertificateGate(kind, parameters)
        result = (
            gate.verify_proposal_item(proposal)
            if "move_type" in proposal
            else gate.verify_sign_free(proposal)
        )
        results.append(
            {
                "id": name,
                "actual_parameters": jsonable(parameters),
                "actual_proposal": proposal,
                "actual_result": jsonable(result),
                "scope": "Existing conditional certificate gate; finite representation only",
            }
        )
    ctx.observe(family, "all_five_named_systems", results)
    gap = ctx.modules["exact_fock_gap"].verify_exact_gap()
    passed = ctx.observe(
        family, "actual_C3_integrated_finite_path_gap", gap["gap_certified"], expected=True
    )
    ctx.observe(family, "actual_path_gap_bounds", gap)
    passed &= ctx.observe(
        family,
        "positive_checked_stoquastic_matrix",
        results[0]["actual_result"]["valid"],
        expected=True,
    )
    ctx.observe(
        family,
        "repulsive_gate_is_unresolved_not_sign_obstruction",
        results[3]["actual_result"]["valid"],
        expected=False,
        grade="NEGATIVE_CONTROL",
    )
    return {
        "finite_computation_passed": bool(passed),
        "remaining": [
            "Repulsive two-site original sign-free representation is not resolved by rejection of this determinant route; replay all original retained bouts separately."
        ],
    }


def debate(ctx: Context, family: str) -> dict:
    module = ctx.module(P009 + "code/review_counts.py")
    trace = P009 + "docs/historical_evidence/demo2_r7_adversarial_debate_1790210039.jsonl"
    rows = [ctx.replay.load(line) for line in ctx.read(trace).splitlines() if line.strip()]
    counts = module.recount(rows)
    ctx.observe(
        family, "retained_actual_contingency_table", counts, grade="HISTORICAL_LABEL_RECOUNT"
    )
    passed = ctx.observe(
        family,
        "contingency_counts",
        [counts.true_positive, counts.false_negative, counts.false_positive, counts.true_negative],
        expected=[6, 0, 2, 2],
        grade="HISTORICAL_LABEL_RECOUNT",
    )
    gate_module = ctx.module(P001 + "code/certificate_gate.py")
    replayed = []
    for row in rows:
        result = gate_module.BqnfCertificateGate(
            row["lattice_key"], {"U": row["u_val"]}
        ).verify_proposal_item(row["proposer_move"])
        replayed.append({"input": row["proposer_move"], "current_result": jsonable(result)})
    ctx.observe(family, "all_deposited_proposal_current_gate_results", replayed)
    valid_gate = gate_module.BqnfCertificateGate(
        "finite", {"configuration_weights": {"p": 1, "n": -1, "s": 2}}
    )
    positive = valid_gate.verify_sign_free(
        {
            "representation": "finite_signed",
            "route": "exact_cancellation",
            "xi_witness": {"pairs": {"p": "n", "n": "p"}},
        }
    )
    negative = valid_gate.verify_sign_free(
        {
            "representation": "finite_signed",
            "route": "exact_cancellation",
            "xi_witness": {"pairs": {"p": "p", "n": "n"}},
        }
    )
    passed &= ctx.observe(
        family,
        "actual_finite_certificate_and_identity_control",
        {"valid_certificate": positive.valid, "invalid_identity": negative.valid},
        expected={"valid_certificate": True, "invalid_identity": False},
    )
    return {
        "finite_computation_passed": bool(passed),
        "remaining": [
            "Contingency labels are historical checker labels; ten rejected deposited proposals and a new finite positive control do not establish historical adversarial discovery."
        ],
    }


def geometry(ctx: Context, family: str) -> dict:
    module = ctx.module(P008 + "code/retraction_benchmark_runner.py")
    proofs = []
    passed = True
    for instance in module.BENCHMARK_INSTANCES:
        cert = module.host_certificate(instance)
        valid = (
            module.verify_potential(instance, cert["potential"])
            if cert["verdict"] == "CONSISTENT"
            else module.verify_inconsistency_witness(instance, cert["dual_witness_walk"])
        )
        passed &= valid
        proofs.append(
            {"instance": jsonable(instance), "actual_certificate": cert, "checked": valid}
        )
    cycle = ctx.module(P009 + "code/triangle_cycle_sum.py")
    before = cycle.cycle_sum((1, 1, 1))
    after = cycle.cycle_sum(cycle.subtract((1, 1, 1), cycle.edge_differences((2, 5, 7))))
    passed &= ctx.observe(
        family, "actual_triangle_gauge_invariance", [str(before), str(after)], expected=["3", "3"]
    )
    passed &= ctx.observe(
        family,
        "every_declared_Paper008_graph_certificate_checked",
        bool(proofs) and all(row["checked"] is True for row in proofs),
        expected=True,
    )
    ctx.observe(family, "all_declared_graph_certificates", proofs)
    paper_k4 = next(
        instance
        for instance in module.BENCHMARK_INSTANCES
        if instance.task_id == "retract_06_k4_rank3_poisoned"
    )
    walk = module.host_certificate(paper_k4)["dual_witness_walk"]
    passed &= ctx.observe(
        family,
        "original_Paper008_K4_and_truncated_witness_control",
        {
            "vertices": len(paper_k4.vertices),
            "edges": len(paper_k4.edges),
            "intact": module.verify_inconsistency_witness(paper_k4, walk),
            "truncated": module.verify_inconsistency_witness(paper_k4, walk[:-1]),
        },
        expected={"vertices": 4, "edges": 6, "intact": True, "truncated": False},
    )
    governor, topology, spec = original_k4_sources(ctx)
    original_k4 = topology.verify_topology_l1_governor(spec)
    checked_k4 = {
        key: original_k4[key]
        for key in (
            "cycle_rank",
            "initial_phi1",
            "repaired_phi1",
            "cut_admitted",
            "coboundary_cleared",
            "section_defect_zero",
            "idempotence_verified",
        )
    }
    checked_k4["repaired_holonomies"] = [
        str(value) for _, value in original_k4["repaired_holonomies"]
    ]
    checked_k4["declared_shared_edges_preserved"] = all(
        spec.ground_claims[edge] == spec.decoupled_repair_claims[edge]
        for edge in (("a", "b"), ("b", "c"), ("d", "a"))
    )
    passed &= ctx.observe(
        family,
        "original_shared_edge_K4_native_repair_and_projection",
        checked_k4,
        expected={
            "cycle_rank": 3,
            "initial_phi1": 8,
            "repaired_phi1": 0,
            "cut_admitted": True,
            "coboundary_cleared": True,
            "section_defect_zero": True,
            "idempotence_verified": True,
            "repaired_holonomies": ["0", "0", "0"],
            "declared_shared_edges_preserved": True,
        },
    )
    ctx.observe(
        family,
        "actual_source_K4_fixture_and_native_report",
        {"specification": jsonable(spec), "report": original_k4},
        grade="PINNED_ORIGINAL_K4_NATIVE_MATHEMATICS",
    )
    gov = governor.L1SymbolGameGovernor(spec.to_constraint_graph())
    for (u, v), value in spec.ground_claims.items():
        if gov.step_assert(u, v, value).admitted is not True:
            raise AggregateReplayError("ORIGINAL_K4_ASSERTION_REFUSED")
    incomplete = dict(spec.decoupled_repair_claims)
    incomplete.pop(("a", "b"))
    refused = gov.step_cut(proposed_claims=incomplete)
    original_phi_after_refusal = gov.primary_obstruction()
    zeroed = {edge.key: 0 for edge in gov.graph.edges}
    zero_verdict = gov.step_cut(proposed_claims=zeroed)
    zero_phi = gov.primary_obstruction()
    zero_shared_preserved = all(
        gov.edge_claims.get(edge) == spec.ground_claims[edge]
        for edge in (("a", "b"), ("b", "c"), ("d", "a"))
    )
    passed &= ctx.observe(
        family,
        "native_zero_does_not_establish_shared_edge_fidelity",
        {
            "missing_edge_admitted": refused.admitted,
            "missing_edge_status": refused.status,
            "unchanged_phi1_after_refusal": str(original_phi_after_refusal),
            "zeroed_complete_claims_admitted": zero_verdict.admitted,
            "zeroed_phi1": str(zero_phi),
            "zeroed_shared_edge_fidelity": zero_shared_preserved,
        },
        expected={
            "missing_edge_admitted": False,
            "missing_edge_status": "IncompleteProposal",
            "unchanged_phi1_after_refusal": "8",
            "zeroed_complete_claims_admitted": True,
            "zeroed_phi1": "0",
            "zeroed_shared_edge_fidelity": False,
        },
        grade="NEGATIVE_FIDELITY_AND_COMPLETENESS_CONTROLS",
    )
    gate = ctx.module(P001 + "code/certificate_gate.py").BqnfCertificateGate(
        "finite", {"configuration_weights": {"p": 1, "n": -1}}
    )
    cancelled = gate.verify_sign_free(
        {
            "representation": "finite_signed",
            "route": "exact_cancellation",
            "xi_witness": {"pairs": {"p": "n", "n": "p"}},
        }
    )
    passed &= ctx.observe(
        family, "actual_two_state_meron_cancellation", cancelled.valid, expected=True
    )
    ctx.observe(family, "actual_cancellation_certificate", cancelled)
    holonomy = ctx.module(P010 + "code/holonomy.py")
    connections = {}
    host_rows = []
    for name in ("pois_01", "base_01", "base_02", "base_03", "base_13"):
        connection = holonomy.connection_from_case(
            ctx.data(P010 + "code/data/c017/" + name + ".json")
        )
        connections[name] = connection
        host_rows.append(
            {"case_id": name, "actual_host_report": jsonable(holonomy.check_flatness(connection))}
        )
    claim_rows = []
    for run in ctx.data(P010 + "code/data/c017/model_claims.json")["runs"]:
        for item in run["cases"]:
            checked = (
                None
                if item["claim"] is None
                else holonomy.verify_claim(connections[item["case"]], item["claim"])
            )
            claim_rows.append(
                {
                    "run": run["run"],
                    "case_id": item["case"],
                    "actual_claim": item["claim"],
                    "current_checked_result": jsonable(checked),
                }
            )
    ctx.observe(family, "all_five_retained_Paper010_nonabelian_connections", host_rows)
    ctx.observe(
        family,
        "all_retained_Paper010_actual_claim_checks",
        claim_rows,
        grade="RETAINED_CANDIDATE_CURRENT_CHECKER_REPLAY",
    )
    return {
        "finite_computation_passed": bool(passed),
        "remaining": [
            "The original standard shared-edge K4 is freshly checked; larger original topology fixtures and historical model outcomes need their own source-bound replay.",
            "Paper010 retained claim rows with missing claim payloads remain unavailable; mathematical zero alone does not establish shared-edge fidelity.",
        ],
    }


def remaining_topologies(ctx: Context, family: str) -> dict:
    """Execute only the remaining three original native-backed topology fixtures."""
    governor, topology, _ = original_k4_sources(ctx)
    checker = ctx.module(P008 + "code/retraction_benchmark_runner.py")
    ctx.read(PFP + "demos/mssn/test_k4_higher_rank.py")
    targets = (
        (topology.TOPOLOGY_K4_ASYMMETRIC, 21, 3, (("a", "b"), ("b", "c"), ("d", "a"))),
        (topology.TOPOLOGY_W4_WHEEL, 16, 4, (("o", "a"), ("o", "b"), ("o", "c"), ("o", "d"))),
        (topology.TOPOLOGY_K5_COMPLETE, 27, 6, (("a", "b"), ("a", "c"), ("a", "d"), ("a", "e"))),
    )
    tape = ctx.output / "native_transport_calls.jsonl"
    controls = []
    for spec, original_initial_phi, rank, unchanged_edges in targets:
        source_state = jsonable(spec)
        before = tape.stat().st_size if tape.exists() else 0
        report = topology.verify_topology_l1_governor(spec)
        graph = spec.to_constraint_graph()
        gov = governor.L1SymbolGameGovernor(graph)
        assertions = []
        for (u, v), value in spec.ground_claims.items():
            verdict = gov.step_assert(u, v, value)
            assertions.append(verdict)
            if verdict.admitted is not True:
                raise AggregateReplayError(
                    "ORIGINAL_TOPOLOGY_ASSERTION_REFUSED:" + spec.topology_id
                )
        initial_phi = gov.primary_obstruction()
        cut = gov.step_cut(proposed_claims=spec.decoupled_repair_claims)
        repaired_phi = gov.primary_obstruction()
        actual_repaired_claims = copy.deepcopy(gov.edge_claims)
        section = gov.project(gov.section)
        if any(value.denominator != 1 for value in section.values()):
            raise AggregateReplayError("ORIGINAL_INTEGER_TOPOLOGY_PROJECTION_CHANGED")
        potential = {vertex: int(value) for vertex, value in section.items()}
        if any(value.denominator != 1 for value in spec.decoupled_repair_claims.values()):
            raise AggregateReplayError("ORIGINAL_INTEGER_TOPOLOGY_REPAIR_CHANGED")
        repaired_instance = checker.GraphInstance(
            spec.topology_id + "_original_repair",
            list(spec.vertices),
            [(u, v, int(spec.decoupled_repair_claims[(u, v)])) for u, v, _ in spec.edges],
            "CONSISTENT",
            "Exact original candidate on original directed edges; edge weights remain in the native governor.",
        )
        corrupt_potential = dict(potential)
        corrupt_potential[spec.vertices[0]] += 1
        incomplete = dict(spec.decoupled_repair_claims)
        del incomplete[spec.edges[0][:2]]
        missing_edge = gov.step_cut(proposed_claims=incomplete)
        after = tape.stat().st_size if tape.exists() else 0
        actual = {
            "cycle_rank": report["cycle_rank"],
            "source_fixture_initial_phi": report["initial_phi1"],
            "second_native_initial_phi": str(initial_phi),
            "source_fixture_repaired_phi": report["repaired_phi1"],
            "second_native_repaired_phi": str(repaired_phi),
            "source_cut_admitted": report["cut_admitted"],
            "actual_cut_admitted": cut.admitted,
            "source_projection_zero": report["section_defect_zero"],
            "source_idempotence": report["idempotence_verified"],
            "every_source_cycle_zero": all(
                value == 0 for _, value in report["repaired_holonomies"]
            ),
            "actual_original_candidate_preserved": actual_repaired_claims
            == spec.decoupled_repair_claims,
            "original_source_state_unchanged": source_state == jsonable(spec),
            "original_carrier_and_weights_preserved": [
                (edge.u, edge.v, edge.weight) for edge in gov.graph.edges
            ]
            == list(spec.edges)
            and gov.graph.vertices == spec.vertices,
            "declared_unchanged_edges_preserved": all(
                actual_repaired_claims[edge] == spec.ground_claims[edge] for edge in unchanged_edges
            ),
            "independent_potential_checker_accepts": checker.verify_potential(
                repaired_instance, potential
            ),
            "corrupted_potential_rejected": not checker.verify_potential(
                repaired_instance, corrupt_potential
            ),
            "missing_edge_admitted": missing_edge.admitted,
            "missing_edge_status": missing_edge.status,
            "missing_edge_preserves_complete_candidate": gov.edge_claims == actual_repaired_claims,
            "native_transport_bytes_recorded": after > before,
        }
        expected = {
            "cycle_rank": rank,
            "source_fixture_initial_phi": original_initial_phi,
            "second_native_initial_phi": str(original_initial_phi),
            "source_fixture_repaired_phi": 0,
            "second_native_repaired_phi": "0",
            "source_cut_admitted": True,
            "actual_cut_admitted": True,
            "source_projection_zero": True,
            "source_idempotence": True,
            "every_source_cycle_zero": True,
            "actual_original_candidate_preserved": True,
            "original_source_state_unchanged": True,
            "original_carrier_and_weights_preserved": True,
            "declared_unchanged_edges_preserved": True,
            "independent_potential_checker_accepts": True,
            "corrupted_potential_rejected": True,
            "missing_edge_admitted": False,
            "missing_edge_status": "IncompleteProposal",
            "missing_edge_preserves_complete_candidate": True,
            "native_transport_bytes_recorded": True,
        }
        controls.append(
            ctx.observe(
                family,
                "remaining_original_native_topology_" + spec.topology_id,
                actual,
                expected=expected,
            )
        )
        ctx.observe(
            family,
            "actual_original_topology_state_and_evidence_" + spec.topology_id,
            {
                "source_specification": source_state,
                "original_source_test_expectation": {
                    "initial_phi1": original_initial_phi,
                    "cycle_rank": rank,
                },
                "unchanged_original_edges": unchanged_edges,
                "native_source_report": report,
                "actual_assertions": assertions,
                "actual_original_cut": cut,
                "actual_claims_after_original_cut": actual_repaired_claims,
                "actual_native_projection": section,
                "independent_potential": potential,
                "independent_checker_instance": repaired_instance,
                "corrupt_potential": corrupt_potential,
                "incomplete_candidate": incomplete,
                "actual_incomplete_candidate_refusal": missing_edge,
                "native_transport_byte_span": [before, after],
            },
            grade="PINNED_ORIGINAL_WEIGHTED_TOPOLOGY_NATIVE_REPAIR_AND_EXTERNAL_EDGE_CHECK",
        )
    return {
        "finite_computation_passed": all(value is True for value in controls),
        "selected_original_topology_ids": [spec.topology_id for spec, *_ in targets],
        "remaining": [
            "These three original finite carriers plus the separately verified standard K4 do not certify arbitrary larger topologies, tower-stage transport, model discovery, or an optimal permission-constrained edit cost.",
            "The original scripted chord-hint branches and artificial loop counters are not empirical model behavior and are not run here.",
        ],
    }


def pharmacy(ctx: Context, family: str) -> dict:
    catalog = ctx.data(P006 + "code/fixtures/pharmacy_catalog_52cb5457f6c4.json")
    entries = list(catalog["antibodies"].values())
    census = {
        "entries": len(entries),
        "statuses": dict(Counter(entry["pharmacy_status"] for entry in entries)),
        "placeholder_fixtures": sum(
            entry["positive_fixture"] == "# Repaired exact state\n"
            and entry["negative_fixture"] == f"# Triggering defect: {entry['target_pattern']}\n"
            for entry in entries
        ),
    }
    passed = ctx.observe(
        family,
        "actual_unchanged_catalog_census",
        census,
        expected={
            "entries": 61,
            "statuses": {"candidate": 56, "active": 5},
            "placeholder_fixtures": 49,
        },
        grade="HISTORICAL_CATALOG_RECOUNT",
    )
    ctx.observe(
        family,
        "historical_class_counts",
        dict(Counter(entry["failure_class"] for entry in entries)),
        grade="HISTORICAL_CATALOG_RECOUNT",
    )
    control = immune(ctx, family)
    return {
        "finite_computation_passed": bool(passed and control["finite_computation_passed"]),
        "remaining": [
            "Placeholder comments are not executable detector fixtures; positive matcher controls do not validate all historical catalog entries."
        ],
    }


def mutation_control_census(
    records: list[dict], case_count: int, mutation_count: int, checker_count: int, accepts
) -> dict:
    census = {
        "case_records": 0,
        "accepted_case_outputs": 0,
        "accepted_typed_refusals": 0,
        "accepted_negative_claims": 0,
        "accepted_non_refusal_outputs": 0,
        "mutation_records": 0,
        "dual_checker_rejections": 0,
        "joint_mutant_detections": 0,
        "partial_checker_rejections": 0,
        "all_checkers_accept_mutation": 0,
        "execution_errors": 0,
        "uninterpretable_check_records": 0,
        "unbound_records": 0,
    }
    for row in records:
        kind = "mutation" if "mutation" in row else "case" if "input" in row else None
        if kind is None:
            census["unbound_records"] += 1
            continue
        census["mutation_records" if kind == "mutation" else "case_records"] += 1
        if "error" in row or "kill_by_exception" in row:
            census["execution_errors"] += 1
            continue
        checks = row.get("checks")
        if type(checks) is not list or len(checks) != checker_count:
            census["uninterpretable_check_records"] += 1
            continue
        flags = [accepts(check) for check in checks]
        if any(type(flag) is not bool for flag in flags):
            census["uninterpretable_check_records"] += 1
            continue
        if kind == "case":
            accepted = all(flag is True for flag in flags) and row.get("accepted") is True
            census["accepted_case_outputs"] += accepted
            coverage = row.get("coverage_class")
            if accepted and coverage == "ACCEPTED_TYPED_REFUSAL":
                census["accepted_typed_refusals"] += 1
            elif accepted and coverage == "SOURCE_CHECKED_NEGATIVE_CLAIM":
                census["accepted_negative_claims"] += 1
            elif accepted and coverage == "SOURCE_CHECKED_CANDIDATE":
                census["accepted_non_refusal_outputs"] += 1
            elif accepted:
                census["unbound_records"] += 1
        else:
            dual = all(flag is False for flag in flags)
            joint = any(flag is False for flag in flags)
            census["dual_checker_rejections"] += dual
            census["joint_mutant_detections"] += joint
            census["partial_checker_rejections"] += joint and not dual
            census["all_checkers_accept_mutation"] += all(flag is True for flag in flags)
    census["declared_cases"] = case_count
    census["declared_mutations"] = mutation_count
    census["expected_controls_succeeded"] = (
        type(case_count) is int
        and case_count > 0
        and type(mutation_count) is int
        and mutation_count > 0
        and type(checker_count) is int
        and checker_count >= 2
        and census["case_records"] == case_count
        and census["accepted_case_outputs"] == case_count
        and census["mutation_records"] == mutation_count
        and census["dual_checker_rejections"] == mutation_count
        and census["execution_errors"] == 0
        and census["uninterpretable_check_records"] == 0
        and census["unbound_records"] == 0
    )
    return census


def mutations(ctx: Context, family: str) -> dict:
    source = ctx.engine / PFP
    catalog = ctx.replay.build_catalog(source)
    results = []
    actual_path = ctx.output / "challenge_actual_evaluations.jsonl"
    with actual_path.open("w+b") as stream:
        for cid in ("C011", "C012", "C022", "C031"):
            row = next(row for row in catalog["challenges"] if row["id"] == cid)
            start = stream.tell()
            result = ctx.replay.reference_challenge(row, source, stream)
            end = stream.tell()
            stream.seek(start)
            actual_bytes = stream.read(end - start)
            stream.seek(end)
            records = [ctx.replay.load(line) for line in actual_bytes.splitlines()]
            census = mutation_control_census(
                records,
                len(row["cases"]),
                len(row["mutations"]),
                len(row["checkers"]),
                ctx.replay.checker_accepts,
            )
            controls_passed = ctx.observe(
                family,
                cid + "_actual_expected_case_and_mutation_controls",
                census["expected_controls_succeeded"],
                expected=True,
            )
            results.append(
                {
                    "id": cid,
                    "result": result,
                    "actual_control_census": census,
                    "actual_evaluation_bytes_sha256": digest(actual_bytes),
                    "explicit_controls_passed": controls_passed,
                }
            )
    ctx.observe(family, "every_current_four_family_reference_and_mutation", results)
    passed = all(
        row["explicit_controls_passed"] is True
        and row["result"].get("complete_case_execution") is True
        and row["result"].get("complete_mutation_execution") is True
        for row in results
    )
    return {
        "finite_computation_passed": bool(passed),
        "remaining": [
            "Inspect all accepted positive candidates, unknowns, unsupported mutations and checker crashes; module agreement does not establish checker independence."
        ],
    }


HANDLERS = {
    "FSP_BLIND_CLUSTER_RECOVERY": meron,
    "MUB6_AFFINE_PHASE_ANSATZ": mub,
    "AST_REFACTORING_RETRACTION": packets,
    "SPECIMEN_MT000_REDUCTION": packets,
    "UNIFIED_PACKET_STREAMS": packets,
    "EIGHT_BEAT_DIALOGUE": dialogue,
    "RETRACTION_CONDITIONING": conditioning,
    "ANTIMORPHISM_FARM": immune,
    "FSP_PHYSICS_RETRACTIONS": physics,
    "PAIRED_ADVERSARIAL_DEBATE": debate,
    "DISCRETE_GEOMETRY_PROBES": geometry,
    "PHARMACY_CATALOG": pharmacy,
    "CHALLENGE_MUTATION_SUITES": mutations,
}


def extend_capability(base: dict, inventory: dict, replay) -> dict:
    lock = copy.deepcopy(base)
    engine = replay.verify_engine(base, full_runtime=False)
    required = set(EXTRA_FILES)
    required.update(
        "omega_engine_woland/" + relative
        for relative in replay.source_files(engine / "omega_engine_woland")
        if relative.endswith(".py")
    )
    for folder in (
        PFP + "demos/mssn",
        PFP + "challenges/a_mechanism/c005_hosted_decode_controls",
        P008 + "docs/source_archive/k4_traces",
    ):
        required.update(folder + "/" + path for path in replay.source_files(engine / folder))
    for family in inventory["aggregate_demo_families"]:
        for item in family["authoritative_sources"]:
            if item["availability"] == "PRESENT":
                if digest((engine / item["path"]).read_bytes()) != item["sha256"]:
                    raise AggregateReplayError("FINDINGS_SOURCE_PIN_MISMATCH: " + item["path"])
                required.add(item["path"])
            elif item["availability"] == "PRESENT_DIRECTORY":
                required.update(
                    item["path"] + "/" + path for path in replay.source_files(engine / item["path"])
                )
    for cid in ("C011", "C012", "C022", "C031"):
        row = next(row for row in inventory["challenges"] if row["id"] == cid)
        package = row["current_package"]
        required.update(package + "/" + path for path in replay.source_files(engine / package))
    for relative in tuple(required):
        for parent in (engine / relative).parents:
            if parent == engine:
                break
            initial = parent / "__init__.py"
            if initial.is_file():
                required.add(initial.relative_to(engine).as_posix())
    for relative in sorted(required, key=lambda value: value.encode("utf-8")):
        replay.regular(engine / relative)
        lock["files"][relative] = digest((engine / relative).read_bytes())
    lock["files"] = dict(sorted(lock["files"].items(), key=lambda item: item[0].encode("utf-8")))
    lock["aggregate_algorithm_scope"] = (
        "Explicit additional preserved algorithm and data paths; no ambient sibling imports"
    )
    return lock


def worker(job: dict) -> int:
    output = Path(job["output_dir"])
    execution_configuration = empty_cache_configuration(Path(job["pycache_prefix"]), worker=True)
    execution_configuration["runtime_environment"] = job["capability"].get("runtime_environment")
    (output / "execution_configuration.json").write_bytes(canonical(execution_configuration))
    replay = local_module("paper011_aggregate_replay_boundary", "recreate_demos.py")
    replay.verify_runtime_environment(job["capability"], full_runtime=False)
    ctx = Context(job["capability"], output, job["inventory"], replay)
    source_import_journal = []
    replay.configure_worker(
        Path(job["capability"]["engine_root"]) / PFP,
        job["capability"],
        source_import_journal,
        output,
    )
    replay.trace_native_calls(output)
    results = []
    selected = tuple(job.get("family_ids", AGGREGATES))
    variant = job.get("variant", "main")
    validate_execution_variant(selected, variant)
    if (
        not selected
        or len(set(selected)) != len(selected)
        or any(family not in AGGREGATES for family in selected)
    ):
        raise AggregateReplayError("INVALID_SELECTED_FAMILY_SCOPE")
    for family in selected:
        try:
            handler = {
                "remaining-topologies": remaining_topologies,
                "original-live-ast": original_live_ast,
            }.get(variant, HANDLERS[family])
            result = handler(ctx, family)
            control_outcome = explicit_control_outcome(ctx.observations, family)
            result["declared_handler_outcome"] = result["finite_computation_passed"]
            result["finite_computation_passed"] = (
                result["finite_computation_passed"] is True
                and control_outcome["all_explicit_controls_passed"] is True
            )
            result["explicit_control_outcome"] = control_outcome
            status = (
                "FINITE_RECREATION_WITH_RESIDUALS"
                if result["finite_computation_passed"]
                else "RECREATION_RESIDUAL"
            )
        except Exception as exc:
            status = "RECREATION_GAP"
            result = {
                "finite_computation_passed": False,
                "exception": type(exc).__name__,
                "detail": str(exc),
                "remaining": [
                    "Repair this exact pinned execution contract and replay all original obligations."
                ],
            }
        results.append({"id": family, "status": status, **result})
        print(json.dumps({"id": family, "status": status}), flush=True)
    ctx.journal.extend(bind_import_journal_root(source_import_journal, PFP))
    for row in list(ctx.journal):
        ctx.read(row["path"])
    (output / "observations.jsonl").write_bytes(
        b"".join(canonical(row) + b"\n" for row in ctx.observations)
    )
    (output / "import_adaptations.json").write_bytes(canonical(ctx.journal))
    (output / "worker_result.json").write_bytes(
        canonical(
            {
                "families": results,
                "all_original_obligations_completed": False,
                "model_calls": 0,
                "authority_effect": "None",
                "execution_configuration": execution_configuration,
                "variant": variant,
            }
        )
    )
    return 0 if all(row["finite_computation_passed"] for row in results) else 2


def validate_execution_variant(family_ids: tuple[str, ...], variant: str) -> None:
    if variant not in {"main", "remaining-topologies", "original-live-ast"}:
        raise AggregateReplayError("UNKNOWN_EXECUTION_VARIANT")
    if variant == "remaining-topologies" and family_ids != ("DISCRETE_GEOMETRY_PROBES",):
        raise AggregateReplayError("EXACT_REMAINING_TOPOLOGY_FAMILY_SCOPE_REQUIRED")
    if variant == "original-live-ast" and family_ids != ("AST_REFACTORING_RETRACTION",):
        raise AggregateReplayError("EXACT_ORIGINAL_LIVE_AST_FAMILY_SCOPE_REQUIRED")


def run(
    base: dict,
    output: Path,
    timeout: int = 240,
    family_ids: tuple[str, ...] = AGGREGATES,
    variant: str = "main",
) -> dict:
    validate_execution_variant(family_ids, variant)
    if output.exists():
        raise AggregateReplayError("OUTPUT_DIRECTORY_OCCUPIED")
    output.mkdir(parents=True)
    parent_cache = output / "parent_empty_bytecode_cache"
    parent_cache.mkdir(exist_ok=False)
    parent_execution_configuration = empty_cache_configuration(parent_cache, activate=True)
    replay = local_module("paper011_aggregate_outer_boundary", "recreate_demos.py")
    inventory_raw = (PAPER / "docs/findings_demo_inventory.json").read_bytes()
    inventory = replay.load(inventory_raw)
    if tuple(row["id"] for row in inventory["aggregate_demo_families"]) != AGGREGATES:
        raise AggregateReplayError("AGGREGATE_INVENTORY_SCOPE_MISMATCH")
    if (
        not family_ids
        or len(set(family_ids)) != len(family_ids)
        or any(family not in AGGREGATES for family in family_ids)
    ):
        raise AggregateReplayError("INVALID_SELECTED_FAMILY_SCOPE")
    capability = extend_capability(base, inventory, replay)
    replay.verify_engine(capability)
    code_pins = {
        name: digest(Path(__file__).with_name(name).read_bytes())
        for name in (
            "aggregate_recreations.py",
            "recreate_demos.py",
            "demo_catalog.py",
            "source_custody.py",
        )
    }
    worker_cache = output / "worker_empty_bytecode_cache"
    worker_cache.mkdir(exist_ok=False)
    job = {
        "capability": capability,
        "inventory": inventory,
        "output_dir": str(output.absolute()),
        "family_ids": list(family_ids),
        "pycache_prefix": str(worker_cache),
        "parent_execution_configuration": parent_execution_configuration,
        "variant": variant,
    }
    (output / "job.json").write_bytes(canonical(job))
    (output / "capability.json").write_bytes(canonical(capability))
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTHONPATH", "PYTHONSTARTUP"}
        and not any(secret in key.upper() for secret in ("TOKEN", "SECRET", "PASSWORD", "API_KEY"))
    }
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    bootstrap = "import sys;sys.pycache_prefix=sys.argv[3];sys.dont_write_bytecode=True;import importlib.util,json;s=importlib.util.spec_from_file_location('paper011_aggregate_worker',sys.argv[1]);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m);sys.exit(m.worker(json.loads(open(sys.argv[2],'rb').read())))"
    process = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            bootstrap,
            str(Path(__file__).absolute()),
            str((output / "job.json").absolute()),
            str(worker_cache),
        ],
        cwd=capability["engine_root"],
        env=env,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    (output / "process_stdout.txt").write_bytes(process.stdout)
    (output / "process_stderr.txt").write_bytes(process.stderr)
    replay.verify_engine(capability)
    if digest((PAPER / "docs/findings_demo_inventory.json").read_bytes()) != digest(inventory_raw):
        raise AggregateReplayError("INVENTORY_CHANGED_DURING_SUBPROCESS")
    if code_pins != {
        name: digest(Path(__file__).with_name(name).read_bytes()) for name in code_pins
    }:
        raise AggregateReplayError("REPLAY_MACHINERY_CHANGED_DURING_SUBPROCESS")
    result_path = output / "worker_result.json"
    result = (
        replay.load(result_path.read_bytes())
        if result_path.exists()
        else {"families": [], "status": "WORKER_FAILURE"}
    )
    receipt = {
        "schema_version": "paper011.aggregate-recreated-run.v2",
        "authority_effect": "None",
        "source_git_head": capability["source_git_head"],
        "inventory_sha256": digest(inventory_raw),
        "capability_sha256": digest(canonical(capability)),
        "code_sha256": code_pins,
        "parent_execution_configuration": parent_execution_configuration,
        "process_exit": process.returncode,
        "declared_family_ids": list(family_ids),
        "complete_findings_inventory_family_ids": list(AGGREGATES),
        "variant": variant,
        "result": result,
        "custody_recheck": "ALL_PINNED_ENGINE_ALGORITHMS_INPUTS_AND_PAPER_MACHINERY_REHASHED_AFTER_SUBPROCESS",
        "artifacts_sha256": replay.source_files(output),
        "model_calls": 0,
    }
    receipt["receipt_sha256"] = digest(canonical(receipt))
    (output / "aggregate_receipt.json").write_bytes(canonical(receipt))
    return receipt


def review_previous_run(previous: Path, output: Path) -> dict:
    """Reclassify retained v1 observations without rerunning their algorithms."""
    if output.exists():
        raise AggregateReplayError("OUTPUT_DIRECTORY_OCCUPIED")
    output.mkdir(parents=True)
    cache_prefix = output / "empty_bytecode_cache"
    cache_prefix.mkdir(exist_ok=False)
    execution_configuration = empty_cache_configuration(cache_prefix, activate=True)
    custody = local_module("paper011_aggregate_review_custody", "source_custody.py")
    receipt_raw = custody._read_regular(previous, "aggregate_receipt.json")
    receipt = custody._json(receipt_raw)
    if receipt.get("schema_version") != "paper011.aggregate-recreated-run.v1":
        raise AggregateReplayError("REVIEW_REQUIRES_V1_DIAGNOSTIC")
    committed = receipt.pop("receipt_sha256")
    if digest(canonical(receipt)) != committed:
        raise AggregateReplayError("PREVIOUS_RECEIPT_DIGEST_MISMATCH")
    expected = {"aggregate_receipt.json", *receipt["artifacts_sha256"]}
    observed = {
        path.removeprefix(previous.name + "/")
        for path in custody._inventory(previous.parent, previous.name)
    }
    if expected != observed:
        raise AggregateReplayError("PREVIOUS_ARTIFACT_INVENTORY_MISMATCH")
    for relative, sha in receipt["artifacts_sha256"].items():
        if digest(custody._read_regular(previous, relative)) != sha:
            raise AggregateReplayError("PREVIOUS_ARTIFACT_CHANGED: " + relative)
    rows = [
        custody._json(line)
        for line in custody._read_regular(previous, "observations.jsonl").splitlines()
    ]
    for row in rows:
        # V1's exact source used expected=None exclusively for observation-only records.
        asserted = row["expected"] is not None
        passed = strict_equal(row["actual"], row["expected"]) if asserted else None
        row.update(
            {
                "asserted": asserted,
                "passed": passed,
                "verification_status": "CONTROL_PASSED"
                if passed is True
                else "CONTROL_FAILED"
                if passed is False
                else "OBSERVATION_ONLY",
            }
        )
    families = []
    for family in receipt["result"]["families"]:
        controls = explicit_control_outcome(rows, family["id"])
        mutation = family["id"] == "CHALLENGE_MUTATION_SUITES"
        families.append(
            {
                "id": family["id"],
                "previous_handler_outcome": family["finite_computation_passed"],
                "explicit_control_outcome": controls,
                "retained_scoped_controls_verified": None
                if mutation
                else family["finite_computation_passed"] is True
                and controls["all_explicit_controls_passed"] is True,
                "scope": "FRESH_ACTUAL_MUTATION_CONTROL_REPLAY_REQUIRED"
                if mutation
                else "RECLASSIFICATION_OF_RETAINED_FINITE_CONTROLS_ONLY",
                "remaining": family["remaining"],
            }
        )
    corrected = b"".join(canonical(row) + b"\n" for row in rows)
    (output / "reclassified_observations.jsonl").write_bytes(corrected)
    review = {
        "schema_version": "paper011.aggregate-v1-classification-review.v1",
        "previous_directory": str(previous.absolute()),
        "previous_receipt_raw_sha256": digest(receipt_raw),
        "previous_receipt_self_sha256": committed,
        "previous_artifacts_sha256": receipt["artifacts_sha256"],
        "classification_code_sha256": digest(Path(__file__).read_bytes()),
        "execution_configuration": execution_configuration,
        "reclassified_observations_sha256": digest(corrected),
        "families": families,
        "algorithm_executions": 0,
        "all_original_obligations_completed": False,
        "authority_effect": "None",
    }
    review["receipt_sha256"] = digest(canonical(review))
    (output / "classification_review.json").write_bytes(canonical(review))
    return review


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capability", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--family", action="append", choices=AGGREGATES)
    parser.add_argument(
        "--variant", choices=("main", "remaining-topologies", "original-live-ast"), default="main"
    )
    parser.add_argument("--review-existing", type=Path)
    parser.add_argument("--worker-job", type=Path)
    args = parser.parse_args()
    if args.worker_job:
        job = json.loads(args.worker_job.read_bytes())
        empty_cache_configuration(Path(job["pycache_prefix"]), activate=True, worker=True)
        return worker(job)
    if args.review_existing:
        if (
            args.output_dir is None
            or args.capability is not None
            or args.family
            or args.variant != "main"
        ):
            parser.error("--review-existing requires only --output-dir")
        review = review_previous_run(args.review_existing.absolute(), args.output_dir.absolute())
        print(json.dumps({"receipt_sha256": review["receipt_sha256"], "algorithm_executions": 0}))
        return 0
    if args.capability is None or args.output_dir is None:
        parser.error("--capability and --output-dir are required")
    base = json.loads(args.capability.read_bytes())
    base = base.get("capability", base)
    receipt = run(
        base,
        args.output_dir.absolute(),
        args.timeout,
        tuple(args.family) if args.family else AGGREGATES,
        args.variant,
    )
    print(
        json.dumps(
            {
                "receipt_sha256": receipt["receipt_sha256"],
                "families": receipt["result"].get("families", []),
            },
            sort_keys=True,
        )
    )
    return receipt["process_exit"] or 0


if __name__ == "__main__":
    raise SystemExit(main())
