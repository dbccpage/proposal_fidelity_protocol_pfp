"""Persist two complete source reads and independent finite packet controls."""
import hashlib, json, runpy
from pathlib import Path

H = Path(__file__).resolve().parent
P = 'additional_rust_quantum_probability_remaining'
np = H / (P + '_notes.json')
n = json.loads(np.read_text())
n['28'] = {
    'assessment': 'Full565-line hard_invariants source read. Production13-97 is a generic count scaffold; cfg(test)99-538 contains eight concrete GF(2), quotient, capacity, logical-witness, authority-string and declaration regression groups. The cases explicitly require d1*d0=0 on five stock complexes, distinguish exact/closed-residual/open examples, exercise a computed torus distance, require syndrome-zero plus nontrivial quotient for LGGR, and refuse incomplete packets. The later count-scaffold tests are separate from the mathematical owner.',
    'limitations': [
        'No original Rust test execution in this pass. Full test-source review is distinct from a fresh passing receipt.',
        'Finite named examples and selected malformed declarations do not establish a universal invariant or mutation-detection completeness.',
        'The authority_effect=None assertions verify emitted strings in those examples; they are not an access-control or unforgeability proof.',
        'The capacity cases inherit the selected-candidate distance premise discussed in RQPR-F008; the raw-carrier boundary inherits RQPR-F009.'
    ]
}
n['36'] = {
    'assessment': 'Full960-line packet_wall source read. The GF(2) path validates boundary composition, calls the quotient classifier and emits authority None; the optional declared distance only selects a capacity label. The count path validates declaration presence, positive dimensions/window, unique event/action IDs, pair memberships, coordinates and binary annotations, then removes every mapped defect and computes an OR visibility indicator. A separate diagnostic matrix packet checks field presence and lengths before classification. Tests cover stock torus/open/incomplete packets, ordinary count examples, one capacity label and diagnostic refusals.',
    'limitations': [
        'No native execution. Independent controls reproduce only the explicitly cited branches, not the Rust implementation as a whole.',
        'Public DefectEvent.weight is trusted rather than recomputed, allowing the capacity label to disagree with the actual residual weight (RQPR-F012).',
        'The distance is caller-declared; proposed_repair is bookkeeping, not an executed or verified repair. A label for one selected residual is not an optimal decoder or physical no-go theorem.',
        'The count d0 relation permits one action to name multiple distinct defects. This may model a multi-target action, but mu_repair_count counts actions and cannot bound removed defects without an additional per-action capacity premise.',
        'correction_window is only checked positive; cycle separation is not constrained by it. The logical indicator is OR over caller annotations, not a derived GF(2) pairing. Carrier/proxy names are nonempty strings, not semantic validators.',
        'The reason saying repair image saturated means only the supplied relation has been exhausted; no search over all permitted repairs occurs. Opportunity multiplication saturates. These are finite declared bookkeeping diagnostics with no physical calibration or hash-bound certificate.'
    ]
}
np.write_text(json.dumps(n, indent=2) + '\n')
runpy.run_path(str(H / (P + '_checkpoint.py')))
rp = H / (P + '.json')
r = json.loads(rp.read_text())
scope = json.loads((H / (P + '_scope.json')).read_text())['files']
def ev(i, a, b):
    f = scope[i]
    return {'path': f['path'], 'sha256': f['sha256'], 'lines': [a, b]}
finding = {
    'id': 'RQPR-F012', 'severity': 'medium',
    'title': 'Caller-supplied defect weight can hide a capacity-wall label',
    'finding': 'DefectEvent exposes residual and weight independently. terminalize_packet classifies residual but passes the stored weight to classify_wall_terminal and copies it to the receipt. For the torus logical residual of true Hamming weight2 and declared distance2 (radius0), the complete constructor yields CapacityWallHit; constructing the same public packet with weight0 retains ClosedResidual and reports residual_weight0. The quotient classification is unchanged, but the capacity decision and receipt weight are no longer bound to the residual.',
    'evidence': [ev(36, 89, 128), ev(36, 184, 220), ev(36, 251, 294)],
    'recommended_action': 'Recompute the weight from the admitted GF(2) residual, or reject a supplied weight mismatch. Add a regression comparing constructor-generated and directly deserialized packets.',
    'validation': 'Independent exact branch substitution and existing fully read torus fixture/classifier definitions; no native execution.'
}
r['findings'] = [x for x in r['findings'] if x['id'] != finding['id']] + [finding]
claim = {
    'id': 'RQPR-C015',
    'claim': 'Packet-wall terminalization implements finite declared classification and bookkeeping. Its count image may remove multiple defect IDs per action, and neither that image nor caller-supplied distance establishes an optimal repair capacity, a linear logical witness, or a physical obstruction.',
    'evidence': [ev(36, 223, 310), ev(36, 330, 380), ev(36, 399, 582), ev(28, 99, 538)],
    'dependencies': ['Admitted GF(2) carrier and boundary composition', 'Caller-supplied distance and finite repair relation', 'Caller-supplied binary visibility annotations'],
    'limitations': ['The count relation has no per-action defect-capacity bound or time-window enforcement.', 'The regression battery supplies selected finite checks, not universal completeness or a fresh native replay.', 'All emitted authority effects remain None; mathematical labels alone confer no execution authority.']
}
r['claims'] = [x for x in r['claims'] if x['id'] != claim['id']] + [claim]
wall = lambda status, weight, radius: 'CapacityWallHit' if status == 'ClosedResidual' and weight > radius else status
assert wall('ClosedResidual', 2, 0) == 'CapacityWallHit'
assert wall('ClosedResidual', 0, 0) == 'ClosedResidual'
actions = ['a0']; defects = ['e0', 'e1']; relation = [('a0', 'e0'), ('a0', 'e1')]
assert len({d for _, d in relation}) == len(relation)
assert all(a in actions and d in defects for a, d in relation)
residual = [d for d in defects if d not in {d for _, d in relation}]
assert residual == [] and len(actions) == 1 and len(defects) == 2
cp = H / (P + '_packet_controls.json')
cp.write_text(json.dumps({
    'method': 'Independent finite reconstruction of cited source branch logic, not Rust execution', 'passed': True,
    'forged_weight': {'classifier_status': 'ClosedResidual', 'true_weight': 2, 'declared_distance': 2, 'radius': 0, 'honest_terminal': wall('ClosedResidual', 2, 0), 'forged_weight': 0, 'forged_terminal': wall('ClosedResidual', 0, 0)},
    'count_multi_target_action': {'actions': actions, 'defects': defects, 'relation': relation, 'map_admission_checks_pass': True, 'terminal': 'Absorbed', 'lambda_proj_count': 2, 'mu_repair_count': 1, 'interpretation': 'An admitted multi-target relation; no unit-capacity assumption is enforced. This is a limit on inference from rates, not a claim that multi-target repair is physically impossible.'}
}, indent=2) + '\n')
r['validation'] = [x for x in r['validation'] if x.get('id') != 'RQPR-PACKET-CONTROLS'] + [{'id': 'RQPR-PACKET-CONTROLS', 'path': str(cp.relative_to(H.parents[1])).replace('\\', '/'), 'sha256': hashlib.sha256(cp.read_bytes()).hexdigest(), 'passed': True, 'native_execution': False}]
r['audit_state'] = 'frozen_while_awaiting_deepseek_self_critique_post_freeze_evaluation'
rp.write_text(json.dumps(r, indent=2) + '\n')
with (H / (P + '.md')).open('a', encoding='utf-8') as md:
    md.write('\n\n## Packet and invariant checkpoint\n\nCoverage is38/51 full source bodies,13pending. The complete hard-invariant test source supplies selected finite regressions, not a fresh execution receipt or universal proof. Packet terminalization trusts a separately supplied residual weight (RQPR-F012); an independent exact control shows that changing weight2 to0 suppresses the capacity-wall label for an otherwise unchanged closed residual. A second control admits one action mapped to two defects, so the count-rate labels need an additional per-action capacity premise. The checkpoint is frozen while awaiting the DeepSeek self-critique run.\n')
print(json.dumps({'full': r['full_source_read_count'], 'remaining': len(r['remaining_work']), 'claims': len(r['claims']), 'findings': len(r['findings']), 'report_sha256': hashlib.sha256(rp.read_bytes()).hexdigest()}))
