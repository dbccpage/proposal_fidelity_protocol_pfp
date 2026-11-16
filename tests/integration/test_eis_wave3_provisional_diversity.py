"""Integration tests for Wave 3 multi-root provisional promotion and queue separation.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from eis.domain.external_admission import HumanAntiSkillAdmissionDecisionV1
from eis.domain.pharmacy_models import LearningEvidencePreimageV1, PharmacyStatus
from eis.domain.pharmacy_search import rule_content_bytes
from eis.domain.pharmacy_seeder import record_reproduced_failure
from eis.use_cases.antibody_admission import admit_antibody_by_operator
from pciv.use_cases.custody import ensure_caller_prompt_genome
from pciv.use_cases.immunity import resolve_civilization_immune_store
from pfp_core.caller_feedback import (
    CallerLineageContextV1,
    ImmuneScreenRequestV1,
    list_provisional_review_queue,
    screen_caller_turn,
)
from pfp_core.immunity import host_danger


def _sha256_ref(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def test_correlated_failures_stay_candidate_while_diverse_roots_enter_provisional_review_queue(
    tmp_path: Path,
) -> None:
    store = resolve_civilization_immune_store(None, tmp_path, read_only=False)
    prompt_bytes = b"System: Compute exact output."
    genome = ensure_caller_prompt_genome(prompt_bytes, {"domain": "wave3.diversity"})
    failing_reply = b"def bad():\n    return CORRELATED_LEAK\n"
    positive_clean = "def good():\n    return 1\n"

    ab_corr = None
    for idx in range(3):
        ab_corr = record_reproduced_failure(
            prompt_id=genome.prompt_id,
            preimage=LearningEvidencePreimageV1(
                prompt_id=genome.prompt_id,
                prompt_utf8_bytes=prompt_bytes,
                candidate_reply_bytes=failing_reply,
                failure_class="CorrelatedDefect",
                failed_predicates=("no_leak",),
                checker_id="host.public_smoke",
                checker_output_bytes=f'{{"attempt":{idx}}}'.encode(),
            ),
            target_pattern="CORRELATED_LEAK",
            positive_fixture=positive_clean,
            negative_fixture=failing_reply.decode("utf-8"),
            run_id=f"run_corr_{idx}",
            task_id="task_corr",
            producer_actor="proposer_seat",
            model_id="same_model",
            scaffold_digest="same_scaffold",
            precedent_set_digest="same_prec",
            lineage_root="same_root",
            repository=store.catalog,
            registry=store.registry,
            self_panel=(positive_clean,),
        )
    assert ab_corr is not None
    assert ab_corr.pharmacy_status == PharmacyStatus.CANDIDATE.value
    assert list_provisional_review_queue(store) == ()

    ab_div = None
    for idx in range(3):
        ab_div = record_reproduced_failure(
            prompt_id=genome.prompt_id,
            preimage=LearningEvidencePreimageV1(
                prompt_id=genome.prompt_id,
                prompt_utf8_bytes=prompt_bytes,
                candidate_reply_bytes=b"def bad():\n    return DIVERSE_LEAK\n",
                failure_class="DiverseDefect",
                failed_predicates=("no_diverse_leak",),
                checker_id="host.public_smoke",
                checker_output_bytes=f'{{"diverse":{idx}}}'.encode(),
            ),
            target_pattern="DIVERSE_LEAK",
            positive_fixture=positive_clean,
            negative_fixture="def bad():\n    return DIVERSE_LEAK\n",
            run_id=f"run_div_{idx}",
            task_id="task_div",
            producer_actor="proposer_seat",
            model_id=f"model_{idx}",
            scaffold_digest=f"scaffold_{idx}",
            precedent_set_digest=f"prec_{idx}",
            lineage_root=f"root_{idx}",
            repository=store.catalog,
            registry=store.registry,
            self_panel=(positive_clean,),
        )
    assert ab_div is not None
    assert ab_div.pharmacy_status == PharmacyStatus.PROVISIONAL.value
    queue = list_provisional_review_queue(store)
    assert [row["antibody_id"] for row in queue] == [ab_div.antibody_id]

    pre_admit = screen_caller_turn(
        ImmuneScreenRequestV1(
            lineage=CallerLineageContextV1(prompt_id=genome.prompt_id),
            prompt_utf8_bytes=prompt_bytes,
            candidate_reply_bytes=b"def bad():\n    return DIVERSE_LEAK\n",
            signal2_danger=None,
        ),
        store,
        self_panel=(positive_clean,),
    )
    assert pre_admit.disposition == "PASS"
    assert pre_admit.fired_antibody_ids == ()

    saved_rec = store.catalog.load_catalog()["antibodies"][ab_div.antibody_id]
    digest = _sha256_ref(rule_content_bytes(saved_rec))
    with pytest.raises(PermissionError, match="SELF_ADMISSION_REFUSED"):
        admit_antibody_by_operator(
            ab_div.antibody_id,
            HumanAntiSkillAdmissionDecisionV1(
                decision_id="dec_self_refuse",
                issuer="proposer_seat",
                rule_bytes_sha256=digest,
                scope="prompt_line",
                receipt_sha256=_sha256_ref(b"dec_self_refuse"),
            ),
            catalog=store.catalog,
            self_panel=(positive_clean,),
        )

    admit_antibody_by_operator(
        ab_div.antibody_id,
        HumanAntiSkillAdmissionDecisionV1(
            decision_id="dec_div_admit",
            issuer="human_reviewer_1",
            rule_bytes_sha256=digest,
            scope="prompt_line",
            receipt_sha256=_sha256_ref(b"dec_div_admit"),
        ),
        catalog=store.catalog,
        self_panel=(positive_clean,),
    )
    assert list_provisional_review_queue(store) == ()

    post_admit = screen_caller_turn(
        ImmuneScreenRequestV1(
            lineage=CallerLineageContextV1(prompt_id=genome.prompt_id),
            prompt_utf8_bytes=prompt_bytes,
            candidate_reply_bytes=b"def bad():\n    return DIVERSE_LEAK\n",
            signal2_danger=host_danger("PUBLIC_CHECK_FAILED", "host.public_smoke", "diverse"),
        ),
        store,
        self_panel=(positive_clean,),
    )
    assert post_admit.disposition == "HOLD_OR_REPAIR"
    assert ab_div.antibody_id in post_admit.fired_antibody_ids
