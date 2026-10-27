"""PHARMACY-001: harvesting cannot admit, and a phantom cannot come back.

Two properties, each pinned by tests whose failure mode has been observed:

1. `farm_antibodies_from_defects` is *incapable* of writing a non-CANDIDATE
   status -- enforced by the signature, not by a convention a later edit can
   quietly break. It was broken exactly that way once already.
2. The three antibodies farmed from defects that never existed cannot be
   farmed again, and the register says why.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import pytest

from eis.domain.pharmacy_models import (
    Antibody,
    PharmacyStatus,
)
from eis.domain.pharmacy_seeder import PharmacySeeder
from eis.infrastructure.pharmacy_writer import (
    filesystem_byte_writer,
    filesystem_catalog_bytes,
)
from adversary.stage.infrastructure.pharmacy_writer import (
    filesystem_catalog_text,
    filesystem_text_writer,
)
from eis.domain.pharmacy_templates import classify_failure
from eis.domain.retired_antibodies import (
    RETIRED_ANTIBODIES,
    RETIRED_ANTIBODY_IDS,
    is_retired,
    retirement_reason,
)
from adversary.stage.domain.immune.models import (
    Antibody as SwarmAntibody,
)
from adversary.stage.domain.immune.models import (
    PharmacyStatus as SwarmPharmacyStatus,
)
from adversary.stage.domain.immune.seeder import PharmacySeeder as SwarmSeeder

# The three phantoms, and the defect strings that produce them. Reconstructed
# from the id formula and verified against the stored `target_pattern` of each
# record before this test was written.
PHANTOM_DEFECTS = tuple(record.defect for record in RETIRED_ANTIBODIES.values())

# The fourth file in the same PR #156 diff. It was LAST, so the parser had
# nothing left to append into it and it produced no phantom. Its id is not on
# the register, so it is the negative control: farming must still work here, or
# the retirement tests below would pass vacuously.
CLEAN_SIBLING_DEFECT = (
    "defect:syntax_error:operations.use_cases.councils.social_graph"
)


def _expected_id(defect: str) -> str:
    return f"ab_{classify_failure(defect)}_{hashlib.sha256(defect.encode('utf-8')).hexdigest()[:8]}"


# ---------------------------------------------------------------------------
# 1. Harvesting cannot admit
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("model", [Antibody, SwarmAntibody], ids=["operations", "swarm"])
def test_farm_has_no_status_parameter_at_all(model: type) -> None:
    """The enforcement, stated directly.

    Not "farm happens to pass CANDIDATE" -- there is no argument through which
    a caller could pass anything else. Mutation: add `pharmacy_status` back to
    the signature and this fails, before any behaviour changes.
    """
    parameters = inspect.signature(model.farm).parameters
    assert "pharmacy_status" not in parameters
    assert "authority_effect" not in parameters


@pytest.mark.parametrize(
    ("model", "status_enum"),
    [(Antibody, PharmacyStatus), (SwarmAntibody, SwarmPharmacyStatus)],
    ids=["operations", "swarm"],
)
def test_a_farmed_antibody_is_a_candidate(model: type, status_enum: type) -> None:
    """Mutation: make `farm` pass ADMITTED -> this fails."""
    antibody = model.farm(
        antibody_id="ab_test_0000",
        failure_class="test",
        target_pattern="test",
        constraint_type="ProjectOut",
        operatorizability="repairable",
        action="repair",
        severity="P1",
        description="d",
        negative_fixture="n",
        positive_fixture="p",
    )
    assert antibody.pharmacy_status == status_enum.CANDIDATE.value
    assert antibody.authority_effect == "None"


def test_the_swarm_seeder_no_longer_self_admits(tmp_path: Path) -> None:
    """The original defect, at its original site.

    `_defect_to_antibody` hardcoded `pharmacy_status="admitted"`, so a local
    defect-harvesting run minted its own evidence. Mutation: restore that
    literal -> this fails.
    """
    seeder = SwarmSeeder(repo_root=tmp_path, text_writer=filesystem_text_writer, text_source=filesystem_catalog_text)
    harvested = seeder.farm_antibodies_from_defects(
        ["circular import between a and b"], run_id="r", task_id="t"
    )
    assert harvested, "the seeder must still farm something"
    assert [a.pharmacy_status for a in harvested] == ["candidate"]


def test_a_farmed_antibody_reaches_disk_as_a_candidate(tmp_path: Path) -> None:
    """The status must survive persistence, not just construction."""
    seeder = SwarmSeeder(repo_root=tmp_path, text_writer=filesystem_text_writer, text_source=filesystem_catalog_text)
    seeder.farm_antibodies_from_defects(["layer violation x"], run_id="r", task_id="t")

    written = list(seeder.catalog_repo.candidates_dir.glob("ab_*.json"))
    assert written, "expected at least one antibody on disk"
    for path in written:
        assert json.loads(path.read_text(encoding="utf-8"))["pharmacy_status"] == "candidate"
    assert not list(seeder.catalog_repo.antibodies_dir.glob("ab_*.json")), "farmed candidate must not pollute root"


@pytest.mark.parametrize("model", [Antibody, SwarmAntibody], ids=["operations", "swarm"])
def test_an_unknown_status_is_refused(model: type) -> None:
    """The enum is a bare `str` on the record, so it needs a guard to bite.

    Mutation: drop the `__post_init__` check -> a typo becomes a live state that
    no consumer knows how to gate on.
    """
    with pytest.raises(ValueError, match="PHARMACY_STATUS_UNKNOWN"):
        model(
            antibody_id="ab_x",
            failure_class="f",
            target_pattern="t",
            constraint_type="ProjectOut",
            operatorizability="repairable",
            action="repair",
            severity="P1",
            description="d",
            negative_fixture="n",
            positive_fixture="p",
            pharmacy_status="admited",  # codespell:ignore
        )


@pytest.mark.parametrize("model", [Antibody, SwarmAntibody], ids=["operations", "swarm"])
def test_a_non_none_authority_effect_is_refused(model: type) -> None:
    """Direct construction must not bypass the pharmacy authority fence."""
    with pytest.raises(ValueError, match="PHARMACY_AUTHORITY_EFFECT_NON_NONE"):
        model(
            antibody_id="ab_x",
            failure_class="f",
            target_pattern="t",
            constraint_type="ProjectOut",
            operatorizability="repairable",
            action="repair",
            severity="P1",
            description="d",
            negative_fixture="n",
            positive_fixture="p",
            authority_effect="admit",
        )


@pytest.mark.parametrize("model", [Antibody, SwarmAntibody], ids=["operations", "swarm"])
def test_loading_an_already_admitted_record_still_works(model: type) -> None:
    """Negative control for the guard above.

    Existing catalogs on disk carry `admitted` records. Refusing to *farm* one
    must not mean refusing to *read* one, or the fix would corrupt every
    catalog it touched.
    """
    antibody = model(
        antibody_id="ab_legacy",
        failure_class="f",
        target_pattern="t",
        constraint_type="ProjectOut",
        operatorizability="repairable",
        action="repair",
        severity="P1",
        description="d",
        negative_fixture="n",
        positive_fixture="p",
        pharmacy_status="admitted",
    )
    assert antibody.pharmacy_status == "admitted"


# ---------------------------------------------------------------------------
# 2. A phantom cannot come back
# ---------------------------------------------------------------------------


def test_the_register_names_exactly_the_three_phantoms() -> None:
    assert RETIRED_ANTIBODY_IDS == {
        "ab_syntax_error_e033d14a",
        "ab_syntax_error_4cb62bc5",
        "ab_syntax_error_bb7045c0",
    }


def test_each_retired_id_is_reproduced_by_its_recorded_defect() -> None:
    """The register is auditable, not just assertive.

    Hash the recorded defect string and the id comes back. Mutation: change one
    recorded defect string -> this fails, so the register cannot drift into
    naming ids whose provenance it no longer explains.
    """
    for antibody_id, record in RETIRED_ANTIBODIES.items():
        assert _expected_id(record.defect) == antibody_id


def test_every_retirement_records_a_reason_and_a_repair() -> None:
    for record in RETIRED_ANTIBODIES.values():
        assert "Phantom defect" in record.reason
        assert record.repaired_by, "a retirement must name the commit that fixed the detector"
        assert "PR #156" in record.provenance


def test_the_three_phantoms_cannot_be_farmed_again(tmp_path: Path) -> None:
    """The regression that matters. Mutation: drop the `is_retired` check -> all
    three come back under their original ids."""
    seeder = PharmacySeeder(repo_root=tmp_path, byte_writer=filesystem_byte_writer, byte_source=filesystem_catalog_bytes)
    farmed = seeder.farm_antibodies_from_defects(
        list(PHANTOM_DEFECTS), run_id="r", task_id="t"
    )

    assert farmed == [], "a retired antibody was farmed again"
    assert sorted(seeder.refused_retired) == sorted(RETIRED_ANTIBODY_IDS)
    assert not list((tmp_path / "_intelligence" / "antibodies").rglob("ab_syntax_error_*.json"))


def test_a_non_retired_sibling_defect_is_still_farmed(tmp_path: Path) -> None:
    """Negative control.

    Without this, a seeder that farmed *nothing at all* would pass the test
    above and look like a working retirement.
    """
    seeder = PharmacySeeder(repo_root=tmp_path, byte_writer=filesystem_byte_writer, byte_source=filesystem_catalog_bytes)
    farmed = seeder.farm_antibodies_from_defects(
        [CLEAN_SIBLING_DEFECT], run_id="r", task_id="t"
    )

    assert len(farmed) == 1
    assert farmed[0].antibody_id == _expected_id(CLEAN_SIBLING_DEFECT)
    assert farmed[0].antibody_id not in RETIRED_ANTIBODY_IDS
    assert farmed[0].pharmacy_status == "candidate"
    assert seeder.refused_retired == []


def test_repeated_observation_in_one_run_increments_the_catalog_count(tmp_path: Path) -> None:
    """A repeated defect is two observations, even before the next run."""
    seeder = PharmacySeeder(repo_root=tmp_path, byte_writer=filesystem_byte_writer, byte_source=filesystem_catalog_bytes)

    farmed = seeder.farm_antibodies_from_defects(
        [CLEAN_SIBLING_DEFECT, CLEAN_SIBLING_DEFECT], run_id="r", task_id="t"
    )

    assert [antibody.times_seen for antibody in farmed] == [1, 2]
    antibody_id = _expected_id(CLEAN_SIBLING_DEFECT)
    catalog = seeder.load_catalog()
    ab_path = seeder.candidates_dir / f"{antibody_id}.json"
    assert ab_path.is_file(), "Expected candidate antibody to be isolated in candidates/ subfolder"
    saved = json.loads(ab_path.read_text(encoding="utf-8"))
    assert saved["times_seen"] == 2


def test_retirement_helpers_agree_with_the_register() -> None:
    assert is_retired("ab_syntax_error_e033d14a")
    assert not is_retired(_expected_id(CLEAN_SIBLING_DEFECT))
    assert retirement_reason("ab_syntax_error_e033d14a")
    assert retirement_reason("ab_not_a_real_id") is None


def test_retired_is_distinct_from_rejected() -> None:
    """They are different judgements and must not collapse.

    REJECTED: a real defect, judged not worth guarding.
    RETIRED:  the defect never existed; the detector was wrong.
    """
    assert PharmacyStatus.RETIRED.value == "retired"
    assert PharmacyStatus.RETIRED is not PharmacyStatus.REJECTED
    assert SwarmPharmacyStatus.RETIRED.value == "retired"
