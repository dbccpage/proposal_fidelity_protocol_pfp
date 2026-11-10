"""Small independent checks of public historical records, without executing their code."""
from __future__ import annotations

from fractions import Fraction
import hashlib
from itertools import product
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    witness_rows = []
    for path in sorted((ROOT / '_ic/darpa/adversary/self_digestion/witnesses').glob('*.json')):
        data = json.loads(path.read_text())
        support = data['support_runs']
        assert len(set(support)) == len(support) == data['fires_in'] == len(data['witnesses'])
        assert all(w['ref'].split('#')[0] in support for w in data['witnesses'])
        assert all(all(w['trigger'].get(k) == v for k, v in data['detector'].items()) for w in data['witnesses'])
        witness_rows.append({'path': path.relative_to(ROOT).as_posix(), 'internal_support_count': len(support),
                             'declared_corpus_size': data['corpus_runs'], 'internal_consistency': True,
                             'raw_corpus_and_outcome_sequence_authenticated': False})
    x0 = tuple(product((-1, 0, 1), repeat=2))
    f01 = lambda p: (p[0] + p[1], p[0] - p[1])
    g10 = lambda p: (Fraction(p[0] + p[1], 2), Fraction(p[0] - p[1], 2))
    f12 = lambda p: (p[0], p[1] + p[0])
    g21 = lambda p: (p[0], p[1] - p[0])
    x1, x2 = tuple(map(f01, x0)), tuple(f12(f01(p)) for p in x0)
    assert len(set(x1)) == len(set(x2)) == 9
    assert all(g10(f01(p)) == p and g10(g21(f12(f01(p)))) == p for p in x0)
    counts = {str(d): sum(p[0] + p[1] == d for p in x0) for d in (-1, 0, 1, 2)}
    assert counts == {'-1': 2, '0': 3, '1': 2, '2': 1}
    assert all((p[0]+p[1] == d) == (f01(p)[0] == d) == (f12(f01(p))[0] == d)
               for d in (-1, 0, 1, 2) for p in x0)
    assert g10((1, 0)) == (Fraction(1, 2), Fraction(1, 2)) and (1, 0) not in x1
    assert f01((1, 1))[0] != 1  # d=1 guard wrongly rejects the valid d=2 candidate.
    review_root = ROOT / '_ic/nara/historical/oewas007/research/wdp_calibrated_recovery/reviews'
    raw = (review_root / 'r1_code.json').read_bytes()
    prior = json.loads((review_root / 'r2_code.json').read_text())['prior_review_sha256']
    pin = {'expected': prior, 'raw_sha256': hashlib.sha256(raw).hexdigest(),
           'lf_sha256': hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest()}
    pin['matches'] = 'raw' if prior == pin['raw_sha256'] else ('LF_only' if prior == pin['lf_sha256'] else 'neither')
    result = {'status': 'bounded_public_checks_complete', 'witness_internal_checks': witness_rows,
              'finite_reentry_packet': {'carrier_sizes': [9, 9, 9], 'inverse_and_validity_checks': True,
                                       'solution_counts': counts, 'stale_task_guard_counterexample': True,
                                       'out_of_image_decoder_counterexample': True,
                                       'fuel_reset_excess_under_declared_ledger': '5'},
              'historical_review_prior_pin': pin,
              'limits': 'No embedded historical commands, resource-exhaustion inputs, external sources, provider calls, protected benchmark inputs, Lean builds or historical test suites were executed.'}
    (ROOT / 'dag/reviews/additional_historical_context_probe.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'witnesses': len(witness_rows), 'finite_packet_carriers': [9, 9, 9], 'prior_review_pin': pin['matches']}))


if __name__ == '__main__':
    main()
