"""Hard budget guard: a persistent, locked, integer micro-USD ledger enforced before every paid call.

AuthorityEffect: None. Ported in spirit (with attribution) from the_symbol_game omega_engine_pfp
(infrastructure/seat_transport/routing.py BudgetPolicy / admit_spend, openrouter_seat_gateway.py
CallLedger, omega_engine_woland budget_ledger.py): money is integer micro-USD, the worst case is
admitted BEFORE dispatch, an ambiguous outcome keeps its reservation, and an unreported cost is
unknown rather than zero. The reference keeps its ledger in SQLite behind a native host; this
version is a JSON file behind a lock so the ledger can be reviewed and committed.

Three independent limits apply to a paid call; the first one exceeded refuses it:
  anthropic_weekly   the $150-per-ISO-week Anthropic cap (configurable, default 150 USD);
  paid_other_weekly  paid non-Anthropic providers (OpenRouter paid models), default 10 USD;
  run                the per-run cap passed on the CLI (--max-cost-usd), applied to all paid calls.
Free-tier calls cost 0 and are only counted (their rate limits are handled by the provider layer).
"""
from __future__ import annotations

import json
from pathlib import Path

from .llm_common import FileLock, atomic_write, iso_week, json_bytes, utc_iso

SCHEMA_ID = 'omega.pfp.llm-ladder.budget-ledger.v1'
MICRO = 1_000_000
DEFAULT_CAPS = {'anthropic_weekly_usd': 150.0, 'paid_other_weekly_usd': 10.0}
FAMILIES = ('anthropic', 'paid_other', 'free')


class BudgetRefused(Exception):
    """A paid call was refused before dispatch. `code` names the limit; nothing was sent."""

    def __init__(self, code: str, message: str):
        super().__init__(code + ': ' + message)
        self.code, self.message = code, message


def usd_to_micro(usd) -> int:
    return int(round(float(usd) * MICRO))


def micro_to_usd(micro: int) -> float:
    return micro / MICRO


def cost_microusd(input_tokens: int, output_tokens: int, in_per_mtok: int, out_per_mtok: int) -> int:
    """Ceiling of the exact cost. Prices are micro-USD per million tokens."""
    return (input_tokens * in_per_mtok + output_tokens * out_per_mtok + MICRO - 1) // MICRO


def _empty_week():
    return {'external_adjustment_microusd': {'anthropic': 0, 'paid_other': 0},
            'by_provider': {}, 'reserved': {}, 'unreconciled_microusd': {'anthropic': 0, 'paid_other': 0},
            'runs': {}}


class Ledger:
    def __init__(self, path, caps=None, clock_week=iso_week):
        self.path = Path(path)
        self._caps_override = dict(caps or {})
        self._week = clock_week

    # ------------------------------------------------------------------ persistence
    def _load(self) -> dict:
        if self.path.is_file():
            data = json.loads(self.path.read_bytes().decode('utf-8'))
            if data.get('schema_id') != SCHEMA_ID:
                raise ValueError('budget ledger has an unknown schema_id')
        else:
            data = {'schema_id': SCHEMA_ID, 'authority_effect': 'None', 'caps': dict(DEFAULT_CAPS), 'weeks': {},
                    'note': ('Integer micro-USD. Costs are rated from provider usage (not an invoice); '
                             'an unreported cost keeps its worst-case reservation.')}
        data['caps'] = {**DEFAULT_CAPS, **data.get('caps', {}), **self._caps_override}
        data['weeks'].setdefault(self._week(), _empty_week())
        return data

    def _save(self, data: dict) -> None:
        data['updated_utc'] = utc_iso()
        atomic_write(self.path, json_bytes(data))

    def snapshot(self) -> dict:
        with FileLock(self.path):
            return self._load()

    # ------------------------------------------------------------------ totals
    @staticmethod
    def _family_total(week: dict, family: str) -> int:
        spent = 0
        for provider, models in week['by_provider'].items():
            for row in models.values():
                if row.get('family') == family:
                    spent += row['cost_microusd']
        reserved = sum(r['microusd'] for r in week['reserved'].values() if r['family'] == family)
        return (spent + reserved + week['external_adjustment_microusd'].get(family, 0)
                + week['unreconciled_microusd'].get(family, 0))

    def week_totals(self) -> dict:
        data = self.snapshot()
        week = data['weeks'][self._week()]
        caps = data['caps']
        return {'week': self._week(),
                'anthropic_microusd': self._family_total(week, 'anthropic'),
                'anthropic_cap_microusd': usd_to_micro(caps['anthropic_weekly_usd']),
                'paid_other_microusd': self._family_total(week, 'paid_other'),
                'paid_other_cap_microusd': usd_to_micro(caps['paid_other_weekly_usd'])}

    def remaining_anthropic_microusd(self) -> int:
        totals = self.week_totals()
        return totals['anthropic_cap_microusd'] - totals['anthropic_microusd']

    # ------------------------------------------------------------------ admission
    def reserve(self, call_id: str, *, run_id: str, run_cap_microusd: int, family: str, provider: str,
                model: str, estimate_microusd: int) -> None:
        """Admit the worst case for one call or raise BudgetRefused. Persisted before returning."""
        if family not in FAMILIES:
            raise ValueError('unknown budget family ' + repr(family))
        if type(estimate_microusd) is not int or estimate_microusd < 0:
            raise ValueError('estimate must be a non-negative integer of micro-USD')
        with FileLock(self.path):
            data = self._load()
            week = data['weeks'][self._week()]
            if call_id in week['reserved']:
                raise ValueError('duplicate call_id ' + call_id)
            run = week['runs'].setdefault(run_id, {'spent_microusd': 0, 'reserved_microusd': 0, 'calls': 0, 'cap_microusd': run_cap_microusd})
            if family != 'free':
                if run_cap_microusd <= 0:
                    raise BudgetRefused('RUN_CAP_ZERO', 'run cap is 0; paid call refused before dispatch')
                if estimate_microusd <= 0:
                    raise BudgetRefused('ESTIMATE_REQUIRED', 'a paid call needs a positive worst-case estimate')
                in_run = run['spent_microusd'] + run['reserved_microusd']
                if in_run + estimate_microusd > run_cap_microusd:
                    raise BudgetRefused('RUN_CAP', 'run %s: %d + %d micro-USD exceeds the run cap %d' % (
                        run_id, in_run, estimate_microusd, run_cap_microusd))
            caps = data['caps']
            if family == 'anthropic':
                total = self._family_total(week, 'anthropic')
                cap = usd_to_micro(caps['anthropic_weekly_usd'])
                if total + estimate_microusd > cap:
                    raise BudgetRefused('ANTHROPIC_WEEKLY_CAP', 'week %s: %d + %d micro-USD exceeds the cap %d' % (
                        self._week(), total, estimate_microusd, cap))
            elif family == 'paid_other':
                total = self._family_total(week, 'paid_other')
                cap = usd_to_micro(caps['paid_other_weekly_usd'])
                if total + estimate_microusd > cap:
                    raise BudgetRefused('PAID_OTHER_WEEKLY_CAP', 'week %s: %d + %d micro-USD exceeds the cap %d' % (
                        self._week(), total, estimate_microusd, cap))
            week['reserved'][call_id] = {'family': family, 'provider': provider, 'model': model,
                                         'microusd': estimate_microusd, 'run_id': run_id}
            run['reserved_microusd'] += estimate_microusd
            self._save(data)

    def settle(self, call_id: str, *, cost_microusd: int, input_tokens: int, output_tokens: int,
               cost_source: str = 'price_table') -> None:
        """Replace the reservation with the rated cost. A cost above the reservation is still booked."""
        with FileLock(self.path):
            data = self._load()
            week = data['weeks'][self._week()]
            held = week['reserved'].pop(call_id, None)
            if held is None:
                raise KeyError('no reservation for ' + call_id)
            row = week['by_provider'].setdefault(held['provider'], {}).setdefault(held['model'], {
                'family': held['family'], 'calls': 0, 'input_tokens': 0, 'output_tokens': 0, 'cost_microusd': 0})
            row['calls'] += 1
            row['input_tokens'] += int(input_tokens or 0)
            row['output_tokens'] += int(output_tokens or 0)
            row['cost_microusd'] += int(cost_microusd)
            run = week['runs'].setdefault(held['run_id'], {'spent_microusd': 0, 'reserved_microusd': 0, 'calls': 0, 'cap_microusd': 0})
            run['reserved_microusd'] = max(0, run['reserved_microusd'] - held['microusd'])
            run['spent_microusd'] += int(cost_microusd)
            run['calls'] += 1
            if cost_source != 'price_table':
                row.setdefault('cost_sources', {})
                row['cost_sources'][cost_source] = row['cost_sources'].get(cost_source, 0) + 1
            self._save(data)

    def release(self, call_id: str) -> None:
        """Drop a reservation for a call known not to have been dispatched or billed."""
        with FileLock(self.path):
            data = self._load()
            week = data['weeks'][self._week()]
            held = week['reserved'].pop(call_id, None)
            if held is not None:
                run = week['runs'].get(held['run_id'])
                if run:
                    run['reserved_microusd'] = max(0, run['reserved_microusd'] - held['microusd'])
            self._save(data)

    def retain_unreconciled(self, call_id: str) -> int:
        """Ambiguous outcome (timeout after send): keep the worst case as spend until reconciled by hand."""
        with FileLock(self.path):
            data = self._load()
            week = data['weeks'][self._week()]
            held = week['reserved'].pop(call_id, None)
            if held is None:
                return 0
            fam = held['family']
            if fam in ('anthropic', 'paid_other'):
                week['unreconciled_microusd'][fam] = week['unreconciled_microusd'].get(fam, 0) + held['microusd']
            run = week['runs'].get(held['run_id'])
            if run:
                run['reserved_microusd'] = max(0, run['reserved_microusd'] - held['microusd'])
                run['spent_microusd'] += held['microusd'] if fam != 'free' else 0
            self._save(data)
            return held['microusd']

    def count_free_call(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> None:
        """Free-tier calls are counted (tokens, calls) with cost 0."""
        with FileLock(self.path):
            data = self._load()
            week = data['weeks'][self._week()]
            row = week['by_provider'].setdefault(provider, {}).setdefault(model, {
                'family': 'free', 'calls': 0, 'input_tokens': 0, 'output_tokens': 0, 'cost_microusd': 0})
            row['calls'] += 1
            row['input_tokens'] += int(input_tokens or 0)
            row['output_tokens'] += int(output_tokens or 0)
            self._save(data)

    def set_external_adjustment(self, family: str, microusd: int) -> None:
        """Operator hook: spend made outside this ledger (other worktrees, the console) this week."""
        with FileLock(self.path):
            data = self._load()
            data['weeks'][self._week()]['external_adjustment_microusd'][family] = int(microusd)
            self._save(data)

    def run_summary(self, run_id: str) -> dict:
        week = self.snapshot()['weeks'][self._week()]
        return dict(week['runs'].get(run_id, {}))
