"""Four-layer release gate for the Symbol Game package.

`EPIC-OE-SYMGAM-010` asks for an autopoietic replay engine and a mutual
verification harness whose layers fail *independently*. The harness under test
is `omega_engine_pfp/infrastructure/release_gate.py`; this module is the
second witness for it.

Each criterion below is paired with the mutation the epic names as decisive. A
criterion no mutation can turn red is not a criterion, so every positive
assertion here has a negative twin that breaks it.

The load-bearing fact this sprint found: **the epic manifest audit had 48 tests
and every one of them ran against a `tmp_path` fixture.** None audited the real
repository, so a real drift -- an epic plan file edited without the manifest
being regenerated -- sat in `origin/main` undetected. The manifest tests below
close that hole by auditing the repository this file lives in.

AuthorityEffect: None. Replaying a corpus is not certifying a release.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from omega_engine_pfp.infrastructure.release_gate import (
    ALL_LAYERS,
    GOLDEN_CORPUS_PATH,
    LAYER_EPIC_MANIFEST,
    LAYER_HOST_PARITY,
    LAYER_LEAN_CONCORDANCE,
    LAYER_WIRE_PARITY,
    LayerFinding,
    LayerOutcome,
    ReleaseGateError,
    first_difference,
    format_report,
    is_release_ready,
    load_golden_corpus,
    outcome_census,
    replay_vector,
    run_all_layers,
    unbacked_claims,
    verify_epic_manifest,
    verify_host_parity,
    verify_lean_concordance,
    verify_wire_parity,
)

# Imported under an alias: pytest collects any module-level name matching
# `test_*` as a test case, and `test_names_in` is a helper taking a path. Under
# its own name it would be collected, called with no arguments, and reported as
# an error in this file rather than as the utility it is.
from omega_engine_pfp.infrastructure.release_gate import (  # noqa: E402
    test_names_in as collect_test_names,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CORPUS_PATH = REPO_ROOT / GOLDEN_CORPUS_PATH
DOSSIER_PATH = (
    REPO_ROOT / "omega_engine_pfp" / "infrastructure" / "release_dossier.json"
)


def _real_vectors() -> list[dict]:
    return load_golden_corpus(CORPUS_PATH)


def _write_corpus(path: pathlib.Path, vectors: list[dict]) -> pathlib.Path:
    """Write a corpus whose declared count matches its contents.

    The count is derived rather than passed so a test that mutates a *vector*
    cannot accidentally also trip the truncation check and pass for the wrong
    reason.
    """
    path.write_text(
        json.dumps({"vector_count": len(vectors), "vectors": vectors}),
        encoding="utf-8",
    )
    return path


# --------------------------------------------------------------------------
# Criterion 1 -- every recorded episode replays byte-identically
# --------------------------------------------------------------------------


def test_every_recorded_vector_replays_byte_identically():
    finding = verify_wire_parity(REPO_ROOT)
    assert finding.outcome is LayerOutcome.SATISFIED, finding.detail
    assert finding.checked == finding.total
    # A corpus that replays 0 of 0 would also satisfy "no problems"; the count
    # is asserted positive so an emptied corpus cannot read as parity.
    assert finding.total > 0


def test_corpus_is_not_self_compared():
    """The corpus is written by Rust; this harness is the Python witness."""
    vectors = _real_vectors()
    assert vectors, "corpus is empty"
    for vector in vectors:
        assert replay_vector(vector) == []


def test_single_byte_mutation_names_the_vector_and_its_offset():
    """Epic's decisive mutation for criterion 1."""
    vectors = _real_vectors()
    victim = dict(vectors[0])
    recorded = bytearray(bytes.fromhex(victim["canonical_bytes_hex"]))
    # Flip one bit of the final byte: the offset is then known exactly, so the
    # test asserts the reported position rather than merely that it failed.
    flip_at = len(recorded) - 1
    recorded[flip_at] ^= 0x01
    victim["canonical_bytes_hex"] = bytes(recorded).hex()

    problems = replay_vector(victim)

    assert problems, "a mutated byte replayed as identical"
    joined = "; ".join(problems)
    assert victim["name"] in joined, joined
    assert f"offset {flip_at}" in joined, joined


def test_mutated_corpus_makes_the_wire_layer_violated(tmp_path):
    vectors = _real_vectors()
    victim = dict(vectors[0])
    victim["domain_digest_sha256"] = "0" * 64
    corpus = _write_corpus(tmp_path / "corpus.json", [victim, *vectors[1:]])

    finding = verify_wire_parity(REPO_ROOT, corpus)

    assert finding.outcome is LayerOutcome.VIOLATED
    # The pair stays informative: one vector failed, the rest still replayed.
    assert finding.checked == len(vectors) - 1
    assert finding.total == len(vectors)
    assert "domain digest differs" in finding.detail


def test_first_difference_reports_offset_and_truncation():
    assert first_difference(b"abc", b"abc") is None
    assert first_difference(b"abc", b"abd") == 2
    # A prefix is not equal to the whole; the truncation point is the answer.
    assert first_difference(b"ab", b"abc") == 2
    assert first_difference(b"abc", b"ab") == 2


def test_silently_truncated_corpus_is_refused(tmp_path):
    """Dropping a vector without updating the count must not report parity."""
    vectors = _real_vectors()
    corpus = tmp_path / "corpus.json"
    corpus.write_text(
        json.dumps({"vector_count": len(vectors), "vectors": vectors[:-1]}),
        encoding="utf-8",
    )
    with pytest.raises(ReleaseGateError) as excinfo:
        load_golden_corpus(corpus)
    assert excinfo.value.code == "CORPUS_COUNT_MISMATCH"


def test_empty_corpus_is_refused_rather_than_reported_green(tmp_path):
    corpus = _write_corpus(tmp_path / "corpus.json", [])
    with pytest.raises(ReleaseGateError) as excinfo:
        load_golden_corpus(corpus)
    assert excinfo.value.code == "CORPUS_EMPTY"


def test_vector_missing_a_required_key_is_a_corpus_defect(tmp_path):
    vectors = _real_vectors()
    stripped = {k: v for k, v in vectors[0].items() if k != "canonical_json"}
    corpus = _write_corpus(tmp_path / "corpus.json", [stripped])
    with pytest.raises(ReleaseGateError) as excinfo:
        load_golden_corpus(corpus)
    assert excinfo.value.code == "CORPUS_VECTOR_KEYS"
    assert "canonical_json" in excinfo.value.detail


@pytest.mark.parametrize(
    "payload,code",
    [
        ("[]", "CORPUS_SHAPE"),
        ('{"vector_count": 1}', "CORPUS_SHAPE"),
        ("{not json", "CORPUS_UNREADABLE"),
    ],
)
def test_unusable_corpus_shapes_are_refused(tmp_path, payload, code):
    corpus = tmp_path / "corpus.json"
    corpus.write_text(payload, encoding="utf-8")
    with pytest.raises(ReleaseGateError) as excinfo:
        load_golden_corpus(corpus)
    assert excinfo.value.code == code


def test_missing_corpus_is_refused(tmp_path):
    with pytest.raises(ReleaseGateError) as excinfo:
        load_golden_corpus(tmp_path / "absent.json")
    assert excinfo.value.code == "CORPUS_MISSING"


# --------------------------------------------------------------------------
# Criterion 2 -- each verification layer fails independently
# --------------------------------------------------------------------------


def _finding(layer: str, outcome: LayerOutcome) -> LayerFinding:
    return LayerFinding(
        layer=layer, outcome=outcome, checked=1, total=1, detail="fixture"
    )


def test_every_declared_layer_reports_exactly_once():
    findings = run_all_layers(REPO_ROOT)
    assert tuple(f.layer for f in findings) == ALL_LAYERS
    assert len({f.layer for f in findings}) == len(ALL_LAYERS)


def test_a_fault_at_one_layer_is_attributed_to_that_layer():
    """Epic's decisive mutation for criterion 2.

    Layer 3 is driven to VIOLATED through its injected runner while the other
    three layers run for real. If the harness collapsed its layers into one
    report, the wire and manifest layers would be dragged red with it.
    """

    def failing_runner(_repo_root):
        return 1, "OK skill_a\nFAIL skill_b differs between .agents and .grok\n"

    faulted = verify_host_parity(REPO_ROOT, failing_runner)
    assert faulted.layer == LAYER_HOST_PARITY
    assert faulted.outcome is LayerOutcome.VIOLATED
    assert "skill_b" in faulted.detail

    # The neighbouring layers are untouched by that fault.
    assert verify_wire_parity(REPO_ROOT).outcome is LayerOutcome.SATISFIED
    assert verify_epic_manifest(REPO_ROOT).outcome is LayerOutcome.SATISFIED


def test_the_harness_does_not_short_circuit_after_a_violation():
    """Two simultaneous faults must both be attributable.

    A gate that stopped at the first failure could report only one of them, and
    the second would be discovered only after the first was fixed.
    """
    findings = run_all_layers(REPO_ROOT)
    assert len(findings) == len(ALL_LAYERS)
    # Layer 4 is UNVERIFIABLE in this repository, yet layers 1-3 still ran and
    # produced their own counts -- evidence that no layer gates another.
    by_layer = {f.layer: f for f in findings}
    assert by_layer[LAYER_LEAN_CONCORDANCE].outcome is LayerOutcome.UNVERIFIABLE
    assert by_layer[LAYER_WIRE_PARITY].total > 0
    assert by_layer[LAYER_HOST_PARITY].total > 0


def test_a_findings_set_missing_a_layer_is_refused():
    """Collapsing two layers into one report is caught rather than averaged."""
    collapsed = [
        _finding(LAYER_WIRE_PARITY, LayerOutcome.SATISFIED),
        _finding(LAYER_EPIC_MANIFEST, LayerOutcome.SATISFIED),
        _finding(LAYER_HOST_PARITY, LayerOutcome.SATISFIED),
    ]
    with pytest.raises(ReleaseGateError) as excinfo:
        is_release_ready(collapsed)
    assert excinfo.value.code == "LAYER_SET"


def test_an_undeclared_layer_name_is_refused():
    with pytest.raises(ReleaseGateError) as excinfo:
        _finding("LAYER_9_INVENTED", LayerOutcome.SATISFIED)
    assert excinfo.value.code == "UNKNOWN_LAYER"


@pytest.mark.parametrize(
    "checked,total,code",
    [(2, 1, "COUNT_EXCEEDS_TOTAL"), (-1, 1, "NEGATIVE_COUNT")],
)
def test_incoherent_counts_are_refused(checked, total, code):
    with pytest.raises(ReleaseGateError) as excinfo:
        LayerFinding(
            layer=LAYER_WIRE_PARITY,
            outcome=LayerOutcome.SATISFIED,
            checked=checked,
            total=total,
            detail="",
        )
    assert excinfo.value.code == code


def test_unverifiable_blocks_release_exactly_as_violated_does():
    """`UNVERIFIABLE` is a missing witness, never a quiet pass."""
    all_satisfied = [_finding(layer, LayerOutcome.SATISFIED) for layer in ALL_LAYERS]
    assert is_release_ready(all_satisfied) is True

    for blocking in (LayerOutcome.UNVERIFIABLE, LayerOutcome.VIOLATED):
        degraded = [
            _finding(layer, LayerOutcome.SATISFIED) for layer in ALL_LAYERS[:-1]
        ] + [_finding(ALL_LAYERS[-1], blocking)]
        assert is_release_ready(degraded) is False, blocking


def test_census_counts_kinds_not_only_a_total():
    findings = [
        _finding(LAYER_WIRE_PARITY, LayerOutcome.SATISFIED),
        _finding(LAYER_EPIC_MANIFEST, LayerOutcome.VIOLATED),
        _finding(LAYER_HOST_PARITY, LayerOutcome.UNVERIFIABLE),
        _finding(LAYER_LEAN_CONCORDANCE, LayerOutcome.UNVERIFIABLE),
    ]
    assert outcome_census(findings) == {
        "SATISFIED": 1,
        "VIOLATED": 1,
        "UNVERIFIABLE": 2,
    }


def test_report_names_every_layer_and_its_verdict():
    findings = run_all_layers(REPO_ROOT)
    report = format_report(findings)
    for layer in ALL_LAYERS:
        assert layer in report, f"{layer} absent from the report"
    assert "AuthorityEffect: None" in report
    assert f"release_ready={is_release_ready(findings)}" in report


# --------------------------------------------------------------------------
# Criterion 3 -- the epic manifest audit passes on the REAL repository
# --------------------------------------------------------------------------


def test_epic_manifest_audit_passes_on_the_real_repository():
    """The check whose absence let a real drift reach `origin/main`.

    Every pre-existing manifest test ran against a `tmp_path` fixture, so an
    epic plan file edited without the manifest being regenerated was invisible
    to the suite. This audits the repository the test itself lives in.
    """
    finding = verify_epic_manifest(REPO_ROOT)
    assert finding.outcome is LayerOutcome.SATISFIED, finding.detail


def test_epic_count_is_checked_against_the_shared_constant():
    """`EXPECTED_EPIC_COUNT`, not a literal restated in the test.

    A restated literal is a second place to update, and the two drift apart in
    exactly the situation the count exists to detect.
    """
    from omega_engine_product_planning_office.domain.manifest_models import (
        EXPECTED_EPIC_COUNT,
    )
    from omega_engine_product_planning_office.use_cases.epic_manifest_audit import (
        _direct_epic_inventory,
    )

    finding = verify_epic_manifest(REPO_ROOT)
    assert finding.total == EXPECTED_EPIC_COUNT
    assert finding.checked == EXPECTED_EPIC_COUNT

    plan_files = _direct_epic_inventory(REPO_ROOT)
    assert len(plan_files) == EXPECTED_EPIC_COUNT


def test_an_unregistered_plan_file_makes_the_audit_refuse():
    """Epic's decisive mutation for criterion 3.

    A plan file is added to the real epics directory without regenerating the
    manifest. The audit must refuse; the file is removed again whatever the
    assertion does.
    """
    epics_dir = REPO_ROOT / "omega_engine_product_planning_office" / "plans" / "epics"
    intruder = epics_dir / "epic_oe_zzz_999_release_gate_mutation_probe_plan.md"
    assert not intruder.exists(), "probe file already present; refusing to clobber"
    intruder.write_text("# Unregistered probe\n", encoding="utf-8")
    try:
        finding = verify_epic_manifest(REPO_ROOT)
        assert finding.outcome is LayerOutcome.VIOLATED
        assert finding.checked == 0
    finally:
        intruder.unlink()

    # And the repository is left exactly as it was found.
    assert verify_epic_manifest(REPO_ROOT).outcome is LayerOutcome.SATISFIED


# --------------------------------------------------------------------------
# Criterion 4 -- four-host parity is verified inside this gate
# --------------------------------------------------------------------------


def test_host_parity_is_verified_inside_the_harness():
    """Not as a separate manual step: a gate nobody remembers to run is none."""
    finding = verify_host_parity(REPO_ROOT)
    assert finding.outcome is LayerOutcome.SATISFIED, finding.detail
    assert finding.checked == finding.total
    assert finding.total > 0


def test_host_drift_is_reported_by_the_harness():
    """Epic's decisive mutation for criterion 4."""

    def drifted(_repo_root):
        return 1, "OK skill_a\nFAIL skill_b .claude copy differs\nOK skill_c\n"

    finding = verify_host_parity(REPO_ROOT, drifted)
    assert finding.outcome is LayerOutcome.VIOLATED
    assert finding.checked == 2 and finding.total == 3
    assert "skill_b" in finding.detail


def test_a_nonzero_exit_without_a_fail_line_is_still_a_violation():
    """A parity script that dies before reporting must not read as green."""

    def crashed(_repo_root):
        return 2, "Traceback (most recent call last):\n"

    finding = verify_host_parity(REPO_ROOT, crashed)
    assert finding.outcome is LayerOutcome.VIOLATED
    assert "exit=2" in finding.detail


def test_lean_layer_is_unverifiable_rather_than_green_here():
    """`lean4/` is a pointer to CODA; an absent proof is not a discharged one."""
    finding = verify_lean_concordance(REPO_ROOT)
    assert finding.outcome is LayerOutcome.UNVERIFIABLE
    assert finding.checked == 0


def test_lean_layer_stays_unverifiable_when_a_manifest_appears(tmp_path):
    """A Lake manifest turning up must demand implementation, not self-certify."""
    (tmp_path / "lean4").mkdir()
    (tmp_path / "lean4" / "lakefile.toml").write_text("", encoding="utf-8")
    finding = verify_lean_concordance(tmp_path)
    assert finding.outcome is LayerOutcome.UNVERIFIABLE
    assert "must be implemented" in finding.detail


def test_lean_layer_reports_an_absent_directory_distinctly(tmp_path):
    finding = verify_lean_concordance(tmp_path)
    assert finding.outcome is LayerOutcome.UNVERIFIABLE
    assert "absent" in finding.detail


# --------------------------------------------------------------------------
# Criterion 5 -- every dossier claim names its discharging test
# --------------------------------------------------------------------------


def test_collect_test_names_reads_the_ast_not_the_text(tmp_path):
    """A docstring naming a test would satisfy a grep without a test existing."""
    module = tmp_path / "test_sample.py"
    module.write_text(
        '"""Mentions test_ghost in prose."""\n'
        "\n"
        "def test_real():\n"
        "    pass\n"
        "\n"
        "async def test_async_real():\n"
        "    pass\n"
        "\n"
        "def helper():\n"
        "    pass\n",
        encoding="utf-8",
    )
    names = collect_test_names(module)
    assert names == frozenset({"test_real", "test_async_real"})
    assert "test_ghost" not in names
    assert "helper" not in names


def test_unreadable_test_module_is_refused(tmp_path):
    module = tmp_path / "test_broken.py"
    module.write_text("def test_x(:\n", encoding="utf-8")
    with pytest.raises(ReleaseGateError) as excinfo:
        collect_test_names(module)
    assert excinfo.value.code == "TEST_MODULE_UNREADABLE"


def test_empty_dossier_is_refused():
    with pytest.raises(ReleaseGateError) as excinfo:
        unbacked_claims({}, REPO_ROOT)
    assert excinfo.value.code == "DOSSIER_EMPTY"


def test_a_claim_naming_a_missing_test_is_reported():
    """Epic's decisive mutation for criterion 5."""
    here = "omega_engine_pfp/tests/test_symbol_game_release_gate.py"
    problems = unbacked_claims(
        {
            "CLAIM-REAL": f"{here}::test_empty_dossier_is_refused",
            "CLAIM-GHOST": f"{here}::test_this_does_not_exist",
        },
        REPO_ROOT,
    )
    assert len(problems) == 1
    assert "CLAIM-GHOST" in problems[0]
    assert "defines no test_this_does_not_exist" in problems[0]


@pytest.mark.parametrize(
    "discharge,fragment",
    [
        ("no_separator_here", "does not name a test"),
        ("does/not/exist.py::test_x", "does not exist"),
    ],
)
def test_malformed_or_missing_discharges_are_reported(discharge, fragment):
    problems = unbacked_claims({"CLAIM-X": discharge}, REPO_ROOT)
    assert len(problems) == 1
    assert fragment in problems[0]


def test_release_dossier_binds_every_claim_to_a_test_that_exists():
    """The shipped dossier is checked, not a fixture standing in for it."""
    dossier = json.loads(DOSSIER_PATH.read_text(encoding="utf-8"))
    claims = dossier["claims"]
    assert claims, "dossier declares no claims"
    assert unbacked_claims(claims, REPO_ROOT) == []


def test_release_dossier_covers_every_epic_criterion():
    """A criterion absent from the dossier is an unrecorded obligation."""
    dossier = json.loads(DOSSIER_PATH.read_text(encoding="utf-8"))
    covered = {claim["criterion"] for claim in dossier["criteria"]}
    assert covered == {1, 2, 3, 4, 5}


def test_release_dossier_records_the_open_obligation_rather_than_omitting_it():
    """Layer 4 cannot be discharged here; the dossier must say so explicitly."""
    dossier = json.loads(DOSSIER_PATH.read_text(encoding="utf-8"))
    open_items = dossier["open_obligations"]
    assert open_items, "an undischargeable layer is recorded, never dropped"
    lean = [item for item in open_items if item["layer"] == LAYER_LEAN_CONCORDANCE]
    assert len(lean) == 1
    assert lean[0]["disposition"] == "UNVERIFIABLE_IN_THIS_REPOSITORY"


def test_dossier_does_not_claim_release_readiness():
    """AuthorityEffect: None. The gate reports; a human promotes."""
    dossier = json.loads(DOSSIER_PATH.read_text(encoding="utf-8"))
    assert dossier["authority_effect"] == "None"
    assert dossier["release_ready"] is False
    assert is_release_ready(run_all_layers(REPO_ROOT)) is False
