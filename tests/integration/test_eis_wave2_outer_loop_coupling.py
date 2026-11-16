"""Integration tests for Wave 2 outer-loop StrandGenomeV1 EIS coupling.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from adversary.stage.infrastructure.default_adapters import FileCemeteryAdapter

from eis.domain.external_admission import HumanAntiSkillAdmissionDecisionV1
from eis.domain.pharmacy_models import LearningEvidencePreimageV1
from eis.domain.pharmacy_search import rule_content_bytes
from eis.domain.pharmacy_seeder import record_reproduced_failure
from eis.use_cases.antibody_admission import admit_antibody_by_operator
from pciv.domain.lamarckian import CochainResidualV1, ReproducedFailureCaseV1
from pciv.domain.models import ProtectedSpanV1
from pciv.use_cases.custody import ensure_caller_prompt_genome
from pciv.use_cases.immunity import resolve_civilization_immune_store
from pciv.use_cases.lamarckian_loop import (
    spawn_antibody_constrained_child,
    verify_lineage_cure,
)
from pciv.use_cases.transitive_immunity import FixedPointLineageTaintEngineV1
from pfp_core.caller_feedback import (
    CallerLineageContextV1,
    bind_strand_genome_to_immune_store,
)
from pfp_core.immunity import host_danger
from pfp_core.outer_loop_v1rc import StrandGenomeV1


def _sha256_ref(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def test_strand_genome_inherits_scoped_admitted_antibodies_and_excludes_unadmitted_or_out_of_scope(
    tmp_path: Path,
) -> None:
    store = resolve_civilization_immune_store(None, tmp_path, read_only=False)
    prompt_a = b"System: Strand A.\nUser: Return exact output."
    prompt_b = b"System: Strand B.\nUser: Return exact output."
    genome_a = ensure_caller_prompt_genome(prompt_a, {"domain": "wave2.a"})
    genome_b = ensure_caller_prompt_genome(prompt_b, {"domain": "wave2.b"})

    ab_a = record_reproduced_failure(
        prompt_id=genome_a.prompt_id,
        preimage=LearningEvidencePreimageV1(
            prompt_id=genome_a.prompt_id,
            prompt_utf8_bytes=prompt_a,
            candidate_reply_bytes=b"UNSAFE_TOKEN_A",
            failure_class="Wave2DefectA",
            failed_predicates=("no_token_a",),
            checker_id="host.public_smoke",
            checker_output_bytes=b'{"passed":false,"reason":"token A"}',
        ),
        target_pattern="UNSAFE_TOKEN_A",
        positive_fixture="def ok_a():\n    return 1\n",
        negative_fixture="UNSAFE_TOKEN_A",
        guidance_text="Avoid UNSAFE_TOKEN_A in exact replies.",
        run_id="run_w2_a",
        task_id="task_w2_a",
        scope_level="prompt_line",
        producer_actor="proposer_seat",
        repository=store.catalog,
        registry=store.registry,
    )
    rec_a = store.catalog.load_catalog()["antibodies"][ab_a.antibody_id]
    admit_antibody_by_operator(
        ab_a.antibody_id,
        HumanAntiSkillAdmissionDecisionV1(
            decision_id="dec_w2_a",
            issuer="human_reviewer_1",
            rule_bytes_sha256=_sha256_ref(rule_content_bytes(rec_a)),
            scope="prompt_line",
            receipt_sha256=_sha256_ref(b"dec_w2_a"),
        ),
        catalog=store.catalog,
        self_panel=("def ok_a():\n    return 1\n",),
    )

    ab_b_cand = record_reproduced_failure(
        prompt_id=genome_b.prompt_id,
        preimage=LearningEvidencePreimageV1(
            prompt_id=genome_b.prompt_id,
            prompt_utf8_bytes=prompt_b,
            candidate_reply_bytes=b"UNSAFE_TOKEN_B",
            failure_class="Wave2DefectB",
            failed_predicates=("no_token_b",),
            checker_id="host.public_smoke",
            checker_output_bytes=b'{"passed":false,"reason":"token B"}',
        ),
        target_pattern="UNSAFE_TOKEN_B",
        positive_fixture="def ok_b():\n    return 2\n",
        negative_fixture="UNSAFE_TOKEN_B",
        run_id="run_w2_b",
        task_id="task_w2_b",
        scope_level="prompt_line",
        producer_actor="proposer_seat",
        repository=store.catalog,
        registry=store.registry,
    )

    base_strand = StrandGenomeV1(genome_id="strand_wave2_seed", base_prompt="Solve cleanly.")
    bound_a = bind_strand_genome_to_immune_store(
        base_strand,
        store,
        CallerLineageContextV1(prompt_id=genome_a.prompt_id),
    )
    bound_b = bind_strand_genome_to_immune_store(
        base_strand,
        store,
        CallerLineageContextV1(prompt_id=genome_b.prompt_id),
    )
    assert [r.rule_id for r in bound_a.admitted_rules] == [ab_a.antibody_id]
    assert "Avoid UNSAFE_TOKEN_A in exact replies." in bound_a.rendered_text if hasattr(bound_a, "rendered_text") else (
        "Avoid UNSAFE_TOKEN_A in exact replies." in bound_a.render_prompt()
    )
    assert ab_b_cand.antibody_id not in [r.rule_id for r in bound_a.admitted_rules]
    assert bound_b.admitted_rules == ()


def test_outer_loop_strand_relapse_is_buried_and_tainted_while_cured_strand_adopts(
    tmp_path: Path,
) -> None:
    store = resolve_civilization_immune_store(None, tmp_path, read_only=False)
    parent_bytes = b"System: Core Rule.\nUser: Solve cleanly."
    span = ProtectedSpanV1(name="system_framing", start_byte=0, end_byte=18)
    parent_genome = ensure_caller_prompt_genome(
        parent_bytes,
        {"domain": "wave2.outer"},
        protected_spans=(span,),
    )
    failing_reply = b"def bad():\n    return WAVE2_FLOAT_SMUGGLE\n"
    witness_sha = hashlib.sha256(b"w2_witness").hexdigest()

    ab = record_reproduced_failure(
        prompt_id=parent_genome.prompt_id,
        preimage=LearningEvidencePreimageV1(
            prompt_id=parent_genome.prompt_id,
            prompt_utf8_bytes=parent_bytes,
            candidate_reply_bytes=failing_reply,
            failure_class="FloatSmuggling",
            failed_predicates=("exact_fraction",),
            checker_id="host.public_smoke",
            checker_output_bytes=b'{"passed":false,"reason":"float smuggle"}',
        ),
        target_pattern="WAVE2_FLOAT_SMUGGLE",
        positive_fixture="def good():\n    return 1\n",
        negative_fixture=failing_reply.decode("utf-8"),
        guidance_text="Forbid WAVE2_FLOAT_SMUGGLE in generated output.",
        run_id="run_w2_cure",
        task_id="task_w2_cure",
        producer_actor="proposer_seat",
        repository=store.catalog,
        registry=store.registry,
    )
    rec = store.catalog.load_catalog()["antibodies"][ab.antibody_id]
    admit_antibody_by_operator(
        ab.antibody_id,
        HumanAntiSkillAdmissionDecisionV1(
            decision_id="dec_w2_cure",
            issuer="human_reviewer_1",
            rule_bytes_sha256=_sha256_ref(rule_content_bytes(rec)),
            scope="prompt_line",
            receipt_sha256=_sha256_ref(b"dec_w2_cure"),
        ),
        catalog=store.catalog,
        self_panel=("def good():\n    return 1\n",),
    )

    strand = bind_strand_genome_to_immune_store(
        StrandGenomeV1(genome_id="strand_parent", base_prompt="Solve cleanly."),
        store,
        CallerLineageContextV1(prompt_id=parent_genome.prompt_id),
    )
    assert any(r.rule_id == ab.antibody_id for r in strand.admitted_rules)

    child_genome, child_bytes, receipt = spawn_antibody_constrained_child(
        parent_genome=parent_genome,
        parent_prompt_bytes=parent_bytes,
        antibody=store.catalog.load_catalog()["antibodies"][ab.antibody_id],
        falsification_witness_sha256=witness_sha,
        cochain_residual=CochainResidualV1("1/2", "0/1", "0/1"),
        receipt_store=store.receipt_store,
    )
    case = ReproducedFailureCaseV1(
        case_id="case_w2_relapse",
        prompt_utf8_bytes=parent_bytes,
        parent_failing_reply_bytes=failing_reply,
        failure_class="FloatSmuggling",
        witness_sha256=witness_sha,
    )
    cemetery = FileCemeteryAdapter(tmp_path / "cemetery")
    taint_relapse = FixedPointLineageTaintEngineV1()
    relapse = verify_lineage_cure(
        parent_genome=parent_genome,
        child_genome=child_genome,
        parent_prompt_bytes=parent_bytes,
        child_prompt_bytes=child_bytes,
        mutation_receipt=receipt,
        reproducing_case=case,
        child_reply_bytes=failing_reply,
        child_host_danger=host_danger("PUBLIC_CHECK_FAILED", "host.public_smoke", "relapsed"),
        held_out_passed=False,
        store=store,
        cemetery=cemetery,
        taint_engine=taint_relapse,
    )
    assert relapse.cure_status == "RELAPSED_BURIED"
    assert taint_relapse.is_tainted(child_genome.prompt_id) is True

    taint_cured = FixedPointLineageTaintEngineV1()
    cured = verify_lineage_cure(
        parent_genome=parent_genome,
        child_genome=child_genome,
        parent_prompt_bytes=parent_bytes,
        child_prompt_bytes=child_bytes,
        mutation_receipt=receipt,
        reproducing_case=case,
        child_reply_bytes=b"def good():\n    return 1\n",
        child_host_danger=None,
        held_out_passed=True,
        store=store,
        cemetery=cemetery,
        taint_engine=taint_cured,
    )
    assert cured.cure_status == "CURED_ADOPTED"
    assert taint_cured.is_tainted(child_genome.prompt_id) is False
