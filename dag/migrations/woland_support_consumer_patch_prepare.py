"""Prepare reviewable consumer changes; never write either source repository.

Only sibling woland_support_consumer_patch* artifacts are written. The parent
migration owner applies patches after reviewing their source hashes and move plan.
"""
from __future__ import annotations

import ast
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREFIX = "woland_support_consumer_patch"
ANOMALON = HERE.parents[2] / "anomalon"
SUPPORT = "pilots/anomalon_woland_support"
BASE = "9d5e9f38d7c7f966b2f78a2125db2c0ed4d1cf6c"
changes = []
reads = {}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read(path: str) -> str:
    raw = (ANOMALON / path).read_bytes()
    reads[path] = {"sha256": sha(raw), "lines": len(raw.splitlines())}
    return raw.decode("utf-8")


def change(path: str, original: str | None, revised: str | None, reason: str, repo="anomalon"):
    if revised is not None and path.endswith(".py"):
        ast.parse(revised, filename=path)
    changes.append({
        "repository": repo, "path": path, "reason": reason,
        "before_sha256": sha(original.encode()) if original is not None else None,
        "after_sha256": sha(revised.encode()) if revised is not None else None,
        "before": original, "after": revised,
    })


def remove_functions(source: str, names: set[str]):
    lines = source.splitlines(keepends=True)
    selected = []
    for node in ast.parse(source).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names:
            start = min([node.lineno, *[d.lineno for d in node.decorator_list]]) - 1
            selected.append((start, node.end_lineno, node.name))
    assert {name for _, _, name in selected} == names
    extracted = "\n\n".join("".join(lines[start:end]).rstrip() for start, end, _ in selected) + "\n"
    for start, end, _ in reversed(selected):
        del lines[start:end]
    return "".join(lines), extracted


def prepare_checker_boundary():
    task_path = "omega_engine_woland/infrastructure/research/harness_tasks.py"
    old = read(task_path)
    start = old.index("from omega_engine_woland.tests.pilots.")
    end = old.index("\n\nCONTRACTS =", start)
    resolver = '''
class HarnessCheckerUnavailable(ValueError):
    """The historical calibration checker corpus is not installed locally."""


CHECKER_MODULES = {
    "flow": (
        ("c052_maxflow_mincut_certificates.judge_packet.exact_checker", "check_solution"),
        ("c052_maxflow_mincut_certificates.judge_packet.independent_checker", "check_solution"),
    ),
    "linear": (
        ("c054_exact_linear_systems.judge_packet.exact_checker", "check_exact"),
        ("c054_exact_linear_systems.judge_packet.independent_checker", "independent_check"),
    ),
    "sql": (
        ("c059_sql_null_total_query_synthesis.judge_packet.exact_checker", "verify_candidate"),
        ("c059_sql_null_total_query_synthesis.judge_packet.independent_checker", "independent_check"),
    ),
}


def _checker_pair(kind):
    """Resolve only legacy local owners; never substitute unbound external judges."""
    from importlib import import_module

    pairs = []
    for suffix, entrypoint in CHECKER_MODULES[kind]:
        module = "omega_engine_woland.tests.pilots." + suffix
        try:
            owner = import_module(module)
        except ModuleNotFoundError as error:
            # Preserve internal checker dependency defects as their original error.
            if error.name and (error.name == module or module.startswith(error.name + ".")):
                raise HarnessCheckerUnavailable(
                    "HARNESS_CHECKER_CORPUS_UNAVAILABLE:" + kind
                    + "; historical pilots moved to proposal_fidelity_protocol_pfp/"
                    "pilots/anomalon_woland; live campaigns require a separately bound checker adapter"
                ) from error
            raise
        pairs.append(getattr(owner, entrypoint))
    return tuple(pairs)


def require_checkers(kinds=("flow", "linear", "sql")):
    """Fail before execution or billing when a requested corpus checker is absent."""
    for kind in kinds:
        if kind in CHECKER_MODULES:
            _checker_pair(kind)
'''
    new = old[:start] + resolver + old[end:]
    new = new.replace('def judge(kind, case, result):\n',
                      'def judge(kind, case, result):\n    if kind in CHECKER_MODULES:\n        exact, independent = _checker_pair(kind)\n')
    for family in ("flow", "linear", "sql"):
        new = new.replace(f"{family}_exact(case, result), {family}_independent(case, result)",
                          "exact(case, result), independent(case, result)")
    new = new.replace('def execute_cases(runner, code, task, cases, store):\n',
                      'def execute_cases(runner, code, task, cases, store):\n    require_checkers((task["kind"],))\n')
    change(task_path, old, new, "Lazy legacy checker boundary; absent relocated corpus raises a specific infrastructure error, while built-in task checks remain usable.")

    evaluator_path = "omega_engine_woland/infrastructure/research/harness_evaluator.py"
    old = read(evaluator_path)
    new = old.replace('    participant_task,\n', '    participant_task,\n    require_checkers,\n')
    new = new.replace('    def trial(self, candidate, task, phase, name, repetition):\n',
                      '    def trial(self, candidate, task, phase, name, repetition):\n        require_checkers((task["kind"],))\n')
    change(evaluator_path, old, new, "Refuse a missing task checker before assignments, execution, provider dispatch or billing.")


def main():
    prepare_checker_boundary()
    cli_path = "omega_engine_woland/entrypoints/research/harness_cli.py"
    old = read(cli_path)
    new = old.replace('DEFAULT_PRICES = (\n    ROOT / "omega_engine_woland/documentation/harness_evolution/pricing_observation.json"\n)\n', '')
    new = new.replace('parser.add_argument("--prices", type=Path, default=DEFAULT_PRICES)',
                      'parser.add_argument(\n        "--prices", type=Path, required=True,\n        help="Explicit pricing observations: current for live runs, frozen for historical replay",\n    )')
    new = new.replace('"--pricing-evidence", type=Path, default=DEFAULT_PRICES.with_name("pricing_evidence.json")',
                      '"--pricing-evidence", type=Path, required=True,\n        help="Evidence bytes whose SHA-256 is bound by every supplied pricing row"')
    assert new != old and "DEFAULT_PRICES" not in new
    new = new.replace('from omega_engine_woland.infrastructure.research.harness_store import HarnessStore\n',
                      'from omega_engine_woland.infrastructure.research.harness_store import HarnessStore\nfrom omega_engine_woland.infrastructure.research.harness_tasks import require_checkers\n')
    new = new.replace('    store = HarnessStore(args.output)\n',
                      '    if args.command in ("run", "resume") or (args.command == "preflight" and args.live):\n        require_checkers()\n    store = HarnessStore(args.output)\n')
    change(cli_path, old, new, "Require explicit pricing/evidence; relocated historical observations are not runtime defaults.")

    fixture = '''"""Synthetic rates for offline harness tests; these are not market-price observations."""

import hashlib
import json
from pathlib import Path

PRICING_EVIDENCE = b'{"kind":"offline-test-fixture","market_quote":false}\\n'


def pricing_fixture():
    """Fresh mapping so mutation tests cannot alter another test's rates."""
    rows = {}
    for model, input_rate, output_rate in (
        ("claude-haiku-5-5", 100_000, 500_000),
        ("claude-sonnet-5-5", 2_000_000, 10_000_000),
    ):
        rows[model] = {
            "model_deployment_id": model,
            "input_microusd_per_mtok": input_rate,
            "output_microusd_per_mtok": output_rate,
            "effective_from_utc": "2026-10-23T14:50:07.000000Z",
            "observed_at_utc": "2026-10-23T14:50:07.000000Z",
            "stale_after_utc": "2026-10-24T14:50:07.000000Z",
            "evidence_digest": "sha256:" + hashlib.sha256(PRICING_EVIDENCE).hexdigest(),
        }
    return rows


def pricing_cli_args(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    prices = directory / "synthetic-prices.json"
    evidence = directory / "synthetic-evidence.json"
    prices.write_text(json.dumps(pricing_fixture()), encoding="utf-8")
    evidence.write_bytes(PRICING_EVIDENCE)
    return ["--prices", str(prices), "--pricing-evidence", str(evidence)]
'''
    fixture_path = "omega_engine_woland/tests/research/harness_fixtures.py"
    assert not (ANOMALON / fixture_path).exists()
    change(fixture_path, None, fixture, "Own the accounting test inputs locally, without reading demo receipts.")

    archive_test = "omega_engine_woland/tests/research/test_frozen_review_replay.py"
    old = read(archive_test)
    relocated = old.replace("from omega_engine_woland.documentation.harness_evolution import", "from pilots.anomalon_woland_support.documentation.harness_evolution import")
    change(archive_test, old, None, "Move archive-specific tests with the retained archive tooling.")
    change(SUPPORT + "/tests/test_frozen_review_replay.py", None, relocated, "Import relocated tool; keep frozen internal archive paths unchanged.", "pfp")

    calibration_test = "omega_engine_woland/tests/test_calibration_tasks.py"
    old = read(calibration_test)
    change(calibration_test, old, None, "Move dedicated calibration-bank tests beside their corpus.")
    change(SUPPORT + "/tests/test_calibration_tasks.py", None, old, "Existing parents[1]/program_profiles/calibration resolves correctly from support/tests.", "pfp")

    execution_path = "omega_engine_woland/tests/research/test_harness_execution.py"
    old = read(execution_path)
    new = old.replace('from omega_engine_woland.tests.research.test_harness_contracts import receipt',
                      'from omega_engine_woland.tests.research.harness_fixtures import pricing_fixture\nfrom omega_engine_woland.tests.research.test_harness_contracts import receipt')
    start = new.index("PRICES = json.loads(")
    end = new.index("\nCODE =", start)
    new = new[:start] + "PRICES = pricing_fixture()" + new[end:]
    new, calibration = remove_functions(new, {"test_three_independent_judged_families_calibrate"})
    new = new.replace("and frozen-task calibration.", "and runtime task checks.")
    new = new.replace("from omega_engine_woland.infrastructure.research.harness_tasks import freeze_tasks, judge\n", "")
    change(execution_path, old, new, "Retain orchestration/replay coverage; remove historical pricing dependency and relocate corpus calibration.")
    calibration = calibration.replace("omega_engine_woland.tests.pilots.", "pilots.anomalon_woland.")
    calibration = calibration.replace('def test_three_independent_judged_families_calibrate():',
        '''def test_three_independent_judged_families_calibrate(monkeypatch):
    # Corpus-only adapter; this does not bind external checkers into a live campaign.
    from importlib import import_module

    def relocated_pair(kind):
        return tuple(getattr(import_module("pilots.anomalon_woland." + module), entrypoint)
                     for module, entrypoint in harness_tasks.CHECKER_MODULES[kind])

    monkeypatch.setattr(harness_tasks, "_checker_pair", relocated_pair)''')
    calibration = ('"""Cross-repository harness calibration; requires the Anomalon harness runtime.\n\n'
                   'This is retained corpus evidence, not a standalone PFP runtime test.\n"""\n\n'
                   'from omega_engine_woland.infrastructure.research import harness_tasks\n'
                   'from omega_engine_woland.infrastructure.research.harness_tasks import freeze_tasks, judge\n\n\n' + calibration)
    change(SUPPORT + "/tests/test_harness_corpus_calibration.py", None, calibration,
           "Preserve three-family calibration with relocated public solvers; runtime checker import prerequisite remains explicit.", "pfp")

    budget_path = "omega_engine_woland/tests/providers/test_harness_anthropic_budget.py"
    old = read(budget_path)
    new = old.replace("from pathlib import Path\n", "")
    start = new.index("ROOT = Path(")
    end = new.index("\n\ndef spec()", start)
    new = new[:start] + ('from omega_engine_woland.tests.research.harness_fixtures import pricing_fixture\n\n'
                        'PRICES = pricing_fixture()\n') + new[end:]
    change(budget_path, old, new, "Keep provider accounting tests and expected arithmetic with synthetic fixture rates.")

    regressions_path = "omega_engine_woland/tests/research/test_harness_review_regressions.py"
    old = read(regressions_path)
    new, packaging = remove_functions(old, {"test_package_refuses_linked_payload_directories", "test_package_traversal_errors_are_fatal"})
    for import_line in ["import os\n", "import subprocess\n", "from omega_engine_woland.documentation.harness_evolution import build_review_package as package\n"]:
        new = new.replace(import_line, "")
    new = new.replace("from omega_engine_woland.tests.research.test_harness_contracts import spec as fixture_spec",
                      "from omega_engine_woland.tests.research.harness_fixtures import pricing_cli_args\nfrom omega_engine_woland.tests.research.test_harness_contracts import spec as fixture_spec")
    new = new.replace('harness_cli.main(["preflight", "--live", "--image", "fixture", "--output", str(store.root)])',
                      'harness_cli.main(["preflight", "--live", "--image", "fixture", "--output", str(store.root),\n                          *pricing_cli_args(tmp_path / "pricing")])')
    new = new.replace('    monkeypatch.setattr(harness_cli, "prepare", lambda *a: fixture_spec())',
                      '    monkeypatch.setattr(harness_cli, "require_checkers", lambda: None)\n    monkeypatch.setattr(harness_cli, "prepare", lambda *a: fixture_spec())')
    change(regressions_path, old, new, "Retain all runtime regressions; split only package-copy tests and supply explicit fixture pricing to mocked CLI.")
    packaging = ('"""Offline safety checks for the relocated historical package builder."""\n\n'
                 'import os\nimport subprocess\n\nimport pytest\n\n'
                 'from pilots.anomalon_woland_support.documentation.harness_evolution import build_review_package as package\n\n\n' + packaging)
    change(SUPPORT + "/tests/test_harness_package_copy.py", None, packaging, "Move archive package-copy safety tests without skipping them.", "pfp")

    ddc_path = "omega_engine_woland/tests/test_ddc_code_repair.py"
    old = read(ddc_path)
    demo = read("omega_engine_woland/documentation/examples/code_repair.py")
    nodes = [node for node in ast.parse(demo).body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in {"SOURCE", "CHECK", "PATCH"} for t in node.targets)]
    assert len(nodes) == 3
    literals = "\n".join(ast.get_source_segment(demo, n) for n in nodes)
    new = old.replace("from omega_engine_woland.documentation.examples.code_repair import CHECK, PATCH, SOURCE\n", "")
    new = new.replace("ROOT = Path(__file__).resolve().parents[2]", '# Test-owned toy inputs. Runtime coverage does not import the archived example CLI.\n' + literals + '\n\nROOT = Path(__file__).resolve().parents[2]')
    change(ddc_path, old, new, "Keep native composition/runtime tests; inline only the minimal test program/check/patch literals.")

    windows_path = "omega_engine_woland/tests/research/test_windows_harness.py"
    old = read(windows_path)
    new = old.replace('                "--windows-runtime",', '                "--prices",\n                "unused-prices.json",\n                "--pricing-evidence",\n                "unused-evidence.json",\n                "--windows-runtime",')
    assert old != new
    change(windows_path, old, new, "Keep early Windows paid-entrypoint refusal test; explicit placeholder pricing paths are never read.")

    boundary_tests = (HERE / (PREFIX + "_boundary_tests.txt")).read_text(encoding="utf-8")
    change("omega_engine_woland/tests/research/test_harness_corpus_boundary.py", None, boundary_tests,
           "Offline regressions for missing corpus, internal import errors, zero-side-effect refusal and explicit pricing.")

    usage = (HERE / (PREFIX + "_support_usage.md")).read_text(encoding="utf-8")
    change(SUPPORT + "/CURRENT_USE.md", None, usage,
           "Document current test invocation and historical helper limits outside frozen corpus bytes.", "pfp")

    for repo in ("anomalon", "pfp"):
        patch = []
        for row in changes:
            if row["repository"] != repo:
                continue
            patch.extend(difflib.unified_diff(
                (row["before"] or "").splitlines(keepends=True),
                (row["after"] or "").splitlines(keepends=True),
                fromfile="a/" + row["path"] if row["before"] is not None else "/dev/null",
                tofile="b/" + row["path"] if row["after"] is not None else "/dev/null",
            ))
        (HERE / f"{PREFIX}.{repo}.patch").write_text("".join(patch), encoding="utf-8", newline="\n")
    report = {
        "anomalon_source_commit": BASE,
        "status": "prepared_not_applied",
        "scope": "Consumer changes only; corpus bytes and frozen internal archive paths remain unchanged.",
        "source_reads": reads,
        "changes": changes,
        "validation": ["Every revised Python file parsed with ast.parse; preparation itself performs no execution.",
                       "Original source files were read only; outputs confined to this prefix."],
        "bounded_overlay_validation": json.loads((HERE / (PREFIX + "_validation.json")).read_text(encoding="utf-8")) if (HERE / (PREFIX + "_validation.json")).exists() else None,
        "application_notes": [
            "Full original frozen-review test must also be retained byte-for-byte as support/tests/historical_sources/test_frozen_review_replay.py.txt; parent move plan owns this source copy.",
            "If the parent move receipt verifies a deleted source is already absent, skip that patch deletion. If the calibration test target already has after_sha256, its addition is a no-op.",
            "Apply all remaining rows only after checking exact before_sha256 / absent-new-path preconditions. No source mutation is performed by this preparer.",
        ],
        "blocking_prerequisites": [
            "Live certificate campaigns intentionally remain unavailable without a separately source-bound checker adapter. The explicit relocated calibration test uses real PFP checker owners only within that test.",
            "Historical replay/package helpers retain original ROOT/SERIES/ARCHIVE assumptions; actual full archive default is already absent. Run them only with explicit historical context or a separate adapter; do not rewrite frozen evidence.",
            "Apply PFP additions only after the support corpus is copied. Dedicated archive/calibration source removals are authorized migrations only after target-byte custody verification.",
        ],
    }
    (HERE / f"{PREFIX}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"changes": len(changes), "repositories": {r: sum(c['repository'] == r for c in changes) for r in ('anomalon','pfp')}, "status": report['status']}))


if __name__ == "__main__":
    main()
