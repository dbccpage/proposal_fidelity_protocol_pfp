"""Mutation-resistant branch tests for the governance digest refactor."""

from __future__ import annotations

import unittest

from operads.application.governance_digest.digest_corpus import (
    RUNS_CORPUS,
    digest_corpus,
)
from operads.application.governance_digest.textops import (
    apply_edits,
    measure,
    sha256_text,
)
from operads.domain.governance_digest.records import (
    REQUIRED_FRONTMATTER,
    EditLocator,
    GovernanceCorpus,
    PatternDoc,
    RepairSpec,
    TextDoc,
)

RULE_PATH = ".agents/rules/example.md"
RULE_TEXT = "## Before\n\nbody\n\n## After\n"
REPLACEMENT = "Pattern: `AP_TEST`\n\n"
LOCATOR = EditLocator("insert_before", anchor_text="## After")


def _doc(corpus: str, path: str, text: str) -> TextDoc:
    return TextDoc(corpus, path, sha256_text(text), text)


def _pattern(pattern_id: str, dual: str, *, category: str, language: str = "python") -> PatternDoc:
    return PatternDoc(
        relative_path=f".agents/patterns/{pattern_id}.md",
        sha256=f"hash-{pattern_id}",
        pattern_id=pattern_id,
        name=pattern_id,
        category=category,
        language=language,
        dual_pattern=dual,
        frontmatter_keys=REQUIRED_FRONTMATTER,
        detection_text="detect" if category == "anti_pattern" else "",
    )


def _repair(*, pattern_hash: str = "hash-AP_TEST") -> RepairSpec:
    edited, error = apply_edits(RULE_TEXT, [(LOCATOR, REPLACEMENT)])
    assert error == ""
    assert edited is not None
    return RepairSpec(
        repair_id="repair-test",
        edit_kind="cite_pattern",
        target_path=RULE_PATH,
        target_section="Before",
        pattern_ids=("AP_TEST", "HP_TEST"),
        locator=LOCATOR,
        replacement_text=REPLACEMENT,
        pre_fingerprint=measure(
            RULE_TEXT,
            edit_kind="cite_pattern",
            target_section="Before",
            locator=LOCATOR,
            replacement_text=REPLACEMENT,
        ),
        post_fingerprint=measure(
            edited,
            edit_kind="cite_pattern",
            target_section="Before",
            locator=LOCATOR,
            replacement_text=REPLACEMENT,
        ),
        pattern_sha256=(("AP_TEST", pattern_hash), ("HP_TEST", "hash-HP_TEST")),
    )


def _repair_finding(receipt: dict[str, object]) -> dict[str, object]:
    findings = receipt["findings"]
    assert isinstance(findings, list)
    return next(item for item in findings if item["finding_id"].endswith(":repair-test"))


class GovernanceDigestRefactorBranchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.patterns = (
            _pattern("AP_TEST", "HP_TEST", category="anti_pattern"),
            _pattern("HP_TEST", "AP_TEST", category="healthy_pattern"),
        )

    def _digest(self, target_text: str, spec: RepairSpec | None = None) -> dict[str, object]:
        corpus = GovernanceCorpus(
            patterns=self.patterns,
            rules=(_doc("rules", RULE_PATH, target_text),),
        )
        return digest_corpus(corpus, (spec or _repair(),))

    def test_repair_state_machine_distinguishes_every_non_missing_state(self) -> None:
        pending = self._digest(RULE_TEXT)
        self.assertEqual(_repair_finding(pending)["disposition"], "repair_pending")
        self.assertEqual(len(pending["proposals"]), 1)

        edited, error = apply_edits(RULE_TEXT, [(LOCATOR, REPLACEMENT)])
        self.assertEqual(error, "")
        assert edited is not None
        codified = self._digest(edited)
        self.assertEqual(_repair_finding(codified)["disposition"], "already_codified")
        self.assertEqual(codified["proposals"], [])

        drifted = self._digest(RULE_TEXT.replace("body", "changed"))
        self.assertEqual(
            _repair_finding(drifted)["reason"],
            "the watched span matches neither stored fingerprint",
        )
        self.assertEqual(drifted["proposals"], [])

        pattern_drift = self._digest(RULE_TEXT, _repair(pattern_hash="stale-hash"))
        self.assertEqual(
            _repair_finding(pattern_drift)["reason"],
            "pattern file bytes differ from the fingerprint stored with this repair",
        )
        self.assertEqual(pattern_drift["proposals"], [])

    def test_duplicate_repair_specs_do_not_duplicate_findings_or_proposals(self) -> None:
        spec = _repair()
        corpus = GovernanceCorpus(
            patterns=self.patterns,
            rules=(_doc("rules", RULE_PATH, RULE_TEXT),),
        )

        receipt = digest_corpus(corpus, (spec, spec))

        repair_findings = [
            item for item in receipt["findings"] if item["finding_id"].endswith(":repair-test")
        ]
        self.assertEqual(len(repair_findings), 1)
        self.assertEqual(len(receipt["proposals"]), 1)

    def test_owner_coverage_separates_table_gap_registered_repair_and_unknown_language(
        self,
    ) -> None:
        owner_path = ".agents/skills/techne-code-python-anti-patterns/SKILL.md"
        owner = _doc(
            "skills",
            owner_path,
            "| Anti-Pattern | Healthy Pattern |\n|---|---|\n| `AP_TEST` | `HP_TEST` |\n",
        )
        codified = digest_corpus(GovernanceCorpus(patterns=self.patterns, skills=(owner,)), ())
        by_id = {item["finding_id"]: item for item in codified["findings"]}
        self.assertEqual(by_id["skill_table_ok:AP_TEST"]["disposition"], "already_codified")
        self.assertEqual(by_id["skill_table_ok:HP_TEST"]["disposition"], "already_codified")

        missing_table = digest_corpus(GovernanceCorpus(patterns=self.patterns), ())
        missing_ids = {item["finding_id"] for item in missing_table["findings"]}
        self.assertIn("skill_table_gap:AP_TEST", missing_ids)

        table_repair = _repair()
        table_repair = RepairSpec(
            repair_id=table_repair.repair_id,
            edit_kind="skill_table_row",
            target_path=owner_path,
            target_section=table_repair.target_section,
            pattern_ids=table_repair.pattern_ids,
            locator=table_repair.locator,
            replacement_text=table_repair.replacement_text,
            pre_fingerprint=table_repair.pre_fingerprint,
            post_fingerprint=table_repair.post_fingerprint,
            pattern_sha256=table_repair.pattern_sha256,
        )
        registered = digest_corpus(GovernanceCorpus(patterns=self.patterns), (table_repair,))
        registered_ids = {item["finding_id"] for item in registered["findings"]}
        self.assertNotIn("skill_table_gap:AP_TEST", registered_ids)

        unknown_patterns = (
            _pattern("AP_OTHER", "HP_OTHER", category="anti_pattern", language="other"),
            _pattern("HP_OTHER", "AP_OTHER", category="healthy_pattern", language="other"),
        )
        unknown = digest_corpus(GovernanceCorpus(patterns=unknown_patterns), ())
        unknown_ids = {item["finding_id"] for item in unknown["findings"]}
        self.assertIn("missing_specialist:AP_OTHER", unknown_ids)
        self.assertNotIn("missing_specialist:HP_OTHER", unknown_ids)

    def test_stale_pointer_requires_both_absence_and_normalized_reference(self) -> None:
        pointer = _doc(
            "symbol_game", "pointer.md", r"source: _intelligence\symbol_game\runs\receipt.json"
        )
        present = digest_corpus(GovernanceCorpus(stale_pointers=(pointer,)), ())
        self.assertEqual(present["findings"], [])

        absent = digest_corpus(
            GovernanceCorpus(absent_corpora=(RUNS_CORPUS,), stale_pointers=(pointer,)),
            (),
        )
        self.assertEqual(absent["findings"][0]["disposition"], "stale_corpus_pointer")

        unrelated = digest_corpus(
            GovernanceCorpus(
                absent_corpora=(RUNS_CORPUS,),
                stale_pointers=(_doc("symbol_game", "pointer.md", "source: elsewhere"),),
            ),
            (),
        )
        self.assertEqual(unrelated["findings"], [])

    def test_harvest_custody_requires_object_key_and_tolerates_non_mapping_roots(self) -> None:
        corpus = GovernanceCorpus(
            harvest_receipts=(
                _doc("harvest", "list.json", '[{"merkle_roots": {}}]'),
                _doc("harvest", "missing.json", '{"other": 1}'),
                _doc("harvest", "scalar-roots.json", '{"merkle_roots": "not-a-map"}'),
            )
        )

        receipt = digest_corpus(corpus, ())

        self.assertEqual(len(receipt["findings"]), 1)
        self.assertEqual(receipt["findings"][0]["finding_id"], "custody:scalar-roots.json")
        self.assertEqual(receipt["findings"][0]["evidence"], [])


if __name__ == "__main__":
    unittest.main()
