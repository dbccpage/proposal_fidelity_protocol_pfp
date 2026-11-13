"""PR #63 review (P2): workflow custody covers the EIS/PCIV/OPERADS code the workflows invoke."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest

import source_custody
from host_charpoly_workflows import HOST_CHARPOLY_PLANS, IMPLEMENTATION_FILES as HOST_IMPLEMENTATION_FILES
from eis_pciv_workflows import EIS_PCIV_PLANS, IMPLEMENTATION_FILES as EIS_IMPLEMENTATION_FILES

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

PROBE = """
import json, sys
sys.path[:0] = [sys.argv[1], sys.argv[2], sys.argv[3]]
import host_charpoly_workflows, eis_pciv_workflows
import eis.domain.allostery, eis.domain.value_objects, eis.use_cases.two_signal_regulation
import operads.domain.operad.planar, operads.domain.operad.operation, operads.domain.operad.colours
root = sys.argv[2]
print(json.dumps(sorted({m.__file__ for m in list(sys.modules.values())
                         if getattr(m, '__file__', None) and m.__file__.startswith(root)})))
"""


class TestSourceCustody(unittest.TestCase):
    def test_runtime_closure_is_pinned(self):
        out = subprocess.run([sys.executable, "-I", "-B", "-c", PROBE, str(HERE), str(ROOT), str(ROOT / "ops")],
                             capture_output=True, text=True, check=True)
        imported = {Path(p).resolve().relative_to(ROOT).as_posix() for p in json.loads(out.stdout)}
        # Every imported module -- including the dag/benchmark files, which were previously
        # skipped -- must be pinned: the regulation files by repo-relative path, the benchmark
        # files (source_custody.py among them) by their dag/benchmark implementation pins.
        dag_pinned = {f"workflows/wf52_finite_qm_benchmark/{name}" for name in set(HOST_IMPLEMENTATION_FILES) | set(EIS_IMPLEMENTATION_FILES)}
        pinned = set(source_custody.REGULATION_FILES) | dag_pinned
        self.assertEqual(sorted(imported - pinned), [])
        self.assertIn("source_custody.py", HOST_IMPLEMENTATION_FILES)

    def test_plans_pin_regulation_modules(self):
        for plans in (HOST_CHARPOLY_PLANS, EIS_PCIV_PLANS):
            for plan in plans.values():
                for name in ("eis/use_cases/two_signal_regulation.py", "eis/domain/allostery.py",
                             "operads/domain/operad/planar.py", "pciv/use_cases/fitness.py"):
                    self.assertIn(name, plan["source_pins"])

    def test_changed_regulation_module_invalidates_a_plan(self):
        import reference_runner as rr

        plan_id = next(iter(HOST_CHARPOLY_PLANS))
        original = deepcopy(HOST_CHARPOLY_PLANS[plan_id]["source_pins"])
        try:
            HOST_CHARPOLY_PLANS[plan_id]["source_pins"]["eis/use_cases/two_signal_regulation.py"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "source changed"):
                rr.run(plan_id, rr.OfflineTape(["x"]), Path("unused-never-created"), "custody-probe", max_output_tokens=10)
        finally:
            HOST_CHARPOLY_PLANS[plan_id]["source_pins"] = original


if __name__ == "__main__":
    unittest.main()
