"""Unit tests for Prompt Hierarchy addressable URI, parsing, and gate evaluation.

Tests:
1. Canonical Prompt URI parsing, hierarchy ancestors, and rejection of malformed URIs.
2. Building PromptTreeNode from raw mappings and verifying AuthorityEffect invariant.
3. Parsing PFP Stage 4 prompt (p_research_04.yaml) and companion sidecar binding.
4. Two-Signal Danger Gate and Anti-Op gating:
   - Clean payload passes.
   - Procedural Anti-Op refuses unlicensed keywords or syntax violations.
   - Empirical Antibody requires BOTH Signal 1 (Epitope) and Signal 2 (Host Danger).
   - Candidate (unadmitted) antibodies remain inert even if both signals trigger.

AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from omega_engine_epistemic_immune_system.domain.pharmacy_catalog import (
    PharmacyCatalogRepository,
)
from omega_engine_epistemic_immune_system.infrastructure.pharmacy_writer import (
    filesystem_catalog_bytes,
)
from omega_engine_operads.domain.prompt_hierarchy import (
    AntiOpBinding,
    AntibodyBinding,
    PromptGateReceipt,
    PromptTreeNode,
    PromptUri,
    load_prompt_node_from_binding_dict,
    parse_prompt_uri,
)
from omega_engine_operads.application.prompt_gates import evaluate_prompt_gates
from omega_engine_operads.infrastructure.parser.prompt_hierarchy_loader import (
    load_prompt_node_from_pfp_yaml,
)


def _find_repo_root() -> Path:
    current = Path(__file__).resolve().parent
    for parent in [current, *current.parents]:
        if (parent / ".agents").is_dir() and (parent / "pyproject.toml").is_file():
            return parent
    raise RuntimeError("Could not find repository root")


def _evaluate_registered_prompt(node, payload, **kwargs):
    # Fixture detectors stand for host implementations outside these keyword tests.
    from omega_engine_operads.domain.prompt_hierarchy.evaluator import DEFAULT_KEYWORD_PATTERNS
    detectors = {op.op_id: (lambda value: False) for op in node.anti_ops
                 if not DEFAULT_KEYWORD_PATTERNS.get(op.op_id)}
    detectors.update(kwargs.pop("custom_detectors", {}) or {})
    return evaluate_prompt_gates(node, payload, custom_detectors=detectors, **kwargs)


# ---------------------------------------------------------------------------
# 1. Prompt URI Tests
# ---------------------------------------------------------------------------

def test_prompt_uri_parsing_valid() -> None:
    uri_str = "prompt://education/pfp/workflows/research/stage_04/P_RESEARCH_04"
    uri = parse_prompt_uri(uri_str)

    assert uri.raw_uri == uri_str
    assert uri.domain == "education"
    assert uri.subdomain == "pfp"
    assert uri.task == "workflows"
    assert uri.stage == "research"
    assert uri.prompt_id == "stage_04"
    assert uri.subprompt_id == "P_RESEARCH_04"
    assert str(uri) == uri_str


def test_prompt_uri_ancestor_chain() -> None:
    uri = parse_prompt_uri("prompt://education/pfp/workflows/research/P_RESEARCH_04")
    ancestors = uri.ancestor_uris()

    assert ancestors == (
        "prompt://education",
        "prompt://education/pfp",
        "prompt://education/pfp/workflows",
        "prompt://education/pfp/workflows/research",
        "prompt://education/pfp/workflows/research/P_RESEARCH_04",
    )


def test_prompt_uri_invalid_format_raises() -> None:
    with pytest.raises(ValueError, match="Invalid prompt URI format"):
        parse_prompt_uri("https://education/pfp/workflows/research/stage_04/P04")

    with pytest.raises(ValueError, match="Invalid prompt URI format"):
        parse_prompt_uri("prompt://education/pfp")


# ---------------------------------------------------------------------------
# 2. PromptTreeNode & Binding Dict Tests
# ---------------------------------------------------------------------------

def test_load_prompt_node_from_binding_dict() -> None:
    data = {
        "prompt_uri": "prompt://test_domain/sub/task/stage/PROMPT_TEST",
        "title": "Test Prompt Node",
        "description": "A node for testing",
        "oewas_anti_ops": [
            {
                "op_id": "test.refuse_foo",
                "inspects_slot": "candidate_text",
                "refusal_code": "ANTI_FOO",
                "description": "Refuse foo occurrences",
            }
        ],
        "oeeis_antibodies": [
            {
                "antibody_id": "ab_test_antibody",
                "signal1_epitope": "forbidden_epitope",
                "signal2_required_danger": "HOST_TEST_FAILURE",
                "minimum_status": "admitted",
            }
        ],
    }
    node = load_prompt_node_from_binding_dict(data)

    assert node.uri.prompt_id == "PROMPT_TEST"
    assert node.title == "Test Prompt Node"
    assert len(node.anti_ops) == 1
    assert node.anti_ops[0].op_id == "test.refuse_foo"
    assert len(node.antibodies) == 1
    assert node.antibodies[0].antibody_id == "ab_test_antibody"
    assert node.authority_effect == "None"


def test_prompt_node_authority_effect_strictly_none() -> None:
    uri = parse_prompt_uri("prompt://test_domain/sub/task/stage/PROMPT_TEST")
    with pytest.raises(ValueError, match="AuthorityEffect must be 'None'"):
        PromptTreeNode(
            uri=uri,
            title="Invalid Authority Node",
            authority_effect="ENFORCED",  # type: ignore
        )


def _pfp_research_04_path() -> Path:
    repo_root = _find_repo_root()
    fixture = (
        repo_root
        / "omega_engine_operads"
        / "tests"
        / "fixtures"
        / "prompt_hierarchy"
        / "p_research_04.yaml"
    )
    if fixture.is_file():
        return fixture
    return (
        repo_root
        / "omega_engine_education"
        / "documentation"
        / "004_oepfp"
        / "workflows"
        / "research"
        / "prompts"
        / "p_research_04.yaml"
    )


# ---------------------------------------------------------------------------
# 3. PFP Stage 4 Prompt & Companion Sidecar Parsing
# ---------------------------------------------------------------------------

def test_load_pfp_research_04_prompt_node() -> None:
    pfp_yaml_path = _pfp_research_04_path()
    assert pfp_yaml_path.is_file(), f"Missing PFP Stage 4 file at {pfp_yaml_path}"

    node = load_prompt_node_from_pfp_yaml(pfp_yaml_path)

    # Validate Canonical Address
    assert node.uri.raw_uri == "prompt://education/pfp/workflows/research/stage_04/P_RESEARCH_04"
    assert node.uri.domain == "education"
    assert node.uri.prompt_id == "stage_04"
    assert node.uri.subprompt_id == "P_RESEARCH_04"

    # Validate Anti-Ops merged from both p_research_04.yaml and p_research_04.binding.yaml
    anti_op_ids = {op.op_id for op in node.anti_ops}
    assert "pfp.refuse_unlicensed_multiplication" in anti_op_ids
    assert "pfp.refuse_unlicensed_causality" in anti_op_ids
    assert "pfp.refuse_unmapped_continuum_import" in anti_op_ids
    assert "glossa.refuse_missing_claim_envelope" in anti_op_ids
    assert "sfh.refuse_bare_except" in anti_op_ids

    # Validate Antibodies merged from p_research_04.binding.yaml
    antibody_ids = {ab.antibody_id for ab in node.antibodies}
    assert "ab_q40_bitmask_assignment_inversion" in antibody_ids
    assert "ab_adversarial_refusal_bypass_leakage" in antibody_ids



# ---------------------------------------------------------------------------
# 4. Prompt Gate Evaluation Tests (Two-Signal Danger Gate & Anti-Ops)
# ---------------------------------------------------------------------------

def test_evaluate_clean_payload_passes() -> None:
    repo_root = _find_repo_root()
    pfp_yaml_path = _pfp_research_04_path()
    node = load_prompt_node_from_pfp_yaml(pfp_yaml_path)
    catalog = PharmacyCatalogRepository(repo_root, byte_source=filesystem_catalog_bytes).load_catalog()

    clean_payload = {
        "candidate_text": "Derivation of discrete projection on finite Hilbert space without continuum assumptions.",
        "candidate_code": "def project(v):\n    try:\n        return v.norm()\n    except ValueError:\n        return 0\n",
    }

    receipt = _evaluate_registered_prompt(
        node,
        clean_payload,
        catalog=catalog,
        host_danger_signals=(),
    )

    assert receipt.passed is True
    assert receipt.status == "PASS"
    assert receipt.anti_ops_fired == ()
    assert receipt.antibodies_fired == ()
    assert receipt.refusal_code is None
    assert receipt.authority_effect == "None"


def test_evaluate_anti_op_refusal_unmapped_continuum() -> None:
    repo_root = _find_repo_root()
    pfp_yaml_path = _pfp_research_04_path()
    node = load_prompt_node_from_pfp_yaml(pfp_yaml_path)
    catalog = PharmacyCatalogRepository(repo_root, byte_source=filesystem_catalog_bytes).load_catalog()

    violating_payload = {
        "candidate_text": "We formulate the field equations over a smooth manifold and continuous physics.",
        "candidate_code": "pass",
    }

    receipt = _evaluate_registered_prompt(
        node,
        violating_payload,
        catalog=catalog,
    )

    assert receipt.passed is False
    assert receipt.status == "REFUSED"
    assert "pfp.refuse_unmapped_continuum_import" in receipt.anti_ops_fired
    assert receipt.refusal_code == "ANTI_UNMAPPED_CONTINUUM_IMPORT"


def test_evaluate_custom_detector_anti_op() -> None:
    repo_root = _find_repo_root()
    pfp_yaml_path = _pfp_research_04_path()
    node = load_prompt_node_from_pfp_yaml(pfp_yaml_path)
    catalog = PharmacyCatalogRepository(repo_root, byte_source=filesystem_catalog_bytes).load_catalog()

    custom_detectors = {
        "sfh.refuse_bare_except": lambda code: bool(code and "except:" in str(code)),
    }

    violating_code_payload = {
        "candidate_text": "Clean discrete math",
        "candidate_code": "try:\n    do_work()\nexcept:\n    pass",
    }

    receipt = _evaluate_registered_prompt(
        node,
        violating_code_payload,
        catalog=catalog,
        custom_detectors=custom_detectors,
    )

    assert receipt.passed is False
    assert receipt.status == "REFUSED"
    assert "sfh.refuse_bare_except" in receipt.anti_ops_fired
    assert receipt.refusal_code == "SFH-PY-001"


def test_two_signal_danger_gate_requires_both_signals() -> None:
    """An admitted antibody requires Signal 1 (Epitope) AND Signal 2 (Host Danger)."""
    repo_root = _find_repo_root()
    pfp_yaml_path = _pfp_research_04_path()
    node = load_prompt_node_from_pfp_yaml(pfp_yaml_path)
    catalog = PharmacyCatalogRepository(repo_root, byte_source=filesystem_catalog_bytes).load_catalog()

    # Payload matching the epitope of admitted antibody 'ab_q40_bitmask_assignment_inversion'
    epitope_payload = {
        "candidate_text": "Investigating potential bitmask assignment inversion in state vector.",
        "candidate_code": "pass",
    }

    # Case A: Signal 1 present, but NO host danger signal (Signal 2 absent) -> MUST PASS
    receipt_no_danger = _evaluate_registered_prompt(
        node,
        epitope_payload,
        catalog=catalog,
        host_danger_signals=(),
    )
    assert receipt_no_danger.passed is True
    assert receipt_no_danger.antibodies_fired == ()

    # Case B: Both Signal 1 AND Signal 2 present -> MUST REFUSE
    receipt_with_danger = _evaluate_registered_prompt(
        node,
        epitope_payload,
        catalog=catalog,
        host_danger_signals=("HOST_EVALUATOR_ALERT",),
    )
    assert receipt_with_danger.passed is False
    assert receipt_with_danger.status == "REFUSED"
    assert "ab_q40_bitmask_assignment_inversion" in receipt_with_danger.antibodies_fired
    assert receipt_with_danger.refusal_code == "ANTIBODY_ACTIVATION:ab_q40_bitmask_assignment_inversion"


def test_candidate_antibody_remains_inert() -> None:
    """An antibody with 'candidate' status never fires even if both signals are present."""
    repo_root = _find_repo_root()
    pfp_yaml_path = _pfp_research_04_path()
    node = load_prompt_node_from_pfp_yaml(pfp_yaml_path)
    catalog = PharmacyCatalogRepository(repo_root, byte_source=filesystem_catalog_bytes).load_catalog()

    # 'ab_adversarial_refusal_bypass_leakage' is candidate, not admitted
    candidate_antibody_id = "ab_adversarial_refusal_bypass_leakage"
    assert catalog["antibodies"][candidate_antibody_id]["pharmacy_status"] == "candidate"

    payload = {
        "candidate_text": "Observed adversarial refusal bypass in evaluator output.",
        "candidate_code": "pass",
    }


    receipt = _evaluate_registered_prompt(
        node,
        payload,
        catalog=catalog,
        host_danger_signals=("HOST_TEST_FAILURE",),
    )

    # Must remain inert because status is candidate, not admitted
    assert receipt.passed is True
    assert candidate_antibody_id not in receipt.antibodies_fired


def test_receipt_to_dict_format() -> None:
    receipt = PromptGateReceipt(
        prompt_uri="prompt://test/sub/task/st/id",
        status="PASS",
        anti_ops_evaluated=("op1",),
        antibodies_evaluated=("ab1",),
    )
    d = receipt.to_dict()
    assert d["schema_version"] == "omega.prompt_hierarchy.gate_receipt.v1"
    assert d["prompt_uri"] == "prompt://test/sub/task/st/id"
    assert d["status"] == "PASS"
    assert d["authority_effect"] == "None"
    assert d["anti_ops_evaluated"] == ["op1"]
    assert d["anti_ops_fired"] == []


def test_unimplemented_anti_op_refuses():
    node = PromptTreeNode(uri=PromptUri.parse("prompt://test/domain/task/stage/P1"), title="test",
                          anti_ops=(AntiOpBinding("missing.detector", "candidate_text", "UNSAFE"),))
    receipt = evaluate_prompt_gates(node, {"candidate_text": "clean"})
    assert not receipt.passed
    assert receipt.refusal_code == "NOT_EXECUTABLE"


def test_missing_inspected_slot_refuses():
    node = PromptTreeNode(uri=PromptUri.parse("prompt://test/domain/task/stage/P1"), title="test",
                          anti_ops=(AntiOpBinding("pfp.refuse_unlicensed_multiplication", "candidate_text", "UNSAFE"),))
    receipt = evaluate_prompt_gates(node, {})
    assert not receipt.passed
    assert receipt.refusal_code == "NOT_EXECUTABLE"


def test_empty_danger_binding_cannot_replace_independent_signal():
    catalog = PharmacyCatalogRepository(_find_repo_root(), byte_source=filesystem_catalog_bytes).load_catalog()
    antibody = AntibodyBinding("ab_q40_bitmask_assignment_inversion", "bitmask", "")
    node = PromptTreeNode(uri=PromptUri.parse("prompt://test/domain/task/stage/P1"),
                          title="test", antibodies=(antibody,))
    no_danger = evaluate_prompt_gates(node, {"candidate_text": "bitmask"}, catalog=catalog)
    assert no_danger.passed
    assert no_danger.antibodies_fired == ()
    with_danger = evaluate_prompt_gates(node, {"candidate_text": "bitmask"}, catalog=catalog,
                                       host_danger_signals=("HOST_EVALUATOR_ALERT",))
    assert not with_danger.passed
    assert with_danger.antibodies_fired == (antibody.antibody_id,)
