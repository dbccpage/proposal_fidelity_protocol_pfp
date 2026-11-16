"""Integration falsifiers for closed-loop EIS feedback into calling prompts and bouts.

Each test exercises one of the four motions (collection, feedback, Act III sieve,
and lineage immunity/cure) against detached-cabinet failure modes.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


def _sha256_ref(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _seed_and_admit_test_antibody(
    store,
    *,
    prompt_id: str,
    prompt_bytes: bytes,
    reply_bytes: bytes,
    failure_class: str,
    failed_predicates: tuple[str, ...],
    checker_output_bytes: bytes,
    target_pattern: str,
    positive_fixture: str,
    negative_fixture: str,
    scope_level: str = "prompt_line",
    admission_scope: str = "prompt_line",
    decision_id: str,
    run_id: str,
    task_id: str,
    guidance_text: str = "",
):
    from eis.domain.external_admission import HumanAntiSkillAdmissionDecisionV1
    from eis.domain.pharmacy_models import LearningEvidencePreimageV1
    from eis.domain.pharmacy_search import rule_content_bytes
    from eis.domain.pharmacy_seeder import record_reproduced_failure
    from eis.use_cases.antibody_admission import admit_antibody_by_operator

    preimage = LearningEvidencePreimageV1(
        prompt_id=prompt_id,
        prompt_utf8_bytes=prompt_bytes,
        candidate_reply_bytes=reply_bytes,
        failure_class=failure_class,
        failed_predicates=failed_predicates,
        checker_id="host.public_smoke",
        checker_output_bytes=checker_output_bytes,
    )
    ab = record_reproduced_failure(
        prompt_id=prompt_id,
        preimage=preimage,
        target_pattern=target_pattern,
        positive_fixture=positive_fixture,
        negative_fixture=negative_fixture,
        guidance_text=guidance_text,
        run_id=run_id,
        task_id=task_id,
        scope_level=scope_level,
        producer_actor="proposer_seat",
        repository=store.catalog,
        registry=store.registry,
    )
    saved_rec = store.catalog.load_catalog()["antibodies"][ab.antibody_id]
    rule_digest = "sha256:" + hashlib.sha256(rule_content_bytes(saved_rec)).hexdigest()
    admit_antibody_by_operator(
        ab.antibody_id,
        HumanAntiSkillAdmissionDecisionV1(
            decision_id=decision_id,
            issuer="human_reviewer_1",
            rule_bytes_sha256=rule_digest,
            scope=admission_scope,
            receipt_sha256=_sha256_ref(decision_id.encode("utf-8")),
        ),
        catalog=store.catalog,
        self_panel=(positive_fixture,),
    )
    return ab


def test_pharmacy_write_without_prompt_id_or_evidence_preimage_is_refused(tmp_path: Path) -> None:
    """Collection must bind prompt_id and full prompt/reply/checker byte preimage."""
    from eis.domain.pharmacy_catalog import PharmacyCatalogRepository
    from eis.domain.pharmacy_models import (
        LearningEvidencePreimageV1,
        compute_learning_evidence_sha256,
    )
    from eis.domain.pharmacy_seeder import record_reproduced_failure
    from eis.infrastructure.pharmacy_writer import (
        filesystem_byte_writer,
        filesystem_catalog_bytes,
    )
    from pciv.use_cases.custody import ensure_caller_prompt_genome
    from pfp_core.immunity import AntibodyRegistry

    prompt_bytes = b"System: Use exact rational arithmetic.\nUser: Compute trace."
    reply_bytes = b"def f(): return float(0.5)"
    checker_bytes = json.dumps({"passed": False, "predicate": "no_float_cast"}).encode("utf-8")

    genome = ensure_caller_prompt_genome(prompt_bytes, {"domain": "pfp.test"})
    preimage = LearningEvidencePreimageV1(
        prompt_id=genome.prompt_id,
        prompt_utf8_bytes=prompt_bytes,
        candidate_reply_bytes=reply_bytes,
        failure_class="CounterfeitExactness",
        failed_predicates=("no_float_cast",),
        checker_id="host.public_smoke",
        checker_output_bytes=checker_bytes,
    )

    # Reject missing/empty prompt_id or missing host checker output bytes+predicates.
    with pytest.raises(ValueError):
        LearningEvidencePreimageV1(
            prompt_id="",
            prompt_utf8_bytes=prompt_bytes,
            candidate_reply_bytes=reply_bytes,
            failure_class="CounterfeitExactness",
            failed_predicates=("no_float_cast",),
            checker_id="host.public_smoke",
            checker_output_bytes=checker_bytes,
        )
    with pytest.raises(ValueError):
        LearningEvidencePreimageV1(
            prompt_id=genome.prompt_id,
            prompt_utf8_bytes=prompt_bytes,
            candidate_reply_bytes=reply_bytes,
            failure_class="CounterfeitExactness",
            failed_predicates=(),
            checker_id="host.public_smoke",
            checker_output_bytes=b"",
        )

    # Preimage digest changes when 1 byte of prompt, reply, or checker output changes.
    base_digest = compute_learning_evidence_sha256(preimage)
    d_prompt = compute_learning_evidence_sha256(
        LearningEvidencePreimageV1(
            prompt_id=genome.prompt_id,
            prompt_utf8_bytes=prompt_bytes + b" ",
            candidate_reply_bytes=reply_bytes,
            failure_class="CounterfeitExactness",
            failed_predicates=("no_float_cast",),
            checker_id="host.public_smoke",
            checker_output_bytes=checker_bytes,
        )
    )
    d_reply = compute_learning_evidence_sha256(
        LearningEvidencePreimageV1(
            prompt_id=genome.prompt_id,
            prompt_utf8_bytes=prompt_bytes,
            candidate_reply_bytes=reply_bytes + b" ",
            failure_class="CounterfeitExactness",
            failed_predicates=("no_float_cast",),
            checker_id="host.public_smoke",
            checker_output_bytes=checker_bytes,
        )
    )
    d_checker = compute_learning_evidence_sha256(
        LearningEvidencePreimageV1(
            prompt_id=genome.prompt_id,
            prompt_utf8_bytes=prompt_bytes,
            candidate_reply_bytes=reply_bytes,
            failure_class="CounterfeitExactness",
            failed_predicates=("no_float_cast",),
            checker_id="host.public_smoke",
            checker_output_bytes=checker_bytes + b" ",
        )
    )
    assert len({base_digest, d_prompt, d_reply, d_checker}) == 4

    catalog_file = tmp_path / "eis" / "antibodies" / "pharmacy_catalog.json"
    repo = PharmacyCatalogRepository(
        tmp_path,
        catalog_file=catalog_file,
        telemetry_dir=tmp_path / "_ic" / "telemetry",
        byte_writer=filesystem_byte_writer,
        byte_source=filesystem_catalog_bytes,
    )
    registry = AntibodyRegistry()

    with pytest.raises(ValueError, match="PROMPT_ID"):
        record_reproduced_failure(
            prompt_id="",
            preimage=preimage,
            target_pattern=r"float\(",
            positive_fixture="from fractions import Fraction\nx = Fraction(1, 2)",
            run_id="run_1",
            task_id="task_1",
            repository=repo,
            registry=registry,
        )

    # Correlated repetitions (same model and scaffold) must stay "candidate".
    for idx in range(3):
        ab = record_reproduced_failure(
            prompt_id=genome.prompt_id,
            preimage=preimage,
            target_pattern=r"float\(",
            positive_fixture="from fractions import Fraction\nx = Fraction(1, 2)",
            run_id=f"run_corr_{idx}",
            task_id="task_1",
            model_id="model_a",
            scaffold_digest="scaf_a",
            precedent_set_digest="prec_a",
            repository=repo,
            registry=registry,
            self_panel=("from fractions import Fraction\nx = Fraction(1, 2)",),
        )
        assert ab.pharmacy_status == "candidate"
        assert ab.authority_effect == "None"
        assert ab.source_prompt_id == genome.prompt_id
        assert ab.evidence_sha256 == base_digest

    # Independent observations across 3 distinct model/scaffold/precedent/lineage tuples
    # promote to "provisional" (queued for human review, still never "admitted").
    for idx, (m_id, s_id, p_id, l_id) in enumerate(
        (
            ("model_b", "scaf_b", "prec_b", "lin_b"),
            ("model_c", "scaf_c", "prec_c", "lin_c"),
        ),
        start=1,
    ):
        ab_ind = record_reproduced_failure(
            prompt_id=genome.prompt_id,
            preimage=preimage,
            target_pattern=r"float\(",
            positive_fixture="from fractions import Fraction\nx = Fraction(1, 2)",
            run_id=f"run_ind_{idx}",
            task_id="task_1",
            model_id=m_id,
            scaffold_digest=s_id,
            precedent_set_digest=p_id,
            lineage_root=l_id,
            repository=repo,
            registry=registry,
            self_panel=("from fractions import Fraction\nx = Fraction(1, 2)",),
        )
    assert ab_ind.pharmacy_status == "provisional"
    assert ab_ind.authority_effect == "None"

    on_disk = json.loads(catalog_file.read_text(encoding="utf-8"))
    saved = on_disk["antibodies"][ab_ind.antibody_id]
    assert saved["source_prompt_id"] == genome.prompt_id
    assert saved["evidence_sha256"] == base_digest
    assert saved["pharmacy_status"] == "provisional"


def test_act3_sieve_flips_disposition_to_hold_on_active_antibody_with_host_danger(
    tmp_path: Path,
) -> None:
    """Act III sieve must change disposition to HOLD when an admitted antibody + host danger fire."""
    from adversary.stage.domain import AUTHORITY_EFFECT_NONE, CandidateProposalV1, WorkPacketV1
    from adversary.use_cases.act_helpers import execute_act3_epistemic_sieve

    from eis.domain.external_admission import HumanAntiSkillAdmissionDecisionV1
    from eis.domain.pharmacy_models import LearningEvidencePreimageV1
    from eis.domain.pharmacy_search import rule_content_bytes
    from eis.domain.pharmacy_seeder import record_reproduced_failure
    from eis.use_cases.antibody_admission import admit_antibody_by_operator
    from pciv.domain.society import (
        AggregateFitnessVectorV1,
        MigrationPolicyV1,
        PromptCivilizationV1,
        PromptFamilyRecordV1,
        PromptSocietyV1,
    )
    from pciv.use_cases.custody import ensure_caller_prompt_genome
    from pciv.use_cases.immunity import resolve_civilization_immune_store
    from pfp_core.caller_feedback import CallerLineageContextV1
    from pfp_core.immunity import host_danger

    prompt_bytes = b"System: Exact arithmetic only.\nUser: Implement solver."
    genome = ensure_caller_prompt_genome(prompt_bytes, {"domain": "core.math"})

    soc_id = _sha256_ref(b"society_math")
    fam_id = _sha256_ref(b"family_exact")
    civ_id = _sha256_ref(b"civ_pfp")

    family = PromptFamilyRecordV1(
        family_id=fam_id,
        society_id=soc_id,
        root_genome_id=genome.prompt_id,
        member_genome_ids=(genome.prompt_id,),
        shared_antibody_ids=(),
        self_panel_digest=_sha256_ref(b"self_panel_exact"),
    )
    society = PromptSocietyV1(
        society_id=soc_id,
        domain_protocol="core.math:v1",
        family_ids=(fam_id,),
        aggregate_fitness_vector=AggregateFitnessVectorV1("4/5", "10/1", "9/10"),
        migration_policy=MigrationPolicyV1(5, ("core.math.*",)),
        created_utc="2026-11-16T00:00:00Z",
    )
    civ = PromptCivilizationV1(
        civilization_id=civ_id,
        society_ids=(soc_id,),
        global_immune_registry="oeeis:registry:v1",
        reservation_budget_pool=1000,
        governance_epoch=0,
        created_utc="2026-11-16T00:00:00Z",
        authority_effect="None",
    )

    store = resolve_civilization_immune_store(
        civ,
        tmp_path,
        read_only=False,
        family_index={fam_id: family},
        societies={soc_id: society},
    )
    preimage = LearningEvidencePreimageV1(
        prompt_id=genome.prompt_id,
        prompt_utf8_bytes=prompt_bytes,
        candidate_reply_bytes=b"return float(0.5)",
        failure_class="CounterfeitExactness",
        failed_predicates=("no_float_cast",),
        checker_id="host.public_smoke",
        checker_output_bytes=b'{"passed":false,"reason":"float cast forbidden"}',
    )
    ab = record_reproduced_failure(
        prompt_id=genome.prompt_id,
        preimage=preimage,
        target_pattern=r"FORBIDDEN_FLOAT_CAST|float\(",
        positive_fixture="from fractions import Fraction\nreturn Fraction(1, 2)",
        negative_fixture="return FORBIDDEN_FLOAT_CAST(float(0.5))",
        run_id="run_act3_seed",
        task_id="task_act3",
        scope_level="family",
        family_id=fam_id,
        society_id=soc_id,
        civilization_id=civ_id,
        producer_actor="proposer_seat",
        repository=store.catalog,
        registry=store.registry,
    )

    saved_rec = store.catalog.load_catalog()["antibodies"][ab.antibody_id]
    rule_digest = "sha256:" + hashlib.sha256(rule_content_bytes(saved_rec)).hexdigest()
    decision = HumanAntiSkillAdmissionDecisionV1(
        decision_id="dec_act3_001",
        issuer="human_reviewer_1",
        rule_bytes_sha256=rule_digest,
        scope="family",
        receipt_sha256=_sha256_ref(b"signed_decision_act3_001"),
    )
    admit_antibody_by_operator(
        ab.antibody_id,
        decision,
        catalog=store.catalog,
        self_panel=("from fractions import Fraction\nreturn Fraction(1, 2)",),
    )

    pkt = WorkPacketV1(
        task_key="task_act3_sieve",
        scene_id="act3_epistemic_sieve",
        objective="Implement exact solver",
        input_artifact_refs=(),
        acceptance_criteria=("Exact arithmetic",),
        budget_units=10,
        evaluator_epoch_id=_sha256_ref(b"epoch_1"),
    )
    bad_code = "def solve():\n    return FORBIDDEN_FLOAT_CAST(float(0.5))\n"
    cand = CandidateProposalV1(
        producer_agent_id="seat_gauge_breaker",
        work_packet_id=pkt.packet_id,
        artifact_refs=(_sha256_ref(bad_code.encode("utf-8")),),
        prediction_receipt_id=_sha256_ref(b"cand_1" + b"\0" + bad_code.encode("utf-8")),
        nonclaims=("Candidate only",),
        authority_effect=AUTHORITY_EFFECT_NONE,
    )
    cands_data = [{"candidate_id": cand.candidate_id, "content": bad_code}]
    lineage = CallerLineageContextV1(
        prompt_id=genome.prompt_id,
        family_id=fam_id,
        society_id=soc_id,
        civilization_id=civ_id,
    )

    # Case A: Pattern matches, but host checker reports no danger -> two-signal law keeps PASS
    # at sieve level with DIAGNOSTIC_OR_NORMALIZE on the candidate verdict.
    res_no_danger = execute_act3_epistemic_sieve(
        pkt.objective,
        [cand],
        cands_data,
        immune_store=store,
        lineage_ctx=lineage,
        host_danger_probe=lambda _c, _b: None,
        prompt_utf8_bytes=prompt_bytes,
        run_key=pkt.task_key,
        return_result=True,
    )
    assert res_no_danger.disposition == "PASS"
    assert len(res_no_danger.surviving_candidates) == 1
    assert res_no_danger.per_candidate_verdicts[0].disposition == "DIAGNOSTIC_OR_NORMALIZE"

    # Case B: Pattern matches AND independent allowlisted host danger fires -> HOLD + cemetery headstone.
    danger = host_danger(
        "PUBLIC_CHECK_FAILED",
        "host.public_smoke",
        "checker failed exact rational constraint",
        defects=1,
    )
    res_with_danger = execute_act3_epistemic_sieve(
        pkt.objective,
        [cand],
        cands_data,
        immune_store=store,
        lineage_ctx=lineage,
        host_danger_probe=lambda _c, _b: danger,
        prompt_utf8_bytes=prompt_bytes,
        run_key=pkt.task_key,
        return_result=True,
    )
    assert res_with_danger.disposition == "HOLD"
    assert res_with_danger.surviving_candidates == ()
    assert len(res_with_danger.buried_headstones) == 1
    assert res_with_danger.per_candidate_verdicts[0].disposition == "HOLD_OR_REPAIR"
    assert ab.antibody_id in res_with_danger.per_candidate_verdicts[0].fired_antibody_ids


def test_autoimmune_antibody_matching_self_panel_is_purged_before_holding_stranger(
    tmp_path: Path,
) -> None:
    """Detectors matching healthy self-panel entries must be refused and retired before holding strangers."""
    from eis.domain.external_admission import HumanAntiSkillAdmissionDecisionV1
    from eis.domain.pharmacy_models import LearningEvidencePreimageV1
    from eis.domain.pharmacy_search import rule_content_bytes
    from eis.domain.pharmacy_seeder import record_reproduced_failure
    from eis.use_cases.antibody_admission import admit_antibody_by_operator
    from pciv.use_cases.custody import ensure_caller_prompt_genome
    from pciv.use_cases.immunity import resolve_civilization_immune_store
    from pfp_core.caller_feedback import (
        CallerLineageContextV1,
        ImmuneScreenRequestV1,
        promote_antibody_scope,
        screen_caller_turn,
    )
    from pfp_core.immunity import host_danger

    clean_panel = (
        "from fractions import Fraction\ndef exact_sum(a: int, b: int) -> Fraction:\n    return Fraction(a + b, 1)",
    )
    prompt_a = b"System: Compute Fraction.\nUser: Task A."
    genome_a = ensure_caller_prompt_genome(prompt_a, {"domain": "pfp.self"})
    store = resolve_civilization_immune_store(None, tmp_path, read_only=False)

    preimage = LearningEvidencePreimageV1(
        prompt_id=genome_a.prompt_id,
        prompt_utf8_bytes=prompt_a,
        candidate_reply_bytes=b"return Fraction(1, 2)",
        failure_class="OverbroadDetector",
        failed_predicates=("false_alarm",),
        checker_id="host.public_smoke",
        checker_output_bytes=b'{"passed":false,"reason":"false_alarm"}',
    )
    ab = record_reproduced_failure(
        prompt_id=genome_a.prompt_id,
        preimage=preimage,
        target_pattern=r"Fraction",
        positive_fixture="x = 1",
        negative_fixture="return Fraction(1, 2)",
        run_id="run_autoimmune",
        task_id="task_auto",
        producer_actor="proposer_seat",
        repository=store.catalog,
        registry=store.registry,
    )

    saved_rec = store.catalog.load_catalog()["antibodies"][ab.antibody_id]
    rule_digest = "sha256:" + hashlib.sha256(rule_content_bytes(saved_rec)).hexdigest()
    decision = HumanAntiSkillAdmissionDecisionV1(
        decision_id="dec_auto_001",
        issuer="human_reviewer_1",
        rule_bytes_sha256=rule_digest,
        scope="global",
        receipt_sha256=_sha256_ref(b"signed_decision_auto_001"),
    )

    with pytest.raises(ValueError, match="AUTOIMMUNE_RULE_REFUSED"):
        admit_antibody_by_operator(
            ab.antibody_id,
            decision,
            catalog=store.catalog,
            self_panel=clean_panel,
        )

    after = store.catalog.load_catalog()["antibodies"][ab.antibody_id]
    assert after["pharmacy_status"] == "retired"

    # Even scope expansion attempts on an autoimmune pattern must refuse.
    with pytest.raises(ValueError, match="AUTOIMMUNE_RULE_REFUSED"):
        promote_antibody_scope(
            ab.antibody_id,
            target_scope="family",
            family_id=_sha256_ref(b"fam_target"),
            self_panel=clean_panel,
            store=store,
        )

    # Stranger prompt carrying healthy Fraction code passes cleanly.
    stranger = ensure_caller_prompt_genome(b"System: Solve stranger.\nUser: Compute.", {"domain": "pfp.self"})
    verdict = screen_caller_turn(
        ImmuneScreenRequestV1(
            lineage=CallerLineageContextV1(prompt_id=stranger.prompt_id),
            prompt_utf8_bytes=b"System: Solve stranger.\nUser: Compute.",
            candidate_reply_bytes=clean_panel[0].encode("utf-8"),
            signal2_danger=None,
        ),
        store,
        self_panel=clean_panel,
    )
    assert verdict.disposition == "PASS"
    assert verdict.fired_antibody_ids == ()

    # Even if forced into the catalog directly, load-time Thymus screening excludes it
    # from holding a stranger alongside an unrelated signal1 check.
    forced_catalog = store.catalog.load_catalog()
    forced_catalog["antibodies"][ab.antibody_id]["pharmacy_status"] = "admitted"
    forced_catalog["antibodies"][ab.antibody_id].pop("thymus_receipt_sha256", None)
    forced_catalog.get("managed_projections", {}).pop(ab.antibody_id, None)
    store.catalog.catalog_file.write_text(json.dumps(forced_catalog), encoding="utf-8")

    verdict_forced = screen_caller_turn(
        ImmuneScreenRequestV1(
            lineage=CallerLineageContextV1(prompt_id=stranger.prompt_id),
            prompt_utf8_bytes=b"System: Solve stranger.\nUser: Compute.",
            candidate_reply_bytes=clean_panel[0].encode("utf-8"),
            signal2_danger=host_danger("PUBLIC_CHECK_FAILED", "host.public_smoke", "unrelated fail"),
        ),
        store,
        self_panel=clean_panel,
    )
    assert ab.antibody_id not in verdict_forced.fired_antibody_ids


def test_child_genome_relapsing_on_parent_failure_is_buried_and_tainted(tmp_path: Path) -> None:
    """A child prompt is adopted only after the antibody fires on parent failure and child cure passes."""
    from adversary.stage.infrastructure.default_adapters import FileCemeteryAdapter

    from pciv.domain.lamarckian import (
        CochainResidualV1,
        ReproducedFailureCaseV1,
    )
    from pciv.domain.models import ProtectedSpanV1
    from pciv.use_cases.custody import ensure_caller_prompt_genome
    from pciv.use_cases.immunity import resolve_civilization_immune_store
    from pciv.use_cases.lamarckian_loop import (
        LamarckianReceiptStore,
        load_active_lineage_antibodies,
        spawn_antibody_constrained_child,
        verify_lineage_cure,
    )
    from pciv.use_cases.transitive_immunity import FixedPointLineageTaintEngineV1
    from pfp_core.immunity import host_danger

    parent_bytes = b"System: Core Rule.\nUser: Return exact integer ratio."
    span = ProtectedSpanV1(name="system_framing", start_byte=0, end_byte=18)
    parent_genome = ensure_caller_prompt_genome(
        parent_bytes,
        {"domain": "core.math"},
        protected_spans=(span,),
    )
    failing_parent_reply = b"def answer():\n    return float(0.25)  # UNSAFE_FLOAT_CAST\n"
    witness_sha = hashlib.sha256(b"host_witness_float_001").hexdigest()

    store = resolve_civilization_immune_store(None, tmp_path, read_only=False)
    ab = _seed_and_admit_test_antibody(
        store,
        prompt_id=parent_genome.prompt_id,
        prompt_bytes=parent_bytes,
        reply_bytes=failing_parent_reply,
        failure_class="CounterfeitExactness",
        failed_predicates=("exact_ratio_required",),
        checker_output_bytes=b'{"passed":false,"reason":"UNSAFE_FLOAT_CAST"}',
        target_pattern=r"UNSAFE_FLOAT_CAST|float\(",
        positive_fixture="from fractions import Fraction\ndef answer():\n    return Fraction(1, 4)\n",
        negative_fixture=failing_parent_reply.decode("utf-8"),
        guidance_text="Use exact Fraction arithmetic instead of float casts.",
        run_id="run_lineage_1",
        task_id="task_lineage",
        decision_id="dec_lineage_001",
    )

    child_genome, child_bytes, lamarckian_receipt = spawn_antibody_constrained_child(
        parent_genome=parent_genome,
        parent_prompt_bytes=parent_bytes,
        antibody=store.catalog.load_catalog()["antibodies"][ab.antibody_id],
        falsification_witness_sha256=witness_sha,
        cochain_residual=CochainResidualV1("1/2", "0/1", "0/1"),
        receipt_store=store.receipt_store,
    )
    assert child_bytes[:18] == parent_bytes[:18]
    assert lamarckian_receipt.antibody_id == ab.antibody_id
    assert lamarckian_receipt.hop_distance == 1
    assert lamarckian_receipt.attenuation_weight == "1/2"
    assert lamarckian_receipt.parent_genome_id == parent_genome.content_digest
    assert lamarckian_receipt.child_genome_id == child_genome.content_digest

    # Next generation lookup resolves the active antibody across hop_distance 1..10,
    # and evaporates at hop_distance 11 when not promoted to a family.
    loaded_abs, loaded_receipts = load_active_lineage_antibodies(
        child_genome.prompt_id, store.receipt_store, store.catalog
    )
    assert any(item["antibody_id"] == ab.antibody_id for item in loaded_abs)
    assert loaded_receipts[0].receipt_id == lamarckian_receipt.receipt_id

    hop11_receipt_store = LamarckianReceiptStore(tmp_path / "eis" / "antibodies" / "hop11.jsonl")
    hop11_receipt_store.append(
        lamarckian_receipt.__class__.create(
            parent_genome_id=parent_genome.content_digest,
            child_genome_id=_sha256_ref(b"hop11_child"),
            falsification_witness_sha256=witness_sha,
            cochain_residual=CochainResidualV1("1/2", "0/1", "0/1"),
            antibody_id=ab.antibody_id,
            hop_distance=10,
        ),
        parent_prompt_id=parent_genome.prompt_id,
        child_prompt_id="genome_" + hashlib.sha256(b"hop11_child").hexdigest(),
    )
    # Chain 1 extra hop beyond hop 10 -> cumulative hop 11 must evaporate.
    hop11_child_id = "genome_" + hashlib.sha256(b"hop12_child").hexdigest()
    hop11_receipt_store.append(
        lamarckian_receipt.__class__.create(
            parent_genome_id=_sha256_ref(b"hop11_child"),
            child_genome_id="sha256:" + hop11_child_id.removeprefix("genome_"),
            falsification_witness_sha256=witness_sha,
            cochain_residual=CochainResidualV1("1/2", "0/1", "0/1"),
            antibody_id=ab.antibody_id,
            hop_distance=2,
        ),
        parent_prompt_id="genome_" + hashlib.sha256(b"hop11_child").hexdigest(),
        child_prompt_id=hop11_child_id,
    )
    evap_abs, _ = load_active_lineage_antibodies(hop11_child_id, hop11_receipt_store, store.catalog)
    assert all(item["antibody_id"] != ab.antibody_id for item in evap_abs)

    repro_case = ReproducedFailureCaseV1(
        case_id="case_float_relapse",
        prompt_utf8_bytes=parent_bytes,
        parent_failing_reply_bytes=failing_parent_reply,
        failure_class="CounterfeitExactness",
        witness_sha256=witness_sha,
    )
    cemetery = FileCemeteryAdapter(tmp_path / "cemetery")
    taint = FixedPointLineageTaintEngineV1()

    # Relapsing child (parent failure reproduces) must be buried and tainted.
    relapse_receipt = verify_lineage_cure(
        parent_genome=parent_genome,
        child_genome=child_genome,
        parent_prompt_bytes=parent_bytes,
        child_prompt_bytes=child_bytes,
        mutation_receipt=lamarckian_receipt,
        reproducing_case=repro_case,
        child_reply_bytes=failing_parent_reply,
        child_host_danger=host_danger("PUBLIC_CHECK_FAILED", "host.public_smoke", "UNSAFE_FLOAT_CAST still present"),
        held_out_passed=False,
        store=store,
        cemetery=cemetery,
        taint_engine=taint,
    )
    assert relapse_receipt.cure_status == "RELAPSED_BURIED"
    assert relapse_receipt.host_failure_reproduced is True
    assert taint.is_tainted(child_genome.prompt_id) is True
    assert len(list((tmp_path / "cemetery").glob("*.headstone.json"))) == 1

    # Cured child (antibody fired on parent failure, absent on child, holdout passed) -> CURED_ADOPTED.
    cured_reply = b"from fractions import Fraction\ndef answer():\n    return Fraction(1, 4)\n"
    cure_receipt = verify_lineage_cure(
        parent_genome=parent_genome,
        child_genome=child_genome,
        parent_prompt_bytes=parent_bytes,
        child_prompt_bytes=child_bytes,
        mutation_receipt=lamarckian_receipt,
        reproducing_case=repro_case,
        child_reply_bytes=cured_reply,
        child_host_danger=None,
        held_out_passed=True,
        store=store,
        cemetery=cemetery,
        taint_engine=FixedPointLineageTaintEngineV1(),
    )
    assert cure_receipt.cure_status == "CURED_ADOPTED"
    assert cure_receipt.antibody_screened is True
    assert cure_receipt.antibody_fired_on_parent_failure is True
    assert cure_receipt.host_failure_reproduced is False


def _run_bout_with_unsafe_token(tmp_path: Path, store, bad_code: str):
    from adversary.domain.evidence import CandidateCheckV1, CheckerVerdict
    from adversary.domain.ports import CandidateCheckerPort
    from adversary.infrastructure.native import DefaultNativeOperationPort
    from adversary.profile.profile_loader import load_adversary_council_profile
    from adversary.runtime import build_adversary_runtime
    from adversary.stage.domain import WorkPacketV1
    from adversary.stage.infrastructure.default_adapters import FixtureAgentTurnAdapter
    from adversary.use_cases.bout_service import execute_7act_adversary_bout
    from operations.domain.rop.result import Ok

    from pfp.domain.value_objects.seat_turn import SeatTurnReplyV1

    class _AcceptingHost:
        def execute_host_request(self, request_bytes: bytes):
            return Ok(b'{"status":"ACCEPTED"}')

    class _RejectingChecker(CandidateCheckerPort):
        def check_candidate(
            self,
            *,
            run_key: str,
            objective: str,
            candidate_id: str,
            candidate_bytes: bytes,
            carrier_context=None,
        ):
            receipt_bytes = b'{"passed":false,"reason":"UNSAFE_BYPASS_TOKEN rejected"}'
            return Ok(
                CandidateCheckV1(
                    verdict=CheckerVerdict.REJECTED,
                    candidate_id=candidate_id,
                    candidate_content_sha256=_sha256_ref(candidate_bytes),
                    checker_id="host.public_smoke",
                    checker_receipt_sha256=_sha256_ref(receipt_bytes),
                    checker_receipt_bytes=receipt_bytes,
                    reason="UNSAFE_BYPASS_TOKEN rejected",
                )
            )

    _, _, profile, _, _ = load_adversary_council_profile()
    rt = build_adversary_runtime(
        output_dir=tmp_path / "_intelligence",
        fixture_mode=False,
        host=_AcceptingHost(),
    )
    canned = {
        ("act2_panel_debate", "seat_gauge_breaker"): SeatTurnReplyV1(
            reply_text=bad_code,
            machine_fields={"AUTHORITY_EFFECT": "None"},
            residual_colour="Open",
            authority_effect="None",
            raw_bytes=bad_code.encode("utf-8"),
        ),
    }
    object.__setattr__(rt, "seat_port", FixtureAgentTurnAdapter(canned_replies=canned))
    packet = WorkPacketV1(
        task_key="bout_shared_screen_01",
        scene_id="act1_perception",
        objective="Generate safe function without bypass tokens",
        input_artifact_refs=(),
        acceptance_criteria=("Zero bypass tokens",),
        budget_units=25,
        evaluator_epoch_id=_sha256_ref(b"shared_epoch_1"),
    )
    return execute_7act_adversary_bout(
        profile,
        rt,
        packet,
        output_dir=tmp_path / "_intelligence" / "_adversary",
        repo_root=tmp_path,
        candidate_checker=_RejectingChecker(),
        immune_store=store,
        native_support=DefaultNativeOperationPort(),
    )


def test_wild_complete_task_turn_and_act3_swarm_bout_call_same_screen_caller_turn_on_single_pharmacy_store(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Wild complete_task_turn and Act III 7-act bout must invoke the same screen_caller_turn on one pharmacy store."""
    from adversary.domain.providers.types import CandidateRequest, CandidateResponse
    from adversary.use_cases import act_helpers

    import pfp_core.caller_feedback as cf
    from pciv.use_cases.custody import ensure_caller_prompt_genome
    from pciv.use_cases.immunity import resolve_civilization_immune_store
    from pfp.infrastructure import task_turn
    from pfp.infrastructure.task_turn import PfpTurnRefusal, complete_task_turn

    store = resolve_civilization_immune_store(None, tmp_path, read_only=False)
    seed_prompt = b"Seed exact prompt."
    seed_genome = ensure_caller_prompt_genome(seed_prompt, {"domain": "pfp.shared"})
    ab = _seed_and_admit_test_antibody(
        store,
        prompt_id=seed_genome.prompt_id,
        prompt_bytes=seed_prompt,
        reply_bytes=b"UNSAFE_BYPASS_TOKEN",
        failure_class="BoundaryBypass",
        failed_predicates=("forbid_bypass_token",),
        checker_output_bytes=b'{"passed":false,"reason":"UNSAFE_BYPASS_TOKEN rejected"}',
        target_pattern="UNSAFE_BYPASS_TOKEN",
        positive_fixture="def safe_impl():\n    return 42\n",
        negative_fixture="UNSAFE_BYPASS_TOKEN",
        scope_level="civilization",
        admission_scope="global",
        decision_id="dec_shared_001",
        run_id="run_shared_seed",
        task_id="task_shared_seed",
    )

    spy_calls: list[tuple[Path, str, tuple[str, ...], str]] = []
    real_screen = cf.screen_caller_turn

    def _spied_screen(req, s, *, self_panel=None):
        verdict = real_screen(req, s, self_panel=self_panel)
        spy_calls.append(
            (s.catalog.catalog_file, verdict.disposition, verdict.fired_antibody_ids, verdict.prompt_id)
        )
        return verdict

    monkeypatch.setattr(cf, "screen_caller_turn", _spied_screen)
    monkeypatch.setattr(act_helpers, "screen_caller_turn", _spied_screen)
    if hasattr(task_turn, "screen_caller_turn"):
        monkeypatch.setattr(task_turn, "screen_caller_turn", _spied_screen)

    class WildGateway:
        def complete(self, request, **_options):
            public = json.loads(request.user)
            payload = {
                **{k: public[k] for k in ("task_id", "attempt_id", "input_sha256")},
                "answer": "def bad():\n    return UNSAFE_BYPASS_TOKEN\n",
            }
            return (
                CandidateResponse(
                    json.dumps(payload),
                    "test-model",
                    "openrouter",
                    cost_usd=None,
                    transport="live",
                ),
                None,
            )

    failing_judge = (("host.public_smoke", lambda _case, _ans: (False, "UNSAFE_BYPASS_TOKEN rejected")),)
    with pytest.raises(PfpTurnRefusal) as wild_exc:
        complete_task_turn(
            WildGateway(),
            CandidateRequest("Return safe implementation.", "Compute result."),
            task_id="wild_task_01",
            attempt_id="att_01",
            checker_id="host.public_smoke",
            judges=failing_judge,
            require_checker=True,
            immune_store=store,
        )

    assert len(spy_calls) == 1
    assert spy_calls[0][0] == store.catalog.catalog_file
    assert spy_calls[0][1] == "HOLD_OR_REPAIR"
    assert ab.antibody_id in spy_calls[0][2]
    assert wild_exc.value.checked["immune_verdict"]["disposition"] == "HOLD_OR_REPAIR"
    catalog_after_wild = json.loads(store.catalog.catalog_file.read_text(encoding="utf-8"))
    assert any(
        entry.get("source_prompt_id") == spy_calls[0][3]
        for entry in catalog_after_wild["antibodies"].values()
    )

    bout_res = _run_bout_with_unsafe_token(
        tmp_path, store, "def swarm_bad():\n    return UNSAFE_BYPASS_TOKEN\n"
    )
    assert bout_res.is_err
    assert bout_res.unwrap_err().code == "ACT3_IMMUNE_SIEVE_HOLD"
    assert len(spy_calls) >= 2
    assert spy_calls[1][0] == store.catalog.catalog_file
    assert spy_calls[1][1] == "HOLD_OR_REPAIR"
    assert ab.antibody_id in spy_calls[1][2]
