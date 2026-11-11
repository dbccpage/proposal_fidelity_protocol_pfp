"""Narrow, no-retry, single-use adapter for the Anthropic Messages API.

Same safety bar as openrouter_provider: one fixed endpoint, no SDK, no proxy,
no redirect, no retry, no fallback model, duplicate-key-refusing JSON, hashed
prepared requests consumed before the network, a 30 second quote expiry, and
violations collected into ``accounting_error`` while a known charge is kept.

No key is read until the explicit live path calls ``transport_from_environment``.
Quotes hold only under the declared premises (pinned tariff, at most one token
per UTF-8 byte plus fixed overheads, provider enforcement of ``max_tokens``).
A provider violating those premises can overbill; this module is not a bank.
``Reply``, ``canonical`` and ``sha`` are reused from reference_runner.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from budget_ledger import MAX_RUN_MICROUSD, integer, quote_microusd
from reference_runner import Reply, canonical, sha

URL = 'https://api.anthropic.com/v1/messages'
API_VERSION = '2023-06-01'
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
QUOTE_TTL_SECONDS = 30
PER_MESSAGE_OVERHEAD_TOKENS = 16
PER_REQUEST_OVERHEAD_TOKENS = 512

# Source: claude-api skill model/pricing tables (cached 2026-11-03), read on the
# date below. Prices are USD per million tokens as decimal strings, which equal
# microUSD per token. Re-verify against https://docs.claude.com pricing before
# any live run. 'thinking' is 'adaptive' (on by default, budget_tokens rejected
# by the API) or 'manual' (budget_tokens admitted). A 'long' tier reprices the
# whole request when input tokens exceed 'long_above'.
PRICING_OBSERVED_ON = '2026-11-10'
PRICING = {
    'claude-opus-5-5': {'input': '4.00', 'output': '20.00', 'context': 1_000_000,
                        'max_output': 128_000, 'thinking': 'adaptive'},
    'claude-sonnet-5-5': {'input': '2.00', 'output': '10.00', 'context': 1_000_000,
                          'max_output': 128_000, 'thinking': 'adaptive'},
    'claude-haiku-5-5': {'input': '0.10', 'output': '0.50', 'context': 1_000_000,
                         'max_output': 128_000, 'thinking': 'adaptive',
                         'long_above': 100_000, 'long_input': '0.50', 'long_output': '2.50'},
    'claude-haiku-4-5-20251001': {'input': '1.00', 'output': '5.00', 'context': 200_000,
                                  'max_output': 64_000, 'thinking': 'manual'},
}
# Aliases that the skill lists next to a dated snapshot id are refused.
REFUSED_ALIASES = {'claude-haiku-4-5'}


class ProviderError(ValueError):
    pass


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProviderError('Duplicate JSON key')
        result[key] = value
    return result


def parse_json(raw):
    def reject_constant(value):
        raise ProviderError('Nonfinite JSON number')
    try:
        return json.loads(raw, parse_float=str, parse_constant=reject_constant, object_pairs_hook=unique_object)
    except ValueError as exc:
        raise ProviderError('Response is not valid JSON; charge requires reconciliation') from exc


def tariff(row, input_tokens):
    if 'long_above' in row and input_tokens > row['long_above']:
        return row['long_input'], row['long_output']
    return row['input'], row['output']


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProviderError('Redirect refused; credential destination is fixed')


class HTTPTransport:
    """One synchronous POST; no SDK, proxy, redirect, streaming or retry loop."""
    def __init__(self, api_key, timeout_seconds=120):
        if not isinstance(api_key, str) or not api_key or any(c.isspace() for c in api_key):
            raise ProviderError('ANTHROPIC_API_KEY is missing or malformed')
        integer(timeout_seconds, 'timeout', positive=True)
        self._key = api_key
        self.timeout = timeout_seconds
        self._opener = build_opener(ProxyHandler({}), NoRedirect())

    def __repr__(self):
        return f'HTTPTransport(url={URL!r}, timeout_seconds={self.timeout})'

    def request(self, method, path, body):
        if method != 'POST' or path != '/v1/messages':
            raise ProviderError('Endpoint outside the fixed transport allowlist')
        headers = {'x-api-key': self._key, 'anthropic-version': API_VERSION, 'content-type': 'application/json'}
        request = Request(URL, data=canonical(body), headers=headers, method='POST')
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except HTTPError as exc:
            code = exc.code
            exc.close()  # the server error body is not read or persisted
            raise ProviderError(f'HTTP {code}; no retry; charge unknown, requires reconciliation') from None
        except (URLError, TimeoutError, OSError):
            raise ProviderError('Transport failed after possible transmission; no retry; '
                                'charge unknown, requires reconciliation') from None
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ProviderError('Response exceeded local byte ceiling; charge requires reconciliation')
        return raw, parse_json(raw)


def transport_from_environment(timeout_seconds=120):
    """Explicit live path only: the single place that reads ANTHROPIC_API_KEY."""
    return HTTPTransport(os.environ.get('ANTHROPIC_API_KEY'), timeout_seconds)


@dataclass(frozen=True)
class Prepared:
    request_sha256: str
    wire: dict
    evidence: dict
    quote_microusd: int
    input_bound: int
    output_bound: int
    prepared_at: float


class AnthropicProvider:
    """Single-use: one prepare, at most one dispatch, then the instance is spent."""
    offline = False

    def __init__(self, model, transport, budget_tokens=0):
        if model in REFUSED_ALIASES or model not in PRICING:
            raise ProviderError('Unknown model or undated alias; only pinned concrete ids are admitted')
        integer(budget_tokens, 'budget tokens')
        if budget_tokens and PRICING[model]['thinking'] != 'manual':
            raise ProviderError('budget_tokens is not admitted for this model')
        if budget_tokens and budget_tokens < 1024:
            raise ProviderError('budget_tokens must be at least 1024')
        self.model = model
        self.row = dict(PRICING[model])
        self.budget_tokens = budget_tokens
        self.transport = transport
        self.name = f'anthropic:{model}'
        self._prepared = None
        self._state = 'fresh'

    @property
    def admission_identity(self):
        return {'adapter': 'anthropic-byte-bound-v1', 'model': self.model, 'budget_tokens': self.budget_tokens,
                'pricing_observed_on': PRICING_OBSERVED_ON}

    def _prepare(self, request):
        if self._state != 'fresh':
            raise ProviderError('Instance already prepared or dispatched; use a new instance')
        self._state = 'spent'  # any refusal below also spends the instance
        if not isinstance(request, dict) or set(request) != {'messages', 'max_output_tokens', 'tools', 'retries'}:
            raise ProviderError('Unexpected request fields')
        if request['tools'] != [] or type(request['retries']) is not int or request['retries'] != 0:
            raise ProviderError('Tools and retries are not admitted')
        messages = request['messages']
        if not isinstance(messages, list) or not messages:
            raise ProviderError('Text messages required')
        for message in messages:
            if (not isinstance(message, dict) or set(message) != {'role', 'content'}
                    or message['role'] not in {'system', 'user', 'assistant'}
                    or type(message['content']) is not str or not message['content'].strip()):
                raise ProviderError('Only ordinary non-empty text messages are admitted')
        system = None
        if messages[0]['role'] == 'system':
            system, messages = messages[0]['content'], messages[1:]
        if any(m['role'] == 'system' for m in messages):
            raise ProviderError('System message admitted only in the leading position')
        if not messages or messages[0]['role'] != 'user' or messages[-1]['role'] != 'user':
            raise ProviderError('Conversation must start and end with a user message (no prefill)')
        output = integer(request['max_output_tokens'], 'max output tokens', positive=True)
        if output > self.row['max_output']:
            raise ProviderError('Requested output exceeds model ceiling')
        if self.budget_tokens and self.budget_tokens >= output:
            raise ProviderError('budget_tokens must be below max_tokens')
        texts = [m['content'] for m in request['messages']]
        try:
            text_bytes = sum(len(t.encode('utf-8')) for t in texts)
        except UnicodeError:
            raise ProviderError('Message text is not valid Unicode') from None
        input_bound = text_bytes + PER_MESSAGE_OVERHEAD_TOKENS * len(texts) + PER_REQUEST_OVERHEAD_TOKENS
        if input_bound > self.row['context']:
            raise ProviderError('Input bound exceeds model context window')
        in_price, out_price = tariff(self.row, input_bound)
        quote = quote_microusd(input_bound, output, in_price, out_price)
        if quote > MAX_RUN_MICROUSD:
            raise ProviderError('Quote exceeds the per-run cap')
        wire = {'model': self.model, 'max_tokens': output, 'messages': deepcopy(messages), 'stream': False}
        if system is not None:
            wire['system'] = system
        if self.budget_tokens:
            wire['thinking'] = {'type': 'enabled', 'budget_tokens': self.budget_tokens}
        evidence = {'adapter_identity': self.admission_identity, 'pricing_row': self.row,
                    'applied_tariff': {'input': in_price, 'output': out_price},
                    'wire_request': wire, 'wire_request_sha256': sha(canonical(wire)),
                    'input_token_bound': input_bound, 'output_token_bound': output, 'quote_microusd': quote,
                    'quote_method': 'utf8_bytes_plus_fixed_overheads_times_input_plus_max_tokens_times_output_ceiling',
                    'premises': [
                        'Pinned tariff matches the live Anthropic price list; re-verify before any live run.',
                        'Byte-level BPE yields at most one input token per UTF-8 byte; per-message and '
                        'per-request overheads cover role and framing tokens. A premise, not a proof.',
                        'The API enforces max_tokens over text plus any thinking tokens, which bill as output.',
                        'No cache_control, tools, fallbacks, speed or service tier are sent, so no cache, '
                        'tool, fast-mode or priority charges apply.']}
        self._prepared = Prepared(sha(canonical(request)), wire, evidence, quote, input_bound, output, time.monotonic())
        return quote

    def upper_quote(self, request):
        quote = self._prepare(request)
        self._state = 'prepared'
        return quote

    def preflight(self, request):
        """Quote and evidence only; this instance can never dispatch."""
        quote = self._prepare(request)
        self._state = 'preflight_only'
        return quote, self.request_evidence()

    def request_evidence(self):
        if self._prepared is None:
            raise ProviderError('No prepared request')
        return deepcopy(self._prepared.evidence)

    def complete(self, request):
        prepared, state = self._prepared, self._state
        self._prepared, self._state = None, 'spent'  # consume before network; no replay
        if state != 'prepared' or prepared is None:
            raise ProviderError('Instance is not in a dispatchable prepared state')
        if sha(canonical(request)) != prepared.request_sha256:
            raise ProviderError('Request changed after quotation')
        if sha(canonical(prepared.wire)) != prepared.evidence['wire_request_sha256']:
            raise ProviderError('Prepared wire changed after quotation')
        if time.monotonic() - prepared.prepared_at > QUOTE_TTL_SECONDS:
            raise ProviderError('Quote expired before dispatch')
        raw, result = self.transport.request('POST', '/v1/messages', prepared.wire)
        return self._reply(raw, result, prepared)

    def _reply(self, raw, result, prepared):
        violations = []
        if not isinstance(result, dict):
            result = {}
            violations.append('Response is not a JSON object')
        usage = result.get('usage')
        if not isinstance(usage, dict):
            usage = {}
        tokens = [usage.get('input_tokens'), usage.get('output_tokens')]
        valid = all(type(v) is int and v >= 0 for v in tokens)
        input_tokens, output_tokens = tokens if valid else (None, None)
        charge = None
        if not valid:
            violations.append('Token usage missing or invalid; liability unknown')
        elif any(usage.get(k) not in (None, 0) for k in ('cache_creation_input_tokens', 'cache_read_input_tokens')):
            violations.append('Cache tokens reported; not admitted; liability unknown')
        elif usage.get('speed') not in (None, 'standard') or usage.get('service_tier') not in (None, 'standard'):
            violations.append('Non-standard speed or service tier; liability unknown')
        else:
            in_price, out_price = tariff(self.row, input_tokens)
            charge = quote_microusd(input_tokens, output_tokens, in_price, out_price)
            if input_tokens > prepared.input_bound or output_tokens > prepared.output_bound:
                violations.append('Provider exceeded a reserved token bound')
            if charge > prepared.quote_microusd:
                violations.append('Computed charge exceeded the quote')
        if result.get('model') != self.model:
            violations.append('Returned model differs from the admitted model')
        if result.get('type') != 'message' or result.get('role') != 'assistant':
            violations.append('Unexpected response type or role')
        blocks = result.get('content')
        parts = []
        for block in blocks if isinstance(blocks, list) else []:
            kind = block.get('type') if isinstance(block, dict) else None
            if kind == 'text' and type(block.get('text')) is str:
                parts.append(block['text'])
            elif kind not in ('thinking', 'redacted_thinking'):
                violations.append(f'Unexpected content block: {ascii(kind)[:40]}')
        text = ''.join(parts)
        if not parts:
            violations.append('Missing text answer')
        finish_reason, request_id = result.get('stop_reason'), result.get('id')
        if type(finish_reason) is not str:
            finish_reason = 'unavailable'
            violations.append('Invalid stop_reason')
        if request_id is not None and type(request_id) is not str:
            request_id = None
            violations.append('Invalid request id')
        malformed = None
        try:
            canonical(result)
            text.encode('utf-8')
        except UnicodeError:
            # Keep the known charge; evidence stays writable as ASCII-escaped JSON.
            violations.append('Provider response contains invalid Unicode')
            text = ''
            malformed = json.dumps(result, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)
        return Reply(text, charge, input_tokens, output_tokens, None, finish_reason, request_id,
                     provider_evidence={'response_sha256': sha(raw), 'usage': usage,
                                        'reported_model': result.get('model'),
                                        'reported_stop_reason': result.get('stop_reason'),
                                        'reported_request_id': result.get('id'),
                                        'malformed_response_ascii_json': malformed},
                     accounting_error='; '.join(violations) if violations else None)
