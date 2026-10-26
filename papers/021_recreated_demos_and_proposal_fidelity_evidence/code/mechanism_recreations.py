"""Bounded offline intervention demonstrations; never empirical model results.

The C002--C010 source documents specify studies, rather than retained runnable
studies. Here their mechanical components have real inputs and negative controls.
Each result keeps the unperformed empirical obligations explicit. Mathematical
graph evaluation and certificate verification use hash-bound Rust executables.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import stat
import subprocess
import sys
from dataclasses import dataclass
from fractions import Fraction
from importlib.metadata import version
from pathlib import Path
from typing import Any

SCHEMA = "paper011.mechanism-recreation.v1"
MIN_TORCH = (2, 13, 0)
PFP = "omega_engine_education/documentation/030_the_symbol_game_proposal_fidelity_protocol_pfp/demos"
MECHANISM_SPECS = {
    "C001": "c001_attention_distractor_mask_task_level.md",
    "C002": "c002_attention_steering_sweep_correctness.md",
    "C003": "c003_head_attribution_activation_patching.md",
    "C004": "c004_grammar_masked_decode_ladder.md",
    "C005": "c005_hosted_decode_controls_bakeoff.md",
    "C006": "c006_host_scratch_space_vs_cot.md",
    "C007": "c007_context_compaction_kv_surgery.md",
    "C008": "c008_activation_steering_sign_discipline.md",
    "C009": "c009_model_size_ladder_advantage_curve.md",
    "C010": "c010_repeated_sampling_frontier.md",
}
INCIDENCE = [["-1", "1", "0"], ["0", "-1", "1"], ["1", "0", "-1"]]


class MechanismError(ValueError):
    """An invalid fixture or an unbound replay capability."""


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False, ensure_ascii=True).encode("utf-8")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def regular(path: Path) -> None:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise MechanismError("NONREGULAR_OR_REDIRECTED_FILE")
    for ancestor in path.parents:
        info = ancestor.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise MechanismError("REDIRECTED_ANCESTOR")


def _unique(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise MechanismError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def load(raw: bytes) -> Any:
    if raw.startswith(b"\xef\xbb\xbf"):
        raise MechanismError("BOM_REFUSED")
    return json.loads(raw, object_pairs_hook=_unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(MechanismError("NONFINITE_JSON")))


def capture_sources(repository: Path) -> dict:
    """Capture a small, declared source set; do not copy any corpus."""
    folder = repository / PFP / "challenges/a_mechanism"
    files = {}
    for name in MECHANISM_SPECS.values():
        path = folder / name
        regular(path)
        files[path.relative_to(repository).as_posix()] = sha(path.read_bytes())
    for relative in (
        "challenges/a_mechanism/c001_attention_distractor_mask/attention_hook.py",
        "challenges/a_mechanism/c005_hosted_decode_controls/checkers.py",
        "challenges/a_mechanism/c005_hosted_decode_controls/schemas.py",
        "demos/demo_mub6_regge/README.md", "demos/demo_symbol_tui/README.md",
    ):
        path = repository / PFP / relative
        regular(path)
        files[path.relative_to(repository).as_posix()] = sha(path.read_bytes())
    head = subprocess.run(["git", "-C", str(repository), "rev-parse", "HEAD"],
                          check=True, capture_output=True, text=True).stdout.strip()
    return {"schema_version": "paper011.mechanism-source-bindings.v1", "source_git_head": head,
            "files": dict(sorted(files.items(), key=lambda row: row[0].encode("utf-8")))}


def verify_sources(repository: Path, binding: dict) -> None:
    if binding.get("schema_version") != "paper011.mechanism-source-bindings.v1" or not binding.get("files"):
        raise MechanismError("SOURCE_BINDING_REQUIRED")
    for relative, expected in binding["files"].items():
        if not isinstance(relative, str) or "\\" in relative or ":" in relative or any(
            part in {"", ".", ".."} for part in relative.split("/")
        ):
            raise MechanismError("SOURCE_PATH_ESCAPE")
        path = repository / relative
        regular(path)
        if sha(path.read_bytes()) != expected:
            raise MechanismError("SOURCE_BYTES_CHANGED: " + relative)


@dataclass(frozen=True)
class Native:
    """Explicit byte-bound finite host; retains every request and response."""

    path: Path
    expected_sha256: str
    functional: bool = False

    def call(self, action: str, payload: dict) -> dict:
        regular(self.path)
        if sha(self.path.read_bytes()) != self.expected_sha256:
            raise MechanismError("NATIVE_BYTES_CHANGED")
        request = payload if self.functional else {
            "schema_version": "omega.symbol-game.runtime-request.v1", "action": action, "payload": payload,
        }
        raw = canonical(request)
        if len(raw) > 65_536:
            raise MechanismError("REQUEST_TOO_LARGE")
        command = [str(self.path)] + ([] if self.functional else ["invoke"])
        result = subprocess.run(command, input=raw, capture_output=True, check=False, timeout=30)
        if sha(self.path.read_bytes()) != self.expected_sha256:
            raise MechanismError("NATIVE_BYTES_CHANGED_DURING_CALL")
        if result.returncode:
            raise MechanismError("NATIVE_PROCESS_FAILURE: " + result.stderr.decode("utf-8", "replace")[:500])
        response = load(result.stdout)
        if self.functional:
            if response.get("status") != "PASS" or not isinstance(response.get("result"), dict):
                raise MechanismError("NATIVE_GRAPH_REFUSAL")
        elif (response.get("schema_version") != "omega.symbol-game.runtime-outcome.v1"
              or response.get("action") != action or response.get("success") is not True
              or response.get("error") is not None or not isinstance(response.get("result"), dict)):
            raise MechanismError("NATIVE_RUNTIME_REFUSAL: " + str(response.get("error")))
        return {"request": request, "request_sha256": sha(raw), "response": response,
                "response_bytes_sha256": sha(result.stdout), "binary_sha256": self.expected_sha256}


def public_torch_version(text: str) -> tuple[int, int, int]:
    base = text.split("+", 1)[0]
    parts = base.split(".")
    if (
        len(parts) != 3
        or any(
            not part.isascii() or not part.isdigit() or (len(part) > 1 and part.startswith("0"))
            for part in parts
        )
    ):
        raise MechanismError("TORCH_VERSION_MISMATCH")
    return (int(parts[0]), int(parts[1]), int(parts[2]))


def require_torch_version(installed: str) -> None:
    if public_torch_version(installed) < MIN_TORCH:
        raise MechanismError("TORCH_VERSION_MISMATCH")


def torch_cpu():
    require_torch_version(version("torch"))
    import torch
    torch.set_num_threads(1)
    return torch


def record(cid: str, mechanism: dict, controls: dict, missing: list[str]) -> dict:
    if not controls or any(type(value) is not bool or value is not True for value in controls.values()):
        raise MechanismError("MECHANISM_CONTROL_FAILED: " + cid)
    return {"schema_version": SCHEMA, "id": cid, "grade": "FRESH_OFFLINE_MECHANISM_FIXTURE",
            "mechanism": mechanism, "controls": controls, "empirical_result": False,
            "challenge_gate_satisfied": False, "unperformed_obligations": missing,
            "scope": "Declared finite mechanism fixture; no model accuracy, benefit or significance result."}


def attention_mask(allowed: Any, positions: list[int], position_ids: Any):
    torch = torch_cpu()
    if not torch.equal(position_ids, torch.arange(allowed.shape[-1], device="cpu")):
        raise MechanismError("POSITION_IDS_CHANGED")
    if any(type(p) is not int or p < 0 or p >= allowed.shape[-1] for p in positions):
        raise MechanismError("MASK_POSITION_OUT_OF_RANGE")
    result = allowed.clone()
    result[..., positions] = False
    return result


def c001() -> dict:
    """Recreate the key-column intervention with explicit character offsets."""
    torch = torch_cpu()
    prompt = "A 1 B 1 noise"
    offsets = [(m.start(), m.end()) for m in re.finditer(r"\S+", prompt)]
    spans = [(8, 13)]
    positions = [i for i, (a, b) in enumerate(offsets) if any(c <= a < b <= d for c, d in spans)]
    allowed = torch.tril(torch.ones((1, 2, 5, 5), dtype=torch.bool))
    pos = torch.arange(5)
    masked = attention_mask(allowed, positions, pos)
    null = attention_mask(allowed, [], pos)
    bad_position_refused = False
    try:
        attention_mask(allowed, positions, pos + 1)
    except MechanismError:
        bad_position_refused = True
    return record("C001", {"prompt": prompt, "offsets": offsets, "distractor_spans": spans,
                           "selected_key_positions": positions, "before": allowed.int().tolist(),
                           "after": masked.int().tolist(), "position_ids": pos.tolist(),
                           "adaptation": "Paper tensor reconstruction of retained key-mask rule; not an executed model hook."},
                  {"null_is_identical": torch.equal(null, allowed),
                   "selected_keys_blocked": not bool(masked[..., positions].any()),
                   "nonselected_keys_preserved": torch.equal(masked[..., :4], allowed[..., :4]),
                   "shifted_positions_refused": bad_position_refused},
                  ["Pinned model execution with eager attention", "Token-for-token null-arm check on real model",
                   "Host-rescored hidden cases and paired accuracy statistics", "Independent two-signal immune gate replay"])


def c002() -> dict:
    torch = torch_cpu()
    scores = torch.tensor([[0.2, -0.3, 0.5, 0.1]], dtype=torch.float64)
    positions = [1, 2]
    rows = []
    for delta in [0, 0.5, 1, 2, 4, 8, 16]:
        bias = torch.zeros_like(scores)
        bias[:, positions] = delta
        probabilities = torch.softmax(scores + bias, dim=-1)
        rows.append({"delta": str(delta), "carrier_mass": probabilities[:, positions].sum().item(),
                     "probabilities": probabilities.tolist()})
    base = torch.softmax(scores, dim=-1)
    return record("C002", {"scores": scores.tolist(), "carrier_positions": positions, "sweep": rows,
                           "model": "NONE; explicit attention-score fixture"},
                  {"null_is_identical": rows[0]["probabilities"] == base.tolist(),
                   "carrier_mass_increases": all(a["carrier_mass"] < b["carrier_mass"] for a, b in zip(rows, rows[1:])),
                   "carrier_bias_changes_probabilities": rows[0]["probabilities"] != rows[-1]["probabilities"]},
                  ["Public host-verified selection over 19 settings", "Freeze selection before hidden reveal",
                   "Pinned-model hidden, random-key and maximum-steering arms with three seeds"])


def patch_head(corrupted: Any, clean: Any, head: int):
    if corrupted.shape != clean.shape or type(head) is not int or not 0 <= head < corrupted.shape[0]:
        raise MechanismError("PATCH_SHAPE_OR_HEAD")
    result = corrupted.clone()
    result[head] = clean[head]
    return result


def c003() -> dict:
    torch = torch_cpu()
    clean = torch.tensor([[3.0, 0.0], [0.0, 1.0]], dtype=torch.float64)
    corrupt = torch.tensor([[-1.0, 0.0], [0.0, 1.0]], dtype=torch.float64)
    readout = torch.tensor([1.0, -1.0], dtype=torch.float64)
    def ld(heads):
        return torch.dot(heads.sum(dim=0), readout).item()
    clean_ld, corrupt_ld = ld(clean), ld(corrupt)
    effects = [{"head": head, "patched_ld": ld(patch_head(corrupt, clean, head)),
                "normalized_effect": (ld(patch_head(corrupt, clean, head)) - corrupt_ld) / (clean_ld - corrupt_ld)}
               for head in range(2)]
    whole_patch = corrupt
    for head in range(2):
        whole_patch = patch_head(whole_patch, clean, head)
    return record("C003", {"clean_heads": clean.tolist(), "corrupted_heads": corrupt.tolist(),
                           "readout": readout.tolist(), "clean_ld": clean_ld, "corrupt_ld": corrupt_ld,
                           "effects": effects, "ranking": sorted(range(2), key=lambda h: (-effects[h]["normalized_effect"], h))},
                  {"whole_clean_patch_recovers_clean": torch.equal(whole_patch, clean) and ld(whole_patch) == clean_ld,
                   "irrelevant_head_has_zero_effect": effects[1]["normalized_effect"] == 0,
                   "causal_head_recovers_difference": effects[0]["normalized_effect"] == 1,
                   "null_patch_is_identical": torch.equal(patch_head(corrupt, corrupt, 0), corrupt)},
                  ["300 public attribution prompt pairs on pinned model", "Public selection of k and alpha",
                   "Frozen-head hidden, random, attention-ranked and ablation arms"])


def integer_prefix(prefix: str, slots: int) -> tuple[bool, bool]:
    """Bounded signed-integer slot recognizer; exact arity, canonical integers."""
    if type(slots) is not int or not 1 <= slots <= 12 or not isinstance(prefix, str):
        raise MechanismError("GRAMMAR_INPUT")
    parts = prefix.split(" ")
    if len(parts) > slots:
        return False, False
    integer = re.compile(r"(?:0|-?[1-9][0-9]*)\Z")
    if any(not integer.fullmatch(part) for part in parts[:-1]):
        return False, False
    last = parts[-1]
    if not (last in {"", "-"} or integer.fullmatch(last)):
        return False, False
    complete = len(parts) == slots and bool(integer.fullmatch(last))
    return True, complete


def grammar_generate(proposals: list[str], slots: int) -> tuple[str, list[dict]]:
    """Actually reject proposed characters before accepting each emitted token."""
    prefix = ""
    trace = []
    for target in proposals:
        options = ["x", target]
        accepted = None
        for token in options:
            viable, complete = integer_prefix(prefix + token, slots)
            trace.append({"prefix": prefix, "proposed": token, "admitted": viable, "complete": complete})
            if viable:
                accepted = token
                break
        if accepted is None:
            raise MechanismError("EMPTY_GRAMMAR_FRONTIER")
        prefix += accepted
    if not integer_prefix(prefix, slots)[1]:
        raise MechanismError("INCOMPLETE_GRAMMAR_OUTPUT")
    return prefix, trace


def c004(host: Native) -> dict:
    output, trace = grammar_generate(list("1 1 -2"), 3)
    candidate = output.split(" ")
    zero = host.call("verify_l1_certificate", {"matrix": {"rows": INCIDENCE},
        "omega": candidate, "p": ["0", "1", "2"], "y": ["0", "0", "0"]})
    corrupt_candidate = host.call("verify_l1_certificate", {"matrix": {"rows": INCIDENCE},
        "omega": ["1", "1", "-3"], "p": ["0", "1", "2"], "y": ["0", "0", "0"]})
    certificate = host.call("verify_l1_certificate", {"matrix": {"rows": INCIDENCE},
        "omega": ["1", "1", "1"], "p": ["0", "1", "2"], "y": ["1", "1", "1"]})
    wrong = host.call("verify_l1_certificate", {"matrix": {"rows": INCIDENCE},
        "omega": ["1", "1", "1"], "p": ["0", "1", "2"], "y": ["0", "0", "0"]})
    native = certificate["response"]["result"]
    return record("C004", {"raw_output": output, "output_sha256": sha(output.encode()), "grammar_trace": trace,
                           "original_claims": ["1", "1", "1"], "repaired_claims": candidate,
                           "candidate_zero_certificate": zero, "corrupted_candidate_control": corrupt_candidate,
                           "certificate": certificate, "corrupted_dual_control": wrong},
                  {"output_independently_validated": integer_prefix(output, 3) == (True, True),
                   "noncanonical_integer_rejected": not integer_prefix("007 1 -8", 3)[0],
                   "wrong_arity_rejected": not integer_prefix("1 1 -2 0", 3)[0],
                   "actual_output_candidate_zero_checked": zero["response"]["result"].get("accepted") is True
                       and zero["response"]["result"]["certificate"]["dual_value"] == "0",
                   "corrupted_candidate_refused": corrupt_candidate["response"]["result"].get("accepted") is False,
                   "native_optimality_certificate_accepted": native.get("accepted") is True and native["certificate"]["dual_value"] == "3",
                   "bad_dual_refused": wrong["response"]["result"].get("accepted") is False},
                  ["Pinned tokenizer and model decode ladder", "Hidden cases at out-of-public-range cycle lengths",
                   "Four-arm model validity, zero-reaching and optimality comparisons"])


def graph(phi: Native, claims: list[str]) -> dict:
    return phi.call("graph_phi1", {"vertices": ["A", "B", "C"], "edges": [
        {"u": u, "v": v, "weight": "1", "claim": value}
        for (u, v), value in zip([("A", "B"), ("B", "C"), ("C", "A")], claims, strict=True)
    ]})


def load_retained_module(repository: Path, binding: dict, relative: str):
    verify_sources(repository, binding)
    key = PFP + "/" + relative
    if key not in binding["files"]:
        raise MechanismError("UNBOUND_SOURCE_MODULE")
    path = repository / key
    name = "paper011_retained_" + sha(path.read_bytes())[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise MechanismError("SOURCE_MODULE_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def c005(repository: Path, binding: dict, phi: Native) -> dict:
    schema = load_retained_module(repository, binding, "challenges/a_mechanism/c005_hosted_decode_controls/schemas.py")
    checker = load_retained_module(repository, binding, "challenges/a_mechanism/c005_hosted_decode_controls/checkers.py")
    raw = b'{"verdict":"INCONSISTENT","certificate":{}}'
    proposal = load(raw)
    shape, _ = schema.validate_json_schema(proposal, "consistency_verdict")
    legacy = checker.verify_consistency_certificate([("A", "B", 1), ("B", "C", 1), ("C", "A", -2)],
                                                   proposal["verdict"], proposal["certificate"])
    native = graph(phi, ["1", "1", "-2"])
    malformed, _ = schema.validate_json_schema({"verdict": "INCONSISTENT"}, "consistency_verdict")
    return record("C005", {"raw_output": raw.decode(), "output_sha256": sha(raw),
                           "schema_valid": shape, "retained_checker_accepts": legacy.is_valid,
                           "native_graph": native, "falsifier": "Retained checker accepts an unsupported contradiction on a native zero-defect graph."},
                  {"retained_false_positive_reproduced": shape is True and legacy.is_valid is True,
                   "native_graph_is_consistent": native["response"]["result"]["phi1"] == "0",
                   "missing_certificate_shape_refused": malformed is False},
                  ["Provider capability probes and actual byte-bound controlled responses",
                   "Corrected independent inconsistency witness checker", "Hosted matched-arm bakeoff"])


def compact_ledger(declarations: list[dict], restatements: list[dict]) -> tuple[bytes, list[str]]:
    authoritative = {}
    refused = []
    for item in declarations:
        cid = item["id"]
        if not isinstance(cid, str) or cid in authoritative:
            raise MechanismError("DUPLICATE_CONSTRAINT_ID")
        authoritative[cid] = canonical(item)
    for item in restatements:
        if item.get("id") not in authoritative or canonical(item) != authoritative[item["id"]]:
            refused.append(item.get("id", "UNKNOWN"))
    return b"\n".join(authoritative[key] for key in sorted(authoritative)), refused


def c006(host: Native, phi: Native) -> dict:
    original = graph(phi, ["1", "1", "1"])
    stationary = graph(phi, ["1", "1", "1"])
    repaired = graph(phi, ["1", "1", "-2"])
    values = [call["response"]["result"]["phi1"] for call in [original, stationary, repaired]]
    declarations = [{"id": name, "claim": claim, "repairable": name == "CA"}
                    for name, claim in zip(["AB", "BC", "CA"], ["1", "1", "1"], strict=True)]
    ledger, refused = compact_ledger(declarations, [{"id": "AB", "claim": "9", "repairable": False}])
    history = [{"turn": turn, "host_state_digest": sha(canonical(["1", "1", "1"])),
                "canonical_move_digest": sha(canonical({"CUT": ["1", "1", "1"]})),
                "move_kind": "CUT", "target_variable": None, "outcome": "IdempotentStationary"}
               for turn in [1, 2]]
    attractor = host.call("detect_stationary_attractor", {"history": history, "decided_variables": []})
    return record("C006", {"session": [{"move": "ASSERT", "evaluation": original},
                                      {"move": "CUT", "outcome": "REFUSED_STATIONARY", "evaluation": stationary},
                                      {"move": "CUT", "outcome": "ADMITTED_DESCENT", "evaluation": repaired},
                                      {"move": "VERIFY", "outcome": "ACCEPTED_ZERO_DEFECT_FIXTURE"}],
                           "scratch_bytes": ledger.decode(), "scratch_sha256": sha(ledger),
                           "constraint_edit_refusals": refused, "attractor": attractor,
                           "session_policy": "Paper bounded session over native evaluated states; no model or canonical driver claim."},
                  {"strict_descent_measured_natively": Fraction(values[2]) < Fraction(values[0]),
                   "stationary_cut_not_descent": values[0] == values[1],
                   "zero_terminal_backed_by_native": values[2] == "0",
                   "protected_constraint_edit_refused": refused == ["AB"],
                   "native_repeated_cut_detected": attractor["response"]["result"]["escalate"] is True},
                  ["Full declared K4 through cycle-rank-8 board families", "Canonical scratch-board adapter dependency repair",
                   "Pinned-model scratch versus matched chain-of-thought sessions and statistics"])


def retained_kv_positions(length: int, constraint_positions: list[int], capacity: int) -> list[int]:
    if any(type(p) is not int or not 0 <= p < length for p in constraint_positions):
        raise MechanismError("KV_POSITION_INVALID")
    mandatory = set(constraint_positions)
    if type(capacity) is not int or len(mandatory) > capacity or capacity > length:
        raise MechanismError("KV_CAPACITY_CANNOT_RETAIN_CONSTRAINTS")
    recent = [i for i in reversed(range(length)) if i not in mandatory][:capacity-len(mandatory)]
    return sorted(mandatory | set(recent))


def c007() -> dict:
    torch = torch_cpu()
    declarations = [{"id": "s1:AB", "claim": "1", "repairable": False},
                    {"id": "s2:BC", "claim": "1", "repairable": False},
                    {"id": "s3:CA", "claim": "1", "repairable": True}]
    compacted, refusals = compact_ledger(declarations, [{"id": "s1:AB", "claim": "2", "repairable": False}])
    positions = [0, 1, 4, 5, 8, 9]
    kept = retained_kv_positions(16, positions, 8)
    cache = torch.arange(32, dtype=torch.float64).reshape(1, 1, 16, 2)
    evicted = cache[:, :, kept, :].clone()
    impossible = False
    try:
        retained_kv_positions(16, positions, 5)
    except MechanismError:
        impossible = True
    return record("C007", {"constraint_ledger_bytes": compacted.decode(), "ledger_sha256": sha(compacted),
                           "typo_restatement_refusals": refusals, "constraint_positions": positions,
                           "retained_positions": kept, "original_kv": cache.tolist(), "retained_kv": evicted.tolist(),
                           "kv_scope": "Explicit tensor cache fixture; not model-generated key/value activations."},
                  {"all_declared_constraints_retained": len(compacted.splitlines()) == len(declarations),
                   "typo_cannot_replace_authority": refusals == ["s1:AB"] and b'"claim":"2"' not in compacted,
                   "all_constraint_kv_positions_retained": set(positions) <= set(kept),
                   "kept_kv_values_identical": torch.equal(evicted, cache[:, :, kept, :]),
                   "impossible_retention_budget_refused": impossible},
                  ["30-to-48-turn canonical staged repair sessions", "Real model KV-prefix reuse identity check",
                   "Matched text, KV eviction and window model outcomes"])


def c008() -> dict:
    torch = torch_cpu()
    correct = torch.tensor([[2.0, 0.0], [4.0, 0.0]], dtype=torch.float64)
    flipped = torch.tensor([[-2.0, 0.0], [-4.0, 0.0]], dtype=torch.float64)
    direction = correct.mean(dim=0) - flipped.mean(dim=0)
    residual = torch.tensor([[1.0, 2.0], [3.0, 4.0]], dtype=torch.float64)
    scale = torch.linalg.vector_norm(residual, dim=-1).mean() / torch.linalg.vector_norm(direction)
    steered = residual + scale * direction
    random_direction = torch.tensor([0.0, 6.0], dtype=torch.float64)
    random_control = residual + scale * random_direction
    return record("C008", {"public_correct_activations": correct.tolist(), "public_flipped_activations": flipped.tolist(),
                           "direction": direction.tolist(), "direction_sha256": sha(canonical(direction.tolist())),
                           "alpha": "1", "norm_scale": scale.item(), "before": residual.tolist(),
                           "steered": steered.tolist(), "random_control": random_control.tolist(),
                           "model": "NONE; residual-stream tensor fixture"},
                  {"mean_difference_computed": direction.tolist() == [6.0, 0.0],
                   "null_steering_identical": torch.equal(residual + 0 * direction, residual),
                   "steering_changes_selected_component": not torch.equal(steered[:, 0], residual[:, 0]),
                   "orthogonal_component_preserved": torch.equal(steered[:, 1], residual[:, 1]),
                   "equal_norm_random_control": torch.equal(torch.linalg.vector_norm(direction), torch.linalg.vector_norm(random_direction))},
                  ["200 pinned-model public Pauli phase contrast pairs", "Native per-site Pauli certificate checker",
                   "Public layer/alpha selection and frozen hidden/control model runs"])


def paired_gap(rows: list[dict]) -> dict:
    if not rows or len({row["case_id"] for row in rows}) != len(rows):
        raise MechanismError("DUPLICATE_OR_EMPTY_PAIRED_CASES")
    if any(type(row.get(arm)) is not bool for row in rows for arm in ("A", "B")):
        raise MechanismError("VERDICTS_MUST_BE_BOOLEAN")
    n = len(rows)
    a, b = sum(row["A"] for row in rows), sum(row["B"] for row in rows)
    return {"n": n, "A_successes": a, "B_successes": b, "gap": str(Fraction(a-b, n)),
            "A_only": sum(row["A"] and not row["B"] for row in rows),
            "B_only": sum(row["B"] and not row["A"] for row in rows)}


def c009() -> dict:
    rows = [{"case_id": str(i), "A": a, "B": b}
            for i, (a, b) in enumerate([(True, False), (True, True), (False, False), (False, True)])]
    duplicate_refused = False
    try:
        paired_gap(rows + rows[:1])
    except MechanismError:
        duplicate_refused = True
    return record("C009", {"rows": rows, "paired_summary": paired_gap(rows),
                           "model_ladder_runs": [], "fixture_scope": "Tally mechanics only; no model rung measurement."},
                  {"paired_gap_zero": paired_gap(rows)["gap"] == "0",
                   "opposite_discordances_preserved": paired_gap(rows)["A_only"] == paired_gap(rows)["B_only"] == 1,
                   "duplicate_observations_refused": duplicate_refused},
                  ["Seven pinned model rungs and five anchor families", "Independent rescore of shared hidden cases",
                   "Three seeds, per-cell budget receipts, intervals and corrected paired significance tests"])


def coverage_at_k(n: int, verified: int, k: int) -> str:
    if any(type(value) is not int for value in (n, verified, k)) or not 0 <= verified <= n or not 1 <= k <= n:
        raise MechanismError("COVERAGE_INPUT")
    return str(1 - Fraction(math.comb(n-verified, k), math.comb(n, k)))


def c010(phi: Native) -> dict:
    proposals = [["1", "1", "1"], ["1", "1", "1"], ["1", "1", "-2"], ["0", "1", "-1"]]
    cache, samples = {}, []
    for index, proposal in enumerate(proposals):
        key = sha(canonical(proposal))
        if key not in cache:
            cache[key] = graph(phi, proposal)
        verdict = cache[key]["response"]["result"]["phi1"] == "0"
        samples.append({"index": index, "proposal": proposal, "candidate_sha256": key, "verified_consistent": verdict,
                        "checker_call": key, "input_type": "Explicit new cochain fixture, no edit-optimality claim"})
    verified = sum(row["verified_consistent"] for row in samples)
    first = next(row["index"] for row in samples if row["verified_consistent"])
    return record("C010", {"samples": samples, "checker_calls": list(cache.values()),
                           "coverage_at_k": [{"k": k, "estimate": coverage_at_k(len(samples), verified, k)} for k in range(1, 5)],
                           "first_verified_sample_index": first, "billed_provider_cost_microusd": 0,
                           "fixture_scope": "Native-rescored sampling mechanics; candidates declared directly, no model draws."},
                  {"duplicates_checked_once": len(cache) == 3 and len(samples) == 4,
                   "first_verified_stop_is_index_two": first == 2,
                   "all_unverified_coverage_zero": coverage_at_k(4, 0, 2) == "0",
                   "full_sample_coverage_one": coverage_at_k(4, verified, 4) == "1"},
                  ["120 cases from the three specified certificate families", "Best-of-N, iterative and hybrid actual model draws",
                   "Provider accounting at three budget points and independent judge rescoring"])


def terminal_views(packet: dict, cemetery: list[dict], view: str = "all") -> str:
    """Navigate actual bound packet and refused-turn bytes, without fake Hodge bars."""
    if packet.get("payload_sha256") != sha(canonical(packet.get("payload"))):
        raise MechanismError("PACKET_PAYLOAD_DIGEST_MISMATCH")
    previous = sha(b"paper011-cemetery-genesis")
    lines = ["PACKET INSPECTOR", "task: " + packet["task_id"], "payload sha256: " + packet["payload_sha256"],
             "protected: " + ", ".join(packet["protected_edges"]), "payload: " + canonical(packet["payload"]).decode(),
             "HODGE VIEW: unavailable (no declared native decomposition port)", "CEMETERY DAG"]
    for entry in cemetery:
        body = {key: value for key, value in entry.items() if key != "entry_sha256"}
        if entry.get("prev_sha256") != previous or entry.get("entry_sha256") != sha(canonical(body)):
            raise MechanismError("CEMETERY_CHAIN_MISMATCH")
        lines.append(str(entry["turn"]) + " " + entry["refusal"] + " raw=" + entry["raw_output"])
        previous = entry["entry_sha256"]
    if view not in {"all", "packet", "hodge", "cemetery"}:
        raise MechanismError("UNKNOWN_TERMINAL_VIEW")
    if view == "packet":
        lines = lines[:5]
    elif view == "hodge":
        lines = lines[5:6]
    elif view == "cemetery":
        lines = lines[6:]
    return "\n".join(lines)


def symbol_tui() -> dict:
    packet = {"task_id": "paper011-triangle", "protected_edges": ["AB", "BC"],
              "payload": {"AB": "1", "BC": "1", "CA": "1"}}
    packet["payload_sha256"] = sha(canonical(packet["payload"]))
    body = {"turn": 1, "refusal": "PROTECTED_EDGE_EDIT", "raw_output": '{"AB":"9"}',
            "prev_sha256": sha(b"paper011-cemetery-genesis")}
    entry = {**body, "entry_sha256": sha(canonical(body))}
    display = terminal_views(packet, [entry])
    corrupt = dict(entry, raw_output="discarded")
    refused = False
    try:
        terminal_views(packet, [corrupt])
    except MechanismError:
        refused = True
    return record("demo_symbol_tui", {"packet": packet, "cemetery": [entry], "rendered_terminal": display,
                                      "display_scope": "Executable packet and hash-chain renderer; Hodge component remains unavailable."},
                  {"packet_data_rendered": packet["payload_sha256"] in display,
                   "raw_refused_turn_preserved": body["raw_output"] in display,
                   "corrupt_cemetery_refused": refused,
                   "no_fabricated_hodge_decomposition": "HODGE VIEW: unavailable" in display},
                  ["Native Hodge decomposition and evidence-bound component visualization", "Full canonical interactive terminal integration"])


def recreate_all(repository: Path, binding: dict, host: Native, phi: Native) -> list[dict]:
    verify_sources(repository, binding)
    rows = [c001(), c002(), c003(), c004(host), c005(repository, binding, phi), c006(host, phi),
            c007(), c008(), c009(), c010(phi), symbol_tui()]
    rows.append({"schema_version": SCHEMA, "id": "demo_mub6_regge", "grade": "UNRESOLVED_POSITIVE_OBLIGATION",
                 "empirical_result": False, "challenge_gate_satisfied": False,
                 "unperformed_obligations": ["Declared MUB(6) primal-dual constraint system and native certificate port",
                                              "Declared four-simplex geometry and native Regge deficit/Bianchi certificate"],
                 "reason": "Retained README describes results without inputs or a certifier; a zero constant or unrelated LP cannot recreate them."})
    for row in rows:
        row["source_bindings_sha256"] = sha(canonical(binding))
    verify_sources(repository, binding)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source-bindings", type=Path, required=True)
    parser.add_argument("--engine-capability", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--capture-sources", action="store_true")
    parser.add_argument("--terminal-view", choices=["all", "packet", "hodge", "cemetery"])
    args = parser.parse_args()
    if args.capture_sources:
        if args.source_bindings.exists():
            raise MechanismError("EXISTING_SOURCE_BINDING_NOT_REPINNED")
        args.source_bindings.parent.mkdir(parents=True, exist_ok=True)
        args.source_bindings.write_bytes(canonical(capture_sources(args.repository)) + b"\n")
    binding = load(args.source_bindings.read_bytes())
    capability = load(args.engine_capability.read_bytes())
    native = capability["binaries"]["symbol_game"]
    functional = capability["binaries"]["graph_functional"]
    rows = recreate_all(args.repository, binding, Native(Path(native["path"]), native["sha256"]),
                        Native(Path(functional["path"]), functional["sha256"], True))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for row in rows:
        (args.output_dir / (row["id"] + ".json")).write_bytes(canonical(row) + b"\n")
    summary = {"schema_version": "paper011.mechanism-run-summary.v1", "ids": [row["id"] for row in rows],
               "fresh_mechanism_fixtures": sum(row["grade"] == "FRESH_OFFLINE_MECHANISM_FIXTURE" for row in rows),
               "empirical_challenge_gates_satisfied": 0, "source_bindings_sha256": sha(canonical(binding)),
               "runtime": {"python": sys.version, "torch": version("torch"), "device": "cpu"},
               "receipts": {row["id"] + ".json": sha((args.output_dir / (row["id"] + ".json")).read_bytes()) for row in rows}}
    (args.output_dir / "summary.json").write_bytes(canonical(summary) + b"\n")
    print(json.dumps({key: value for key, value in summary.items() if key not in {"runtime", "receipts"}}))
    if args.terminal_view:
        tui = next(row for row in rows if row["id"] == "demo_symbol_tui")["mechanism"]
        print(terminal_views(tui["packet"], tui["cemetery"], args.terminal_view))


if __name__ == "__main__":
    main()
