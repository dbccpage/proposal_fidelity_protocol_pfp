"""Pilot035 composition adapter over the existing full-Panel IDE coordinator.

There is no provider path here. Prepared model replies, host execution and replay
use the same Adversary/PFP boundary as ordinary skill runs.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

import yaml

from eis.use_cases.pharmacy_search import PharmacySearchIndex
from pfp.domain.pfp_ingress import strict_json
from operads.application.ports.immune_screen_port import (
    DetectorIdentity, DetectorMatch, HostDangerObservation,
)
from adversary.infrastructure.estates.native_immune_screen import NativeImmuneScreen
from operads.infrastructure.parser.prompt_hierarchy_loader import load_prompt_node_from_pfp_yaml
from adversary.entrypoints import teamwork_cli
from adversary.infrastructure.operad_binding import operation_binding, validate_operation_binding
from adversary.infrastructure.pilot035_check import DATA, ROOT, NativeTaoChecker, canonical, public_task
from adversary.infrastructure.prompt_family_binder import PromptFamilyBinder
from adversary.use_cases.teamwork import TeamworkRun, next_action, observe
from adversary.use_cases.teamwork_pfp import check_teamwork_reply, prepare_teamwork_turn


MAX_RETAINED_HISTORY_BYTES = 64 * 1024 * 1024


def _save(path: Path, value, *, new=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x' if new else 'w', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def _load(path: Path):
    return _load_text(path.read_text(encoding='utf-8'))


def _bound(catalog: Path):
    operation = operation_binding('research.pilot035', '1', adapter='research')
    validate_operation_binding(operation, role_id='research.pilot035')
    node = load_prompt_node_from_pfp_yaml(DATA/'tao.yaml')
    template = yaml.safe_load((DATA/'tao.yaml').read_text(encoding='utf-8'))['objective']
    index = PharmacySearchIndex(catalog)
    bound = PromptFamilyBinder(index).bind(template_text=template, node=node,
                                           operation_id='adversary.research.pilot035')
    return node, index, bound, operation


def _run(path: Path):
    run = TeamworkRun.model_validate(_load(path))
    if run.executor != 'ide' or run.brief is None or not run.brief.task_premises:
        raise ValueError('PILOT035_IDE_STATE_REQUIRED')
    config = run.brief.task_premises
    if config.get('pilot_version') != 'pilot035.finite-tao.v1':
        raise ValueError('PILOT035_VERSION_MISMATCH')
    node, index, bound, operation = _bound(Path(config['catalog_path']))
    if bound.metadata != config['immune_binding'] or operation != config['operation_binding']:
        raise ValueError('PILOT035_BINDING_CHANGED')
    if public_task() != config['public_task']:
        raise ValueError('PILOT035_INPUT_CHANGED')
    NativeTaoChecker(Path(config['checker_binary']), config['checker_binary_sha256']).validate_task(public_task())
    return run, config, node, index


def _evaluate(config, node, index, candidate: str):
    answer = strict_json(candidate)
    if type(answer) is not dict:
        raise ValueError('PILOT035_ANSWER_OBJECT_REQUIRED')
    checked = NativeTaoChecker(Path(config['checker_binary']), config['checker_binary_sha256']).check(answer)
    claims = canonical(answer['claims']).decode('utf-8')
    spec = node.immune_fence
    query = dict(domain=spec.domain, tags=list(spec.tags), stage=spec.stage,
                 prompt_field=spec.prompt_field, scope=str(node.uri), limit=spec.max_antibodies)
    matches = index.match(query, claims)
    if matches['catalog_digest'] != config['immune_binding']['catalog_digest']:
        raise ValueError('PILOT035_BINDING_CHANGED')
    selected = {row['antibody_id'] for row in matches['selected']}
    if not set(spec.required_antibody_ids) <= selected:
        raise ValueError('PILOT035_ADMISSION_CHANGED')
    # Signal2 comes from the independently executed finite checker. Never derive
    # defect count or scope findings from the detector hit list.
    scope_findings = [row for row in checked['findings'] if row['code'] in (
        'UNSUPPORTED_ALL_CHM_PROMOTION', 'UNSUPPORTED_MUB6_PROMOTION')]
    danger = (HostDangerObservation(kind='REPLAY_FAILURE', severity='HIGH',
        defect_count=len(scope_findings), evidence_digest='sha256:'+checked['raw_output_sha256'],
        observer_id='native.mub.pilot035.finite-check.v1') if scope_findings else None)
    screen = NativeImmuneScreen()
    results = []
    for row in matches['selected']:
        hits = [DetectorMatch(hit['antibody_id'], hit['matched_text'], hit['offset'])
                for hit in matches.get('hits', ()) if hit['antibody_id'] == row['antibody_id']]
        verdict = screen.danger_verdict(hits, danger,
            detector=DetectorIdentity(row['antibody_id'], frozenset(), True))
        results.append({'antibody_id':row['antibody_id'], 'rule_digest':row['rule_digest'],
                        'hits':len(hits), **asdict(verdict)})
    return {'pilot_version':config['pilot_version'],
        'accepted':checked['accepted'] and not any(row['blocks'] for row in results),
        'native_check':checked, 'immune_screen':results,
        'immune_binding':config['immune_binding'], 'external_provider_dispatches':0,
        'ide_usage':None, 'ide_cost_usd':None, 'authority_effect':'None',
        'scope':'Finite structured claims on the explicit Tao phase table only; explanation prose is not a theorem checker.'}


def _teamwork(args):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = teamwork_cli.main(args)
    if code:
        raise ValueError('PILOT035_WORKFLOW_REFUSED: '+output.getvalue()[:600])
    return _load_text(output.getvalue())


def _load_text(text):
    return strict_json(text, max_bytes=MAX_RETAINED_HISTORY_BYTES)


def advance(path: Path):
    """Perform only the existing coordinator's pending host operations."""
    while True:
        run, _, _, _ = _run(path)
        action = next_action(run)
        if action is None or action.communication == 'pfp':
            return _teamwork(['next','--state',str(path)])
        command = {'native_gates':'native-gates','recheck':'recheck','ddc_store':'ddc-store',
                   'ddc_complete':'ddc-complete','digest':'digest'}.get(action.kind)
        if action.communication == 'deterministic':
            command = 'check'
        if command is None:
            raise ValueError('PILOT035_UNKNOWN_HOST_ACTION:'+action.kind)
        args = [command,'--state',str(path)]
        if command in ('ddc-store','ddc-complete','digest'):
            args += ['--output-dir',str(path.parent/'ddc')]
        _teamwork(args)


def start(state: Path, catalog: Path, checker: Path):
    if state.exists():
        raise ValueError('STATE_EXISTS')
    node, _, bound, operation = _bound(catalog)
    checker = checker.resolve()
    if not checker.is_file():
        raise ValueError('CHECKER_UNAVAILABLE')
    checker_digest = sha256(checker.read_bytes()).hexdigest()
    NativeTaoChecker(checker, checker_digest).validate_task(public_task())
    config = dict(pilot_version='pilot035.finite-tao.v1', catalog_path=str(catalog.resolve()),
        checker_binary=str(checker), checker_binary_sha256=checker_digest,
        public_task=public_task(), immune_binding=bound.metadata, operation_binding=operation)
    premises = state.with_suffix('.premises.json')
    _save(premises, config, new=True)
    checker_source = [Path(__file__), ROOT/'adversary/infrastructure/pilot035_check.py',
        DATA/'task.json', DATA/'answer.schema.json', DATA/'tao.yaml', DATA/'tao.binding.yaml', premises]
    args = ['start','--state',str(state),'--objective',bound.text,
        '--response-profile','compact-v2','--artifact-schema',str(DATA/'answer.schema.json'),
        '--task-premises',str(premises),'--max-repairs','1','--max-actions','48',
        '--acceptance','The original native checker accepts the structured finite answer; broader claims stay unsupported.',
        '--checker-id','pilot035.finite-tao.v1']
    for path in checker_source:
        args += ['--checker-source',str(path)]
    args += ['--check-command',sys.executable,'-B','-m',
        'adversary.infrastructure.pilot035_play','host-check','--state',str(state)]
    _teamwork(args)
    return advance(state)


def submit(state: Path, reply: Path):
    run, _, _, _ = _run(state)
    action = next_action(run)
    if action is None or action.communication != 'pfp':
        raise ValueError('PILOT035_NO_PENDING_REPLY')
    args = ['submit','--state',str(state),'--raw-reply',str(reply), '--worker','current IDE session']
    if action.kind in ('build','repair'):
        checked = check_teamwork_reply(action, prepare_teamwork_turn(action), reply.read_bytes(),
            worker='current IDE session', metadata={'cost_usd':None,'transport':'current_ide_session'})
        if not checked.blocked:
            candidate = state.parent/(action.action_id+'.candidate.json')
            raw = checked.content.encode('utf-8')
            with candidate.open('xb') as stream:
                stream.write(raw)
            host = candidate.with_suffix('.host.json')
            _save(host, dict(action_id=action.action_id,worker='Pilot035 candidate readback',
                summary='Retained the actual checked IDE candidate bytes.',
                artifacts={**action.artifacts,str(candidate):sha256(raw).hexdigest()}),new=True)
            args += ['--host-result',str(host)]
    _teamwork(args)
    return advance(state)


def replay(state: Path):
    final, config, node, index = _run(state)
    run = final.model_copy(update={'observations':()})
    checks = 0
    for observation in final.observations:
        action = next_action(run)
        if action is None:
            raise ValueError('PILOT035_REPLAY_EXTRA_OBSERVATION')
        from .teamwork_intelligence_host import _current_artifacts, _current_checker, validate_ddc_context
        _current_artifacts(action.artifacts)
        _current_checker(action)
        if action.kind == 'native_gates' and observation.metadata.get('native_gate_receipt'):
            from .teamwork_native_gates import replay_native_gate_reference
            replay_native_gate_reference(action, observation.metadata['native_gate_receipt'])
        if action.kind in ('ddc_store', 'ddc_complete') and not observation.blocked:
            validate_ddc_context(action.model_copy(update={'ddc_program':observation.ddc_program}))
        if action.kind == 'recheck' and observation.check is not None:
            actual = _evaluate(config,node,index,action.candidate)
            captured = observation.metadata.get('checker_capture',{})
            raw = bytes.fromhex(captured['stdout_hex'])
            stderr = bytes.fromhex(captured['stderr_hex'])
            if (captured.get('command') != list(action.check_command)
                    or type(captured.get('exit_code')) is not int
                    or captured['exit_code'] != (0 if actual['accepted'] else 1)
                    or captured['exit_code'] != observation.check.exit_status
                    or captured.get('authority_effect') != 'None'
                    or captured.get('authenticated') is not False
                    or sha256(raw + b'\n--- stderr ---\n' + stderr).hexdigest()
                        != observation.check.output_sha256):
                raise ValueError('PILOT035_REPLAY_CAPTURE_MISMATCH')
            if _load_text(raw.decode('utf-8')) != actual:
                raise ValueError('PILOT035_REPLAY_CHECK_MISMATCH')
            checks += 1
        run = observe(run, observation)
    if not checks:
        raise ValueError('PILOT035_REPLAY_NO_ORIGINAL_CHECK')
    return dict(status='REPLAYED',original_checks=checks,external_provider_dispatches=0,
                panel_coverage=run.panel_coverage,work_status=run.work_status,authority_effect='None')


def main(args=None):
    parser = argparse.ArgumentParser(description='Pilot035 through shared Adversary and admitted immune fences')
    commands = parser.add_subparsers(dest='command',required=True)
    for name in ('start','next','submit','replay','host-check'):
        command = commands.add_parser(name)
        command.add_argument('--state',type=Path,required=True)
        if name == 'start':
            command.add_argument('--catalog',type=Path,default=ROOT/'eis/antibodies/pharmacy_catalog.json')
            command.add_argument('--checker',type=Path,required=True)
        if name == 'submit':
            command.add_argument('--raw-reply',type=Path,required=True)
    parsed = parser.parse_args(args)
    try:
        if parsed.command == 'start':
            result = start(parsed.state.resolve(),parsed.catalog,parsed.checker)
        elif parsed.command == 'submit':
            result = submit(parsed.state.resolve(),parsed.raw_reply)
        elif parsed.command == 'next':
            result = advance(parsed.state.resolve())
        elif parsed.command == 'replay':
            result = replay(parsed.state.resolve())
        else:
            run, config, node, index = _run(parsed.state)
            action = next_action(run)
            if action is None or action.kind != 'recheck':
                raise ValueError('PILOT035_CHECK_NOT_PENDING')
            result = _evaluate(config,node,index,action.candidate)
            print(json.dumps(result,sort_keys=True))
            return 0 if result['accepted'] else 1
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 0
    except (ValueError,OSError,RuntimeError,KeyError) as exc:
        print(json.dumps({'status':'REFUSED','reason':str(exc),'authority_effect':'None'}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
