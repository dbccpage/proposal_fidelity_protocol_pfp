"""Layer 2 family whose operad candidates the host runs: WF56.

Every check in this family is made by the Rust host ``pfp_operad``. It types
each candidate, runs the ones that name a body on the task's input and on
cases the model never sees, and compares each result with its own judge. This
module asks the model, hands the reply to the host and reports the host's
outcome. It compares nothing.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pfp.infrastructure import operad_host

from ..fidelity import HostOracleContext
from .base import (
    CERTIFIED,
    REFUSED,
    Session,
    Verdict,
    WorkflowFamily,
    canonical,
    certified,
    host_code,
    host_passed,
    refused,
    spec_from,
)
from .registry import register

FOLDER = 'wf56_host_run_operad_candidates'
ANSWER_REJECTED = 'ANSWER_REJECTED'


@register
class HostRunOperadCandidates(WorkflowFamily):
    """WF56. A reply names the operation it used, with a body from a closed list, and the host runs it.

    Domain: integer sums, the task of WF1. In WF2 to WF5 an operad candidate is
    a signature and a sentence, so the host can type it and no more. Here a
    candidate is ``{"id", "sources", "target", "body"}``: colours from the
    canon's ``task_value_colour`` and a body the host can execute. The run:

    1. Stage ``solve`` returns candidates and an answer.
    2. The host types every candidate and runs each one that has a body on the
       task's case and on the sealed probe cases. It compares each result with
       its own judge's; the caller supplies no expected value.
    3. The host judges the answer.

    A candidate is ``HOST_VERIFIED`` when its body gave the judge's result on
    every case, ``REFUSED`` when it is ill typed or gave another result, and
    ``UNVERIFIED_CANDIDATE`` when it has no body or does not fit the cases.
    The run is certified when at least one candidate is verified, none is
    refused and the answer is accepted.
    """
    spec = spec_from('WF56', 'Host-run operad candidates', 2, ['WF2'], None,
                     'rust_candidate_body_run_against_host_judge', FOLDER)

    def prompt(self, task: Mapping[str, Any]) -> str:
        return (f"{self.spec.wf_id} {task.get('statement', '')}\n"
                + canonical({key: task.get(key) for key in ('case', 'colours', 'bodies')}).decode('utf-8'))

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        task = session.task
        reply = session.ask(self.stage, self.prompt(task))
        if reply is None:
            return refused('NO_ADMISSIBLE_REPLY')
        content = reply.content if isinstance(reply.content, Mapping) else {}
        checker = task.get('checker')
        cases = [task.get('case'), *session.sealed.get('probes', [])]
        ran = operad_host.outcome('run', {'checker': checker, 'cases': cases,
                                          'candidates': content.get('candidates')})
        detail = {'candidates': ran.get('result')}
        if not host_passed(host, 'candidate_run_against_host_judge', ran):
            return refused(host_code(ran, ran.get('result', {}).get('verdict')), **detail)
        judged = operad_host.outcome('judge', {'checker': checker, 'case': task.get('case'),
                                               'answer': content.get('answer')})
        if not host_passed(host, 'answer_accepted_by_host_judge', judged):
            return refused(host_code(judged, ANSWER_REJECTED), **detail)
        return certified(ran['result']['verdict'], **detail)

    def fixtures(self):
        task = {'statement': 'Add the integers in values. Name the operation you used as a candidate with a body '
                             'from bodies and colours from colours. Reply {"candidates": [{"id", "sources", '
                             '"target", "body"}], "answer": {"total": n}}.',
                'checker': 'integer_sum_v1', 'case': {'values': [1, 2, 3]},
                'colours': ['Integer', 'IntegerList'],
                'bodies': ['identity', 'sum', 'product', 'difference', 'pack', 'sum_list']}
        sealed = {'probes': [{'values': [4, -1, 6]}, {'values': [-20, 5, 5]}]}
        each = ['Integer', 'Integer', 'Integer']

        def candidate(cid, sources, body=None, **more):
            return {'id': cid, 'sources': sources, 'target': 'Integer', **({'body': body} if body else {}), **more}

        def bundle(candidates, total=6):
            return {'task': task, 'sealed': sealed,
                    'replies': [{'candidates': candidates, 'answer': {'total': total}}]}
        add_list = candidate('add-the-list', ['IntegerList'], 'sum_list')
        return {
            'list_sum_is_verified': (bundle([add_list]), CERTIFIED),
            'one_input_per_value_is_verified': (bundle([candidate('add-each', each, 'sum')]), CERTIFIED),
            'an_unverified_extra_does_not_block': (
                bundle([add_list, candidate('explain', ['Integer'])]), CERTIFIED),
            'product_agrees_only_on_the_task_case': (bundle([candidate('multiply', each, 'product')]), REFUSED),
            'signature_without_a_body': (bundle([candidate('add-the-list', ['IntegerList'])]), REFUSED),
            'colour_outside_the_task_colours': (bundle([candidate('add', ['RationalValue'], 'sum')]), REFUSED),
            'verified_operation_with_a_wrong_answer': (bundle([add_list], total=7), REFUSED),
            'body_outside_the_closed_list': (bundle([candidate('mean', ['IntegerList'], 'average')]), REFUSED),
            'reply_that_marks_itself_verified': (
                bundle([candidate('add-the-list', ['IntegerList'], 'sum_list', disposition='HOST_VERIFIED')]),
                REFUSED),
            'reply_without_candidates': ({'task': task, 'sealed': sealed, 'replies': [{'answer': {'total': 6}}]},
                                         REFUSED),
        }
