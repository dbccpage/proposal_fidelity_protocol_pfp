# OEWAS001: unique source keys in fenced declarations

AuthorityEffect: None. Full epic: RESEARCH_HOLD.

Repeated `inputs` keys previously selected an empty list and compiled a nullary operation. The first real filesystem/parser/SQLite control failed before repair, then passed on identical test bytes after the minimal loader change.

The local SafeLoader rejects repeated explicit constructed keys in operand, operation and composition fences. It preserves defined merge overrides and sequence precedence, alias reuse, the YAML value tag, integer metadata and ordinary foreign fences. It does not change the global SafeLoader or introduce a string-only-key rule.

Independent review added alias-key and quoted merge-key controls: 32 primary plus 12 adjacent tests passed. Replacing the three production loads with safe_load caused 17 failures; bypassing the colour-key predicate caused five failures. Exact production source was restored; the final primary file passed all 32 controls. The [sealed independent receipt](independent/review.json) binds commands, versions, source/test bytes and raw outputs; first RED/GREEN attribution is retained separately.

The real compiler refuses with DOCUMENT_PARSE_ERROR400 before catalogs/events/outbox/idempotency are written. Corrected source recovers under the same refused key/version, preserves ordered ports and remains UNADMITTED; a successful retry replays the stored snapshot.

Root final Ruff and required publication gates passed. This branch is based directly on ae33a85 and complements PR698's malformed-input shape guards, which it does not include. Complete native admission, all YAML readers and the broader compiler epic remain open. No provider calls, native build, theorem or authority grant.
