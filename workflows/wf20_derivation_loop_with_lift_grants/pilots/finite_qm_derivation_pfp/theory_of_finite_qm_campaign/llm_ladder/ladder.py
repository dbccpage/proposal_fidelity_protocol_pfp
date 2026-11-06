"""CLI of the PFP LLM ladder.

    python -I -X utf8 dag/pfp/llm_ladder/ladder.py --node TFQ-0028 --stage P0 --max-cost-usd 0.50 [--dry-run]

--dry-run compiles the packet and prints it with the planned tiers and the cost estimate; it makes no
provider call (not even count_tokens) and writes nothing. Without it the ladder runs: free models first,
escalating only when an attempt was sent and the host rejected it N times (see runner.py), under the hard
budget guard (budget.py). Keys are read at run time from the environment or the .env of this checkout /
the main checkout; they are never printed, logged, written or copied.

AuthorityEffect: None.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # dag/pfp, so that the package `llm_ladder` imports under `python -I`
sys.dont_write_bytecode = True

from llm_ladder.budget import Ledger, usd_to_micro  # noqa: E402
from llm_ladder.config import DEFAULT_POLICY, load_tiers  # noqa: E402
from llm_ladder.llm_common import ROOT, SECRET_NAMES, Redactor, load_env  # noqa: E402
from llm_ladder.providers import build_providers  # noqa: E402
from llm_ladder.runner import LadderRunner  # noqa: E402
from llm_ladder.verify import DeclIndex, default_cache_path  # noqa: E402


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--node', required=True, help='DAG node id, e.g. TFQ-0028')
    parser.add_argument('--stage', default='P0', help='only P0 is wired')
    parser.add_argument('--max-cost-usd', type=float, required=True, help='run-level cap on all PAID calls (Anthropic and paid OpenRouter)')
    parser.add_argument('--dry-run', action='store_true', help='print the packet, tiers and estimate; call nothing, write nothing')
    parser.add_argument('--no-feedback', action='store_true', help='control arm: do not inject negative/positive operad entries')
    parser.add_argument('--start-tier', type=int, default=0)
    parser.add_argument('--max-tier', type=int, default=4, help='highest tier allowed (5 = Fable needs --allow-fable)')
    parser.add_argument('--allow-fable', action='store_true', help='permit tier 5 (claude-fable-5-1), the final hard step only')
    parser.add_argument('--effort', default=None, choices=['low', 'medium', 'high', 'xhigh', 'max'], help='override the per-tier Anthropic effort')
    parser.add_argument('--ledger', default=str(HERE / 'budget_ledger.json'))
    parser.add_argument('--anthropic-weekly-cap-usd', type=float, default=150.0)
    parser.add_argument('--paid-other-weekly-cap-usd', type=float, default=10.0)
    parser.add_argument('--tiers-config', default=None, help='JSON file replacing the default tiers')
    parser.add_argument('--min-verified', type=int, default=None)
    parser.add_argument('--max-failure-rate', type=float, default=None)
    parser.add_argument('--measure-attempts', type=int, default=None, help='measurement mode: exactly N answered attempts at --start-tier, no acceptance stop, no escalation')
    parser.add_argument('--abstain-stop', type=int, default=None, help='stop (no escalation) after N distinct models answered validly with nothing to ground (default off)')
    parser.add_argument('--no-partial', action='store_true', help='turn off accepted_partial (1 verified claim, 0 refused): such answers go back to being rejected/abstained')
    parser.add_argument('--partial-min-verified', type=int, default=None, help='verified claims needed for accepted_partial (default 1)')
    parser.add_argument('--no-skip-ungroundable', action='store_true', help='send every node, including those with no @SRC, no candidates and no code anchor in the checkout')
    parser.add_argument('--partial-terminal', action='store_true', help='end the run at the first accepted_partial instead of escalating (old behaviour)')
    parser.add_argument('--numeric-counts', action='store_true', help='credit correct numeric claims toward acceptance (off by default: they prove arithmetic, not relevance)')
    parser.add_argument('--no-lean', action='store_true', help='skip Lean elaboration of skeletons')
    parser.add_argument('--env-file', default=None, help='explicit .env path (default: this checkout, then the main checkout)')
    parser.add_argument('--root', default=str(ROOT))
    parser.add_argument('--json', action='store_true', help='print the dry-run plan / run summary as JSON only')
    return parser.parse_args(argv)


def build_runner(args, *, providers=None):
    env = load_env(env_file=args.env_file, root=Path(args.root))
    redactor = Redactor(env.get(name) for name in SECRET_NAMES)
    ledger = Ledger(args.ledger, caps={'anthropic_weekly_usd': args.anthropic_weekly_cap_usd,
                                       'paid_other_weekly_usd': args.paid_other_weekly_cap_usd})
    policy = dict(DEFAULT_POLICY)
    if args.min_verified is not None:
        policy['min_verified'] = args.min_verified
    if args.abstain_stop is not None:
        policy['abstain_stop'] = args.abstain_stop
    if args.no_partial:
        policy['accept_partial'] = False
    if args.partial_min_verified is not None:
        policy['partial_min_verified'] = args.partial_min_verified
    if args.no_skip_ungroundable:
        policy['skip_ungroundable'] = False
    if args.numeric_counts:
        policy['numeric_counts'] = True
    if args.partial_terminal:
        policy['partial_escalates'] = False
    if args.max_failure_rate is not None:
        policy['max_failure_rate'] = args.max_failure_rate
    providers = providers if providers is not None else build_providers(env)
    runner = LadderRunner(args.root, ledger=ledger, providers=providers, tiers=load_tiers(args.tiers_config, env), policy=policy,
                          redactor=redactor, decl_index=DeclIndex(args.root, cache_path=default_cache_path(args.root)))
    if args.no_lean:
        runner.verifier.run_lean = False
    return runner


def print_plan(plan: dict) -> None:
    packet = plan.pop('packet')
    print('=== compiled packet (%s, attempt %s, input_sha256 %s) ===' % (packet.node_id, packet.attempt_id, packet.input_sha256[:12]))
    print('--- system ---')
    print(packet.system)
    print('--- user ---')
    print(packet.user)
    print('--- response schema: %d top-level slots, %d bytes ---' % (len(packet.schema['properties']), len(json.dumps(packet.schema))))
    print('=== plan ===')
    print('estimated input tokens (system+user+schema): %d' % plan['estimated_input_tokens'])
    if plan.get('would_skip_ungroundable'):
        print('WOULD BE SKIPPED (skipped_ungroundable, no provider call): %s' % plan['ungroundable_reason'])
    baseline = plan['staged_prompt_tokens_baseline']
    if baseline:
        print('staged prompt packet (prepare_stage.py) for the same node: ~%d tokens  ->  %.1f%% of it' % (
            baseline, 100.0 * plan['estimated_input_tokens'] / baseline))
    for row in plan['tiers']:
        print('tier %d %-6s %-10s %-34s configured=%-5s effort=%-6s max_tokens=%-5d attempts<=%d worst/call=$%.4f' % (
            row['tier'], row['name'], row['provider'], row['model'], row['configured'], row['effort'], row['max_tokens'],
            row['attempts_before_escalation'], row['worst_case_usd_per_call']))
    print('worst case if every paid tier used all its attempts: $%.4f; run cap: $%.4f' % (
        plan['worst_case_all_paid_tiers_usd'], plan['run_cap_usd']))
    week = plan['week']
    print('week %s: anthropic $%.4f of $%.2f, paid-other $%.4f of $%.2f' % (
        week['week'], week['anthropic_microusd'] / 1e6, week['anthropic_cap_microusd'] / 1e6,
        week['paid_other_microusd'] / 1e6, week['paid_other_cap_microusd'] / 1e6))
    print(plan['note'])


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.stage != 'P0':
        print('Only --stage P0 is wired. P1+ need host-reviewed missions (dag/pfp/prepare_stage.py).', file=sys.stderr)
        return 2
    runner = build_runner(args)
    cap = usd_to_micro(args.max_cost_usd)
    if args.dry_run:
        plan = runner.plan(args.node, stage=args.stage, start_tier=args.start_tier, max_tier=args.max_tier, run_cap_microusd=cap,
                           feedback=not args.no_feedback, allow_fable=args.allow_fable, effort_override=args.effort)
        if args.json:
            packet = plan.pop('packet')
            plan['packet'] = packet.as_request_json()
            print(json.dumps(plan, indent=2, ensure_ascii=False))
        else:
            print_plan(plan)
        return 0
    summary = runner.run(args.node, stage=args.stage, run_cap_microusd=cap, start_tier=args.start_tier, max_tier=args.max_tier,
                         feedback=not args.no_feedback, allow_fable=args.allow_fable, effort_override=args.effort,
                         fixed_attempts=args.measure_attempts)
    summary = runner.red.redact_obj(summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    # 0 accepted; 3 accepted_partial; 4 skipped_ungroundable; 1 anything else. accepted_partial is never reported as accepted.
    return {'accepted': 0, 'accepted_partial': 3, 'skipped_ungroundable': 4}.get(summary['status'], 1)


if __name__ == '__main__':
    raise SystemExit(main())
