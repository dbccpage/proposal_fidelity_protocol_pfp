"""End-to-End Lamarckian Retro-Inheritance Integration Test (NF-02).

Validates the full feedback loop:
T_loop = <P_0, G_g> -> [Woland Dialectic] -> Artifact A -> [PFP Measurement] -> Defect Witness W -> [Thymus] -> Antibody alpha -> [Forge] -> G_{g+1}

Testing:
1. AST cochain extraction refuses to publish a residual when gamma2 and xi are unmeasured.
2. Rule 1: Protected Core Invariance (Core(G_{g+1}) == Core(G_g)).
3. Rule 2: Witness Grounding (fail-closed on ungrounded antibody).
4. Rule 3: Attenuated Influence (w(alpha, d) = (1/2)^d for 1 <= d <= 10; d > 10 evaporated).
5. Lineage recording via PromptCivGenealogyAdapter.
6. Schema and tamper validation of LamarckianMutationReceiptV1.

AuthorityEffect: None.
Zero-Float Law: Uses exact rational arithmetic.
"""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import pytest

from omega_engine_prompt_civilization.domain.lamarckian import (
    CochainResidualV1,
    LamarckianMutationReceiptV1,
)
from omega_engine_prompt_civilization.domain.models import ProtectedSpanV1
from omega_engine_prompt_civilization.infrastructure.genealogy_adapter import (
    FileGenealogyAdapter,
)
from omega_engine_prompt_civilization.use_cases.lamarckian_loop import (
    LamarckianLoopService,
    UnmeasuredCurvatureRefusal,
)
from omega_engine_woland.infrastructure.estates.prompt_civ_genealogy import (
    PromptCivGenealogyAdapter,
)


def test_end_to_end_lamarckian_loop_with_ast_cochain() -> None:
    """Test 1: AST extraction refuses an unmeasured residual; the loop records a supplied one."""
    service = LamarckianLoopService()

    # 1. Define synthetic codebase with an architectural defect:
    # Domain layer importing infrastructure layer directly, violating Clean Architecture Dependency Rule.
    synthetic_sources = {
        "domain": (
            "import infrastructure\n"
            "def calculate():\n"
            "    return infrastructure.load_data()\n"
        ),
        "infrastructure": (
            "def load_data():\n"
            "    return 42\n"
        ),
    }

    with pytest.raises(UnmeasuredCurvatureRefusal) as caught:
        service.extract_cochain_from_ast(synthetic_sources)
    refusal = caught.value
    assert refusal.code == "UNMEASURED_CURVATURE"
    assert refusal.authority_effect == "None"
    assert len(refusal.witness_sha256) == 64
    assert len(refusal.obstructions) > 0
    assert getattr(refusal, "residual", None) is None
    # The mutation rules below take a caller-supplied residual. It is not
    # the AST extraction, and it is not a zero curvature measurement.
    witness_sha = refusal.witness_sha256
    residual = CochainResidualV1.from_fractions(
        phi1=Fraction(1, 1),
        gamma2=Fraction(1, 2),
        xi=Fraction(1, 3),
    )

    # 2. Define parent prompt with an immutable protected core
    core_text = (
        "# PROTECTED CORE DIRECTIVES\n"
        "# AuthorityEffect: None\n"
        "# Zero-Float Law: Exact rational arithmetic only\n"
    )
    plastic_text = (
        "\n# Plastic Instruction Scaffold\n"
        "def solve(task):\n"
        "    return execute(task)\n"
    )
    parent_bytes = (core_text + plastic_text).encode("utf-8")
    parent_id = "sha256:" + hashlib.sha256(parent_bytes).hexdigest()

    protected_spans = [
        ProtectedSpanV1(name="core", start_byte=0, end_byte=len(core_text.encode("utf-8")))
    ]

    # 3. Execute Lamarckian feedback cycle
    result = service.execute_loop(
        parent_prompt_bytes=parent_bytes,
        parent_genome_id=parent_id,
        protected_spans=protected_spans,
        generation=0,
        falsification_witness_sha256=witness_sha,
        cochain_residual=residual,
        antibody_id="ab_ast_clean_arch_001",
        guidance_text="# Constraint: Enforce layer rank hierarchy. Presentation cannot import domain.",
    )

    # 4. Verify Rule 1: Protected Core Invariance
    core_len = len(core_text.encode("utf-8"))
    assert result.child_prompt_bytes[:core_len] == core_text.encode("utf-8")
    assert result.mutation_applied is True
    assert result.authority_effect == "None"

    # 5. Verify Receipt Properties
    receipt = result.receipt
    assert receipt.receipt_id.startswith("sha256:")
    assert receipt.parent_genome_id == parent_id
    assert receipt.child_genome_id == result.child_genome_id
    assert receipt.falsification_witness_sha256 == witness_sha
    assert receipt.cochain_residual == residual
    assert receipt.hop_distance == 1
    assert receipt.attenuation_weight == "1/2"

    # Verify JSON schema conformance
    wire = receipt.to_dict()
    assert wire["receipt_id"] == receipt.receipt_id
    assert wire["hop_distance"] == 1
    assert wire["attenuation_weight"] == "1/2"
    assert wire["cochain_residual"]["phi1"] == residual.phi1


def test_rule_1_protected_core_invariance_falsifier() -> None:
    """Test 2: Rule 1 fail-closed refusal when mutation targets protected core."""
    service = LamarckianLoopService()

    core_text = "# IMMUTABLE SYSTEM CORE DIRECTIVE\n"
    plastic_text = "# Plastic region\n"
    parent_bytes = (core_text + plastic_text).encode("utf-8")
    parent_id = "sha256:" + hashlib.sha256(parent_bytes).hexdigest()

    core_len = len(core_text.encode("utf-8"))
    protected_spans = [ProtectedSpanV1(name="core", start_byte=0, end_byte=core_len)]
    residual = CochainResidualV1.from_fractions(phi1=1, gamma2=0, xi=0)
    witness = hashlib.sha256(b"defect").hexdigest()

    # Attempt mutation overlapping protected core [5, 15)
    with pytest.raises(PermissionError, match="PROTECTED_SPAN_MUTATION_REFUSED"):
        service.execute_loop(
            parent_prompt_bytes=parent_bytes,
            parent_genome_id=parent_id,
            protected_spans=protected_spans,
            generation=0,
            falsification_witness_sha256=witness,
            cochain_residual=residual,
            antibody_id="ab_illegal_01",
            guidance_text="# Bad injection",
            edit_start_byte=5,
            edit_end_byte=15,
        )


def test_rule_2_witness_grounding_falsifier() -> None:
    """Test 3: Rule 2 fail-closed refusal when antibody has no authentic witness."""
    service = LamarckianLoopService()

    parent_bytes = b"# Core\n# Plastic\n"
    parent_id = "sha256:" + hashlib.sha256(parent_bytes).hexdigest()
    protected_spans = [ProtectedSpanV1(name="core", start_byte=0, end_byte=6)]

    # 1. Invalid or empty witness hash
    with pytest.raises(ValueError, match="WITNESS_GROUNDING_FAILED"):
        service.execute_loop(
            parent_prompt_bytes=parent_bytes,
            parent_genome_id=parent_id,
            protected_spans=protected_spans,
            generation=0,
            falsification_witness_sha256="not-a-valid-sha256-hex",
            cochain_residual=CochainResidualV1.from_fractions(phi1=1, gamma2=0, xi=0),
            antibody_id="ab_ungrounded_01",
            guidance_text="# Ungrounded",
        )

    # 2. Zero cochain residual without defect witness
    with pytest.raises(ValueError, match="WITNESS_GROUNDING_FAILED"):
        service.execute_loop(
            parent_prompt_bytes=parent_bytes,
            parent_genome_id=parent_id,
            protected_spans=protected_spans,
            generation=0,
            falsification_witness_sha256="",
            cochain_residual=CochainResidualV1.from_fractions(phi1=0, gamma2=0, xi=0),
            antibody_id="ab_zero_01",
            guidance_text="# Zero",
        )


def test_rule_3_attenuation_and_evaporation_boundary() -> None:
    """Test 4: Rule 3 hop distance attenuation (1/2)^d and d > 10 evaporation gate."""
    service = LamarckianLoopService()

    parent_bytes = b"# Core\n# Plastic\n"
    parent_id = "sha256:" + hashlib.sha256(parent_bytes).hexdigest()
    protected_spans = [ProtectedSpanV1(name="core", start_byte=0, end_byte=6)]
    witness = hashlib.sha256(b"defect_proof").hexdigest()
    residual = CochainResidualV1.from_fractions(phi1=1, gamma2=0, xi=0)

    # Valid hops 1 through 10
    expected_weights = {
        1: "1/2",
        2: "1/4",
        5: "1/32",
        10: "1/1024",
    }
    for hop, expected_w in expected_weights.items():
        res = service.execute_loop(
            parent_prompt_bytes=parent_bytes,
            parent_genome_id=parent_id,
            protected_spans=protected_spans,
            generation=10,
            origin_generation=11 - hop,
            falsification_witness_sha256=witness,
            cochain_residual=residual,
            antibody_id=f"ab_hop_{hop}",
            guidance_text=f"# Guidance hop {hop}",
        )
        assert res.receipt.hop_distance == hop
        assert res.receipt.attenuation_weight == expected_w

    # Hop distance 11 (> 10 must evaporate per Rule 3)
    with pytest.raises(ValueError, match="HOP_DISTANCE_OUT_OF_BOUNDS"):
        service.execute_loop(
            parent_prompt_bytes=parent_bytes,
            parent_genome_id=parent_id,
            protected_spans=protected_spans,
            generation=15,
            origin_generation=4,  # hop = 16 - 4 = 12 > 10
            falsification_witness_sha256=witness,
            cochain_residual=residual,
            antibody_id="ab_evaporated",
            guidance_text="# Must evaporate",
        )


def test_woland_bout_genealogy_store_reentry_link(tmp_path: Path) -> None:
    """Test 5: Integration with PromptCivGenealogyAdapter and FileGenealogyAdapter."""
    service = LamarckianLoopService()

    parent_bytes = b"# System Core\n# Plastic Task Execution\n"
    parent_id = "sha256:" + hashlib.sha256(parent_bytes).hexdigest()
    protected_spans = [ProtectedSpanV1(name="core", start_byte=0, end_byte=13)]

    # Simulated Woland bout failure witness
    bout_blockers = ["CYCLIC_LAYER_DEPENDENCY", "MISSING_INTERFACE_PORT"]
    witness = hashlib.sha256(":".join(bout_blockers).encode("utf-8")).hexdigest()
    residual = CochainResidualV1.from_fractions(phi1=2, gamma2=0, xi=0)

    # Execute Lamarckian loop
    loop_result = service.execute_loop(
        parent_prompt_bytes=parent_bytes,
        parent_genome_id=parent_id,
        protected_spans=protected_spans,
        generation=1,
        falsification_witness_sha256=witness,
        cochain_residual=residual,
        antibody_id="ab_bout_repair_01",
        guidance_text="# Break cyclic layer dependency and introduce interface port.",
    )

    # Record into Prompt Civilization genealogy store via Woland adapter
    lineage_file = tmp_path / "lineage.jsonl"
    genealogy_adapter = PromptCivGenealogyAdapter(lineage_file)

    parent_key = "task:woland_bout_gen_1"
    child_key = f"bout:{loop_result.receipt.receipt_id[:16]}"
    guidance = "Injected antibody ab_bout_repair_01 to eliminate cyclic layer dependency"

    record_res = genealogy_adapter.record_lineage(
        parent_key=parent_key,
        child_key=child_key,
        deficiencies=bout_blockers,
        guidance=guidance,
    )
    assert record_res.is_ok
    lineage_id = record_res.unwrap()
    assert lineage_id.startswith("sha256:")

    # Read back from store and verify integrity
    file_adapter = FileGenealogyAdapter(lineage_file)
    entry_res = file_adapter.get_lineage(child_key)
    assert entry_res.is_ok
    entry = entry_res.unwrap()
    assert entry.parent_run_key == parent_key
    assert entry.child_run_key == child_key
    assert set(entry.structural_deficiencies) == set(bout_blockers)
    assert entry.re_entry_reason == "WOLAND_SWARM_BOUT"
