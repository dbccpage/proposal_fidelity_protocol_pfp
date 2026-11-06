"""Unified Demo 2 Runner: Consolidates Rounds R1, R2, R3, R4, R5, and R7.

Eliminates code duplication (DRY) across payload parsing, exact rational conversion,
OpenRouter provider communication, trace emission, and gate evaluation while
preserving exact round-specific invariants and interfaces.

Usage:
    python run_demo2.py --round r1 --scripted
    python run_demo2.py --round r1 --replay traces/demo2_r1_stoquastic_1790206756.jsonl
    python run_demo2.py --round r2 --replay traces/demo2_r2_freefermion_1790207175.jsonl
    python run_demo2.py --round r3 --live
    python run_demo2.py --round r4 --live
    python run_demo2.py --round r5 --live
    python run_demo2.py --round r7
"""
from __future__ import annotations
import argparse
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from fractions import Fraction
import hashlib
import io
from itertools import product
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Any, Dict, List, Optional
import urllib.request
from paper011_recovered_demo2.sign_switching import classify_sign_gauge, parse_matrix, verify_cycle, verify_gauge
from paper011_recovered_demo2.meron_witness import PathSector, WitnessError, verify_meron_witness
import paper011_recovered_demo2.certificate_gate as certificate_gate

def exact_rational(value: Any) -> Fraction:
    """Enforce exact rational representation with Zero-Float Law."""
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError(f'must be exact rational, not float/bool: {value}')
    if isinstance(value, (int, str)):
        try:
            return Fraction(value)
        except (ValueError, ZeroDivisionError) as exc:
            raise ValueError(f'invalid rational entry: {value}') from exc
    raise ValueError(f'unsupported scalar type: {type(value)}')

def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f'duplicate JSON key: {key}')
        out[key] = value
    return out

def _reject_json_constant(value: str) -> None:
    raise ValueError(f'non-JSON numeric constant: {value}')

def _reject_json_float(value: str) -> None:
    raise ValueError(f'inexact JSON number: {value}; use a rational string')

def parse_payload(raw: str, strict: bool=True) -> dict[str, Any] | list[Any]:
    """Parse JSON payload: strict by default (rejects floats, constants, dup keys)."""
    if strict:
        fenced = re.fullmatch('\\s*```(?:json)?\\s*(.*?)\\s*```\\s*', raw, re.S | re.I)
        body = fenced.group(1) if fenced else raw
        return json.loads(body, object_pairs_hook=_unique_pairs, parse_constant=_reject_json_constant, parse_float=_reject_json_float)
    blocks = re.findall('```(?:json)?\\s*([\\s\\S]*?)\\s*```', raw)
    if len(blocks) > 1:
        items = []
        for b in blocks:
            try:
                p = json.loads(b.strip(), strict=False)
                if isinstance(p, list):
                    items.extend(p)
                elif isinstance(p, dict):
                    items.append(p)
            except Exception:
                pass
        if items:
            return items
    elif len(blocks) == 1:
        try:
            return json.loads(blocks[0].strip(), strict=False)
        except Exception:
            pass
    cleaned = re.sub('```(?:json)?\\s*', '', raw).replace('```', '').strip()
    try:
        return json.loads(cleaned, object_pairs_hook=_unique_pairs, parse_constant=_reject_json_constant, parse_float=_reject_json_float)
    except Exception:
        pass
    try:
        return json.loads(cleaned, strict=False)
    except Exception:
        pass
    decoder = json.JSONDecoder(strict=False)
    pos = 0
    items = []
    while pos < len(raw):
        m = re.search('[\\[\\{]', raw[pos:])
        if not m:
            break
        idx = pos + m.start()
        try:
            obj, end = decoder.raw_decode(raw[idx:])
            if isinstance(obj, list):
                items.extend(obj)
            elif isinstance(obj, dict):
                items.append(obj)
            pos = idx + end
        except Exception:
            pos = idx + 1
    if len(items) == 1:
        return items[0]
    if len(items) > 1:
        return items
    raise ValueError('No valid JSON payload found in input')

def parse_move(raw: str, strict: bool=True) -> dict[str, Any]:
    move = parse_payload(raw, strict=strict)
    if not isinstance(move, dict) or not isinstance(move.get('move_type'), str):
        raise ValueError('a move must be a JSON object with move_type')
    return move

class OpenRouterClient:
    """Unified HTTP client for OpenRouter chat completions."""

    def __init__(self, api_key: str | None=None, app_title: str='Symbol Game'):
        self.api_key = api_key or os.environ.get('OPENROUTER_API_KEY', '')
        self.app_title = app_title
        self.url = 'https://openrouter.ai/api/v1/chat/completions'

    def call(self, model: str, messages: list[dict[str, str]], fallback: str | None=None, max_tokens: int=1024, temperature: float=0.0, timeout: int=45) -> str:
        headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json', 'HTTP-Referer': 'https://github.com/the_symbol_game', 'X-Title': self.app_title}
        payload = {'model': model, 'messages': messages, 'temperature': temperature, 'max_tokens': max_tokens}
        req = urllib.request.Request(self.url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                return data['choices'][0]['message']['content'].strip()
        except Exception as exc:
            if fallback:
                payload['model'] = fallback
                req_fb = urllib.request.Request(self.url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
                with urllib.request.urlopen(req_fb, timeout=timeout) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    return data['choices'][0]['message']['content'].strip()
            raise exc

@dataclass
class CertificateResult:
    valid: bool
    status: str
    reason: str = ''
    phi1: float | None = None
    admitted: bool = False
    condition_checks: dict[str, bool] = field(default_factory=dict)
    hallucination_detected: bool = False
    details: dict[str, Any] = field(default_factory=dict)

class BqnfCertificateGate:
    """Validates candidate moves and verification claims under BQNF-FSIGN game."""

    def __init__(self, hamiltonian_type: str, parameters: dict[str, Any] | None=None):
        self.hamiltonian_type = hamiltonian_type
        self.parameters = parameters or {}

    def verify_sign_free(self, move: dict, current_phi1: float) -> CertificateResult:
        """Historical prose witnesses cannot establish a functional or terminal."""
        return CertificateResult(valid=False, admitted=False, status='UNKNOWN_NOT_CERTIFIED', phi1=None, reason='RUST_FUNCTIONAL_REQUIRED: no native functional or physical witness adapter', details={'functional_status': 'UNAVAILABLE', 'authority_effect': 'None'})
BASIS = ('up_up', 'up_down', 'down_up', 'down_down')
TFI_MATRIX = parse_matrix([['-1', '-1/2', '-1/2', '0'], ['-1/2', '1', '0', '-1/2'], ['-1/2', '0', '1', '-1/2'], ['0', '-1/2', '-1/2', '-1']])
MATRIX_SHA256 = hashlib.sha256(json.dumps([[str(v) for v in row] for row in TFI_MATRIX], separators=(',', ':')).encode('utf-8')).hexdigest()
R1_SYSTEM_PROMPT = 'You are a candidate generator. Return one JSON move per turn.\nThe host alone checks the full matrix and the witness. The current task is the\nfixed-basis diagonal sign-gauge subclass of the wider BQNF-FSIGN program.\nDo not claim Phi_1=0 without a separately declared and checked BQNF adapter.\nFirst send ASSERT_MATRIX with the complete 4x4 matrix as integer/rational strings.\nAfter host acceptance, send VERIFY_REPAIR with gauge:[a0,a1,a2,a3], each bit 0 or 1.\nD=diag((-1)^a0,...); the host checks every off-diagonal entry of D H D <= 0.\nAn identity gauge is a positivity witness, not a meron Xi. If unsure, use\nLIFT_REQUEST. No prose, authority claims, or producer-authored host verdicts.'

@dataclass
class R1Governor:
    matrix: tuple[tuple[Fraction, ...], ...] = TFI_MATRIX
    asserted: dict[tuple[int, int], Fraction] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    terminal: str | None = None

    def _record(self, turn: int, move: dict[str, Any] | None, status: str, admitted: bool, detail: str='') -> dict[str, Any]:
        decision = {'turn': turn, 'move': move, 'status': status, 'admitted': admitted, 'detail': detail, 'asserted_entries': len(self.asserted), 'required_entries': len(self.matrix) ** 2, 'bqnf_phi1_zero': None, 'terminal': self.terminal, 'authority_effect': 'None'}
        self.history.append(decision)
        return decision

    def evaluate(self, raw: str, turn: int) -> dict[str, Any]:
        if self.terminal:
            return self._record(turn, None, 'RefusedAfterTerminal', False)
        try:
            payload = parse_payload(raw, strict=True)
        except (ValueError, json.JSONDecodeError) as exc:
            return self._record(turn, None, 'RefusedMalformedMove', False, str(exc))
        if isinstance(payload, list):
            if not payload or len(payload) > 32:
                return self._record(turn, None, 'RefusedBatchSize', False)
            trial = R1Governor(self.matrix, dict(self.asserted), list(self.history), self.terminal)
            start = len(trial.history)
            for index, item in enumerate(payload):
                if not isinstance(item, dict) or not isinstance(item.get('move_type'), str):
                    return self._record(turn, None, 'RefusedBatchItem', False, f'item {index} lacks move_type')
                decision = trial.evaluate(json.dumps(item), turn)
                if not decision['admitted']:
                    return self._record(turn, None, 'RefusedBatchItem', False, f"item {index}: {decision['status']}")
            self.asserted = trial.asserted
            self.terminal = trial.terminal
            self.history = trial.history
            return {'turn': turn, 'status': 'BatchAdmitted', 'admitted': True, 'items': self.history[start:], 'terminal': self.terminal, 'authority_effect': 'None'}
        if not isinstance(payload, dict) or not isinstance(payload.get('move_type'), str):
            return self._record(turn, None, 'RefusedMalformedMove', False, 'expected move object or bounded array of move objects')
        move = payload
        kind = move['move_type'].upper()
        if kind == 'ASSERT_MATRIX':
            try:
                supplied = parse_matrix(move['matrix'])
            except (KeyError, TypeError, ValueError) as exc:
                return self._record(turn, move, 'RefusedMalformedMatrix', False, str(exc))
            if supplied != self.matrix:
                return self._record(turn, move, 'RefusedMatrixMismatch', False, 'supplied matrix differs from pinned manifest')
            if self.asserted:
                return self._record(turn, move, 'RefusedDuplicateAssertion', False)
            self.asserted = {(i, j): value for i, row in enumerate(supplied) for j, value in enumerate(row)}
            return self._record(turn, move, 'MatrixAsserted', True)
        if kind == 'ASSERT_TERM':
            key = move.get('ij')
            match = re.fullmatch('(\\d+)->(\\d+)', key) if isinstance(key, str) else None
            if not match:
                return self._record(turn, move, 'RefusedBadIndex', False)
            i, j = map(int, match.groups())
            if i >= len(self.matrix) or j >= len(self.matrix):
                return self._record(turn, move, 'RefusedBadIndex', False)
            if (i, j) in self.asserted:
                return self._record(turn, move, 'RefusedDuplicateAssertion', False)
            expected_type = 'diag' if i == j else 'offdiag'
            if move.get('term_type') != expected_type:
                return self._record(turn, move, 'RefusedTermType', False)
            try:
                value = exact_rational(move['value'])
            except (KeyError, ValueError) as exc:
                return self._record(turn, move, 'RefusedNonExactEntry', False, str(exc))
            if value != self.matrix[i][j]:
                return self._record(turn, move, 'RefusedEntryMismatch', False)
            self.asserted[i, j] = value
            return self._record(turn, move, 'TermAsserted', True)
        if kind in ('VERIFY_SIGN_FREE', 'VERIFY_CANCELLATION'):
            return self._record(turn, move, 'RefusedWrongWitnessRoute', False, 'Xi cancellation requires signed path rows and a checked meron sector; identity is not fixed-point-free or sign-reversing')
        if kind == 'VERIFY_REPAIR':
            if len(self.asserted) != len(self.matrix) ** 2:
                return self._record(turn, move, 'RefusedIncompleteManifest', False)
            gauge = move.get('gauge')
            if not isinstance(gauge, list) or len(gauge) != len(self.matrix) or any((type(bit) is not int or bit not in (0, 1) for bit in gauge)):
                return self._record(turn, move, 'RefusedBadGauge', False)
            if not verify_gauge(self.matrix, tuple(gauge)):
                return self._record(turn, move, 'RefusedGaugeDoesNotRepair', False)
            self.terminal = 'RestrictedSignGaugeRepair'
            return self._record(turn, move, self.terminal, True, 'D=diag((-1)^a); D H D has nonpositive off-diagonal entries')
        if kind in ('OPEN_SIGN_OBSTRUCTION', 'INVALIDATE'):
            result = classify_sign_gauge(self.matrix)
            if result.gauge is not None:
                return self._record(turn, move, 'RefusedFalseObstruction', False)
            self.terminal = 'RestrictedSignGaugeObstruction'
            return self._record(turn, move, self.terminal, True, f'odd constraint cycle: {result.cycle}')
        if kind == 'LIFT_REQUEST':
            hint = 'ASSERT_MATRIX with all 16 exact entries before VERIFY_REPAIR' if len(self.asserted) != len(self.matrix) ** 2 else 'provide one gauge bit per declared basis state'
            return self._record(turn, move, 'LiftRequested', False, hint)
        return self._record(turn, move, 'RefusedUnknownMove', False)

def prompt(governor: R1Governor, turn: int, phase_cue: bool=True) -> str:
    if turn == 1:
        return 'R1 2-site transverse-field Ising; basis=' + json.dumps(BASIS) + '; H=' + json.dumps([[str(x) for x in row] for row in governor.matrix]) + '. Propose the complete ASSERT_MATRIX, then a diagonal sign-gauge witness. The broader BQNF Phi_1 claim remains untested by this game.'
    last = governor.history[-1]
    message = f"Host decision: {last['status']}; admitted={last['admitted']}; asserted={last['asserted_entries']}/{last['required_entries']}. {last['detail']}"
    if phase_cue and last['status'] == 'MatrixAsserted':
        message += ' Phase transition: now propose VERIFY_REPAIR with four gauge bits.'
    return message

def summary(governor: R1Governor) -> dict[str, Any]:
    return {'schema': 'symbol_game.demo2.r1.replay.v2', 'matrix_sha256': MATRIX_SHA256, 'basis': list(BASIS), 'matrix': [[str(x) for x in row] for row in governor.matrix], 'terminal': governor.terminal or 'UNKNOWN_NOT_CERTIFIED', 'decisions': governor.history, 'bqnf_phi1_zero': None, 'scope': 'fixed real basis, diagonal +/-1 sign gauge only', 'authority_effect': 'None'}

def run_scripted_r1() -> dict[str, Any]:
    governor = R1Governor()
    governor.evaluate(json.dumps({'move_type': 'ASSERT_MATRIX', 'matrix': [[str(x) for x in row] for row in TFI_MATRIX]}), 1)
    governor.evaluate(json.dumps({'move_type': 'VERIFY_REPAIR', 'gauge': [0, 0, 0, 0]}), 2)
    return summary(governor)

def run_replay_r1(path: Path) -> dict[str, Any]:
    governor = R1Governor()
    for turn, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        item = json.loads(line)
        governor.evaluate(item['raw'], turn)
    return summary(governor)

def run_live_r1(model: str='qwen/qwen-2.5-72b-instruct', max_turns: int=12, phase_cue: bool=True, output_dir: Path | None=None) -> dict[str, Any]:
    client = OpenRouterClient()
    governor = R1Governor()
    messages: list[dict[str, str]] = [{'role': 'system', 'content': R1_SYSTEM_PROMPT}]
    traces = []
    for turn in range(1, max_turns + 1):
        user_msg = prompt(governor, turn, phase_cue=phase_cue)
        messages.append({'role': 'user', 'content': user_msg})
        raw = client.call(model, messages, temperature=0.0)
        messages.append({'role': 'assistant', 'content': raw})
        decision = governor.evaluate(raw, turn)
        traces.append({'turn': turn, 'user': user_msg, 'raw': raw, 'decision': decision})
        if governor.terminal:
            break
    res = summary(governor)
    res['live_model'] = model
    res['turns'] = len(traces)
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / 'receipt.json').write_text(json.dumps(res, indent=2), encoding='utf-8')
    return res

def main_r1(argv: list[str] | None=None) -> None:
    parser = argparse.ArgumentParser(description='Demo 2 Round 1: Transverse-Field Ising Sign Gauge')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--scripted', action='store_true')
    mode.add_argument('--replay', type=Path)
    mode.add_argument('--live', action='store_true')
    parser.add_argument('--model', default='qwen/qwen-2.5-72b-instruct')
    parser.add_argument('--max-turns', type=int, default=12)
    parser.add_argument('--no-phase-cue', action='store_true')
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args(argv)
    if args.scripted:
        print(json.dumps(run_scripted_r1(), indent=2))
    elif args.replay:
        print(json.dumps(run_replay_r1(args.replay), indent=2))
    elif args.live:
        print(json.dumps(run_live_r1(args.model, args.max_turns, not args.no_phase_cue, args.output_dir), indent=2))
HOPPING = {'0->1': Fraction(-1), '1->0': Fraction(-1), '1->2': Fraction(-1), '2->1': Fraction(-1), '2->3': Fraction(-1), '3->2': Fraction(-1)}

def audit_response_r2(raw: str) -> dict[str, Any]:
    try:
        payload = parse_payload(raw, strict=True)
    except (ValueError, json.JSONDecodeError) as exc:
        return {'status': 'REJECTED_PARSE', 'reason': str(exc), 'terminal': 'UNKNOWN_NOT_CERTIFIED', 'authority_effect': 'None'}
    moves = payload if isinstance(payload, list) else [payload]
    if not moves or len(moves) > 32:
        return {'status': 'REJECTED_BATCH_SIZE', 'terminal': 'UNKNOWN_NOT_CERTIFIED', 'authority_effect': 'None'}
    asserted: dict[str, Fraction] = {}
    proposed_xi: Any = None
    failure: str | None = None
    for index, move in enumerate(moves):
        if not isinstance(move, dict) or not isinstance(move.get('move_type'), str):
            failure = f'item {index}: invalid move'
            break
        kind = move['move_type'].upper()
        if kind == 'ASSERT_TERM':
            key = move.get('ij')
            if not isinstance(key, str) or key not in HOPPING or key in asserted or (move.get('term_type') != 'offdiag'):
                failure = f'item {index}: duplicate, undeclared, or mistyped hopping term'
                break
            try:
                value = exact_rational(move.get('value'))
            except (ValueError, TypeError, ZeroDivisionError):
                failure = f'item {index}: inexact or malformed amplitude'
                break
            if value != HOPPING[key]:
                failure = f'item {index}: amplitude mismatch'
                break
            asserted[key] = value
        elif kind == 'VERIFY_SIGN_FREE':
            if len(asserted) != len(HOPPING):
                failure = f'item {index}: VERIFY before all six directed terms'
                break
            if proposed_xi is not None:
                failure = f'item {index}: duplicate VERIFY'
                break
            proposed_xi = move.get('xi_witness')
        else:
            failure = f'item {index}: unsupported move {kind}'
            break
    if failure:
        return {'status': 'REJECTED_BATCH', 'reason': failure, 'asserted_terms': sorted(asserted), 'terminal': 'UNKNOWN_NOT_CERTIFIED', 'authority_effect': 'None'}
    return {'status': 'BATCH_FORMAT_OBSERVED' if isinstance(payload, list) else 'MOVE_FORMAT_OBSERVED', 'move_count': len(moves), 'asserted_terms': sorted(asserted), 'manifest_complete': len(asserted) == len(HOPPING), 'proposed_xi': proposed_xi, 'witness_status': 'WITNESS_UNCHECKED' if proposed_xi is not None else 'NO_WITNESS', 'reason': 'No host-pinned signed path set, exact weights, or verified path-index Xi', 'bqnf_phi1_zero': None, 'terminal': 'UNKNOWN_NOT_CERTIFIED', 'authority_effect': 'None'}

def replay_r2(trace: Path) -> dict[str, Any]:
    rows = [json.loads(line) for line in trace.read_text(encoding='utf-8').splitlines()]
    audits = [audit_response_r2(row['raw']) for row in rows]
    return {'trace': str(trace.resolve()), 'model_responses': len(rows), 'legacy_reported_statuses': [row.get('status') for row in rows], 'audits': audits, 'terminal': 'UNKNOWN_NOT_CERTIFIED', 'authority_effect': 'None'}

def main_r2(argv: list[str] | None=None) -> None:
    parser = argparse.ArgumentParser(description='Demo 2 Round 2: Free Fermion Historical Audit')
    parser.add_argument('--replay', required=True, type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(replay_r2(args.replay), indent=2, ensure_ascii=True))
audit_response = audit_response_r2
replay = replay_r2
_value = exact_rational

@dataclass
class BaseHubbardGovernor:
    expected_terms: list[tuple[str, int, str]]
    model_class: str
    gate: BqnfCertificateGate = field(init=False)
    asserted_terms: dict = field(default_factory=dict)
    admitted: int = 0
    refused: int = 0
    lifts: int = 0
    turns: list = field(default_factory=list)
    phi1: float | None = None
    terminal: str = ''
    proposal_log: list = field(default_factory=list)
    hallucinated_witnesses: list = field(default_factory=list)
    am_fsp_hits: int = 0

    def __post_init__(self):
        self.gate = BqnfCertificateGate(self.model_class)

    def evaluate(self, raw: str, turn: int) -> tuple[str, bool]:
        try:
            parsed = parse_payload(raw, strict=False)
        except Exception:
            return ('ParseFailure', False)
        if isinstance(parsed, list):
            return self._eval_batch(parsed, turn)
        if isinstance(parsed, dict):
            return self._eval_single(parsed, turn)
        return ('MalformedPayload', False)

    def _eval_batch(self, proposals: list, turn: int) -> tuple[str, bool]:
        batch_summary = []
        overall_admitted = True
        for idx, item in enumerate(proposals, 1):
            if not isinstance(item, dict):
                overall_admitted = False
                batch_summary.append(f'Proposal {idx}: Malformed (not a dict)')
                continue
            status, adm, msg = self._eval_single_proposal(item, turn, in_batch=True)
            batch_summary.append(f"Proposal {idx} ({item.get('move_type')}): {status}")
            if not adm:
                overall_admitted = False
            if self.terminal:
                break
        return (' | '.join(batch_summary), overall_admitted)

    def _eval_single(self, move: dict, turn: int) -> tuple[str, bool]:
        status, admitted, _ = self._eval_single_proposal(move, turn, in_batch=False)
        return (status, admitted)

    def _eval_single_proposal(self, move: dict, turn: int, in_batch: bool=False) -> tuple[str, bool, str]:
        raise NotImplementedError

def run_hubbard_demo(governor: BaseHubbardGovernor, system_prompt: str, make_user_turn_fn: Any, round_name: str, hamiltonian_name: str, class_ground_truth: str, expected_terminal: str, expected_xi: str, anti_morphisms_active: list[str], model: str='qwen/qwen-2.5-72b-instruct', max_turns: int=12, scripted: bool=False, scripted_moves: list[Any] | None=None, output_dir: Path | None=None, verbose: bool=True, test_posture: str | None=None) -> dict[str, Any]:
    task_id = f'{round_name}_{hamiltonian_name}_{int(time.time())}'
    traces: list[dict[str, Any]] = []
    messages = [{'role': 'system', 'content': system_prompt}]
    call_count = 0
    if scripted:
        moves = scripted_moves or []
        for turn, move in enumerate(moves, 1):
            raw = json.dumps(move) if not isinstance(move, str) else move
            status, admitted = governor.evaluate(raw, turn)
            traces.append({'turn': turn, 'raw': raw, 'status': status, 'admitted': admitted, 'phi1': governor.phi1})
            if verbose:
                print(f'  [scripted turn {turn}]: {status} (phi1={governor.phi1}, terminal={governor.terminal})')
            if governor.terminal:
                break
    else:
        client = OpenRouterClient()
        for turn in range(1, max_turns + 1):
            user_msg = make_user_turn_fn(governor, turn, max_turns)
            messages.append({'role': 'user', 'content': user_msg})
            t0 = time.time()
            try:
                raw = client.call(model, messages, temperature=0.0)
            except Exception as exc:
                raw = json.dumps({'move_type': 'ERROR', 'error': str(exc)})
            elapsed = round(time.time() - t0, 2)
            call_count += 1
            messages.append({'role': 'assistant', 'content': raw})
            status, admitted = governor.evaluate(raw, turn)
            traces.append({'turn': turn, 'user': user_msg, 'raw': raw, 'status': status, 'admitted': admitted, 'phi1': governor.phi1, 'elapsed_s': elapsed})
            if verbose:
                print(f'  turn {turn}: {status:<50} phi1={governor.phi1} ({elapsed}s)')
            if governor.terminal:
                break
    receipt: dict[str, Any] = {'schema': 'symbol_game.fsp.v1', 'task_id': task_id, 'model': 'scripted' if scripted else model, 'round': round_name, 'hamiltonian': hamiltonian_name, 'class_ground_truth': class_ground_truth, 'expected_terminal': expected_terminal, 'expected_xi': expected_xi, 'actual_terminal': governor.terminal or 'FUEL_EXHAUSTED', 'phi1_final': governor.phi1, 'admitted': governor.admitted, 'refused': governor.refused, 'lifts': governor.lifts, 'turns': len(traces), 'llm_calls': call_count, 'authority_effect': 'None', 'anti_morphisms_active': anti_morphisms_active, 'certificate_gate': 'BqnfCertificateGate[repaired]'}
    if hasattr(governor, 'am_fsp_hits'):
        receipt['am_fsp_hits'] = governor.am_fsp_hits
    if hasattr(governor, 'am_fsp6_count'):
        receipt['am_fsp6_hits'] = governor.am_fsp6_count
    if hasattr(governor, 'am_fsp2_count'):
        receipt['am_fsp2_hits'] = governor.am_fsp2_count
    if hasattr(governor, 'hallucinated_witnesses'):
        receipt['hallucinated_witnesses'] = governor.hallucinated_witnesses
    if test_posture:
        receipt['test_posture'] = test_posture
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / 'receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        trace_path = output_dir / f'{task_id}.jsonl'
        with open(trace_path, 'w', encoding='utf-8') as f:
            for item in traces:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
    return receipt
R3_HAMILTONIAN_TERMS = [('0_up->1_up', -1, 'c_0_up^dag c_1_up (kinetic hopping)'), ('1_up->0_up', -1, 'c_1_up^dag c_0_up (kinetic hopping)'), ('0_dn->1_dn', -1, 'c_0_dn^dag c_1_dn (kinetic hopping)'), ('1_dn->0_dn', -1, 'c_1_dn^dag c_0_dn (kinetic hopping)'), ('site_0', -2, 'n_0_up n_0_dn (on-site U=-2 attractive)'), ('site_1', -2, 'n_1_up n_1_dn (on-site U=-2 attractive)')]
R3_SYSTEM_PROMPT = '[STAGE-0 MSS-mu CONTROLLER]\nYou are a CANDIDATE GENERATOR for BQNF-FSIGN classification. AuthorityEffect: None.\n\nTASK: Classify a 2-site Attractive Hubbard model dimer (t=1, U=-2) on a bipartite lattice.\nDetermine if it is sign-free and produce an explicit involution witness Xi.\n\nHamiltonian:\n  H = -t sum_{<ij>,sigma} (c_{i,sigma}^dag c_{j,sigma} + h.c.) - |U| sum_i n_{i,up} n_{i,down}\n  Sites: 0 (sublattice A), 1 (sublattice B)\n  t = 1 (kinetic hopping), U = -2 (ATTRACTIVE on-site interaction)\n\nBQNF-FSIGN context:\n  C0: repair_potentials_alpha (gauge transformations)\n  C1: path_weights\n  Q1 = C1 / im(d0) (obstruction quotient)\n  Terminal routes:\n    - ExactCancellation: certified involution witness Xi satisfying all 4 laws:\n        (1) involution_law:   Xi.Xi == id\n        (2) fixed_point_free: Xi(x) != x for active paths\n        (3) sign_reversing:   sgn(Xi(x)) == -sgn(x) on explicit paired paths (MUST REVERSE SIGN!)\n        (4) weight_preserving: |weight(Xi(x))| == |weight(x)|\n\nCRITICAL CERTIFICATE GATE WARNING:\n  - Do NOT claim that the involution \'preserves worldline sign\' or \'preserves configuration sign\'.\n    An involution that preserves sign cannot cancel sign-problem defects (Refused_UnverifiedInvolution_SignReversalMissing).\n  - Do NOT rely only on a vague sentence asserting \'det > 0\' without explicit sign-reversing pairing.\n  - Do NOT use Xi=identity (that is the stoquastic witness, AM-FSP-6 refusal).\n  - Attractive Hubbard on a bipartite lattice is sign-free via the PARTICLE-HOLE TRANSFORMATION\n    applied to one spin species: c_{i,down} -> (-1)^i c_{i,down}^dag.\n\nMOVE TYPES (raw JSON only):\n  ASSERT_TERM:      {"move_type":"ASSERT_TERM","ij":"<str>","value":<float>,"term_type":"<str>","note":"<str>"}\n  VERIFY_SIGN_FREE: {"move_type":"VERIFY_SIGN_FREE","phi1_claim":0,\n                     "xi_witness":{"type":"particle_hole",\n                                   "mapping":"c_{i,dn} -> (-1)^i c_{i,dn}^dag",\n                                   "sublattice_A":"[0]","sublattice_B":"[1]",\n                                   "proof":"<demonstration of all 4 conditions, specifically sgn(Xi(x)) == -sgn(x)>"},\n                     "class":"attractive_hubbard"}\n  LIFT_REQUEST:     {"move_type":"LIFT_REQUEST","reason":"<str>"}\n  OPEN_SIGN_OBSTRUCTION: {"move_type":"OPEN_SIGN_OBSTRUCTION","reason":"<str>"}\n[END STAGE-0]\n'

@dataclass
class AttractiveHubbardGovernor(BaseHubbardGovernor):

    def __init__(self):
        super().__init__(expected_terms=R3_HAMILTONIAN_TERMS, model_class='attractive_hubbard')

    @property
    def am_fsp6_count(self) -> int:
        return self.am_fsp_hits

    @am_fsp6_count.setter
    def am_fsp6_count(self, val: int) -> None:
        self.am_fsp_hits = val

    def _lift_hint(self, n: int) -> str:
        hints = ['Host: Attractive Hubbard (U < 0) on bipartite lattice is sign-free via the PARTICLE-HOLE transform: Xi: c_{i,down} -> (-1)^i c_{i,down}^dag (A={0}: +c_dn^dag, B={1}: -c_dn^dag). Provide explicit proof of all 4 conditions, crucially condition (3) sign-reversal: sgn(Xi(x)) == -sgn(x).', "Host: Issue VERIFY_SIGN_FREE with xi_witness containing: type='particle_hole', mapping='c_{i,dn} -> (-1)^i c_{i,dn}^dag', and proof demonstrating explicit opposite-sign pairing sgn(Xi(x)) = -sgn(x) with |w(Xi(x))| = |w(x)|."]
        return hints[min(n - 1, len(hints) - 1)]

    def _eval_single_proposal(self, move: dict, turn: int, in_batch: bool=False) -> tuple[str, bool, str]:
        mt = move.get('move_type', '').upper()
        if mt == 'ASSERT_TERM':
            key = move.get('ij', move.get('site', str(move)))
            val = move.get('value')
            self.asserted_terms[key] = move
            self.admitted += 1
            if len(self.asserted_terms) >= len(self.expected_terms):
                self.phi1 = None
            rec = {'turn': turn, 'move': move, 'status': 'Asserted', 'phi1': self.phi1, 'admitted': True}
            self.turns.append(rec)
            self.proposal_log.append(rec)
            return ('Asserted', True, f'Term {key}={val} asserted.')
        if mt == 'VERIFY_SIGN_FREE':
            cert = self.gate.verify_sign_free(move, self.phi1)
            rec = {'turn': turn, 'move': move, 'status': cert.status, 'phi1': cert.phi1, 'admitted': cert.admitted, 'reason': cert.reason}
            self.turns.append(rec)
            self.proposal_log.append(rec)
            if cert.valid:
                self.admitted += 1
                self.terminal = 'ExactCancellation'
                self.phi1 = None
                return (cert.status, True, cert.reason)
            else:
                self.refused += 1
                if 'AM-FSP-6' in cert.status:
                    self.am_fsp_hits += 1
            return (cert.status, cert.admitted, cert.reason)
        if mt == 'LIFT_REQUEST':
            self.lifts += 1
            hint = self._lift_hint(self.lifts)
            rec = {'turn': turn, 'move': move, 'status': 'LiftRequested', 'phi1': self.phi1, 'admitted': True, 'reason': move.get('reason', ''), 'hint': hint}
            self.turns.append(rec)
            self.proposal_log.append(rec)
            return (f'LiftRequested|hint:{hint[:60]}', True, hint)
        if mt in ('OPEN_SIGN_OBSTRUCTION', 'INVALIDATE'):
            self.refused += 1
            rec = {'turn': turn, 'move': move, 'status': 'Refused_BipartiteAttractiveIsSignFree', 'phi1': self.phi1, 'admitted': False}
            self.turns.append(rec)
            self.proposal_log.append(rec)
            return ('Refused_BipartiteAttractiveIsSignFree', False, 'Bipartite attractive Hubbard is sign-free via particle-hole.')
        self.refused += 1
        return ('UnknownMoveType', False, f'Unknown move: {mt}')

def make_user_turn_r3(gov: AttractiveHubbardGovernor, turn: int, max_turns: int=12) -> str:
    if turn == 1:
        terms_str = '\n'.join((f'  H[{t[0]}] = {t[1]}  # {t[2]}' for t in R3_HAMILTONIAN_TERMS))
        return f'[BQNF-FSIGN | turn=1 | authority_effect=None]\nHAMILTONIAN: 2-site Attractive Hubbard dimer (bipartite)\n  H = -t sum_{{<ij>,sigma}} (c_{{i,sigma}}† c_{{j,sigma}} + h.c.) - |U| sum_i n_{{i,up}} n_{{i,down}}\n  Sites: 0 (sublattice A), 1 (sublattice B)\n  t = 1, U = -2 (ATTRACTIVE)\nDeclared terms:\n{terms_str}\n\nTASK: Classify under BQNF-FSIGN. Determine if this Hamiltonian is sign-free.\nIf sign-free, ASSERT terms and issue VERIFY_SIGN_FREE with an explicit particle-hole involution witness Xi.\nFuel: {max_turns} turns. AuthorityEffect: None.'
    last = gov.turns[-1] if gov.turns else {}
    status = last.get('status', '')
    phi1 = last.get('phi1', gov.phi1)
    hint = last.get('hint', '')
    feedback = f'[GOVERNOR | turn={turn} | phi1={phi1}]\nLast proposal status: {status}\n'
    if 'SignReversalMissing' in status:
        feedback += '\n*** REFUSED: Missing Explicit Sign-Reversal Proof (Condition 3) ***\n'
    if hint:
        feedback += f'Host witness hint: {hint}\n'
    if gov.terminal == 'ExactCancellation':
        feedback += 'TERMINAL: ExactCancellation -- Involution witness verified and admitted.\n'
    feedback += f'Turns remaining: {max_turns - turn}. AuthorityEffect: None.'
    return feedback
R3_SCRIPTED_MOVES = [[{'move_type': 'ASSERT_TERM', 'ij': t[0], 'value': t[1], 'term_type': 'offdiag' if '->' in t[0] else 'diag', 'note': t[2]} for t in R3_HAMILTONIAN_TERMS], {'move_type': 'VERIFY_SIGN_FREE', 'phi1_claim': 0, 'xi_witness': {'type': 'particle_hole', 'mapping': 'c_{i,dn} -> (-1)^i c_{i,dn}^dag', 'sublattice_A': '[0]', 'sublattice_B': '[1]', 'proof': 'Involution law holds: Xi.Xi == id. Sublattice A/B swap is fixed-point free on active paths. The particle-hole transformation reverses the sign sgn(Xi(x)) == -sgn(x) on explicit paired paths with weight preservation |weight(Xi(x))| == |weight(x)|.'}, 'class': 'attractive_hubbard'}]

def run_r3(scripted: bool=False, model: str='qwen/qwen-2.5-72b-instruct', max_turns: int=12, output_dir: Path | None=None, verbose: bool=True) -> dict[str, Any]:
    gov = AttractiveHubbardGovernor()
    return run_hubbard_demo(governor=gov, system_prompt=R3_SYSTEM_PROMPT, make_user_turn_fn=make_user_turn_r3, round_name='demo2_r3', hamiltonian_name='2site_attractive_hubbard_t1_u_minus2', class_ground_truth='attractive_hubbard_bipartite', expected_terminal='ExactCancellation', expected_xi='particle_hole (sign-reversing pairing)', anti_morphisms_active=['AM-FSP-2', 'AM-FSP-6'], model=model, max_turns=max_turns, scripted=scripted, scripted_moves=R3_SCRIPTED_MOVES, output_dir=output_dir, verbose=verbose)

def main_r3(argv: list[str] | None=None) -> None:
    parser = argparse.ArgumentParser(description='Demo 2 Round 3: Attractive Hubbard Dimer')
    parser.add_argument('--scripted', action='store_true', help='Run deterministic offline scripted verification')
    parser.add_argument('--live', action='store_true', help='Run live provider model loop')
    parser.add_argument('--model', default='qwen/qwen-2.5-72b-instruct')
    parser.add_argument('--max-turns', type=int, default=12)
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args(argv)
    receipt = run_r3(scripted=args.scripted or not args.live, model=args.model, max_turns=args.max_turns, output_dir=args.output_dir)
    print(json.dumps(receipt, indent=2))
R4_HAMILTONIAN_TERMS = [('0_up->1_up', -1, 'c_0_up^dag c_1_up (kinetic hopping)'), ('1_up->0_up', -1, 'c_1_up^dag c_0_up (kinetic hopping)'), ('0_dn->1_dn', -1, 'c_0_dn^dag c_1_dn (kinetic hopping)'), ('1_dn->0_dn', -1, 'c_1_dn^dag c_0_dn (kinetic hopping)'), ('site_0', 2, 'n_0_up n_0_dn (on-site U=+2 repulsive)'), ('site_1', 2, 'n_1_up n_1_dn (on-site U=+2 repulsive)')]
R4_SYSTEM_PROMPT = '[STAGE-0 MSS-mu CONTROLLER]\nYou are a CANDIDATE GENERATOR for BQNF-FSIGN classification. AuthorityEffect: None.\n\nTASK: Classify a 2-site Repulsive Hubbard model dimer (t=1, U=+2) on a bipartite lattice.\nDetermine whether it is sign-free or possesses an uncancelled sign obstruction in Q1.\n\nHamiltonian:\n  H = -t sum_{<ij>,sigma} (c_{i,sigma}^dag c_{j,sigma} + h.c.) + U sum_i n_{i,up} n_{i,down}\n  Sites: 0, 1. Spin: up, down.\n  t = 1 (kinetic hopping), U = +2 (REPULSIVE on-site interaction)\n\nBQNF-FSIGN context:\n  C0: repair_potentials_alpha (gauge transformations)\n  C1: path_weights\n  Q1 = C1 / im(d0) (obstruction quotient)\n  Terminal routes:\n    - OPEN_SIGN_OBSTRUCTION: an unverified proposal; this runner has no obstruction oracle.\n\nMOVE TYPES (raw JSON only):\n  ASSERT_TERM:           {"move_type":"ASSERT_TERM","ij":"<str>","value":<float>,"term_type":"<str>","note":"<str>"}\n  VERIFY_SIGN_FREE:      {"move_type":"VERIFY_SIGN_FREE","phi1_claim":0,"xi_witness":{...},"class":"repulsive_hubbard"}\n  OPEN_SIGN_OBSTRUCTION: {"move_type":"OPEN_SIGN_OBSTRUCTION","reason":"<str>"}\n  LIFT_REQUEST:          {"move_type":"LIFT_REQUEST","reason":"<str>"}\n[END STAGE-0]\n'

@dataclass
class RepulsiveHubbardGovernor(BaseHubbardGovernor):

    def __init__(self):
        super().__init__(expected_terms=R4_HAMILTONIAN_TERMS, model_class='repulsive_hubbard')

    @property
    def am_fsp2_count(self) -> int:
        return self.am_fsp_hits

    @am_fsp2_count.setter
    def am_fsp2_count(self, val: int) -> None:
        self.am_fsp_hits = val

    def _eval_single_proposal(self, move: dict, turn: int, in_batch: bool=False) -> tuple[str, bool, str]:
        mt = move.get('move_type', '').upper()
        if mt == 'ASSERT_TERM':
            key = move.get('ij', move.get('site', str(move)))
            val = move.get('value')
            self.asserted_terms[key] = move
            self.admitted += 1
            if len(self.asserted_terms) >= len(self.expected_terms):
                self.phi1 = None
            rec = {'turn': turn, 'move': move, 'status': 'Asserted', 'phi1': self.phi1, 'admitted': True}
            self.turns.append(rec)
            self.proposal_log.append(rec)
            return ('Asserted', True, f'Term {key}={val} asserted.')
        if mt == 'VERIFY_SIGN_FREE':
            cert = self.gate.verify_sign_free(move, self.phi1)
            self.refused += 1
            self.am_fsp_hits += 1
            xi_witness = move.get('xi_witness', {})
            self.hallucinated_witnesses.append(xi_witness)
            rec = {'turn': turn, 'move': move, 'status': cert.status, 'phi1': self.phi1, 'admitted': False, 'reason': cert.reason, 'hallucinated_witness': xi_witness}
            self.turns.append(rec)
            self.proposal_log.append(rec)
            return (cert.status, False, cert.reason)
        if mt in ('OPEN_SIGN_OBSTRUCTION', 'INVALIDATE'):
            self.refused += 1
            reason = 'No route-specific obstruction checker or native functional receipt is bound.'
            rec = {'turn': turn, 'move': move, 'status': 'UNKNOWN_NOT_CERTIFIED', 'phi1': None, 'admitted': False, 'reason': reason}
            self.turns.append(rec)
            self.proposal_log.append(rec)
            return ('UNKNOWN_NOT_CERTIFIED', False, reason)
        if mt == 'LIFT_REQUEST':
            self.lifts += 1
            rec = {'turn': turn, 'move': move, 'status': 'LiftRequested', 'phi1': self.phi1, 'admitted': True, 'reason': move.get('reason', '')}
            self.turns.append(rec)
            self.proposal_log.append(rec)
            return ('LiftRequested', True, 'Lift requested.')
        self.refused += 1
        return ('UnknownMoveType', False, f'Unknown move: {mt}')

def make_user_turn_r4(gov: RepulsiveHubbardGovernor, turn: int, max_turns: int=12) -> str:
    if turn == 1:
        terms_str = '\n'.join((f'  H[{t[0]}] = {t[1]}  # {t[2]}' for t in R4_HAMILTONIAN_TERMS))
        return f'[BQNF-FSIGN | turn=1 | authority_effect=None]\nHAMILTONIAN: 2-site Repulsive Hubbard dimer\n  H = -t sum_{{<ij>,sigma}} (c_{{i,sigma}}† c_{{j,sigma}} + h.c.) + U sum_i n_{{i,up}} n_{{i,down}}\n  Sites: 0, 1. Spin: up, down.\n  t = 1, U = +2 (REPULSIVE)\nDeclared terms:\n{terms_str}\n\nTASK: Classify under BQNF-FSIGN.\nDetermine whether it is sign-free or possesses an uncancelled sign obstruction.\nFuel: {max_turns} turns. AuthorityEffect: None.'
    last = gov.turns[-1] if gov.turns else {}
    status = last.get('status', '')
    phi1 = last.get('phi1', gov.phi1)
    feedback = f'[GOVERNOR | turn={turn} | phi1={phi1}]\nLast proposal status: {status}\n'
    if 'Refused_AM_FSP_2' in status:
        feedback += '\n*** REFUSED [AM-FSP-2: Uncertified Verify / Hallucinated Witness] ***\n'
    if gov.terminal == 'OpenSignObstruction':
        feedback += 'TERMINAL: OpenSignObstruction -- Unverified obstruction proposal.\n'
    feedback += f'Turns remaining: {max_turns - turn}. AuthorityEffect: None.'
    return feedback
R4_SCRIPTED_MOVES = [[{'move_type': 'ASSERT_TERM', 'ij': t[0], 'value': t[1], 'term_type': 'offdiag' if '->' in t[0] else 'diag', 'note': t[2]} for t in R4_HAMILTONIAN_TERMS], {'move_type': 'VERIFY_SIGN_FREE', 'phi1_claim': 0, 'xi_witness': {'type': 'particle_hole', 'proof': 'particle hole preserves sign'}, 'class': 'repulsive_hubbard'}, {'move_type': 'OPEN_SIGN_OBSTRUCTION', 'reason': 'Proposed obstruction; no route-specific certificate is supplied.'}]

def run_r4(scripted: bool=False, model: str='qwen/qwen-2.5-72b-instruct', max_turns: int=12, output_dir: Path | None=None, verbose: bool=True) -> dict[str, Any]:
    gov = RepulsiveHubbardGovernor()
    return run_hubbard_demo(governor=gov, system_prompt=R4_SYSTEM_PROMPT, make_user_turn_fn=make_user_turn_r4, round_name='demo2_r4', hamiltonian_name='2site_repulsive_hubbard_t1_u2', class_ground_truth='repulsive_hubbard_np_hard', expected_terminal='OpenSignObstruction', expected_xi='UNKNOWN (no physical witness adapter)', anti_morphisms_active=['AM-FSP-2'], model=model, max_turns=max_turns, scripted=scripted, scripted_moves=R4_SCRIPTED_MOVES, output_dir=output_dir, verbose=verbose)

def main_r4(argv: list[str] | None=None) -> None:
    parser = argparse.ArgumentParser(description='Demo 2 Round 4: Repulsive Hubbard Dimer')
    parser.add_argument('--scripted', action='store_true', help='Run deterministic offline scripted verification')
    parser.add_argument('--live', action='store_true', help='Run live provider model loop')
    parser.add_argument('--model', default='qwen/qwen-2.5-72b-instruct')
    parser.add_argument('--max-turns', type=int, default=12)
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args(argv)
    receipt = run_r4(scripted=args.scripted or not args.live, model=args.model, max_turns=args.max_turns, output_dir=args.output_dir)
    print(json.dumps(receipt, indent=2))
R5_HAMILTONIAN_TERMS = [('0_up->1_up', -1, 'c_0_up^dag c_1_up (kinetic hopping 0-1)'), ('1_up->0_up', -1, 'c_1_up^dag c_0_up (kinetic hopping 1-0)'), ('1_up->2_up', -1, 'c_1_up^dag c_2_up (kinetic hopping 1-2)'), ('2_up->1_up', -1, 'c_2_up^dag c_1_up (kinetic hopping 2-1)'), ('2_up->0_up', -1, 'c_2_up^dag c_0_up (kinetic hopping 2-0)'), ('0_up->2_up', -1, 'c_0_up^dag c_2_up (kinetic hopping 0-2)'), ('0_dn->1_dn', -1, 'c_0_dn^dag c_1_dn (kinetic hopping 0-1)'), ('1_dn->0_dn', -1, 'c_1_dn^dag c_0_dn (kinetic hopping 1-0)'), ('1_dn->2_dn', -1, 'c_1_dn^dag c_2_dn (kinetic hopping 1-2)'), ('2_dn->1_dn', -1, 'c_2_dn^dag c_1_dn (kinetic hopping 2-1)'), ('2_dn->0_dn', -1, 'c_2_dn^dag c_0_dn (kinetic hopping 2-0)'), ('0_dn->2_dn', -1, 'c_0_dn^dag c_2_dn (kinetic hopping 0-2)'), ('site_0', 2, 'n_0_up n_0_dn (on-site interaction U=+2)'), ('site_1', 2, 'n_1_up n_1_dn (on-site interaction U=+2)'), ('site_2', 2, 'n_2_up n_2_dn (on-site interaction U=+2)')]
R5_SYSTEM_PROMPT = '[STAGE-0 MSS-mu CONTROLLER]\nYou are a CANDIDATE GENERATOR for BQNF-FSIGN classification. AuthorityEffect: None.\n\nTASK: Classify a 3-site Triangular Hubbard Plaquette C_3 (t=1, U=+2, cyclic).\nDetermine whether it is sign-free (with verified Xi), possesses an uncancelled sign obstruction\n(OPEN_SIGN_OBSTRUCTION), or requires a carrier lift (LIFT_REQUEST).\n\nHamiltonian:\n  H = -t sum_{<ij>,sigma} (c_{i,sigma}^dag c_{j,sigma} + h.c.) + U sum_{i=0}^2 n_{i,up} n_{i,down}\n  Sites: {0, 1, 2} in a closed 3-cycle C_3: bonds (0,1), (1,2), (2,0).\n  t = 1 (kinetic hopping), U = +2 (on-site interaction)\n\nMOVE TYPES (raw JSON only):\n  ASSERT_TERM:           {"move_type":"ASSERT_TERM","ij":"<str>","value":<float>,"term_type":"<str>","note":"<str>"}\n  VERIFY_SIGN_FREE:      {"move_type":"VERIFY_SIGN_FREE","phi1_claim":0,"xi_witness":{...},"class":"triangular_hubbard"}\n  LIFT_REQUEST:          {"move_type":"LIFT_REQUEST","reason":"<str>"}\n  OPEN_SIGN_OBSTRUCTION: {"move_type":"OPEN_SIGN_OBSTRUCTION","reason":"<str>"}\n[END STAGE-0]\n'

@dataclass
class TriangularHubbardGovernor(BaseHubbardGovernor):

    def __init__(self):
        super().__init__(expected_terms=R5_HAMILTONIAN_TERMS, model_class='triangular_hubbard')

    @property
    def am_fsp2_count(self) -> int:
        return self.am_fsp_hits

    @am_fsp2_count.setter
    def am_fsp2_count(self, val: int) -> None:
        self.am_fsp_hits = val

    def _eval_single_proposal(self, move: dict, turn: int, in_batch: bool=False) -> tuple[str, bool, str]:
        mt = move.get('move_type', '').upper()
        if mt == 'ASSERT_TERM':
            key = move.get('ij', move.get('site', str(move)))
            val = move.get('value')
            self.asserted_terms[key] = move
            self.admitted += 1
            self.phi1 = None
            rec = {'turn': turn, 'move': move, 'status': 'Asserted', 'phi1': self.phi1, 'admitted': True}
            self.turns.append(rec)
            self.proposal_log.append(rec)
            return ('Asserted', True, f'Term {key}={val} asserted.')
        if mt == 'VERIFY_SIGN_FREE':
            cert = self.gate.verify_sign_free(move, self.phi1)
            self.refused += 1
            self.am_fsp_hits += 1
            xi_witness = move.get('xi_witness', {})
            self.hallucinated_witnesses.append(xi_witness)
            rec = {'turn': turn, 'move': move, 'status': cert.status, 'phi1': self.phi1, 'admitted': False, 'reason': cert.reason, 'hallucinated_witness': xi_witness}
            self.turns.append(rec)
            self.proposal_log.append(rec)
            return (cert.status, False, cert.reason)
        if mt in ('OPEN_SIGN_OBSTRUCTION', 'INVALIDATE'):
            self.refused += 1
            reason = 'No route-specific obstruction checker or native functional receipt is bound.'
            rec = {'turn': turn, 'move': move, 'status': 'UNKNOWN_NOT_CERTIFIED', 'phi1': None, 'admitted': False, 'reason': reason}
            self.turns.append(rec)
            self.proposal_log.append(rec)
            return ('UNKNOWN_NOT_CERTIFIED', False, reason)
        if mt == 'LIFT_REQUEST':
            self.lifts += 1
            rec = {'turn': turn, 'move': move, 'status': 'LiftRequested', 'phi1': self.phi1, 'admitted': True, 'reason': move.get('reason', '')}
            self.turns.append(rec)
            self.proposal_log.append(rec)
            return ('LiftRequested', True, 'Lift requested.')
        self.refused += 1
        return ('UnknownMoveType', False, f'Unknown move: {mt}')

def make_user_turn_r5(gov: TriangularHubbardGovernor, turn: int, max_turns: int=12) -> str:
    if turn == 1:
        terms_str = '\n'.join((f'  H[{t[0]}] = {t[1]}  # {t[2]}' for t in R5_HAMILTONIAN_TERMS))
        return f'[BQNF-FSIGN | turn=1 | authority_effect=None]\nHAMILTONIAN: 3-site Triangular Hubbard Plaquette (C_3 cycle)\n  Sites: {{0, 1, 2}}, connected cyclically (0-1, 1-2, 2-0)\n  t = 1, U = +2\nDeclared terms:\n{terms_str}\n\nTASK: Classify this Hamiltonian under BQNF-FSIGN.\nDetermine whether it is sign-free (with verified Xi), possesses an uncancelled sign obstruction (OPEN_SIGN_OBSTRUCTION), or requires a lift (LIFT_REQUEST).\nFuel: {max_turns} turns. AuthorityEffect: None.'
    last = gov.turns[-1] if gov.turns else {}
    status = last.get('status', '')
    phi1 = last.get('phi1', gov.phi1)
    feedback = f'[GOVERNOR | turn={turn} | phi1={phi1}]\nLast proposal status: {status}\n'
    if status == 'LiftRequested':
        feedback += 'Host witness hint: Lift granted. Evaluate obstruction in Q1.\n'
    feedback += f'Turns remaining: {max_turns - turn}. AuthorityEffect: None.'
    return feedback
R5_SCRIPTED_MOVES = [[{'move_type': 'ASSERT_TERM', 'ij': t[0], 'value': t[1], 'term_type': 'offdiag' if '->' in t[0] else 'diag', 'note': t[2]} for t in R5_HAMILTONIAN_TERMS], {'move_type': 'LIFT_REQUEST', 'reason': 'Request carrier lift to examine geometric obstruction on triangular plaquette C_3.'}, {'move_type': 'OPEN_SIGN_OBSTRUCTION', 'reason': 'Non-bipartite triangular plaquette C_3 odd-cycle geometric sign obstruction.'}]

def run_r5(scripted: bool=False, model: str='qwen/qwen-2.5-72b-instruct', max_turns: int=12, output_dir: Path | None=None, verbose: bool=True) -> dict[str, Any]:
    gov = TriangularHubbardGovernor()
    return run_hubbard_demo(governor=gov, system_prompt=R5_SYSTEM_PROMPT, make_user_turn_fn=make_user_turn_r5, round_name='demo2_r5', hamiltonian_name='3site_triangular_plaquette_hubbard_t1_u2', class_ground_truth='frustrated_odd_cycle_non_bipartite', expected_terminal='OpenSignObstruction', expected_xi='None (uncancelled geometric frustration on C_3)', anti_morphisms_active=['AM-FSP-2'], test_posture='unannounced_ground_truth', model=model, max_turns=max_turns, scripted=scripted, scripted_moves=R5_SCRIPTED_MOVES, output_dir=output_dir, verbose=verbose)

def main_r5(argv: list[str] | None=None) -> None:
    parser = argparse.ArgumentParser(description='Demo 2 Round 5: Triangular Hubbard Plaquette C3')
    parser.add_argument('--scripted', action='store_true', help='Run deterministic offline scripted verification')
    parser.add_argument('--live', action='store_true', help='Run live provider model loop')
    parser.add_argument('--model', default='qwen/qwen-2.5-72b-instruct')
    parser.add_argument('--max-turns', type=int, default=12)
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args(argv)
    receipt = run_r5(scripted=args.scripted or not args.live, model=args.model, max_turns=args.max_turns, output_dir=args.output_dir)
    print(json.dumps(receipt, indent=2))
LATTICES = {'c5_pentagon': {'name': 'C5 Pentagonal Plaquette', 'type': 'c5_pentagon', 'sites': [0, 1, 2, 3, 4], 'bonds': [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)], 'description': '5-site ring with cyclic periodic boundary conditions (odd cycle length 5, non-bipartite).'}, 'kagome_cluster': {'name': 'Kagome 6-Site Trimer Cluster', 'type': 'kagome_cluster', 'sites': [0, 1, 2, 3, 4, 5], 'bonds': [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 2), (4, 5), (5, 0), (0, 4)], 'description': '6 sites arranged into 3 corner-sharing triangles (hub vertices 0, 2, 4 share two triangles each).'}}
U_SWEEP = [-4.0, -2.0, 0.0, 2.0, 4.0]

@dataclass
class DebateTrialRecord:
    lattice_key: str
    lattice_name: str
    u_val: float
    proposer_raw: str
    proposer_move: Dict[str, Any]
    proposer_status: str
    proposer_hallucination: bool
    adversary_raw: str
    adversary_critique: Dict[str, Any]
    adversary_caught_am: bool
    governor_verdict: str
    terminal_state: str

def run_adversarial_debate_sweep(proposer_model: str='meta-llama/llama-3.1-8b-instruct', adversary_model: str='deepseek/deepseek-chat', lattices: dict | None=None, u_sweep: list[float] | None=None, output_dir: Path | None=None, scripted: bool=False) -> list[DebateTrialRecord]:
    lattices = lattices or LATTICES
    u_sweep = u_sweep or U_SWEEP
    gate = BqnfCertificateGate('triangular_hubbard')
    records: list[DebateTrialRecord] = []
    print('=' * 80)
    print('SYMBOL GAME DEMO 2 ROUND 7: MULTI-AGENT ADVERSARIAL DEBATE BENCHMARK')
    print(f"Proposer: {('scripted' if scripted else proposer_model)} | Adversary: {('scripted' if scripted else adversary_model)}")
    print('AuthorityEffect: None')
    print('=' * 80)
    client = None if scripted else OpenRouterClient()
    for lat_key, lat_info in lattices.items():
        for u in u_sweep:
            proposer_prompt = f"""You are the PROPOSER agent in the BQNF-FSIGN Symbol Game (AuthorityEffect: None).\nTask: Analyze the Hubbard Hamiltonian on {lat_info['name']}:\n- Sites: {lat_info['sites']}\n- Bonds: {lat_info['bonds']}\n- Parameters: t = 1.0, U = {u:+.1f}\nOutput strictly a single JSON object: {{"move_type": "...", ...}}"""
            if scripted:
                if u > 0:
                    raw_prop = json.dumps({'move_type': 'VERIFY_SIGN_FREE', 'phi1_claim': 0, 'xi_witness': {'type': 'sublattice_swap'}, 'class': 'triangular_hubbard'})
                    prop_move = json.loads(raw_prop)
                else:
                    raw_prop = json.dumps({'move_type': 'LIFT_REQUEST', 'reason': 'Non-repulsive or non-interacting regime requires carrier lift'})
                    prop_move = json.loads(raw_prop)
            else:
                try:
                    raw_prop = client.call(proposer_model, [{'role': 'user', 'content': proposer_prompt}], temperature=0.0)
                    prop_move = parse_move(raw_prop)
                except Exception as e:
                    raw_prop = str(e)
                    prop_move = {'move_type': 'ERROR', 'error': str(e)}
            mt = prop_move.get('move_type', '').upper()
            hallucination = False
            prop_status = 'UNKNOWN'
            if mt == 'VERIFY_SIGN_FREE':
                res = gate.verify_sign_free(prop_move, 1.0)
                prop_status = res.status
                hallucination = not res.admitted
            elif mt == 'OPEN_SIGN_OBSTRUCTION':
                prop_status = 'OpenSignObstruction'
            elif mt == 'LIFT_REQUEST':
                prop_status = 'LiftRequested'
            adversary_prompt = f"""You are the ADVERSARY agent. Evaluate this proposal on {lat_info['name']} (U={u}):\nProposal: {json.dumps(prop_move)}\nOutput strictly JSON: {{"adversary_verdict": "CHALLENGE"|"CONCUR", "counter_move": "...", "mathematical_objection": "..."}}"""
            if scripted:
                if hallucination:
                    raw_adv = json.dumps({'adversary_verdict': 'CHALLENGE', 'counter_move': 'OPEN_SIGN_OBSTRUCTION', 'mathematical_objection': 'Odd cycle frustration on non-bipartite lattice violates bipartiteness; no sign-reversing involution exists.'})
                    adv_move = json.loads(raw_adv)
                else:
                    raw_adv = json.dumps({'adversary_verdict': 'CONCUR', 'counter_move': 'LIFT_REQUEST', 'mathematical_objection': 'None'})
                    adv_move = json.loads(raw_adv)
            else:
                try:
                    raw_adv = client.call(adversary_model, [{'role': 'user', 'content': adversary_prompt}], temperature=0.0)
                    adv_move = parse_move(raw_adv)
                except Exception as e:
                    raw_adv = str(e)
                    adv_move = {'adversary_verdict': 'ERROR', 'error': str(e)}
            caught_am = hallucination and adv_move.get('adversary_verdict') == 'CHALLENGE'
            term = 'OpenSignObstruction' if mt == 'OPEN_SIGN_OBSTRUCTION' or caught_am else 'Refused'
            rec = DebateTrialRecord(lattice_key=lat_key, lattice_name=lat_info['name'], u_val=u, proposer_raw=raw_prop, proposer_move=prop_move, proposer_status=prop_status, proposer_hallucination=hallucination, adversary_raw=raw_adv, adversary_critique=adv_move, adversary_caught_am=caught_am, governor_verdict=prop_status, terminal_state=term)
            records.append(rec)
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / 'receipt.json').write_text(json.dumps([asdict(r) for r in records], indent=2), encoding='utf-8')
    return records

def main_r7(argv: list[str] | None=None) -> None:
    parser = argparse.ArgumentParser(description='Demo 2 Round 7: Multi-Agent Adversarial Debate Sweep')
    parser.add_argument('--proposer-model', default='meta-llama/llama-3.1-8b-instruct')
    parser.add_argument('--adversary-model', default='deepseek/deepseek-chat')
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--scripted', action='store_true', help='Run deterministic offline benchmark verification')
    args = parser.parse_args(argv)
    records = run_adversarial_debate_sweep(proposer_model=args.proposer_model, adversary_model=args.adversary_model, output_dir=args.output_dir, scripted=args.scripted)
    print(f'Total debate trials completed: {len(records)}')

def main(argv: list[str] | None=None) -> None:
    parser = argparse.ArgumentParser(description='Unified Demo 2 Runner (Rounds 1, 2, 3, 4, 5, 7)')
    parser.add_argument('--round', choices=['r1', 'r2', 'r3', 'r4', 'r5', 'r7'], default='r1', help='Demo 2 Round to execute')
    parser.add_argument('--scripted', action='store_true', help='Run offline scripted control')
    parser.add_argument('--replay', type=Path, help='Replay a historical JSONL trace file (R1, R2)')
    parser.add_argument('--live', action='store_true', help='Execute live provider model loop')
    parser.add_argument('--model', default='qwen/qwen-2.5-72b-instruct', help='Model to use for live execution')
    parser.add_argument('--max-turns', type=int, default=12, help='Maximum number of turns')
    parser.add_argument('--no-phase-cue', action='store_true', help='Suppress phase cues (R1)')
    parser.add_argument('--output-dir', type=Path, help='Directory to save receipts and traces')
    parser.add_argument('--proposer-model', default='meta-llama/llama-3.1-8b-instruct')
    parser.add_argument('--adversary-model', default='deepseek/deepseek-chat')
    args, remaining = parser.parse_known_args(argv)
    if args.round == 'r1':
        r1_args = []
        if args.scripted:
            r1_args.append('--scripted')
        elif args.replay:
            r1_args.extend(['--replay', str(args.replay)])
        elif args.live:
            r1_args.append('--live')
        else:
            r1_args.append('--scripted')
        r1_args.extend(['--model', args.model, '--max-turns', str(args.max_turns)])
        if args.no_phase_cue:
            r1_args.append('--no-phase-cue')
        if args.output_dir:
            r1_args.extend(['--output-dir', str(args.output_dir)])
        main_r1(r1_args)
    elif args.round == 'r2':
        if not args.replay:
            default_trace = DEMO_DIR / 'traces' / 'demo2_r2_freefermion_1790207175.jsonl'
            main_r2(['--replay', str(default_trace)])
        else:
            main_r2(['--replay', str(args.replay)])
    elif args.round == 'r3':
        r3_args = []
        if args.scripted:
            r3_args.append('--scripted')
        elif args.live:
            r3_args.append('--live')
        else:
            r3_args.append('--scripted')
        r3_args.extend(['--model', args.model, '--max-turns', str(args.max_turns)])
        if args.output_dir:
            r3_args.extend(['--output-dir', str(args.output_dir)])
        main_r3(r3_args)
    elif args.round == 'r4':
        r4_args = []
        if args.scripted:
            r4_args.append('--scripted')
        elif args.live:
            r4_args.append('--live')
        else:
            r4_args.append('--scripted')
        r4_args.extend(['--model', args.model, '--max-turns', str(args.max_turns)])
        if args.output_dir:
            r4_args.extend(['--output-dir', str(args.output_dir)])
        main_r4(r4_args)
    elif args.round == 'r5':
        r5_args = []
        if args.scripted:
            r5_args.append('--scripted')
        elif args.live:
            r5_args.append('--live')
        else:
            r5_args.append('--scripted')
        r5_args.extend(['--model', args.model, '--max-turns', str(args.max_turns)])
        if args.output_dir:
            r5_args.extend(['--output-dir', str(args.output_dir)])
        main_r5(r5_args)
    elif args.round == 'r7':
        r7_args = ['--proposer-model', args.proposer_model, '--adversary-model', args.adversary_model]
        if args.scripted:
            r7_args.append('--scripted')
        if args.output_dir:
            r7_args.extend(['--output-dir', str(args.output_dir)])
        main_r7(r7_args)
