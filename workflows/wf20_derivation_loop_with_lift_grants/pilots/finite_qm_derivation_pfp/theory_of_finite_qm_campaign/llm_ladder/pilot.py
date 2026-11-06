"""Pilot harness: does operad feedback lower the failure rate, and what does each tier cost?

    python -I -X utf8 dag/pfp/llm_ladder/pilot.py --nodes TFQ-0028,TFQ-0022,TFQ-0031 --k 4 --claude-cap-usd 3.5

For every node the harness runs, in this order:
  A  control arm   K answered attempts on the free tier, no feedback injected (measurement mode);
  B  guided arm    the same K models in the same order, with the negative and positive operad entries
                   that arm A produced injected into the packet;
  C  full ladder   the real policy (free first, escalate after N host failures), guided, from tier 0;
  D  calibration   (--calibrate-node only) one guided call at each Claude tier on the same packet, to show
                   what a tier adds over the free models. Spend is bounded by --claude-cap-usd.
Arms A and B are paired by model and by position, so the comparison is within model. With K this small the
result is descriptive; the harness reports it that way (no significance claim).

AuthorityEffect: None. Every call is metered by the same budget guard as the CLI.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.dont_write_bytecode = True

from llm_ladder.budget import Ledger, micro_to_usd, usd_to_micro  # noqa: E402
from llm_ladder.config import DEFAULT_POLICY, load_tiers  # noqa: E402
from llm_ladder.llm_common import ROOT, SECRET_NAMES, Redactor, load_env, utc_stamp, write_new, json_bytes  # noqa: E402
from llm_ladder.providers import build_providers  # noqa: E402
from llm_ladder.runner import LadderRunner  # noqa: E402
from llm_ladder.verify import DeclIndex, default_cache_path  # noqa: E402


def arm_stats(summary: dict) -> dict:
    rows = [a for a in summary['attempts'] if a.get('status') in ('accepted', 'accepted_partial', 'rejected')]
    failures = sum(a['failures_total'] for a in rows)
    verified = sum(a['verified_total'] for a in rows)
    injected = {i for a in rows for i in a.get('injected_neg_ids', [])}
    repeats = sum(1 for a in rows for i in a.get('negative_entries', []) if i in injected)
    return {'attempts': len(rows), 'models': [a['model'] for a in rows], 'verified_total': verified, 'failures_total': failures,
            'failure_rate': round(failures / (failures + verified), 4) if failures + verified else None,
            'per_attempt_verified': [a['verified_total'] for a in rows], 'per_attempt_failures': [a['failures_total'] for a in rows],
            'would_accept': sum(1 for a in rows if a['verified_total'] >= DEFAULT_POLICY['min_verified']
                                and a['failure_rate'] <= DEFAULT_POLICY['max_failure_rate']),
            'accepted_partial_attempts': sum(1 for a in rows if a['status'] == 'accepted_partial'),
            'failures_by_class': summary['hallucinations_by_class'], 'known_neg_injected': [a['known_neg_injected'] for a in rows],
            'known_pos_injected': [a['known_pos_injected'] for a in rows], 'repeated_known_bad_moves': repeats,
            'infra_errors': [a.get('code') for a in summary['attempts'] if a.get('status') == 'infra_error'],
            'tokens_in': sum(a.get('input_tokens') or 0 for a in rows), 'tokens_out': sum(a.get('output_tokens') or 0 for a in rows),
            'usd': summary['spend_usd'], 'run_dir': summary.get('run_dir')}


def ladder_stats(summary: dict) -> dict:
    tiers = {}
    for tier, row in summary['totals_by_tier'].items():
        tiers[tier] = {'calls': row['calls'], 'answered': row['sent'], 'in': row['input_tokens'], 'out': row['output_tokens'],
                       'usd': round(micro_to_usd(row['cost_microusd']), 6), 'errors': row['errors']}
    best = next((a for a in summary['attempts'] if a['attempt_id'] == summary['best_attempt']), None)
    return {'status': summary['status'], 'stop_reason': summary['stop_reason'], 'by_tier': tiers, 'usd': summary['spend_usd'],
            'best_attempt': summary['best_attempt'], 'best_model': best['model'] if best else None,
            'verified_in_best': summary.get('verified'), 'hallucinations_by_class': summary['hallucinations_by_class'],
            'attempt_log': [{k: a.get(k) for k in ('attempt_id', 'tier', 'model', 'status', 'code', 'verified_total', 'failures_total',
                                                   'failures_by_class', 'known_neg_injected', 'cost_microusd')} for a in summary['attempts']],
            'run_dir': summary.get('run_dir')}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--nodes', required=True)
    parser.add_argument('--k', type=int, default=4)
    parser.add_argument('--claude-cap-usd', type=float, default=3.5, help='cap on ALL paid spend of this pilot (full ladder runs and calibration together)')
    parser.add_argument('--calibrate-node', default=None)
    parser.add_argument('--calibrate-tiers', default='2,3,4,5')
    parser.add_argument('--ledger', default=str(HERE / 'budget_ledger.json'))
    parser.add_argument('--out-dir', default=str(HERE / 'pilot'))
    parser.add_argument('--skip', default='', help='comma list of arm letters to skip, e.g. A,B')
    parser.add_argument('--max-tier', type=int, default=4)
    parser.add_argument('--abstain-stop', type=int, default=0)
    parser.add_argument('--label', default='')
    args = parser.parse_args(argv)
    env = load_env(root=ROOT)
    red = Redactor(env.get(n) for n in SECRET_NAMES)
    ledger = Ledger(args.ledger)
    runner = LadderRunner(ROOT, ledger=ledger, providers=build_providers(env), tiers=load_tiers(env=env), policy=dict(DEFAULT_POLICY, abstain_stop=args.abstain_stop), redactor=red,
                          decl_index=DeclIndex(ROOT, cache_path=default_cache_path(ROOT)))
    total_cap = usd_to_micro(args.claude_cap_usd)
    skip = {s for s in args.skip.split(',') if s}
    report = {'schema_id': 'omega.pfp.llm-ladder.pilot.v1', 'authority_effect': 'None', 'started_utc': utc_stamp(), 'label': args.label, 'abstain_stop': args.abstain_stop, 'k': args.k, 'nodes': {}}
    before = ledger.week_totals()

    def remaining() -> int:
        """What is left of the pilot's own cap: every later run is capped by it, so the pilot cannot overspend."""
        now = ledger.week_totals()
        spent = (now['anthropic_microusd'] - before['anthropic_microusd']) + (now['paid_other_microusd'] - before['paid_other_microusd'])
        return max(0, total_cap - spent)
    for node in args.nodes.split(','):
        entry = report['nodes'].setdefault(node, {})
        if 'A' not in skip:
            entry['A_control'] = arm_stats(runner.run(node, run_cap_microusd=0, feedback=False, max_tier=0, fixed_attempts=args.k))
            print(node, 'A', json.dumps({k: entry['A_control'][k] for k in ('verified_total', 'failures_total', 'failure_rate', 'per_attempt_verified')}), flush=True)
        if 'B' not in skip:
            entry['B_guided'] = arm_stats(runner.run(node, run_cap_microusd=0, feedback=True, max_tier=0, fixed_attempts=args.k))
            print(node, 'B', json.dumps({k: entry['B_guided'][k] for k in ('verified_total', 'failures_total', 'failure_rate', 'per_attempt_verified', 'known_neg_injected', 'repeated_known_bad_moves')}), flush=True)
        if 'C' not in skip:
            entry['C_ladder'] = ladder_stats(runner.run(node, run_cap_microusd=remaining(), feedback=True, max_tier=args.max_tier))
            print(node, 'C', entry['C_ladder']['status'], entry['C_ladder']['stop_reason'], entry['C_ladder']['usd'], flush=True)
    if args.calibrate_node and 'D' not in skip:
        calib = report.setdefault('calibration', {'node': args.calibrate_node, 'tiers': {}})
        for tier in (int(t) for t in args.calibrate_tiers.split(',')):
            summary = runner.run(args.calibrate_node, run_cap_microusd=remaining(), feedback=True, start_tier=tier, max_tier=tier,
                                 allow_fable=(tier == 5), fixed_attempts=1)
            calib['tiers'][str(tier)] = arm_stats(summary) | {'status': summary['status'], 'stop_reason': summary['stop_reason']}
            print('calibration tier', tier, calib['tiers'][str(tier)]['verified_total'], calib['tiers'][str(tier)]['failures_total'], calib['tiers'][str(tier)]['usd'], flush=True)
    after = ledger.week_totals()
    report['anthropic_usd_this_pilot'] = round(micro_to_usd(after['anthropic_microusd'] - before['anthropic_microusd']), 6)
    report['paid_other_usd_this_pilot'] = round(micro_to_usd(after['paid_other_microusd'] - before['paid_other_microusd']), 6)
    report['week_after'] = {k: v for k, v in after.items()}
    out = Path(args.out_dir) / ('pilot_%s.json' % utc_stamp())
    write_new(out, json_bytes(red.redact_obj(report)))
    print('wrote', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
