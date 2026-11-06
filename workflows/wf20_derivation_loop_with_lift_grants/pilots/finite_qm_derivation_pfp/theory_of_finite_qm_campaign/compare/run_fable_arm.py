"""OPTIONAL fresh-Fable re-run of Arm F. THIS COSTS MONEY (claude-fable-5-1 is the dearest model on the price table).

    python -I -X utf8 dag/pfp/compare/run_fable_arm.py                                 # dry run (the default): plan and worst-case cost, nothing sent
    python -I -X utf8 dag/pfp/compare/run_fable_arm.py --compile-packets              # dry run with exact packet sizes (builds clean rooms, local only)
    python -I -X utf8 dag/pfp/compare/run_fable_arm.py --confirm-spend --usd-cap 8    # spends up to USD 8 of Anthropic budget

Why it exists. Arm F "reuse" (cohort.json) is an outcome comparison: the agentic Fable sessions had tools, many turns and human
steering, and their instructions are not in the repository, so their input is not byte-identical to what the swarm receives.
This script gives Fable exactly the swarm's input: the same clean room, the same compiled packet (byte-identical first packet,
checked by packet_bytes_sha256), the same response schema, the same verifier, the same per-prompt call cap and wall-clock cap,
no tools. It is the paired, like-for-like measurement at stage P0 and it is the only Arm F mode whose cost is fully recorded.

Safeguards, all pre-dispatch: it refuses without --confirm-spend AND an explicit positive --usd-cap; the shared ledger's
weekly Anthropic cap still applies (budget.py); each call's worst case is reserved before it is sent; the per-prompt cap is
min(--node-cap-usd, what is left of --usd-cap); max_retries is 0; there is no model substitution.
Defaults give Fable the ladder's own tier-5 settings (max_tokens 8000, effort medium at P0), which are more generous than any
swarm tier; --effort/--max-tokens deviations are recorded in the receipt and are labelled SENSITIVITY, not primary.

AuthorityEffect: None.
"""
from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))  # dag/pfp, so that the package `llm_ladder` imports under `python -I`
sys.dont_write_bytecode = True

from compare_common import (DEFAULT_MAX_CALLS, DEFAULT_WALLCLOCK_S, REPO, SHORT_ROOT, CompareError, assert_no_leak, build_cleanroom,  # noqa: E402
                            cleanroom_dir, compare_run_dirs, free_space_gb, json_bytes, load_cohort, make_packet_factory,
                            packet_bytes_sha256, run_ladder_item, seeded_memory, selected_items, write_new)

FABLE_MODEL = 'claude-fable-5-1'


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--cohort', default=None)
    parser.add_argument('--strata', default='D', help='D (default: derivation prompts) or D,P; C has no Arm F and is refused')
    parser.add_argument('--only', default=None)
    parser.add_argument('--dry-run', action='store_true', help='the default; stated for clarity')
    parser.add_argument('--compile-packets', action='store_true')
    parser.add_argument('--confirm-spend', action='store_true', help='REQUIRED to dispatch; together with --usd-cap')
    parser.add_argument('--usd-cap', type=float, default=None, help='explicit cap on the whole fresh-Fable arm, USD (required to dispatch)')
    parser.add_argument('--node-cap-usd', type=float, default=1.50, help='cap per prompt (further limited by what is left of --usd-cap)')
    parser.add_argument('--max-attempts', type=int, default=3, help='answered attempts per prompt before stopping (the first answer that passes the ladder policy ends it)')
    parser.add_argument('--max-calls', type=int, default=None, help='provider calls per prompt; default = --max-attempts (protocol ceiling %d)' % DEFAULT_MAX_CALLS)
    parser.add_argument('--wallclock-s', type=int, default=DEFAULT_WALLCLOCK_S)
    parser.add_argument('--effort', default=None, choices=['low', 'medium', 'high', 'xhigh', 'max'], help='SENSITIVITY: override the ladder P0 effort for Fable (medium)')
    parser.add_argument('--max-tokens', type=int, default=None, help='SENSITIVITY: override the tier-5 max_tokens (8000)')
    parser.add_argument('--abstain-stop', type=int, default=0)
    parser.add_argument('--seed-memory', default=None)
    parser.add_argument('--allow-rerun', default=None, metavar='REASON')
    parser.add_argument('--workdir', default=str(SHORT_ROOT))
    parser.add_argument('--keep-cleanroom', action='store_true')
    parser.add_argument('--min-free-gb', type=float, default=3.0)
    parser.add_argument('--ledger', default=str(HERE.parent / 'llm_ladder' / 'budget_ledger.json'))
    parser.add_argument('--anthropic-weekly-cap-usd', type=float, default=150.0)
    parser.add_argument('--paid-other-weekly-cap-usd', type=float, default=10.0)
    parser.add_argument('--env-file', default=None)
    return parser.parse_args(argv)


def fable_tier(args) -> dict:
    from llm_ladder.config import DEFAULT_TIERS
    tier = copy.deepcopy(next(t for t in DEFAULT_TIERS if t['id'] == 5))
    tier['attempts_before_escalation'] = args.max_attempts
    tier['max_infra_failures'] = 1
    if args.max_tokens:
        tier['max_tokens'] = args.max_tokens
    if [c['model'] for c in tier['candidates']] != [FABLE_MODEL]:
        raise CompareError('tier 5 of the ladder no longer names exactly %s; refusing to guess' % FABLE_MODEL)
    return tier


def worst_case_usd(tier: dict, tokens: int, attempts: int) -> float:
    from llm_ladder.budget import cost_microusd, micro_to_usd
    from llm_ladder.config import PRICES
    price = PRICES[('anthropic', FABLE_MODEL)]
    return micro_to_usd(attempts * cost_microusd(tokens, tier['max_tokens'], *price))


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        if args.confirm_spend and (args.usd_cap is None or args.usd_cap <= 0):
            raise CompareError('--confirm-spend needs an explicit positive --usd-cap (USD for the whole fresh-Fable arm).')
        execute = args.confirm_spend and not args.dry_run
        strata = tuple(s.strip() for s in args.strata.split(',') if s.strip())
        if 'C' in strata:
            raise CompareError('stratum C has no Arm F baseline; a fresh Fable run on controls would be spend with nothing to compare against.')
        cohort = load_cohort(args.cohort) if args.cohort else load_cohort()
        items = selected_items(cohort, strata, args.only.split(',') if args.only else None, arm_f_only=True)
        if not items:
            raise CompareError('no cohort item selected')
        if 'P' in strata:
            print('NOTE: stratum P already has recorded Opus/Fable attempts on these packets; re-running Fable there duplicates recorded spend.')
        args.max_calls = args.max_calls or args.max_attempts
        if args.max_calls > DEFAULT_MAX_CALLS:
            raise CompareError('--max-calls above the protocol ceiling of %d provider calls per prompt' % DEFAULT_MAX_CALLS)
        prior = {i['node_id']: [p.name for p in compare_run_dirs(i['node_id'], 'compare_fable')] for i in items if compare_run_dirs(i['node_id'], 'compare_fable')}
        if prior and execute and not args.allow_rerun:
            raise CompareError('already run (one fresh-Fable run per prompt): %s. A rerun needs --allow-rerun "reason".' % json.dumps(prior))
        workdir = Path(args.workdir)
        if free_space_gb(workdir) < args.min_free_gb:
            raise CompareError('only %.1f GB free where %s lives (need %.1f)' % (free_space_gb(workdir), workdir, args.min_free_gb))
        tier = fable_tier(args)
        tokens_by_node, packet_lines = {}, {}
        if args.compile_packets and not execute:  # exact sizes; a live run compiles each packet inside run_ladder_item
            from llm_ladder.config import DEFAULT_POLICY
            from llm_ladder.memory import HallucinationIndex, index_path
            from llm_ladder.verify import DeclIndex
            for item in items:
                root = cleanroom_dir(item, 'dryf', workdir)
                if root.exists():
                    shutil.rmtree(root, ignore_errors=True)
                manifest = build_cleanroom(item['arm_s']['freeze_commit'], root, exclude=tuple(item['arm_s']['exclude_paths']))
                seeded_memory(root, None, set())
                packet, _ = make_packet_factory(item, root, dict(DEFAULT_POLICY), DeclIndex(root), HallucinationIndex(index_path(root)))
                assert_no_leak(packet, item['arm_s']['leak_markers'])
                tokens_by_node[item['node_id']] = packet.estimated_tokens()
                packet_lines[item['node_id']] = 'bytes_sha256=%s tokens~%d clean_room_files=%d' % (packet_bytes_sha256(packet.system, packet.user, packet.schema)[:16],
                                                                                                    packet.estimated_tokens(), manifest['files'])
                shutil.rmtree(root, ignore_errors=True)
        rows, total = [], 0.0
        for item in items:
            tokens = tokens_by_node.get(item['node_id'], 12000)
            worst = min(worst_case_usd(tier, tokens, args.max_attempts), args.node_cap_usd)
            total += worst
            rows.append((item['stratum'], item['node_id'], tokens, worst, item['node_id'] in tokens_by_node))
        total_capped = min(total, args.usd_cap) if args.usd_cap else total
        print('=== Fresh Fable arm (OPTIONAL, COSTS MONEY) ===')
        print('model %s, effort %s, max_tokens %d, answered attempts per prompt <= %d, provider calls per prompt <= %d, wall-clock %d s' % (
            FABLE_MODEL, args.effort or 'ladder P0 default (medium)', tier['max_tokens'], args.max_attempts, args.max_calls, args.wallclock_s))
        if args.effort or args.max_tokens:
            print('DEVIATION from the pre-registered defaults is recorded as SENSITIVITY, not primary.')
        print('tools: none (single-shot structured reply, as for the swarm). Ledger: %s (weekly Anthropic cap USD %.2f applies)' % (
            Path(args.ledger).as_posix(), args.anthropic_weekly_cap_usd))
        print('%-2s %-40s %8s %12s' % ('S', 'node', 'tokens', 'worst-case$'))
        for stratum, node, tokens, worst, exact in rows:
            print('%-2s %-40s %8d %12.4f%s' % (stratum, node, tokens, worst, '' if exact else '  (assumed tokens)'))
        for node, line in packet_lines.items():
            print('packet %-36s %s' % (node, line))
        print('worst case over the arm (every attempt at its token cap on every prompt): USD %.2f%s' % (
            total_capped, ' (capped by --usd-cap %.2f)' % args.usd_cap if args.usd_cap else ''))
        if not execute:
            print('\nDRY RUN: nothing was sent and no key was read. To spend: --confirm-spend --usd-cap <USD>.')
            return 0
        # ---- live run
        from llm_ladder.llm_common import SECRET_NAMES, Redactor, load_env
        from llm_ladder.providers import build_providers
        env = load_env(env_file=args.env_file, root=REPO)
        if not env.get('ANTHROPIC_API_KEY'):
            raise CompareError('ANTHROPIC_API_KEY not found (environment, --env-file, or the .env files the ladder searches); nothing was sent.')
        redactor = Redactor(env.get(name) for name in SECRET_NAMES)
        providers = {k: v for k, v in build_providers(env).items() if k == 'anthropic'}
        args.arm_cap_usd = args.usd_cap
        spent, results = 0, []
        for item in items:
            outcome = run_ladder_item(args, item, arm='F', suffix='compare_fable', cohort=cohort, providers=providers, redactor=redactor, tiers=[tier],
                                      start_tier=5, max_tier=5, allow_fable=True, arm_spent_micro=spent, workdir=workdir, effort_override=args.effort)
            spent += outcome['spend_microusd']
            results.append(outcome)
            print('%-2s %-40s %-16s calls=%d spend=USD %.4f %5.0fs  %s' % (outcome['stratum'], outcome['node_id'], outcome['status'], outcome['calls'],
                                                                         outcome['spend_usd'], outcome['seconds'], outcome['stop_reason']), flush=True)
        summary_path = HERE / 'receipts' / ('fable_arm_%s.json' % time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()))
        write_new(summary_path, json_bytes(redactor.redact_obj({'schema_id': 'omega.pfp.compare.fable-arm-summary.v1', 'authority_effect': 'None',
                                                                 'protocol_sha256': cohort['protocol']['sha256'], 'usd_cap': args.usd_cap,
                                                                 'effort_override': args.effort, 'max_tokens_override': args.max_tokens,
                                                                 'arm_spend_usd': spent / 1e6, 'results': results})))
        print('fresh-Fable spend USD %.4f; summary %s' % (spent / 1e6, summary_path.relative_to(REPO).as_posix()))
        return 0
    except CompareError as error:
        print('REFUSED: %s' % error, file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
