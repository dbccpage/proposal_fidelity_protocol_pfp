"""Layer 3 family whose patch the host tests on a working copy: WF57.

Every check in this family is made by the Rust host ``pfp_operad``. It verifies
the declared sources, copies them, runs the task's check commands, applies the
patch to the copy, runs the checks again and decides the outcome. This module
asks the model for a patch, writes the task's files to a folder and hands both
to the host. It applies nothing and compares nothing.
"""
from __future__ import annotations

import json
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pfp.infrastructure import operad_host

from .. import REPO_ROOT
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
from .learning import EXAMPLE_LEDGER, lines
from .registry import register

FOLDER = 'wf57_host_tested_patch_repair'
EXAMPLE = REPO_ROOT / 'workflows' / FOLDER / 'examples' / 'refused_operation'
# The fields of a repair request the task fixes. A reply cannot replace them.
TASK_FIELDS = ('run_key', 'objective', 'sources', 'write_paths', 'checks')


def terminal_code(outcome: Mapping[str, Any]) -> str:
    """The host's code for a run that did not pass: its refusal, or the outcome of its record."""
    record = outcome.get('result') or {}
    return host_code(outcome, (record.get('refusal') or {}).get('code') or record.get('outcome'))


@register
class HostTestedPatchRepair(WorkflowFamily):
    """WF57. A reply is a patch, and the host tests it on a copy of the task's files.

    Domain: a small set of text files and check commands that exit 0 or not.
    In the fixtures the files are requests for the host's own commands, so the
    checks are ``pfp_operad run`` and ``pfp_operad judge`` and need no other
    program. The run:

    1. Stage ``propose`` shows the files in the write set and the checks, and
       returns ``{"candidate_patch": "<unified diff>"}``.
    2. The host verifies each declared file against its SHA-256, copies the
       files to a new run folder and runs every check on the copy.
    3. The host applies the patch to the copy, only inside the write set and
       only where each hunk fits exactly, and runs every check again.
    4. The host compares the checks that failed before with the ones that fail
       after, and confirms the declared files were never written.

    The run is certified when the outcome is ``REPAIRED``: every check that
    failed now passes and no check that passed now fails. Any other outcome is
    refused with the host's code. A patch that was tested and did not repair
    leaves a failure record, which the host adds to the task's ledger, the same
    ledger WF55 reads.
    """
    spec = spec_from('WF57', 'Host-tested patch repair', 3, ['WF9', 'WF56'], None,
                     'rust_patch_tested_on_working_copy', FOLDER)
    stage = 'propose'

    def prompt(self, task: Mapping[str, Any]) -> str:
        shown = {name: text for name, text in task.get('files', {}).items() if name in task.get('write_paths', [])}
        return (f"{self.spec.wf_id} {task.get('statement', '')}\n"
                + canonical({'objective': task.get('objective'), 'files': shown,
                             'write_paths': task.get('write_paths'), 'checks': task.get('checks')}).decode('utf-8'))

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        task = session.task
        reply = session.ask(self.stage, self.prompt(task))
        if reply is None:
            return refused('NO_ADMISSIBLE_REPLY')
        content = reply.content if isinstance(reply.content, Mapping) else {}
        request = {**content, **{key: task.get(key) for key in TASK_FIELDS}, 'workflow': self.spec.wf_id}
        with tempfile.TemporaryDirectory(prefix='pfp-wf57-') as scratch:
            source, book = Path(scratch) / 'source', Path(scratch) / 'ledger.jsonl'
            source.mkdir()
            for name, text in task.get('files', {}).items():
                (source / name).write_bytes(text.encode('utf-8'))
            book.write_text(''.join(line + '\n' for line in task.get('ledger', [])), encoding='utf-8')
            tested = operad_host.call(('repair', str(source), str(Path(scratch) / 'run')), request)
            record = tested.get('result') or {}
            repaired = host_passed(host, 'patch_repairs_the_working_copy', tested)
            if record.get('failure'):
                kept = operad_host.ledger('append', book, record['failure'])
                if not host_passed(host, 'failed_patch_recorded', kept):
                    return refused(host_code(kept), record=record)
            detail = {'record': record, 'ledger': lines(book)}
        if not repaired:
            return refused(terminal_code(tested), **detail)
        return certified(record['outcome'], **detail)

    def fixtures(self):
        shipped = json.loads((EXAMPLE / 'request.json').read_text(encoding='utf-8'))
        files = {name: (EXAMPLE / 'source' / name).read_text(encoding='utf-8') for name in shipped['sources']}
        task = {'statement': 'A check fails on a file below. Reply {"candidate_patch": "<unified diff>"} with a/ '
                             'and b/ paths that makes every check pass. Only files in write_paths may change.',
                **{key: shipped[key] for key in TASK_FIELDS}, 'files': files, 'ledger': []}
        good = shipped['candidate_patch']
        both_files = ['operation.json', 'answer.json']
        breaks_answer = (good + '--- a/answer.json\n+++ b/answer.json\n@@ -4 +4 @@\n'
                         '-  "answer": {"total": 6}\n+  "answer": {"total": 7}\n')
        weak = good.replace('"body": "sum"', '"body": "difference"')
        by_list = good.replace('+    {"id": "combine", "sources": ["Integer", "Integer", "Integer"]',
                               '+    {"id": "combine", "sources": ["IntegerList"]').replace(
                                   '"body": "sum"', '"body": "sum_list"')

        def bundle(patch=good, reply=None, **over):
            return {'task': {**task, **over},
                    'replies': [{'candidate_patch': patch} if reply is None else reply]}
        return {
            'patch_repairs_the_refused_operation': (bundle(), CERTIFIED),
            'another_patch_that_repairs_it': (bundle(by_list), CERTIFIED),
            'patch_that_leaves_the_check_failing': (bundle(weak), REFUSED),
            'failed_patch_joins_an_existing_ledger': (bundle(weak, ledger=lines(EXAMPLE_LEDGER)), REFUSED),
            'patch_that_breaks_the_passing_check': (bundle(breaks_answer, write_paths=both_files), REFUSED),
            'patch_outside_the_write_set': (bundle(breaks_answer), REFUSED),
            'reply_that_widens_its_own_write_set': (
                bundle(reply={'candidate_patch': breaks_answer, 'write_paths': both_files}), REFUSED),
            'patch_that_does_not_fit_the_file': (bundle(good.replace('@@ -9 +9 @@', '@@ -8 +8 @@')), REFUSED),
            'reply_in_words_instead_of_a_patch': (bundle('Change the body from product to sum.'), REFUSED),
            'reply_that_declares_itself_repaired': (
                bundle(reply={'candidate_patch': good, 'outcome': 'REPAIRED'}), REFUSED),
            'reply_without_a_patch': (bundle(reply={}), REFUSED),
            'file_that_differs_from_its_declared_hash': (
                bundle(files={**files, 'answer.json': files['answer.json'].replace('6', '7')}), REFUSED),
            'check_whose_program_is_missing': (
                bundle(checks=[{'check_id': 'operation', 'argv': ['pfp-no-such-program']}]), REFUSED),
            'nothing_to_repair': (bundle(checks=shipped['checks'][1:]), REFUSED),
        }
