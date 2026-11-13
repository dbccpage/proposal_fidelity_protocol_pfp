"""Provider adapters: Provider_a (official SDK) and Provider_b-compatible HTTPS (urllib) for the free tiers.

AuthorityEffect: None. Adapters send one request per call, never retry silently, never log a key, and
return every field the receipt needs (provider, model, tokens, cost, request id, stop reason).

Reference: upstream_repo private_engine/infrastructure/providers (provider_b_compat.py, http.py,
local_host_local.py, adapters/model_backends.py with its MODEL_PROVIDER selector). Ported ideas:
a bounded reply read, redacted classified failures, an unreported cost is unknown (not zero), Local_host
reached on the loopback host and probed before use. Not ported: the native Rust host, the SQLite
accounting and the PFP task-turn envelope (see design.md for the mapping).

provider_a 0.76 does not type `output_config`, so effort and the JSON-schema format travel in
`extra_body`. Adaptive thinking is requested with thinking={"type": "adaptive"}; budget_tokens is never
sent (it is a 400 on these models). Sampling parameters are never sent.
"""
from __future__ import annotations

import json
import re
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from .budget import cost_microusd as rate_cost
from .config import PRICES, PROVIDERS

MAX_REPLY_BYTES = 8 * 1024 * 1024
USER_AGENT = 'pfp-model-ladder/1.0'


@dataclass
class CallRequest:
    model: str
    system: str
    user: str
    max_tokens: int
    schema: dict | None = None
    schema_name: str = 'pfp_p0'
    effort: str | None = None
    stream: bool = False
    timeout: float = 180.0
    body_extra: dict = field(default_factory=dict)


@dataclass
class CallResult:
    provider: str
    model: str
    text: str
    input_tokens: int | None
    output_tokens: int | None
    cost_microusd: int | None
    cost_source: str
    request_id: str | None
    stop_reason: str | None
    refusal: bool = False
    stop_category: str | None = None
    truncated: bool = False
    latency_s: float = 0.0
    streamed: bool = False
    effort: str | None = None
    structured_mode: str = 'none'
    backoff_events: list = field(default_factory=list)
    http_status: int | None = None


class ProviderError(Exception):
    """A classified failure with no secret in it. `ambiguous` means the request may have been billed."""

    def __init__(self, code, message='', *, status=None, retry_after=None, ambiguous=False, backoff_events=None):
        super().__init__(code + (': ' + message if message else ''))
        self.code, self.message, self.status = code, message, status
        self.retry_after, self.ambiguous = retry_after, ambiguous
        self.backoff_events = backoff_events or []


# --------------------------------------------------------------------------- helpers
def extract_json(text: str):
    """(object or None, error or None). Tolerates fences and leading prose; never evals."""
    if not isinstance(text, str) or not text.strip():
        return None, 'empty_reply'
    candidate = text.strip()
    fence = re.search(r'```(?:json)?\s*\n(.*?)```', candidate, re.S)
    if fence:
        candidate = fence.group(1).strip()
    try:
        return json.loads(candidate), None
    except ValueError:
        pass
    start = candidate.find('{')
    if start >= 0:
        try:
            value, _ = json.JSONDecoder().raw_decode(candidate[start:])
            return value, None
        except ValueError as error:
            return None, 'invalid_json: ' + str(error)[:120]
    return None, 'no_json_object'


def _wait_from_body(body: str):
    """Seconds named by 'try again in 1m17.5s' / '250ms' / '2h3m' style messages, else None."""
    match = re.search(r'try again in\s+((?:\d+(?:\.\d+)?(?:ms|h|m|s))+)', body or '', re.I)
    if not match:
        return None
    total = 0.0
    for value, unit in re.findall(r'(\d+(?:\.\d+)?)(ms|h|m|s)', match.group(1), re.I):
        total += float(value) * {'ms': 0.001, 's': 1.0, 'm': 60.0, 'h': 3600.0}[unit.lower()]
    return total


def default_transport(url, headers, body, timeout):
    request = urllib.request.Request(url, data=body, headers=dict(headers), method='POST')
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_REPLY_BYTES + 1)
            return response.status, {k.lower(): v for k, v in response.headers.items()}, raw
    except urllib.error.HTTPError as error:
        try:
            raw = error.read(MAX_REPLY_BYTES + 1)
        finally:
            error.close()
        return error.code, {k.lower(): v for k, v in error.headers.items()}, raw
    except (socket.timeout, TimeoutError):
        raise ProviderError('timeout', 'no reply before the deadline', ambiguous=True) from None
    except urllib.error.URLError as error:
        reason = getattr(error, 'reason', None)
        if isinstance(reason, (socket.timeout, TimeoutError)):
            raise ProviderError('timeout', 'no reply before the deadline', ambiguous=True) from None
        raise ProviderError('transport', type(reason).__name__ if reason else 'URLError') from None
    except OSError as error:
        raise ProviderError('transport', type(error).__name__) from None


# --------------------------------------------------------------------------- Provider_b-compatible
class ProviderBCompatProvider:
    """Host_g, Host_c, HOST_N NIM, Router_r and Local_host: POST {base}/chat/completions."""

    def __init__(self, name, api_key, *, config=None, transport=None, sleeper=time.sleep, clock=time.monotonic,
                 base_url=None):
        self.name = name
        self.cfg = dict(config or PROVIDERS[name])
        if base_url:
            self.cfg['base_url'] = base_url
        self._key = api_key
        self._transport = transport or default_transport
        self._sleep, self._clock = sleeper, clock
        self._last = None

    @property
    def available(self) -> bool:
        return bool(self._key) or self.cfg.get('key') is None

    def estimate_input_tokens(self, req: CallRequest) -> int:
        schema = json.dumps(req.schema) if req.schema else ''
        return (len((req.system + req.user + schema).encode('utf-8')) + 2) // 3 + 16

    def _pace(self):
        gap = self.cfg.get('min_interval_s', 0.0)
        if self._last is not None and gap:
            wait = gap - (self._clock() - self._last)
            if wait > 0:
                self._sleep(wait)

    def _body(self, req: CallRequest, structured: str) -> dict:
        system = req.system
        if structured != 'json_schema' and req.schema:
            # No enforced schema (provider without support, or the 400 fallback): the model must see the schema in the text.
            system += ('\n\nThe provider does not enforce the response schema. Your reply must validate against this JSON schema:\n'
                       + json.dumps(req.schema, separators=(',', ':'), ensure_ascii=False))
        body = {'model': req.model,
                'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': req.user}],
                self.cfg.get('max_tokens_field', 'max_tokens'): req.max_tokens}
        body.update(self.cfg.get('body_extra', {}))
        body.update(req.body_extra or {})
        if structured == 'json_schema' and req.schema:
            body['response_format'] = {'type': 'json_schema', 'json_schema': {
                'name': req.schema_name, 'schema': req.schema}}
        elif structured == 'json_object':
            body['response_format'] = {'type': 'json_object'}
        return body

    def complete(self, req: CallRequest) -> CallResult:
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'User-Agent': USER_AGENT}
        if self._key:
            headers['Authorization'] = 'Bearer ' + self._key
        url = self.cfg['base_url'].rstrip('/') + '/chat/completions'
        mode = self.cfg.get('structured', 'none') if req.schema else 'none'
        events, retries, tried_modes = [], 0, []
        started = self._clock()
        while True:
            tried_modes.append(mode)
            self._pace()
            body = json.dumps(self._body(req, mode)).encode('utf-8')
            self._last = self._clock()
            status, rheaders, raw = self._transport(url, headers, body, req.timeout)
            text = raw[:MAX_REPLY_BYTES].decode('utf-8', errors='replace')
            if status == 429:
                wait = None
                if rheaders.get('retry-after'):
                    try:
                        wait = float(rheaders['retry-after'])
                    except ValueError:
                        wait = None
                wait = wait if wait is not None else _wait_from_body(text)
                wait = 5.0 if wait is None else wait
                events.append({'status': 429, 'wait_s': round(wait, 2)})
                if retries >= self.cfg.get('max_429_retries', 2) or wait > self.cfg.get('max_wait_s', 45.0):
                    raise ProviderError('rate_limited', 'provider rate limit; suggested wait %.1fs' % wait,
                                        status=429, retry_after=wait, backoff_events=events)
                retries += 1
                self._sleep(wait + 0.5)
                continue
            if status == 400 and mode != 'none' and re.search(r'response_format|json_schema|schema|structured', text, re.I):
                events.append({'status': 400, 'note': 'structured output refused; resent without it'})
                mode = 'none'
                continue
            if status in (401, 403):
                raise ProviderError('auth', 'HTTP %d' % status, status=status, backoff_events=events)
            if status == 402:
                raise ProviderError('payment_required', 'HTTP 402', status=status, backoff_events=events)
            if status == 404:
                raise ProviderError('model_unavailable', 'HTTP 404 (unknown model or endpoint)', status=status,
                                    backoff_events=events)
            if status >= 500:
                raise ProviderError('server', 'HTTP %d' % status, status=status, backoff_events=events)
            if status != 200:
                raise ProviderError('bad_request', 'HTTP %d: %s' % (status, text[:160].replace('\n', ' ')),
                                    status=status, backoff_events=events)
            try:
                data = json.loads(text)
                choice = (data.get('choices') or [{}])[0]
                message = choice.get('message') or {}
                content = message.get('content')
            except (ValueError, AttributeError, IndexError):
                raise ProviderError('malformed_reply', 'reply is not a chat completion', status=status,
                                    ambiguous=True, backoff_events=events) from None
            usage = data.get('usage') or {}
            tin, tout = usage.get('prompt_tokens'), usage.get('completion_tokens')
            cost, source = None, 'unreported'
            reported = usage.get('cost')
            if isinstance(reported, (int, float)) and not isinstance(reported, bool) and reported >= 0:
                cost, source = int(round(reported * 1_000_000 + 0.4999)), 'provider_receipt'
            elif (self.name, req.model) in PRICES and isinstance(tin, int) and isinstance(tout, int):
                pin, pout = PRICES[(self.name, req.model)]
                cost, source = rate_cost(tin, tout, pin, pout), 'price_table'
            elif (self.name, req.model) not in PRICES:
                cost, source = 0, 'free_tier'
            finish = choice.get('finish_reason')
            return CallResult(
                provider=self.name, model=data.get('model') or req.model,
                text=content if isinstance(content, str) else '', input_tokens=tin, output_tokens=tout,
                cost_microusd=cost, cost_source=source, request_id=data.get('id') or rheaders.get('x-request-id'),
                stop_reason=finish, truncated=(finish == 'length'), latency_s=round(self._clock() - started, 3),
                structured_mode=tried_modes[-1], backoff_events=events, http_status=status)


# --------------------------------------------------------------------------- Provider_a
class ProviderAProvider:
    name = 'provider_a'

    def __init__(self, api_key, *, client=None):
        self._key = api_key
        self._client = client

    @property
    def available(self) -> bool:
        return bool(self._key) or self._client is not None

    @property
    def client(self):
        if self._client is None:
            import provider_a
            # max_retries=0: a silent SDK retry would be an unreserved second billable request.
            self._client = provider_a.Provider_a(api_key=self._key, max_retries=0, timeout=300.0)
        return self._client

    @staticmethod
    def _kwargs(req: CallRequest) -> dict:
        kwargs = {'model': req.model, 'max_tokens': req.max_tokens, 'system': req.system,
                  'messages': [{'role': 'user', 'content': req.user}], 'thinking': {'type': 'adaptive'}}
        output_config = {}
        if req.effort:
            output_config['effort'] = req.effort
        if req.schema:
            output_config['format'] = {'type': 'json_schema', 'schema': req.schema}
        if output_config:
            kwargs['extra_body'] = {'output_config': output_config}
        return kwargs

    def estimate_input_tokens(self, req: CallRequest) -> int:
        """Exact input count from the count_tokens endpoint (free), plus the schema, plus 8% margin."""
        counted = self.client.messages.count_tokens(model=req.model, system=req.system,
                                                    messages=[{'role': 'user', 'content': req.user}])
        schema = (len(json.dumps(req.schema).encode('utf-8')) + 2) // 3 if req.schema else 0
        return int((counted.input_tokens + schema) * 1.08) + 8

    def complete(self, req: CallRequest) -> CallResult:
        import provider_a
        kwargs = self._kwargs(req)
        started = time.monotonic()
        streamed_id = None
        try:
            if req.stream:
                with self.client.messages.stream(**kwargs) as stream:
                    message = stream.get_final_message()
                    try:
                        streamed_id = stream.response.headers.get('request-id')
                    except AttributeError:
                        streamed_id = None
            else:
                message = self.client.messages.create(**kwargs)
        except provider_a.RateLimitError as error:
            retry = None
            try:
                retry = float(error.response.headers.get('retry-after', ''))
            except (ValueError, AttributeError, TypeError):
                pass
            raise ProviderError('rate_limited', 'provider_a 429', status=429, retry_after=retry) from None
        except provider_a.AuthenticationError:
            raise ProviderError('auth', 'provider_a authentication failed', status=401) from None
        except provider_a.APITimeoutError:
            raise ProviderError('timeout', 'no reply before the deadline', ambiguous=True) from None
        except provider_a.APIConnectionError:
            raise ProviderError('transport', 'connection error before a reply') from None
        except provider_a.APIStatusError as error:
            code = 'server' if error.status_code >= 500 else 'bad_request'
            raise ProviderError(code, 'HTTP %d: %s' % (error.status_code, str(getattr(error, 'message', ''))[:200]),
                                status=error.status_code) from None
        text = ''.join(getattr(block, 'text', '') for block in message.content if getattr(block, 'type', '') == 'text')
        usage = message.usage
        tin, tout = usage.input_tokens, usage.output_tokens
        pin, pout = PRICES[(self.name, req.model)]
        details = getattr(message, 'stop_details', None)
        category = getattr(details, 'category', None) if details is not None else None
        request_id = streamed_id or getattr(message, '_request_id', None) or getattr(message, 'id', None)
        return CallResult(
            provider=self.name, model=getattr(message, 'model', req.model), text=text, input_tokens=tin,
            output_tokens=tout, cost_microusd=rate_cost(tin, tout, pin, pout), cost_source='price_table',
            request_id=request_id, stop_reason=message.stop_reason, refusal=(message.stop_reason == 'refusal'),
            stop_category=category, truncated=(message.stop_reason == 'max_tokens'),
            latency_s=round(time.monotonic() - started, 3), streamed=bool(req.stream), effort=req.effort,
            structured_mode='json_schema' if req.schema else 'none')


# --------------------------------------------------------------------------- factory
def probe_local_host(base_url, timeout=1.5) -> bool:
    """True when an Local_host server answers on the loopback host (GET /api/tags). Never raises."""
    root = base_url.rstrip('/')
    if root.endswith('/v1'):
        root = root[:-3]
    try:
        with urllib.request.urlopen(urllib.request.Request(root + '/api/tags', headers={'User-Agent': USER_AGENT}),
                                    timeout=timeout) as response:
            return response.status == 200
    except (OSError, ValueError):
        return False


def build_providers(env: dict, *, transport=None, provider_a_client=None, sleeper=time.sleep) -> dict:
    """One adapter per configured provider that has a credential (Local_host needs none and is probed lazily)."""
    providers = {}
    for name, cfg in PROVIDERS.items():
        if cfg['kind'] == 'provider_a':
            key = env.get(cfg['key'], '')
            if key or provider_a_client is not None:
                providers[name] = ProviderAProvider(key, client=provider_a_client)
        else:
            key = env.get(cfg['key'], '') if cfg['key'] else ''
            if key or cfg['key'] is None:
                base = None
                if name == 'local_host':
                    host = (env.get('OEARS_LOCAL_HOST_HOST') or 'http://127.0.0.1:11434').rstrip('/')
                    base = host if host.endswith('/v1') else host + '/v1'
                    if transport is None and not probe_local_host(base):
                        continue
                providers[name] = ProviderBCompatProvider(name, key, transport=transport, sleeper=sleeper, base_url=base)
    return providers
