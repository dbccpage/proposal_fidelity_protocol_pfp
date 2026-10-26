"""Targeted unit tests for Prompt Representation Pydantic models and YAML specifications.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path

import yaml
from pydantic import ValidationError

_PROMPTS_DIR = (
    Path(__file__).resolve().parents[1]
    / "domain"
    / "prompt_representations"
)

# Register prompt_representations as a proper package in sys.modules
if "prompt_representations" not in sys.modules:
    pkg = types.ModuleType("prompt_representations")
    pkg.__path__ = [str(_PROMPTS_DIR)]
    pkg.__file__ = str(_PROMPTS_DIR / "__init__.py")
    sys.modules["prompt_representations"] = pkg
    spec = importlib.util.spec_from_file_location("prompt_representations", _PROMPTS_DIR / "__init__.py")
    if spec and spec.loader:
        spec.loader.exec_module(pkg)

from prompt_representations import (
    CochainPromptRepresentation,
    CochainSpanBinding,
    DiagramBox,
    DiagramPromptRepresentation,
    DiagramSpanBinding,
    DiagramWire,
    EgraphPromptRepresentation,
    EgraphSpanBinding,
    OperadEnvironment,
    OperadicPromptRepresentation,
    OperadSpanBinding,
    OperadSpanTable,
    OperadTreeSkeleton,
    RawPromptRepresentation,
    RelationalPromptRepresentation,
    RelationalSpanRow,
    StructuredPromptRepresentation,
    StructuredSegmentBinding,
    SymbolicPromptRepresentation,
)


class TestPromptRepresentations(unittest.TestCase):
    def setUp(self) -> None:
        self.repr_dir = _PROMPTS_DIR
        self.infra_repr_dir = (
            Path(__file__).resolve().parents[1]
            / "infrastructure"
            / "yaml"
            / "prompts"
            / "reprs"
        )
        self.pilot_dir = (
            Path(__file__).resolve().parents[2]
            / "documentation"
            / "030_the_symbol_game_proposal_fidelity_protocol_pfp"
            / "pilots"
            / "pilot_output"
        )
        trials_file = self.pilot_dir / "trials.json"
        if trials_file.is_file():
            with open(trials_file, "r", encoding="utf-8") as f:
                self.trials = json.load(f)
        else:
            self.trials = []
            yaml_specs = [
                "raw_prompt_representation.yaml",
                "structured_prompt_representation.yaml",
                "relational_prompt_representation.yaml",
                "symbolic_prompt_representation.yaml",
                "operadic_prompt_representation.yaml",
                "egraph_prompt_representation.yaml",
                "diagram_prompt_representation.yaml",
                "cochain_prompt_representation.yaml",
            ]
            for ys in yaml_specs:
                spec_path = self.repr_dir / ys
                if spec_path.is_file():
                    with open(spec_path, "r", encoding="utf-8") as f:
                        doc = yaml.safe_load(f)
                        if "canonical_example" in doc:
                            ex = dict(doc["canonical_example"])
                            if "prompt" in ex and isinstance(ex["prompt"], str):
                                ex["prompt"] = ex["prompt"].strip("\r\n")
                            self.trials.append(ex)

    def _get_trial(self, trial_id: str) -> dict:
        for t in self.trials:
            if t["trial_id"] == trial_id:
                return t
        raise KeyError(f"Trial {trial_id} not found in trials.json")

    def test_raw_representation_model(self) -> None:
        trial = self._get_trial("case0:raw")
        raw_repr = RawPromptRepresentation.from_text(
            source_id=trial["source_id"],
            source_text=trial["prompt"],
        )
        self.assertEqual(raw_repr.source_sha256, trial["source_sha256"])
        self.assertEqual(raw_repr.prompt_sha256(), trial["prompt_sha256"])
        self.assertEqual(raw_repr.render(), trial["prompt"])

        # Test invalid digest raises ValidationError
        with self.assertRaises(ValidationError):
            RawPromptRepresentation(
                source_id="test",
                source_text="some text",
                source_sha256="0" * 64,
                representation_kind="raw",
                authority_effect="None",
            )

    def test_structured_representation_model(self) -> None:
        trial = self._get_trial("case0:structured")
        payload_data = json.loads(trial["prompt"])

        segments = [
            StructuredSegmentBinding(
                slot=seg["slot"],
                role=seg["role"],
                text=seg["text"],
            )
            for seg in payload_data["segments"]
        ]

        structured_repr = StructuredPromptRepresentation.from_source_and_segments(
            source_id=trial["source_id"],
            source_text=payload_data["source"],
            proposal_sha256=trial["proposal_sha256"],
            segments=segments,
        )
        self.assertEqual(structured_repr.source_sha256, trial["source_sha256"])
        self.assertEqual(structured_repr.render(), trial["prompt"])
        self.assertEqual(structured_repr.prompt_sha256(), trial["prompt_sha256"])

        # Test invalid slot sequence raises ValidationError
        with self.assertRaises(ValidationError):
            bad_segments = [
                StructuredSegmentBinding(slot="s1", role="task", text="Task text"),
            ]
            StructuredPromptRepresentation.from_source_and_segments(
                source_id="test",
                source_text="Task text",
                proposal_sha256="a" * 64,
                segments=bad_segments,
            )

    def test_relational_representation_model(self) -> None:
        trial = self._get_trial("case0:relational")
        spans = [
            RelationalSpanRow(slot="s0", role="task", text="Task: Extract all primes less than 20. "),
            RelationalSpanRow(
                slot="s1",
                role="constraint",
                text='Constraint: Output must be a JSON array of integers strictly ordered ascending with key "primes". ',
            ),
            RelationalSpanRow(slot="s2", role="output", text="Output: JSON only without code fences."),
        ]
        rel_repr = RelationalPromptRepresentation.from_spans(
            source_id=trial["source_id"],
            source_sha256=trial["source_sha256"],
            proposal_sha256=trial["proposal_sha256"],
            spans=spans,
        )
        self.assertEqual(rel_repr.render(), trial["prompt"])
        self.assertEqual(rel_repr.prompt_sha256(), trial["prompt_sha256"])
        self.assertIn("CREATE TABLE IF NOT EXISTS prompt_spans", rel_repr.ddl())

    def test_symbolic_representation_model(self) -> None:
        trial = self._get_trial("case0:symbolic")
        slot_roles = [
            ("s0", "task"),
            ("s1", "constraint"),
            ("s2", "output"),
        ]
        slot_texts = {
            "s0": "Task: Extract all primes less than 20. ",
            "s1": 'Constraint: Output must be a JSON array of integers strictly ordered ascending with key "primes". ',
            "s2": "Output: JSON only without code fences.",
        }
        sym_repr = SymbolicPromptRepresentation.from_bindings(
            source_id=trial["source_id"],
            source_sha256=trial["source_sha256"],
            proposal_sha256=trial["proposal_sha256"],
            grammar_sha256="a" * 64,
            slot_roles=slot_roles,
            slot_texts=slot_texts,
        )
        self.assertEqual(sym_repr.wire, "<<p><v1><<q><s0>><<c><s1>><<o><s2>>>")
        self.assertEqual(sym_repr.render(), trial["prompt"])
        self.assertEqual(sym_repr.prompt_sha256(), trial["prompt_sha256"])

    def test_operadic_representation_model(self) -> None:
        operad_repr = OperadicPromptRepresentation(
            source_id="pilot_004:operadic",
            source_sha256="a" * 64,
            proposal_sha256="b" * 64,
            environment=OperadEnvironment(
                ring="Q[x, y]",
                region="[-3, 3] x [-3, 3] over Q^2",
                constants={"deltoid": "(x^2+y^2)^2 - 27"},
            ),
            skeleton=OperadTreeSkeleton(
                operations=[
                    "Op_subdivide(B) -> {B_00, B_10, B_01, B_11}",
                    "Op_collar(B, cusps) -> CuspCollarReceipt",
                ]
            ),
            span_table=OperadSpanTable(
                spans=[
                    OperadSpanBinding(slot="s0", role="task", text="Isolate cusps."),
                    OperadSpanBinding(slot="s1", role="constraint", text="Exact rational boundaries."),
                ],
                ideals=["RULE_DELTOID_SINGULARITY_COLLAR_FENCE", "IDEAL_EXACT_RATIONAL_DOMAIN"],
                antibodies=["AB_DELTOID_SINGULARITY_LEAK"],
            ),
        )
        rendered = operad_repr.render()
        self.assertIn("Layer 0 (Environment):", rendered)
        self.assertIn("Ring: Q[x, y].", rendered)
        self.assertIn("Layer 1 (TreeSkeleton):", rendered)
        self.assertIn("Op_subdivide", rendered)
        self.assertIn("Layer 2 (SpanTable):", rendered)
        self.assertIn("s0 [task]: Isolate cusps.", rendered)
        self.assertIn("Ideals: IDEAL_EXACT_RATIONAL_DOMAIN, RULE_DELTOID_SINGULARITY_COLLAR_FENCE.", rendered)

        meta = operad_repr.to_canonical_metadata()
        self.assertEqual(meta["representation_kind"], "operadic")
        self.assertEqual(meta["operation_count"], 2)
        self.assertEqual(meta["span_count"], 2)
        self.assertEqual(meta["ideal_count"], 2)

        # Invariant check: Task span required
        with self.assertRaises(ValidationError):
            OperadicPromptRepresentation(
                source_id="test",
                source_sha256="a" * 64,
                proposal_sha256="b" * 64,
                environment=OperadEnvironment(ring="Q"),
                skeleton=OperadTreeSkeleton(operations=["Op_test() -> Result"]),
                span_table=OperadSpanTable(
                    spans=[OperadSpanBinding(slot="s0", role="context", text="No task")],
                    ideals=["RULE_TEST"],
                ),
            )

        # Invariant check: Ideals required
        with self.assertRaises(ValidationError):
            OperadicPromptRepresentation(
                source_id="test",
                source_sha256="a" * 64,
                proposal_sha256="b" * 64,
                environment=OperadEnvironment(ring="Q"),
                skeleton=OperadTreeSkeleton(operations=["Op_test() -> Result"]),
                span_table=OperadSpanTable(
                    spans=[OperadSpanBinding(slot="s0", role="task", text="Do work")],
                    ideals=[],
                ),
            )

    def test_egraph_representation_model(self) -> None:
        egraph_repr = EgraphPromptRepresentation(
            source_id="case0:egraph",
            source_sha256="c" * 64,
            proposal_sha256="d" * 64,
            normal_form_level="3NF",
            eclasses={
                "e0": ["task_root", "primary_task"],
                "e1": ["exact_rational", "field_Q"],
            },
            rewrite_rules=["canonical_domain(x) -> Q"],
            spans=[
                EgraphSpanBinding(slot="s0", role="task", eclass_id="e0", text="Compute normal form."),
                EgraphSpanBinding(slot="s1", role="constraint", eclass_id="e1", text="No floats permitted."),
            ],
        )
        rendered = egraph_repr.render()
        self.assertIn("E-Graph Saturated Normal Form (level: 3NF)", rendered)
        self.assertIn('e0 := {"task_root", "primary_task"}', rendered)
        self.assertIn("s0 [task -> e0]: Compute normal form.", rendered)

        meta = egraph_repr.to_canonical_metadata()
        self.assertEqual(meta["representation_kind"], "egraph")
        self.assertEqual(meta["eclass_count"], 2)
        self.assertEqual(meta["span_count"], 2)

        # Invariant check: Undefined eclass reference rejected
        with self.assertRaises(ValidationError):
            EgraphPromptRepresentation(
                source_id="test",
                source_sha256="c" * 64,
                proposal_sha256="d" * 64,
                eclasses={"e0": ["term"]},
                spans=[EgraphSpanBinding(slot="s0", role="task", eclass_id="e99", text="Bad ref")],
            )

    def test_diagram_representation_model(self) -> None:
        diag_repr = DiagramPromptRepresentation(
            source_id="case0:diagram",
            source_sha256="e" * 64,
            proposal_sha256="f" * 64,
            colors=["State", "Token", "Receipt"],
            wires=[
                DiagramWire(wire_id="w0", color="State", source="IN", target="b0"),
                DiagramWire(wire_id="w1", color="Token", source="IN", target="b0"),
                DiagramWire(wire_id="w2", color="Receipt", source="b0", target="OUT"),
            ],
            boxes=[
                DiagramBox(box_id="b0", label="Op_verify", inputs=["w0", "w1"], outputs=["w2"]),
            ],
            spans=[
                DiagramSpanBinding(slot="s0", role="task", box_id="b0", text="Verify port wiring."),
            ],
        )
        rendered = diag_repr.render()
        self.assertIn("Monoidal Category String Diagram Representation", rendered)
        self.assertIn("w0: State (IN -> b0)", rendered)
        self.assertIn("b0 [Op_verify]: [w0, w1] -> [w2]", rendered)
        self.assertIn("s0 [task @ b0]: Verify port wiring.", rendered)

        meta = diag_repr.to_canonical_metadata()
        self.assertEqual(meta["representation_kind"], "diagram")
        self.assertEqual(meta["color_count"], 3)
        self.assertEqual(meta["box_count"], 1)
        self.assertEqual(meta["wire_count"], 3)

        # Invariant check: Undeclared color rejected
        with self.assertRaises(ValidationError):
            DiagramPromptRepresentation(
                source_id="test",
                source_sha256="e" * 64,
                proposal_sha256="f" * 64,
                colors=["State"],
                wires=[DiagramWire(wire_id="w0", color="AlienColor", source="IN", target="b0")],
                boxes=[DiagramBox(box_id="b0", label="Op", inputs=["w0"], outputs=[])],
                spans=[DiagramSpanBinding(slot="s0", role="task", box_id="b0", text="Test")],
            )

    def test_cochain_representation_model(self) -> None:
        cochain_repr = CochainPromptRepresentation(
            source_id="case0:cochain",
            source_sha256="1" * 64,
            proposal_sha256="2" * 64,
            vertices=["v0", "v1", "v2"],
            edges=[["v0", "v1"], ["v1", "v2"], ["v2", "v0"]],
            faces=[["v0", "v1", "v2"]],
            cochain_0={"v0": "0", "v1": "1", "v2": "0"},
            cochain_1={"v0->v1": "1/2", "v1->v2": "1/2", "v2->v0": "-1"},
            cochain_2={"v0->v1->v2": "0"},
            spans=[
                CochainSpanBinding(slot="s0", role="task", simplex="v0", text="Boundary wall task."),
            ],
        )
        rendered = cochain_repr.render()
        self.assertIn("Simplicial Complex Cochain Representation (Domain: Q)", rendered)
        self.assertIn("Simplices: V={v0, v1, v2}", rendered)
        self.assertIn("v0->v1 = 1/2", rendered)
        self.assertIn("s0 [task @ v0]: Boundary wall task.", rendered)

        meta = cochain_repr.to_canonical_metadata()
        self.assertEqual(meta["representation_kind"], "cochain")
        self.assertEqual(meta["vertex_count"], 3)
        self.assertEqual(meta["edge_count"], 3)

        # Invariant check: Floating-point value rejected in rational cochain
        with self.assertRaises(ValidationError):
            CochainPromptRepresentation(
                source_id="test",
                source_sha256="1" * 64,
                proposal_sha256="2" * 64,
                vertices=["v0"],
                cochain_0={"v0": "0.333333"},  # float representation prohibited
                spans=[CochainSpanBinding(slot="s0", role="task", simplex="v0", text="Test")],
            )

        # Invariant check: Undeclared edge vertex rejected
        with self.assertRaises(ValidationError):
            CochainPromptRepresentation(
                source_id="test",
                source_sha256="1" * 64,
                proposal_sha256="2" * 64,
                vertices=["v0", "v1"],
                edges=[["v0", "v99"]],  # v99 not declared
                spans=[CochainSpanBinding(slot="s0", role="task", simplex="v0", text="Test")],
            )

    def _assert_unmeasured_rates_are_withdrawn(self, directory: Path, pattern: str) -> None:
        rate_keys = (
            "validation_rate",
            "constraint_preservation_rate",
            "passed_trials",
            "total_trials",
            "avg_input_tokens",
            "avg_output_tokens",
            "avg_latency_ms",
            "marginal_overhead_tokens",
        )
        repo = Path(__file__).resolve().parents[2]
        old_raw = {
            "source_study": "pilots/pilot_output/results.md",
            "total_trials": 16,
            "passed_trials": 15,
            "validation_rate": 0.938,
        }
        self.assertIsNotNone(self._rate_refusal(old_raw, repo))
        self.assertEqual(int(old_raw["passed_trials"]), 15)
        for path in sorted(directory.glob(pattern)):
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
            block = document["empirical_performance_baseline"]
            self.assertIsNone(self._rate_refusal(block, repo), path.name)
            text = path.read_text(encoding="utf-8")
            for key in rate_keys:
                self.assertNotIn(f"{key}:", text, path.name)

    @staticmethod
    def _rate_refusal(block: dict, repo: Path):
        rate_keys = (
            "validation_rate",
            "constraint_preservation_rate",
            "passed_trials",
            "total_trials",
            "avg_input_tokens",
            "avg_output_tokens",
            "avg_latency_ms",
            "marginal_overhead_tokens",
        )
        present = [key for key in rate_keys if key in block]
        if not present:
            return None
        if not block.get("evidence_status"):
            return "missing evidence_status"
        if block.get("general_efficacy_established") is not False:
            return "general_efficacy_established is not false"
        sources = block.get("sources")
        if type(sources) is not list or not sources:
            return "rate without a resolvable source pin"
        for source in sources:
            pin = repo / source["path"]
            if not pin.is_file():
                return f"missing pin {source['path']}"
        return None

    def test_yaml_specifications_integrity(self) -> None:
        yaml_files = [
            "raw_prompt_representation.yaml",
            "structured_prompt_representation.yaml",
            "relational_prompt_representation.yaml",
            "symbolic_prompt_representation.yaml",
            "operadic_prompt_representation.yaml",
            "egraph_prompt_representation.yaml",
            "diagram_prompt_representation.yaml",
            "cochain_prompt_representation.yaml",
        ]
        for yf in yaml_files:
            # Check in domain directory
            file_path = self.repr_dir / yf
            self.assertTrue(file_path.is_file(), f"Missing domain YAML specification: {yf}")
            with open(file_path, "r", encoding="utf-8") as f:
                doc = yaml.safe_load(f)
            self.assertEqual(doc.get("schema_version"), "pfp.prompt_representation.v1")
            self.assertEqual(doc.get("authority_effect"), "None")
            self.assertIn("invariants", doc)
            self.assertIn("canonical_example", doc)
            self.assertIn("empirical_performance_baseline", doc)

        self._assert_unmeasured_rates_are_withdrawn(self.repr_dir, "*.yaml")
        self._assert_unmeasured_rates_are_withdrawn(
            self.infra_repr_dir, "template_repr_*.yaml"
        )

        # Check in infrastructure reprs directory with template_repr_ prefix
        for slug in ["raw", "structured", "relational", "symbolic", "operadic", "egraph", "diagram", "cochain"]:
            infra_file = self.infra_repr_dir / f"template_repr_{slug}.yaml"
            self.assertTrue(infra_file.is_file(), f"Missing infrastructure YAML: template_repr_{slug}.yaml")
            self.assertLessEqual(len(f"repr_{slug}"), 20, f"Slug too long: repr_{slug}")


if __name__ == "__main__":
    unittest.main()
