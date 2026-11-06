"""PFP-shaped run records for a ladder run, compatible with the batch toolkit's P0 layout.

AuthorityEffect: None. Layout under dag/results/<NODE>/runs/<stamp>_ladder/ :

  .gitattributes, ladder_receipt.json            run-level receipt: policy, every provider call, spend
  p0/request.json                                 compiled packet of the first attempt
  p0/candidate.json  raw_response.json  host_check.json  operad_delta.yaml
                                                  the accepted (else best) attempt, in the stage-contract
                                                  envelope of dag/pfp/batch_tools/stages.py p0_missions
  p0/provider_calls.json                          the redacted call rows (also in the receipt)
  p0/attempts/<attempt>/{request.json,raw_response.txt,response.json,host_check.json,operad_delta.yaml}

Mission slots are written with mining_status PROPOSED_HOST_PARTIAL, never FILLED: FILLED needs a host
review of the contents (prepare_stage.py refuses P1 otherwise). The verified generators and relations
are therefore ready for that review and for the normal P1-P5 pipeline, which this module does not run.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from .llm_common import Redactor, json_bytes, sha256_bytes, utc_iso, write_new
from .verify import G_CODES, VerifyReport

SLOTS = ('slot_m1_layer0_ambient_carrier', 'slot_m2_layer1_forward_morphisms',
         'slot_m3_layer2_ideals_and_annihilators', 'slot_m4_tri_language_witness_anchors')
POLICY_NOTE = ('This run called external model providers; the receipt below lists every call. That differs from '
               'the historical batch policy "external_provider_calls: 0" (dag/pfp/batch_tools/selection.py); the '
               'difference is intentional and recorded here. Provider replies are untrusted proposals: only the '
               'host-verified entries in operad_delta.yaml count, and no theorem is accepted.')
GITATTRIBUTES = '*.json -text whitespace=cr-at-eol\n*.yaml -text whitespace=cr-at-eol\n*.txt -text whitespace=cr-at-eol\n'


def yaml_bytes(value) -> bytes:
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True, width=100).encode('utf-8')


def failure_entry(failure, entry_id, *, model, provider, tier, node_id) -> dict:
    return {'id': entry_id, 'class': failure.cls, 'claim_kind': failure.claim_kind, 'claim': failure.claim[:300],
            'evidence': failure.evidence[:300], 'decl_key': failure.decl_key, 'confidence': failure.confidence,
            'model': model, 'provider': provider, 'tier': tier, 'node_id': node_id}


def build_delta(report: VerifyReport, response, *, model, provider, tier, node_id, entry_ids: dict) -> dict:
    """Stage-contract operad_delta: verified positives plus the negatives of this attempt."""
    generators, relations = [], []
    for g in report.verified['generators']:
        generators.append({'id': g['id'], 'ordered_inputs': g['inputs'], 'output': g['output'], 'arity': g['arity'],
                           'carrier': g['carrier'], 'coefficient_ring': None, 'hypotheses': [],
                           'source_pins': [{'path': g['host_evidence']['path'], 'declaration': g['host_evidence']['decl'],
                                            'line': g['host_evidence']['line']}],
                           'semantic_predicate': 'UNREVIEWED: only the declaration\'s existence (and arity where readable) is host-verified',
                           'evidence_status': g['evidence_status'], 'host_evidence': g['host_evidence'],
                           'proposed_by': {'model': model, 'provider': provider, 'tier': tier}})
    for r in report.verified['relations']:
        relations.append({'id': r['id'], 'equation_or_predicate': r['statement'], 'typing_conditions': r['hypotheses'],
                          'source_pins': [{'path': r['host_evidence']['path'], 'declaration': r['host_evidence']['decl'],
                                           'line': r['host_evidence']['line']}],
                          'evidence_status': r['evidence_status'], 'scope': 'as stated; hypotheses not reviewed',
                          'host_evidence': r['host_evidence'], 'proposed_by': {'model': model, 'provider': provider, 'tier': tier}})
    checked = [{'outer_operation': c['outer'], 'input_slot': c['slot'], 'inner_operation': c['inner'],
                'colour_match': True, 'hypothesis_match': 'not checked', 'licensing_relations': [c['licensing_relation']],
                'evidence_status': c['evidence_status']} for c in report.verified['compositions']]
    failed, counter = [], []
    for failure in report.failures:
        row = failure_entry(failure, entry_ids.get(failure.pattern, ''), model=model, provider=provider, tier=tier, node_id=node_id)
        (counter if failure.entry_type == 'counterexample' else failed).append(row)
    obligations = list((response or {}).get('open_obligations', [])) if isinstance(response, dict) else []
    obligations += ['%s %s unverified: %s' % (u['kind'], u['id'], u['reason']) for u in report.unverifiable]
    obligations.append('Review the semantics of each verified generator and relation before marking any mission slot FILLED.')
    return {'add_or_refine_generators': generators, 'add_or_refine_relations': relations, 'checked_compositions': checked,
            'failed_compositions': failed, 'counterexamples': counter, 'open_obligations': obligations,
            'verified_numeric_claims': report.verified['numeric'], 'verified_lemma_statements': report.verified['lemmas']}


def mission_patch(delta: dict) -> dict:
    return {
        SLOTS[0]: {'mining_status': 'PROPOSED_HOST_PARTIAL', 'carrier': None, 'coefficient_ring': None,
                   'note': 'The ladder does not fill the carrier; generator carriers are model proposals.'},
        SLOTS[1]: {'mining_status': 'PROPOSED_HOST_PARTIAL',
                   'operations': [{'catalog_id': g['id'], 'inputs': g['ordered_inputs'], 'output': g['output'],
                                   'semantic_predicate': g['semantic_predicate']} for g in delta['add_or_refine_generators']],
                   'composition_plan': delta['checked_compositions']},
        SLOTS[2]: {'mining_status': 'PROPOSED_HOST_PARTIAL', 'algebraic_relations': delta['add_or_refine_relations'],
                   'rejection_predicates': [], 'negative_control_plan': [
                       'Near misses are recorded as open obligations; the P4 host check decides.']},
        SLOTS[3]: {'mining_status': 'PROPOSED_HOST_PARTIAL', 'certificate_predicates': [], 'anchors': [],
                   'unpaid_imports': delta['open_obligations']},
    }


def claim_boundary(report: VerifyReport) -> dict:
    return {'supports': ('%d host-verified declaration-grounded entries (existence, readable arity, source-consistent '
                         'numerals) and %d exact numeric recomputations proposed by a model' % (
                             len(report.verified['generators']) + len(report.verified['relations']), len(report.verified['numeric']))),
            'does_not_support': 'Any semantic correctness of a generator or relation, any theorem, or closure of the target.',
            'narrowest_claim': 'The named declarations exist where cited and the recomputed arithmetic holds.',
            'next_test': 'A host reviewer checks the semantics of the verified generators against their declarations, then P1 may start.'}


class RunWriter:
    def __init__(self, root, node_id, run_dir_name, redactor: Redactor):
        self.dir = Path(root) / 'dag' / 'results' / node_id / 'runs' / run_dir_name
        self.node_id, self.red = node_id, redactor
        write_new(self.dir / '.gitattributes', GITATTRIBUTES.encode('ascii'))

    def _json(self, relative, value):
        write_new(self.dir / relative, json_bytes(self.red.redact_obj(value)))

    def _yaml(self, relative, value):
        write_new(self.dir / relative, yaml_bytes(self.red.redact_obj(value)))

    def attempt(self, packet, aid, *, raw_text, response, report: VerifyReport, delta, host_check):
        base = 'p0/attempts/' + aid
        self._json(base + '/request.json', packet.as_request_json())
        write_new(self.dir / base / 'raw_response.txt', self.red.redact(raw_text or '').encode('utf-8'))
        self._json(base + '/response.json', response if response is not None else {'parsed': None})
        self._json(base + '/host_check.json', host_check)
        self._yaml(base + '/operad_delta.yaml', delta)

    def best(self, packet, aid, *, raw_text, response, delta, host_check, report, run_delta):
        binding = {'task_id': self.node_id, 'stage_id': 'P0_MINE_OPERAD', 'attempt_id': aid, 'input_sha256': packet.input_sha256}
        self._json('p0/request.json', packet.as_request_json())
        envelope = {**binding, 'status': 'ready_for_host_review' if host_check['status'] != 'incomplete' else 'incomplete',
                    'mission_patch': mission_patch(delta), 'source_checks': [], 'next_missing_dependency':
                    'Host review of the verified entries; semantic mining of the unverified claims',
                    'operad_delta': run_delta, 'claim_boundary': claim_boundary(report),
                    'execution': 'Provider reply from the LLM ladder; untrusted proposal, host-verified entries only.'}
        self._json('p0/candidate.json', envelope)
        self._json('p0/raw_response.json', {**binding, 'raw_text': raw_text, 'parsed': response})
        self._yaml('p0/operad_delta.yaml', run_delta)
        self._json('p0/host_check.json', {**binding, 'candidate_sha256': sha256_bytes((self.dir / 'p0/candidate.json').read_bytes()),
                                          **host_check, 'operad_delta': run_delta, 'claim_boundary': claim_boundary(report)})

    def receipt(self, receipt: dict, calls: list):
        self._json('p0/provider_calls.json', {'calls': calls})
        self._json('ladder_receipt.json', receipt)


def host_check_record(report: VerifyReport, *, accepted: bool, aid: str, model: str, partial: bool = False) -> dict:
    codes = sorted({G_CODES.get(f.cls, 'G3_WITNESS') for f in report.failures})
    if accepted:
        status = 'reviewed_for_next_step_pending_host_semantic_review'
    elif partial:
        status = 'partial_reviewed_pending_host_semantic_review'
    elif report.failures:
        status = 'repairable_candidate_defect'
    else:
        status = 'incomplete'
    return {'status': status, 'attempt_id': aid, 'model': model, 'bounded_failure_codes': codes,
            'predicate_results': {'verified_total': report.verified_total(), 'failed_total': report.failure_total(),
                                  'failure_rate': round(report.failure_rate(), 4), 'failures_by_class': report.by_class(),
                                  'unverifiable': len(report.unverifiable), 'lean': report.lean,
                                  'schema_errors': report.schema_errors[:5]},
            'checked_at_utc': utc_iso()}
