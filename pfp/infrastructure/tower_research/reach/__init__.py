"""The reach programme's receiving side: receipts, transport, and the ledger.

AuthorityEffect: None. Nothing in this package grants, activates, or promotes
anything. It recomputes verdicts from pinned bytes and records them.

Modules:

- ``canonical``: canonical bytes, strict parsing, digests, rationals.
- ``codes``: the closed registry of refusal codes and caps.
- ``schema``: closed field sets, checked at every depth.
- ``stage_registry``: the stage table pin and per-row digests.
- ``targets``: loading a pinned target checker and running it.
- ``transport``: ``mssn.transport-certificate.v2`` with its loss ledger.
- ``receipt``: the ``reach-receipt/1`` checker (K1-K16); grades are computed.
- ``ledger``: the reach ledger and its computed numbers (T, C, D, A).
- ``cli``: regenerate or check the committed files.
"""
