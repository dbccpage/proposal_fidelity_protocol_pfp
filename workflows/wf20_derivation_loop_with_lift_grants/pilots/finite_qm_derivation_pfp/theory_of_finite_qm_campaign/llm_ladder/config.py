"""Static configuration of the ladder: providers, prices, tiers, stage effort and acceptance defaults.

AuthorityEffect: None. Everything here is a default the CLI or a --tiers-config JSON file can override.

Prices are micro-USD per million tokens.
  Anthropic: the first-party rates in the Claude API skill's model table (cached 2026-10-06):
    haiku-5-5 0.10/0.50 USD (prompts up to 100K input tokens; this ladder never sends more),
    sonnet-5-5 2/10, opus-5-5 4/20, fable-5-1 10/50 USD per million tokens.
  OpenRouter paid: the live /models listing of 2026-10-21 (gpt-4o-mini 0.15/0.60).
A free tier is priced at 0 but is still rate limited; those limits are enforced in providers.py.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

# name -> adapter settings. `key` names the environment variable; no value lives here.
PROVIDERS = {
    'groq': {'kind': 'openai', 'base_url': 'https://api.groq.com/openai/v1', 'key': 'GROQ_API_KEY',
             'min_interval_s': 3.0, 'max_tokens_field': 'max_completion_tokens', 'structured': 'json_schema',
             'max_wait_s': 45.0, 'max_429_retries': 2},
    'cerebras': {'kind': 'openai', 'base_url': 'https://api.cerebras.ai/v1', 'key': 'CEREBRAS_API_KEY',
                 'min_interval_s': 3.0, 'max_tokens_field': 'max_completion_tokens', 'structured': 'json_schema',
                 'max_wait_s': 45.0, 'max_429_retries': 2},
    'nvidia': {'kind': 'openai', 'base_url': 'https://integrate.api.nvidia.com/v1', 'key': 'NVIDIA_API_KEY',
               'min_interval_s': 2.5, 'max_tokens_field': 'max_tokens', 'structured': 'none',
               'max_wait_s': 45.0, 'max_429_retries': 2},
    'openrouter': {'kind': 'openai', 'base_url': 'https://openrouter.ai/api/v1', 'key': 'OPENROUTER_API_KEY',
                   'min_interval_s': 3.5, 'max_tokens_field': 'max_tokens', 'structured': 'json_schema',
                   'max_wait_s': 45.0, 'max_429_retries': 2, 'body_extra': {'usage': {'include': True}}},
    'ollama': {'kind': 'openai', 'base_url': 'http://127.0.0.1:11434/v1', 'key': None,
               'min_interval_s': 0.0, 'max_tokens_field': 'max_tokens', 'structured': 'none',
               'max_wait_s': 5.0, 'max_429_retries': 0, 'timeout_s': 180.0},
    'anthropic': {'kind': 'anthropic', 'key': 'ANTHROPIC_API_KEY'},
}

# (provider, model) -> (input, output) micro-USD per million tokens. Missing entries are free.
PRICES = {
    ('anthropic', 'claude-haiku-5-5'): (100_000, 500_000),
    ('anthropic', 'claude-sonnet-5-5'): (2_000_000, 10_000_000),
    ('anthropic', 'claude-opus-5-5'): (4_000_000, 20_000_000),
    ('anthropic', 'claude-fable-5-1'): (10_000_000, 50_000_000),
    ('openrouter', 'openai/gpt-4o-mini'): (150_000, 600_000),
}

# Haiku 5.5 doubles-and-more above 100K input tokens (0.50/2.50). The guard refuses such a request.
HAIKU_LONG_CONTEXT_TOKENS = 100_000

# Stage -> effort per Anthropic tier. Mining stays low or medium; only the final hard step goes high.
STAGE_EFFORT = {
    'P0': {'claude-haiku-5-5': 'low', 'claude-sonnet-5-5': 'medium', 'claude-opus-5-5': 'medium', 'claude-fable-5-1': 'medium'},
    'P1': {'claude-haiku-5-5': 'medium', 'claude-sonnet-5-5': 'high', 'claude-opus-5-5': 'high', 'claude-fable-5-1': 'max'},
}

DEFAULT_TIERS = [
    {'id': 0, 'name': 'free', 'family': 'free', 'attempts_before_escalation': 3, 'max_infra_failures': 6,
     'max_tokens': 3500, 'candidates': [
         # Order matters: models are rotated attempt by attempt. Groq first: fast and honours the JSON schema.
         {'provider': 'groq', 'model': 'openai/gpt-oss-120b', 'body_extra': {'reasoning_effort': 'low'}},
         {'provider': 'groq', 'model': 'qwen/qwen3.8-27b'},
         {'provider': 'groq', 'model': 'openai/gpt-oss-20b', 'body_extra': {'reasoning_effort': 'low'}},
         # OpenRouter free reasoning models burn max_tokens on hidden reasoning unless told not to (observed 2026-10-21).
         # Round 2 diagnostic (2026-10-21): poolside/laguna-s-2.1:free was removed (0 of 57 answers accepted, 296 of the 307
         # schema violations, 21 replies cut at max_tokens); nemotron-3.5-lightning is demoted to last (3 of 39 answers invalid
         # or cut, 7 accepted). OpenRouter free models accept `response_format` but do not enforce it.
         {'provider': 'openrouter', 'model': 'minimax/minimax-m3.1-flash:free', 'body_extra': {'reasoning': {'effort': 'low'}}},
         {'provider': 'openrouter', 'model': 'nvidia/nemotron-3.5-lightning:free', 'body_extra': {'reasoning': {'enabled': False}}},
         # Adapters exist and are wired, but these two did not work with the keys on file on 2026-10-21:
         {'provider': 'cerebras', 'model': 'gpt-oss-120b', 'body_extra': {'reasoning_effort': 'low'}, 'enabled': False,
          'disabled_reason': 'HTTP 402 payment_required_error for both listed models'},
         {'provider': 'nvidia', 'model': 'nvidia/nemotron-3-super-120b-a12b', 'enabled': False,
          'disabled_reason': 'HTTP 403 for every NIM model tried'},
     ]},
    {'id': 1, 'name': 'cheap', 'family': 'paid_other', 'attempts_before_escalation': 2, 'max_infra_failures': 3,
     'max_tokens': 3500, 'candidates': [{'provider': 'openrouter', 'model': 'openai/gpt-4o-mini'}]},
    {'id': 2, 'name': 'haiku', 'family': 'anthropic', 'attempts_before_escalation': 2, 'max_infra_failures': 3,
     'max_tokens': 4000, 'candidates': [{'provider': 'anthropic', 'model': 'claude-haiku-5-5'}]},
    {'id': 3, 'name': 'sonnet', 'family': 'anthropic', 'attempts_before_escalation': 1, 'max_infra_failures': 2,
     'max_tokens': 5000, 'candidates': [{'provider': 'anthropic', 'model': 'claude-sonnet-5-5'}]},
    {'id': 4, 'name': 'opus', 'family': 'anthropic', 'attempts_before_escalation': 1, 'max_infra_failures': 2,
     'max_tokens': 6000, 'candidates': [{'provider': 'anthropic', 'model': 'claude-opus-5-5'}]},
    {'id': 5, 'name': 'fable', 'family': 'anthropic', 'attempts_before_escalation': 1, 'max_infra_failures': 1,
     'max_tokens': 8000, 'candidates': [{'provider': 'anthropic', 'model': 'claude-fable-5-1'}]},
]

# Statuses of an attempt the model answered (an infra error or a budget refusal is not one of them).
ANSWERED_STATUSES = ('accepted', 'accepted_partial', 'rejected')

DEFAULT_POLICY = {
    'min_verified': 2,            # credited generators + relations + compositions + lemma statements for acceptance
    # numeric_counts: a numeric claim supplies its own expression and value, so its exact recomputation proves arithmetic,
    # not relevance. False (default): numeric claims are still recomputed and a false one is still a refused claim, but a
    # correct one earns no credit toward min_verified or partial_min_verified. True restores the old crediting.
    'numeric_counts': False,
    'max_failure_rate': 0.5,      # failed host-checked claims / (verified + failed) at most this to accept
    # accepted_partial: verified >= partial_min_verified, NO refused claim, but fewer than min_verified verified. A terminal
    # outcome of its own (never counted as `accepted`, never an abstention, no escalation). False restores the old behaviour.
    'accept_partial': True, 'partial_min_verified': 1,
    # skip_ungroundable: no provider call for a node with an empty @SRC, no operation/relation candidates and no code anchor
    # in the checkout. Recorded as `skipped_ungroundable` with the reason. False sends every node.
    'skip_ungroundable': True,
    # partial_escalates: an accepted_partial attempt is kept as the run's fallback and the ladder keeps climbing; a later full
    # accept supersedes it, otherwise the run ends accepted_partial with the best partial (most credited items). False
    # restores the old behaviour (the first partial ends the run), which stopped cheap tiers before stronger ones were tried.
    'partial_escalates': True,
    'abstain_stop': 0,            # >0: stop (blocked, no escalation) once this many distinct models answered validly with no claim to check and too few verified
    'feedback': True,             # inject negative and positive operad entries into the packet
    'max_neg_lines': 12, 'max_pos_lines': 8, 'max_source_candidates': 25, 'excerpt_chars': 1400,
    'stream_above_max_tokens': 16000,
    'p0_default_effort_override': None,
}


def load_tiers(path=None, env=None):
    """Default tiers (or a JSON file), then the two environment hints of the reference system's .env:
    ANOMALON_LLM_PROVIDER puts that provider first inside the free tier (a preference, never a requirement), and
    OPENROUTER_MODEL names the paid OpenRouter model of tier 1 (it must have a price in PRICES, else the guard
    refuses the call)."""
    tiers = copy.deepcopy(DEFAULT_TIERS)
    if path:
        tiers = json.loads(Path(path).read_bytes().decode('utf-8'))
    env = env or {}
    prefer = {'or': 'openrouter', 'claude': 'anthropic'}.get((env.get('ANOMALON_LLM_PROVIDER') or '').strip().lower(),
                                                              (env.get('ANOMALON_LLM_PROVIDER') or '').strip().lower())
    model = (env.get('OPENROUTER_MODEL') or '').strip()
    for tier in tiers:
        if tier['family'] == 'free' and prefer:
            tier['candidates'].sort(key=lambda cand: cand['provider'] != prefer)
        if tier['id'] == 1 and model and not model.endswith(':free'):
            tier['candidates'] = [{'provider': 'openrouter', 'model': model}]
    return tiers


def price_for(provider: str, model: str):
    return PRICES.get((provider, model))
