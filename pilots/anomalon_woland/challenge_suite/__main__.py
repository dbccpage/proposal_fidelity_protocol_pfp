"""python -m omega_engine_woland.tests.pilots.challenge_suite --help"""

from __future__ import annotations

import argparse
import json
import sys
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

if __package__ in (None, ""):
    root = next(p for p in Path(__file__).resolve().parents
        if (p / "omega_engine_woland").is_dir() and (p / "omega_engine_pfp").is_dir())
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

import yaml

from omega_engine_pfp.infrastructure.challenge_execution import replay_host, run_host
from omega_engine_woland.tests.pilots.challenge_suite.catalog import PILOTS, build, selected_rows


def create_pilots(plan):
    for family in plan["families"]:
        folder = PILOTS / family["pilot_id"]
        folder.mkdir(exist_ok=True)
        (folder / "tests").mkdir(exist_ok=True)
        cases = list(selected_rows(family))
        if family["family"] == "a_mechanism":
            # These are explicitly planned instrumentation conditions, not fake
            # solver runs or 25 copies of the same neural observation.
            cases = [row for c in family["challenges"] for row in c["cases"][:30]] + [
                dict(
                    challenge=f"C{c:03d}",
                    split="development" if rung == 0 else "held_out",
                    intervention_rung=rung,
                    status="PLANNED",
                    blocker="LOCAL_MODEL_HOOKS_OR_VERIFIED_PROVIDER_CONTROLS_REQUIRED",
                )
                for c in range(1, 11)
                for rung in range(3)
            ]
        if family["family"] == "harness_tests":
            cases = [dict(test_id=name, status="PLANNED") for name in HARNESS_MUTANTS]
        spec = dict(
            schema="pfp.pilot-spec.v1",
            authority_effect="None",
            pilot_id=family["pilot_id"],
            phase="pfp_learning",
            execution_mode="PLANNED",
            source_family=family["family"],
            coordinates=dict(
                task_family="pfp_" + family["family"],
                stage_count=2,
                single_shot=False,
                target_spend_usd=0.05,
                temperature=0.0,
                model_id="not-dispatched",
            ),
            arms=["baseline", "typed_witness", "transfer", "NO_LLM_control"],
            host_gate=dict(
                checker_id="PFP-DEMO004-" + family["family"].upper(),
                expected_outcome="PLANNED",
                independent_judges="challenge-specific; C005 and C042 have one task dispatcher",
            ),
            test_plan=dict(path="testplan.yaml", tests=len(cases), cases=len(cases)),
            canonical_register="../matrix/max_pilot_matrix.yaml#pfp_challenge_learning",
            stopping_rules=[
                "maximum two stages",
                "stop on checker disagreement or infrastructure failure",
                "stop at the caller's explicit run allowance; USD 0.05 is the planned target",
                "no automatic rule admission",
            ],
            limitations=[
                "Host controls do not measure LLM capability",
                "Transfer benefit requires fresh held-out trials",
            ],
        )
        (folder / "spec.yaml").write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")
        (folder / "testplan.yaml").write_text(
            yaml.safe_dump(dict(schema="pfp.challenge-testplan.v1", cases=cases), sort_keys=False),
            encoding="utf-8",
        )
        (folder / "run.py").write_text(
            '"""Thin route to the shared PFP learning campaign. AuthorityEffect: None."""\nfrom omega_engine_woland.tests.pilots.challenge_suite.__main__ import main\n\nif __name__ == "__main__":\n    main()\n',
            encoding="utf-8",
        )
        readme = f"# {family['pilot_id']}: {family['family']}\n\nAuthorityEffect: None.\n\n" + (
            "This pilot tests PFP proposal fidelity and transfer of bounded repair rules across the original challenge family. "
            "The complete source problems remain at repository paths `omega_engine_pfp/tests/demo_004/` "
            "and `omega_engine_woland/tests/pilots/`. Cases and source digests live in the canonical matrix.\n\n"
            "Run `python -m omega_engine_woland.tests.pilots.challenge_suite --help` from the repository root. "
            "Use `--host` for trusted NO_LLM controls and `--replay` for independent reruns. "
            "A reference solver's output is a control, never a model response.\n\n"
            "Compare a baseline prompt, a typed witness prompt, and a failure-derived rule on disjoint held-out cases. "
            "Allow at most two stages. Checker disagreement stops the run. Rules remain candidates until transfer and self-tolerance are measured. "
            "Live dispatch requires explicit token, call and financial limits on one accounted gateway. "
            "USD 0.05 remains the planned run target; this spec supplies no execution authorization.\n\n"
            "Rust support is initially limited to the existing Q40 certificate checker through the canonical Symbol Game host. "
            "Other challenges retain their original domain judges. No claim of general mathematical or physical truth is made.\n"
        )
        (folder / "README.md").write_text(readme, encoding="utf-8")
        (folder / "tests/test_pilot.py").write_text(
            '"""Frozen test-plan custody. Domain attempts are retained in campaign receipts."""\n'
            "from pathlib import Path\nimport pytest\nimport yaml\n"
            "from omega_engine_woland.tests.pilots.challenge_suite.catalog import load_case\n"
            "from omega_engine_pfp.use_cases.pfp_prompt import stimulus\n\n"
            '_PLAN = yaml.safe_load((Path(__file__).resolve().parent.parent / "testplan.yaml").read_text(encoding="utf-8"))\n\n'
            '@pytest.mark.parametrize("case", _PLAN["cases"])\n'
            "def test_declared_case(case):\n"
            '    if "source" in case:\n'
            "        value = load_case(case)\n"
            "        assert type(value) is dict\n"
            "        assert type(stimulus(value)) is dict\n"
            "    else:\n"
            '        pytest.skip(case.get("blocker", "Planned instrumentation condition"))\n\n'
            '@pytest.mark.parametrize("case", [c for c in _PLAN["cases"] if "source" in c][:4])\n'
            "def test_refuse_source_digest_mutation(case):\n"
            '    mutated = dict(case, sha256="0" * 64)\n'
            '    with pytest.raises(ValueError, match="CASE_SOURCE_DRIFT"):\n'
            "        load_case(mutated)\n",
            encoding="utf-8",
        )
        if family["family"] == "harness_tests":
            (folder / "tests/test_pilot.py").write_text(
                '"""Actual PFP gate mutants, not inventory passes."""\nimport pytest\n'
                "from omega_engine_woland.tests.pilots.challenge_suite.__main__ import HARNESS_MUTANTS\n"
                "from omega_engine_pfp.tests.test_challenge_learning import test_gate_mutant as _assert_mutant\n\n"
                '@pytest.mark.parametrize("name", HARNESS_MUTANTS)\n'
                "def test_pfp_gate_mutant(name):\n    _assert_mutant(name)\n",
                encoding="utf-8",
            )


HARNESS_MUTANTS = (
    "bare_answer",
    "duplicate_json_key",
    "nan",
    "infinite_number",
    "wrong_policy",
    "missing_answer",
    "scalar_answer",
    "missing_summary",
    "empty_thesis",
    "numeric_summary",
    "extra_summary_key",
    "missing_integrity",
    "integer_boolean",
    "string_boolean",
    "wrong_biases_type",
    "numeric_bias",
    "nonempty_sections",
    "extra_envelope_key",
    "fenced_json",
    "trailing_prose",
    "wrong_witness",
    "unwarranted_refusal",
    "checker_exception",
    "checker_disagreement",
    "missing_checker",
)


def main():
    parser = argparse.ArgumentParser(
        description="PFP learning campaign; no implicit live dispatch."
    )
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--host", type=Path, help="new directory for NO_LLM control receipts")
    parser.add_argument(
        "--replay", type=Path, help="re-run and compare an existing control manifest"
    )
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check one selected NO_LLM fixture, without writing a run",
    )
    parser.add_argument(
        "--reply", type=Path, help="With --check, grade a caller-supplied SPK-001 envelope"
    )
    parser.add_argument(
        "--live", metavar="MODEL", help="fresh accounted OpenRouter run with explicit bounds"
    )
    parser.add_argument("--max-output-tokens", type=int)
    parser.add_argument("--max-provider-calls", type=int)
    budget = parser.add_mutually_exclusive_group()
    budget.add_argument("--max-cost-microusd", type=int)
    budget.add_argument("--max-estimated-cost-microusd", type=int)
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--challenge")
    parser.add_argument("--split", choices=("development", "held_out"), default="development")
    parser.add_argument("--ordinal", type=int, default=0)
    parser.add_argument(
        "--arm", choices=("baseline", "typed_witness", "transfer"), default="baseline"
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--replay-live", type=Path)
    parser.add_argument("--transfer-from", type=Path)
    args = parser.parse_args()
    if args.live:
        if args.check or args.build or args.host or args.replay or args.replay_live:
            parser.error("--live cannot be combined with another execution action")
        if not args.challenge or not args.output:
            parser.error("--live requires --challenge and --output")
        if not args.max_output_tokens or args.max_output_tokens < 1:
            parser.error("--live requires positive --max-output-tokens")
        if not args.max_provider_calls or args.max_provider_calls < 1:
            parser.error("--live requires positive --max-provider-calls")
        if args.max_cost_microusd is None and args.max_estimated_cost_microusd is None:
            parser.error("--live requires an explicit hard or estimated cost policy")
    if args.check:
        from omega_engine_pfp.infrastructure.challenge_execution import isolated
        from omega_engine_pfp.infrastructure.challenge_live import choose_case

        if not args.challenge:
            parser.error("--check requires --challenge")
        if args.live or args.host or args.build or args.replay or args.replay_live:
            parser.error("--check cannot be combined with another execution action")
        try:
            row = choose_case(args.challenge, args.split, args.ordinal)
            request = dict(kind="NO_LLM", row=row)
            if args.reply:
                request.update(kind="LLM", raw_reply=args.reply.read_text(encoding="utf-8"))
            result = isolated(request, args.timeout)
        except (ValueError, KeyError, OSError) as exc:
            print(json.dumps(dict(status="REFUSED", reason=str(exc), provider_calls=0)))
            return 2
        print(
            json.dumps(
                dict(
                    row=row,
                    result=result,
                    provider_calls=0,
                    evidence_grade="CALLER_SUPPLIED_UNAUTHENTICATED"
                    if args.reply
                    else "NO_LLM_FIXTURE",
                    authority_effect="None",
                )
            )
        )
        return (
            0 if result["status"] in ("FIXTURE_VERIFIED", "HOST_ACCEPTED", "TYPED_REFUSAL") else 2
        )
    if args.reply:
        parser.error("--reply requires --check")
    if args.build:
        plan = build()
        create_pilots(plan)
        print(
            json.dumps(
                {
                    "pilots": len(plan["families"]),
                    "source_cases": sum(
                        len(c["cases"]) for f in plan["families"] for c in f["challenges"]
                    ),
                }
            )
        )
    if args.host:
        print(json.dumps(run_host(args.host, args.timeout)["totals"]))
    if args.replay:
        print(json.dumps(replay_host(args.replay, args.timeout)["totals"]))
    if args.live:
        from omega_engine_pfp.infrastructure.challenge_live import choose_case, live_run
        from omega_engine_pfp.infrastructure.estimated_gateway import (
            create_accounted_openrouter_gateway,
        )

        try:
            if args.output.exists():
                raise ValueError("RUN_ALREADY_EXISTS")
            accounting = args.output.with_name(args.output.name + ".budget.sqlite3")
            if accounting.exists():
                raise ValueError("ACCOUNTING_ALREADY_EXISTS")
            row = choose_case(args.challenge, args.split, args.ordinal)
            objective = json.dumps(dict(row=row, arm=args.arm), sort_keys=True).encode()
            gateway = create_accounted_openrouter_gateway(
                args.live, args.max_output_tokens, env_file=args.env_file,
                max_cost_microusd=args.max_cost_microusd,
                max_estimated_cost_microusd=args.max_estimated_cost_microusd,
                max_calls=args.max_provider_calls, accounting_path=accounting,
                run_id="challenge-" + uuid4().hex,
                objective_sha256=sha256(objective).hexdigest(),
            )
            records = live_run(
                row, args.output, args.live, args.arm, transfer_from=args.transfer_from,
                gateway=gateway, max_output_tokens=args.max_output_tokens,
                max_provider_calls=args.max_provider_calls,
            )
        except (ValueError, KeyError, OSError) as exc:
            print(json.dumps(dict(status="REFUSED", reason=str(exc))))
            return 2
        status = records[-1]["result"]["status"] if records else "NO_STAGE_RECORDED"
        print(json.dumps(dict(recorded_stages=len(records), status=status,
                             output=str(args.output))))
        return 2 if status in ("NO_STAGE_RECORDED", "INFRASTRUCTURE_ERROR") else 0
    if args.replay_live:
        from omega_engine_pfp.infrastructure.challenge_live import replay_live

        print(json.dumps({"replayed_stages": replay_live(args.replay_live)}))


if __name__ == "__main__":
    raise SystemExit(main())
