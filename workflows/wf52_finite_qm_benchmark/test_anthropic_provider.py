"""Offline checks for anthropic_provider: fake transports only, no key, no network."""
import email.message
import io
import json
import socket
from urllib.request import HTTPSHandler, ProxyHandler, build_opener
from urllib.response import addinfourl

import pytest

import anthropic_provider as ap
from budget_ledger import BudgetError, RunLedger
from reference_runner import canonical, sha

FAKE_KEY = 'test-key-not-a-real-credential'


def request(text='hello', max_output=100, system='abc', **extra):
    messages = ([{'role': 'system', 'content': system}] if system else []) + [{'role': 'user', 'content': text}]
    return {'messages': messages, 'max_output_tokens': max_output, 'tools': [], 'retries': 0, **extra}


def body(model='claude-opus-5-5', input_tokens=10, output_tokens=20, **usage):
    return {'id': 'msg_1', 'type': 'message', 'role': 'assistant', 'model': model, 'stop_reason': 'end_turn',
            'content': [{'type': 'thinking', 'thinking': ''}, {'type': 'text', 'text': 'answer'}],
            'usage': {'input_tokens': input_tokens, 'output_tokens': output_tokens, **usage}}


class FakeTransport:
    def __init__(self, data=None, error=None):
        self.data, self.error, self.calls = data, error, []

    def request(self, method, path, wire):
        self.calls.append((method, path, wire))
        if self.error:
            raise self.error
        raw = json.dumps(self.data).encode()
        return raw, ap.parse_json(raw)


class FakeHTTPS(HTTPSHandler):
    """Replaces the real HTTPS handler; answers in-process."""
    def __init__(self, code=200, payload=b'{}', exc=None, location=None):
        super().__init__()
        self.code, self.payload, self.exc, self.location, self.seen = code, payload, exc, location, []

    def https_open(self, req):
        self.seen.append(req)
        if self.exc:
            raise self.exc
        headers = email.message.Message()
        if self.location:
            headers['Location'] = self.location
        response = addinfourl(io.BytesIO(self.payload), headers, req.full_url, self.code)
        response.msg = 'fake'
        return response


def http_transport(handler):
    transport = ap.HTTPTransport(FAKE_KEY, timeout_seconds=5)
    transport._opener = build_opener(ProxyHandler({}), ap.NoRedirect(), handler)
    return transport


def test_exact_integer_quote_and_wire():
    provider = ap.AnthropicProvider('claude-opus-5-5', FakeTransport())
    quote = provider.upper_quote(request())
    # input bound = 8 bytes + 2*16 + 512 = 552; 552*4 + 100*20 = 4208 microUSD.
    assert type(quote) is int and quote == 4208
    evidence = provider.request_evidence()
    assert evidence['input_token_bound'] == 552 and evidence['output_token_bound'] == 100
    assert evidence['wire_request'] == {'model': 'claude-opus-5-5', 'max_tokens': 100, 'stream': False,
                                        'system': 'abc', 'messages': [{'role': 'user', 'content': 'hello'}]}


def test_fractional_tariff_rounds_up_and_long_tier_applies():
    assert ap.AnthropicProvider('claude-haiku-5-5', FakeTransport()).upper_quote(request()) == 106  # 55.2 + 50
    long_text = 'x' * 100_000  # bound 100_547 > 100K selects 0.50 / 2.50
    assert ap.AnthropicProvider('claude-haiku-5-5', FakeTransport()).upper_quote(request(long_text)) == 50_524  # 50_273.5 + 250


@pytest.mark.parametrize('model', ['claude-opus-9', 'claude-haiku-4-5', 'gpt-4', 'claude-opus-5-5-latest'])
def test_unknown_model_and_alias_refused(model):
    with pytest.raises(ap.ProviderError):
        ap.AnthropicProvider(model, FakeTransport())


@pytest.mark.parametrize('bad', [
    request() | {'tools': [{'name': 'x'}]},
    request() | {'retries': 1},
    request() | {'messages': [{'role': 'user', 'content': [{'type': 'image'}]}]},
    request() | {'messages': [{'role': 'user', 'content': 'a'}, {'role': 'system', 'content': 'late'}]},
    request() | {'messages': [{'role': 'user', 'content': 'a'}, {'role': 'assistant', 'content': 'prefill'}]},
    request() | {'extra': 1},
])
def test_tools_retries_non_text_and_bad_shapes_refused(bad):
    with pytest.raises(ap.ProviderError):
        ap.AnthropicProvider('claude-opus-5-5', FakeTransport()).upper_quote(bad)


def test_quote_over_run_cap_refused():
    with pytest.raises(ap.ProviderError, match='cap'):
        ap.AnthropicProvider('claude-opus-5-5', FakeTransport()).upper_quote(request(max_output=5000))


def test_budget_tokens_rules():
    with pytest.raises(ap.ProviderError):
        ap.AnthropicProvider('claude-opus-5-5', FakeTransport(), budget_tokens=2048)
    with pytest.raises(ap.ProviderError, match='below'):
        ap.AnthropicProvider('claude-haiku-4-5-20251001', FakeTransport(), budget_tokens=2048).upper_quote(request(max_output=2048))
    provider = ap.AnthropicProvider('claude-haiku-4-5-20251001', FakeTransport(), budget_tokens=1024)
    assert provider.upper_quote(request(max_output=2048)) == 552 * 1 + 2048 * 5
    assert provider.request_evidence()['wire_request']['thinking'] == {'type': 'enabled', 'budget_tokens': 1024}


def test_preflight_instance_cannot_complete_or_requote():
    transport = FakeTransport(body())
    provider = ap.AnthropicProvider('claude-opus-5-5', transport)
    quote, evidence = provider.preflight(request())
    assert quote == evidence['quote_microusd'] == 4208
    with pytest.raises(ap.ProviderError):
        provider.complete(request())
    with pytest.raises(ap.ProviderError):
        provider.upper_quote(request())
    assert transport.calls == []


def test_success_settles_exact_charge_and_instance_is_spent(tmp_path):
    transport = FakeTransport(body(input_tokens=500, output_tokens=90))
    provider = ap.AnthropicProvider('claude-opus-5-5', transport)
    ledger = RunLedger(tmp_path / 'ledger.sqlite')
    ledger.start('run', 'a' * 64)
    req = request()
    quote = provider.upper_quote(req)
    ledger.reserve('run', 'call', sha(canonical(req)), quote)
    reply = provider.complete(req)
    assert reply.accounting_error is None and reply.text == 'answer'
    assert reply.actual_microusd == 500 * 4 + 90 * 20 == 3800
    assert reply.finish_reason == 'end_turn' and reply.provider_request_id == 'msg_1'
    ledger.settle('call', reply.actual_microusd, reply.provider_evidence['response_sha256'])
    summary = ledger.summary('run')
    assert summary['spent_microusd'] == 3800 and summary['held_microusd'] == 0 and not summary['blocked']
    for again in (lambda: provider.complete(req), lambda: provider.upper_quote(req)):
        with pytest.raises(ap.ProviderError):
            again()
    assert len(transport.calls) == 1
    ledger.close()


def test_changed_request_after_quote_refused_without_dispatch():
    transport = FakeTransport(body())
    provider = ap.AnthropicProvider('claude-opus-5-5', transport)
    provider.upper_quote(request())
    with pytest.raises(ap.ProviderError, match='changed'):
        provider.complete(request('different'))
    assert transport.calls == []


def test_expired_quote_refused(monkeypatch):
    transport = FakeTransport(body())
    clock = iter([1000.0, 1031.0])
    monkeypatch.setattr(ap.time, 'monotonic', lambda: next(clock))
    provider = ap.AnthropicProvider('claude-opus-5-5', transport)
    provider.upper_quote(request())
    with pytest.raises(ap.ProviderError, match='expired'):
        provider.complete(request())
    assert transport.calls == []


@pytest.mark.parametrize('handler', [FakeHTTPS(code=502, payload=b'{"secret":"server body"}'),
                                     FakeHTTPS(exc=socket.timeout('timed out'))])
def test_http_502_and_timeout_hold_full_quote_and_block(tmp_path, handler):
    provider = ap.AnthropicProvider('claude-opus-5-5', http_transport(handler))
    ledger = RunLedger(tmp_path / 'ledger.sqlite')
    ledger.start('run', 'b' * 64)
    req = request()
    quote = provider.upper_quote(req)
    ledger.reserve('run', 'call', sha(canonical(req)), quote)
    with pytest.raises(ap.ProviderError, match='charge unknown') as info:
        provider.complete(req)
    assert FAKE_KEY not in str(info.value) and 'server body' not in str(info.value)
    assert len(handler.seen) == 1
    ledger.mark_uncertain('call')
    summary = ledger.summary('run')
    assert summary['held_microusd'] == quote and summary['blocked']
    with pytest.raises(BudgetError):
        ledger.reserve('run', 'retry', sha(canonical(req)), quote)
    ledger.close()


def test_missing_usage_is_unknown_liability():
    data = body()
    del data['usage']
    provider = ap.AnthropicProvider('claude-opus-5-5', FakeTransport(data))
    provider.upper_quote(request())
    reply = provider.complete(request())
    assert reply.actual_microusd is None and 'unknown' in reply.accounting_error


@pytest.mark.parametrize('usage', [{'cache_read_input_tokens': 5}, {'cache_creation_input_tokens': 1},
                                   {'input_tokens': True}, {'output_tokens': -1}, {'input_tokens': '10'}])
def test_cache_tokens_or_invalid_usage_hold(usage):
    provider = ap.AnthropicProvider('claude-opus-5-5', FakeTransport(body(**usage)))
    provider.upper_quote(request())
    reply = provider.complete(request())
    assert reply.actual_microusd is None and reply.accounting_error


def test_overrun_recorded_and_blocks(tmp_path):
    provider = ap.AnthropicProvider('claude-opus-5-5', FakeTransport(body(input_tokens=552, output_tokens=500)))
    ledger = RunLedger(tmp_path / 'ledger.sqlite')
    ledger.start('run', 'c' * 64)
    req = request()
    ledger.reserve('run', 'call', sha(canonical(req)), provider.upper_quote(req))
    reply = provider.complete(req)
    assert reply.actual_microusd == 552 * 4 + 500 * 20
    assert 'exceeded a reserved token bound' in reply.accounting_error and 'exceeded the quote' in reply.accounting_error
    with pytest.raises(BudgetError, match='exceeded quote'):
        ledger.settle('call', reply.actual_microusd, reply.provider_evidence['response_sha256'])
    summary = ledger.summary('run')
    assert summary['spent_microusd'] == reply.actual_microusd and summary['blocked']
    ledger.close()


def test_response_identity_and_tool_blocks_are_violations():
    data = body(model='claude-sonnet-5-5')
    data['content'].append({'type': 'tool_use', 'id': 't', 'name': 'x', 'input': {}})
    provider = ap.AnthropicProvider('claude-opus-5-5', FakeTransport(data))
    provider.upper_quote(request())
    reply = provider.complete(request())
    assert reply.actual_microusd == 10 * 4 + 20 * 20  # known charge is kept
    assert 'model differs' in reply.accounting_error and 'tool_use' in reply.accounting_error
    assert reply.text == 'answer'


def test_key_not_read_during_prepare_and_absent_from_outputs(monkeypatch):
    class GuardedEnv(dict):
        def __getitem__(self, key):
            if key == 'ANTHROPIC_API_KEY':
                raise AssertionError('key read')
            return super().__getitem__(key)
        get = lambda self, key, default=None: self[key] if key in self else default

    env = GuardedEnv(ANTHROPIC_API_KEY=FAKE_KEY)
    monkeypatch.setattr(ap.os, 'environ', env)
    called = []
    monkeypatch.setattr(ap, 'transport_from_environment', lambda *a: called.append(a))
    handler = FakeHTTPS(payload=json.dumps(body()).encode())
    provider = ap.AnthropicProvider('claude-opus-5-5', http_transport(handler))
    provider.preflight(request())
    live = ap.AnthropicProvider('claude-opus-5-5', provider.transport)
    live.upper_quote(request())
    evidence = live.request_evidence()
    reply = live.complete(request())
    assert called == [] and reply.accounting_error is None
    sent = handler.seen[0]
    assert sent.full_url == ap.URL and sent.get_method() == 'POST'
    assert sent.get_header('X-api-key') == FAKE_KEY and sent.get_header('Anthropic-version') == '2023-06-01'
    for text in (repr(live.transport), json.dumps(evidence), repr(reply)):
        assert FAKE_KEY not in text


def test_transport_from_environment_and_allowlist(monkeypatch):
    monkeypatch.setattr(ap.os, 'environ', {})
    with pytest.raises(ap.ProviderError) as info:
        ap.transport_from_environment()
    monkeypatch.setattr(ap.os, 'environ', {'ANTHROPIC_API_KEY': FAKE_KEY})
    transport = ap.transport_from_environment()
    assert FAKE_KEY not in repr(transport) and FAKE_KEY not in str(info.value)
    with pytest.raises(ap.ProviderError, match='allowlist'):
        transport.request('GET', '/v1/models', None)


def test_redirect_refused():
    handler = FakeHTTPS(code=302, location='https://elsewhere.example/v1/messages')
    with pytest.raises(ap.ProviderError, match='Redirect refused'):
        http_transport(handler).request('POST', '/v1/messages', {'model': 'x'})
    assert len(handler.seen) == 1


def test_duplicate_json_key_refused():
    with pytest.raises(ap.ProviderError):
        ap.parse_json(b'{"usage": 1, "usage": 2}')
