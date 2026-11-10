# Guard follow-up review

The three original exploits are stopped at the reviewed source hashes. Synthetic probes used harmless input and a fake transport; no actual benchmark seed, key, network or provider was accessed. The original review is preserved.

- **GR-F01:** Mutating returned evidence cannot change the dispatched request. Internal wire changes and original-request changes are refused before POST; retrying the consumed preparation also fails.
- **GR-F02:** A persisted unfinished admission blocks the next run after reopening. Clean completed runs still proceed in the frozen order.
- **GR-F03:** The original 110000-microusd overrun is retained. Known charges also survive malformed token/message fields, invalid Unicode and response-artifact failure. A failed final receipt write leaves the charge in the run ledger and the campaign reservation blocks continuation.

One additional boundary limitation was reproduced: a finite reported charge of `9223372036855000000` microusd exceeds SQLite INTEGER capacity. The receipt records that exact liability, but ledger spend remains zero and only smaller holds remain. Both run and campaign are blocked, so no follow-on admission succeeded. This amount is outside the quoted-provider premises; it is an extreme-input accounting-retention defect, not an ordinary-price budget bypass.

The JSON contains exact current source hashes, per-probe results and evidence limits. Original-source pins match the resolution record. No source fixes were made.
