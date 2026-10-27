"""Apply one pinned seed-only DPO recipe after native custody and fresh checks.

The registry is operator supplied data. It provides no code, checker command,
provider route or automatic retrieval policy. AuthorityEffect: None.
"""

from __future__ import annotations

import copy
import hashlib
import json
import stat
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path

from pydantic import ValidationError

from operations.domain.rop.result import Err, Ok, Refusal, Result
from pfp.domain.rewriting.finite_dpo import (
    DpoRule,
    FiniteACSet,
    Part,
    RewriteRefusal,
    apply_registered_rule,
    graph_digest,
    rule_digest,
)
from adversary.domain.checked_reuse import (
    BoundReuseChecker,
    BoundReuseFile,
    BoundReuseTask,
    CheckedReuseRegistry,
    CheckedReuseResult,
    FreshReuseCheck,
)
from adversary.domain.native import NativeOperationPort
from adversary.use_cases.intelligence_digestion.archive_custody import (
    ArchiveCustodyError,
    checked_path,
)
from adversary.use_cases.prompt_family_replay import _program_digest, load_ddc_program

MAX_REUSE_BYTES = 262144
MAX_SESSION_RECHECK_BYTES = 32 * 1024 * 1024
Checker = Callable[[Path, str, dict], FreshReuseCheck | dict]


def _hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _fail(code: str) -> None:
    raise ValueError(code)


def _read(path: Path, *, max_bytes: int = MAX_REUSE_BYTES) -> bytes:
    """Reject alias custody before reading a bounded regular file."""
    if type(max_bytes) is not int or not 1 <= max_bytes <= MAX_SESSION_RECHECK_BYTES:
        _fail("REUSE_READ_BOUND")
    path = path.absolute()
    checked_path(Path(path.anchor), path)
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > max_bytes:
        _fail("REUSE_FILE_CUSTODY")
    with path.open("rb") as stream:
        raw = stream.read(max_bytes + 1)
    if len(raw) > max_bytes:
        _fail("REUSE_FILE_BOUND")
    return raw


def _bound_file(binding: BoundReuseFile) -> bytes:
    raw = _read(Path(binding.path))
    if _hash(raw) != binding.sha256:
        _fail("REUSE_SOURCE_CHANGED")
    return raw


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail("REUSE_DUPLICATE_KEY")
        result[key] = value
    return result


def _json(raw: bytes):
    return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique,
                      parse_constant=lambda _: _fail("REUSE_NONFINITE_JSON"))


def load_checked_reuse_registry(path: Path, expected_sha256: str) -> CheckedReuseRegistry:
    """Load only explicitly pinned registrations, rejecting duplicate JSON keys."""
    raw = _read(Path(path))
    if type(expected_sha256) is not str or _hash(raw) != expected_sha256:
        _fail("REUSE_REGISTRY_CHANGED")
    _json(raw)
    return CheckedReuseRegistry.model_validate_json(raw)


def checker_source_digest(checker: BoundReuseChecker) -> str:
    """Bind the complete declared checker source closure and its identity."""
    return _program_digest(checker.model_dump(mode="json"))


def _field_graph(value: dict) -> FiniteACSet:
    return FiniteACSet(tuple(Part(key, "field", (("key", key),
        ("json", json.dumps(item, sort_keys=True, separators=(",", ":"),
                            ensure_ascii=False, allow_nan=False)))) for key, item in value.items()))


def _registered_seed_rule(value: dict, source_seed: str, target_seed: str) -> DpoRule:
    """Decode exact existing DPO wire graphs; exclude executable/general edits."""
    if set(value) != {"rule_id", "left", "interface", "right"}:
        _fail("REUSE_RULE_SHAPE")

    def graph(raw):
        if type(raw) is not dict or set(raw) != {"parts", "links"} or raw["links"] != []:
            _fail("REUSE_RULE_SHAPE")
        if type(raw["parts"]) is not list:
            _fail("REUSE_RULE_SHAPE")
        parts = []
        for item in raw["parts"]:
            if type(item) is not dict or set(item) != {"id", "kind", "attrs"}:
                _fail("REUSE_RULE_SHAPE")
            attrs = item["attrs"]
            if type(attrs) is not list or any(type(pair) is not list or len(pair) != 2 for pair in attrs):
                _fail("REUSE_RULE_SHAPE")
            parts.append(Part(item["id"], item["kind"], tuple(tuple(pair) for pair in attrs)))
        return FiniteACSet(tuple(parts))

    rule = DpoRule(value["rule_id"], graph(value["left"]), graph(value["interface"]), graph(value["right"]))
    if (rule.interface != FiniteACSet() or rule.left != _field_graph({"seed": source_seed})
            or rule.right != _field_graph({"seed": target_seed})):
        _fail("REUSE_RULE_SCOPE")
    return rule


def _check(callback: Checker, path: Path, task: BoundReuseTask, checker: BoundReuseChecker,
           expected_candidate_sha256: str, *, candidate_limit: int = MAX_REUSE_BYTES,
           answer_candidate: bool = True) -> FreshReuseCheck:
    before = _read(path, max_bytes=candidate_limit)
    if _hash(before) != expected_candidate_sha256:
        _fail("REUSE_CANDIDATE_CHANGED_BEFORE_CHECK")
    for source in checker.sources:
        _bound_file(source)
    _bound_file(task.contract)
    observed = callback(path, task.seed, copy.deepcopy(task.premises))
    if type(observed) is FreshReuseCheck:
        observed = FreshReuseCheck.model_validate_json(observed.model_dump_json())
    elif type(observed) is dict:
        observed = FreshReuseCheck.model_validate_json(json.dumps(observed, allow_nan=False))
    if type(observed) is not FreshReuseCheck:
        _fail("REUSE_CHECK_RECORD_REQUIRED")
    expected = {
        "checker_id": checker.checker_id, "candidate_sha256": _hash(before),
        "seed_sha256": _hash(task.seed.encode("utf-8")),
        "premises_sha256": _program_digest(task.premises),
        "contract_sha256": task.contract.sha256,
        "checker_source_sha256": checker_source_digest(checker),
    }
    if any(getattr(observed, key) != value for key, value in expected.items()):
        _fail("REUSE_CHECK_BINDING_MISMATCH")
    candidate = _json(before)
    if answer_candidate and "outcome" in candidate and candidate["outcome"] != observed.outcome:
        _fail("REUSE_QUERY_BINDING_MISMATCH")
    if answer_candidate and observed.outcome == "QUERY_USER_MORE_INFO":
        if (candidate.get("outcome") != observed.outcome
                or candidate.get("missing_fields") != list(observed.missing_fields)):
            _fail("REUSE_QUERY_BINDING_MISMATCH")
    if _read(path, max_bytes=candidate_limit) != before:
        _fail("REUSE_CANDIDATE_CHANGED_DURING_CHECK")
    for source in checker.sources:
        _bound_file(source)
    _bound_file(task.contract)
    return observed


def recheck_original_session(*, source: BoundReuseFile, task: BoundReuseTask,
        checker: BoundReuseChecker, check: Checker) -> FreshReuseCheck:
    """Recheck a complete, unchanged session against its original bound task.

    Only this validated session path uses the existing session transport's
    32 MiB ceiling. Ordinary recipe files retain their 256 KiB limit. The
    supplied host callback owns the actual check; neither a saved session nor
    a successful structural hint supplies a semantic verdict. A QUERY remains
    unresolved and is not interpreted as an answer embedded in the session.
    The operator-owned callback must execute the declared original acceptance;
    returned fields alone are not authentication. This helper never chooses
    a command from learned guidance. Explicit session premises must match;
    legacy undeclared premises remain caller-bound, not historically proven.
    """
    from pfp.domain.pfp_ingress import strict_json
    from adversary.use_cases.teamwork import TeamworkRun, effective_acceptance

    source = BoundReuseFile.model_validate_json(source.model_dump_json())
    task = BoundReuseTask.model_validate_json(task.model_dump_json())
    checker = BoundReuseChecker.model_validate_json(checker.model_dump_json())
    path = Path(source.path)
    raw = _read(path, max_bytes=MAX_SESSION_RECHECK_BYTES)
    if _hash(raw) != source.sha256:
        _fail("REUSE_SOURCE_CHANGED")
    strict_json(raw.decode("utf-8"), max_bytes=MAX_SESSION_RECHECK_BYTES)
    run = TeamworkRun.model_validate_json(raw, strict=True)
    if run.objective != task.seed:
        _fail("SESSION_ORIGINAL_TASK_MISMATCH")
    if (run.brief is not None and run.brief.task_premises is not None
            and _program_digest(run.brief.task_premises) != _program_digest(task.premises)):
        _fail("SESSION_ORIGINAL_PREMISES_MISMATCH")
    acceptance = effective_acceptance(run)
    expected_checker = acceptance.checker_id if acceptance is not None else run.checker_id
    sources = {Path(item.path).absolute(): item.sha256 for item in checker.sources}
    if ((expected_checker and checker.checker_id != expected_checker)
            or acceptance is not None and any(sources.get(Path(path).absolute()) != digest
                for path, digest in acceptance.check_source_paths.items())):
        _fail("SESSION_ORIGINAL_CHECKER_MISMATCH")
    return _check(check, path, task, checker, source.sha256,
        candidate_limit=MAX_SESSION_RECHECK_BYTES, answer_candidate=False)


def apply_checked_ddc_recipe(*, registry_path: Path, expected_registry_sha256: str,
        recipe_id: str, target_seed: str, target_premises: dict,
        target_contract_sha256: str, output_path: Path,
        source_check: Checker, target_check: Checker, native_support: NativeOperationPort) -> Result[CheckedReuseResult, Refusal]:
    """Return a checked current result or explicit residual; never call an LLM.

    A target candidate is created exclusively and preserved even if its fresh
    check refuses. Existing candidates and historical DDC bundles are untouched.
    """
    try:
        registry = load_checked_reuse_registry(registry_path, expected_registry_sha256)
        recipe = next((item for item in registry.recipes if item.recipe_id == recipe_id), None)
        if recipe is None:
            _fail("UNREGISTERED_RECIPE")
        if (type(target_seed) is not str or target_seed != recipe.target_task.seed
                or type(target_premises) is not dict
                or _program_digest(target_premises) != _program_digest(recipe.target_task.premises)
                or target_contract_sha256 != recipe.target_task.contract.sha256):
            _fail("REUSE_TARGET_TASK_MISMATCH")
        if (recipe.program_binding.prompt_sha256 != _hash(recipe.source_task.seed.encode("utf-8"))
                or recipe.program_binding.premises_sha256 != _program_digest(recipe.source_task.premises)):
            _fail("REUSE_SOURCE_TASK_MISMATCH")
        loaded = load_ddc_program(recipe.program_path, expected=recipe.program_binding,
                                 initial_task_id=recipe.program_binding.storage_task_key, native_support=native_support)
        raw = _bound_file(recipe.source_candidate)
        candidate = _json(raw)
        if type(candidate) is not dict or candidate.get("seed") != recipe.source_task.seed:
            _fail("REUSE_SOURCE_SEED_MISMATCH")
        first = _check(source_check, Path(recipe.source_candidate.path), recipe.source_task,
                       recipe.checker, _hash(raw))
        state = _field_graph(candidate)
        rule = _registered_seed_rule(recipe.rule, recipe.source_task.seed, recipe.target_task.seed)
        if rule_digest(rule) != recipe.rule_sha256:
            _fail("REUSE_RULE_DIGEST_MISMATCH")
        protected = frozenset(part.id for part in state.parts if part.id != "seed")
        rewritten = apply_registered_rule(state, (rule,), rule.rule_id, recipe.part_match,
            recipe.link_match, fuel=recipe.fuel, protected_parts=protected)
        target = {dict(part.attrs)["key"]: _json(dict(part.attrs)["json"].encode("utf-8"))
                  for part in rewritten.state.parts}
        if target.get("seed") != recipe.target_task.seed or set(target) != set(candidate):
            _fail("REUSE_TARGET_SEED_MISMATCH")
        target_raw = json.dumps(target, sort_keys=True, separators=(",", ":"),
                                ensure_ascii=False, allow_nan=False).encode("utf-8")
        if len(target_raw) > MAX_REUSE_BYTES:
            _fail("REUSE_FILE_BOUND")
        # Existing output, hard links and source paths cannot be replaced.
        selected_output = Path(output_path).absolute()
        checked_path(Path(selected_output.anchor), selected_output)
        with selected_output.open("xb") as stream:
            stream.write(target_raw)
        second = _check(target_check, selected_output, recipe.target_task, recipe.checker, _hash(target_raw))
        if second.outcome != first.outcome or second.missing_fields != first.missing_fields:
            _fail("REUSE_OUTCOME_CHANGED")
        _bound_file(recipe.source_candidate)
        load_checked_reuse_registry(registry_path, expected_registry_sha256)
        load_ddc_program(recipe.program_path, expected=recipe.program_binding,
                         initial_task_id=recipe.program_binding.storage_task_key, native_support=native_support)
        if _read(selected_output) != target_raw:
            _fail("REUSE_CANDIDATE_CHANGED_AFTER_CHECK")
        return Ok(CheckedReuseResult(recipe_id=recipe.recipe_id,
            registry_sha256=expected_registry_sha256, source_candidate_sha256=_hash(raw),
            target_candidate_sha256=_hash(target_raw), output_path=str(selected_output),
            native_source_id=loaded["source_id"], semantic_ddc_root=recipe.program_binding.semantic_ddc_root,
            operation={"rule_id": rule.rule_id, "rule_sha256": rule_digest(rule),
                "before_sha256": graph_digest(state), "after_sha256": graph_digest(rewritten.state),
                "part_match": dict(rewritten.part_match), "link_match": dict(rewritten.link_match),
                "fuel": recipe.fuel, "fuel_remaining": rewritten.fuel_remaining,
                "protected_fields": sorted(protected)}, source_check=first, target_check=second,
            outcome=second.outcome,
            mathematical_acceptance="NOT_SOLVED" if second.outcome == "QUERY_USER_MORE_INFO" else "HOST_CHECKED"))
    except (ValueError, TypeError, KeyError, OSError, UnicodeError, RecursionError,
            ValidationError, ArchiveCustodyError) as error:
        code = error.code if isinstance(error, (RewriteRefusal, ArchiveCustodyError)) else str(error).split(":", 1)[0]
        if not code or any(not (character.isalnum() or character == "_") for character in code):
            code = "CHECKED_REUSE_REFUSED"
        return Err(Refusal(code, str(error) or "Checked reuse refused", __name__))


def validate_checked_reuse_result(*, registry_path: Path, expected_registry_sha256: str,
        result: CheckedReuseResult, native_support: NativeOperationPort) -> tuple[CheckedReuseResult, bytes]:
    """Reproduce prior custody/bindings without executing or promoting a check.

    The returned bytes are a current exact snapshot. A current workflow still
    needs its original-task checker; this function does not borrow a verdict.
    """
    result = CheckedReuseResult.model_validate_json(result.model_dump_json())
    registry = load_checked_reuse_registry(registry_path, expected_registry_sha256)
    recipe = next((item for item in registry.recipes if item.recipe_id == result.recipe_id), None)
    if recipe is None:
        _fail("UNREGISTERED_RECIPE")
    if result.registry_sha256 != expected_registry_sha256:
        _fail("REUSE_REGISTRY_CHANGED")
    if (recipe.program_binding.prompt_sha256 != _hash(recipe.source_task.seed.encode("utf-8"))
            or recipe.program_binding.premises_sha256 != _program_digest(recipe.source_task.premises)):
        _fail("REUSE_SOURCE_TASK_MISMATCH")
    loaded = load_ddc_program(recipe.program_path, expected=recipe.program_binding,
                             initial_task_id=recipe.program_binding.storage_task_key, native_support=native_support)
    source_raw = _bound_file(recipe.source_candidate)
    target_raw = _read(Path(result.output_path))
    source = _json(source_raw)
    target = _json(target_raw)
    if (type(source) is not dict or type(target) is not dict
            or source.get("seed") != recipe.source_task.seed
            or target.get("seed") != recipe.target_task.seed
            or result.source_candidate_sha256 != _hash(source_raw)
            or result.target_candidate_sha256 != _hash(target_raw)
            or result.semantic_ddc_root != recipe.program_binding.semantic_ddc_root
            or result.native_source_id != loaded["source_id"]):
        _fail("REUSE_RESULT_BINDING_MISMATCH")
    for checker_file in recipe.checker.sources:
        _bound_file(checker_file)
    for task, raw, value, check in (
            (recipe.source_task, source_raw, source, result.source_check),
            (recipe.target_task, target_raw, target, result.target_check)):
        _bound_file(task.contract)
        expected = {"checker_id": recipe.checker.checker_id, "candidate_sha256": _hash(raw),
            "seed_sha256": _hash(task.seed.encode("utf-8")),
            "premises_sha256": _program_digest(task.premises),
            "contract_sha256": task.contract.sha256,
            "checker_source_sha256": checker_source_digest(recipe.checker)}
        if any(getattr(check, key) != item for key, item in expected.items()):
            _fail("REUSE_CHECK_BINDING_MISMATCH")
        if ("outcome" in value and value["outcome"] != check.outcome) or (
                check.outcome == "QUERY_USER_MORE_INFO"
                and value.get("missing_fields") != list(check.missing_fields)):
            _fail("REUSE_QUERY_BINDING_MISMATCH")
    if (result.source_check.outcome != result.target_check.outcome
            or result.source_check.missing_fields != result.target_check.missing_fields
            or result.outcome != result.target_check.outcome
            or result.mathematical_acceptance != (
                "NOT_SOLVED" if result.outcome == "QUERY_USER_MORE_INFO" else "HOST_CHECKED")):
        _fail("REUSE_OUTCOME_CHANGED")
    state = _field_graph(source)
    rule = _registered_seed_rule(recipe.rule, recipe.source_task.seed, recipe.target_task.seed)
    if rule_digest(rule) != recipe.rule_sha256:
        _fail("REUSE_RULE_DIGEST_MISMATCH")
    protected = frozenset(part.id for part in state.parts if part.id != "seed")
    rewritten = apply_registered_rule(state, (rule,), rule.rule_id, recipe.part_match,
        recipe.link_match, fuel=recipe.fuel, protected_parts=protected)
    reproduced = {dict(part.attrs)["key"]: _json(dict(part.attrs)["json"].encode("utf-8"))
                  for part in rewritten.state.parts}
    if json.dumps(reproduced, sort_keys=True, separators=(",", ":"),
                  ensure_ascii=False, allow_nan=False).encode("utf-8") != target_raw:
        _fail("REUSE_RESULT_BINDING_MISMATCH")
    expected_operation = {"rule_id": rule.rule_id, "rule_sha256": rule_digest(rule),
        "before_sha256": graph_digest(state), "after_sha256": graph_digest(rewritten.state),
        "part_match": dict(rewritten.part_match), "link_match": dict(rewritten.link_match),
        "fuel": recipe.fuel, "fuel_remaining": rewritten.fuel_remaining,
        "protected_fields": sorted(protected)}
    if _program_digest(result.operation) != _program_digest(expected_operation):
        _fail("REUSE_OPERATION_MISMATCH")
    if _bound_file(recipe.source_candidate) != source_raw or _read(Path(result.output_path)) != target_raw:
        _fail("REUSE_SOURCE_CHANGED")
    load_checked_reuse_registry(registry_path, expected_registry_sha256)
    load_ddc_program(recipe.program_path, expected=recipe.program_binding,
                     initial_task_id=recipe.program_binding.storage_task_key, native_support=native_support)
    return result, target_raw


def validate_checked_reuse_dispatch(action, *, native_support: NativeOperationPort) -> None:
    """Check current registered reuse on either IDE or remote host dispatch.

    A valid PFP acknowledgement and an existing artifact cannot replace the
    native recipe readback, current target task and exact candidate snapshot.
    """
    brief = action.brief
    if brief is None or brief.checked_reuse_result is None:
        return
    binding = brief.checked_reuse_registry
    if binding is None or type(brief.task_premises) is not dict:
        _fail("CHECKED_REUSE_CURRENT_TASK_MISMATCH")
    result, candidate_bytes = validate_checked_reuse_result(registry_path=Path(binding.path),
        expected_registry_sha256=binding.sha256, result=brief.checked_reuse_result, native_support=native_support)
    registry = load_checked_reuse_registry(Path(binding.path), binding.sha256)
    recipe = next(row for row in registry.recipes if row.recipe_id == result.recipe_id)
    if (candidate_bytes.decode("utf-8") != brief.checked_reuse_candidate
            or recipe.target_task.seed != action.objective
            or _json(candidate_bytes)["seed"] != action.objective
            or _program_digest(recipe.target_task.premises) != _program_digest(brief.task_premises)):
        _fail("CHECKED_REUSE_CURRENT_TASK_MISMATCH")


def registered_reuse_roundtrip_witness(*, registry_path: Path, expected_registry_sha256: str,
        recipe_id: str, result: CheckedReuseResult, native_support: NativeOperationPort) -> dict:
    """Read-only finite forward/inverse control, not an OS sandbox certificate.

    The inverse is explicitly registered here only for this recorded control.
    It grants no general recipe admission or production mutation permission.
    The caller owns persistence and binding of the returned sidecar.
    """
    result, _ = validate_checked_reuse_result(registry_path=registry_path,
        expected_registry_sha256=expected_registry_sha256, result=result, native_support=native_support)
    registry = load_checked_reuse_registry(registry_path, expected_registry_sha256)
    recipe = next((item for item in registry.recipes if item.recipe_id == recipe_id), None)
    if recipe is None:
        _fail("UNREGISTERED_RECIPE")
    result = CheckedReuseResult.model_validate_json(result.model_dump_json())
    source_raw = _bound_file(recipe.source_candidate)
    target_raw = _read(Path(result.output_path))
    if (result.recipe_id != recipe_id or result.registry_sha256 != expected_registry_sha256
            or result.source_candidate_sha256 != _hash(source_raw)
            or result.target_candidate_sha256 != _hash(target_raw)):
        _fail("REUSE_ROUNDTRIP_BINDING_MISMATCH")
    for source in recipe.checker.sources:
        _bound_file(source)
    _bound_file(recipe.source_task.contract)
    _bound_file(recipe.target_task.contract)
    original = _json(source_raw)
    state = _field_graph(original)
    forward = _registered_seed_rule(recipe.rule, recipe.source_task.seed, recipe.target_task.seed)
    if rule_digest(forward) != recipe.rule_sha256:
        _fail("REUSE_RULE_DIGEST_MISMATCH")
    protected = frozenset(part.id for part in state.parts if part.id != "seed")
    rewritten = apply_registered_rule(state, (forward,), forward.rule_id, recipe.part_match,
        recipe.link_match, fuel=recipe.fuel, protected_parts=protected)
    rewritten_object = {dict(part.attrs)["key"]: _json(dict(part.attrs)["json"].encode("utf-8"))
                        for part in rewritten.state.parts}

    def canonical(value):
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")

    if canonical(rewritten_object) != target_raw:
        _fail("REUSE_ROUNDTRIP_BINDING_MISMATCH")
    inverse = DpoRule("checked_reuse_inverse_control", forward.right, FiniteACSet(), forward.left)
    seed_part = next(part for part in rewritten.state.parts if dict(part.attrs)["key"] == "seed")
    restored = apply_registered_rule(rewritten.state, (inverse,), inverse.rule_id,
        {"seed": seed_part.id}, {}, fuel=1, protected_parts=protected)
    restored_object = {dict(part.attrs)["key"]: _json(dict(part.attrs)["json"].encode("utf-8"))
                       for part in restored.state.parts}
    canonical_before, canonical_restored = canonical(original), canonical(restored_object)
    if canonical_before != canonical_restored or _bound_file(recipe.source_candidate) != source_raw:
        _fail("REUSE_ROUNDTRIP_NOT_RESTORED")
    return {
        "schema_version": "core.adversary.checked-reuse-roundtrip.v1",
        "source_mode": "REGISTERED_FORWARD_INVERSE_FINITE_CONTROL",
        "native_intergate_witness": {
            "canonical_before_hex": source_raw.hex(), "canonical_after_hex": source_raw.hex(),
            "sandbox_before_hex": canonical_before.hex(),
            "sandbox_restored_hex": canonical_restored.hex(),
            "sandbox_boundary_active": True, "declared_authority_effect": "None",
            "has_production_side_effects": False,
        },
        "forward_rule": asdict(forward), "inverse_control_rule": asdict(inverse),
        "forward_rule_sha256": rule_digest(forward), "inverse_rule_sha256": rule_digest(inverse),
        "source_candidate_sha256": _hash(source_raw), "target_candidate_sha256": _hash(target_raw),
        "source_graph_sha256": graph_digest(state), "target_graph_sha256": graph_digest(rewritten.state),
        "restored_graph_sha256": graph_digest(restored.state),
        "checker_source_sha256": checker_source_digest(recipe.checker),
        "source_contract_sha256": recipe.source_task.contract.sha256,
        "target_contract_sha256": recipe.target_task.contract.sha256,
        "registry_sha256": expected_registry_sha256,
        "semantic_ddc_root": recipe.program_binding.semantic_ddc_root,
        "serialization_profile": "python.sorted-compact-utf8-json.v1",
        "provider_calls": 0, "authority_effect": "None",
        "limits": ["Pure bounded field-graph control only; no OS sandbox claim.",
                   "Restoration compares decoded canonical candidate bytes; fresh node IDs may differ.",
                   "Inverse registration is for this explicit control, not automatic general reuse."],
    }
