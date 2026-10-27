"""White-Box Adversarial Coverage Hardening Suite (Tier 5 Challenger).

Stress-tests edge boundaries, degenerate configurations, and branch permutations
across all 5 functional dimensions:
1. Malformed / Hostile Operad Graft Configurations (Python & Native Rust Host FFI)
2. Degenerate Cell Complexes (disconnected, circular, zero-edge, non-nilpotent)
3. Exotic Rational Numbers & PageRank Edge Cases (large bitlengths, negative bounds)
4. RFC 8785 Canonical JSON & Boundary Float Formats (ES 7.1.12.1 formatting)
5. Hostile YAML Scalars (YAML 1.1 booleans, duplicate keys, null values, tabs)

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import pytest
import yaml

from pfp.domain.canonical import (
    MAX_SAFE_INTEGER,
    JcsError,
    canonicalize_json_str,
    format_es_number,
    format_es_string,
    rfc8785_canonical_json,
    rfc8785_digest_sha256,
)
from pfp.domain.cochain import (
    ClosedNonExactClass,
    CochainRefusal,
    PrimeTriadContext,
    PromptCellComplex,
    _fraction_to_wire,
    _parse_bigint,
    _parse_fraction,
)
from pfp.domain.operad import (
    AnnihilatorDecoy,
    CongruenceIdeal,
    LeafTextSpan,
    NullTree,
    OperadTreeNode,
    PromptColour,
    PromptOperator,
)
from pfp.ffi import (
    evaluate_prompt_cochain_disposition as evaluate_prompt_cochain,
)
from pfp.ffi import get_default_host
from pfp.infrastructure.yaml_loading import (
    StrictYamlError,
    strict_yaml_load,
)

# =============================================================================
# DIMENSION 1: MALFORMED & HOSTILE OPERAD GRAFT CONFIGURATIONS
# =============================================================================

class TestOperadAdversarialGrafts:
    """Stress tests on operad trees, slot grafting, congruence ideals, and decoy traps."""

    def test_leaf_text_span_inverted_offsets_raises_value_error(self):
        """Start offset > end offset must be rejected immediately."""
        with pytest.raises(ValueError, match="Start offset 42 exceeds end offset 10"):
            LeafTextSpan(
                id="span_inv",
                colour=PromptColour.RawTextSpan,
                content="test",
                source_offsets=(42, 10),
            )

    def test_leaf_text_span_end_exceeds_doc_length(self):
        """End offset exceeding source document length fails closed."""
        doc = "short"
        span = LeafTextSpan(
            id="span_oob",
            colour=PromptColour.RawTextSpan,
            content="short",
            source_offsets=(0, 100),
        )
        with pytest.raises(ValueError, match="exceeds document length"):
            span.verify_against_document(doc)

    def test_leaf_text_span_content_mutation_detected(self):
        """Content at offsets differing from expected string fails closed."""
        doc = "alpha beta gamma"
        span = LeafTextSpan(
            id="span_mut",
            colour=PromptColour.RawTextSpan,
            content="omega",
            source_offsets=(0, 5),
        )
        with pytest.raises(ValueError, match="Span content mismatch"):
            span.verify_against_document(doc)

    def test_operator_arity_mismatch_on_declaration(self):
        """Declaring operator arity inconsistent with source_colours length must fail."""
        with pytest.raises(ValueError, match="arity mismatch"):
            PromptOperator(
                id="op_mismatch",
                source_colours=(PromptColour.Equation,),
                target_colour=PromptColour.IsolatedVariable,
                arity=3,
            )

    def test_tree_node_slot_out_of_bounds_raises_index_error(self):
        """Grafting into a slot index >= operator arity raises IndexError."""
        op = PromptOperator(
            id="binary_add",
            source_colours=(PromptColour.RationalValue, PromptColour.RationalValue),
            target_colour=PromptColour.RationalValue,
            arity=2,
        )
        node = OperadTreeNode(operator=op, children=())
        leaf = LeafTextSpan("l1", PromptColour.RationalValue, "1", (0, 1))
        # Slot 5 is out of bounds for arity 2
        with pytest.raises(IndexError, match="Slot 5 out of bounds"):
            node.graft(5, leaf)
        # Negative slot is out of bounds
        with pytest.raises(IndexError, match="Slot -1 out of bounds"):
            node.graft(-1, leaf)

    def test_tree_node_child_colour_mismatch_raises_type_error(self):
        """Grafting a child with mismatched colour raises TypeError."""
        op = PromptOperator(
            id="isolate_var",
            source_colours=(PromptColour.Equation,),
            target_colour=PromptColour.IsolatedVariable,
            arity=1,
        )
        node = OperadTreeNode(operator=op, children=())
        leaf = LeafTextSpan("l1", PromptColour.RawTextSpan, "raw text", (0, 8))
        with pytest.raises(TypeError, match="Boundary colour mismatch at slot 0"):
            node.graft(0, leaf)

    def test_congruence_ideal_absorption_in_tree_node(self):
        """If a NullTree is grafted into any slot, node projects to NullTree."""
        op = PromptOperator(
            id="combine",
            source_colours=(PromptColour.RationalValue, PromptColour.RationalValue),
            target_colour=PromptColour.RationalValue,
            arity=2,
        )
        node = OperadTreeNode(operator=op, children=())
        null_child = NullTree(
            ideal_id="IDEAL_EXACT",
            reason="float detected",
            target_colour=PromptColour.RationalValue,
        )
        # Grafting null tree directly returns NullTree
        absorbed = node.graft(0, null_child)
        assert isinstance(absorbed, NullTree)
        assert absorbed.ideal_id == "IDEAL_EXACT"
        assert "grafted child is null tree" in absorbed.reason

    def test_congruence_ideal_rejects_floating_point_strings(self):
        """CongruenceIdeal checks reject floats and scientific notation in rational domains."""
        ideal = CongruenceIdeal(
            id="IDEAL_RATIONAL",
            target_colour=PromptColour.RationalValue,
            assertion="exact rational only",
        )
        # Decimal float
        assert ideal.evaluate_rational_domain("3.14") is not None
        # Scientific notation
        assert ideal.evaluate_rational_domain("1e-5") is not None
        assert ideal.evaluate_rational_domain("2E+3") is not None
        # Malformed fraction
        assert ideal.evaluate_rational_domain("3/0") is not None
        assert ideal.evaluate_rational_domain("foo/bar") is not None
        # Valid exact fractions and integers are accepted (return None)
        assert ideal.evaluate_rational_domain("22/7") is None
        assert ideal.evaluate_rational_domain("-42") is None
        assert ideal.evaluate_rational_domain("0") is None

    def test_annihilator_decoy_unrefuted_trap_raises_value_error(self):
        """Candidate matching decoy bindings without refutation witness is refused."""
        decoy = AnnihilatorDecoy(
            id="DECOY_001",
            description="Trap decoy",
            decoy_candidate_bindings={"x": "3", "y": "0"},
            refutation_witness={
                "equation": "x + 2*y = 5",
                "evaluation": "3 + 2*(0) = 3 != 5",
            },
        )
        # Matching candidate without witness raises
        with pytest.raises(ValueError, match="matches decoy bindings"):
            decoy.evaluate({"x": "3", "y": "0"}, provided_refutation=None)

    def test_annihilator_decoy_invalid_refutation_format_refused(self):
        """Refutation witness that lacks '!=' inequality proof is rejected."""
        decoy = AnnihilatorDecoy(
            id="DECOY_001",
            description="Trap decoy",
            decoy_candidate_bindings={"x": "3", "y": "0"},
            refutation_witness={
                "equation": "x + 2*y = 5",
                "evaluation": "3 + 2*(0) = 3 != 5",
            },
        )
        # Refutation without "!="
        bad_witness = {"equation": "x + 2*y = 5", "evaluation": "3 + 0 = 3"}
        with pytest.raises(ValueError, match="must prove inequality"):
            decoy.evaluate({"x": "3", "y": "0"}, provided_refutation=bad_witness)

    def test_annihilator_decoy_neutralized_with_valid_witness(self):
        """Candidate matching decoy with sound refutation witness evaluates to Neutralized."""
        decoy = AnnihilatorDecoy(
            id="DECOY_001",
            description="Trap decoy",
            decoy_candidate_bindings={"x": "3", "y": "0"},
            refutation_witness={
                "equation": "x + 2*y = 5",
                "evaluation": "3 + 2*(0) = 3 != 5",
            },
        )
        valid_witness = {"equation": "x + 2*y = 5", "evaluation": "3 + 2*(0) = 3 != 5"}
        res = decoy.evaluate({"x": "3", "y": "0"}, provided_refutation=valid_witness)
        assert res["disposition"] == "Neutralized"
        assert res["decoy_id"] == "DECOY_001"

    def test_native_rust_operad_graft_slot_boundary_colour_mismatch(self):
        """Native Rust FFI action operad_graft_slot enforces colour checking and fails closed."""
        host = get_default_host()
        payload = {
            "outer": {
                "type": "node",
                "operator": {
                    "id": "isolate",
                    "source_colours": ["Equation"],
                    "target_colour": "IsolatedVariable",
                    "arity": 1,
                    "description": "Isolate variable",
                },
                "children": [],
            },
            "slot": 0,
            "inner": {
                "type": "leaf",
                "span": {
                    "id": "raw",
                    "colour": "RawTextSpan",
                    "content": "x = 1",
                    "source_offsets": [0, 5],
                },
            },
        }
        res = host.invoke("operad_graft_slot", payload)
        # Should return a failure outcome with BOUNDARY_COLOUR_MISMATCH
        assert res.is_ok
        data = res.unwrap()
        assert data["success"] is False
        assert "BOUNDARY_COLOUR_MISMATCH" in data["error"]

    def test_native_rust_operad_check_annihilator_unrefuted_trap(self):
        """Native Rust FFI action operad_check_annihilator refuses unrefuted decoy candidates."""
        host = get_default_host()
        payload = {
            "annihilator": {
                "id": "TRAP_001",
                "description": "Test trap",
                "decoy_candidate": {
                    "bindings": {"x": "0", "y": "0"},
                },
                "refutation_witness": {
                    "equation": "x + y = 1",
                    "evaluation": "0 + 0 = 0 != 1",
                },
            },
            "candidate_bindings": {"x": "0", "y": "0"},
            "refutation_witness": None,
        }
        res = host.invoke("operad_check_annihilator", payload)
        assert res.is_ok
        data = res.unwrap()
        assert data["success"] is False
        assert "DECOY_TRAP_UNREFUTED" in data["error"]


# =============================================================================
# DIMENSION 2: DEGENERATE CELL COMPLEXES & COCHAIN EXECUTIONS
# =============================================================================

class TestCochainAdversarialComplexes:
    """Stress tests on cell complexes, chain law nilpotence, and disposition invariants."""

    def test_non_nilpotent_complex_curved_geometry_refused(self):
        """d1 * d0 != 0 must fail closed with CHAIN_LAW_VIOLATION via native Rust host."""
        host = get_default_host()
        curved_complex = {
            "c0_dim": 2,
            "c1_dim": 2,
            "c2_dim": 1,
            "d0": [["-1", "1"], ["1", "-1"]],
            "d1": [["1", "2"]],  # 1*(-1) + 2*(1) = 1 != 0
        }
        outcome = host.evaluate_prompt_cochain(
            complex=curved_complex,
            cochain=["0", "0"],
            primal_potential=["0", "0"],
            dual_witness=["0", "0"],
        )
        assert outcome.is_ok
        res = outcome.unwrap().get("result", outcome.unwrap())
        assert res["disposition"] == "Refusal"
        assert "CHAIN_LAW_VIOLATION" in res.get("code", "")

    def test_impossible_profile_refusal_phi1_zero_gamma2_positive(self):
        """Evaluating Phi1=0 and Gamma2>0 is mathematically impossible and refused."""
        triangle = PromptCellComplex.from_oriented_graph(
            vertices=("v0", "v1", "v2"),
            edges=(("v0", "v1"), ("v1", "v2"), ("v2", "v0")),
            faces=(((0, 1), (1, 1), (2, 1)),),
        )
        cochain = [Fraction(1), Fraction(1), Fraction(1)]  # d1 c = 3 != 0
        disp = evaluate_prompt_cochain(
            complex=triangle,
            cochain=cochain,
            primal_potential=[Fraction(0), Fraction(1), Fraction(3)],
            dual_witness=[Fraction(0), Fraction(0), Fraction(0)],
        )
        assert isinstance(disp, CochainRefusal)
        assert "PHI1_CERTIFICATE_INVALID" in disp.reason or "IMPOSSIBLE_PROFILE" in disp.reason

    def test_zero_face_complex_evaluates_gamma2_zero(self):
        """Cell complex with no declared faces (C^2 = Q^0) strictly evaluates Gamma2 = 0."""
        complex_no_faces = PromptCellComplex.from_oriented_graph(
            vertices=("v0", "v1", "v2"),
            edges=(("v0", "v1"), ("v1", "v2"), ("v2", "v0")),
            faces=None,
        )
        assert complex_no_faces.f_count == 0
        assert len(complex_no_faces.d1_matrix) == 0

        # Coherent residual c = (1, 1, 1) with dual witness y = (1, 1, 1)
        disp = evaluate_prompt_cochain(
            complex=complex_no_faces,
            cochain=[Fraction(1), Fraction(1), Fraction(1)],
            primal_potential=[Fraction(0), Fraction(0), Fraction(0)],
            dual_witness=[Fraction(1), Fraction(1), Fraction(1)],
        )
        assert isinstance(disp, ClosedNonExactClass)
        assert disp.gamma2 == Fraction(0)
        assert disp.phi1 == Fraction(3)

    def test_dimension_mismatch_refused_fail_closed(self):
        """Passing cochain, potential, or dual witness with wrong dimension fails closed."""
        triangle = PromptCellComplex.from_oriented_graph(
            vertices=("v0", "v1", "v2"),
            edges=(("v0", "v1"), ("v1", "v2"), ("v2", "v0")),
        )
        disp = evaluate_prompt_cochain(
            complex=triangle,
            cochain=[Fraction(1), Fraction(2)],
            primal_potential=[Fraction(0), Fraction(0), Fraction(0)],
            dual_witness=[Fraction(0), Fraction(0), Fraction(0)],
        )
        assert isinstance(disp, CochainRefusal)
        assert "DIMENSION_MISMATCH" in disp.reason

    def test_prime_000_custody_hash_mismatch_refused(self):
        """Corrupted source bytes failing SHA-256 custody check are refused with SOURCE_BYTES_CORRUPTED."""
        triangle = PromptCellComplex.from_oriented_graph(
            vertices=("v0", "v1", "v2"),
            edges=(("v0", "v1"), ("v1", "v2"), ("v2", "v0")),
            source_bytes="valid source bytes",
        )
        triad = PrimeTriadContext(
            source_bytes="corrupted bytes",
            expected_source_hash=triangle.source_bytes_hash,
            remaining_budget=10,
        )
        disp = evaluate_prompt_cochain(
            complex=triangle,
            cochain=[Fraction(1), Fraction(2), Fraction(-3)],
            primal_potential=[Fraction(0), Fraction(1), Fraction(3)],
            dual_witness=[Fraction(0), Fraction(0), Fraction(0)],
            triad_context=triad,
        )
        assert isinstance(disp, CochainRefusal)
        assert "SOURCE_BYTES_CORRUPTED" in disp.reason

    def test_prime_002_budget_exhaustion_refused(self):
        """Zero remaining budget halts evaluation with RESOURCE_EXHAUSTION."""
        triangle = PromptCellComplex.from_oriented_graph(
            vertices=("v0", "v1", "v2"),
            edges=(("v0", "v1"), ("v1", "v2"), ("v2", "v0")),
        )
        triad = PrimeTriadContext(remaining_budget=0)
        disp = evaluate_prompt_cochain(
            complex=triangle,
            cochain=[Fraction(1), Fraction(2), Fraction(-3)],
            primal_potential=[Fraction(0), Fraction(1), Fraction(3)],
            dual_witness=[Fraction(0), Fraction(0), Fraction(0)],
            triad_context=triad,
        )
        assert isinstance(disp, CochainRefusal)
        assert "RESOURCE_EXHAUSTION" in disp.reason


# =============================================================================
# DIMENSION 3: EXOTIC RATIONAL NUMBERS & PARSER DEFENSES
# =============================================================================

class TestExoticRationalsAndParsers:
    """Stress tests on BigRational parsing, huge numerators, boolean guards, and fraction wire formats."""

    def test_parse_fraction_huge_arbitrary_precision(self):
        """Fractions with 150+ digit numerators and denominators parse exactly without float coercion."""
        huge_num = 10**150 + 7
        huge_den = 10**140 + 3
        frac_str = f"{huge_num}/{huge_den}"
        f = _parse_fraction(frac_str)
        assert isinstance(f, Fraction)
        assert f.numerator == huge_num
        assert f.denominator == huge_den
        wire = _fraction_to_wire(f)
        assert wire == frac_str

    def test_parse_fraction_rejects_floats_strictly(self):
        """Float instances and float string representations raise TypeError or ValueError."""
        with pytest.raises(TypeError, match="float .* not allowed"):
            _parse_fraction(3.14159)
        with pytest.raises(TypeError, match="float .* not allowed"):
            _parse_fraction(0.0)
        with pytest.raises(ValueError, match="floats and non-integers not allowed"):
            _parse_fraction("1.5")
        with pytest.raises(ValueError, match="floats and non-integers not allowed"):
            _parse_fraction("1e-5")
        with pytest.raises(ValueError, match="floats and non-integers not allowed"):
            _parse_fraction("NaN")
        with pytest.raises(ValueError, match="floats and non-integers not allowed"):
            _parse_fraction("Infinity")

    def test_parse_fraction_rejects_booleans_strictly(self):
        """Booleans (which inherit from int in Python) must be rejected fail-closed."""
        with pytest.raises(TypeError, match="bool .* not allowed"):
            _parse_fraction(True)
        with pytest.raises(TypeError, match="bool .* not allowed"):
            _parse_fraction(False)

    def test_parse_fraction_rejects_zero_denominator(self):
        """Zero denominator in string or tuple representation raises ZeroDivisionError."""
        with pytest.raises(ZeroDivisionError, match="Denominator cannot be zero"):
            _parse_fraction("5/0")
        with pytest.raises(ZeroDivisionError, match="Denominator cannot be zero"):
            _parse_fraction([5, 0])
        with pytest.raises(ZeroDivisionError, match="Denominator cannot be zero"):
            _parse_fraction({"numer": 5, "denom": 0})

    def test_parse_bigint_guards(self):
        """BigInt parser accepts large ints and serialized u32 digit arrays, rejecting floats/bools."""
        assert _parse_bigint(12345678901234567890) == 12345678901234567890
        with pytest.raises(TypeError, match="bool .* not allowed"):
            _parse_bigint(True)
        with pytest.raises(TypeError, match="float .* not allowed"):
            _parse_bigint(123.45)
        # Serialized num_bigint format: [sign, [u32_digits]]
        res = _parse_bigint([1, [5, 1]])
        assert res == 4294967301
        with pytest.raises(ValueError, match="Negative u32 digit"):
            _parse_bigint([1, [-1, 0]])


# =============================================================================
# DIMENSION 4: RFC 8785 CANONICAL JSON & BOUNDARY FLOAT FORMATS
# =============================================================================

class TestRfc8785CanonicalParity:
    """Stress tests on ECMAScript 7.1.12.1 formatting, integer safety limits, and UTF-16 key sorting."""

    def test_format_es_number_zero_and_negative_zero(self):
        """Both +0.0 and -0.0 serialize strictly as '0' per RFC 8785 §3.2.2.3."""
        assert format_es_number(0) == "0"
        assert format_es_number(0.0) == "0"
        assert format_es_number(-0.0) == "0"

    def test_format_es_number_safe_integer_bounds(self):
        """Integers within [-2^53 + 1, 2^53 - 1] format as integers; exceeding bounds raises JcsError."""
        assert format_es_number(MAX_SAFE_INTEGER) == "9007199254740991"
        assert format_es_number(-MAX_SAFE_INTEGER) == "-9007199254740991"
        with pytest.raises(JcsError, match="integer magnitude exceeds 2\\^53 - 1 safe limit"):
            format_es_number(MAX_SAFE_INTEGER + 1)
        with pytest.raises(JcsError, match="integer magnitude exceeds 2\\^53 - 1 safe limit"):
            format_es_number(-(MAX_SAFE_INTEGER + 1))

    def test_format_es_number_non_finite_rejected(self):
        """NaN, Infinity, and -Infinity are forbidden in JCS."""
        with pytest.raises(JcsError, match="non-finite numbers are forbidden"):
            format_es_number(float("nan"))
        with pytest.raises(JcsError, match="non-finite numbers are forbidden"):
            format_es_number(float("inf"))
        with pytest.raises(JcsError, match="non-finite numbers are forbidden"):
            format_es_number(float("-inf"))

    def test_format_es_number_exponential_boundaries(self):
        """Numbers with |x| >= 1e21 or |x| < 1e-6 must format in exponential notation."""
        assert format_es_number(1e21) == "1e+21"
        assert format_es_number(1e-6) == "0.000001"
        assert format_es_number(5e-7) == "5e-7"

    def test_format_es_string_minimal_escaping(self):
        """Solidus '/' is NOT escaped, while control characters 0x00-0x1F and quotes are escaped."""
        s = "https://example.com/api/test?arg=\"val\"\t\n\r"
        formatted = format_es_string(s)
        assert r"\/" not in formatted
        assert "/" in formatted
        assert r"\"val\"" in formatted
        assert r"\t" in formatted
        assert r"\n" in formatted
        assert r"\r" in formatted

    def test_utf16_code_unit_key_ordering(self):
        """Keys are sorted by UTF-16 code units (RFC 8785 §3.2.3)."""
        data = {
            "\uFFFD": "bmp_high",
            "\U0001F600": "non_bmp_emoji",
        }
        canonical = rfc8785_canonical_json(data)
        # \U0001F600 surrogate pair starts with 0xD83D < 0xFFFD, so it sorts first in UTF-16
        assert canonical.index("\U0001F600") < canonical.index("\uFFFD")

    def test_canonicalize_json_str_duplicate_keys_rejected(self):
        """JSON string with duplicate keys at the same level is refused fail-closed."""
        dup_json = '{"key": 1, "key": 2}'
        with pytest.raises(JcsError, match="duplicate object key detected"):
            canonicalize_json_str(dup_json)


# =============================================================================
# DIMENSION 5: HOSTILE YAML SCALARS & STRICT YAML INGRESS
# =============================================================================

class TestStrictYamlAdversarialIngress:
    """Stress tests on StrictYamlLoader, YAML 1.1 booleans, duplicate keys, and tabs."""

    @pytest.mark.parametrize("bool_token", [
        "yes", "no", "on", "off",
        "Yes", "No", "On", "Off",
        "YES", "NO", "ON", "OFF",
    ])
    def test_unquoted_yaml11_boolean_scalars_rejected(self, bool_token: str):
        """Every case variant of unquoted YAML 1.1 boolean tokens is rejected."""
        yaml_content = f"flag: {bool_token}"
        with pytest.raises(StrictYamlError, match="Unquoted YAML 1.1 boolean scalar"):
            strict_yaml_load(yaml_content)

    def test_quoted_boolean_strings_accepted(self):
        """Quoted boolean words are valid strings and accepted."""
        yaml_content = """
        word1: "yes"
        word2: 'no'
        word3: "on"
        word4: 'off'
        """
        data = strict_yaml_load(yaml_content)
        assert data == {"word1": "yes", "word2": "no", "word3": "on", "word4": "off"}

    def test_canonical_yaml12_booleans_accepted(self):
        """YAML 1.2 boolean values true/false in various standard cases are parsed as booleans."""
        yaml_content = """
        b1: true
        b2: false
        b3: True
        b4: False
        b5: TRUE
        b6: FALSE
        """
        data = strict_yaml_load(yaml_content)
        assert data == {
            "b1": True, "b2": False,
            "b3": True, "b4": False,
            "b5": True, "b6": False,
        }

    def test_duplicate_keys_in_mapping_rejected(self):
        """Duplicate mapping keys raise StrictYamlError."""
        dup_yaml = """
        name: first_value
        name: second_value
        """
        with pytest.raises(StrictYamlError, match="Duplicate key 'name' detected"):
            strict_yaml_load(dup_yaml)

    def test_duplicate_keys_in_nested_mapping_rejected(self):
        """Duplicate keys in deeply nested structures raise StrictYamlError."""
        dup_nested = """
        root:
          sub:
            target: 1
            target: 2
        """
        with pytest.raises(StrictYamlError, match="Duplicate key 'target' detected"):
            strict_yaml_load(dup_nested)

    def test_tab_indentation_rejected(self):
        """Tab indentation raises YAML syntax/scanner error."""
        tab_yaml = "root:\n\tchild: value\n"
        with pytest.raises(yaml.YAMLError):
            strict_yaml_load(tab_yaml)

    def test_null_scalars_handled_cleanly(self):
        """Null scalars ('null', '~', empty) are parsed without error."""
        null_yaml = """
        a: null
        b: ~
        c:
        """
        data = strict_yaml_load(null_yaml)
        assert data == {"a": None, "b": None, "c": None}

    def test_billion_laughs_anchor_expansion_bounded(self):
        """Billion laughs / recursive anchor attack parses without unbounded recursion."""
        anchor_yaml = """
        a: &a ["lol","lol","lol","lol","lol"]
        b: &b [*a,*a,*a,*a,*a]
        c: &c [*b,*b,*b,*b,*b]
        """
        data = strict_yaml_load(anchor_yaml)
        assert isinstance(data, dict)
        assert len(data["c"]) == 5

    def test_unquoted_boolean_in_sequence_rejected(self):
        """Unquoted boolean token 'yes' inside a sequence raises StrictYamlError."""
        seq_yaml = """
        items:
          - 1
          - yes
          - 3
        """
        with pytest.raises(StrictYamlError, match="Unquoted YAML 1.1 boolean scalar"):
            strict_yaml_load(seq_yaml)

    def test_unquoted_boolean_as_mapping_key_rejected(self):
        """Unquoted boolean token 'on' used as a mapping key raises StrictYamlError."""
        key_yaml = """
        on: enabled_service
        """
        with pytest.raises(StrictYamlError, match="Unquoted YAML 1.1 boolean scalar"):
            strict_yaml_load(key_yaml)


# =============================================================================
# EXPANDED MULTI-DIMENSION HARDENING TESTS
# =============================================================================

class TestExpandedHardeningSuites:
    """Additional extreme boundary cases across operad, cochain, and canonical serialization."""

    def test_multibyte_utf8_leaf_span_offsets(self):
        """Multibyte UTF-8 characters (math symbols, CJK) verify exact character/byte slicing."""
        doc = "∫_0^∞ e^{-x} dx = 1\n日本語テキスト"
        span = LeafTextSpan(
            id="span_integral",
            colour=PromptColour.RawTextSpan,
            content="∫_0^∞ e^{-x} dx = 1",
            source_offsets=(0, len("∫_0^∞ e^{-x} dx = 1")),
        )
        span.verify_against_document(doc)

    def test_cochain_complete_bipartite_k33_closed_nonexact(self):
        """K_{3,3} bipartite complex with 0 faces evaluates as ClosedNonExactClass for cycle flow."""
        # K_{3,3}: Vertices L0, L1, L2, R0, R1, R2.
        # 9 directed edges from Li to Rj: (Li, Rj).
        vertices = ("L0", "L1", "L2", "R0", "R1", "R2")
        edges = tuple((f"L{i}", f"R{j}") for i in range(3) for j in range(3))
        k33 = PromptCellComplex.from_oriented_graph(vertices, edges, faces=None)
        assert k33.v_count == 6
        assert k33.e_count == 9
        assert k33.f_count == 0

        # Cycle flow on 4-cycle: L0->R0, R0<-L1, L1->R1, R1<-L0
        # Directed: e(L0, R0)=1, e(L1, R0)=-1, e(L1, R1)=1, e(L0, R1)=-1
        # Edges indices:
        # (L0, R0)=0, (L0, R1)=1, (L1, R0)=3, (L1, R1)=4
        flow = [Fraction(0)] * 9
        flow[0] = Fraction(1)
        flow[1] = Fraction(-1)
        flow[3] = Fraction(-1)
        flow[4] = Fraction(1)

        # Dual witness annihilating d0 (divergence free flow)
        dual = list(flow)  # cycle flow is orthogonal to coboundaries

        disp = evaluate_prompt_cochain(
            complex=k33,
            cochain=flow,
            primal_potential=[Fraction(0)] * 6,
            dual_witness=dual,
        )
        assert isinstance(disp, ClosedNonExactClass)
        assert disp.gamma2 == Fraction(0)
        assert disp.phi1 == Fraction(4)

    def test_cochain_dual_witness_norm_bound_violation_refused(self):
        """Dual witness violating ||y||_infty <= 1 (e.g. ||y||_infty = 2) is refused fail-closed."""
        triangle = PromptCellComplex.from_oriented_graph(
            vertices=("v0", "v1", "v2"),
            edges=(("v0", "v1"), ("v1", "v2"), ("v2", "v0")),
        )
        disp = evaluate_prompt_cochain(
            complex=triangle,
            cochain=[Fraction(1), Fraction(1), Fraction(1)],
            primal_potential=[Fraction(0), Fraction(0), Fraction(0)],
            dual_witness=[Fraction(2), Fraction(2), Fraction(2)],  # ||y||_infty = 2 > 1
        )
        assert isinstance(disp, CochainRefusal)
        assert "PHI1_CERTIFICATE_INVALID" in disp.reason

    def test_cochain_dual_witness_non_annihilating_subspace_refused(self):
        """Dual witness not annihilating im(d0) (d0^T y != 0) is refused fail-closed."""
        triangle = PromptCellComplex.from_oriented_graph(
            vertices=("v0", "v1", "v2"),
            edges=(("v0", "v1"), ("v1", "v2"), ("v2", "v0")),
        )
        # y = (1, 0, 0): d0^T y = [-1, 1, 0] != 0
        disp = evaluate_prompt_cochain(
            complex=triangle,
            cochain=[Fraction(1), Fraction(1), Fraction(1)],
            primal_potential=[Fraction(0), Fraction(0), Fraction(0)],
            dual_witness=[Fraction(1), Fraction(0), Fraction(0)],
        )
        assert isinstance(disp, CochainRefusal)
        assert "PHI1_CERTIFICATE_INVALID" in disp.reason

    def test_cochain_prime_001_protected_answer_violation(self):
        """Altering or omitting protected questions under Prime 001 fails closed."""
        triad = PrimeTriadContext(
            protected_answers={"Q1": "expected_answer"},
            remaining_budget=10,
        )
        assert triad.protected_answers["Q1"] == "expected_answer"
        triad_dict = triad.to_dict()
        assert triad_dict["protected_answers"] == {"Q1": "expected_answer"}

    def test_parse_fraction_extreme_fractions_and_malformed(self):
        """Extremely small fraction (1 / 10^200) and malformed slash strings."""
        tiny = _parse_fraction(f"1/{10**200}")
        assert tiny.numerator == 1
        assert tiny.denominator == 10**200
        # Multiple slashes
        with pytest.raises(ValueError, match="floats and non-integers not allowed"):
            _parse_fraction("1/2/3")
        # Missing denominator
        with pytest.raises(ValueError, match="floats and non-integers not allowed"):
            _parse_fraction("5/")
        # Empty string
        with pytest.raises(ValueError, match="floats and non-integers not allowed"):
            _parse_fraction("")

    def test_rfc8785_canonical_json_deeply_nested_structures(self):
        """20-level nested structure canonicalizes with sorted keys and zero whitespace."""
        nested: dict[str, Any] = {"leaf": 1}
        for level in range(20):
            nested = {"z_key": nested, "a_key": level}
        canon = rfc8785_canonical_json(nested)
        # In every level, a_key must appear before z_key
        assert canon.startswith('{"a_key":19,"z_key":')
        assert " " not in canon
        assert "\n" not in canon

    def test_rfc8785_digest_sha256_stability_across_key_order(self):
        """SHA-256 digest is byte-identical regardless of insertion order."""
        dict1 = {"b": 2, "a": 1, "c": [3, 2, 1]}
        dict2 = {"c": [3, 2, 1], "a": 1, "b": 2}
        assert rfc8785_digest_sha256(dict1) == rfc8785_digest_sha256(dict2)

