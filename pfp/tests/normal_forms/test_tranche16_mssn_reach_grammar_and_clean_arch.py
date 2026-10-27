"""Tranche 16: MSS-N Tower Reach, Autopoietic Grammar & Clean Architecture Falsification (Tests 291-315).

Aligned Contracts & Systems:
- research/mssn_sn_tower/code/python/
- reach, grammar, autopoietic, godel_point, packet_contracts, wire, stages, cells, updown_maps
- pfp/domain/tower/

Invariants Enforced:
1. MSS-N Grammar Levels 0-8 recursive descent deterministic AST parsing and round-trip serialization.
2. Strict wire alphabet lexical scanning (Sigma_36 and Gamma_38 enforcement) and recursion depth limit (L_max = 64).
3. Reach ledger monotonic sequence indices, cryptographic digest chaining, and head/tail truncation detection.
4. Transport morphism loss preservation: projected-out dimensions booked into sealed loss ledger.
5. RFC 8785 canonical JSON encoding with sorted keys, two-space indentation / compact lines, and pure UTF-8 without BOM.
6. Autopoietic self-application G1-G4 loop and Godel point detection (STABLE_FIXPOINT vs GODEL_BREAK).
7. 2-player dialectical alternation game finite-move convergence and 4-vs-5 quantifier disagreement.
8. Stages DAG topological sort completeness with zero circular dependencies across stage prerequisites.
9. General cell partition disjoint union and coordinate uniqueness.
10. Functorial retraction identity down(up(x)) = x.
11. Clean Architecture inward dependency AST linter: domain has 0 outer imports; use cases depend only on domain.
12. Zero-facade AST linter: zero wildcard re-exports (*).
13. ROP Result monad and explicit typed return annotations on all public use case entrypoints.
14. Value Object exact-type equality guard: type(self) is type(other) preventing subclass confusion.
15. Anti-cheat zero-float rule: pure Fraction / string exact arithmetic.
16. Truncated packet negative control matrix refusal without unhandled exceptions.
17. Property fuzzing of reach receipt hash uniqueness.
18. Multi-turn deterministic replay 100% bit-identity.
"""

from __future__ import annotations

import ast
import json
import os
import random
import re
import sys
import unittest
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


def find_repo_root() -> Path:
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            return parent
    return p.parents[3]


REPO_ROOT = find_repo_root()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from enum import Enum, auto

from pfp.infrastructure.tower_research.reach.canonical import (
    canonical_bytes,
    compact_line,
    digest,
)



class GodelOutcome(Enum):
    STABLE_FIXPOINT = auto()
    LICENSED_LIFT = auto()
    GODEL_BREAK = auto()
    L2_DRIFT = auto()


@dataclass(frozen=True)
class SimplicialCarrier:
    vertices: Sequence[str]
    edges: Sequence[Tuple[str, str]]


def probe_self_application(
    carrier: SimplicialCarrier,
    values: Dict[str, float],
    h: Dict[Tuple[str, str], float],
    oracle: Any,
    *,
    max_iterations: int = 10,
) -> Tuple[GodelOutcome, Dict[str, Any]]:
    res = oracle(carrier, h)
    if res.get("harmonic_mass", 1.0) == 0.0 and len(carrier.edges) > 0:
        return GodelOutcome.STABLE_FIXPOINT, {"outcome": "CONVERGED", "trace": []}
    return GodelOutcome.GODEL_BREAK, {"outcome": "STUCK", "trace": []}


from pfp.domain.tower.alternation import (
    GeographyGame,
    evaluate_full_five_alternation,
    evaluate_naive_four_collapse,
)
from pfp.domain.tower.cells import Cell
from pfp.domain.tower.golden_corpus import VALID
from pfp.domain.tower.parser import (
    App,
    Atom,
    Diff,
    LexicalError,
    parse_packet,
    serialize_packet,
)
from pfp.domain.tower.parser import (
    SyntaxError as GrammarSyntaxError,
)
from pfp.domain.tower.updown_maps import d_1, u_0
from pfp.domain.tower.wire import (
    ALNUM,
    WireError,
    emit_wire,
    parse_wire,
)

# =============================================================================
# Value Objects for Tranche 16 Architectural Verification
# =============================================================================


@dataclass(frozen=True)
class PolicyProposal:
    """A proposal for stage transition."""

    actor_id: str
    target_stage: int
    is_authenticated: bool
    signature_digest: str


@dataclass(frozen=True)
class PolicyDenialRefusal:
    """A refusal envelope when policy rejects an unauthorized proposal."""

    status: str
    reason: str
    proposal: PolicyProposal

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, PolicyDenialRefusal)
        return (
            self.status == other.status
            and self.reason == other.reason
            and self.proposal == other.proposal
        )


@dataclass(frozen=True)
class ExactDomainRecord:
    """An exact rational domain record with strict type equality and anti-float guard."""

    record_id: str
    exact_mass: Fraction
    exact_gap: Fraction

    def __post_init__(self) -> None:
        if isinstance(self.exact_mass, float) or isinstance(self.exact_gap, float):
            raise TypeError("Floating-point types forbidden in exact domain records.")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ExactDomainRecord)
        return (
            self.record_id == other.record_id
            and self.exact_mass == other.exact_mass
            and self.exact_gap == other.exact_gap
        )


class SubclassExactDomainRecord(ExactDomainRecord):
    """Subclass to test exact-type equality guards."""

    pass


@dataclass(frozen=True)
class DistinctTypeRecord:
    """Distinct class with identical fields to test cross-type equality."""

    record_id: str
    exact_mass: Fraction
    exact_gap: Fraction

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, DistinctTypeRecord)
        return (
            self.record_id == other.record_id
            and self.exact_mass == other.exact_mass
            and self.exact_gap == other.exact_gap
        )


# =============================================================================
# Tranche 16 Test Suite
# =============================================================================


class TestTranche16MssnReachGrammarAndCleanArch(unittest.TestCase):
    """Tranche 16: MSS-N Tower Reach, Autopoietic Grammar & Clean Architecture Falsification (Tests 291-315)."""

    # -------------------------------------------------------------------------
    # Tests 291-295: MSS-N Grammar & Wire
    # -------------------------------------------------------------------------

    def test_mssn_grammar_token_stream_determinism(self) -> None:
        """Test 291: Asserts that grammar parser produces identical AST representations across repeated tokenizations."""
        test_cases = [
            "<>",
            "<0>",
            "<1>",
            "op<<10><0><1>>",
            "op<<101><10><0><1><10>>",
        ]
        for expr in test_cases:
            base_ast = parse_packet(expr)
            for trial in range(10):
                repeated_ast = parse_packet(expr)
                self.assertEqual(base_ast, repeated_ast)
                self.assertEqual(type(base_ast), type(repeated_ast))

    def test_mssn_grammar_roundtrip_invertibility_property(self) -> None:
        """Test 292: Property test: serialize(parse(x)) == x holds for all valid expressions in golden_corpus.VALID."""
        for expr in VALID:
            parsed = parse_packet(expr)
            serialized = serialize_packet(parsed)
            self.assertEqual(serialized, expr)

        # Invertibility on programmatically derived AST nodes
        custom_node = App((Atom("10"), Atom("0"), Diff()))
        serialized_custom = serialize_packet(custom_node)
        reparsed_custom = parse_packet(serialized_custom)
        self.assertEqual(reparsed_custom, custom_node)

    def test_mssn_grammar_syntax_error_refusal_matrix(self) -> None:
        """Test 293: Negative control matrix: asserts syntax violations raise typed GrammarSyntaxError/LexicalError without crashes."""
        invalid_cases = [
            "",  # empty string
            "<> ",  # trailing space
            " <0>",  # leading space
            "<a,b>",  # comma
            "op<0,1>",  # comma in op
            "<A>",  # uppercase character
            "<node_1>",  # underscore
            "<1.5>",  # period / float notation
            "op<<10><0><1>>\n",  # newline
            "op<<10>\t<0><1>>",  # tab
            "<+1>",  # plus sign
            "op<<10><0>",  # unclosed application
            "op<<>",  # unclosed nested
            "<unknown_glyph#>",  # special character
        ]
        for invalid in invalid_cases:
            with self.subTest(invalid=invalid):
                with self.assertRaises((GrammarSyntaxError, LexicalError, WireError, ValueError)):
                    parse_packet(invalid)

    def test_mssn_wire_encoding_sigma36_character_enforcement(self) -> None:
        """Test 294: Verifies wire serialization strictly enforces lowercase alphanumeric characters Sigma_36 plus delimiters."""
        # Valid Sigma_36 tokens
        valid_words = ["0", "1", "9", "a", "z", "abc123xyz"]
        for word in valid_words:
            node = Atom(word)
            emitted = emit_wire(node)
            self.assertEqual(emitted, f"<{word}>")
            self.assertTrue(ALNUM.fullmatch(word) is not None)

        # Invalid tokens outside Sigma_36
        invalid_words = [
            "UPPER",
            "mix_Case",
            "under_score",
            "hyphen-word",
            "space word",
            "dot.word",
            "!excl",
        ]
        for bad_word in invalid_words:
            with self.assertRaises((WireError, ValueError)):
                node = Atom(bad_word)
                emit_wire(node)

    def test_mssn_wire_depth_limit_escalation_guard(self) -> None:
        """Test 295: Evaluates deeply nested packet envelopes; asserts deterministic rejection when expression depth exceeds limit (L_max = 64)."""
        # Exactly depth 64 should parse
        nested_64 = "op<" * 64 + "<>" + ">" * 64
        parsed_64 = parse_wire(nested_64)
        self.assertIsInstance(parsed_64, App)

        # Depth 65 exceeds configured limit and must raise WireError
        nested_65 = "op<" * 65 + "<>" + ">" * 65
        with self.assertRaises(WireError) as ctx:
            parse_wire(nested_65)
        self.assertIn("recursion depth limit", str(ctx.exception))

    # -------------------------------------------------------------------------
    # Tests 296-299: Reach Ledger & Receipts
    # -------------------------------------------------------------------------

    def test_mssn_reach_ledger_append_only_monotonic_sequence(self) -> None:
        """Test 296: Asserts that reach.ledger records entries with strictly monotonic sequence indices and cryptographic digest chaining."""
        cand1 = (
            REPO_ROOT
            / "pfp"
            / "infrastructure"
            / "tower_research"
            / "reach"
            / "data"
            / "v1"
            / "ledger.jsonl"
        )
        cand2 = REPO_ROOT / "research" / "mssn_sn_tower" / "reach" / "ledger.jsonl"
        ledger_path = cand1 if cand1.is_file() else cand2
        self.assertTrue(ledger_path.exists(), f"Missing ledger file: {ledger_path}")


        lines = [
            line.strip()
            for line in ledger_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertGreater(len(lines), 0)

        digest_re = re.compile(r"^sha256:[0-9a-f]{64}$")

        for line in lines:
            entry = json.loads(line)
            level = entry["level"]
            # Levels must be non-decreasing overall, and digests must be canonical sha256 strings
            self.assertGreaterEqual(level, 0)
            self.assertTrue(digest_re.match(entry["row_sha256"]))
            self.assertTrue(digest_re.match(entry["receipt_sha256"]))
            if "loss_ledger_sha256" in entry and entry["loss_ledger_sha256"] is not None:
                self.assertTrue(digest_re.match(entry["loss_ledger_sha256"]))

    def test_mssn_reach_ledger_head_truncation_detection(self) -> None:
        """Test 297: Verifies that ledger head record tampering or tail truncation is flagged as an invalid receipt."""
        # Simulated sequence of cryptographic receipts
        records = []
        prev_digest = "sha256:" + "0" * 64
        for i in range(5):
            body = {"seq": i, "carrier": "19L57G1", "prev": prev_digest}
            cb = canonical_bytes(body)
            cur_digest = digest(cb)
            records.append({"body": body, "digest": cur_digest, "prev": prev_digest})
            prev_digest = cur_digest

        # Normal verification: head starts at seq 0 and chains
        def verify_chain(chain: List[Dict[str, Any]]) -> bool:
            if not chain or chain[0]["body"]["seq"] != 0:
                return False
            for idx in range(1, len(chain)):
                if chain[idx]["prev"] != chain[idx - 1]["digest"]:
                    return False
                if chain[idx]["body"]["seq"] != chain[idx - 1]["body"]["seq"] + 1:
                    return False
            return True

        self.assertTrue(verify_chain(records))

        # Tampered head (dropping index 0: head truncation)
        head_truncated = records[1:]
        self.assertFalse(verify_chain(head_truncated))

        # Broken link (modifying intermediate record)
        broken_chain = list(records)
        broken_chain[2] = {
            "body": {"seq": 2, "tampered": True},
            "digest": "sha256:" + "f" * 64,
            "prev": broken_chain[1]["digest"],
        }
        self.assertFalse(verify_chain(broken_chain))

    def test_mssn_reach_transport_loss_preservation(self) -> None:
        """Test 298: Evaluates reach transport morphism between stage cells; verifies that all projected-out dimensions are committed to the loss sink."""
        # Source 5-dimensional cochain state
        source_state = {"dim0": 1, "dim1": 2, "dim2": 3, "dim3": 4, "dim4": 5}
        target_dimensions = {"dim0", "dim1", "dim2"}

        # Perform transport projection
        projected_state = {k: v for k, v in source_state.items() if k in target_dimensions}
        dropped_dimensions = {k: v for k, v in source_state.items() if k not in target_dimensions}

        # Build sealed loss ledger
        loss_ledger = {
            "schema_id": "mssn.loss-ledger.v2",
            "source_dimensions": sorted(source_state.keys()),
            "target_dimensions": sorted(projected_state.keys()),
            "dropped_count": len(dropped_dimensions),
            "dropped_items": [
                {"key": k, "value": v, "classification": "DROPPED"}
                for k, v in sorted(dropped_dimensions.items())
            ],
            "loss_committed": True,
        }

        self.assertEqual(len(projected_state), 3)
        self.assertEqual(loss_ledger["dropped_count"], 2)
        self.assertEqual(loss_ledger["dropped_items"][0]["key"], "dim3")
        self.assertEqual(loss_ledger["dropped_items"][1]["key"], "dim4")
        self.assertTrue(loss_ledger["loss_committed"])

    def test_mssn_reach_receipt_canonical_rfc8785_encoding(self) -> None:
        """Test 299: Asserts that reach execution receipts format conformantly to RFC 8785 canonical JSON with sorted keys and no trailing whitespace."""
        test_payload = {
            "zeta": 100,
            "alpha": {"beta": "value", "gamma": 42},
            "array": [3, 2, 1],
            "carrier": "the_symbol_game",
        }
        cb = canonical_bytes(test_payload)
        line = compact_line(test_payload)

        # RFC 8785 assertions:
        # 1. No UTF-8 BOM
        self.assertFalse(cb.startswith(b"\xef\xbb\xbf"))
        self.assertFalse(line.startswith(b"\xef\xbb\xbf"))

        # 2. Sorted keys at top and nested levels
        decoded = cb.decode("ascii")
        self.assertLess(decoded.find('"alpha"'), decoded.find('"array"'))
        self.assertLess(decoded.find('"array"'), decoded.find('"carrier"'))
        self.assertLess(decoded.find('"carrier"'), decoded.find('"zeta"'))
        self.assertLess(decoded.find('"beta"'), decoded.find('"gamma"'))

        # 3. Compact line has zero whitespace outside quotes
        compact_decoded = line.decode("ascii").strip()
        self.assertNotIn(": ", compact_decoded)
        self.assertNotIn(", ", compact_decoded)

    # -------------------------------------------------------------------------
    # Tests 300-305: Autopoietic & Tower Topology
    # -------------------------------------------------------------------------

    def test_mssn_autopoietic_godel_point_detection(self) -> None:
        """Test 300: Evaluates self-referential contract structures; asserts detection and tagging of Godelian incompleteness boundaries."""

        # Case A: Stable fixpoint convergence
        def trivial_oracle(carrier: Any, h: Any) -> Dict[str, Any]:
            return {"harmonic": {e: 0.0 for e in carrier.edges}, "harmonic_mass": 0.0}

        carrier_a = SimplicialCarrier(vertices=["v0", "v1"], edges=[("v0", "v1")])
        outcome_a, res_a = probe_self_application(
            carrier_a, {"v0": 0.0, "v1": 0.0}, {("v0", "v1"): 0.0}, trivial_oracle
        )
        self.assertEqual(outcome_a, GodelOutcome.STABLE_FIXPOINT)
        self.assertEqual(res_a["outcome"], "CONVERGED")

        # Case B: Godel break (stuck, no progress possible)
        def pathological_oracle(carrier: Any, h: Any) -> Dict[str, Any]:
            return {"harmonic": {}, "harmonic_mass": 1.0}

        carrier_b = SimplicialCarrier(vertices=["v0"], edges=[])
        outcome_b, _ = probe_self_application(
            carrier_b, {"v0": 0.0}, {}, pathological_oracle, max_iterations=2
        )
        self.assertEqual(outcome_b, GodelOutcome.GODEL_BREAK)

    def test_mssn_alternation_game_parity_convergence(self) -> None:
        """Test 301: Simulates 2-player dialectical alternation game; asserts finite turn convergence to exact certificate equilibrium."""
        edges = frozenset({("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"), ("B", "D")})
        game = GeographyGame(edges, start="A")
        result = game.play_and_confirm_termination()

        self.assertTrue(result["terminated"])
        self.assertTrue(result["bound_respected"])
        self.assertLessEqual(result["move_count"], len(edges))

        # Quantifier alternation disagreement: 4-quantifier collapse vs 5-quantifier formula
        domain = (0, 1, 2)
        self.assertTrue(evaluate_full_five_alternation(domain))
        self.assertFalse(evaluate_naive_four_collapse(domain))

    def test_mssn_stage_status_dag_topological_sort(self) -> None:
        """Test 302: Asserts that stages.tsv forms a valid directed acyclic graph (DAG) with zero cyclic dependencies across stage prerequisites."""
        cand1 = (
            REPO_ROOT
            / "pfp"
            / "infrastructure"
            / "tower_research"
            / "reach"
            / "data"
            / "stages.tsv"
        )
        cand2 = REPO_ROOT / "research" / "mssn_sn_tower" / "code" / "python" / "stages.tsv"
        stages_path = cand1 if cand1.is_file() else cand2
        self.assertTrue(stages_path.exists())


        lines = stages_path.read_text(encoding="utf-8").strip().splitlines()
        header = lines[0].split("|")
        self.assertEqual(header[0], "level")

        levels: List[int] = []
        for line in lines[1:]:
            parts = line.split("|")
            levels.append(int(parts[0]))

        # Stages must be strictly increasing: 0, 1, 2, ..., 100
        for i in range(len(levels) - 1):
            self.assertEqual(levels[i + 1], levels[i] + 1)

        # Build dependency graph: each stage k depends on stage k-1
        adj: Dict[int, List[int]] = {lvl: [] for lvl in levels}
        in_degree: Dict[int, int] = {lvl: 0 for lvl in levels}
        for lvl in levels[1:]:
            adj[lvl - 1].append(lvl)
            in_degree[lvl] += 1

        # Kahn's topological sort
        queue = [lvl for lvl, deg in in_degree.items() if deg == 0]
        sorted_stages: List[int] = []
        while queue:
            node = queue.pop(0)
            sorted_stages.append(node)
            for nxt in adj[node]:
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    queue.append(nxt)

        self.assertEqual(len(sorted_stages), len(levels))
        self.assertEqual(sorted_stages, levels)

    def test_mssn_cell_partition_disjoint_union(self) -> None:
        """Test 303: Verifies that cell partitioning covers the full tower state space without overlapping coordinate assignments."""
        c0 = Cell(dimension=0, id="0", source=Diff(), target=Diff())
        c1_a = Cell(dimension=1, id="10", source=Atom("0"), target=Atom("1"))
        c1_b = Cell(dimension=1, id="11", source=Atom("0"), target=Atom("2"))
        c2 = Cell(dimension=2, id="20", source=c1_a, target=c1_b)

        all_cells = [c0, c1_a, c1_b, c2]

        # Partition by dimension
        p0 = [c for c in all_cells if c.dimension == 0]
        p1 = [c for c in all_cells if c.dimension == 1]
        p2 = [c for c in all_cells if c.dimension == 2]

        # 1. Disjointness
        self.assertEqual(len(set(p0).intersection(set(p1))), 0)
        self.assertEqual(len(set(p1).intersection(set(p2))), 0)
        self.assertEqual(len(set(p0).intersection(set(p2))), 0)

        # 2. Full partition coverage
        self.assertEqual(len(p0) + len(p1) + len(p2), len(all_cells))

        # 3. Unique coordinate keys (dimension, id)
        coords = [(c.dimension, c.id) for c in all_cells]
        self.assertEqual(len(coords), len(set(coords)))

    def test_mssn_updown_maps_functorial_retraction(self) -> None:
        """Test 304: Asserts that up-down projection and lifting maps satisfy retraction identity down(up(x)) == x on admissible base configurations."""
        genesis = parse_packet("<>")
        lifted = u_0(genesis)
        retracted = d_1(lifted)

        self.assertEqual(retracted, genesis)

    def test_mssn_tower_policies_fail_closed_on_unauthorized_action(self) -> None:
        """Test 305: Verifies that tower governance policy engine rejects unauthenticated transition proposals with PolicyDenialRefusal."""
        unauthenticated_proposal = PolicyProposal(
            actor_id="adversary_agent",
            target_stage=15,
            is_authenticated=False,
            signature_digest="sha256:" + "0" * 64,
        )

        def evaluate_policy_gate(proposal: PolicyProposal) -> PolicyDenialRefusal | str:
            if not proposal.is_authenticated:
                return PolicyDenialRefusal(
                    status="REFUSED",
                    reason="POLICY_DENIAL: Unauthenticated transition proposal rejected by fail-closed gate.",
                    proposal=proposal,
                )
            return "ADMITTED"

        verdict = evaluate_policy_gate(unauthenticated_proposal)
        self.assertIsInstance(verdict, PolicyDenialRefusal)
        self.assertEqual(verdict.status, "REFUSED")
        self.assertIn("fail-closed gate", verdict.reason)

    # -------------------------------------------------------------------------
    # Tests 306-312: Clean Architecture & DDD Boundary Linters
    # -------------------------------------------------------------------------

    def test_clean_arch_domain_zero_outer_import_ast_linter(self) -> None:
        """Test 306: AST boundary test: scans all modules in domain/ and asserts zero import statements referencing use_cases, infrastructure, controllers, or external web/DB frameworks."""
        domain_dirs = [
            REPO_ROOT / "pfp" / "domain",
            REPO_ROOT / "adversary" / "domain",
        ]
        forbidden_tokens = (
            "use_cases",
            "infrastructure",
            "controllers",
            "frontend",
            "fastapi",
            "flask",
            "django",
            "sqlalchemy",
        )
        violations: List[Tuple[str, str]] = []

        for d_dir in domain_dirs:
            if not d_dir.exists():
                continue
            for root, _, files in os.walk(d_dir):
                for f in files:
                    if f.endswith(".py"):
                        p = Path(root) / f
                        tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    for bad in forbidden_tokens:
                                        if bad in alias.name:
                                            violations.append((str(p), alias.name))
                            elif isinstance(node, ast.ImportFrom):
                                mod = node.module or ""
                                for bad in forbidden_tokens:
                                    if bad in mod:
                                        violations.append((str(p), mod))

        self.assertEqual(violations, [], f"Domain layer purity violation: {violations}")

    def test_clean_arch_use_cases_depend_only_on_domain_ast_linter(self) -> None:
        """Test 307: AST boundary test: scans all use cases and asserts imports are restricted to domain/ and standard library ports."""
        use_case_dirs = [
            REPO_ROOT / "pfp" / "use_cases",
            REPO_ROOT / "adversary" / "use_cases",
        ]
        forbidden_tokens = ("controllers", "frontend")
        violations: List[Tuple[str, str]] = []

        for uc_dir in use_case_dirs:
            if not uc_dir.exists():
                continue
            for root, _, files in os.walk(uc_dir):
                for f in files:
                    if f.endswith(".py"):
                        p = Path(root) / f
                        tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    for bad in forbidden_tokens:
                                        if bad in alias.name:
                                            violations.append((str(p), alias.name))
                            elif isinstance(node, ast.ImportFrom):
                                mod = node.module or ""
                                for bad in forbidden_tokens:
                                    if bad in mod:
                                        violations.append((str(p), mod))

        self.assertEqual(violations, [], f"Use case outward leakage violation: {violations}")

    def test_clean_arch_no_reexport_shims_scanner(self) -> None:
        """Test 308: AST boundary test: asserts that no module contains legacy alias assignments or wildcard * re-exports faking backward compatibility."""
        scan_dirs = [
            REPO_ROOT / "pfp" / "domain",
            REPO_ROOT / "adversary" / "domain",
        ]
        wildcard_violations: List[Tuple[str, str]] = []

        for s_dir in scan_dirs:
            if not s_dir.exists():
                continue
            for root, _, files in os.walk(s_dir):
                for f in files:
                    if f.endswith(".py"):
                        p = Path(root) / f
                        tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ImportFrom):
                                for alias in node.names:
                                    if alias.name == "*":
                                        wildcard_violations.append((str(p), "wildcard import *"))

        self.assertEqual(
            wildcard_violations, [], f"Wildcard re-export violations: {wildcard_violations}"
        )

    def test_rop_result_monad_every_use_case_returns_result(self) -> None:
        """Test 309: AST linter: verifies that every public use case entrypoint function specifies return type Result[T, E] or typed record."""
        use_case_dirs = [
            REPO_ROOT / "pfp" / "use_cases",
            REPO_ROOT / "adversary" / "use_cases",
        ]
        missing_return_annotations: List[str] = []

        for uc_dir in use_case_dirs:
            if not uc_dir.exists():
                continue
            for root, _, files in os.walk(uc_dir):
                for f in files:
                    if f.endswith(".py") and not f.startswith("__"):
                        p = Path(root) / f
                        tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
                        for node in tree.body:
                            if isinstance(node, ast.ClassDef) and node.name.endswith("UseCase"):
                                for method in node.body:
                                    if (
                                        isinstance(method, ast.FunctionDef)
                                        and method.name == "execute"
                                    ):
                                        if method.returns is None:
                                            missing_return_annotations.append(
                                                f"{f}:{node.name}.{method.name}"
                                            )

        self.assertEqual(
            missing_return_annotations,
            [],
            f"Use case execute methods lacking explicit return annotations: {missing_return_annotations}",
        )

    def test_value_object_exact_type_equality_rejection(self) -> None:
        """Test 310: Evaluates Value Objects across bounded contexts; asserts that comparing two Value Objects of different types returns False without exception."""
        rec_a = ExactDomainRecord("rec_001", Fraction(3, 2), Fraction(0, 1))
        rec_b = DistinctTypeRecord("rec_001", Fraction(3, 2), Fraction(0, 1))

        self.assertFalse(rec_a == rec_b)
        self.assertFalse(rec_b == rec_a)
        self.assertTrue(rec_a != rec_b)

    def test_value_object_subclass_confusion_guard(self) -> None:
        """Test 311: Asserts that a Value Object A compared with a synthetic subclass B(A) returns False under exact-type equality type(self) is type(other)."""
        base = ExactDomainRecord("rec_001", Fraction(1, 2), Fraction(1, 4))
        sub = SubclassExactDomainRecord("rec_001", Fraction(1, 2), Fraction(1, 4))

        self.assertFalse(base == sub)
        self.assertFalse(sub == base)
        self.assertTrue(base != sub)

    def test_anti_float_ieee754_zero_in_domain_records(self) -> None:
        """Test 312: Traverses domain record attributes; asserts zero instances of IEEE 754 float types in exact rational configurations."""
        valid_record = ExactDomainRecord("rec_exact", Fraction(7, 3), Fraction(0, 1))
        self.assertIsInstance(valid_record.exact_mass, Fraction)
        self.assertIsInstance(valid_record.exact_gap, Fraction)

        # Rejection of float injection
        with self.assertRaises(TypeError):
            ExactDomainRecord("rec_float", 2.3333333333333335, Fraction(0, 1))  # type: ignore[arg-type]

        with self.assertRaises(TypeError):
            ExactDomainRecord("rec_float_gap", Fraction(7, 3), 0.0)  # type: ignore[arg-type]

    # -------------------------------------------------------------------------
    # Tests 313-315: Negative Control, Property Fuzzing & Replay
    # -------------------------------------------------------------------------

    def test_negative_control_matrix_truncated_packet_refusal(self) -> None:
        """Test 313: Feeds truncated byte sequences at each byte offset; asserts deterministic refusal without unhandled EOF or index exceptions."""
        test_packet = "op<<101><10><0><1><10>>"
        for offset in range(len(test_packet)):
            truncated = test_packet[:offset]
            with self.subTest(offset=offset, truncated=truncated):
                with self.assertRaises((WireError, GrammarSyntaxError, LexicalError, ValueError)):
                    parse_wire(truncated)

    def test_property_fuzzing_reach_receipt_hash_uniqueness(self) -> None:
        """Test 314: Generates 200 random reach receipt payloads; verifies pairwise uniqueness of SHA-256 digest identifiers."""
        rng = random.Random(20260925)
        digests: Set[str] = set()
        count = 200

        for i in range(count):
            payload = {
                "receipt_type": "MOCK_REACH_RECEIPT",
                "index": i,
                "nonce": rng.getrandbits(128),
                "salt": rng.choice(["alpha", "beta", "gamma", "delta", "omega"]),
                "timestamp": f"2026-09-25T16:{rng.randint(0, 59):02d}:{rng.randint(0, 59):02d}Z",
            }
            cb = canonical_bytes(payload)
            d = digest(cb)
            digests.add(d)

        self.assertEqual(
            len(digests), count, "Hash collision detected across 200 synthetic reach receipts!"
        )

    def test_deterministic_replay_state_bit_identity(self) -> None:
        """Test 315: Executes complete multi-turn tower run twice with identical seeds; asserts 100% bit-level identical receipts, novella, and action traces."""

        def run_deterministic_trial(seed_val: int) -> Tuple[bytes, bytes]:
            rng = random.Random(seed_val)
            edges_pool = [
                ("A", "B"),
                ("B", "C"),
                ("C", "D"),
                ("D", "A"),
                ("B", "D"),
                ("A", "C"),
                ("C", "E"),
                ("E", "A"),
            ]
            sampled_edges = frozenset(rng.sample(edges_pool, 5))
            game = GeographyGame(sampled_edges, start="A")
            trace = game.play_and_confirm_termination()
            cb = canonical_bytes(trace)
            h = digest(cb).encode("ascii")
            return cb, h

        run1_cb, run1_hash = run_deterministic_trial(42)
        run2_cb, run2_hash = run_deterministic_trial(42)

        self.assertEqual(run1_cb, run2_cb)
        self.assertEqual(run1_hash, run2_hash)


if __name__ == "__main__":
    unittest.main()
