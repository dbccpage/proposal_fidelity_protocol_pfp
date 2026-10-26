"""Continue a checked prefix without resetting accounting or sending it twice."""

import copy

import pytest

from omega_engine_pfp.infrastructure.pilot_runners.empirical_gates import collect_token_amortization
from omega_engine_pfp.tests.test_empirical_gate_collection import MODELS, TASKS, gateways


def test_retained_settled_prefix_continues_same_allowance_without_resending(tmp_path):
    supplied, calls, _ = gateways(tmp_path)
    prefix = collect_token_amortization(
        run_id="same-run", tasks=TASKS, model_ids=MODELS[:1], gateways=supplied)
    assert len(calls) == 8
    changed = copy.deepcopy(prefix["rows"])
    changed[0]["source_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="RETAINED_MEASUREMENT_NOT_SETTLED"):
        collect_token_amortization(run_id="same-run", tasks=TASKS, model_ids=MODELS,
                                   gateways=supplied, retained_rows=changed)
    assert len(calls) == 8
    completed = collect_token_amortization(
        run_id="same-run", tasks=TASKS, model_ids=MODELS, gateways=supplied,
        retained_rows=prefix["rows"])
    assert len(calls) == 32
    assert completed["summary"]["four_model_coverage"]
    assert completed["rows"][:8] == prefix["rows"]
