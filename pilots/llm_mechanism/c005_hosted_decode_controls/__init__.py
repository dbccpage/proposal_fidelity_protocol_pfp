"""
c005_hosted_decode_controls — Hosted Decoding Controls Bake-off (Challenge C005).

Evaluates logit_bias, json_schema, gbnf, and unconstrained decoding on hosted
and frontier models (<=70B and >70B) under strict budget control ($0.10 ceiling).

AuthorityEffect: None.
"""

from __future__ import annotations

CHALLENGE_ID = "C005"
CHALLENGE_TIER = "T1"
DOMAIN = "a_mechanism"
BUDGET_CEILING_USD = 0.10
USER_TARGET_SPEND_USD = 0.05
HARD_KILL_CEILING_USD = 0.25
