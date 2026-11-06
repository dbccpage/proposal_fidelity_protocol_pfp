# Historical antimorphic-reversal illustration

**Current reading boundary:** 2026-09-27, source base
`52cb5457f6c485ba548cfd292f6012a941ed22cf`.

The canonical use case
`pfp/use_cases/mssn_sn_demos/demo_antimorphic_reversal/run.py`
always refuses with `NO_NATIVE_PORT` because the native delegate is unbound.
Its receipt records that refusal. A set of action names alone does not provide
the implementation.

The legacy scenario adapter at
`pfp/infrastructure/adapters/mssn_scenarios/antimorphic_reversal.py`
contains a finite illustration. It is not evidence of a complete family of
reversible transitions, lossless grammar down-maps, permanent quarantine, or
an integrated native verifier. Historical artifacts in this directory remain
historical artifacts.

Current boundary tests are
`pfp/tests/mssn_sn_demos/test_demo_antimorphic_reversal.py`.
They check the missing actions, typed refusal, and refusal receipt validation.
The earlier `research/mssn_sn_tower/demos/...` commands are obsolete.

See the [main paper](../../paper.md) and [claim ledger](../../paper_claim_ledger.md)
for the claims supported by the pinned source.
