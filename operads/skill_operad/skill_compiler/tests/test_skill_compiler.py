#!/usr/bin/env python3
"""Unit tests for skill_compiler episode/resolve/promote (AuthorityEffect: None)."""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest import mock

from skill_compiler import budget_gate, resolve
from skill_compiler.budget_gate import load_exceptions, valid_exception
from skill_compiler.episode import append_episode, load_episodes, make_episode
from skill_compiler.promote import append_ooutwire_entry
from skill_compiler.resolve import resolve_text

PKG = Path(__file__).resolve().parents[1]


def _mini_repo(tmp: Path) -> Path:
    """Scaffold minimal synthetic tree for resolve package discovery and ooutwire testing."""
    (tmp / ".git").mkdir()
    (tmp / ".agents" / "skills" / "autoskill").mkdir(parents=True)
    (tmp / ".agents" / "skills" / "autoskill" / "SKILL.md").write_text(
        "---\nname: autoskill\n---\n", encoding="utf-8"
    )
    (tmp / ".agents" / "skills" / "blackrod").mkdir(parents=True)
    (tmp / ".agents" / "skills" / "blackrod" / "SKILL.md").write_text(
        "---\nname: blackrod\n---\n", encoding="utf-8"
    )
    (tmp / ".agents" / "skills" / "ooutwire").mkdir(parents=True)
    (
        tmp / ".agents" / "skills" / "ooutwire" / "proposed_skills_register.md"
    ).write_text(
        "---\ntitle: proposed_skills_register\n---\n\n"
        "## Session landings test\n\n"
        "### Entry 0200: `seed`\n\n- **Status:** PROPOSED\n",
        encoding="utf-8",
    )
    (tmp / ".agents" / "operad").mkdir(parents=True)
    (tmp / ".agents" / "operad" / "operad_signature.json").write_text(
        json.dumps(
            {
                "colours": {},
                "identities": [],
                "operations": [{"skill_id": "blackrod", "name": "blackrod"}],
            }
        ),
        encoding="utf-8",
    )
    # Point resolve at routes.yaml from package
    routes_src = (
        PKG.parent / "yaml" / "routes.yaml"
        if (PKG.parent / "yaml" / "routes.yaml").is_file()
        else PKG / "routes.yaml"
    )
    (tmp / ".agents" / "operad" / "skill_compiler").mkdir(parents=True, exist_ok=True)
    if routes_src.is_file():
        (tmp / ".agents" / "operad" / "skill_compiler" / "routes.yaml").write_text(
            routes_src.read_text(encoding="utf-8"), encoding="utf-8"
        )
    return tmp


class EpisodeTests(unittest.TestCase):
    def test_append_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".git").mkdir()
            (root / ".agents").mkdir()
            ep = make_episode(
                source="test",
                signal="user said always use LF",
                proposed_invariant="Rust sources use LF only",
                confidence="HIGH",
            )
            path = append_episode(root, ep)
            self.assertTrue(path.is_file())
            rows = load_episodes(root)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["id"], ep["id"])
            self.assertEqual(rows[0]["schema"], "omega.skill_compiler.episode.v1")

    def test_append_partitions_by_episode_utc_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".git").mkdir()
            (root / ".agents").mkdir()
            ep = make_episode(
                source="test",
                signal="a correction crossed the UTC date boundary",
                proposed_invariant="Episode filenames bind the episode UTC date",
            )
            ep["ts"] = "2026-08-14T02:50:44.0842698Z"
            path = append_episode(root, ep)
            self.assertEqual(path.name, "2026-08-14.jsonl")

    def test_append_refuses_invalid_or_naive_episode_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".git").mkdir()
            (root / ".agents").mkdir()
            for timestamp in ("not-a-timestamp", "2026-08-14T02:50:44"):
                ep = make_episode(
                    source="test",
                    signal="timestamp custody must fail closed",
                    proposed_invariant="Episode timestamps include a UTC offset",
                )
                ep["ts"] = timestamp
                with self.assertRaises(ValueError):
                    append_episode(root, ep)

    def test_persisted_episode_rows_match_their_utc_day_filename(self) -> None:
        repo_root = PKG.parents[2]
        episode_root = repo_root / "runs" / "skill_compiler" / "episodes"
        for path in sorted(episode_root.glob("*.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                raw_ts = row.get("ts") or row.get("timestamp_utc") or ""
                timestamp = datetime.fromisoformat(
                    raw_ts.replace("Z", "+00:00")
                ).astimezone(timezone.utc)
                self.assertEqual(timestamp.strftime("%Y-%m-%d"), path.stem)


class CanonicalPlacementTests(unittest.TestCase):
    def test_compiler_and_eval_bank_have_one_canonical_home(self) -> None:
        repo_root = PKG.parents[2]
        self.assertTrue((repo_root / "omega_engine_operads" / "skill_operad" / "skill_compiler").is_dir())
        self.assertTrue((repo_root / "omega_engine_operads" / "skill_operad" / "skill_compiler" / "eval_bank" / "cases.json").is_file())
        for host in (".agents", ".antigravity", ".claude", ".codex", ".gemini", ".grok"):
            self.assertFalse(
                (repo_root / host / "operad" / "skill_compiler").exists(),
                f"{host} carries a second compiler implementation",
            )
            self.assertFalse(
                (repo_root / host / "evals" / "skills" / "cases.json").exists(),
                f"{host} carries a legacy eval-bank authority",
            )


class ResolveTests(unittest.TestCase):
    def test_live_routes_parse_without_optional_pyyaml(self) -> None:
        routes_file = (
            PKG.parent / "yaml" / "routes.yaml"
            if (PKG.parent / "yaml" / "routes.yaml").is_file()
            else PKG / "routes.yaml"
        )
        with mock.patch.object(resolve, "yaml", None):
            routes = resolve._load_routes(routes_file)
        self.assertIn(
            "canonical_value_validation",
            {route["id"] for route in routes["shared_contracts"]},
        )

    def test_noise_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = _mini_repo(Path(td))
            r = resolve_text(root, signal="", proposed_invariant="")
            self.assertEqual(r.disposition, "NOISE")

    def test_shared_dda(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = _mini_repo(Path(td))
            r = resolve_text(
                root,
                signal="DDA trace missing AE=None check",
                proposed_invariant="Always check DDA AuthorityEffect None",
            )
            self.assertEqual(r.disposition, "SHARED_CONTRACT")
            self.assertIn("dda", r.matched_rules[0].lower() + r.target.lower())

    def test_historical_pr_immunity_precedes_generic_authority_route(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = _mini_repo(Path(td))
            r = resolve_text(
                root,
                signal=(
                    "Mine the historical pull-request conversation DAG for anti-morphisms with AuthorityEffect None"
                ),
                proposed_invariant=(
                    "Bind every PR and later correction before nominating a candidate"
                ),
            )
            self.assertEqual(r.disposition, "SHARED_CONTRACT")
            self.assertEqual(r.matched_rules, ["historical_pr_immunity"])
            self.assertEqual(
                r.target,
                ".agents/skills/_shared/historical_pr_immunity_campaign.md",
            )

    def test_historical_pr_immunity_route_refuses_substring_and_separator_noise(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = _mini_repo(Path(td))
            for signal in (
                "A proposed anti-morphism needs a detector.",
                "Review an anti-morphism proposal.",
                "Mine historical pullXrequest data.",
                "Inspect a conversationdagger trace.",
                "Review a historical pullrequester artifact.",
                "Pullrequester immunity is unrelated.",
                "An ahistorical PR immunity claim is unrelated.",
            ):
                r = resolve_text(
                    root,
                    signal=signal,
                    proposed_invariant="Keep the routing grammar exact.",
                )
                self.assertNotIn("historical_pr_immunity", r.matched_rules)

    def test_historical_pr_immunity_route_matches_both_episode_shapes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = _mini_repo(Path(td))
            for signal in (
                (
                    "Historical pull-request review must mine the bound prompt, response, and conversation DAG."
                ),
                (
                    "The historical PR immunity episode was misrouted while classifying an anti-morphism."
                ),
                "Review historical PR immunity evidence.",
                "Mine historical pull requests for correction edges.",
                "Mine PRs for anti-morphisms.",
            ):
                r = resolve_text(
                    root,
                    signal=signal,
                    proposed_invariant="Bind exact PR evidence before nomination.",
                )
                self.assertEqual(r.matched_rules, ["historical_pr_immunity"])

    def test_code_gate_budget(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = _mini_repo(Path(td))
            r = resolve_text(
                root,
                signal="skill bloat",
                proposed_invariant="Enforce 300-line hot-context budget on SKILL.md",
            )
            self.assertEqual(r.disposition, "CODE_GATE")

    def test_existing_op(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = _mini_repo(Path(td))
            r = resolve_text(
                root,
                signal="blackrod should reject fake tests",
                proposed_invariant="Update blackrod report schema",
            )
            self.assertEqual(r.disposition, "EXISTING_OP")
            self.assertEqual(r.skill_id, "blackrod")

    def test_new_skill_requires_buckets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = _mini_repo(Path(td))
            r = resolve_text(
                root,
                signal="create a new skill package",
                proposed_invariant=(
                    "New skill: when user says /foo trigger, run workflow steps, "
                    "eval with fixtures, authority None tool boundary"
                ),
            )
            self.assertEqual(r.disposition, "NEW_SKILL")


class PromoteTests(unittest.TestCase):
    def test_ooutwire_entry(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = _mini_repo(Path(td))
            out = append_ooutwire_entry(
                root,
                skill_name="goo-phase1-test-skill",
                description="Test ooutwire landing from skill_compiler",
                proposed_by="unit-test",
            )
            self.assertTrue(out["ok"])
            reg = (
                root / ".agents/skills/ooutwire/proposed_skills_register.md"
            ).read_text(encoding="utf-8")
            self.assertIn("goo-phase1-test-skill", reg)
            self.assertIn(out["entry"], reg)

            # Robust field assertion parsing status using regex
            match = re.search(r"Status:\s*(.+)", reg)
            self.assertIsNotNone(match, "Failed to find 'Status:' field in register")
            if match:
                status_val = match.group(1).replace("*", "").strip()
                self.assertIn("PROPOSED", status_val)


class BudgetGateFallbackTests(unittest.TestCase):
    def test_load_exceptions_without_pyyaml(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "budget_exceptions.yaml"
            path.write_text(
                """exceptions:
  oversize:
    approved: true
    expires: 2026-09-01
    reason: "temporary split"
    max_lines: 450
    max_bytes: 24576
""",
                encoding="utf-8",
            )
            with mock.patch.object(budget_gate, "yaml", None):
                exceptions = load_exceptions(path)

            self.assertEqual(
                exceptions,
                {
                    "oversize": {
                        "approved": True,
                        "expires": "2026-09-01",
                        "reason": "temporary split",
                        "max_lines": 450,
                        "max_bytes": 24576,
                    }
                },
            )

    def test_load_exceptions_without_pyyaml_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "budget_exceptions.yaml"
            path.write_text("exceptions:\n  oversize: [true]\n", encoding="utf-8")
            with (
                mock.patch.object(budget_gate, "yaml", None),
                self.assertRaisesRegex(
                    ValueError, "unsupported budget exceptions syntax"
                ),
            ):
                load_exceptions(path)

    def test_inline_comment_does_not_make_false_approval_truthy(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "budget_exceptions.yaml"
            path.write_text(
                "exceptions:\n  oversize:\n    approved: false # denied\n",
                encoding="utf-8",
            )
            with mock.patch.object(budget_gate, "yaml", None):
                exceptions = load_exceptions(path)

            self.assertIs(exceptions["oversize"]["approved"], False)

    def test_non_boolean_approval_values_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "budget_exceptions.yaml"
            for raw_value in ("no", "off", '"false"', '"true"'):
                with self.subTest(raw_value=raw_value):
                    path.write_text(
                        "exceptions:\n"
                        "  oversize:\n"
                        f"    approved: {raw_value}\n"
                        "    expires: 2099-01-01\n",
                        encoding="utf-8",
                    )
                    with mock.patch.object(budget_gate, "yaml", None):
                        exception = load_exceptions(path)["oversize"]

                    allowed, _ = valid_exception(
                        "oversize", exception, today=date(2026, 8, 17)
                    )
                    self.assertFalse(allowed)



class BudgetExceptionApprovalTests(unittest.TestCase):
    """An exception may raise the budget only if it is approved and unexpired.

    `valid_exception` was already well tested. Nothing tested that
    `check_budgets` actually CALLS it, and it did not when the raise was large
    enough: the exception's limits were adopted first, which put the skill back
    under its own raised limit, so the over-budget branch holding the approval
    check never ran. An unapproved or expired exception granted itself the
    raise.
    """

    OVERSIZE = "x" * 4000 + "\n" + ("line\n" * 200)

    def _repo(self, td: str) -> Path:
        root = Path(td)
        skill = root / ".agents" / "skills" / "oversize"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(self.OVERSIZE, encoding="utf-8")
        return root

    def _run(self, root: Path, exceptions: dict) -> int:
        return budget_gate.check_budgets(
            root, ["oversize"], max_lines=10, max_bytes=100,
            exceptions=exceptions, today=date(2026, 8, 27),
        )

    def test_an_unapproved_exception_cannot_raise_the_budget(self) -> None:
        """Mutation: adopt exc limits before checking approval -> returns 0."""
        with tempfile.TemporaryDirectory() as td:
            root = self._repo(td)
            rc = self._run(root, {"oversize": {
                "max_lines": 100000, "max_bytes": 10000000,
                "approved": False, "expires": "2099-01-01",
            }})
            self.assertEqual(rc, 1, "an unapproved exception raised the budget")

    def test_an_expired_exception_cannot_raise_the_budget(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = self._repo(td)
            rc = self._run(root, {"oversize": {
                "max_lines": 100000, "max_bytes": 10000000,
                "approved": True, "expires": "2001-01-01",
            }})
            self.assertEqual(rc, 1, "an expired exception raised the budget")

    def test_an_exception_missing_an_expiry_cannot_raise_the_budget(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = self._repo(td)
            rc = self._run(root, {"oversize": {
                "max_lines": 100000, "max_bytes": 10000000, "approved": True,
            }})
            self.assertEqual(rc, 1, "an exception with no expiry raised the budget")

    def test_an_approved_unexpired_exception_does_raise_the_budget(self) -> None:
        """Negative control.

        Without it, a gate that refused every exception would pass all three
        tests above and look correct while breaking the mechanism entirely.
        """
        with tempfile.TemporaryDirectory() as td:
            root = self._repo(td)
            rc = self._run(root, {"oversize": {
                "max_lines": 100000, "max_bytes": 10000000,
                "approved": True, "expires": "2099-01-01",
            }})
            self.assertEqual(rc, 0, "a valid exception was refused")

    def test_no_exception_still_breaches(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = self._repo(td)
            self.assertEqual(self._run(root, {}), 1)

    def test_a_missing_governed_skill_is_a_breach(self) -> None:
        """A deleted governed skill must not turn the enforcement gate green."""
        with tempfile.TemporaryDirectory() as td:
            rc = budget_gate.check_budgets(
                Path(td), ["missing"], max_lines=10, max_bytes=100,
                exceptions={}, today=date(2026, 8, 27),
            )
            self.assertEqual(rc, 1, "missing governed SKILL.md was silently skipped")

    def test_a_skill_within_budget_passes(self) -> None:
        """The other negative control: the gate must still say yes to a small file."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            skill = root / ".agents" / "skills" / "tiny"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("ok\n", encoding="utf-8")
            rc = budget_gate.check_budgets(
                root, ["tiny"], max_lines=10, max_bytes=100,
                exceptions={}, today=date(2026, 8, 27),
            )
            self.assertEqual(rc, 0)


class BudgetGateHelpers(unittest.TestCase):
    """The branches beneath the budget gate's happy path.

    Every one of these is a way the gate can be handed something it did not
    expect. A loader that returns `{}` on a malformed file, rather than
    raising, is a gate that reports every skill within budget because it read
    no budgets at all.

    AuthorityEffect: None.
    """

    # -- repo_root_from -----------------------------------------------------

    def test_repo_root_is_the_nearest_ancestor_with_git_and_agents(self) -> None:
        """Mutation: return `Path.cwd()` unconditionally and this fails."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            (root / ".git").mkdir()
            (root / ".agents").mkdir()
            deep = root / "a" / "b" / "c"
            deep.mkdir(parents=True)

            self.assertEqual(budget_gate.repo_root_from(deep), root)

    def test_repo_root_requires_both_markers_not_either(self) -> None:
        """A `.git` alone is any clone; `.agents` is what makes it this repo.

        Mutation: change the `and` to an `or` and this fails.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            (root / ".git").mkdir()  # no .agents
            deep = root / "a"
            deep.mkdir()

            self.assertNotEqual(budget_gate.repo_root_from(deep), root)

    # -- count_lines --------------------------------------------------------

    def test_an_empty_file_counts_zero_lines(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "empty.md"
            path.write_text("", encoding="utf-8")

            self.assertEqual(budget_gate.count_lines(path), 0)

    def test_a_final_line_without_a_newline_still_counts(self) -> None:
        """Otherwise a 300-line file ending without a newline reads as 299.

        Mutation: drop the `+ (0 if text.endswith(...))` term and this fails.
        """
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "f.md"
            path.write_text("a\nb\nc", encoding="utf-8")

            self.assertEqual(budget_gate.count_lines(path), 3)

    def test_a_trailing_newline_does_not_add_a_phantom_line(self) -> None:
        """The paired control for the test above."""
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "f.md"
            path.write_text("a\nb\nc\n", encoding="utf-8")

            self.assertEqual(budget_gate.count_lines(path), 3)

    # -- load_exceptions ----------------------------------------------------

    def _load(self, text: str | None) -> dict:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "budget_exceptions.yaml"
            if text is not None:
                path.write_text(text, encoding="utf-8")
            return load_exceptions(path)

    def test_a_missing_exceptions_file_is_no_exceptions(self) -> None:
        self.assertEqual(self._load(None), {})

    def test_an_empty_exceptions_file_is_no_exceptions(self) -> None:
        self.assertEqual(self._load(""), {})

    def test_a_scalar_exceptions_document_is_refused(self) -> None:
        """Fail closed. Mutation: `return {}` instead of raising and this fails."""
        with self.assertRaises((TypeError, ValueError)):
            self._load("just a string\n")

    def test_a_non_mapping_exceptions_key_is_refused(self) -> None:
        with self.assertRaises((TypeError, ValueError)):
            self._load("exceptions:\n  - one\n  - two\n")

    def test_an_exception_whose_body_is_not_a_mapping_is_refused(self) -> None:
        """`name: true` would otherwise be read as an approved exception."""
        with self.assertRaises((TypeError, ValueError)):
            self._load("exceptions:\n  woland: true\n")

    # -- parse_expiry -------------------------------------------------------

    def test_an_unparseable_expiry_is_none_rather_than_an_error(self) -> None:
        """None means "no valid expiry", which `valid_exception` refuses.

        Mutation: return `date.today()` on failure and an exception with a
        garbage expiry silently becomes live.
        """
        self.assertIsNone(budget_gate.parse_expiry("not-a-date"))
        self.assertIsNone(budget_gate.parse_expiry(12345))
        self.assertEqual(budget_gate.parse_expiry("2099-01-01"), date(2099, 1, 1))

    def test_a_datetime_is_not_accepted_as_an_expiry_date(self) -> None:
        """`datetime` is a `date` subclass; the check excludes it deliberately."""
        self.assertIsNone(budget_gate.parse_expiry(datetime(2099, 1, 1, tzinfo=timezone.utc)))


class BudgetGateFallbackParser(unittest.TestCase):
    """The no-pyyaml parser, which must refuse what it cannot represent.

    This parser runs on hosts without pyyaml. A silent misparse there means the
    budget gate enforces different rules depending on what happens to be
    installed, which is worse than not running at all.

    AuthorityEffect: None.
    """

    def _parse(self, text: str) -> dict:
        return budget_gate._load_flat_exceptions_without_yaml(text)

    def test_an_empty_document_is_missing_its_root(self) -> None:
        with self.assertRaises(ValueError):
            self._parse("# only a comment\n")

    def test_an_unsupported_root_key_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            self._parse("budgets:\n")

    def test_an_entry_before_the_root_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            self._parse("  woland:\n")

    def test_an_empty_exceptions_root_parses_to_nothing(self) -> None:
        self.assertEqual(self._parse("exceptions: {}\n")["exceptions"], {})

    def test_a_duplicate_exception_name_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            self._parse(
                "exceptions:\n  woland:\n    approved: true\n  woland:\n    approved: true\n"
            )

    def test_an_unsupported_exception_field_is_refused(self) -> None:
        """Mutation: widen the allowed key set and this fails."""
        with self.assertRaises(ValueError):
            self._parse("exceptions:\n  woland:\n    unknown_field: 1\n")

    def test_a_duplicate_exception_field_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            self._parse(
                "exceptions:\n  woland:\n    approved: true\n    approved: false\n"
            )

    def test_unsupported_indentation_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            self._parse("exceptions:\n      stray: 1\n")

    def test_a_missing_scalar_value_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            self._parse("exceptions:\n  woland:\n    approved:\n")

    def test_a_comment_only_value_parses_as_text_and_fails_closed_later(self) -> None:
        """`approved: # yes` is not refused here, and does not need to be.

        The inline-comment strip only fires on `" #"`, and this value has no
        space before the hash, so `"# yes"` is returned verbatim. That is safe
        because approval is `is True`, not truthiness -- the string is rejected
        downstream by `valid_exception`.

        Asserted as the behaviour that actually holds, rather than the refusal
        I first assumed: a test that demands a refusal the parser never makes
        would have to be deleted the moment anyone ran it.
        """
        parsed = self._parse("exceptions:\n  woland:\n    approved: # yes\n")

        self.assertEqual(parsed["exceptions"]["woland"]["approved"], "# yes")

        ok, why = valid_exception(
            "woland", {"approved": "# yes", "expires": "2099-01-01"}, date(2026, 1, 1)
        )
        self.assertFalse(ok)
        self.assertIn("exact boolean true", why)

    def test_a_quoted_scalar_that_is_not_a_string_is_refused(self) -> None:
        """`ast.literal_eval` returns a tuple for `'a', 'b'`.

        A quoted value that is not text must not silently become a container.
        Mutation: drop the `isinstance(parsed, str)` check and this fails.
        """
        with self.assertRaises(ValueError):
            self._parse("exceptions:\n  woland:\n    reason: 'a', 'b'\n")

    def test_a_quoted_string_containing_brackets_is_still_a_string(self) -> None:
        """The paired control. `'[1, 2]'` evaluates to the STRING "[1, 2]", so
        a checker that refused every quoted value would pass the test above
        while rejecting legitimate prose."""
        parsed = self._parse("exceptions:\n  woland:\n    reason: '[1, 2]'\n")

        self.assertEqual(parsed["exceptions"]["woland"]["reason"], "[1, 2]")

    def test_integers_and_quoted_strings_round_trip(self) -> None:
        """The positive control: a parser that refused everything would pass
        every refusal test above."""
        parsed = self._parse(
            "exceptions:\n"
            "  woland:\n"
            "    approved: true\n"
            "    max_lines: 400\n"
            "    reason: 'a stated reason'\n"
        )["exceptions"]["woland"]

        self.assertIs(parsed["approved"], True)
        self.assertEqual(parsed["max_lines"], 400)
        self.assertEqual(parsed["reason"], "a stated reason")


class BudgetGateEntrypoint(unittest.TestCase):
    """`main` -- the command CI runs. AuthorityEffect: None."""

    def _repo(self, td: str, *, lines: int) -> Path:
        root = Path(td).resolve()
        (root / ".git").mkdir()
        skill = root / ".agents" / "skills" / "autoskill"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("x\n" * lines, encoding="utf-8")
        return root

    def test_main_passes_for_a_skill_within_budget(self) -> None:
        """Mutation: `return 1` at the end of `check_budgets` and this fails."""
        with tempfile.TemporaryDirectory() as td:
            root = self._repo(td, lines=10)
            argv = ["budget_gate", "--repo-root", str(root), "--skills", "autoskill"]
            with mock.patch("sys.argv", argv):
                self.assertEqual(budget_gate.main(), 0)

    def test_main_fails_for_a_skill_over_budget(self) -> None:
        """The gate's whole purpose, exercised through the command.

        Mutation: `return 0` on breach and this fails.
        """
        with tempfile.TemporaryDirectory() as td:
            root = self._repo(td, lines=500)
            argv = [
                "budget_gate", "--repo-root", str(root),
                "--skills", "autoskill", "--max-lines", "300",
            ]
            with mock.patch("sys.argv", argv):
                self.assertEqual(budget_gate.main(), 1)

    def test_main_honours_an_explicit_max_lines(self) -> None:
        """The paired control: the breach above must be caused by the budget,
        not by the file being unreadable or the skill being missing."""
        with tempfile.TemporaryDirectory() as td:
            root = self._repo(td, lines=500)
            argv = [
                "budget_gate", "--repo-root", str(root),
                "--skills", "autoskill", "--max-lines", "1000",
            ]
            with mock.patch("sys.argv", argv):
                self.assertEqual(budget_gate.main(), 0)

    def test_main_reads_an_exceptions_file_from_the_command_line(self) -> None:
        """Mutation: ignore `--exceptions` and this fails, because the breach
        would no longer be waived."""
        with tempfile.TemporaryDirectory() as td:
            root = self._repo(td, lines=500)
            exceptions = root / "exc.yaml"
            exceptions.write_text(
                "exceptions:\n"
                "  autoskill:\n"
                "    approved: true\n"
                "    expires: '2099-01-01'\n"
                "    reason: 'test fixture'\n"
                "    max_lines: 1000\n",
                encoding="utf-8",
            )
            argv = [
                "budget_gate", "--repo-root", str(root), "--skills", "autoskill",
                "--max-lines", "300", "--exceptions", str(exceptions),
            ]
            with mock.patch("sys.argv", argv):
                self.assertEqual(budget_gate.main(), 0)

    def test_main_fails_closed_when_a_governed_skill_is_absent(self) -> None:
        """A skill that is not there is not a skill within budget.

        This is the fix `4f60acbd89` landed; the entrypoint had no test for it.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            (root / ".git").mkdir()
            (root / ".agents" / "skills").mkdir(parents=True)
            argv = ["budget_gate", "--repo-root", str(root), "--skills", "autoskill"]
            with mock.patch("sys.argv", argv):
                self.assertEqual(budget_gate.main(), 1)


if __name__ == "__main__":
    unittest.main()
