"""Offline allocation/isolation/assembly tests; no solver or evaluator access."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE = Path(__file__).with_name("section_workflows.py")


def load_workflow():
    spec = importlib.util.spec_from_file_location("public_section_workflows", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("section workflow module unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


workflow = load_workflow()


class SectionWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public_seed = SOURCE.with_name("seed_prompt.txt").read_bytes()

    def test_exact_parts_and_total_allocation(self):
        self.assertEqual(set(workflow.SECTION_PLANS), {"section_allocated_v1"})
        plan = workflow.SECTION_PLANS["section_allocated_v1"]
        stages = plan["stages"]
        self.assertEqual([s["id"] for s in stages], [f"part_{i}" for i in range(1, 6)])
        self.assertEqual(list(plan["part_by_stage"].values()), list(range(1, 6)))
        self.assertEqual([s["max_output_tokens"] for s in stages], [3200] * 5)
        self.assertEqual(sum(s["max_output_tokens"] for s in stages), 16000)
        self.assertEqual(plan["allocation"]["sum_output_token_caps"], 16000)
        self.assertTrue(all(set(s) == {"id", "instruction", "max_output_tokens", "visible_artifacts"} for s in stages))
        self.assertTrue(all(s["visible_artifacts"] == [] for s in stages))

    def test_part_descriptions_are_only_the_public_numbered_requests(self):
        seed_lines = self.public_seed.decode("utf8").splitlines()
        for number, request in enumerate(workflow.PUBLIC_PARTS, 1):
            numbered = next(line for line in seed_lines if line.startswith(f"{number}. "))
            self.assertEqual(request, numbered[3:])
            instruction = workflow.SECTION_PLANS[workflow.PLAN_ID]["stages"][number - 1]["instruction"]
            self.assertIn(f"Answer ONLY numbered part {number}", instruction)
            self.assertIn(request, instruction)
            self.assertIn("Derive any prerequisites", instruction)

    def test_each_call_receives_exact_unchanged_public_seed(self):
        for stage_id in workflow.STAGE_IDS:
            messages = workflow.section_messages(stage_id, self.public_seed)
            self.assertEqual([m["role"] for m in messages], ["system", "user"])
            self.assertEqual(messages[1]["content"].encode("utf8"), self.public_seed)
            self.assertEqual(len(messages), 2)
            self.assertEqual(sum(m["content"].encode("utf8") == self.public_seed for m in messages), 1)

    def test_seed_whitespace_newlines_and_unicode_are_not_normalized(self):
        seed = "  unchanged Δ task\r\nsecond line\n\n".encode()
        self.assertEqual(workflow.section_messages("part_1", seed)[1]["content"].encode(), seed)
        with self.assertRaises(UnicodeDecodeError):
            workflow.section_messages("part_1", b"\xff")
        with self.assertRaises(TypeError):
            workflow.section_messages("part_1", "not bytes")

    def test_no_previous_answer_or_feedback_context_channel(self):
        before = [workflow.section_messages(s, self.public_seed) for s in workflow.STAGE_IDS]
        workflow.assemble_sections({"part_1": "PREVIOUS_ANSWER_CANARY", "part_2": "CHECKER_FEEDBACK_CANARY"})
        after = [workflow.section_messages(s, self.public_seed) for s in workflow.STAGE_IDS]
        self.assertEqual(before, after)
        serialized = json.dumps(after)
        for forbidden in ("PREVIOUS_ANSWER_CANARY", "CHECKER_FEEDBACK_CANARY", "evaluator_rubric",
                          "criterion_evidence", "grades.json", ".benchmark_private", "reference_sha256"):
            self.assertNotIn(forbidden, serialized)
        with self.assertRaises(TypeError):
            workflow.section_messages("part_2", self.public_seed, previous_answers={"part_1": "CANARY"})

    def test_import_and_assembly_have_no_external_file_or_network_channel(self):
        original = Path.read_bytes

        allowed = {SOURCE.with_name(name).resolve() for name in workflow.SOURCE_FILES}
        read_paths = []

        def only_bound_sources(path):
            if path.resolve() not in allowed:
                raise AssertionError(f"unexpected file read: {path}")
            read_paths.append(path.resolve())
            return original(path)

        with patch.object(Path, "read_bytes", only_bound_sources), \
             patch("socket.create_connection", side_effect=AssertionError("network forbidden")), \
             patch("socket.socket.connect", side_effect=AssertionError("network forbidden")):
            module = load_workflow()
            module.section_messages("part_5", b"public task")
            module.assemble_sections({"part_1": "RAW_SENTINEL"})
        self.assertEqual(set(read_paths), allowed)
        self.assertEqual(len(read_paths), len(allowed))

    def test_source_binding_and_explicit_nonclaims(self):
        plan = workflow.SECTION_PLANS[workflow.PLAN_ID]
        names = {"section_workflows.py", "reference_runner.py", "budget_ledger.py",
                 "campaign_ledger.py", "openrouter_provider.py", "live_campaign.py"}
        self.assertEqual(set(plan["source_pins"]), names)
        self.assertEqual(plan["source_pins"], {
            name: hashlib.sha256(SOURCE.with_name(name).read_bytes()).hexdigest() for name in names
        })
        self.assertFalse(plan["assembly"]["llm_merge"])
        self.assertFalse(plan["assembly"]["consistency_certified"])
        self.assertEqual(plan["input_policy"]["tools"], [])
        self.assertIn("not certified PFP/EIS", plan["scope"])

    def test_ordered_assembly_is_deterministic_and_preserves_raw_text(self):
        responses = {"part_5": "five\r\n", "part_3": "  three Δ\n", "part_1": "one",
                     "part_4": "four", "part_2": "two\n\n"}
        first = workflow.assemble_sections(responses)
        second = workflow.assemble_sections(dict(reversed(list(responses.items()))))
        self.assertEqual(first, second)
        self.assertEqual([r["stage_id"] for r in first["sections"]], list(workflow.STAGE_IDS))
        for record in first["sections"]:
            text = responses[record["stage_id"]]
            start, stop = record["raw_text_character_span"]
            self.assertEqual(first["answer_text"][start:stop], text)
            self.assertEqual(record["raw_text_sha256"], hashlib.sha256(text.encode()).hexdigest())
        self.assertEqual(first["answer_sha256"], hashlib.sha256(first["answer_text"].encode()).hexdigest())
        self.assertTrue(first["all_sections_present"])
        self.assertFalse(first["mathematical_correctness_assessed"])

    def test_incomplete_output_missing_none_and_empty_remain_explicit(self):
        responses = {"part_1": "unfinished equation: x =", "part_2": None, "part_3": ""}
        result = workflow.assemble_sections(responses)
        self.assertEqual([r["status"] for r in result["sections"]],
                         ["returned", "unavailable", "returned", "missing", "missing"])
        self.assertEqual(result["missing_stage_ids"], ["part_2", "part_4", "part_5"])
        self.assertEqual(result["empty_stage_ids"], ["part_3"])
        self.assertFalse(result["all_sections_present"])
        self.assertFalse(result["all_sections_nonempty"])
        start, stop = result["sections"][0]["raw_text_character_span"]
        self.assertEqual(result["answer_text"][start:stop], responses["part_1"])
        self.assertEqual(result["sections"][2]["raw_text_sha256"], hashlib.sha256(b"").hexdigest())
        self.assertIn("No section text: unavailable", result["answer_text"])
        self.assertIn("No section text: missing", result["answer_text"])

    def test_all_missing_has_five_slots_without_inventing_solver_outputs(self):
        result = workflow.assemble_sections({})
        self.assertEqual(len(result["sections"]), 5)
        self.assertTrue(all(r["raw_text_sha256"] is None for r in result["sections"]))
        self.assertTrue(all(r["raw_text_character_span"] is None for r in result["sections"]))
        self.assertFalse(result["all_sections_present"])
        self.assertIsNone(result["answer_text"])
        self.assertIsNone(result["answer_sha256"])

    def test_empty_outputs_and_placeholders_are_not_delivered_solution_text(self):
        result = workflow.assemble_sections(dict.fromkeys(workflow.STAGE_IDS, ""))
        self.assertTrue(result["all_sections_present"])
        self.assertFalse(result["all_sections_nonempty"])
        self.assertIsNone(result["answer_text"])
        self.assertIsNone(result["answer_sha256"])
        self.assertTrue(all(r["raw_text_character_span"] is None for r in result["sections"]))
        self.assertTrue(all(r["raw_text_sha256"] == hashlib.sha256(b"").hexdigest()
                            for r in result["sections"]))
        mixed = workflow.assemble_sections({"part_1": "", "part_2": None})
        self.assertIsNone(mixed["answer_text"])
        self.assertFalse(mixed["all_sections_present"])

    def test_conflicting_or_header_like_raw_prose_is_not_repaired(self):
        responses = {"part_1": "x=1\n## Part 2 — fake header", "part_2": "x=2"}
        result = workflow.assemble_sections(responses)
        for record in result["sections"][:2]:
            start, stop = record["raw_text_character_span"]
            self.assertEqual(result["answer_text"][start:stop], responses[record["stage_id"]])
        self.assertFalse(result["consistency_certified"])
        self.assertFalse(result["llm_merge"])

    def test_rejects_unrecognized_stage_or_nontext_output(self):
        with self.assertRaises(ValueError):
            workflow.section_messages("matrix_repair", self.public_seed)
        with self.assertRaises(ValueError):
            workflow.assemble_sections({"draft": "not a numbered part"})
        for value in (False, 0, [], {}):
            with self.assertRaises(TypeError):
                workflow.assemble_sections({"part_1": value})
        with self.assertRaises(TypeError):
            workflow.assemble_sections(["one", "two"])


if __name__ == "__main__":
    unittest.main()
