"""Arm S of the Fable-versus-swarm comparison: the cheap-first PFP ladder over the frozen cohort.

    python -I -X utf8 dag/pfp/compare/run_swarm_arm.py --dry-run                      # the plan; no network, no key read, nothing written
    python -I -X utf8 dag/pfp/compare/run_swarm_arm.py --dry-run --compile-packets    # also builds each clean room and prints the packet digest (no network)
    python -I -X utf8 dag/pfp/compare/run_swarm_arm.py --max-tier 0                   # free models only, no spend flag needed
    python -I -X utf8 dag/pfp/compare/run_swarm_arm.py --confirm-spend --arm-cap-usd 2.00   # free, cheap OpenRouter and Haiku tiers

What it does for every selected cohort item (protocol.md section 4):
  1. refuses to start unless protocol.md still matches the sha256 pinned in cohort.json;
  2. builds the CLEAN ROOM of the item (git archive of its freeze commit, no dag/results, every Arm F artifact removed);
  3. obtains the packet: compiled from the clean room (strata D and C) or the stored request of the earlier Opus/Fable
     attempt, replayed byte for byte (stratum P); stops if an Arm F marker appears in the packet text;
  4. runs llm_ladder.runner.LadderRunner over the clean room with tiers 0..max-tier only. Opus (tier 4) and Fable (tier 5)
     are never callable: the tier list is cut and the model names are checked;
  5. enforces the money caps of the shared ledger (budget.py), the per-prompt call cap and wall-clock cap, and an arm cap;
  6. copies the run folder to dag/results/<NODE>/runs/<ts>_compare_swarm/ and adds compare_swarm_receipt.json.

The shared hallucination index and the positive operad memory of the repository are NOT used: the clean room starts with an
empty index (cold start) unless --seed-memory names a file, from which entries about cohort nodes are dropped. Runs are named
_compare_swarm so that replay.py and the ladder's positive memory (both glob *_ladder*) never read them.

AuthorityEffect: None. Provider replies are untrusted proposals; only host-verified entries count (and only after score.py).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))  # dag/pfp, so that the package `llm_ladder` imports under `python -I`
sys.dont_write_bytecode = True

from compare_common import (ARM_S_DEFAULT_MAX_TIER, ARM_S_MAX_TIER, DEFAULT_MAX_CALLS, DEFAULT_WALLCLOCK_S, EXPENSIVE_MARKERS, REPO,  # noqa: E402
                            SHORT_ROOT, CompareError, assert_no_leak, build_cleanroom, capped_ledger_class, cleanroom_dir,
                            compare_run_dirs, free_space_gb, json_bytes, load_cohort, make_packet_factory, packet_bytes_sha256,
                            run_ladder_item, seeded_memory, selected_items, write_new)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--cohort', default=None, help='cohort.json (default: next to this script)')
    parser.add_argument('--strata', default='D,P,C', help='comma list of strata to run (default all)')
    parser.add_argument('--only', default=None, help='comma list of node ids')
    parser.add_argument('--stage', default='P0', help='only P0 is wired in the ladder; P1-P5 are refused with the reason')
    parser.add_argument('--max-tier', type=int, default=ARM_S_DEFAULT_MAX_TIER,
                        help='0 free, 1 cheap OpenRouter, 2 Haiku 5.5, 3 Sonnet 5.5; tiers 4 (Opus) and 5 (Fable) are never allowed in Arm S')
    parser.add_argument('--dry-run', action='store_true', help='print the plan; no network, no key read, nothing written (except with --compile-packets: temp clean rooms)')
    parser.add_argument('--compile-packets', action='store_true', help='with --dry-run: build each clean room and compile/load the packet (local only)')
    parser.add_argument('--confirm-spend', action='store_true', help='required for any paid tier (max-tier >= 1)')
    parser.add_argument('--node-cap-usd', type=float, default=0.25, help='cap on PAID calls per prompt (shared ledger run cap)')
    parser.add_argument('--arm-cap-usd', type=float, default=2.00, help='cap on PAID calls across the whole arm')
    parser.add_argument('--max-calls', type=int, default=DEFAULT_MAX_CALLS, help='provider calls per prompt (protocol: equal for both arms)')
    parser.add_argument('--wallclock-s', type=int, default=DEFAULT_WALLCLOCK_S, help='wall-clock per prompt (protocol: equal for both arms)')
    parser.add_argument('--abstain-stop', type=int, default=2, help='stop after N distinct models answered validly with nothing to ground (ladder default off; pre-registered 2)')
    parser.add_argument('--seed-memory', default=None, help='optional hallucination-index JSON to seed the clean rooms (entries about cohort nodes are dropped)')
    parser.add_argument('--allow-rerun', default=None, metavar='REASON', help='permit a second _compare_swarm run for a prompt; the reason is recorded (protocol: only after an all-infrastructure failure)')
    parser.add_argument('--workdir', default=str(SHORT_ROOT), help='short directory for clean rooms (Windows MAX_PATH)')
    parser.add_argument('--keep-cleanroom', action='store_true')
    parser.add_argument('--min-free-gb', type=float, default=3.0)
    parser.add_argument('--ledger', default=str(HERE.parent / 'llm_ladder' / 'budget_ledger.json'))
    parser.add_argument('--anthropic-weekly-cap-usd', type=float, default=150.0)
    parser.add_argument('--paid-other-weekly-cap-usd', type=float, default=10.0)
    parser.add_argument('--env-file', default=None, help='explicit .env path (default: the ladder search order)')
    parser.add_argument('--json', action='store_true', help='print the plan as JSON')
    return parser.parse_args(argv)


# --------------------------------------------------------------------------- guards
def tiers_for_arm_s(max_tier: int, env=None) -> list:
    from llm_ladder.config import load_tiers
    if not 0 <= max_tier <= ARM_S_MAX_TIER:
        raise CompareError('--max-tier %d refused: Arm S may use tiers 0..%d. Opus (4) and Fable (5) are the expensive baseline and are never in the swarm arm.' % (max_tier, ARM_S_MAX_TIER))
    tiers = [t for t in load_tiers(None, env or {}) if t['id'] <= max_tier]
    for tier in tiers:
        for cand in tier['candidates']:
            if any(marker in cand['model'].lower() for marker in EXPENSIVE_MARKERS):
                raise CompareError('model %s is in the expensive set and cannot be in Arm S' % cand['model'])
    return tiers


def stage_guard(stage: str) -> None:
    if stage != 'P0':
        raise CompareError(
            'Only --stage P0 is wired for Arm S. llm_ladder/runner.py raises for any other stage ("P1+ need host-reviewed missions"), and dag/pfp/batch_tools '
            'runs P1-P5 from a host-authored spec without any provider call. The reference system (the_symbol_game/omega_engine_pfp use_cases/pfp_stages.py) '
            'defines a six-stage pipeline behind a native host that this repository does not import. P1-P5 are therefore NOT part of Arm S; protocol.md section 3.1 states what that limits.')


def existing_runs(items: list) -> dict:
    return {i['node_id']: [p.name for p in compare_run_dirs(i['node_id'], 'compare_swarm')] for i in items if compare_run_dirs(i['node_id'], 'compare_swarm')}


# --------------------------------------------------------------------------- plan
def worst_case_per_call(tier: dict, tokens: int) -> float:
    from llm_ladder.budget import cost_microusd, micro_to_usd
    from llm_ladder.config import PRICES
    if tier['family'] == 'free':
        return 0.0
    cand = tier['candidates'][0]
    price = PRICES.get((cand['provider'], cand['model']))
    return micro_to_usd(cost_microusd(tokens, tier['max_tokens'], *price)) if price else float('nan')


def plan_rows(args, items, tiers, tokens_by_node) -> dict:
    rows, worst_total = [], 0.0
    for item in items:
        tokens = tokens_by_node.get(item['node_id'], 12000)
        worst = sum(t['attempts_before_escalation'] * worst_case_per_call(t, tokens) for t in tiers if t['family'] != 'free')
        worst = min(worst, args.node_cap_usd)
        worst_total += worst
        rows.append({'stratum': item['stratum'], 'node_id': item['node_id'], 'packet_source': item['arm_s']['packet_source'],
                     'freeze_commit': item['arm_s']['freeze_commit'][:12], 'freeze_commit_date': item['arm_s']['freeze_commit_date'],
                     'exclude_paths': len(item['arm_s']['exclude_paths']), 'leak_markers': len(item['arm_s']['leak_markers']),
                     'estimated_input_tokens': tokens, 'estimate_is_exact_packet': item['node_id'] in tokens_by_node,
                     'worst_case_paid_usd': round(worst, 4)})
    return {'rows': rows, 'worst_case_total_usd': round(min(worst_total, args.arm_cap_usd), 4)}


def tier_rows(tiers, tokens) -> list:
    out = []
    for tier in tiers:
        for cand in tier['candidates']:
            out.append({'tier': tier['id'], 'name': tier['name'], 'family': tier['family'], 'provider': cand['provider'], 'model': cand['model'],
                        'enabled': cand.get('enabled', True), 'attempts_before_escalation': tier['attempts_before_escalation'],
                        'max_tokens': tier['max_tokens'], 'worst_case_usd_per_call': round(worst_case_per_call(tier, tokens), 5)})
    return out


def print_plan(args, items, tiers, plan, packets) -> None:
    print('=== Arm S plan (stage P0, ladder tiers 0..%d, claude-opus-5-5 and claude-fable-5-1 excluded) ===' % args.max_tier)
    print('protocol sha256 verified against cohort.json; cohort base commit %s' % args.cohort_base[:12])
    print('network: none in --dry-run. Keys: not read in --dry-run. Ledger: %s (read at run time only)' % Path(args.ledger).as_posix())
    print('caps per prompt: %d provider calls, %d s wall-clock, USD %.2f paid; arm cap USD %.2f; abstain-stop %d' % (
        args.max_calls, args.wallclock_s, args.node_cap_usd, args.arm_cap_usd, args.abstain_stop))
    print('memory: cold start (empty hallucination index, no positive entries)%s' % (' + seeded from ' + args.seed_memory if args.seed_memory else ''))
    print()
    print('%-2s %-40s %-24s %-12s %5s %5s %8s %9s' % ('S', 'node', 'packet', 'freeze', 'excl', 'mark', 'tokens', 'worst$'))
    for row in plan['rows']:
        print('%-2s %-40s %-24s %-12s %5d %5d %8d %9.4f%s' % (row['stratum'], row['node_id'], row['packet_source'], row['freeze_commit'], row['exclude_paths'],
                                                            row['leak_markers'], row['estimated_input_tokens'], row['worst_case_paid_usd'],
                                                            '' if row['estimate_is_exact_packet'] else '  (assumed tokens)'))
    print()
    print('%-4s %-7s %-11s %-34s %-8s %4s %7s %10s' % ('tier', 'name', 'provider', 'model', 'enabled', 'att', 'max_tok', 'worst$/call'))
    for row in tier_rows(tiers, max(plan_tokens(plan), 1)):
        print('%-4d %-7s %-11s %-34s %-8s %4d %7d %10.5f' % (row['tier'], row['name'], row['provider'], row['model'], row['enabled'],
                                                           row['attempts_before_escalation'], row['max_tokens'], row['worst_case_usd_per_call']))
    print()
    print('worst case if every paid tier used all its attempts on every prompt, capped per prompt and per arm: USD %.4f' % plan['worst_case_total_usd'])
    paid = args.max_tier >= 1
    print('paid tiers selected: %s%s' % ('yes' if paid else 'no (free models only)', '; --confirm-spend is REQUIRED to run' if paid else ''))
    for node, lines in packets.items():
        print('packet %-36s %s' % (node, lines))


def plan_tokens(plan) -> int:
    values = [r['estimated_input_tokens'] for r in plan['rows']]
    return max(values) if values else 12000


# --------------------------------------------------------------------------- one item
def run_item(args, item, *, cohort, providers, redactor, arm_spent_micro, workdir) -> dict:
    return run_ladder_item(args, item, arm='S', suffix='compare_swarm', cohort=cohort, providers=providers, redactor=redactor,
                           tiers=tiers_for_arm_s(args.max_tier), start_tier=0, max_tier=args.max_tier, allow_fable=False,
                           arm_spent_micro=arm_spent_micro, workdir=workdir)


# --------------------------------------------------------------------------- main
def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        stage_guard(args.stage)
        tiers_for_arm_s(args.max_tier)
        cohort = load_cohort(args.cohort) if args.cohort else load_cohort()
        args.cohort_base = cohort['built_from']['base_commit']
        strata = tuple(s.strip() for s in args.strata.split(',') if s.strip())
        items = selected_items(cohort, strata, args.only.split(',') if args.only else None)
        if not items:
            raise CompareError('no cohort item selected')
        prior = existing_runs(items)
        if prior and not args.allow_rerun and not args.dry_run:
            raise CompareError('already run (protocol: one Arm S run per prompt): %s. A rerun needs --allow-rerun "reason" and is allowed only after an all-infrastructure failure.' % json.dumps(prior))
        if args.max_tier >= 1 and not args.dry_run and not args.confirm_spend:
            raise CompareError('tiers 1..%d are PAID (OpenRouter paid model%s). Re-run with --confirm-spend, or use --max-tier 0 for the free models only.' % (
                args.max_tier, ', Haiku 5.5' if args.max_tier >= 2 else ''))
        workdir = Path(args.workdir)
        if free_space_gb(workdir) < args.min_free_gb:
            raise CompareError('only %.1f GB free where %s lives (need %.1f); free disk or pass --workdir' % (free_space_gb(workdir), workdir, args.min_free_gb))
        tiers = tiers_for_arm_s(args.max_tier)
        if args.dry_run:
            tokens_by_node, packet_lines = {}, {}
            if args.compile_packets:
                from llm_ladder.config import DEFAULT_POLICY
                from llm_ladder.memory import HallucinationIndex, index_path
                from llm_ladder.verify import DeclIndex
                for item in items:
                    root = cleanroom_dir(item, 'dry', workdir)
                    if root.exists():
                        shutil.rmtree(root, ignore_errors=True)
                    manifest = build_cleanroom(item['arm_s']['freeze_commit'], root, exclude=tuple(item['arm_s']['exclude_paths']))
                    seeded_memory(root, None, set())
                    index = DeclIndex(root)
                    packet, _ = make_packet_factory(item, root, dict(DEFAULT_POLICY), index, HallucinationIndex(index_path(root)))
                    assert_no_leak(packet, item['arm_s']['leak_markers'])
                    tokens_by_node[item['node_id']] = packet.estimated_tokens()
                    packet_lines[item['node_id']] = 'bytes_sha256=%s tokens~%d src=%s clean_room_files=%d dropped=%d skipped_long=%d manifest=%s' % (
                        packet_bytes_sha256(packet.system, packet.user, packet.schema)[:16], packet.estimated_tokens(), packet.meta.get('src_offered'),
                        manifest['files'], len(manifest['dropped_arm_f_paths']), manifest['skipped_long_paths'], manifest['manifest_sha256'][:12])
                    shutil.rmtree(root, ignore_errors=True)
            plan = plan_rows(args, items, tiers, tokens_by_node)
            if args.json:
                print(json.dumps({'plan': plan, 'tiers': tier_rows(tiers, plan_tokens(plan)), 'packets': packet_lines, 'caps': {
                    'max_calls': args.max_calls, 'wallclock_s': args.wallclock_s, 'node_cap_usd': args.node_cap_usd, 'arm_cap_usd': args.arm_cap_usd}}, indent=2))
            else:
                print_plan(args, items, tiers, plan, packet_lines)
                if prior:
                    print('\nNOTE: _compare_swarm runs already exist for %s' % json.dumps(prior))
            return 0
        # ---- live run
        from llm_ladder.llm_common import SECRET_NAMES, Redactor, load_env
        from llm_ladder.providers import build_providers
        env = load_env(env_file=args.env_file, root=REPO)
        redactor = Redactor(env.get(name) for name in SECRET_NAMES)
        providers = build_providers(env)
        tiers_for_arm_s(args.max_tier, env)
        results, arm_spent = [], 0
        for item in items:
            outcome = run_item(args, item, cohort=cohort, providers=providers, redactor=redactor, arm_spent_micro=arm_spent, workdir=workdir)
            arm_spent += outcome['spend_microusd']
            results.append(outcome)
            print('%-2s %-40s %-18s calls=%d spend=USD %.4f %5.0fs  %s' % (outcome['stratum'], outcome['node_id'], outcome['status'], outcome['calls'],
                                                                         outcome['spend_usd'], outcome['seconds'], outcome['stop_reason']), flush=True)
        stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
        summary_path = HERE / 'receipts' / ('swarm_arm_%s.json' % stamp)
        write_new(summary_path, json_bytes(redactor.redact_obj({'schema_id': 'omega.pfp.compare.swarm-arm-summary.v1', 'authority_effect': 'None',
                                                                 'protocol_sha256': cohort['protocol']['sha256'], 'max_tier': args.max_tier,
                                                                 'arm_spend_usd': arm_spent / 1e6, 'results': results})))
        print('arm spend USD %.4f; summary %s' % (arm_spent / 1e6, summary_path.relative_to(REPO).as_posix()))
        return 0
    except CompareError as error:
        print('REFUSED: %s' % error, file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
