"""Mine chain-of-thought traces for patterns, rules, skills, antiskills, and antibodies.

AuthorityEffect: None.

Reads landed ``response*.yaml`` files. It does not call a model and it does not
write a prompt. Re-run::

    py -3.12 -m omega_engine_woland.tests.pilots.cot_miner
"""

from __future__ import annotations

import argparse
from importlib.resources import files
import re
from pathlib import Path
from typing import Any

import yaml

from omega_engine_pfp.infrastructure.adapters.pfp_evidence import resource_root

PILOTS = Path(__file__).resolve().parent
RELOCATED_PILOT = resource_root(Path(__file__)) / "omega_engine_pfp" / "tests" / "pilot_0000000"
DEFAULT_RESULTS = (
    RELOCATED_PILOT / "misc"
    if (RELOCATED_PILOT / "misc").is_dir()
    else RELOCATED_PILOT / "results"
)
DEFAULT_SCHEMA = (
    files("omega_engine_pfp").joinpath("infrastructure", "yaml", "pilots", "pilot_response_v1.schema.yaml")
)
UNBOUNDED_REASONING_TOKENS = 1000
HYPOTHESIS_MIN = 6
SCHEMA_MIN = 4
QUOTE_CHARS = 160

CORPUS_TOKENS = ("BigBench", "BBH", "Dyck", "ARC")
PREAMBLE = re.compile(r"we need answer|need parse", re.IGNORECASE)
SUBSTITUTION = re.compile(r"\bSubstitute\b|=>")
CLARIFICATION = re.compile(
    r"what would you like me to do|no explicit question|ask clarification",
    re.IGNORECASE,
)
HYPOTHESIS = re.compile(r"\b(?:Maybe|Could be|Alternatively|Hmm)\b", re.IGNORECASE)
LICENSE_REFUSAL = re.compile(
    r"does not license arithmetic|no licensed arithmetic|not solve arithmetic|without license",
    re.IGNORECASE,
)
ANSWER_CHANNEL = re.compile(
    r"schema doesn't|no field for \"answer\"|answer would be in narrowest|put answer in",
    re.IGNORECASE,
)
FALLBACK_SCHEMA_TERMS = (
    "SPK-001",
    "derived_under_policy",
    "narrowest_defensible_thesis",
    "evidence_scope",
    "next_concrete_test",
    "process_integrity",
    "sections",
)


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data: object) -> bool:
        return True


def _schema_const_strings(node: object) -> set[str]:
    found: set[str] = set()
    if not isinstance(node, dict):
        return found
    const = node.get("const")
    if isinstance(const, str):
        found.add(const)
    enum = node.get("enum")
    if isinstance(enum, list):
        found.update(item for item in enum if isinstance(item, str))
    for key in ("anyOf", "oneOf", "allOf"):
        branch = node.get(key)
        if isinstance(branch, list):
            for item in branch:
                found.update(_schema_const_strings(item))
    return found


def schema_terms(path: Path) -> tuple[str, ...]:
    if not path.is_file():
        return FALLBACK_SCHEMA_TERMS
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    defs = loaded.get("$defs", {}) if isinstance(loaded, dict) else {}
    terms: set[str] = set()
    for name in ("PromptResponsePayload", "ResponseSummaryPayload", "ProcessIntegrityPayload"):
        block = defs.get(name)
        required = block.get("required") if isinstance(block, dict) else None
        if isinstance(required, list):
            terms.update(item for item in required if isinstance(item, str))
    prompt = defs.get("PromptResponsePayload") if isinstance(defs, dict) else None
    properties = prompt.get("properties") if isinstance(prompt, dict) else None
    policy = properties.get("derived_under_policy") if isinstance(properties, dict) else None
    terms.update(_schema_const_strings(policy))
    terms.add("sections")
    return tuple(sorted(terms)) if terms else FALLBACK_SCHEMA_TERMS


def _quote(text: str, pattern: re.Pattern[str]) -> str:
    match = pattern.search(text)
    if match is None:
        return ""
    return " ".join(text[match.start():match.start() + QUOTE_CHARS].split())


def _usage_int(receipt: dict, key: str) -> int:
    usage = receipt.get("usage") if isinstance(receipt, dict) else None
    value = usage.get(key) if isinstance(usage, dict) else None
    if type(value) is int and value >= 0:
        return value
    return 0


def _answers_match(expected: object, received: object) -> bool:
    return type(expected) is type(received) and type(expected) is not float and expected == received


def load_traces(results_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    traces: list[dict[str, Any]] = []
    skipped: list[str] = []
    pilot_dir = results_dir.parent
    response_paths = sorted(results_dir.glob("response*.yaml"))
    tests_dir = pilot_dir / "tests"
    if not response_paths and tests_dir.is_dir():
        for t_dir in sorted(tests_dir.iterdir()):
            if t_dir.is_dir():
                resp_f = t_dir / "response.yaml"
                if resp_f.is_file():
                    response_paths.append(resp_f)

    seen_test_ids: set[str] = set()
    for path in response_paths:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict) or not isinstance(loaded.get("reasoning_content"), str):
            skipped.append(path.name)
            continue
        test_id_str = str(loaded.get("test_id") or path.stem)
        if test_id_str in seen_test_ids:
            continue
        seen_test_ids.add(test_id_str)
        evaluation = loaded.get("evaluation") if isinstance(loaded.get("evaluation"), dict) else {}
        metadata = loaded.get("input_metadata") if isinstance(loaded.get("input_metadata"), dict) else {}
        source_name = metadata.get("source_file") if isinstance(metadata.get("source_file"), str) else ""
        source_text = ""
        if source_name:
            source_path = pilot_dir / source_name
            if not source_path.is_file() and tests_dir.is_dir():
                for t_dir in tests_dir.iterdir():
                    if (t_dir / source_name).is_file():
                        source_path = t_dir / source_name
                        break
                    spec_file = t_dir / "test_spec.yaml"
                    if spec_file.is_file():
                        try:
                            spec_data = yaml.safe_load(spec_file.read_text(encoding="utf-8")) or {}
                            if spec_data.get("source_file") == source_name and (t_dir / "input.yaml").is_file():
                                source_path = t_dir / "input.yaml"
                                break
                        except Exception:
                            pass
            if source_path.is_file():
                source_text = source_path.read_text(encoding="utf-8")
        traces.append({
            "file": path.name,
            "test_id": test_id_str,
            "case_id": str(loaded.get("case_id") or ""),
            "test_kind": str(loaded.get("test_kind") or ""),
            "gate_status": str(evaluation.get("status") or ""),
            "expected": evaluation.get("expected"),
            "extracted_answer": loaded.get("extracted_answer"),
            "answer_match": _answers_match(evaluation.get("expected"), loaded.get("extracted_answer")),
            "reasoning": loaded["reasoning_content"],
            "reasoning_tokens": _usage_int(loaded.get("receipt") or {}, "reasoning_tokens"),
            "source_file": source_name,
            "source_text": source_text,
        })
    return traces, skipped


def _hit(trace: dict[str, Any], hit_id: str, quote: str) -> dict[str, Any]:
    return {
        "id": hit_id,
        "test_id": trace["test_id"],
        "file": trace["file"],
        "gate_status": trace["gate_status"],
        "answer_match": trace["answer_match"],
        "quote": quote,
    }


def classify_trace(trace: dict[str, Any], terms: tuple[str, ...]) -> list[dict[str, Any]]:
    text = trace["reasoning"]
    hits: list[dict[str, Any]] = []
    if PREAMBLE.search(text):
        hits.append(_hit(trace, "need_parse_preamble", _quote(text, PREAMBLE)))
    certificates = len(SUBSTITUTION.findall(text))
    if certificates:
        hits.append(_hit(trace, "substitution_certificate", _quote(text, SUBSTITUTION)))
    schema_hits = sum(text.lower().count(term.lower()) for term in terms)
    if schema_hits >= SCHEMA_MIN and schema_hits > certificates:
        hits.append(_hit(trace, "schema_displacement", f"schema_mentions={schema_hits} certificates={certificates}"))
    source = trace["source_text"]
    for token in CORPUS_TOKENS:
        if token in text and token not in source:
            hits.append(_hit(trace, "corpus_invention", token))
            break
    if CLARIFICATION.search(text):
        hits.append(_hit(trace, "clarification_retreat", _quote(text, CLARIFICATION)))
    hypotheses = len(HYPOTHESIS.findall(text))
    if hypotheses >= HYPOTHESIS_MIN and certificates == 0:
        hits.append(_hit(trace, "ghost_hypothesis_stack", f"hypotheses={hypotheses}"))
    if LICENSE_REFUSAL.search(text):
        template_has_rule = "numeric_license_rule" in source or "forbidden_unlicensed" in source
        if template_has_rule and certificates:
            kind = "template_withdrew_license"
        elif template_has_rule:
            kind = "license_rule_echo"
        else:
            kind = "license_refusal"
        hits.append(_hit(trace, kind, _quote(text, LICENSE_REFUSAL)))
    if ANSWER_CHANNEL.search(text):
        hits.append(_hit(trace, "answer_channel_displacement", _quote(text, ANSWER_CHANNEL)))
    if trace["reasoning_tokens"] >= UNBOUNDED_REASONING_TOKENS and trace["extracted_answer"] is None:
        hits.append(_hit(trace, "unbounded_scratchpad", f"reasoning_tokens={trace['reasoning_tokens']}"))
    return hits


def _group(hits: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for hit in hits:
        grouped.setdefault(hit["id"], []).append(hit)
    return grouped


def _ids(hits: list[dict[str, Any]]) -> list[str]:
    return sorted({hit["test_id"] for hit in hits})


def _candidate(kind: str, candidate_id: str, statement: str, hits: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": candidate_id,
        "kind": kind,
        "admitted": False,
        "statement": statement,
        "trace_count": len(_ids(hits)),
        "answer_match_count": sum(1 for hit in hits if hit["answer_match"]),
        "test_ids": _ids(hits),
        "evidence": [
            {"test_id": hit["test_id"], "file": hit["file"], "quote": hit["quote"]}
            for hit in hits
        ],
    }


def mine(results_dir: Path, schema_path: Path = DEFAULT_SCHEMA) -> dict[str, Any]:
    terms = schema_terms(schema_path)
    traces, skipped = load_traces(results_dir)
    hits = [hit for trace in traces for hit in classify_trace(trace, terms)]
    grouped = _group(hits)

    def take(hit_id: str) -> list[dict[str, Any]]:
        return grouped.get(hit_id, [])

    skills = []
    if take("substitution_certificate"):
        matched = [hit for hit in take("substitution_certificate") if hit["answer_match"]]
        if matched:
            skills.append(_candidate(
                "skill", "skill_substitute_then_report",
                "Bind the declared equations, substitute, and put the checker value in the answer field.",
                matched,
            ))
    if take("need_parse_preamble"):
        paired = [
            hit for hit in take("need_parse_preamble")
            if hit["answer_match"] and hit["test_id"] in set(_ids(take("substitution_certificate")))
        ]
        if paired:
            skills.append(_candidate(
                "skill", "skill_parse_before_arithmetic",
                "Open the scratchpad by parsing the carrier, then calculate. Do not search for a hidden task.",
                paired,
            ))

    antiskills = []
    for hit_id, statement in (
        ("corpus_invention", "Naming a benchmark or corpus that is not in the source prompt."),
        ("clarification_retreat", "Asking what to do with a closed carrier instead of binding it."),
        ("ghost_hypothesis_stack", "Stacking undecided hypotheses without a substitution certificate."),
        ("schema_displacement", "Spending the scratchpad on response-schema field names."),
        ("answer_channel_displacement", "Moving the numeric result into the thesis because the schema has no answer field."),
        ("template_withdrew_license", "Solving the system, then discarding the number because the template withdraws arithmetic license."),
        ("license_refusal", "Refusing arithmetic without the template text that withdraws the license."),
        ("unbounded_scratchpad", "Continuing the scratchpad past the token cap with no extracted answer."),
    ):
        if take(hit_id):
            antiskills.append(_candidate("antiskill", f"antiskill_{hit_id}", statement, take(hit_id)))

    antibodies = []
    for hit_id, antibody_id, predicate in (
        ("corpus_invention", "ab_cot_corpus_invention", "Fire when a corpus token is in the scratchpad and absent from the source prompt."),
        ("template_withdrew_license", "ab_cot_license_conflict", "Fire when the scratchpad both computes a value and then refuses it under a license rule present in the template."),
        ("unbounded_scratchpad", "ab_cot_unbounded_scratchpad", f"Fire when reasoning_tokens >= {UNBOUNDED_REASONING_TOKENS} and extracted_answer is null."),
        ("ghost_hypothesis_stack", "ab_cot_ghost_hypothesis", f"Fire when hypothesis markers >= {HYPOTHESIS_MIN} and no substitution certificate appears."),
        ("answer_channel_displacement", "ab_cot_answer_channel", "Fire when the scratchpad says the checker field cannot hold the answer."),
    ):
        if take(hit_id):
            antibodies.append(_candidate("antibody", antibody_id, predicate, take(hit_id)))

    rules = []
    if take("answer_channel_displacement") or (
        take("schema_displacement") and any(hit["answer_match"] and hit["gate_status"] != "ACCEPTED" for hit in take("schema_displacement"))
    ):
        rules.append({
            "id": "rule_name_the_checker_field",
            "manipulation": "Name the checker field in the task. Do not force the number to live only inside narrowest_defensible_thesis.",
            "test_ids": _ids(take("answer_channel_displacement") + take("schema_displacement")),
        })
    if take("template_withdrew_license"):
        rules.append({
            "id": "rule_license_the_operators",
            "manipulation": "When the template forbids unlicensed arithmetic, put an explicit license on the same operators the carrier uses.",
            "test_ids": _ids(take("template_withdrew_license")),
        })
    if take("corpus_invention") or take("ghost_hypothesis_stack"):
        rules.append({
            "id": "rule_carrier_is_the_whole_task",
            "manipulation": "Tell the scratchpad that the surface form is the whole carrier. Do not invite a search for an outside benchmark.",
            "test_ids": _ids(take("corpus_invention") + take("ghost_hypothesis_stack")),
        })
    if take("unbounded_scratchpad"):
        rules.append({
            "id": "rule_cap_the_scratchpad",
            "manipulation": f"Stop the scratchpad at {UNBOUNDED_REASONING_TOKENS} reasoning tokens unless a substitution certificate is already present.",
            "test_ids": _ids(take("unbounded_scratchpad")),
        })
    if take("substitution_certificate"):
        rules.append({
            "id": "rule_require_one_substitution_line",
            "manipulation": "Require one substitution line before any schema talk or corpus guess.",
            "test_ids": _ids(take("substitution_certificate")),
        })

    patterns = [
        _candidate("pattern", hit_id, f"Repeated scratchpad move `{hit_id}`.", grouped[hit_id])
        for hit_id in sorted(grouped)
    ]
    return {
        "schema": "pfp.cot-mine.v1",
        "authority_effect": "None",
        "results_dir": results_dir.name,
        "schema_terms": list(terms),
        "trace_count": len(traces),
        "skipped_files": skipped,
        "answer_match_count": sum(1 for trace in traces if trace["answer_match"]),
        "accepted_count": sum(1 for trace in traces if trace["gate_status"] == "ACCEPTED"),
        "patterns": patterns,
        "skills": skills,
        "antiskills": antiskills,
        "antibodies": antibodies,
        "rules": rules,
    }


def dump_mine(payload: dict[str, Any]) -> str:
    text = yaml.dump(payload, Dumper=NoAliasDumper, sort_keys=False, allow_unicode=True, width=100)
    if not text.endswith("\n"):
        text += "\n"
    return text


def write_mine(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(dump_mine(payload).encode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mine COT traces into candidate skills and antibodies.")
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    payload = mine(args.results, args.schema)
    out = args.out or (args.results / "cot_mine.yaml")
    write_mine(payload, out)
    print(
        f"traces {payload['trace_count']} skills {len(payload['skills'])} "
        f"antiskills {len(payload['antiskills'])} antibodies {len(payload['antibodies'])} "
        f"rules {len(payload['rules'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
