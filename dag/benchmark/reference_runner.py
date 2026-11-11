"""Bounded benchmark runner, with an injected billing-aware provider port.

There is deliberately no filesystem/retrieval/tool interface in model requests.
This module has no answer-key input and implements no automatic accuracy judge.
The live OpenRouter adapter requires a finite campaign admission and conservative
quotes. Its external provider-enforcement premises are explicit, not proved here.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Protocol

from budget_ledger import BudgetError, RunLedger
from rational_workflows import EXPERIMENTS, public_context, panel_for
from rational_panel import check_panel
from hamiltonian_workflows import MATRIX_PLANS
from hamiltonian_artifact import public_contract as matrix_contract, check_artifact, public_input_artifact
from section_workflows import SECTION_PLANS, assemble_sections
from charpoly_workflows import (CHARPOLY_PLANS, preflight as charpoly_preflight,
                               stage_request as charpoly_stage_request, check_candidate as check_charpoly)
from host_charpoly_workflows import HOST_CHARPOLY_PLANS
from eis_pciv_workflows import (EIS_PCIV_PLANS, build_pciv_quotient_artifact,
                                evaluate_eis_charpoly_stage, public_charpoly_input_context)

HERE = Path(__file__).resolve().parent
PLANS = {
    'direct': [
        'Solve every part of the original task. State assumptions, exceptional cases and checks. Return your complete derivation and final results.',
    ],
    'self_critique': [
        'Draft a complete solution to every part of the original task. State assumptions, exceptional cases and checks.',
        'Audit the preceding draft against the unchanged original task. Correct unsupported steps and missing parameter cases. Return a complete final solution, with unresolved issues stated explicitly.',
    ],
}
PLANS.update(EXPERIMENTS)
PLANS.update(MATRIX_PLANS)
PLANS.update(SECTION_PLANS)
PLANS.update(CHARPOLY_PLANS)
PLANS.update(HOST_CHARPOLY_PLANS)
PLANS.update(EIS_PCIV_PLANS)

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')

@dataclass(frozen=True)
class Reply:
    text: str
    actual_microusd: int | None
    input_tokens: int | None
    output_tokens: int | None
    reasoning_tokens: int | None = None
    finish_reason: str = 'unavailable'
    provider_request_id: str | None = None
    provider_evidence: dict | None = None
    accounting_error: str | None = None

class Provider(Protocol):
    name: str
    offline: bool
    def upper_quote(self, request: dict) -> int:
        """Must cover all billable tokens/fees under externally enforced limits."""
    def complete(self, request: dict) -> Reply:
        """Exactly one dispatch. No hidden retries, fallback, tools or paid judges."""

class OfflineTape:
    name = 'offline-tape-no-provider-execution'
    offline = True
    def __init__(self, responses: list[str]):
        self.responses = iter(responses)
        self.requests = []
    def upper_quote(self, request):
        return 0
    def complete(self, request):
        self.requests.append(request)
        return Reply(next(self.responses), 0, None, None, finish_reason='offline_fixture')

def token_value(value):
    if value is not None and (type(value) is not int or value < 0):
        raise ValueError('Token usage must be an exact nonnegative integer or unavailable')
    return value


def freeze_json(path, value):
    # Evidence must remain serializable even when malformed provider metadata
    # contains lone surrogates. ASCII JSON escaping preserves those code units;
    # it does not admit them as a valid answer or change request canonicalization.
    data = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('ascii') + b'\n'
    with path.open('xb') as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    return sha(data)

def run(plan: str, provider: Provider, output: Path, run_id: str, *, max_output_tokens=4000, live_admission=None):
    """Freeze a run receipt, including failures. Directory creation is exclusive.

    Live dispatch requires the installed OpenRouter adapter and exact membership
    in an initialized, finite campaign. Only explicitly registered adaptations
    are executable; research DAG nodes do not become generic executable stages.
    """
    if plan not in PLANS:
        raise ValueError('Unsupported plan; proposed research hosts are not generic executable stages')
    specification = (EXPERIMENTS.get(plan) or MATRIX_PLANS.get(plan) or SECTION_PLANS.get(plan) or
                     CHARPOLY_PLANS.get(plan) or HOST_CHARPOLY_PLANS.get(plan) or EIS_PCIV_PLANS.get(plan))
    if specification:
        from source_custody import pin_path
        for name, expected in specification['source_pins'].items():
            if sha(pin_path(name).read_bytes()) != expected:
                raise ValueError('Loaded experiment source changed; restart and prepare a newly bound campaign')
        if plan in EXPERIMENTS and sha(canonical(EXPERIMENTS[plan]['contract'])) != EXPERIMENTS[plan]['contract_sha256']:
            raise ValueError('Experiment contract changed')
    offline = provider.offline is True
    if not offline:
        from campaign_ledger import CampaignAdmission
        from openrouter_provider import OpenRouterProvider
        if not isinstance(provider, OpenRouterProvider) or not isinstance(live_admission, CampaignAdmission):
            raise ValueError('Live provider requires the guarded OpenRouter adapter and campaign admission')
    if type(max_output_tokens) is not int or max_output_tokens <= 0:
        raise ValueError('Positive exact output-token limit required')
    commitment = json.loads((HERE / 'commitment.json').read_text(encoding='utf-8'))
    seed = (HERE / 'seed_prompt.txt').read_bytes()
    if sha(seed) != commitment['seed_sha256']:
        raise ValueError('Frozen seed changed')
    seed_text = seed.decode('utf-8')
    output.mkdir(parents=True, exist_ok=False)
    (output / 'calls').mkdir()
    run_cap = 100_000
    if not offline:
        run_cap = live_admission.admit(run_id, plan, provider.admission_identity, sha(seed), max_output_tokens)
    ledger = RunLedger(output / 'ledger.sqlite3')
    ledger.start(run_id, sha(seed), run_cap)
    started = time.perf_counter()
    records = []; previous = None; responses = {}; status = 'offline_fixture_completed' if offline else 'completed'
    experiment = EXPERIMENTS.get(plan)
    matrix_plan = MATRIX_PLANS.get(plan)
    section_plan = SECTION_PLANS.get(plan)
    charpoly_plan = CHARPOLY_PLANS.get(plan)
    host_charpoly_plan = HOST_CHARPOLY_PLANS.get(plan)
    charpoly_verification = None  # set only from an observed, validated native receipt
    composition_verified = False  # set only from an observed composition witness
    eis_pciv_plan = EIS_PCIV_PLANS.get(plan)
    charpoly_checks = []
    charpoly_custody = None
    matrix_checks = []
    eis_pciv_checks = []
    pciv_quotient_receipt = None
    stages = specification['stages'] if specification else [
        {'id': f'control_{index}', 'instruction': instruction, 'max_output_tokens': max_output_tokens,
         'visible_artifacts': [f'control_{index - 1}'] if index else []}
        for index, instruction in enumerate(PLANS[plan])]
    try:
        if charpoly_plan:
            try:
                charpoly_custody = charpoly_preflight(sha(seed))
                freeze_json(output / 'native_preflight.json', charpoly_custody)
            except Exception as exc:
                status = 'host_infrastructure_failure'
                records.append({'error_class': type(exc).__name__, 'error': str(exc)[:300], 'dispatched': False})
                stages = []
        if matrix_plan and matrix_plan['host_matrix']:
            artifact = public_input_artifact(sha(seed))
            responses['matrix_context'] = canonical(artifact).decode('utf-8')
            checked = check_artifact(responses['matrix_context'], sha(seed))
            if not checked['accepted']:
                raise ValueError('Host-derived representation failed its own exact check')
            matrix_checks.append({'stage_id': 'host_matrix', **checked})
            freeze_json(output / 'host_matrix.json', {'artifact': artifact, 'check': matrix_checks[-1]})
        if host_charpoly_plan:
            if host_charpoly_plan.get('host_matrix'):
                artifact = public_input_artifact(sha(seed))
                responses['matrix_context'] = canonical(artifact).decode('utf-8')
                checked = check_artifact(responses['matrix_context'], sha(seed))
                if not checked['accepted']:
                    raise ValueError('Host-derived representation failed its own exact check')
                matrix_checks.append({'stage_id': 'host_matrix', **checked})
                freeze_json(output / 'host_matrix.json', {'artifact': artifact, 'check': matrix_checks[-1]})
            if host_charpoly_plan.get('host_charpoly'):
                from qm_host_charpoly import build_certified_context, validate_certified_context
                certified = build_certified_context(sha(seed))
                validated = validate_certified_context(certified)
                if not validated['valid']:
                    raise ValueError('Host-derived characteristic polynomial context failed validation')
                charpoly_verification = {
                    'status': certified['native_verification']['status'],
                    'grid_points_verified': certified['native_verification']['grid_points_verified'],
                    'receipt_sha256': validated['evidence']['receipt_sha256'],
                    'native_reexecuted': validated['evidence']['native_reexecuted'],
                }
                responses['charpoly_context'] = canonical(certified).decode('utf-8')
                freeze_json(output / 'host_charpoly.json', certified)
            if host_charpoly_plan.get('semantic_composition'):
                from host_charpoly_workflows import build_semantic_composition_artifact
                composition = build_semantic_composition_artifact(sha(seed))
                composition_verified = (composition.get('status') == 'VERIFIED_OFFLINE_COMPOSITION'
                                        and composition.get('operad_composition_witness', {}).get('is_associative') is True)
                responses['semantic_composition_receipt'] = canonical(composition).decode('utf-8')
                freeze_json(output / 'semantic_composition_receipt.json', composition)
        if eis_pciv_plan and plan == 'pciv_quotient_obligation_v1':
            pciv_quotient_receipt = build_pciv_quotient_artifact(sha(seed))
            responses['pciv_quotient_context'] = canonical(pciv_quotient_receipt).decode('utf-8')
            freeze_json(output / 'pciv_quotient_receipt.json', pciv_quotient_receipt)
        for index, stage in enumerate(stages):
            if charpoly_plan and stage['id'] == 'charpoly_repair' and charpoly_checks[-1]['accepted']:
                continue
            if charpoly_plan and stage['id'] == 'solve' and charpoly_plan['checked'] and not charpoly_checks[-1]['accepted']:
                status = 'certificate_refused'
                break
            if plan == 'eis_two_signal_charpoly_v1' and stage['id'] == 'solve' and eis_pciv_plan['checked'] and (not eis_pciv_checks or not eis_pciv_checks[-1]['accepted']):
                status = 'eis_two_signal_refused'
                break
            if matrix_plan and stage['id'] == 'matrix_repair' and matrix_checks[-1]['accepted']:
                continue
            if matrix_plan and stage['id'] == 'solve' and matrix_plan['checked'] and not matrix_checks[-1]['accepted']:
                status = 'representation_refused'
                break
            # The seed is one exact, unchanged user message in every call.
            messages = [{'role': 'system', 'content': stage['instruction']}, {'role': 'user', 'content': seed_text}]
            if experiment:
                messages.append({'role': 'user', 'content': 'Frozen public contract:\n' + canonical(public_context(sha(seed))).decode('utf-8')})
            if charpoly_plan:
                material = charpoly_stage_request(plan, stage['id'], seed_text, sha(seed),
                    {name: json.loads(responses[name]) if name == 'charpoly_feedback' else responses[name]
                     for name in stage['visible_artifacts']})
                messages.append({'role': 'user', 'content': 'Public characteristic-polynomial input contract:\n' + canonical(material['public_context']).decode('utf-8')})
                for value in material['visible_artifacts'].values():
                    messages.append({'role': 'user', 'content': 'Untrusted previous candidate follows. It is not the answer key.\n' + canonical(value).decode('utf-8')})
            if eis_pciv_plan and stage['id'] == 'charpoly_propose':
                messages.append({'role': 'user', 'content': 'Public affine Hamiltonian contract:\n' + canonical(public_charpoly_input_context(sha(seed))).decode('utf-8')})
            if matrix_plan and stage['id'] != 'solve':
                messages.append({'role': 'user', 'content': 'Public representation contract:\n' + canonical(matrix_contract(sha(seed))).decode('utf-8')})
            if not charpoly_plan:
                for visible in stage['visible_artifacts']:
                    messages.append({'role': 'user', 'content': 'Untrusted previous candidate follows. It is not the answer key.\n' + responses[visible]})
            request = {'messages': messages, 'max_output_tokens': min(max_output_tokens, stage['max_output_tokens']), 'tools': [], 'retries': 0}
            request_hash = sha(canonical(request))
            call_id = f'{run_id}:call:{index}'
            quote = provider.upper_quote(request)
            ledger.reserve(run_id, call_id, request_hash, quote)
            record = {'call_id': call_id, 'stage_id': stage['id'], 'request': request, 'request_sha256': request_hash, 'quote_microusd': quote,
                      'visible_artifact_sha256s': {name: sha(responses[name].encode('utf-8')) for name in stage['visible_artifacts']}}
            if not offline:
                record['provider_request_evidence'] = provider.request_evidence()
            records.append(record)
            freeze_json(output / 'calls' / f'{index:03d}.request.json', record)
            call_started = time.perf_counter()
            try:
                reply = provider.complete(request)
                record['provider_duration_seconds'] = time.perf_counter() - call_started
                record['actual_microusd'] = reply.actual_microusd
                # Persist a known charge before text/usage validation or artifact
                # I/O can fail. The raw provider digest binds malformed replies too.
                billing_digest = (reply.provider_evidence or {}).get('response_sha256')
                if billing_digest is None:
                    billing_digest = sha(str(reply.text).encode('utf-8', errors='backslashreplace'))
                record['billing_response_sha256'] = billing_digest
                if reply.actual_microusd is None:
                    ledger.mark_uncertain(call_id)
                else:
                    ledger.settle(call_id, reply.actual_microusd, billing_digest)
                if not isinstance(reply.text, str):
                    raise ValueError('Provider text missing')
                record.update(response_text=reply.text, response_sha256=sha(reply.text.encode()), actual_microusd=reply.actual_microusd,
                              input_tokens=token_value(reply.input_tokens), output_tokens=token_value(reply.output_tokens),
                              reasoning_tokens=token_value(reply.reasoning_tokens), finish_reason=reply.finish_reason,
                              provider_request_id=reply.provider_request_id, provider_evidence=reply.provider_evidence,
                              accounting_error=reply.accounting_error)
                freeze_json(output / 'calls' / f'{index:03d}.response.json', record)
                if reply.actual_microusd is None:
                    status = 'incomplete_accounting'
                    break
                if reply.accounting_error:
                    ledger.block(run_id)
                    status = 'provider_or_accounting_failure'
                    break
                previous = reply.text
                responses[stage['id']] = reply.text
                if charpoly_plan and stage['id'] != 'solve':
                    try:
                        checked = check_charpoly(reply.text, sha(seed))
                    except Exception as exc:
                        # Billing is already settled. A host failure must not be
                        # relabeled as an unknown provider charge or model error.
                        checked = {'accepted': False, 'status': 'INFRASTRUCTURE_REFUSAL',
                                   'solver_context': reply.text, 'feedback': {},
                                   'reason': type(exc).__name__}
                    charpoly_checks.append({'stage_id': stage['id'], **checked})
                    freeze_json(output / 'calls' / f'{index:03d}.charpoly_check.json', charpoly_checks[-1])
                    responses['charpoly_context'] = checked['solver_context']
                    responses['charpoly_feedback'] = canonical(checked['feedback']).decode('utf-8')
                    if checked['status'] == 'INFRASTRUCTURE_REFUSAL':
                        status = 'host_infrastructure_failure'
                        break
                if matrix_plan and stage['id'] != 'solve':
                    checked = check_artifact(reply.text, sha(seed))
                    matrix_checks.append({'stage_id': stage['id'], **checked})
                    freeze_json(output / 'calls' / f'{index:03d}.matrix_check.json', matrix_checks[-1])
                    # Identical valid artifacts have identical solver context in
                    # the gated and ungated arms; no acceptance label is supplied.
                    candidate = checked.get('canonical_candidate')
                    responses['matrix_context'] = canonical(candidate).decode('utf-8') if candidate is not None else reply.text
                    responses['matrix_feedback'] = canonical({'errors': checked['errors'], 'mismatches': checked['mismatches']}).decode('utf-8')
                if plan == 'eis_two_signal_charpoly_v1' and stage['id'] != 'solve':
                    try:
                        checked = evaluate_eis_charpoly_stage(reply.text, sha(seed))
                    except Exception as exc:
                        checked = {'accepted': False, 'status': 'INFRASTRUCTURE_REFUSAL',
                                   'eis_charpoly_context': None, 'refusal_code': type(exc).__name__,
                                   'final_answer_certified': False}
                    eis_pciv_checks.append({'stage_id': stage['id'], **checked})
                    freeze_json(output / 'calls' / f'{index:03d}.eis_charpoly_check.json', eis_pciv_checks[-1])
                    if checked.get('status') == 'INFRASTRUCTURE_REFUSAL':
                        status = 'host_infrastructure_failure'
                        break
                    if checked['accepted'] and checked.get('eis_charpoly_context') is not None:
                        responses['eis_charpoly_context'] = checked['eis_charpoly_context']
            except Exception as exc:
                record.setdefault('provider_duration_seconds', time.perf_counter() - call_started)
                record.update(error_class=type(exc).__name__, error=str(exc)[:300])
                # An overrun is already durably settled; other errors keep their hold.
                try:
                    ledger.mark_uncertain(call_id)
                except BudgetError:
                    ledger.block(run_id)
                status = 'provider_or_accounting_failure'
                break
    except Exception as exc:
        status = 'admission_failure'
        records.append({'error_class': type(exc).__name__, 'error': str(exc)[:300], 'dispatched': False})
    finally:
        summary = ledger.summary(run_id)
        ledger.close()
    host_receipt = None
    if charpoly_plan:
        previous = responses.get('solve')  # A certificate alone is never a final answer.
        accepted = bool(charpoly_checks and charpoly_checks[-1]['accepted'])
        host_receipt = {'checker': 'registered_qm_native_charpoly_v1',
                        'status': 'HOST_INFRASTRUCTURE_FAILURE' if status == 'host_infrastructure_failure' else 'CHECKED_INTERMEDIATE_ONLY',
                        'checked_gate': charpoly_plan['checked'], 'certificate_accepted': accepted,
                        'native_preflight': charpoly_custody, 'stage_checks': charpoly_checks,
                        'artifact_errors': {} if accepted else {'charpoly': 'UNACCEPTED_OR_MISSING'},
                        'claims': [{'status': 'EXACT_INTERMEDIATE_CHARPOLY_IDENTITY'}] if accepted else [],
                        'final_answer_certified': False, 'all_requested_obligations_remain_uncertified': True,
                        'scope': charpoly_plan['scope']}
        freeze_json(output / 'host_checks.json', host_receipt)
    if section_plan:
        assembled = assemble_sections(responses)
        previous = assembled['answer_text']
        host_receipt = {key: value for key, value in assembled.items() if key != 'answer_text'}
        host_receipt['artifact_errors'] = {
            name: 'SECTION_NOT_DELIVERED' for name in
            assembled['missing_stage_ids'] + assembled['empty_stage_ids']}
        host_receipt['claims'] = []
        host_receipt['all_requested_obligations_remain_uncertified'] = True
        if not assembled['all_sections_nonempty'] and status in ('completed', 'offline_fixture_completed'):
            status = 'section_delivery_incomplete'
        freeze_json(output / 'host_checks.json', host_receipt)
    if matrix_plan:
        previous = responses.get('solve')  # A matrix alone is never a final answer.
        accepted = bool(matrix_checks and matrix_checks[-1]['accepted'])
        host_receipt = {'checker': 'public_affine_hamiltonian_v1', 'checked_gate': matrix_plan['checked'],
                        'host_derived_matrix_control': matrix_plan['host_matrix'],
                        'representation_accepted': accepted, 'stage_checks': matrix_checks,
                        'artifact_errors': {} if accepted else {'matrix': 'UNACCEPTED_OR_MISSING'},
                        'claims': [{'status': 'EXACT_AFFINE_HAMILTONIAN_MATCH'}] if accepted else [],
                        'all_requested_obligations_remain_uncertified': True,
                        'scope': matrix_plan['scope']}
        freeze_json(output / 'host_checks.json', host_receipt)
    if host_charpoly_plan:
        previous = responses.get('solve')
        claims = []
        if host_charpoly_plan.get('host_matrix'):
            claims.append({'status': 'EXACT_AFFINE_HAMILTONIAN_MATCH'})
        charpoly_accepted = bool(charpoly_verification and charpoly_verification['status'] == 'CERTIFIED_IDENTITY')
        if charpoly_accepted:
            claims.append({'status': 'EXACT_INTERMEDIATE_CHARPOLY_IDENTITY'})  # receipt in charpoly_verification
        if composition_verified:
            claims.append({'status': 'TYPED_OPERADIC_COMPOSITION_VERIFIED'})
        accepted_matrix = bool(matrix_checks and matrix_checks[-1]['accepted']) if host_charpoly_plan.get('host_matrix') else False
        host_receipt = {
            'checker': 'registered_qm_host_charpoly_v1' if host_charpoly_plan.get('host_charpoly') else (
                'public_affine_hamiltonian_v1' if host_charpoly_plan.get('host_matrix') else 'coverage_first_direct_baseline_v1'
            ),
            'checked_gate': host_charpoly_plan['checked'],
            'host_derived_matrix': host_charpoly_plan.get('host_matrix', False),
            'host_derived_charpoly': host_charpoly_plan.get('host_charpoly', False),
            'semantic_composition': host_charpoly_plan.get('semantic_composition', False),
            'representation_accepted': accepted_matrix,
            'certificate_accepted': charpoly_accepted,
            'charpoly_verification': charpoly_verification,
            'operadic_associativity_verified': composition_verified,
            'grid_points_verified': charpoly_verification['grid_points_verified'] if charpoly_accepted else 0,
            'stage_checks': matrix_checks,
            'artifact_errors': {} if (not host_charpoly_plan['checked'] or accepted_matrix) else {'matrix': 'UNACCEPTED_OR_MISSING'},
            'claims': claims,
            'final_answer_certified': False,
            'all_requested_obligations_remain_uncertified': True,
            'scope': host_charpoly_plan['scope']
        }
        freeze_json(output / 'host_checks.json', host_receipt)
    if eis_pciv_plan:
        previous = responses.get('solve')
        if plan == 'eis_two_signal_charpoly_v1':
            accepted = bool(eis_pciv_checks and eis_pciv_checks[-1]['accepted'])
            host_receipt = {
                'checker': 'eis_two_signal_charpoly_v1',
                'status': 'HOST_INFRASTRUCTURE_FAILURE' if status == 'host_infrastructure_failure' else 'CHECKED_INTERMEDIATE_ONLY',
                'checked_gate': eis_pciv_plan['checked'],
                'certificate_accepted': accepted,
                'stage_checks': eis_pciv_checks,
                'artifact_errors': {} if accepted else {'charpoly': 'EIS_TWO_SIGNAL_REFUSED_OR_MISSING'},
                'claims': [{'status': 'EXACT_INTERMEDIATE_CHARPOLY_IDENTITY_TWO_SIGNAL_REGULATED'}] if accepted else [],
                'final_answer_certified': False,
                'all_requested_obligations_remain_uncertified': True,
                'scope': eis_pciv_plan['scope'],
            }
        else:
            host_receipt = {
                'checker': 'pciv_operational_quotient_v1',
                'status': 'PRE_DISPATCH_QUOTIENT_AND_SEED_FENCE_ONLY',
                'checked_gate': eis_pciv_plan['checked'],
                'quotient_verified': pciv_quotient_receipt is not None and pciv_quotient_receipt['protected_seed_fence']['verified_byte_identical'],
                'surviving_representative_count': pciv_quotient_receipt['surviving_representative_count'] if pciv_quotient_receipt else 0,
                'collapsed_duplicate_count': pciv_quotient_receipt['collapsed_duplicate_count'] if pciv_quotient_receipt else 0,
                'stage_checks': [],
                'artifact_errors': {},
                'claims': [{'status': 'PCIV_OPERATIONAL_QUOTIENT_AND_SEED_FENCE_VERIFIED'}] if pciv_quotient_receipt else [],
                'final_answer_certified': False,
                'all_requested_obligations_remain_uncertified': True,
                'scope': eis_pciv_plan['scope'],
            }
        freeze_json(output / 'host_checks.json', host_receipt)
    if experiment:
        candidate_text = responses.get('solve')
        panel_text = panel_for(plan, responses, sha(seed), canonical)
        # A critic output is evidence only and can never become the answer.
        previous = candidate_text
        try:
            host_receipt, previous = check_panel(candidate_text, panel_text, sha(seed))
            host_receipt['visibility'] = {
                'mode': experiment['visibility'],
                'visible_artifacts_by_stage': {stage['id']: stage['visible_artifacts'] for stage in stages},
                'solver_artifact_withheld_from_challenger': experiment['visibility'] == 'blind',
                'scope': 'Broker request visibility only; no claim of statistical error independence or provider-side isolation.',
            }
            freeze_json(output / 'host_checks.json', host_receipt)
            if panel_text is not None:
                freeze_json(output / 'panel_artifact.json', {'text': panel_text, 'sha256': sha(panel_text.encode('utf-8'))})
            if host_receipt['artifact_errors'] and status in ('completed', 'offline_fixture_completed'):
                status = 'artifact_validation_failure'
        except Exception as exc:
            host_receipt = {'status': 'HOST_INFRASTRUCTURE_FAILURE', 'error_class': type(exc).__name__}
            status = 'host_infrastructure_failure' if status in ('completed', 'offline_fixture_completed') else status
    wall = time.perf_counter() - started
    def total(field):
        values = [r.get(field) for r in records if 'request' in r]
        return sum(values) if values and all(v is not None for v in values) else None
    receipt = {'schema_version': '1.0', 'run_id': run_id, 'plan': plan, 'provider': provider.name,
               'status': status, 'offline': offline, 'seed_sha256': sha(seed),
               'answer_text': previous, 'answer_sha256': sha(previous.encode()) if previous is not None else None,
               'accuracy_score': None, 'accuracy_status': 'unscored_no_evaluator_feedback',
               'wall_time_seconds': wall, 'sum_provider_duration_seconds': sum(r.get('provider_duration_seconds', 0) for r in records),
               'input_tokens': total('input_tokens'), 'output_tokens': total('output_tokens'), 'reasoning_tokens': total('reasoning_tokens'),
               'budget': summary, 'calls': records,
               'host_checks': host_receipt,
               'plan_sha256': sha(canonical(PLANS[plan])),
               'implementation_sha256': {name: sha((HERE / name).read_bytes()) for name in
                                         ('reference_runner.py', 'budget_ledger.py', 'campaign_ledger.py', 'openrouter_provider.py',
                                          'rational_panel.py', 'rational_workflows.py', 'hamiltonian_artifact.py', 'hamiltonian_workflows.py',
                                          'section_workflows.py', 'charpoly_workflows.py', 'qm_native_charpoly.py', 'native_sidecar.py')},
               'scope': 'Orchestration/checker fixture only. No live model performance observation.' if offline else
                        'One frozen-seed provider run. Cost bound is conditional on recorded provider premises; accuracy requires independent post-freeze review.'}
    if charpoly_plan:
        receipt['implementation_sha256'].update({name: sha((HERE / name).read_bytes())
                                                 for name in charpoly_plan['source_pins']})
    if host_charpoly_plan:
        from source_custody import pin_path
        receipt['implementation_sha256'].update({name: sha(pin_path(name).read_bytes())
                                                 for name in host_charpoly_plan['source_pins']})
    if eis_pciv_plan:
        from source_custody import pin_path
        receipt['implementation_sha256'].update({name: sha(pin_path(name).read_bytes())
                                                 for name in eis_pciv_plan['source_pins']})
    receipt_hash = freeze_json(output / 'run.json', receipt)
    (output / 'run.sha256').write_text(receipt_hash + '\n', encoding='ascii')
    if not offline:
        live_admission.finish(run_id, receipt, receipt_hash)
    return receipt

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', choices=PLANS, default='direct')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    spec = (EXPERIMENTS.get(args.plan) or MATRIX_PLANS.get(args.plan) or SECTION_PLANS.get(args.plan) or
            CHARPOLY_PLANS.get(args.plan) or HOST_CHARPOLY_PLANS.get(args.plan) or EIS_PCIV_PLANS.get(args.plan))
    count = len(spec['stages']) if spec else len(PLANS[args.plan])
    receipt = run(args.plan, OfflineTape(['Synthetic fixture; no QM answer supplied.'] * count), args.output, args.run_id)
    print(json.dumps({k: receipt[k] for k in ('run_id', 'status', 'accuracy_status', 'offline')}))
