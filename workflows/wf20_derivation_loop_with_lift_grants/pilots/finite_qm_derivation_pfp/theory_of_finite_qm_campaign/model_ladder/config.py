"""Static configuration of the ladder: providers, prices, tiers, stage effort and acceptance defaults.

AuthorityEffect: None. Everything here is a default the CLI or a --tiers-config JSON file can override.

Prices are micro-USD per million tokens.
  Provider_a: the first-party rates in the Model_a API skill's model table (cached 2026-10-06):
    tier3-5-5 0.10/0.50 USD (prompts up to 100K input tokens; this ladder never sends more),
    tier2-5-5 2/10, tier1-5-5 4/20, solo-5-1 10/50 USD per million tokens.
  Router_r paid: the live /models listing of 2026-10-21 (model-b3 0.15/0.60).
A free tier is priced at 0 but is still rate limited; those limits are enforced in providers.py.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

# name -> adapter settings. `key` names the environment variable; no value lives here.
PROVIDERS = {
    'host_g': {'kind': 'provider_b', 'base_url': 'https://api.host_g.com/provider_b/v1', 'key': 'HOST_G_API_KEY',
             'min_interval_s': 3.0, 'max_tokens_field': 'max_completion_tokens', 'structured': 'json_schema',
             'max_wait_s': 45.0, 'max_429_retries': 2},
    'host_c': {'kind': 'provider_b', 'base_url': 'https://api.host_c.ai/v1', 'key': 'HOST_C_API_KEY',
                 'min_interval_s': 3.0, 'max_tokens_field': 'max_completion_tokens', 'structured': 'json_schema',
                 'max_wait_s': 45.0, 'max_429_retries': 2},
    'host_n': {'kind': 'provider_b', 'base_url': 'https://integrate.api.host_n.com/v1', 'key': 'HOST_N_API_KEY',
               'min_interval_s': 2.5, 'max_tokens_field': 'max_tokens', 'structured': 'none',
               'max_wait_s': 45.0, 'max_429_retries': 2},
    'router_r': {'kind': 'provider_b', 'base_url': 'https://router_r.ai/api/v1', 'key': 'ROUTER_R_API_KEY',
                   'min_interval_s': 3.5, 'max_tokens_field': 'max_tokens', 'structured': 'json_schema',
                   'max_wait_s': 45.0, 'max_429_retries': 2, 'body_extra': {'usage': {'include': True}}},
    'local_host': {'kind': 'provider_b', 'base_url': 'http://127.0.0.1:11434/v1', 'key': None,
               'min_interval_s': 0.0, 'max_tokens_field': 'max_tokens', 'structured': 'none',
               'max_wait_s': 5.0, 'max_429_retries': 0, 'timeout_s': 180.0},
    'provider_a': {'kind': 'provider_a', 'key': 'PROVIDER_A_API_KEY'},
}

# (provider, model) -> (input, output) micro-USD per million tokens. Missing entries are free.
PRICES = {
    ('provider_a', 'model-a3'): (100_000, 500_000),
    ('provider_a', 'model-a2'): (2_000_000, 10_000_000),
    ('provider_a', 'model-a1'): (4_000_000, 20_000_000),
    ('provider_a', 'model-a4'): (10_000_000, 50_000_000),
    ('router_r', 'provider_b/model-b3'): (150_000, 600_000),
}

# Tier3 5.5 doubles-and-more above 100K input tokens (0.50/2.50). The guard refuses such a request.
TIER3_LONG_CONTEXT_TOKENS = 100_000

# Stage -> effort per Provider_a tier. Mining stays low or medium; only the final hard step goes high.
STAGE_EFFORT = {
    'P0': {'model-a3': 'low', 'model-a2': 'medium', 'model-a1': 'medium', 'model-a4': 'medium'},
    'P1': {'model-a3': 'medium', 'model-a2': 'high', 'model-a1': 'high', 'model-a4': 'max'},
}

DEFAULT_TIERS = [
    {'id': 0, 'name': 'free', 'family': 'free', 'attempts_before_escalation': 3, 'max_infra_failures': 6,
     'max_tokens': 3500, 'candidates': [
         # Order matters: models are rotated attempt by attempt. Host_g first: fast and honours the JSON schema.
         {'provider': 'host_g', 'model': 'provider_b/model-b1', 'body_extra': {'reasoning_effort': 'low'}},
         {'provider': 'host_g', 'model': 'model_c/model-c1'},
         {'provider': 'host_g', 'model': 'provider_b/model-b2', 'body_extra': {'reasoning_effort': 'low'}},
         # Router_r free reasoning models burn max_tokens on hidden reasoning unless told not to (observed 2026-10-21).
         # Round 2 diagnostic (2026-10-21): poolside/laguna-s-2.1:free was removed (0 of 57 answers accepted, 296 of the 307
         # schema violations, 21 replies cut at max_tokens); nemotron-3.5-lightning is demoted to last (3 of 39 answers invalid
         # or cut, 7 accepted). Router_r free models accept `response_format` but do not enforce it.
         {'provider': 'router_r', 'model': 'minimax/minimax-m3.1-flash:free', 'body_extra': {'reasoning': {'effort': 'low'}}},
         {'provider': 'router_r', 'model': 'host_n/nemotron-3.5-lightning:free', 'body_extra': {'reasoning': {'enabled': False}}},
         # Adapters exist and are wired, but these two did not work with the keys on file on 2026-10-21:
         {'provider': 'host_c', 'model': 'model-b1', 'body_extra': {'reasoning_effort': 'low'}, 'enabled': False,
          'disabled_reason': 'HTTP 402 payment_required_error for both listed models'},
         {'provider': 'host_n', 'model': 'host_n/nemotron-3-super-120b-a12b', 'enabled': False,
          'disabled_reason': 'HTTP 403 for every NIM model tried'},
     ]},
    {'id': 1, 'name': 'cheap', 'family': 'paid_other', 'attempts_before_escalation': 2, 'max_infra_failures': 3,
     'max_tokens': 3500, 'candidates': [{'provider': 'router_r', 'model': 'provider_b/model-b3'}]},
    {'id': 2, 'name': 'tier3', 'family': 'provider_a', 'attempts_before_escalation': 2, 'max_infra_failures': 3,
     'max_tokens': 4000, 'candidates': [{'provider': 'provider_a', 'model': 'model-a3'}]},
    {'id': 3, 'name': 'tier2', 'family': 'provider_a', 'attempts_before_escalation': 1, 'max_infra_failures': 2,
     'max_tokens': 5000, 'candidates': [{'provider': 'provider_a', 'model': 'model-a2'}]},
    {'id': 4, 'name': 'tier1', 'family': 'provider_a', 'attempts_before_escalation': 1, 'max_infra_failures': 2,
     'max_tokens': 6000, 'candidates': [{'provider': 'provider_a', 'model': 'model-a1'}]},
    {'id': 5, 'name': 'solo', 'family': 'provider_a', 'attempts_before_escalation': 1, 'max_infra_failures': 1,
     'max_tokens': 8000, 'candidates': [{'provider': 'provider_a', 'model': 'model-a4'}]},
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
    MODEL_PROVIDER puts that provider first inside the free tier (a preference, never a requirement), and
    ROUTER_R_MODEL names the paid Router_r model of tier 1 (it must have a price in PRICES, else the guard
    refuses the call)."""
    tiers = copy.deepcopy(DEFAULT_TIERS)
    if path:
        tiers = json.loads(Path(path).read_bytes().decode('utf-8'))
    env = env or {}
    prefer = {'or': 'router_r', 'model_a': 'provider_a'}.get((env.get('MODEL_PROVIDER') or '').strip().lower(),
                                                              (env.get('MODEL_PROVIDER') or '').strip().lower())
    model = (env.get('ROUTER_R_MODEL') or '').strip()
    for tier in tiers:
        if tier['family'] == 'free' and prefer:
            tier['candidates'].sort(key=lambda cand: cand['provider'] != prefer)
        if tier['id'] == 1 and model and not model.endswith(':free'):
            tier['candidates'] = [{'provider': 'router_r', 'model': model}]
    return tiers


def price_for(provider: str, model: str):
    return PRICES.get((provider, model))
