"""COT miner: repeated scratchpad moves become unadmitted candidates.

AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from adversary.tests.pilots.cot_miner import classify_trace, mine, schema_terms

PILOT = Path(__file__).resolve().parents[2] / "pfp" / "tests" / "pilot_0000000"
RESULTS = PILOT / "misc" if (PILOT / "misc").is_dir() else PILOT / "results"
SCHEMA = (
    Path(__file__).resolve().parents[1]
    / "infrastructure"
    / "yaml"
    / "pilots"
    / "pilot_response_v1.schema.yaml"
)


def _trace(text: str, **overrides):
    base = {
        "file": "response_case.yaml",
        "test_id": "case",
        "case_id": "case",
        "test_kind": "plain_input",
        "gate_status": "MALFORMED",
        "expected": 3,
        "extracted_answer": None,
        "answer_match": False,
        "reasoning": text,
        "reasoning_tokens": 10,
        "source_file": "seed.yaml",
        "source_text": "Solve x + 2y = 5.",
    }
    base.update(overrides)
    return base


def test_schema_terms_come_from_the_response_contract():
    terms = schema_terms(SCHEMA)
    assert "narrowest_defensible_thesis" in terms
    assert "SPK-001" in terms


def test_corpus_name_absent_from_the_source_is_an_invention():
    hits = classify_trace(_trace("Could be from BigBench or a Dyck task."), schema_terms(SCHEMA))
    assert "corpus_invention" in {hit["id"] for hit in hits}
    assert "ghost_hypothesis_stack" not in {hit["id"] for hit in hits}


def test_license_rule_in_the_template_is_not_called_an_invention():
    echo = classify_trace(
        _trace(
            "The correct behavior is to not solve arithmetic without license.",
            source_text="numeric_license_rule: explicit license",
        ),
        schema_terms(SCHEMA),
    )
    echo_ids = {hit["id"] for hit in echo}
    assert "license_rule_echo" in echo_ids
    assert "template_withdrew_license" not in echo_ids
    assert "license_refusal" not in echo_ids

    conflict = classify_trace(
        _trace(
            "Substitute x = 1. The correct behavior is to not solve arithmetic without license.",
            source_text="numeric_license_rule: explicit license",
        ),
        schema_terms(SCHEMA),
    )
    conflict_ids = {hit["id"] for hit in conflict}
    assert "template_withdrew_license" in conflict_ids
    assert "substitution_certificate" in conflict_ids
    assert "license_rule_echo" not in conflict_ids
    assert "license_refusal" not in conflict_ids
    quote = next(hit["quote"] for hit in conflict if hit["id"] == "template_withdrew_license")
    assert quote.startswith("not solve arithmetic")


def test_real_pilot_0000000_mine_is_deterministic_and_unadmitted():
    first = mine(RESULTS, SCHEMA)
    second = mine(RESULTS, SCHEMA)
    assert first == second
    assert first["authority_effect"] == "None"
    assert first["trace_count"] >= 22
    assert first["accepted_count"] >= 1
    by_skill = {item["id"]: item for item in first["skills"]}
    by_anti = {item["id"]: item for item in first["antiskills"]}
    by_antibody = {item["id"]: item for item in first["antibodies"]}
    assert "seed_plain" in by_skill["skill_substitute_then_report"]["test_ids"]
    assert "rewrite_03_plain" in by_anti["antiskill_corpus_invention"]["test_ids"]
    assert len(by_anti["antiskill_template_withdrew_license"]["test_ids"]) >= 1
    assert all(item["admitted"] is False for item in first["antibodies"])
    assert "ab_cot_license_conflict" in by_antibody
    assert "rule_license_the_operators" in {item["id"] for item in first["rules"]}
    dumped = yaml.safe_load(yaml.dump(first))
    assert dumped["schema"] == "pfp.cot-mine.v1"
