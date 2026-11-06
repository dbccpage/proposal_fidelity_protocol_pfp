"""Independent counterexamples to the original release's false certificates."""
import copy
import hashlib
import itertools
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from certificate_gate import BqnfCertificateGate
from fock_path_enumerator import compute_path_weight_3hop, verify_fock_path_proposition
from run_adversarial_debate_benchmark import (
    TRACE_FILE,
    load_records,
    run_benchmark,
    summarize_records,
)
from symbol_game_governor import (
    ConstraintGraph,
    Edge,
    Phi1Certificate,
    SymbolGameGovernor,
    canonical_json_bytes,
    compute_exact_phi_1,
    verify_phi_1_certificate,
)


def test_degenerate_multicycle_dual_is_feasible():
    vertices = ('0', '1', '2', '3')
    edges = (('0','1',1), ('0','3',1), ('1','2',3), ('1','3',1), ('2','3',2))
    claims = dict(zip(((u,v) for u,v,_ in edges), map(Fraction, (2,2,1,0,-2))))
    cert = compute_exact_phi_1(vertices, edges, claims)
    assert cert.phi_1 == 2
    assert verify_phi_1_certificate(vertices, edges, claims, cert)
    old = Phi1Certificate(Fraction(2), cert.primal_potentials,
        {('0','1'):Fraction(-2), ('0','3'):Fraction(2), ('1','2'):Fraction(-2), ('1','3'):Fraction(0), ('2','3'):Fraction(-2)}, Fraction(0))
    assert not verify_phi_1_certificate(vertices, edges, claims, old)


def test_small_rational_cycles_against_independent_potential_grid():
    vertices = ('a','b','c','isolated')
    edges = (('a','b',1), ('b','c',2), ('c','a',3))
    for values in itertools.product((Fraction(-1,2), Fraction(0), Fraction(1,2)), repeat=3):
        claims = dict(zip(((u,v) for u,v,_ in edges), values))
        cert = compute_exact_phi_1(vertices, edges, claims)
        grid = [Fraction(i,2) for i in range(-3,4)]
        best = min(abs(values[0]-b) + 2*abs(values[1]-(c-b)) + 3*abs(values[2]+c) for b in grid for c in grid)
        assert cert.phi_1 == best
        assert verify_phi_1_certificate(vertices, edges, claims, cert)


@pytest.mark.parametrize('vertices,edges', [
    (('a','a'),()), (('a','b'),(Edge('a','b'), Edge('a','b'))),
])
def test_ambiguous_carriers_rejected(vertices, edges):
    with pytest.raises(ValueError):
        ConstraintGraph(vertices, edges)


def test_foreign_claim_cannot_satisfy_carrier_completeness():
    graph = ConstraintGraph(('a','b'), (Edge('a','b'),))
    with pytest.raises(ValueError):
        SymbolGameGovernor(graph, {('x','y'):0})


def test_retract_restores_state_and_retains_append_only_evidence():
    gov = SymbolGameGovernor(ConstraintGraph(('a','b'), (Edge('a','b'),)), {('a','b'):1})
    gov.execute_move('CUT', {'potentials':{'b':1}})
    gov.execute_move('ASSERT', {'u':'a','v':'b','value':7})
    before = copy.deepcopy(gov.events)
    out = gov.execute_move('RETRACT', {'target_turn':1})
    assert out.admitted and out.defect == 0
    assert gov.claims['a','b'] == 1 and gov.section['b'] == 1
    assert gov.events[:2] == before and len(gov.history) == 3
    assert gov.execute_move('VERIFY', {}).admitted
    assert not gov.execute_move('RETRACT', {'target_turn':999}).admitted
    assert gov.execute_move('RETRACT', {'target_turn':0}).admitted
    assert gov.section['b'] == 0 and gov.claims['a','b'] == 1


def test_json_is_parseable_and_hash_chain_binds_genesis_and_outcomes():
    assert json.loads(canonical_json_bytes({'r':Fraction(1,3)})) == {'r':'1/3'}
    with pytest.raises(ValueError):
        canonical_json_bytes({'r':float('nan')})
    graph = ConstraintGraph(('a','b'), (Edge('a','b'),))
    first = SymbolGameGovernor(graph, {('a','b'):1})
    second = SymbolGameGovernor(graph, {('a','b'):2})
    assert first._hash_chain != second._hash_chain
    prior = first._hash_chain
    payload = {'potentials': {'b':Fraction(1)}}
    out = first.execute_move('CUT', payload)
    payload['potentials']['b'] = 9
    assert first.events[0]['payload']['potentials']['b'] == 1
    assert first.events[0]['prior_hash'] == prior
    assert hashlib.sha256(canonical_json_bytes(first.events[0])).hexdigest() == out.evidence_sha256


@pytest.mark.parametrize('name', ['repulsive_hubbard','non_stoquastic','unknown'])
def test_positivity_route_name_does_not_certify(name):
    assert not BqnfCertificateGate(name).verify_sign_free({'route':'positivity'}).valid
    assert not BqnfCertificateGate(name, {'hamiltonian_matrix':[[0,1],[1,0]]}).verify_sign_free({'route':'positivity'}).valid


def test_keyword_stuffing_and_negated_laws_do_not_certify():
    witness = {'type':'involution','mapping':'swap fixed pair', 'proof':'not an involution; no sign reversal; no equal weight magnitude'}
    assert not BqnfCertificateGate('unknown').verify_sign_free({'xi_witness':witness}).valid


def test_explicit_pairing_with_positive_residue():
    gate = BqnfCertificateGate('toy', {'configuration_weights':{'n':'-1/3','p':'1/3','residue':2}})
    result = gate.verify_sign_free({'representation':'finite_signed', 'xi_witness':{'pairs':{'n':'p','p':'n'}}})
    assert result.valid and result.status == 'ExactCancellation'
    assert all(result.condition_checks.values())


@pytest.mark.parametrize('weights,pairs,failed', [
    ({'n':-1,'p':1}, {'n':'n','p':'p'}, 'fixed_point_free'),
    ({'n':-1,'p':2}, {'n':'p','p':'n'}, 'weight_preserving'),
    ({'n':-1,'p':-1}, {'n':'p','p':'n'}, 'sign_reversing'),
    ({'n':-1,'p':1,'unpaired':-2}, {'n':'p','p':'n'}, 'negative_coverage'),
    ({'a':-1,'b':1,'c':-1}, {'a':'b','b':'c','c':'a'}, 'involution_law'),
])
def test_failed_pairing_laws_refused(weights,pairs,failed):
    result = BqnfCertificateGate('toy', {'configuration_weights':weights}).verify_sign_free({'representation':'finite_signed','xi_witness':{'pairs':pairs}})
    assert not result.valid and not result.condition_checks[failed]


def test_proposer_cannot_supply_own_weights_or_out_of_carrier_pair():
    move = {'representation':'finite_signed','configuration_weights':{'n':-1,'p':1},'xi_witness':{'pairs':{'n':'p','p':'n'}}}
    assert not BqnfCertificateGate('toy').verify_sign_free(move).valid
    gate = BqnfCertificateGate('toy', {'configuration_weights':{'n':-1,'p':1}})
    move['xi_witness']['pairs']['n'] = 'absent'
    assert not gate.verify_sign_free(move).valid


@pytest.mark.parametrize('override', [{'mu_down':1}, {'h_down':[[0,-2],[-2,0]]}, {'h_up':[[0,1],[0,0]]}, {'U':2}])
def test_determinant_squaring_checks_its_hypotheses(override):
    params = {'U':-2,'h_up':[[0,-1],[-1,0]],'h_down':[[0,-1],[-1,0]],'mu_up':0,'mu_down':0}
    gate = BqnfCertificateGate('attractive_hubbard', {**params, **override})
    assert not gate.verify_sign_free({'representation':'continuous_hs','route':'determinant_squaring'}).valid


def test_missing_U_is_not_free_fermion_certificate():
    assert not BqnfCertificateGate('free_fermion').verify_sign_free({'representation':'determinant'}).valid


def test_missing_or_fake_odd_cycle_refused():
    gate = BqnfCertificateGate('c3_triangular', {'bonds':[(0,1),(1,2)]})
    assert not gate.verify_proposal_item({'move_type':'OPEN_SIGN_OBSTRUCTION','obstruction_witness':{'type':'alternating_site_gauge','cycle':[0,1,2]}})[1]


def test_nonconstant_integral_matches_closed_form():
    beta = .25
    expected = beta**2/4 - beta/4 + (1-math.exp(-2*beta))/8
    assert math.isclose(compute_path_weight_3hop((0,2,0),1,beta), expected, rel_tol=1e-12)
    assert math.isclose(compute_path_weight_3hop((4,4,4),-1,beta), -math.exp(-1)/384, rel_tol=1e-14)


def test_short_path_sectors_are_excluded_too():
    result = verify_fock_path_proposition()
    assert result['one_hop_paths'] == 0
    assert min(result['zero_hop_lower_bound'],result['two_hop_lower_bound']) > result['abs_target_weight']
    assert result['min_positive_3hop_weight'] >= result['analytic_positive_3hop_lower_bound'] - 1e-16


def test_metrics_recomputed_from_historical_labels():
    rows = load_records()
    result = summarize_records(rows)
    assert (result['adversary_true_positives'],result['adversary_false_positives'],result['adversary_true_negatives'],result['adversary_false_negatives']) == (6,2,2,0)
    assert result['adversary_challenge_precision'] == .75
    rows[0]['adversary_critique']['adversary_verdict'] = 'CONCUR'
    changed = summarize_records(rows)
    assert changed['adversary_false_positives'] == 1 and changed['adversary_true_negatives'] == 3
    assert changed['adversary_classification_accuracy'] == .9


@pytest.mark.parametrize('case', ['missing','empty','duplicate','partial'])
def test_replay_refuses_incomplete_inputs(tmp_path, case):
    path = tmp_path/'trace.jsonl'
    lines = TRACE_FILE.read_text().splitlines()
    if case != 'missing':
        path.write_text('' if case=='empty' else '\n'.join(lines + [lines[0]] if case=='duplicate' else lines[:-1]))
    with pytest.raises((ValueError, FileNotFoundError)):
        load_records(path)


def test_live_mode_never_fabricates_execution():
    with pytest.raises(ValueError, match='not implemented'):
        run_benchmark(live=True)


@pytest.mark.parametrize('move,payload', [('CUT', {'potentials':{'outside':1}}), ('CUT', {'potentials':None}), ('ASSERT', {'u':'a','v':'b','value':'nan'}), ('CUT', {'potentials':{'b':float('nan')}}), ('BOGUS', {}), ('CUT', [])])
def test_malformed_governor_moves_refuse_without_state_loss(move,payload):
    gov = SymbolGameGovernor(ConstraintGraph(('a','b'), (Edge('a','b'),)), {('a','b'):1})
    outcome = gov.execute_move(move,payload)
    assert not outcome.admitted
    assert gov.section == {'a':0,'b':0} and gov.claims['a','b'] == 1
    assert len(gov.events) == len(gov.history) == 1
