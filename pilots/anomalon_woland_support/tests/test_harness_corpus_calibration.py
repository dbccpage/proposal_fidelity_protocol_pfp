"""Cross-repository harness calibration; requires the Anomalon harness runtime.

This is retained corpus evidence, not a standalone PFP runtime test.
"""

from omega_engine_woland.infrastructure.research import harness_tasks
from omega_engine_woland.infrastructure.research.harness_tasks import freeze_tasks, judge


def test_three_independent_judged_families_calibrate(monkeypatch):
    # Corpus-only adapter; this does not bind external checkers into a live campaign.
    from importlib import import_module

    def relocated_pair(kind):
        return tuple(getattr(import_module("pilots.anomalon_woland." + module), entrypoint)
                     for module, entrypoint in harness_tasks.CHECKER_MODULES[kind])

    monkeypatch.setattr(harness_tasks, "_checker_pair", relocated_pair)
    from pilots.anomalon_woland.c052_maxflow_mincut_certificates.reference_solver.solver import (
        solve as flow,
    )
    from pilots.anomalon_woland.c054_exact_linear_systems.reference_solver.solver import (
        solve as linear,
    )
    from pilots.anomalon_woland.c059_sql_null_total_query_synthesis.reference_solver.solver import (
        solve as sql,
    )

    count = 0
    for task in freeze_tasks():
        if task["kind"] in ("flow", "linear", "sql"):
            for case in task["public"] + task["private"]:
                output = {"flow": flow, "linear": linear, "sql": sql}[task["kind"]](case)
                assert judge(task["kind"], case, output)[0]
                assert not judge(task["kind"], case, {})[0]
                count += 1
    assert count == 158
