"""A reference self-check cannot earn REFERENCE_SELF_CONSISTENT without its asserted evidence."""

import pytest
from projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask import (
    run_adversary_bout as bout,
)


@pytest.mark.parametrize(
    "failure, expected",
    [
        ("empty", "EMPTY_MUTATION_AUDIT"),
        ("survived", "MUTATION_AUDIT_FAILED"),
        ("no_cycle", "NO_CONTRADICTION_WITNESS"),
    ],
)
def test_failed_evidence_refuses_before_persistence(monkeypatch, tmp_path, failure, expected):
    if failure == "empty":
        monkeypatch.setattr(bout, "generate_mutation_cases", lambda: [])
    elif failure == "survived":
        monkeypatch.setattr(
            bout, "verify_certificate", lambda *args: (True, "test mutation survived")
        )
    else:
        monkeypatch.setattr(
            bout, "host_verdict", lambda system: ("CONSISTENT", {v: 0 for v in system.items})
        )
    target = tmp_path / "must_not_be_created"
    result = bout.run_adversary_c001_bout(custom_run_dir=target)
    assert result.is_err
    assert result.unwrap_err().code == expected
    assert not target.exists()
