"""Sealed edge-case tests for task 1. Runs in an isolated process after freeze.

Never imported by pfp_core, task prompts, skills or self panels.
"""
from decimal import Decimal

import candidate as m

# Shared with the public contract (allowed to appear in public material).
PUBLIC_CONTRACT_TOKENS = {'0.00', '0.01', 'E_AMOUNT', 'E_PARTS', 'E_IDEMPOTENCY_CONFLICT', 'E_UNKNOWN_PAYMENT',
                          'E_REFUND_EXCEEDS', 'payment', 'refund', 'kind', 'amount', 'account', 'code',
                          'acct', 'key'}


def _raises(code, fn, *args):
    try:
        fn(*args)
    except m.LedgerError as exc:
        return exc.code == code
    return False


def test_half_up_rounding_low():
    L = m.new_ledger(); m.post_payment(L, 'h1', 'zed', '1.005')
    assert m.balance(L, 'zed') == '1.01'


def test_half_up_rounding_high():
    L = m.new_ledger(); m.post_payment(L, 'h2', 'zed', '2.675')
    assert m.balance(L, 'zed') == '2.68'


def test_negative_amount_refused():
    assert _raises('E_AMOUNT', m.post_payment, m.new_ledger(), 'n1', 'zed', '-3.10')


def test_amount_rounding_to_zero_refused():
    assert _raises('E_AMOUNT', m.post_payment, m.new_ledger(), 'n2', 'zed', '0.004')


def test_nonfinite_and_garbage_refused():
    L = m.new_ledger()
    assert _raises('E_AMOUNT', m.post_payment, L, 'n3', 'zed', 'NaN')
    assert _raises('E_AMOUNT', m.post_payment, L, 'n4', 'zed', 'twelve')


def test_identical_replay_returns_same_receipt_once():
    L = m.new_ledger()
    a = m.post_payment(L, 'dup', 'yy', '7.5'); b = m.post_payment(L, 'dup', 'yy', '7.50')
    assert a == b and m.balance(L, 'yy') == '7.50'


def test_conflicting_replay_refused():
    L = m.new_ledger(); m.post_payment(L, 'dup2', 'yy', '7.50')
    assert _raises('E_IDEMPOTENCY_CONFLICT', m.post_payment, L, 'dup2', 'yy', '7.51')


def test_refund_exceeding_leaves_ledger_unchanged():
    L = m.new_ledger(); m.post_payment(L, 'p9', 'ww', '20.00'); m.refund(L, 'r9', 'p9', '15.00')
    assert _raises('E_REFUND_EXCEEDS', m.refund, L, 'r10', 'p9', '5.01')
    assert m.balance(L, 'ww') == '5.00'
    assert m.refund(L, 'r10', 'p9', '5.00')['amount'] == '5.00'


def test_refund_unknown_payment_by_keyword():
    L = m.new_ledger()
    try:
        m.refund(ledger=L, key='r1', payment_key='missing', amount='1.00')
    except m.LedgerError as exc:
        assert exc.code == 'E_UNKNOWN_PAYMENT'
    else:
        raise AssertionError('no error')


def test_refund_replay_idempotent():
    L = m.new_ledger(); m.post_payment(L, 'p1', 'vv', '9.99')
    m.refund(L, 'rr', 'p1', '3.33'); m.refund(L, 'rr', 'p1', '3.330')
    assert m.balance(L, 'vv') == '6.66'


def test_balance_unknown_account_zero():
    assert m.balance(m.new_ledger(), 'nobody') == '0.00'


def test_split_conserves_total_and_front_loads_remainder():
    parts = m.split_amount('100.00', 3)
    assert parts == ['33.34', '33.33', '33.33'] and sum(map(Decimal, parts)) == Decimal('100.00')


def test_split_more_parts_than_cents():
    assert m.split_amount('0.02', 3) == ['0.01', '0.01', '0.00']


def test_split_bad_parts():
    assert _raises('E_PARTS', m.split_amount, '1.00', 0) and _raises('E_PARTS', m.split_amount, '1.00', True)


def test_receipt_shape():
    r = m.post_payment(m.new_ledger(), 'shape', 'uu', '3')
    assert r == {'key': 'shape', 'kind': 'payment', 'account': 'uu', 'amount': '3.00'}
