"""Original task checker: absent homology premises require a typed question."""

from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path

from omega_engine_operations.domain.rop.result import Err
from omega_engine_pfp.use_cases import clarification
from omega_engine_adversary.domain.checked_reuse import BoundReuseChecker
from omega_engine_adversary.use_cases.checked_ddc_reuse import checker_source_digest
from omega_engine_adversary.use_cases.prompt_family_replay import _program_digest

CHECKER_ID = "homological-object-missing-inputs.v1"


def checker_binding():
    here = Path(__file__).resolve().parent
    paths = (Path(__file__).resolve(), Path(clarification.__file__).resolve(),
             here / "contract.json", here / "answer_schema.json")
    return BoundReuseChecker.model_validate_json(json.dumps({"checker_id": CHECKER_ID,
        "sources": [{"path": str(path), "sha256": sha256(path.read_bytes()).hexdigest()} for path in paths]}))


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("DUPLICATE_KEY")
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--seed", required=True)
    parser.add_argument("--premises-json", required=True)
    parser.add_argument("--contract", type=Path, default=Path(__file__).with_name("contract.json"))
    parser.add_argument("--reuse-binding", action="store_true")
    args = parser.parse_args()
    try:
        raw = args.candidate.read_bytes()
        if len(raw) > 65_536:
            raise ValueError("CANDIDATE_TOO_LARGE")
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError("NONFINITE_JSON")))
        contract_raw = args.contract.read_bytes()
        contract = json.loads(contract_raw, object_pairs_hook=unique)
        premises = json.loads(args.premises_json, object_pairs_hook=unique)
        if (set(premises) != {"required_fields", "supplied_fields"}
                or premises["required_fields"] != contract["required_fields"]):
            raise ValueError("PREMISES_CONTRACT_MISMATCH")
        observed = clarification.check_clarification(value, seed=args.seed,
            required_fields=tuple(contract["required_fields"]), supplied_fields=premises["supplied_fields"])
        if isinstance(observed, Err):
            raise ValueError(observed.error.code)
        # This recipe reuses identity-neutral questions only. A source-specific
        # question is not silently relabelled for a different target object.
        if any(name in question["question"].casefold() for question in value["questions"]
               for name in ("potato", "tomato")):
            raise ValueError("QUESTIONS_MUST_BE_TASK_NEUTRAL")
        result = {"checker_id": CHECKER_ID, "accepted": True,
            "outcome": observed.value.outcome, "missing_fields": list(observed.value.missing_fields),
            "candidate_sha256": sha256(raw).hexdigest(),
            "seed_sha256": sha256(args.seed.encode("utf-8")).hexdigest(),
            "premises_sha256": _program_digest(premises),
            "contract_sha256": sha256(contract_raw).hexdigest(),
            "checker_source_sha256": checker_source_digest(checker_binding())}
        if not args.reuse_binding:
            result["mathematical_acceptance"] = "NOT_SOLVED"
            result["questions"] = value["questions"]
        print(json.dumps(result, sort_keys=True))
        return 0
    except (ValueError, KeyError, TypeError, OSError, UnicodeError) as error:
        print(json.dumps({"accepted": False, "outcome": "CHECK_REFUSED", "reason": str(error),
                          "mathematical_acceptance": "NOT_SOLVED"}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
