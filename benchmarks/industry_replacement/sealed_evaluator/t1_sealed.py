"""Sealed edge-case scenarios for task 1. Judged in the parent after freeze.

Never imported by pfp_core, task prompts, skills or self panels.
"""
from .scenario import ANY, call, ok, raises, ref

# Shared with the public contract (allowed to appear in public material).
PUBLIC_CONTRACT_TOKENS = {'0.00', '0.01', 'E_AMOUNT', 'E_PARTS', 'E_IDEMPOTENCY_CONFLICT', 'E_UNKNOWN_PAYMENT',
                          'E_REFUND_EXCEEDS', 'payment', 'refund', 'kind', 'amount', 'account', 'code',
                          'acct', 'key', 'new_ledger', 'post_payment', 'balance', 'split_amount', 'LedgerError',
                          'ledger', 'payment_key'}

L = ref('L')
NEW = (call('new_ledger', as_='L'), ANY)


def err(code):
    return raises('LedgerError', code)


SCENARIOS = {
    'half_up_rounding_low': [NEW, (call('post_payment', L, 'h1', 'zed', '1.005'), ANY),
                             (call('balance', L, 'zed'), ok('1.01'))],
    'half_up_rounding_high': [NEW, (call('post_payment', L, 'h2', 'zed', '2.675'), ANY),
                              (call('balance', L, 'zed'), ok('2.68'))],
    'negative_amount_refused': [NEW, (call('post_payment', L, 'n1', 'zed', '-3.10'), err('E_AMOUNT'))],
    'amount_rounding_to_zero_refused': [NEW, (call('post_payment', L, 'n2', 'zed', '0.004'), err('E_AMOUNT'))],
    'nonfinite_and_garbage_refused': [NEW, (call('post_payment', L, 'n3', 'zed', 'NaN'), err('E_AMOUNT')),
                                      (call('post_payment', L, 'n4', 'zed', 'twelve'), err('E_AMOUNT'))],
    'identical_replay_returns_same_receipt_once': [
        NEW, (call('post_payment', L, 'dup', 'yy', '7.5'), ANY),
        (call('post_payment', L, 'dup', 'yy', '7.50'), ok({'key': 'dup', 'kind': 'payment', 'account': 'yy',
                                                          'amount': '7.50'})),
        (call('balance', L, 'yy'), ok('7.50'))],
    'conflicting_replay_refused': [NEW, (call('post_payment', L, 'dup2', 'yy', '7.50'), ANY),
                                   (call('post_payment', L, 'dup2', 'yy', '7.51'), err('E_IDEMPOTENCY_CONFLICT'))],
    'refund_exceeding_leaves_ledger_unchanged': [
        NEW, (call('post_payment', L, 'p9', 'ww', '20.00'), ANY), (call('refund', L, 'r9', 'p9', '15.00'), ANY),
        (call('refund', L, 'r10', 'p9', '5.01'), err('E_REFUND_EXCEEDS')), (call('balance', L, 'ww'), ok('5.00')),
        (call('refund', L, 'r10', 'p9', '5.00'), ok({'key': 'r10', 'kind': 'refund', 'account': 'ww',
                                                     'amount': '5.00'}))],
    'refund_unknown_payment_by_keyword': [
        NEW, (call('refund', ledger=L, key='r1', payment_key='missing', amount='1.00'), err('E_UNKNOWN_PAYMENT'))],
    'refund_replay_idempotent': [
        NEW, (call('post_payment', L, 'p1', 'vv', '9.99'), ANY), (call('refund', L, 'rr', 'p1', '3.33'), ANY),
        (call('refund', L, 'rr', 'p1', '3.330'), ANY), (call('balance', L, 'vv'), ok('6.66'))],
    'balance_unknown_account_zero': [NEW, (call('balance', L, 'nobody'), ok('0.00'))],
    'split_conserves_total_and_front_loads_remainder': [
        (call('split_amount', '100.00', 3), ok(['33.34', '33.33', '33.33']))],
    'split_more_parts_than_cents': [(call('split_amount', '0.02', 3), ok(['0.01', '0.01', '0.00']))],
    'split_bad_parts': [(call('split_amount', '1.00', 0), err('E_PARTS')),
                        (call('split_amount', '1.00', True), err('E_PARTS'))],
    'receipt_shape': [NEW, (call('post_payment', L, 'shape', 'uu', '3'),
                            ok({'key': 'shape', 'kind': 'payment', 'account': 'uu', 'amount': '3.00'}))],
}
