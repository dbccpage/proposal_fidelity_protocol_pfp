"""Task 1: api_refactor_under_contract.

Refactor a messy payments ledger module without changing its public contract.
Public host checks: syntax, byte fence over the frozen block, AST signature
match of the public functions, and one import smoke using the worked example
printed in the prompt. Edge-case behaviour (rounding, idempotency, atomic
refunds, split conservation) is left to the sealed evaluator.
"""
from __future__ import annotations

from pfp_core.fidelity import HostOracleContext, ProtectedContract
from pfp_core.immunity import host_danger

from .common import SMOKE_DRIVER_HEAD, extract_code, parses, run_isolated, signatures

TASK_ID = 't1_api_refactor_under_contract'
PUBLIC_FUNCTIONS = ('new_ledger', 'post_payment', 'refund', 'balance', 'split_amount')

FROZEN = '''# BEGIN FROZEN PUBLIC CONTRACT
class LedgerError(Exception):
    """Raised with one of ERROR_CODES as ``code``; the ledger is unchanged."""
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


ERROR_CODES = ("E_AMOUNT", "E_PARTS", "E_IDEMPOTENCY_CONFLICT", "E_UNKNOWN_PAYMENT", "E_REFUND_EXCEEDS")
# END FROZEN PUBLIC CONTRACT'''

LEGACY = '''from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

''' + FROZEN + '''


def new_ledger() -> dict:
    return {"entries": [], "receipts": {}, "payments": {}}


def post_payment(ledger: dict, key: str, account: str, amount: str) -> dict:
    # convert
    try:
        d = Decimal(amount)
    except (InvalidOperation, TypeError):
        raise LedgerError("E_AMOUNT")
    if not d.is_finite():
        raise LedgerError("E_AMOUNT")
    d = d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if d <= 0:
        raise LedgerError("E_AMOUNT")
    req = ("payment", account, d)
    if key in ledger["receipts"]:
        old = ledger["receipts"][key]
        if old["request"] == req:
            return dict(old["receipt"])
        else:
            raise LedgerError("E_IDEMPOTENCY_CONFLICT")
    r = {"key": key, "kind": "payment", "account": account, "amount": str(d)}
    ledger["entries"].append((account, d))
    ledger["payments"][key] = {"account": account, "amount": d, "refunded": Decimal("0.00")}
    ledger["receipts"][key] = {"request": req, "receipt": r}
    return dict(r)


def refund(ledger: dict, key: str, payment_key: str, amount: str) -> dict:
    # convert (copied from above)
    try:
        d = Decimal(amount)
    except (InvalidOperation, TypeError):
        raise LedgerError("E_AMOUNT")
    if not d.is_finite():
        raise LedgerError("E_AMOUNT")
    d = d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if d <= 0:
        raise LedgerError("E_AMOUNT")
    req = ("refund", payment_key, d)
    if key in ledger["receipts"]:
        old = ledger["receipts"][key]
        if old["request"] == req:
            return dict(old["receipt"])
        raise LedgerError("E_IDEMPOTENCY_CONFLICT")
    if payment_key not in ledger["payments"]:
        raise LedgerError("E_UNKNOWN_PAYMENT")
    p = ledger["payments"][payment_key]
    if d > p["amount"] - p["refunded"]:
        raise LedgerError("E_REFUND_EXCEEDS")
    p["refunded"] = p["refunded"] + d
    ledger["entries"].append((p["account"], -d))
    r = {"key": key, "kind": "refund", "account": p["account"], "amount": str(d)}
    ledger["receipts"][key] = {"request": req, "receipt": r}
    return dict(r)


def balance(ledger: dict, account: str) -> str:
    t = Decimal("0.00")
    for a, v in ledger["entries"]:
        if a == account:
            t = t + v
    return str(t.quantize(Decimal("0.01")))


def split_amount(amount: str, parts: int) -> list:
    if type(parts) is not int or parts < 1:
        raise LedgerError("E_PARTS")
    try:
        d = Decimal(amount)
    except (InvalidOperation, TypeError):
        raise LedgerError("E_AMOUNT")
    if not d.is_finite():
        raise LedgerError("E_AMOUNT")
    d = d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if d <= 0:
        raise LedgerError("E_AMOUNT")
    cents = int(d * 100)
    base = cents // parts
    rem = cents % parts
    out = []
    for i in range(parts):
        c = base + (1 if i < rem else 0)
        out.append(str((Decimal(c) / 100).quantize(Decimal("0.01"))))
    return out
'''

PUBLIC_PROMPT = f'''Refactor the legacy module below for readability (remove duplication, use descriptive names).
Behaviour must not change. The block between the FROZEN markers is a published contract:
reproduce it byte-for-byte. Keep every public function name, parameter name and annotation.
Worked example: post_payment(L, "k1", "acct", "10") then balance(L, "acct") returns "10.00".
Return the complete module as one Python code block.

```python
{LEGACY}```
'''

CONTRACT = ProtectedContract.fence_markers(LEGACY, '# BEGIN FROZEN PUBLIC CONTRACT', '# END FROZEN PUBLIC CONTRACT')
LEGACY_SIGNATURES = signatures(LEGACY, PUBLIC_FUNCTIONS)
SELF_PANEL = [LEGACY]
OBLIGATIONS = ('rounding and quantization preserved', 'idempotent replay and conflict semantics',
               'refunds atomic on failure', 'split conserves the total')

SMOKE = SMOKE_DRIVER_HEAD + '''
try:
    L = candidate.new_ledger()
    candidate.post_payment(L, "k1", "acct", "10")
    emit({"balance": candidate.balance(L, "acct")})
except Exception as exc:
    emit({"error": type(exc).__name__})
'''


def public_check(text: str):
    code = extract_code(text)
    host = HostOracleContext(uncertified_obligations=OBLIGATIONS)
    err = parses(code)
    if not host.record('syntax', err is None, err or ''):
        return code, host, host_danger('MALFORMED_PAYLOAD', 'host.ast_parse', err)
    fence = CONTRACT.violations(code)
    sig_ok = signatures(code, PUBLIC_FUNCTIONS) == LEGACY_SIGNATURES
    host.record('frozen_fence', not fence, ','.join(fence))
    host.record('public_signatures', sig_ok)
    if fence or not sig_ok:
        return code, host, host_danger('PROTECTED_FIELD_VIOLATION', 'host.contract_check', code)
    smoke = run_isolated(code, SMOKE, validate=lambda r: isinstance(r, dict)).get('result') or {}
    if not host.record('worked_example', smoke.get('balance') == '10.00', str(smoke)):
        return code, host, host_danger('REPLAY_FAILURE', 'host.public_smoke', str(smoke))
    return code, host, None


# ---- Offline candidate fixtures (scripted solver outputs, not model outputs) ----
FAITHFUL = '''from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

''' + FROZEN + '''

CENT = Decimal("0.01")


def _money(amount) -> Decimal:
    """Parse a positive amount and round it half-up to cents."""
    try:
        value = Decimal(amount)
    except (InvalidOperation, TypeError):
        raise LedgerError("E_AMOUNT")
    if not value.is_finite():
        raise LedgerError("E_AMOUNT")
    value = value.quantize(CENT, rounding=ROUND_HALF_UP)
    if value <= 0:
        raise LedgerError("E_AMOUNT")
    return value


def _replay(ledger, key, request):
    """Stored receipt for an identical replay; conflict for a different request."""
    stored = ledger["receipts"].get(key)
    if stored is None:
        return None
    if stored["request"] != request:
        raise LedgerError("E_IDEMPOTENCY_CONFLICT")
    return dict(stored["receipt"])


def _commit(ledger, key, request, receipt, account, delta):
    ledger["entries"].append((account, delta))
    ledger["receipts"][key] = {"request": request, "receipt": receipt}
    return dict(receipt)


def new_ledger() -> dict:
    return {"entries": [], "receipts": {}, "payments": {}}


def post_payment(ledger: dict, key: str, account: str, amount: str) -> dict:
    value = _money(amount)
    request = ("payment", account, value)
    replay = _replay(ledger, key, request)
    if replay is not None:
        return replay
    ledger["payments"][key] = {"account": account, "amount": value, "refunded": Decimal("0.00")}
    receipt = {"key": key, "kind": "payment", "account": account, "amount": str(value)}
    return _commit(ledger, key, request, receipt, account, value)


def refund(ledger: dict, key: str, payment_key: str, amount: str) -> dict:
    value = _money(amount)
    request = ("refund", payment_key, value)
    replay = _replay(ledger, key, request)
    if replay is not None:
        return replay
    payment = ledger["payments"].get(payment_key)
    if payment is None:
        raise LedgerError("E_UNKNOWN_PAYMENT")
    if value > payment["amount"] - payment["refunded"]:
        raise LedgerError("E_REFUND_EXCEEDS")
    payment["refunded"] += value
    receipt = {"key": key, "kind": "refund", "account": payment["account"], "amount": str(value)}
    return _commit(ledger, key, request, receipt, payment["account"], -value)


def balance(ledger: dict, account: str) -> str:
    total = sum((v for a, v in ledger["entries"] if a == account), Decimal("0.00"))
    return str(total.quantize(CENT))


def split_amount(amount: str, parts: int) -> list:
    if type(parts) is not int or parts < 1:
        raise LedgerError("E_PARTS")
    cents = int(_money(amount) * 100)
    base, extra = divmod(cents, parts)
    return [str((Decimal(base + (i < extra)) / 100).quantize(CENT)) for i in range(parts)]
'''

_VERBOSE_DOC = '"""Payments ledger.\n\n' + 'This module keeps an append-only list of entries and receipts. ' * 40 + '\n"""\n'

CANDIDATES = {
    'faithful': f'```python\n{FAITHFUL}```\n',
    'verbose': f'```python\n{_VERBOSE_DOC}{FAITHFUL}```\n',
    'format_quirky': f'Sure! Here is the cleaned-up module.\n\n```py\n{FAITHFUL}```\nLet me know if you want tests.\n',
    'contract_drift': '```python\n' + FAITHFUL.replace('payment_key: str, amount: str', 'payment_key: str, value: str')
                      .replace('value = _money(amount)\n    request = ("refund"', 'value = _money(value)\n    request = ("refund"') + '```\n',
    'truncated': '```python\n' + FAITHFUL[: len(FAITHFUL) * 3 // 4] + '\n',
    'subtly_buggy': '```python\n' + FAITHFUL.replace(
        'value = value.quantize(CENT, rounding=ROUND_HALF_UP)',
        'value = Decimal(str(round(float(value), 2))).quantize(CENT)') + '```\n',
}
REPAIRABLE = {'contract_drift', 'truncated'}  # defect visible from the public task and host evidence
