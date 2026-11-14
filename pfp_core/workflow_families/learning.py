"""Layer 7 family that learns across runs: WF55, the failure ledger with trial-gated rules.

Every check in this family is made by the Rust host ``pfp_operad``. It judges
each answer, writes the failure and trial records, keeps the ledger's chain and
decides admission. This module asks the model, carries records between host
commands and reports the host's outcome. It compares no answer and counts
nothing.
"""
from __future__ import annotations

import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pfp.infrastructure import operad_host

from .. import REPO_ROOT
from ..fidelity import HostOracleContext
from .base import CERTIFIED, REFUSED, Session, Verdict, WorkflowFamily, canonical, certified, refused, spec_from
from .registry import register

FOLDER = 'wf55_failure_ledger_with_trial_gated_rules'
EXAMPLE_LEDGER = REPO_ROOT / 'workflows' / FOLDER / 'examples' / 'ledger_after_first_run.jsonl'
PASS = 'PASS'


def lines(path: Path) -> list[str]:
    return path.read_text(encoding='utf-8').splitlines()


def passed(host: HostOracleContext, name: str, outcome: Mapping[str, Any]) -> bool:
    """Record one host outcome under ``name``; True when the host passed it."""
    return host.record(name, outcome['status'] == PASS, canonical(outcome).decode('utf-8'))


def code(outcome: Mapping[str, Any]) -> str:
    """The host's refusal code, or its status when the check ran and did not hold."""
    return outcome.get('refusal', {}).get('code', outcome['status'])


@register
class FailureLedgerTrialGatedRules(WorkflowFamily):
    """WF55. Keep failures in a ledger and load a rule in later runs only after it wins a held-out trial.

    Domain: integer sums, the task of WF1. The task carries the ledger so far,
    answers the host rejected in earlier runs, and held-out cases. The run:

    1. The host replays the ledger's chain and lists the rules already admitted.
    2. The host judges each reported failure itself and writes its record; an
       answer the judge accepts cannot be recorded as a failure.
    3. Stage ``propose`` returns one rule: an id, a capability kind, a constraint
       in words and the failures it comes from.
    4. Each held-out case is answered twice: stage ``baseline`` with the admitted
       rules, stage ``treated`` with the proposed rule added.
    5. The host judges both answers of every case and writes the trial record.
    6. The ledger admits the rule only on that trial, when it gained correct
       answers and broke no case the baseline had right.

    The outcome carries the new ledger. Give it to the next run as ``ledger``
    and that run's prompts carry the admitted rule. A rejected rule stays in
    the ledger and can be tried again.
    """
    spec = spec_from('WF55', 'Failure ledger with trial-gated rules', 7, ['WF1', 'WF14'], None,
                     'rust_ledger_admission_on_host_judged_trial', FOLDER)
    WORKFLOW = 'WF55'

    def solve_prompt(self, task: Mapping[str, Any], case: Any, rules: list[str]) -> str:
        """The task statement, the rules in force and one case."""
        return f"{self.spec.wf_id} {task.get('statement', '')}\n" + canonical(
            {'rules': rules, 'case': case}).decode('utf-8')

    def propose_prompt(self, task: Mapping[str, Any]) -> str:
        return (f'{self.spec.wf_id} {self.spec.name}. The host rejected these answers. Propose one rule that '
                'would have prevented them: {"id", "capability_kind", "constraint", "derived_from"}.\n'
                + canonical({'statement': task.get('statement', ''), 'failures': task.get('failures', [])})
                .decode('utf-8'))

    def answers(self, session: Session, stage: str, case: Mapping[str, Any], rules: list[str]) -> Any:
        """One answer to one held-out case; no reply is ``None`` and the host judges it wrong."""
        reply = session.ask(f"{stage}:{case.get('id')}", self.solve_prompt(session.task, case.get('case'), rules))
        return None if reply is None else reply.content

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        with tempfile.TemporaryDirectory(prefix='pfp-wf55-') as scratch:
            book = Path(scratch) / 'ledger.jsonl'
            book.write_text(''.join(line + '\n' for line in session.task.get('ledger', [])), encoding='utf-8')
            result = self.learn(session, host, book)
            detail = dict(result.detail, ledger=lines(book),
                          admitted=operad_host.ledger('admitted', book).get('result'))
        return Verdict(result.verdict, result.code, detail)

    def learn(self, session: Session, host: HostOracleContext, book: Path) -> Verdict:
        task = session.task
        checker = task.get('checker')
        loaded = operad_host.ledger('admitted', book)
        if not passed(host, 'ledger_chain_replayed', loaded):
            return refused(code(loaded))
        rules = [rule['constraint'] for rule in loaded['result']]
        for failure in task.get('failures', []):
            seen = operad_host.outcome('witness', {**failure, 'checker': checker})
            if not passed(host, f"failure_witnessed:{failure.get('id')}", seen):
                return refused(code(seen), failure=failure.get('id'))
            kept = operad_host.ledger('append', book, seen['result']['record'])
            if not passed(host, f"failure_recorded:{failure.get('id')}", kept):
                return refused(code(kept), failure=failure.get('id'))
        reply = session.ask('propose', self.propose_prompt(task))
        if reply is None:
            return refused('NO_ADMISSIBLE_REPLY')
        proposal = dict(reply.content) if isinstance(reply.content, Mapping) else {}
        kept = operad_host.ledger('append', book, {**proposal, 'kind': 'candidate'})
        if not passed(host, 'rule_recorded', kept):
            return refused(code(kept))
        rule = kept['result']['record']
        cases = [{'id': case.get('id'), 'case': case.get('case'),
                  'baseline': self.answers(session, 'baseline', case, rules),
                  'treated': self.answers(session, 'treated', case, [*rules, rule['constraint']])}
                 for case in task.get('held_out', [])]
        scored = operad_host.outcome('trial', {'candidate': rule['id'], 'checker': checker, 'cases': cases})
        if not passed(host, 'trial_judged', scored):
            return refused(code(scored), rule=rule['id'])
        detail = {'rule': rule, 'loaded': rules, 'trial': scored['result']}
        kept = operad_host.ledger('append', book, scored['result']['record'])
        if not passed(host, 'trial_recorded', kept):
            return refused(code(kept), **detail)
        admission = {'kind': 'admission', 'candidate': rule['id'], 'trial': kept['result']['seq']}
        earned = operad_host.ledger('append', book, admission)
        if not passed(host, 'rule_admitted_on_its_latest_trial', earned):
            return refused(code(earned), **detail)
        return certified('RULE_ADMITTED', **detail)

    def fixtures(self):
        def case(cid, values):
            return {'id': cid, 'case': {'values': values}}

        def failure(fid, values, total, run='run-1'):
            return {**case(fid, values), 'workflow': 'WF1', 'run': run, 'answer': {'total': total}}
        task = {'statement': 'Add the integers in values. Reply {"total": n}.', 'checker': 'integer_sum_v1',
                'ledger': [],
                'failures': [failure('f1', [9, -2], 11), failure('f2', [-6, -1, 4], 11)],
                'held_out': [case('h1', [8, -3]), case('h2', [-7, 2, -1]), case('h3', [3, 8])]}
        rule = {'id': 'keep-the-sign', 'capability_kind': 'antibody',
                'constraint': 'A minus sign belongs to its number. Subtract a negative value; do not add it.',
                'derived_from': ['f1', 'f2']}
        right = [{'total': 5}, {'total': -6}, {'total': 11}]
        unsigned = [{'total': 11}, {'total': 10}, {'total': 11}]

        def bundle(baseline, treated, proposal=rule, **over):
            answers = [answer for pair in zip(baseline, treated, strict=True) for answer in pair]
            return {'task': {**task, **over}, 'replies': [proposal, *answers]}
        second = {'failures': [failure('f3', [5, -5, -1], 11, 'run-2')],
                  'held_out': [case('h4', [-4, -4]), case('h5', [10, -1])],
                  'ledger': lines(EXAMPLE_LEDGER)}
        again = {**rule, 'id': 'check-each-sign', 'derived_from': ['f3'],
                 'constraint': 'Read each value with its sign before adding.'}
        edited = [line.replace('keep-the-sign', 'keep-the-sum') for line in lines(EXAMPLE_LEDGER)]
        return {
            'rule_admitted_on_a_winning_trial': (bundle(unsigned, right), CERTIFIED),
            'later_run_loads_the_admitted_rule': (
                bundle([{'total': 8}, {'total': 9}], [{'total': -8}, {'total': 9}], again, **second), CERTIFIED),
            'no_gain_is_not_earned': (bundle(unsigned, unsigned), REFUSED),
            'a_rule_that_breaks_a_clean_case': (bundle(unsigned, [*right[:2], {'total': -11}]), REFUSED),
            'a_correct_answer_is_not_a_failure': (
                bundle(unsigned, right, failures=[failure('f1', [9, -2], 7)]), REFUSED),
            'trial_on_the_failures_the_rule_came_from': (
                bundle(unsigned[:1], right[:1], held_out=[case('f1', [9, -2])]), REFUSED),
            'rule_from_an_unrecorded_failure': (
                bundle(unsigned, right, {**rule, 'derived_from': ['f9']}), REFUSED),
            'rule_that_names_its_own_admission': (
                bundle(unsigned, right, {**rule, 'kind': 'admission', 'trial': 0}), REFUSED),
            'edited_ledger_is_refused': (bundle(unsigned, right, again, **{**second, 'ledger': edited}), REFUSED),
        }
