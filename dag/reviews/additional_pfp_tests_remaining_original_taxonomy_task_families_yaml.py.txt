"""Bedrock task family tokens come from task_families.yaml.

The catalog covers the six bedrock ids, the Pillar III directive ids, every
matrix token, and independently introduced challenge/research families.

AuthorityEffect: None.
"""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from pfp.domain.value_objects.taxonomy import (
    VALID_TASK_FAMILIES,
    get_valid_task_families,
    TaskFamilyVO,
)
from pfp.infrastructure.taxonomy.task_families import (
    TaskFamilyEnum,
)

_YAML = (
    Path(__file__).resolve().parents[2]
    / "infrastructure"
    / "yaml"
    / "taxonomy"
    / "task_families.yaml"
)
_DOMAIN = Path(__file__).resolve().parents[2] / "domain" / "value_objects" / "taxonomy.py"
_MATRIX = Path(__file__).resolve().parents[3] / "pilots" / "matrix" / "max_pilot_matrix.yaml"
_BEDROCK = frozenset(
    {
        "linear_algebra",
        "graph_facts",
        "graph_repair",
        "refusal",
        "cochain_defect",
        "magma_associativity",
    }
)
_MATRIX = (
    Path(__file__).resolve().parents[3]
    / "education"
    / "pilots"
    / "matrix"
    / "max_pilot_matrix.yaml"
)
_BEDROCK = frozenset({
    "linear_algebra",
    "graph_facts",
    "graph_repair",
    "refusal",
    "cochain_defect",
    "magma_associativity",
})
_DIRECTIVE = {
    "group_commutator": "Commutator Subgroups & Word Problem Invariants",
    "simplex_homology": "Simplicial Complex Betti Number Calculations",
    "curvature_defect": "Discrete 4D Bianchi Identities & Holonomy Residuals",
    "hopf_fibration": "Discrete Hopf Map Projections",
    "attention_mechanism_control": "Causal Head Attribution & Attention Steering",
    "activation_patching": "Layer-wise Activation Interventions & Noise Contrast",
}


def _matrix_task_family_tokens(document: object) -> list[str]:
    found: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "task_family":
                    if type(value) is not str or not value:
                        raise AssertionError(
                            f"task_family token must be a non-empty str, got {value!r}"
                        )
                    found.append(value)
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(document)
    return found


class TestTaskFamiliesFromYaml(unittest.TestCase):
    def test_domain_set_matches_catalog_ids(self) -> None:
        raw = yaml.safe_load(_YAML.read_text(encoding="utf-8"))
        ids = [item["id"] for item in raw["categories"]]
        self.assertLessEqual(set(ids), set(get_valid_task_families()))
        self.assertTrue(_BEDROCK <= VALID_TASK_FAMILIES)
        self.assertEqual([member.value for member in TaskFamilyEnum], ids)
        source = _DOMAIN.read_text(encoding="utf-8")
        for token in ids:
            if token not in _BEDROCK:
                self.assertNotIn(token, source)
            self.assertEqual(str(TaskFamilyVO(token)), token)

    def test_catalog_covers_bedrock_directive_matrix_and_research_families(self) -> None:
        raw = yaml.safe_load(_YAML.read_text(encoding="utf-8"))
        categories = raw["categories"]
        ids = [item["id"] for item in categories]
        self.assertEqual(ids, sorted(set(ids)))
        catalog = set(ids)
        self.assertTrue(_BEDROCK <= catalog)
        self.assertTrue(set(_DIRECTIVE) <= catalog)
        matrix_doc = yaml.safe_load(_MATRIX.read_text(encoding="utf-8"))
        matrix_tokens = _matrix_task_family_tokens(matrix_doc)
        self.assertTrue(matrix_tokens)
        self.assertTrue(all(type(token) is str and token for token in matrix_tokens))
        matrix = set(matrix_tokens)
        self.assertGreaterEqual(len(matrix), 31)
        self.assertIn("linear_algebra", matrix)
        self.assertIn("arithmetic_enumeration", matrix)
        self.assertTrue(matrix <= catalog)
        for item in categories:
            self.assertEqual(set(item), {"id", "display_name", "description"})
            token = item["id"]
            self.assertTrue(item["display_name"])
            self.assertEqual(str(TaskFamilyVO(token)), token)
            self.assertEqual(TaskFamilyEnum[token].value, token)
            if token in _BEDROCK:
                self.assertIn("Source: bedrock.", item["description"])
            elif token in _DIRECTIVE:
                self.assertIn(_DIRECTIVE[token], item["description"])
                self.assertIn("Source: directive.", item["description"])
            self.assertTrue(item["description"])

    def test_unknown_family_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            TaskFamilyVO("unknown_family")


if __name__ == "__main__":
    unittest.main()
