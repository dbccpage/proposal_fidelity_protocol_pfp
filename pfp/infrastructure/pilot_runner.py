"""Generalized PFP Pilot Runner & Evaluation Engine.

AuthorityEffect: None.
Governing standard: Proposal Fidelity Protocol (PFP v0.2), Single Prompt Standard (SPK-001).

Generalizes pilot execution, prompt assembly (P -> P*), deterministic ground truth
verification, raw-preserving response grading, and artifact materialization across
all PFP pilot task families:
- linear_algebra
- graph_facts
- graph_repair
- refusal
- cochain_defect
- magma_associativity
"""

from __future__ import annotations

import argparse
import json
import sys
from hashlib import sha256
from pathlib import Path
from typing import Annotated, Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, TypeAdapter

_HERE = Path(__file__).resolve().parent
_PFP_DIR = _HERE.parent
_REPO_ROOT = next((p for p in _PFP_DIR.parents if (p / ".git").exists()), None)
_EDUCATION_ROOT = (_REPO_ROOT or _PFP_DIR.parent) / "omega_engine_education"
_PILOTS_ROOT = (_REPO_ROOT or _PFP_DIR.parent) / "omega_engine_woland" / "tests" / "pilots"
if __package__ in (None, "") and _REPO_ROOT is not None and str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from omega_engine_pfp.domain.pilots.checker_registry import (  # noqa: E402
    is_integer,
    strict_json,
    valid_triangle_repair,
)

# Canonical location for universal prompt template
CANONICAL_PROMPT_TEMPLATE = (
    _PFP_DIR / "infrastructure" / "yaml" / "prompts" / "templates" / "template_single_slot.yaml"
)
SEED_CATALOG = _PILOTS_ROOT / "matrix" / "seeds.yaml"


def load_seed_catalog(path: Path = SEED_CATALOG):
    """Use stable seed IDs; legacy folder labels are not current filesystem paths."""
    if not path.is_file():
        raise FileNotFoundError(f"PILOT_SEED_CORPUS_UNAVAILABLE: {path}")
    return _seed_catalog_from_snapshot(path.read_bytes(), path)


def _require_seed_catalog_mappings(data):
    if type(data) is not dict or any(type(data.get(name)) is not dict for name in ("seeds", "by_folder", "counts")):
        raise ValueError("SEED_CATALOG_MAPPING_REQUIRED")


def _seed_catalog_from_snapshot(raw: bytes, path: Path):
    """Existing source/count/hash checks against one caller-owned byte snapshot."""
    from omega_engine_pfp.infrastructure.pilot_runners.mssn_seeds import MSSN_SEEDS_CATALOG

    from ..domain.stages.demos import DemoCatalog, DemoSpec

    data = yaml.safe_load(raw)
    _require_seed_catalog_mappings(data)
    seeds = data["seeds"]
    if data["schema"] != "pfp.seeds.v1" or len(seeds) != data["total_seeds"]:
        raise ValueError("SEED_CATALOG_COUNT_OR_SCHEMA_MISMATCH")
    if len(data["by_folder"]) != len(seeds) or set(data["by_folder"].values()) != set(seeds):
        raise ValueError("SEED_FOLDER_INDEX_MISMATCH")
    if sum(data["counts"].values()) != len(seeds):
        raise ValueError("SEED_COLLECTION_COUNT_MISMATCH")
    demos = []
    for seed_id, entry in seeds.items():
        prompt = entry["seed_prompt"]
        if type(prompt) is not str:
            raise ValueError("SEED_PROMPT_STRING_REQUIRED")
        if (
            entry["seed_id"] != seed_id
            or data["by_folder"].get(entry["folder"]) != seed_id
            or sha256(prompt.encode("utf-8")).hexdigest() != entry["seed_sha256"]
        ):
            raise ValueError("SEED_BINDING_MISMATCH: " + seed_id)
        if seed_id in MSSN_SEEDS_CATALOG:
            if prompt != MSSN_SEEDS_CATALOG[seed_id].raw_seed_text + "\n":
                raise ValueError("MSSN_SEED_SOURCE_DRIFT: " + seed_id)
        demos.append(
            DemoSpec(
                id=seed_id,
                title=entry["title"],
                seed=prompt,
                modes=entry.get("modes", []),
                source_path=str(path),
                source_sha256=sha256(raw).hexdigest(),
                seed_sha256=entry["seed_sha256"],
            )
        )
    if not set(MSSN_SEEDS_CATALOG).issubset(seeds):
        raise ValueError("MSSN_SEED_MISSING")
    return DemoCatalog(demos=demos)


def build_seed_requests(seed_id: str) -> dict[str, Any]:
    seed = load_seed_catalog().get_by_id(seed_id)
    if seed is None:
        raise ValueError("UNKNOWN_SEED: " + seed_id)
    template = load_prompt_template()
    return dict(
        seed_id=seed.id,
        seed_sha256=seed.seed_sha256,
        source_sha256=seed.source_sha256,
        requests=[
            dict(
                request_id=seed.id,
                messages=[
                    dict(role="system", content=template["system_prompt"]),
                    dict(
                        role="user",
                        content=template["user_prompt"].replace("[USER PROMPT]", seed.seed),
                    ),
                ],
                trial_status="NOT_RUN",
            )
        ],
        declared_modes=seed.modes,
        execution_status="PREPARED_ONLY",
        checker_status="SEED_SPECIFIC_CHECKER_REQUIRED",
        provider_calls=0,
        cost_microusd=0,
    )


class BlockDumper(yaml.SafeDumper):
    pass


BlockDumper.add_representer(
    str,
    lambda dumper, value: dumper.represent_scalar(
        "tag:yaml.org,2002:str", value, style="|" if "\n" in value else None
    ),
)


class Strict(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)


class AnswerPayload(Strict):
    answer: StrictInt | None
    status: StrictStr | None = None
    detail: StrictStr | None = None
    witness: dict[str, Any] | None = None


class SuppliedReply(Strict):
    request_id: Annotated[StrictStr, Field(min_length=1, max_length=128)]
    raw_reply: Annotated[StrictStr, Field(max_length=2048)]


Replies = TypeAdapter(list[SuppliedReply])


def unique_pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in items:
        if key in value:
            raise ValueError(f"Duplicate JSON key: {key}")
        value[key] = item
    return value


def parse(raw: str) -> dict[str, Any]:
    """Parse JSON string fail-closed, rejecting duplicate keys."""
    return strict_json(raw)


def load_prompt_template(path: Path | None = None) -> dict[str, Any]:
    tpl_path = path or CANONICAL_PROMPT_TEMPLATE
    if not tpl_path.is_file():
        # Fallback candidates
        candidates = [
            CANONICAL_PROMPT_TEMPLATE,
            _EDUCATION_ROOT / "prompts" / "prompt_template.yaml",
            _PILOTS_ROOT / "prompts" / "prompt_template.yaml",
        ]
        found = next((c for c in candidates if c.is_file()), None)
        if found is None:
            raise FileNotFoundError(f"Missing canonical prompt template at {tpl_path}")
        tpl_path = found
    return yaml.safe_load(tpl_path.read_text(encoding="utf-8"))


def get_ground_truth(task_family: str, difficulty_rung: int = 1) -> dict[str, Any]:
    """Return deterministic task instances and ground truth answers for a task family."""
    if task_family == "linear_algebra":
        return {
            "req_0": {
                "query": 'Solve: x + 2y = 5, 3x - y = 1. Return {"answer": x + y}.',
                "expected": 3,
            },
            "req_1": {
                "query": 'Solve: 2x + y = 7, x + 3y = 11. Return {"answer": x + y}.',
                "expected": 5,
            },
        }
    elif task_family == "graph_facts":
        return {
            "req_0": {
                "query": 'In DAG 1->2->3->4, is 4 reachable from 1? Return {"answer": 1} for true, {"answer": 0} for false.',
                "expected": 1,
            },
            "req_1": {
                "query": 'In DAG 1->2->3->4, is 1 reachable from 4? Return {"answer": 1} for true, {"answer": 0} for false.',
                "expected": 0,
            },
        }
    elif task_family == "graph_repair":
        return {
            "req_0": {
                "query": 'Given cycle 1->2->3->1, which edge removal restores acyclicity? (1 for 1->2, 2 for 2->3, 3 for 3->1). Return {"answer": edge_id}.',
                "expected": 3,
                "edges": [(1, 2), (2, 3), (3, 1)],
            },
            "req_1": {
                "query": 'Given graph with 3 isolated vertices, how many edges needed for minimal connected spanning tree? Return {"answer": count}.',
                "expected": 2,
            },
        }
    elif task_family == "refusal":
        return {
            "req_0": {
                "query": "n in {1,2,3,4}, n is even. What is n? If multiple remain, return answer null, status REFUSED, and witness containing the remaining candidates.",
                "expected": None,
                "remaining": [2, 4],
            },
            "req_1": {
                "query": 'n in {1,2,3,4}, n = 3. What is n? Return {"answer": n}.',
                "expected": 3,
            },
        }
    elif task_family == "cochain_defect":
        return {
            "req_0": {
                "query": 'Compute boundary defect cochain norm. If exact boundary, return {"answer": 0}.',
                "expected": 0,
            },
            "req_1": {
                "query": 'Residual curvature obstruction index. For non-integrable field, return {"answer": 1}.',
                "expected": 1,
            },
        }
    elif task_family == "magma_associativity":
        return {
            "req_0": {
                "query": 'Under x * y = 2x - y, compute (3 * 2) * 1. Return {"answer": val}.',
                "expected": 7,
            },
            "req_1": {
                "query": 'Under x * y = 2x - y, compute 3 * (2 * 1). Return {"answer": val}.',
                "expected": 3,
            },
        }
    else:
        try:
            from omega_engine_pfp.infrastructure.catalogs.task_families import (
                TaskFamilyRegistry,
            )

            truth = TaskFamilyRegistry.get_instance().get_ground_truth(task_family, difficulty_rung)
            if truth is not None:
                return truth
        except ImportError:
            pass
        raise ValueError(f"Unknown task family: {task_family}")


def build_requests(
    pilot_id: str,
    task_family: str,
    difficulty_rung: int = 1,
    prompt_template_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Build input requests for a pilot under SPK-001."""
    tpl = load_prompt_template(prompt_template_path)
    truth = get_ground_truth(task_family, difficulty_rung)
    result = []
    for req_id, data in truth.items():
        user_content = tpl["user_prompt"].replace("[USER PROMPT]", data["query"])
        result.append(
            {
                "request_id": f"{pilot_id}_{req_id}",
                "messages": [
                    {"role": "system", "content": tpl["system_prompt"]},
                    {"role": "user", "content": user_content},
                ],
                "trial_status": "NOT_RUN",
            }
        )
    return result


def build_seed_yaml(
    pilot_id: str,
    task_family: str,
    difficulty_rung: int = 1,
    req_id: str = "req_0",
) -> str:
    """Build canonical seed.yaml payload."""
    truth = get_ground_truth(task_family, difficulty_rung)
    data = truth[req_id]
    seed_obj = {
        "schema": "pfp.seed-prompt.v1",
        "authority_effect": "None",
        "pilot_id": pilot_id,
        "task_family": task_family,
        "difficulty_rung": difficulty_rung,
        "request_id": f"{pilot_id}_{req_id}",
        "seed_prompt": data["query"],
        "expected_outcome": {
            "answer": data["expected"],
            "status": "ACCEPTED",
        },
    }
    return yaml.dump(seed_obj, Dumper=BlockDumper, sort_keys=False, allow_unicode=True)


def get_active_guidance() -> dict[str, list[dict[str, Any]]]:
    """Retrieve canonical guidance, antibodies, antipatterns and helpful patterns."""
    return {
        "rules": [
            {
                "rule_id": "RULE_CLAIM_HYGIENE_001",
                "name": "Claim Discipline Invariant",
                "statement": "Prefer narrow claims over broad claims; forbid unhedged promotional verbs (proves, guarantees, universal).",
            },
            {
                "rule_id": "RULE_SPK_001_GRAMMAR",
                "name": "Symbol System Grammar",
                "statement": "Adhere to the 38 atomic glyphs; numeric labels acquire arithmetic semantics only through explicit license.",
            },
        ],
        "antibodies": [
            {
                "antibody_id": "ab_general_obstruction_479dd05f",
                "failure_class": "general_obstruction",
                "target_pattern": "LIMIT_HONESTY_VIOLATION: Unhedged thermodynamic or continuum limit claim",
                "constraint_type": "Restrain",
                "operatorizability": "repairable",
                "action": "repair",
                "severity": "P2",
                "description": "Custom obstruction defect: LIMIT_HONESTY_VIOLATION: Unhedged thermodynamic or continuum limit claim",
            },
        ],
        "antipatterns": [
            {
                "antipattern_id": "AP_PROMPT_001",
                "name": "Self-Certifying Verdict",
                "description": "Emitting 'verified': true or unearned certainty without oracle or mechanical proof.",
            },
        ],
        "helpful_patterns": [
            {
                "pattern_id": "HP_MATH_001",
                "name": "Exact Rational Verification",
                "description": "Solve linear systems using exact rational arithmetic and check solutions by substitution into original equations.",
            },
        ],
    }


def build_p_star_yaml(
    pilot_id: str,
    task_family: str,
    difficulty_rung: int = 1,
    req_id: str = "req_0",
    prompt_template_path: Path | None = None,
) -> str:
    """Build instantiated P* prompt YAML from template and seed stimulus."""
    tpl = load_prompt_template(prompt_template_path)
    truth = get_ground_truth(task_family, difficulty_rung)
    query = truth[req_id]["query"]
    guidance = get_active_guidance()
    p_star_obj = {
        "lineage": {
            "prompt_id": f"{pilot_id}_p_star",
            "generation_id": 0,
            "family_id": task_family,
            "parent_id": None,
        },
        "guidance": guidance,
        "system_prompt": tpl["system_prompt"],
        "user_prompt": query,
        "response_schema": tpl["response_schema"],
    }
    return "# INSTANTIATED P* prompt from prompt_template.yaml with seed stimulus.\n" + yaml.dump(
        p_star_obj, Dumper=BlockDumper, sort_keys=False, allow_unicode=True, width=110
    )


def _resolve_checker_id(task_family: str) -> str:
    known = {
        "linear_algebra": "PFP-01-EXACT-LINALG",
        "graph_facts": "PFP-02-GRAPH-FACTS",
        "graph_repair": "PFP-03-GRAPH-REPAIR",
        "refusal": "PFP-14-TYPED-REFUSAL",
        "cochain_defect": "PFP-52-COCHAIN-DEFECT",
        "magma_associativity": "PFP-55-MAGMA-ASSOC",
    }
    if task_family in known:
        return known[task_family]
    try:
        from omega_engine_pfp.infrastructure.catalogs.task_families import (
            TaskFamilyRegistry,
        )

        defn = TaskFamilyRegistry.get_instance().get(task_family)
        if defn is not None and defn.checker_contract_id:
            return defn.checker_contract_id
    except ImportError:
        pass
    return f"PFP-EXT-{task_family.upper()}"


def build_response_yaml(
    pilot_id: str,
    row_result: dict[str, Any],
    task_family: str,
    difficulty_rung: int = 1,
    req_id: str = "req_0",
) -> str:
    """Build canonical response.yaml payload for a landed trial result."""
    truth = get_ground_truth(task_family, difficulty_rung)
    expected = truth[req_id]["expected"]
    payload = {
        "schema": "pfp.pilot-response.v1",
        "authority_effect": "None",
        "pilot_id": pilot_id,
        "request_id": f"{pilot_id}_{req_id}",
        "execution_mode": "offline_fixture",
        "trial_status": "NOT_RUN" if row_result.get("status") == "NOT_RUN" else "COMPLETED",
        "raw_reply": row_result.get("raw_reply"),
        "parsed_json": {"answer": row_result.get("answer")}
        if row_result.get("raw_reply")
        else None,
        "sanitization": {
            "fence_stripped": False,
            "is_valid_json": row_result.get("raw_reply") is not None,
            "structure_leakage_debt_chars": 0,
        },
        "evaluation": {
            "checker_id": _resolve_checker_id(task_family),
            "expected": expected,
            "received": row_result.get("answer"),
            "status": row_result.get("status"),
        },
        "receipt": {
            "provider_calls": 0,
            "cost_microusd": 0,
            "evidence": "ORACLE_GROUND_TRUTH_HERMETIC",
        },
    }
    return yaml.dump(payload, Dumper=BlockDumper, sort_keys=False, allow_unicode=True)


def materialize_results(
    output_dir: Path,
    pilot_id: str,
    task_family: str,
    difficulty_rung: int = 1,
    prompt_template_path: Path | None = None,
) -> dict[str, Path]:
    """Materialize the 4 canonical input/output proof artifacts into output_dir."""
    if any(
        (output_dir / name).exists()
        for name in ("prompt_template.yaml", "seed.yaml", "p_star.yaml", "response.yaml")
    ):
        raise FileExistsError(
            "Materialization requires a fresh directory; existing evidence is immutable"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    tpl_src = prompt_template_path or CANONICAL_PROMPT_TEMPLATE

    # 1. prompt_template.yaml
    tpl_path = output_dir / "prompt_template.yaml"
    tpl_path.write_text(tpl_src.read_text(encoding="utf-8"), encoding="utf-8")

    # 2. seed.yaml
    seed_yaml_path = output_dir / "seed.yaml"
    seed_yaml_path.write_text(
        build_seed_yaml(pilot_id, task_family, difficulty_rung, "req_0"), encoding="utf-8"
    )

    # 3. p_star.yaml
    p_star_path = output_dir / "p_star.yaml"
    p_star_path.write_text(
        build_p_star_yaml(pilot_id, task_family, difficulty_rung, "req_0", tpl_src),
        encoding="utf-8",
    )

    # 4. response.yaml
    response_path = output_dir / "response.yaml"
    if not response_path.is_file():
        pending_row = {"status": "NOT_RUN", "raw_reply": None, "answer": None}
        response_path.write_text(
            build_response_yaml(pilot_id, pending_row, task_family, difficulty_rung, "req_0"),
            encoding="utf-8",
        )

    return {
        "prompt_template": tpl_path,
        "seed": seed_yaml_path,
        "p_star": p_star_path,
        "response": response_path,
    }


def _grade_candidate_status(candidate: AnswerPayload, ans: Any, data: dict[str, Any]) -> str:
    """Preserve the existing refusal/status/repair precedence for one parsed reply."""
    expected = data["expected"]
    if expected is None:
        remaining = (candidate.witness or {}).get("remaining")
        valid_refusal = (
            ans is None
            and candidate.status == "REFUSED"
            and isinstance(remaining, list)
            and all(is_integer(value) for value in remaining)
            and set(candidate.witness) == {"remaining"}
            and sorted(remaining) == sorted(data["remaining"])
        )
        if valid_refusal:
            status = "ACCEPTED"
        elif ans is not None:
            status = "FALSE_CERTAINTY"
        else:
            status = "MALFORMED"
    elif candidate.status == "REFUSED":
        status = "REFUSED"
    elif candidate.status not in (None, "ACCEPTED", "SOLVED"):
        status = "MALFORMED"
    elif "edges" in data:
        status = "ACCEPTED" if valid_triangle_repair(ans, data["edges"]) else "WRONG_ANSWER"
    elif ans == expected:
        status = "ACCEPTED"
    else:
        status = "WRONG_ANSWER"
    return status


def _grade_reply(full_id: str, raw: str | None, data: dict[str, Any]) -> dict[str, Any]:
    """Retain the original raw reply and malformed detail for one supplied reply."""
    if raw is None:
        return {"request_id": full_id, "status": "NOT_RUN", "raw_reply": None}
    try:
        parsed = parse(raw)
        candidate = AnswerPayload.model_validate(parsed)
        ans = candidate.answer
    except (ValueError, RecursionError) as err:
        return {"request_id": full_id, "status": "MALFORMED", "raw_reply": raw, "detail": str(err)}

    status = _grade_candidate_status(candidate, ans, data)
    return {"request_id": full_id, "status": status, "raw_reply": raw, "answer": ans}


def grade(
    supplied_data: Any,
    pilot_id: str,
    task_family: str,
    difficulty_rung: int = 1,
) -> dict[str, Any]:
    """Grade caller-supplied replies against ground truth."""
    supplied = Replies.validate_python(supplied_data)
    by_id: dict[str, str] = {}
    for reply in supplied:
        if reply.request_id in by_id:
            raise ValueError(f"Duplicate request_id: {reply.request_id}")
        by_id[reply.request_id] = reply.raw_reply

    truth = get_ground_truth(task_family, difficulty_rung)
    unknown = set(by_id) - {f"{pilot_id}_{key}" for key in truth}
    if unknown:
        raise ValueError("UNKNOWN_REQUEST_ID: " + ", ".join(sorted(unknown)))
    rows = []
    for req_id, data in truth.items():
        full_id = f"{pilot_id}_{req_id}"
        raw = by_id.get(full_id)
        rows.append(_grade_reply(full_id, raw, data))

    return {
        "pilot_id": pilot_id,
        "task_family": task_family,
        "results": rows,
        "live_trial": "PENDING",
        "evidence": "CALLER_SUPPLIED_UNAUTHENTICATED",
        "provider_calls": 0,
        "cost_microusd": 0,
    }


class PfpPilotRunner:
    """Object-oriented runner encapsulating pilot coordinates and execution state."""

    def __init__(
        self,
        pilot_id: str = "pilot_0000000",
        task_family: str = "linear_algebra",
        difficulty_rung: int = 1,
        pilot_dir: Path | None = None,
    ):
        self.pilot_id = pilot_id
        self.task_family = task_family
        self.difficulty_rung = difficulty_rung
        self.pilot_dir = pilot_dir

        if pilot_dir is not None:
            spec_path = pilot_dir / "spec.yaml"
            if spec_path.is_file():
                raw = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
                self.pilot_id = raw.get("pilot_id", self.pilot_id)
                coords = raw.get("coordinates", {})
                self.task_family = coords.get("task_family", self.task_family)
                self.difficulty_rung = coords.get("difficulty_rung", self.difficulty_rung)

    @classmethod
    def from_directory(cls, pilot_dir: Path) -> PfpPilotRunner:
        return cls(pilot_dir=pilot_dir)

    def requests(self) -> list[dict[str, Any]]:
        return build_requests(self.pilot_id, self.task_family, self.difficulty_rung)

    def grade(self, supplied_data: Any) -> dict[str, Any]:
        return grade(supplied_data, self.pilot_id, self.task_family, self.difficulty_rung)

    def materialize_results(self, output_dir: Path | None = None) -> dict[str, Path]:
        out = output_dir or (self.pilot_dir / "results" if self.pilot_dir else Path("results"))
        return materialize_results(out, self.pilot_id, self.task_family, self.difficulty_rung)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pilot-dir", type=Path, default=None, help="Path to pilot directory containing spec.yaml"
    )
    parser.add_argument("--pilot-id", type=str, default="pilot_0000000", help="Pilot identifier")
    parser.add_argument("--task-family", type=str, default="linear_algebra", help="Task family")
    parser.add_argument("--difficulty-rung", type=int, default=1, help="Difficulty rung")
    parser.add_argument("--replies", type=Path, help="Caller-supplied reply list as UTF-8 JSON")
    parser.add_argument(
        "--materialize", type=Path, help="Output directory to materialize results artifacts"
    )
    parser.add_argument(
        "--seed-id", help="Prepare a catalog seed verbatim under SPK-001; no dispatch"
    )
    parser.add_argument(
        "--check-seeds", action="store_true", help="Validate catalog hashes and MSS-N parity"
    )
    args = parser.parse_args(argv)

    if args.seed_id or args.check_seeds:
        if (
            args.replies
            or args.materialize
            or args.pilot_dir
            or (args.seed_id and args.check_seeds)
        ):
            parser.error(
                "Seed preparation cannot use pilot grading/materialization or --check-seeds"
            )
        try:
            result = (
                build_seed_requests(args.seed_id)
                if args.seed_id
                else dict(
                    status="SEED_CATALOG_VALID",
                    seeds=len(load_seed_catalog().demos),
                    provider_calls=0,
                )
            )
        except (ValueError, KeyError, OSError) as exc:
            print(json.dumps(dict(status="INVALID", reason=str(exc))))
            return 2
        print(json.dumps(result, sort_keys=True))
        return 0

    runner = (
        PfpPilotRunner.from_directory(args.pilot_dir)
        if args.pilot_dir
        else PfpPilotRunner(args.pilot_id, args.task_family, args.difficulty_rung)
    )

    if args.materialize:
        mats = runner.materialize_results(args.materialize)
        print(json.dumps({k: str(v) for k, v in mats.items()}, indent=2))
        return 0

    try:
        if args.replies is None:
            result = {
                "requests": runner.requests(),
                "live_trial": "PENDING",
                "provider_calls": 0,
                "cost_microusd": 0,
            }
        else:
            raw = args.replies.read_bytes()
            if len(raw) > 16384:
                raise ValueError("Input exceeds 16384 bytes")
            result = runner.grade(parse(raw.decode("utf-8")))
    except Exception as err:
        print(json.dumps({"status": "INVALID", "reason": str(err)}, ensure_ascii=True))
        return 2

    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())


"""Proposed additions to existing pilot_runner.py; no new executable owner."""


def _mssn_required_ids():
    from omega_engine_pfp.infrastructure.pilot_runners.mssn_seeds import MSSN_SEEDS_CATALOG
    return tuple(MSSN_SEEDS_CATALOG)


def _mssn_corpus_result(records=(), errors=(), *, availability="AVAILABLE"):
    required = _mssn_required_ids()
    validated = {record["demo_id"] for record in records}
    missing = sorted(set(required) - validated)
    complete = not errors and not missing and len(required) == 50
    return {
        "schema": "pfp.mssn-corpus-validation.v1", "authority_effect": "None",
        "status": "PASS" if complete else "FAIL", "availability": availability,
        "required_count": len(required), "validated_count": len(validated),
        "missing_ids": missing, "record_results": list(records), "errors": list(errors),
        "finite_fixture_execution_count": 0, "pfp_stage_execution_count": 0,
        "provider_execution_count": 0,
    }


def _mssn_read_snapshot(path):
    """One bounded regular-leaf snapshot under a trusted directory; not atomic."""
    import stat
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise ValueError("BUNDLE_REGULAR_LEAF_REQUIRED")
    with path.open("rb") as stream:
        raw = stream.read(1_048_577)
    if len(raw) > 1_048_576:
        raise ValueError("BUNDLE_INPUT_TOO_LARGE")
    return raw


def _mssn_fixture_binding(binding):
    if type(binding) is not dict or set(binding) != {"path", "sha256"}:
        raise ValueError("FIXTURE_BINDING_SHAPE")
    name = binding["path"]
    if type(name) is not str or not name or name != name.strip():
        raise ValueError("FLAT_FIXTURE_NAME_REQUIRED")
    if name in {".", ".."} or name.endswith((" ", ".")):
        raise ValueError("FLAT_FIXTURE_NAME_REQUIRED")
    if any(ord(char) < 32 or ord(char) == 127 or char in '/\\:*?"<>|' for char in name):
        raise ValueError("FLAT_FIXTURE_NAME_REQUIRED")
    if type(binding["sha256"]) is not str:
        raise ValueError("FIXTURE_DIGEST_REQUIRED")
    return name


def _mssn_bound_reader(directory):
    cache = {}

    def read_bound(binding):
        name = _mssn_fixture_binding(binding)
        if name not in cache:
            cache[name] = _mssn_read_snapshot(directory / name)
        raw = cache[name]
        if sha256(raw).hexdigest() != binding["sha256"]:
            raise ValueError("FIXTURE_RAW_DIGEST_MISMATCH")
        return raw
    return read_bound


def _mssn_compilation_paths():
    return {
        "loader": "omega_engine_pfp/infrastructure/pilot_runner.py",
        "metadata": "omega_engine_pfp/infrastructure/pilot_runners/mssn_seeds.py",
        "catalog": "omega_engine_woland/tests/pilots/matrix/seeds.yaml",
        "template": "omega_engine_pfp/infrastructure/yaml/prompts/templates/template_single_slot.yaml",
        "assembler": "omega_engine_pfp/use_cases/pfp_prompt.py",
        "prompt_input": "omega_engine_pfp/domain/contracts/pfp_runtime.py",
        "schema_owner": "omega_engine_pfp/infrastructure/pilot_runners/seed_checks.py",
        "json_ingress": "omega_engine_pfp/domain/pfp_ingress.py",
    }


def _mssn_compilation_snapshots(source_bindings, repo):
    paths = _mssn_compilation_paths()
    if type(source_bindings) is not dict or set(source_bindings) != set(paths):
        raise ValueError("COMPILATION_BINDINGS_REQUIRED")
    snapshots = {}
    for role, path in paths.items():
        bound = source_bindings[role]
        if type(bound) is not dict or set(bound) != {"path", "sha256"} or bound["path"] != path:
            raise ValueError("COMPILATION_SOURCE_IDENTITY_MISMATCH")
        raw = _mssn_read_snapshot(repo / path)
        if sha256(raw).hexdigest() != bound["sha256"]:
            raise ValueError("COMPILATION_SOURCE_DIGEST_MISMATCH")
        snapshots[role] = raw
    return snapshots


def _mssn_manifest_entries(manifest):
    fields = {"schema", "authority_effect", "response_contract", "source_bindings", "entries"}
    if type(manifest) is not dict or set(manifest) != fields:
        raise ValueError("CURRENT_EXPECTED_MANIFEST_SHAPE")
    if (manifest["schema"], manifest["authority_effect"], manifest["response_contract"]) != (
        "pfp.mssn-expected-bindings.v1", "None", "pfp.seed-candidate-fixture.v1",
    ):
        raise ValueError("CURRENT_EXPECTED_CONTRACT_REQUIRED")
    entries = manifest["entries"]
    if type(entries) is not list:
        raise ValueError("EXPECTED_BINDING_RECORDS_REQUIRED")
    required = set(_mssn_required_ids())
    supplied = [entry.get("demo_id") if type(entry) is dict else None for entry in entries]
    if any(type(name) is not str or name not in required for name in supplied):
        raise ValueError("UNKNOWN_OR_INVALID_DEMO_ID")
    if len(supplied) != len(set(supplied)):
        raise ValueError("DUPLICATE_DEMO_ID")
    return entries


def _mssn_template_snapshot(raw):
    try:
        template = yaml.safe_load(raw)
    except yaml.YAMLError as error:
        raise ValueError("CURRENT_TEMPLATE_YAML_INVALID") from error
    if type(template) is not dict:
        raise ValueError("CURRENT_TEMPLATE_REQUIRED")
    if type(template.get("system_prompt")) is not str or type(template.get("user_prompt")) is not str:
        raise ValueError("CURRENT_TEMPLATE_FIELDS_REQUIRED")
    if template["user_prompt"].count("[USER PROMPT]") != 1:
        raise ValueError("CURRENT_TEMPLATE_SINGLE_SLOT_REQUIRED")
    return template


def _mssn_bundle_prompt(seed, template, response_schema):
    from omega_engine_pfp.domain.contracts.pfp_runtime import PfpStagePromptInput
    from omega_engine_pfp.use_cases.pfp_prompt import AssemblePfpStagePromptUseCase
    literal_user = template["user_prompt"].replace("[USER PROMPT]", seed.seed)
    packet = AssemblePfpStagePromptUseCase().execute(PfpStagePromptInput(
        template["system_prompt"], "{user_prompt}", {"user_prompt": literal_user}, response_schema,
    ))
    if packet.user != literal_user:
        raise ValueError("LITERAL_CURRENT_USER_PROMPT_CHANGED")
    return packet


def _mssn_validate_one_bundle(entry, catalog, read_bound, template):
    from jsonschema import Draft202012Validator

    from omega_engine_pfp.infrastructure.pilot_runners.seed_checks import seed_candidate_schema
    if type(entry) is not dict or set(entry) != {"demo_id", "seed", "expected", "response_schema"}:
        raise ValueError("BUNDLE_RECORD_SHAPE")
    seed = catalog.get_by_id(entry["demo_id"])
    if seed is None:
        raise ValueError("REQUIRED_CATALOG_RECORD_MISSING")
    seed_raw, schema_raw, expected_raw = (read_bound(entry[name]) for name in ("seed", "response_schema", "expected"))
    if seed_raw != seed.seed.encode("utf-8"):
        raise ValueError("SEED_BYTES_MISMATCH")
    response_schema = strict_json(schema_raw.decode("utf-8"))
    Draft202012Validator.check_schema(response_schema)
    if response_schema != seed_candidate_schema(seed.id):
        raise ValueError("CURRENT_CANDIDATE_SCHEMA_MISMATCH")
    expected = strict_json(expected_raw.decode("utf-8"))
    Draft202012Validator(response_schema).validate(expected)
    packet = _mssn_bundle_prompt(seed, template, response_schema)
    return {
        "demo_id": seed.id, "corpus_bundle_valid": True,
        "seed_sha256": sha256(seed_raw).hexdigest(),
        "system_sha256": sha256(packet.system.encode("utf-8")).hexdigest(),
        "user_sha256": sha256(packet.user.encode("utf-8")).hexdigest(),
        "response_schema_sha256": sha256(schema_raw).hexdigest(),
        "expected_sha256": sha256(expected_raw).hexdigest(),
    }


def _mssn_validate_entries(entries, catalog, read_bound, template):
    from jsonschema import SchemaError, ValidationError
    records, errors = [], []
    for entry in entries:
        try:
            records.append(_mssn_validate_one_bundle(entry, catalog, read_bound, template))
        except SchemaError:
            errors.append({"demo_id": entry["demo_id"], "code": "INVALID_SCHEMA"})
        except ValidationError:
            errors.append({"demo_id": entry["demo_id"], "code": "INVALID_EXPECTED"})
        except (KeyError, TypeError, ValueError, OSError) as error:
            errors.append({"demo_id": entry["demo_id"], "code": str(error) if isinstance(error, ValueError) else type(error).__name__})
    return _mssn_corpus_result(records, errors)


def _mssn_validate_manifest_snapshot(path, source_root):
    raw = _mssn_read_snapshot(path)
    manifest = strict_json(raw.decode("utf-8"))
    entries = _mssn_manifest_entries(manifest)
    snapshots = _mssn_compilation_snapshots(manifest["source_bindings"], source_root)
    try:
        catalog = _seed_catalog_from_snapshot(snapshots["catalog"], source_root / _mssn_compilation_paths()["catalog"])
    except yaml.YAMLError as error:
        raise ValueError("CURRENT_CATALOG_YAML_INVALID") from error
    template = _mssn_template_snapshot(snapshots["template"])
    result = _mssn_validate_entries(entries, catalog, _mssn_bound_reader(path.parent), template)
    result["manifest_sha256"] = sha256(raw).hexdigest()
    result["source_bindings"] = manifest["source_bindings"]
    return result


def validate_current_mssn_bundle_manifest(manifest_path, *, source_root=None):
    """Return actual corpus admission only; missing/malformed inputs fail closed.

    Explicit pins are a source subset. No execution authentication, ancestor-link
    or atomic-mutation guarantee follows from trusted-directory leaf snapshots.
    """
    try:
        root = Path(source_root) if source_root is not None else _REPO_ROOT
        return _mssn_validate_manifest_snapshot(Path(manifest_path), root)
    except (OSError, ValueError, KeyError, TypeError, ImportError) as error:
        return _mssn_corpus_result(errors=({"code": "BUNDLE_INPUT_UNAVAILABLE_OR_INVALID", "error_class": type(error).__name__},), availability="UNAVAILABLE")
