"""A native graph refusal is a typed refusal receipt, not an abandoned trace.

Counterexample: after the provider adapter began raising
``NativeFunctionalRefusal`` (the evaluator ran and refused) and
``NativeFunctionalInputRefused`` (the request was refused before the call),
``infrastructure/demos/named.py`` caught only ``NativeFunctionalUnavailable``.
The other two escaped ``execution.run``, which abandoned the trace and wrote no
receipt. The native transport is replaced here; no binary runs.
AuthorityEffect: None.
"""

from __future__ import annotations

import pytest

from adversary.infrastructure.providers.adapters import native_functional as nf
from pfp.infrastructure.demos.execution import run, verify

SCENARIO = "demo_adversary_tribunal"


def _refusal(reason: str) -> nf.NativeFunctionalRefusal:
    return nf.NativeFunctionalRefusal(reason, returncode=2, stdout="", stderr="")


@pytest.mark.parametrize(
    ("raised", "code", "reason"),
    [
        (_refusal("forest budget exceeded"), "NATIVE_FUNCTIONAL_REFUSAL", "forest budget exceeded"),
        (
            nf.NativeFunctionalInputRefused("claim edge absent from declared carrier"),
            "FUNCTIONAL_INPUT_REFUSED",
            "claim edge absent from declared carrier",
        ),
    ],
)
def test_native_refusal_writes_a_typed_refusal_receipt_with_its_reason(
    monkeypatch: pytest.MonkeyPatch, tmp_path, raised, code, reason
) -> None:
    def refusing(*args, **kwargs):
        raise raised

    monkeypatch.setattr(nf, "compute_graph_phi1", refusing)
    output = tmp_path / SCENARIO
    receipt = run(SCENARIO, output)
    assert receipt["result"]["status"] == "TYPED_REFUSAL"
    assert receipt["result"]["code"] == code
    assert reason in receipt["result"]["detail"]
    assert (output / "receipt.json").is_file()
    checked = verify(output / "receipt.json")
    assert checked["reproduced"] is True
    assert checked["outcome"] == "TYPED_REFUSAL"


def test_missing_native_pin_still_refuses_as_unavailable(monkeypatch, tmp_path) -> None:
    for name in ("CORE_FUNCTIONAL_GRAPH_BIN", "CORE_FUNCTIONAL_GRAPH_SHA256"):
        monkeypatch.delenv(name, raising=False)
    receipt = run(SCENARIO, tmp_path / SCENARIO)
    assert receipt["result"]["code"] == "FUNCTIONAL_BOUNDARY_UNAVAILABLE"
