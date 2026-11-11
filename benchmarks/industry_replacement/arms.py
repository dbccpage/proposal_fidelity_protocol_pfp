"""The four compared arms, shared by the offline harness and the live runner.

direct_baseline                 task prompt only, one call, no checks.
industry_all_skills_and_rules   AGENTS.md + every SKILL.md in context, one call; AGENTS.md ``deny:``
                                guardrails enforced as a pre-commit style hard block.
industry_coder_reviewer_loop    the same context; a draft call then a review call that sees the task, the
                                rules and the draft; guardrails enforced on the reviewed output.
pfp_eis_pciv_regulated          legacy_importer -> thymus screening of every imported guard against the
                                task's public self panel -> PCIV-selected skill genome -> one call ->
                                host normalizer + public host checks (Signal 2) + admitted guards
                                (Signal 1) -> two-signal disposition -> at most one bounded repair.

No arm sees the sealed evaluator. Prices and latencies used offline are a
declared simulation tariff, not a provider quote.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

from pfp_core import immunity
from pfp_core.fidelity import WholeRunBudget, sha256_hex
from pfp_core.legacy_importer import estimate_tokens, import_stack

from tasks import t1_api_refactor, t2_sql_migration, t3_skill_triage, t4_protocol_synthesis
from tasks.common import extract_code

HERE = Path(__file__).resolve().parent
STACK = import_stack(HERE / 'industry_stack')
TASKS = {t.TASK_ID: t for t in (t1_api_refactor, t2_sql_migration, t3_skill_triage, t4_protocol_synthesis)}
ARMS = ('direct_baseline', 'industry_all_skills_and_rules', 'industry_coder_reviewer_loop', 'pfp_eis_pciv_regulated')

BASE_INSTRUCTION = 'You are a careful senior software engineer. Solve the task exactly as specified.'
REVIEW_INSTRUCTION = ('Review the draft below against the task and the repository rules. Fix every defect you '
                      'find and return the corrected complete module as one Python code block.')
REPAIR_INSTRUCTION = ('The host ran public checks on your previous answer. Fix the reported problems and return '
                      'the corrected complete module as one Python code block.')
MAX_OUTPUT_TOKENS = 4000
SIM_TARIFF = {'input_microusd_per_token': 1, 'output_microusd_per_token': 5,
              'call_latency_ms': 400, 'ms_per_output_token': 15}
AGENTS_GUARDS = [g for g in STACK.guards if g.target_epitope == 'AGENTS']


def industry_system() -> str:
    return STACK.rules_text + '\n\n' + '\n'.join(s.text for s in STACK.skills)


def pfp_system(task, skills) -> str:
    facts = ''
    if hasattr(task, 'schema_diff'):
        facts = f'\nHost-computed facts (deterministic, from the public examples): {task.schema_diff()}'
    return BASE_INSTRUCTION + facts + ''.join('\n\n' + s.text for s in skills)


_CHECK_CACHE: dict = {}


def public_check(task, text: str):
    """Host checks are pure functions of the public task and the text, so results are cached."""
    key = (task.TASK_ID, sha256_hex(text))
    if key not in _CHECK_CACHE:
        _CHECK_CACHE[key] = task.public_check(text)
    return _CHECK_CACHE[key]


def screened_guards(task):
    """All imported guards (AGENTS and skills) after thymus screening on this task's self panel."""
    return immunity.screen_rules(STACK.guards, task.SELF_PANEL)


def conflicting_skills(task) -> set[str]:
    """Skills owning a guard the thymus killed in this domain: their rules conflict with clean output."""
    _, killed = screened_guards(task)
    return {k['rule_id'].split(':')[1] for k in killed if k['rule_id'].startswith('skill:')}


@dataclass
class RunRecord:
    arm: str
    task_id: str
    sample: str
    delivered: str | None
    disposition: str
    stages: list = field(default_factory=list)
    budget: dict = field(default_factory=dict)
    host: dict | None = None
    signal1: list = field(default_factory=list)
    killed_guards: list = field(default_factory=list)
    last_text: str | None = None  # the last model text, delivered or not (for post-freeze analysis)


def simulated_quote(request: dict) -> int:
    in_tok = estimate_tokens('\n'.join(m['content'] for m in request['messages']))
    t = SIM_TARIFF
    return in_tok * t['input_microusd_per_token'] + request['max_output_tokens'] * t['output_microusd_per_token']


def simulated_usage(request: dict, text: str) -> dict:
    in_tok = estimate_tokens('\n'.join(m['content'] for m in request['messages']))
    out_tok = estimate_tokens(text)
    t = SIM_TARIFF
    return {'text': text, 'input_tokens': in_tok, 'output_tokens': out_tok,
            'microusd': in_tok * t['input_microusd_per_token'] + out_tok * t['output_microusd_per_token'],
            'wall_ms': t['call_latency_ms'] + out_tok * t['ms_per_output_token'], 'accounting_error': None}


def _call(budget: WholeRunBudget, solver, stage: str, messages: list[dict], record: RunRecord) -> str | None:
    """Quote, reserve, dispatch once, then settle or hold. None when the call is refused or fails.

    ``solver`` implements ``upper_quote(stage, request) -> int`` and
    ``complete(stage, request) -> dict(text, input_tokens, output_tokens, microusd, wall_ms,
    accounting_error)``; ``microusd`` None means unknown liability.
    """
    request = {'messages': messages, 'max_output_tokens': MAX_OUTPUT_TOKENS, 'tools': [], 'retries': 0}
    digest = sha256_hex(json.dumps(request, sort_keys=True, separators=(',', ':')))
    try:
        quote = solver.upper_quote(stage, request)
    except Exception as exc:  # admission failure: nothing dispatched
        record.stages.append({'stage': stage, 'refused': f'admission: {type(exc).__name__}: {str(exc)[:160]}'})
        return None
    call_id = budget.reserve(stage, digest, quote)
    if call_id is None:
        record.stages.append({'stage': stage, 'refused': 'budget', 'quote_microusd': quote})
        return None
    try:
        reply = solver.complete(stage, request)
    except Exception as exc:  # may have reached the provider: hold, never retry
        budget.hold_call(stage, call_id, f'{type(exc).__name__}')
        record.stages.append({'stage': stage, 'held': str(exc)[:160], 'quote_microusd': quote})
        return None
    if reply['microusd'] is None:
        budget.hold_call(stage, call_id, 'charge unknown')
        record.stages.append({'stage': stage, 'held': reply.get('accounting_error'), 'quote_microusd': quote})
        return None
    settled = budget.settle(stage, call_id, reply['microusd'], reply['input_tokens'] or 0,
                            reply['output_tokens'] or 0, reply.get('wall_ms') or 0)
    record.stages.append({'stage': stage, 'quote_microusd': quote, 'microusd': reply['microusd'],
                          'input_tokens': reply['input_tokens'], 'output_tokens': reply['output_tokens']})
    if not settled or reply.get('accounting_error'):
        if settled:
            budget.block(stage, reply['accounting_error'])
        return None
    record.last_text = reply['text']
    return reply['text']


def run_arm(arm: str, task, solver, sample: str, *, skills=(), cap_microusd: int = 100_000,
            ledger_path=':memory:', run_id: str | None = None) -> RunRecord:
    record = RunRecord(arm, task.TASK_ID, sample, None, 'REFUSED')
    budget = WholeRunBudget(run_id or f'{arm}:{task.TASK_ID}:{sample}', sha256_hex(task.PUBLIC_PROMPT),
                            cap_microusd, ledger_path)
    user = {'role': 'user', 'content': task.PUBLIC_PROMPT}
    try:
        if arm == 'direct_baseline':
            text = _call(budget, solver, 'draft', [{'role': 'system', 'content': BASE_INSTRUCTION}, user], record)
            record.delivered, record.disposition = text, ('DELIVERED' if text is not None else 'REFUSED')
        elif arm.startswith('industry_'):
            system = {'role': 'system', 'content': industry_system()}
            text = _call(budget, solver, 'draft', [system, user], record)
            if text is not None and arm == 'industry_coder_reviewer_loop':
                review = {'role': 'user', 'content': REVIEW_INSTRUCTION + '\n\nDraft:\n' + text}
                text = _call(budget, solver, 'review', [system, user, review], record)
            if text is not None:
                hits = immunity.signal1(extract_code(text), AGENTS_GUARDS)
                record.signal1 = [h.detector_id for h in hits]
                record.delivered, record.disposition = (None, 'GUARDRAIL_BLOCK') if hits else (text, 'DELIVERED')
        elif arm == 'pfp_eis_pciv_regulated':
            admitted, killed = screened_guards(task)
            record.killed_guards = [k['rule_id'] for k in killed]
            messages = [{'role': 'system', 'content': pfp_system(task, skills)}, user]
            text = _call(budget, solver, 'draft', messages, record)
            for attempt in range(2):
                if text is None:
                    break
                code, host, danger = public_check(task, text)
                matches = immunity.signal1(code, admitted)
                decision = immunity.decide(matches, danger)
                record.host, record.signal1 = host.to_dict(), [m.detector_id for m in matches]
                record.stages.append({'stage': f'regulate:{attempt}', 'disposition': decision.disposition,
                                      'basis': decision.basis, 'refusal_code': decision.refusal_code})
                if decision.disposition != immunity.HOLD:
                    record.delivered, record.disposition = code, 'DELIVERED'
                    break
                record.disposition = 'HOLD_REFUSED'
                if attempt == 1:
                    break
                feedback = {'role': 'user', 'content': REPAIR_INSTRUCTION + f'\nFailed host predicates: {host.failed}'
                            f'\nDanger kind: {danger.danger_type if danger else None}\n\nPrevious answer:\n{text}'}
                text = _call(budget, solver, 'repair', messages + [feedback], record)
        else:
            raise ValueError(f'unknown arm {arm}')
    finally:
        record.budget = budget.summary()
        budget.close()
    return record
