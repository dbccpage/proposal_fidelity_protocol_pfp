"""Digest and apply cycle for governance corpora. AuthorityEffect: None."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from operads.application.governance_digest.apply_proposals import (
    apply_proposals,
)
from operads.application.governance_digest.digest_corpus import (
    canonical_json,
    digest_corpus,
)
from operads.application.governance_digest.receipt_path import (
    receipt_destination_allowed,
    write_receipt,
)
from operads.application.governance_digest.repairs import live_repairs
from operads.application.governance_digest.textops import (
    apply_edits,
    measure,
    sha256_text,
)
from operads.domain.governance_digest.records import (
    EditLocator,
    GovernanceCorpus,
    PatternDoc,
    Proposal,
    RepairSpec,
    TextDoc,
)
from operads.infrastructure.fs.governance_corpus_adapter import (
    FsGovernanceCorpusAdapter,
)

BOILER = (
    "- **Clean Architecture**: Inward dependencies maintained across operations and domain roots.\n"
    "- **Four-Host Parity**: State changes synchronized across `.agents`, `.claude`, `.codex`, and `.grok`.\n"
    "- **Claim Discipline**: Narrowest defensible claims recorded without unmechanized proof hype.\n"
)
LESSON = {
    "source_path": "pkg/a.py",
    "source_revision": "sha256:abc",
    "failed_claim": "the integral was treated as a number with no carrier",
    "counterexample": "f(x)=x on an unnamed domain",
    "cause": "the carrier was omitted",
    "correction": "name the carrier and the measure",
    "verification": "the regression fixture admits only the declared carrier",
    "applicability": "definite integrals over an explicit carrier",
    "exceptions": "a refused missing-carrier prompt is not this lesson",
}


def _doc(corpus: str, path: str, text: str) -> TextDoc:
    return TextDoc(corpus, path, sha256_text(text), text)


def _pattern(
    pattern_id: str,
    dual: str,
    *,
    category: str = "anti_pattern",
    language: str = "python",
    detection: str = "needle",
    stem: str | None = None,
) -> PatternDoc:
    name = stem or f"{pattern_id}_name"
    return PatternDoc(
        relative_path=f".agents/anti_pattern/{language}/{name}.md",
        sha256=sha256_text(pattern_id + dual),
        pattern_id=pattern_id,
        name=name,
        category=category,
        language=language,
        dual_pattern=dual,
        frontmatter_keys=(
            "pattern_id",
            "name",
            "category",
            "operad_type",
            "operad_source_colours",
            "operad_target_colour",
            "operad_arity",
            "operad_residual",
            "dual_pattern",
            "language",
            "authority_effect",
        ),
        detection_text=detection,
    )


def _pair(anti: str, healthy: str, healthy_stem: str, anti_stem: str, language: str = "python") -> tuple[PatternDoc, PatternDoc]:
    return (
        _pattern(anti, healthy_stem, language=language, stem=anti_stem),
        _pattern(
            healthy,
            anti_stem,
            category="healthy_pattern",
            language=language,
            detection="",
            stem=healthy_stem,
        ),
    )


RULE = (
    "# Rule\n\n"
    "## Alpha (`RULE_A`)\n\n"
    "alpha body\n\n"
    "## Beta (`RULE_B`)\n\n"
    "beta body\n\n"
    "## Gamma (`RULE_C`)\n\n"
    "end\n"
)
RULE_PATH = ".agents/rules/fixture_rule.md"
CITE_A = "\n> **Pattern estate:** `AP_A` / `HP_A` (`.agents/anti_pattern/python/`).\n\n"
CITE_B = "\n> **Pattern estate:** `AP_B` / `HP_B` (`.agents/anti_pattern/python/`).\n\n"


def _bind(
    repair_id: str,
    edit_kind: str,
    target_path: str,
    target_section: str,
    pattern_ids: tuple[str, ...],
    locator: EditLocator,
    replacement: str,
    text: str,
    patterns: tuple[PatternDoc, ...],
) -> RepairSpec:
    pre = measure(text, edit_kind=edit_kind, target_section=target_section, locator=locator, replacement_text=replacement)
    edited, error = apply_edits(text, [(locator, replacement)])
    if edited is None:
        raise AssertionError(error)
    post = measure(
        edited, edit_kind=edit_kind, target_section=target_section, locator=locator, replacement_text=replacement
    )
    sha = {pattern.pattern_id: pattern.sha256 for pattern in patterns}
    return RepairSpec(
        repair_id=repair_id,
        edit_kind=edit_kind,
        target_path=target_path,
        target_section=target_section,
        pattern_ids=pattern_ids,
        locator=locator,
        replacement_text=replacement,
        pre_fingerprint=pre,
        post_fingerprint=post,
        pattern_sha256=tuple((pattern_id, sha[pattern_id]) for pattern_id in pattern_ids),
    )


class MemoryStore:
    def __init__(self, files: dict[str, str]) -> None:
        self.files = dict(files)
        self.canon_writes: list[str] = []

    def read(self, relative_path: str) -> str | None:
        return self.files.get(relative_path)

    def write(self, relative_path: str, text: str) -> None:
        if relative_path.startswith(".agents/"):
            self.canon_writes.append(relative_path)
        self.files[relative_path] = text


def _proposal(spec: RepairSpec, file_text: str) -> Proposal:
    return Proposal(
        proposal_id=spec.repair_id,
        repair_id=spec.repair_id,
        target_path=spec.target_path,
        target_section=spec.target_section,
        edit_kind=spec.edit_kind,
        expected_target_hash=sha256_text(file_text),
        replacement_text=spec.replacement_text,
        evidence_ids=spec.pattern_ids + (spec.pre_fingerprint, spec.post_fingerprint),
        locator=spec.locator,
        pattern_ids=spec.pattern_ids,
    )


class GovernanceDigestTests(unittest.TestCase):
    def _corpus(self, rule_text: str = RULE, extra_rules: tuple[TextDoc, ...] = (), **kwargs: object) -> GovernanceCorpus:
        anti, healthy = _pair("AP_A", "HP_A", "HP_A_stem", "AP_A_stem")
        base = {
            "patterns": (anti, healthy),
            "rules": (_doc("rules", RULE_PATH, rule_text),) + extra_rules,
        }
        base.update(kwargs)
        return GovernanceCorpus(**base)  # type: ignore[arg-type]

    def _cite(self, text: str = RULE) -> RepairSpec:
        anti, healthy = _pair("AP_A", "HP_A", "HP_A_stem", "AP_A_stem")
        return _bind(
            "cite-a",
            "cite_pattern",
            RULE_PATH,
            "RULE_A",
            ("AP_A", "HP_A"),
            EditLocator("insert_before", anchor_text="## Beta (`RULE_B`)"),
            CITE_A,
            text,
            (anti, healthy),
        )

    def test_citation_cycle_and_unrelated_edit(self) -> None:
        spec = self._cite()
        corpus = self._corpus()
        first = digest_corpus(corpus, (spec,))
        self.assertEqual([item["proposal_id"] for item in first["proposals"]], ["cite-a"])
        self.assertEqual(first["proposals"][0]["edit_kind"], "cite_pattern")
        dispositions = {item["finding_id"]: item["disposition"] for item in first["findings"]}
        self.assertEqual(dispositions["repair_pending:cite-a"], "repair_pending")

        store = MemoryStore({RULE_PATH: RULE})
        applied = apply_proposals(store, [_proposal(spec, RULE)], (spec,))
        self.assertEqual(applied["outcomes"][0]["status"], "applied")
        self.assertEqual(store.canon_writes, [RULE_PATH])
        self.assertIn("`AP_A`", store.files[RULE_PATH])

        edited = store.files[RULE_PATH]
        second = digest_corpus(self._corpus(rule_text=edited), (spec,))
        self.assertEqual(second["proposals"], [])
        dispositions = {item["finding_id"]: item["disposition"] for item in second["findings"]}
        self.assertEqual(dispositions["already_codified:cite-a"], "already_codified")

        drifted = edited.replace("alpha body", "alpha body drifted", 1)
        third = digest_corpus(self._corpus(rule_text=drifted), (spec,))
        self.assertEqual(third["proposals"], [])
        dispositions = {item["finding_id"]: item["disposition"] for item in third["findings"]}
        self.assertEqual(dispositions["anchor_changed:cite-a"], "anchor_changed")

    def test_two_proposals_for_one_file_write_once(self) -> None:
        anti_a, healthy_a = _pair("AP_A", "HP_A", "HP_A_stem", "AP_A_stem")
        anti_b, healthy_b = _pair("AP_B", "HP_B", "HP_B_stem", "AP_B_stem")
        spec_a = self._cite()
        spec_b = _bind(
            "cite-b",
            "cite_pattern",
            RULE_PATH,
            "RULE_B",
            ("AP_B", "HP_B"),
            EditLocator("insert_before", anchor_text="## Gamma (`RULE_C`)"),
            CITE_B,
            RULE,
            (anti_b, healthy_b),
        )
        corpus = GovernanceCorpus(
            patterns=(anti_a, healthy_a, anti_b, healthy_b),
            rules=(_doc("rules", RULE_PATH, RULE),),
        )
        receipt = digest_corpus(corpus, (spec_a, spec_b))
        self.assertEqual([item["proposal_id"] for item in receipt["proposals"]], ["cite-a", "cite-b"])
        self.assertEqual(receipt["proposals"][0]["expected_target_hash"], receipt["proposals"][1]["expected_target_hash"])
        store = MemoryStore({RULE_PATH: RULE})
        result = apply_proposals(
            store,
            [_proposal(spec_a, RULE), _proposal(spec_b, RULE)],
            (spec_a, spec_b),
        )
        self.assertEqual(store.canon_writes, [RULE_PATH])
        self.assertTrue(all(item["status"] == "applied" for item in result["outcomes"]))
        self.assertIn("`AP_A`", store.files[RULE_PATH])
        self.assertIn("`AP_B`", store.files[RULE_PATH])

    def test_conflicting_edits_leave_the_file_unchanged(self) -> None:
        text = "AAABBB"
        left_locator = EditLocator("replace", old_text="AAAB")
        right_locator = EditLocator("replace", old_text="ABBB")
        left = RepairSpec(
            repair_id="left",
            edit_kind="replace_link",
            target_path=".agents/rules/overlap.md",
            target_section="s",
            pattern_ids=("AP_A",),
            locator=left_locator,
            replacement_text="LEFT",
            pre_fingerprint=measure(
                text,
                edit_kind="replace_link",
                target_section="s",
                locator=left_locator,
                replacement_text="LEFT",
            ),
            post_fingerprint="post",
            pattern_sha256=(("AP_A", "hash"),),
        )
        right = RepairSpec(
            repair_id="right",
            edit_kind="replace_link",
            target_path=".agents/rules/overlap.md",
            target_section="s",
            pattern_ids=("AP_A",),
            locator=right_locator,
            replacement_text="RIGHT",
            pre_fingerprint=measure(
                text,
                edit_kind="replace_link",
                target_section="s",
                locator=right_locator,
                replacement_text="RIGHT",
            ),
            post_fingerprint="post",
            pattern_sha256=(("AP_A", "hash"),),
        )
        store = MemoryStore({left.target_path: text})
        result = apply_proposals(store, [_proposal(left, text), _proposal(right, text)], (left, right))
        self.assertEqual(store.files[left.target_path], text)
        self.assertEqual(store.canon_writes, [])
        self.assertTrue(all(item["reason"] == "conflicting_edits" for item in result["outcomes"]))

    def test_disallowed_target_is_not_applied(self) -> None:
        spec = self._cite()
        forged = Proposal(
            proposal_id="cite-a",
            repair_id="cite-a",
            target_path=".agents/rules/not_the_owner.md",
            target_section=spec.target_section,
            edit_kind=spec.edit_kind,
            expected_target_hash=sha256_text(RULE),
            replacement_text=spec.replacement_text,
            evidence_ids=spec.pattern_ids,
            locator=spec.locator,
            pattern_ids=spec.pattern_ids,
        )
        store = MemoryStore({forged.target_path: RULE, RULE_PATH: RULE})
        result = apply_proposals(store, [forged], (spec,))
        self.assertEqual(result["outcomes"][0]["status"], "failed")
        self.assertEqual(result["outcomes"][0]["reason"], "target_not_permitted")
        self.assertEqual(store.files[forged.target_path], RULE)
        self.assertEqual(store.canon_writes, [])

    def test_id_outside_the_owner_section_is_not_already_codified(self) -> None:
        spec = self._cite()
        other = _doc("rules", ".agents/rules/other.md", "historical note mentions `AP_A` in passing\n")
        receipt = digest_corpus(self._corpus(extra_rules=(other,)), (spec,))
        dispositions = {item["finding_id"]: item["disposition"] for item in receipt["findings"]}
        self.assertNotEqual(dispositions.get("already_codified:cite-a"), "already_codified")
        self.assertEqual(dispositions["repair_pending:cite-a"], "repair_pending")
        self.assertIn("cite-a", [item["proposal_id"] for item in receipt["proposals"]])

    def test_broken_and_duplicate_pairs_emit_no_proposals(self) -> None:
        broken_anti = _pattern("AP_A", "HP_MISSING", stem="AP_A_stem")
        spec = self._cite()
        receipt = digest_corpus(GovernanceCorpus(patterns=(broken_anti,), rules=(_doc("rules", RULE_PATH, RULE),)), (spec,))
        self.assertEqual(receipt["proposals"], [])
        self.assertTrue(any(row["code"] == "missing_dual" for row in receipt["pair_defects"]))

        first = _pattern("AP_A", "HP_A_stem", stem="AP_A_one")
        second = _pattern("AP_A", "HP_A_stem", stem="AP_A_two")
        duplicated = digest_corpus(
            GovernanceCorpus(patterns=(first, second), rules=(_doc("rules", RULE_PATH, RULE),)),
            (spec,),
        )
        self.assertEqual(duplicated["proposals"], [])
        self.assertTrue(any(row["code"] == "duplicate_pattern_id" for row in duplicated["pair_defects"]))

    def test_missing_repair_target_fails_closed_as_anchor_changed(self) -> None:
        spec = self._cite()
        receipt = digest_corpus(self._corpus(extra_rules=(), rules=()), (spec,))

        self.assertEqual(receipt["proposals"], [])
        finding = next(item for item in receipt["findings"] if item["finding_id"] == "anchor_changed:cite-a")
        self.assertEqual(finding["corpus"], "rules")
        self.assertEqual(finding["reason"], "repair target is not in the snapshot")
        self.assertEqual(finding["evidence"], [{"name": "repair_id", "value": "cite-a"}])

    def test_harvest_receipts_classify_valid_custody_and_ignore_invalid_json(self) -> None:
        valid = _doc(
            "harvest",
            "_intelligence/teamwork/harvest/valid.json",
            json.dumps({"merkle_roots": {"z": "last", "a": "first"}}),
        )
        invalid = _doc("harvest", "_intelligence/teamwork/harvest/invalid.json", "{not-json")

        receipt = digest_corpus(GovernanceCorpus(harvest_receipts=(valid, invalid)), ())

        custody = [item for item in receipt["findings"] if item["disposition"] == "custody_provenance"]
        self.assertEqual(len(custody), 1)
        self.assertEqual(
            custody[0]["evidence"],
            [{"name": "a", "value": "first"}, {"name": "z", "value": "last"}],
        )

    def test_boilerplate_slop_recurrence_lessons_and_absent_corpus(self) -> None:
        session = (
            "# Session\n\n## Touched Artifacts & Files\n\n"
            "- [`a.py`](pkg/a.py)\n\n"
            "## Architectural Invariants & Observational Notes\n\n"
            + BOILER
            + "\n## Comment Slop Audit Status\n"
        )
        other_session = session.replace("[`a.py`](pkg/a.py)", "[`c.py`](pkg/c.py)")
        prefix_only = (
            "# Session\n\n## Touched Artifacts & Files\n\n"
            "- [`nested`](pkg/nested/a.py)\n\n"
            "## Architectural Invariants & Observational Notes\n\n"
            + BOILER
        )
        code_lesson = "\n".join(f"- {key}: `{value}`" for key, value in LESSON.items())
        paper = json.dumps(LESSON)
        incomplete = "- failed_claim: `a claim without the other fields`"
        corpus = GovernanceCorpus(
            documentation=(
                _doc("documentation", ".agents/documentation/sessions/s1.md", session),
                _doc("documentation", ".agents/documentation/sessions/s2.md", session),
                _doc("documentation", ".agents/documentation/sessions/s3.md", other_session),
                _doc("documentation", ".agents/documentation/sessions/prefix.md", prefix_only),
                _doc(
                    "documentation",
                    ".agents/documentation/slop_audit/jcs.md",
                    "- Line 1 [CONVERSATIONAL_AI_ARTIFACT]: `Step 6`",
                ),
                _doc("documentation", ".agents/documentation/sessions/code_lesson.md", code_lesson),
            ),
            handoffs=(_doc("teamwork", ".agents/teamwork/auditor_1/handoff.md", incomplete),),
            paper_reviews=(_doc("core_paper_reviews", "_intelligence/core_paper_reviews/paper.json", paper),),
            absent_corpora=("_intelligence/symbol_game/runs",),
            stale_pointers=(
                _doc(
                    "symbol_game",
                    "_intelligence/symbol_game/runs_synthesis_and_learnings.md",
                    "Source Directory: `_intelligence/symbol_game/runs/`",
                ),
            ),
            patterns=_pair("AP_SQL_001", "HP_SQL_001", "HP_SQL_001_stem", "AP_SQL_001_stem", language="sql"),
        )
        before = tuple(doc.text for doc in corpus.documentation)
        first = digest_corpus(corpus, ())
        second = digest_corpus(corpus, ())
        self.assertEqual(canonical_json(first), canonical_json(second))
        self.assertEqual(before, tuple(doc.text for doc in corpus.documentation))
        self.assertEqual(first["proposals"], [])
        self.assertEqual(first["corpus_absent"], ["_intelligence/symbol_game/runs"])
        noise_kinds = {item["kind"] for item in first["noise"]}
        self.assertIn("session_boilerplate", noise_kinds)
        self.assertIn("slop", noise_kinds)
        boilerplate = [item for item in first["noise"] if item["source"].endswith("s1.md")][0]
        self.assertIn("pkg/a.py", boilerplate["touch_paths"])
        by_id = {item["finding_id"]: item for item in first["findings"]}
        self.assertEqual(by_id["recurring_touch:pkg/a.py"]["disposition"], "recurring_touch_candidate")
        self.assertEqual(by_id["recurring_touch:pkg/a.py"]["evidence"][0]["value"], "unknown")
        self.assertNotIn("recurring_touch:pkg", by_id)
        self.assertNotIn("recurring_touch:pkg/nested/a.py", by_id)
        self.assertNotIn("recurring_touch:pkg/c.py", by_id)
        self.assertEqual(by_id["lesson_candidate:.agents/documentation/sessions/code_lesson.md"]["disposition"], "lesson_candidate")
        paper_finding = by_id["lesson_candidate:_intelligence/core_paper_reviews/paper.json"]
        evidence = {item["name"]: item["value"] for item in paper_finding["evidence"]}
        self.assertEqual(evidence["counterexample"], LESSON["counterexample"])
        self.assertEqual(evidence["verification"], LESSON["verification"])
        self.assertEqual(evidence["applicability"], LESSON["applicability"])
        self.assertEqual(
            by_id["lesson_incomplete:.agents/teamwork/auditor_1/handoff.md"]["disposition"],
            "lesson_incomplete",
        )
        self.assertEqual(
            by_id["stale_corpus_pointer:_intelligence/symbol_game/runs_synthesis_and_learnings.md"]["disposition"],
            "stale_corpus_pointer",
        )
        self.assertIn("rule_unlinked:AP_SQL_001", by_id)
        self.assertTrue(all(item["proposal_id"] != "rule_unlinked:AP_SQL_001" for item in first["proposals"]))

    def test_digest_of_a_temp_tree_does_not_modify_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            session = workspace / ".agents" / "documentation" / "sessions"
            session.mkdir(parents=True)
            target = session / "one.md"
            target.write_text("# Session\n\nAuthorityEffect: None.\n", encoding="utf-8", newline="\n")
            before = target.read_bytes()
            digest_corpus(FsGovernanceCorpusAdapter(workspace).load(), ())
            self.assertEqual(target.read_bytes(), before)

    def test_receipt_destination_refuses_governed_roots(self) -> None:
        self.assertFalse(receipt_destination_allowed(".agents/out.json"))
        self.assertFalse(receipt_destination_allowed("runs/../_intelligence/out.json"))
        self.assertTrue(receipt_destination_allowed("runs/governance_digest.json"))
        with tempfile.TemporaryDirectory() as tmp:
            forbidden = str(Path(tmp) / ".agents" / "out.json")
            with self.assertRaises(PermissionError):
                write_receipt(forbidden, "{}\n")
            self.assertFalse(Path(forbidden).exists())
            allowed = str(Path(tmp) / "runs" / "out.json")
            write_receipt(allowed, "{}\n")
            self.assertTrue(Path(allowed).is_file())

    def test_receipt_destination_is_judged_below_the_repository_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            # A worktree checked out under .claude/worktrees/ inside another repository.
            root = Path(tmp) / "repo" / ".claude" / "worktrees" / "w"
            self.assertTrue(receipt_destination_allowed(str(root / "runs" / "d.json"), root))
            self.assertFalse(receipt_destination_allowed(str(root / ".agents" / "d.json"), root))
            self.assertFalse(receipt_destination_allowed(str(root / "runs" / ".." / "_intelligence" / "d.json"), root))
            escaped = str(root / ".." / ".." / ".." / ".codex" / "d.json")
            self.assertFalse(receipt_destination_allowed(escaped, root))
            outside = str(Path(tmp) / "elsewhere" / ".claude" / "d.json")
            self.assertFalse(receipt_destination_allowed(outside, root))
            write_receipt(str(root / "runs" / "d.json"), "{}\n", root)
            self.assertTrue((root / "runs" / "d.json").is_file())

    def test_partial_mirror_is_repaired_on_the_next_apply(self) -> None:
        spec = self._cite()
        store = MemoryStore({RULE_PATH: RULE})
        first = apply_proposals(store, [_proposal(spec, RULE)], (spec,), fail_mirror_hosts=frozenset({".codex"}))
        self.assertEqual(first["outcomes"][0]["status"], "partial")
        self.assertNotIn(".codex/rules/fixture_rule.md", store.files)
        self.assertIn(".claude/rules/fixture_rule.md", store.files)
        second = apply_proposals(
            store,
            [_proposal(spec, RULE)],
            (spec,),
        )
        self.assertEqual(second["outcomes"][0]["status"], "applied")
        self.assertEqual(second["outcomes"][0]["reason"], "mirror_repair")
        self.assertEqual(store.files[".codex/rules/fixture_rule.md"], store.files[RULE_PATH])
        self.assertEqual(store.canon_writes, [RULE_PATH])

    def test_drifted_span_is_not_applied(self) -> None:
        spec = self._cite()
        drifted = RULE.replace("alpha body", "alpha body drifted", 1)
        store = MemoryStore({RULE_PATH: drifted})
        result = apply_proposals(store, [_proposal(spec, drifted)], (spec,))
        self.assertEqual(result["outcomes"][0]["status"], "failed")
        self.assertEqual(result["outcomes"][0]["reason"], "anchor_changed")
        self.assertEqual(store.files[RULE_PATH], drifted)
        self.assertEqual(store.canon_writes, [])

    def test_jsonl_records_keep_distinct_finding_ids(self) -> None:
        first = dict(LESSON)
        second = dict(LESSON)
        second["counterexample"] = "a second carrier"
        text = json.dumps(first) + "\n" + json.dumps(second) + "\n"
        corpus = GovernanceCorpus(
            omc_records=(_doc("omc_dags", "_intelligence/omc_dags/batch.jsonl", text),),
        )
        receipt = digest_corpus(corpus, ())
        ids = [item["finding_id"] for item in receipt["findings"]]
        self.assertEqual(
            ids,
            [
                "lesson_candidate:_intelligence/omc_dags/batch.jsonl#1",
                "lesson_candidate:_intelligence/omc_dags/batch.jsonl#2",
            ],
        )

    def test_empty_receipt_repairs_codified_mirrors(self) -> None:
        spec = self._cite()
        edited, error = apply_edits(RULE, [(spec.locator, spec.replacement_text)])
        self.assertIsNotNone(edited)
        assert edited is not None
        store = MemoryStore({RULE_PATH: edited})
        result = apply_proposals(store, (), (spec,))
        self.assertEqual(store.canon_writes, [])
        self.assertEqual(store.files[".claude/rules/fixture_rule.md"], edited)
        self.assertEqual(store.files[".codex/rules/fixture_rule.md"], edited)
        self.assertEqual(store.files[".grok/rules/fixture_rule.md"], edited)
        self.assertEqual(result["outcomes"][0]["status"], "applied")
        self.assertEqual(result["outcomes"][0]["reason"], "mirror_reconciled")
        again = apply_proposals(store, (), (spec,))
        self.assertEqual(again["outcomes"], [])

    def test_checked_in_repairs_match_a_stored_fingerprint(self) -> None:
        specs = live_repairs()
        self.assertEqual(len(specs), 6)
        patterns_dir = Path(".agents/patterns") if Path(".agents/patterns").is_dir() else Path(".agents/anti_pattern")
        pattern_text: dict[str, str] = {}
        for path in patterns_dir.rglob("*.md"):
            with path.open(encoding="utf-8", newline="") as handle:
                text = handle.read()
            for line in text.splitlines():
                if line.startswith("pattern_id:"):
                    pattern_text[line.split(":", 1)[1].strip()] = text
                    break
        for spec in specs:
            with open(spec.target_path, encoding="utf-8", newline="") as handle:
                text = handle.read()
            current = measure(
                text,
                edit_kind=spec.edit_kind,
                target_section=spec.target_section,
                locator=spec.locator,
                replacement_text=spec.replacement_text,
            )
            self.assertIn(current, {spec.pre_fingerprint, spec.post_fingerprint})
            for pattern_id, expected in spec.pattern_sha256:
                self.assertEqual(sha256_text(pattern_text[pattern_id]), expected)


if __name__ == "__main__":
    unittest.main()
