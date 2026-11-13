"""Narrow, no-retry OpenRouter adapter with conservative context-window quotes.

No key is read until the explicit CLI dispatch path constructs HTTPTransport.
Quotes assume the endpoint honours its advertised context/token ceilings and
tariff. A provider violating those premises can overbill; this is not a bank.
Only text, one provider endpoint, and ordinary token pricing are admitted.
"""
from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy
from decimal import Decimal, InvalidOperation, ROUND_CEILING
import json
import math
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler

from budget_ledger import BudgetError, integer
from reference_runner import Reply, canonical, sha

BASE = 'https://openrouter.ai/api/v1'
MAX_RESPONSE_BYTES = 8 * 1024 * 1024


class ProviderError(ValueError):
    pass


def decimal(value):
    if type(value) not in (str, int):
        raise ProviderError('Exact decimal string or integer required')
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ProviderError('Invalid decimal') from exc
    if not result.is_finite() or result < 0:
        raise ProviderError('Finite nonnegative decimal required')
    return result


def microusd(value):
    return int((decimal(value) * 1_000_000).to_integral_value(rounding=ROUND_CEILING))


def price_ceiling(value):
    """JSON numeric ceiling no greater than the exact reserved decimal tariff."""
    number = float(value)
    if not math.isfinite(number):
        raise ProviderError('Price cannot be represented as a finite JSON number')
    if Decimal(str(number)) > value:
        number = math.nextafter(number, -math.inf)
    return number


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
    return json.loads(raw, parse_float=str, parse_constant=reject_constant, object_pairs_hook=unique_object)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProviderError('Redirect refused; credential destination is fixed')


class HTTPTransport:
    """One synchronous request; no SDK, proxy, redirect, streaming or retry loop."""
    def __init__(self, api_key, timeout_seconds=120):
        if not isinstance(api_key, str) or not api_key or any(c.isspace() for c in api_key):
            raise ProviderError('OPENROUTER_API_KEY is missing or malformed')
        integer(timeout_seconds, 'timeout', positive=True)
        self._key = api_key
        self.timeout = timeout_seconds
        self._opener = build_opener(ProxyHandler({}), NoRedirect())

    def request(self, method, path, body=None):
        if method == 'GET' and re.fullmatch(r'/models/[A-Za-z0-9_.%:-]+/[A-Za-z0-9_.%:-]+/endpoints', path):
            pass
        elif method == 'POST' and path == '/chat/completions':
            pass
        else:
            raise ProviderError('Endpoint outside the fixed transport allowlist')
        headers = {'Authorization': 'Bearer ' + self._key, 'Content-Type': 'application/json'}
        request = Request(BASE + path, data=canonical(body) if body is not None else None,
                          headers=headers, method=method)
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except HTTPError as exc:
            # Do not persist a server-supplied error body or a credential-bearing request.
            raise ProviderError(f'HTTP {exc.code}; no retry; charge requires reconciliation') from None
        except (URLError, TimeoutError, OSError):
            raise ProviderError('Transport failed; no retry; charge requires reconciliation') from None
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ProviderError('Response exceeded local byte ceiling')
        return raw, parse_json(raw)


@dataclass(frozen=True)
class Prepared:
    request_sha256: str
    wire: dict
    evidence: dict
    quote_microusd: int
    context_bound: int
    output_bound: int
    provider_name: str
    prepared_at: float


class OpenRouterProvider:
    offline = False

    def __init__(self, model, endpoint_slug, transport):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', model):
            raise ProviderError('Concrete model slug required; routing variants are not admitted')
        if model.startswith('openrouter/'):
            raise ProviderError('Router models are not admitted')
        if not re.fullmatch(r'[a-z0-9_.-]+(?:/[a-z0-9_.-]+)*', endpoint_slug):
            raise ProviderError('Concrete endpoint slug required')
        self.model = model
        self.endpoint_slug = endpoint_slug
        self.transport = transport
        self.name = f'openrouter:{model}@{endpoint_slug}'
        self._prepared = None

    @property
    def admission_identity(self):
        return {'adapter': 'openrouter-context-bound-v1', 'model': self.model, 'endpoint_slug': self.endpoint_slug}

    def upper_quote(self, request):
        if self._prepared is not None:
            raise ProviderError('Previous prepared dispatch must not be overwritten')
        if set(request) != {'messages', 'max_output_tokens', 'tools', 'retries'}:
            raise ProviderError('Unexpected request fields')
        if request['tools'] != [] or type(request['retries']) is not int or request['retries'] != 0:
            raise ProviderError('Tools and retries are not admitted')
        messages = request['messages']
        if not isinstance(messages, list) or not messages:
            raise ProviderError('Text messages required')
        for message in messages:
            if set(message) != {'role', 'content'} or message['role'] not in {'system', 'user', 'assistant'} or type(message['content']) is not str:
                raise ProviderError('Only ordinary text messages are admitted')
        output = integer(request['max_output_tokens'], 'max output tokens', positive=True)
        author, slug = self.model.split('/')
        raw, data = self.transport.request('GET', f'/models/{quote(author)}/{quote(slug)}/endpoints')
        metadata = data['data']
        if metadata.get('id') != self.model:
            raise ProviderError('Metadata model identity mismatch')
        architecture = metadata.get('architecture', {})
        if 'text' not in architecture.get('input_modalities', []) or architecture.get('output_modalities') != ['text']:
            raise ProviderError('Only a text-output endpoint is admitted')
        # Routing slugs are prefixes. Refuse ambiguous descendants instead of
        # pretending that a base provider name pins a region or variant.
        candidates = [e for e in metadata['endpoints'] if e.get('tag') == self.endpoint_slug or
                      str(e.get('tag', '')).startswith(self.endpoint_slug + '/')]
        if len(candidates) != 1 or candidates[0].get('tag') != self.endpoint_slug:
            raise ProviderError('Endpoint slug is absent or ambiguously matches variants')
        endpoint = candidates[0]
        if endpoint.get('model_id') != self.model or type(endpoint.get('status')) is not int or endpoint['status'] != 0:
            raise ProviderError('Endpoint model or availability mismatch')
        if 'max_tokens' not in endpoint.get('supported_parameters', []):
            raise ProviderError('Endpoint does not advertise max_tokens enforcement')
        context = integer(endpoint.get('context_length'), 'endpoint context', positive=True)
        max_prompt = endpoint.get('max_prompt_tokens')
        if max_prompt is not None:
            context = min(context, integer(max_prompt, 'max prompt tokens', positive=True))
        max_completion = integer(endpoint.get('max_completion_tokens'), 'max completion tokens', positive=True)
        if output > max_completion or output > endpoint['context_length']:
            raise ProviderError('Requested output exceeds endpoint ceiling')
        pricing = endpoint.get('pricing', {})
        known = {'prompt', 'completion', 'request', 'image', 'web_search', 'internal_reasoning',
                 'input_cache_read', 'input_cache_write', 'overrides', 'discount'}
        if set(pricing) - known or pricing.get('overrides') not in (None, []):
            raise ProviderError('Unknown tariff fields or conditional pricing are not admitted')
        if not {'prompt', 'completion'} <= set(pricing):
            raise ProviderError('Incomplete tariff')
        prompt = decimal(pricing['prompt']); completion = decimal(pricing['completion'])
        for field in ('request', 'image', 'web_search', 'internal_reasoning', 'input_cache_write', 'discount'):
            if decimal(pricing.get(field, '0')) != 0:
                raise ProviderError('Fixed, auxiliary or cache-write charges are not admitted')
        if decimal(pricing.get('input_cache_read', '0')) > prompt:
            raise ProviderError('Cache-read tariff exceeds reserved prompt tariff')
        provider_name = endpoint.get('provider_name')
        if type(provider_name) is not str or not provider_name:
            raise ProviderError('Provider identity missing')
        upper = microusd(str(context * prompt + output * completion))
        wire = {'model': self.model, 'messages': messages, 'max_tokens': output, 'stream': False,
                'provider': {'only': [self.endpoint_slug], 'order': [self.endpoint_slug],
                             'allow_fallbacks': False, 'require_parameters': True,
                             'max_price': {'prompt': price_ceiling(prompt * 1_000_000),
                                           'completion': price_ceiling(completion * 1_000_000), 'request': 0}}}
        evidence = {'adapter_identity': self.admission_identity, 'metadata_sha256': sha(raw),
                    'endpoint_snapshot': endpoint, 'wire_request': wire, 'wire_request_sha256': sha(canonical(wire)),
                    'input_token_bound': context, 'output_token_bound': output,
                    'quote_method': 'entire_advertised_input_context_plus_capped_completion',
                    'premises': ['Advertised endpoint ceilings remain enforced for this request.',
                                 'Routing, tariff and max_tokens controls are honoured.',
                                 'Omitted auxiliary tariff fields mean no such charge; per-request price is also capped at zero.',
                                 'Ordinary completion tokens include any billable reasoning tokens; no unlisted fees.']}
        self._prepared = Prepared(sha(canonical(request)), wire, evidence, upper, context, output,
                                  provider_name, time.monotonic())
        return upper

    def request_evidence(self):
        if self._prepared is None:
            raise ProviderError('No prepared request')
        return deepcopy(self._prepared.evidence)

    def complete(self, request):
        prepared = self._prepared
        self._prepared = None  # consume before network; a timeout cannot be replayed
        if prepared is None or sha(canonical(request)) != prepared.request_sha256:
            raise ProviderError('No matching prepared request')
        if sha(canonical(prepared.wire)) != prepared.evidence['wire_request_sha256']:
            raise ProviderError('Prepared wire changed after quotation')
        if time.monotonic() - prepared.prepared_at > 30:
            raise ProviderError('Tariff observation expired before dispatch')
        raw, result = self.transport.request('POST', '/chat/completions', prepared.wire)
        violations = []
        if not isinstance(result, dict):
            result = {}
            violations.append('Response is not a JSON object')
        usage = result.get('usage', {})
        if not isinstance(usage, dict):
            usage = {}
            violations.append('Usage is not a JSON object')
        charge = None
        if usage.get('cost') is not None:
            try:
                charge = microusd(usage['cost'])
            except ProviderError:
                violations.append('Invalid reported cost')
        input_tokens = usage.get('prompt_tokens'); output_tokens = usage.get('completion_tokens')
        details = usage.get('completion_tokens_details') or {}
        reasoning_tokens = details.get('reasoning_tokens') if isinstance(details, dict) else None
        def token(value):
            if value is not None and (type(value) is not int or value < 0):
                violations.append('Invalid reported token count')
                return None
            return value
        input_tokens, output_tokens, reasoning_tokens = map(token, (input_tokens, output_tokens, reasoning_tokens))
        if input_tokens is None or output_tokens is None:
            violations.append('Token usage unavailable; cannot validate billing premises')
        elif input_tokens > prepared.context_bound or output_tokens > prepared.output_bound:
            violations.append('Provider exceeded a reserved token ceiling')
        if result.get('model') != self.model or result.get('provider') != prepared.provider_name:
            violations.append('Returned model/provider differs from the admitted endpoint')
        choices = result.get('choices', [])
        if not isinstance(choices, list):
            choices = []
        text = None
        choice = choices[0] if len(choices) == 1 and isinstance(choices[0], dict) else {}
        if choice:
            message = choice.get('message', {})
            if not isinstance(message, dict):
                message = {}
            text = message.get('content')
            if message.get('tool_calls') or message.get('function_call'):
                violations.append('Unexpected tool call')
        if type(text) is not str:
            # Preserve a known bill even when there is no publishable answer.
            text = ''
            violations.append('Missing single text answer')
        else:
            try:
                text.encode('utf-8')
            except UnicodeError:
                text = ''
                violations.append('Answer contains invalid Unicode')
        finish_reason = choice.get('finish_reason', 'unavailable')
        request_id = result.get('id')
        for name, value in (('finish_reason', finish_reason), ('request_id', request_id)):
            valid = type(value) is str or (name == 'request_id' and value is None)
            if valid and value is not None:
                try:
                    value.encode('utf-8')
                except UnicodeError:
                    valid = False
            if not valid:
                violations.append('Invalid ' + name)
                if name == 'finish_reason': finish_reason = 'unavailable'
                else: request_id = None
        # Retain the known charge even if any nested provider metadata contains
        # malformed Unicode. Lossless ASCII-escaped evidence remains writable.
        malformed_response = None
        try:
            canonical(result)
        except UnicodeError:
            violations.append('Provider response contains invalid Unicode')
            malformed_response = json.dumps(result, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)
        return Reply(text, charge, input_tokens, output_tokens, reasoning_tokens,
                     finish_reason, request_id,
                     provider_evidence={'response_sha256': sha(raw), 'usage': usage,
                                        'reported_model': result.get('model'), 'reported_provider': result.get('provider'),
                                        'reported_finish_reason': choice.get('finish_reason'), 'reported_request_id': result.get('id'),
                                        'malformed_response_ascii_json': malformed_response},
                     accounting_error='; '.join(violations) if violations else None)
