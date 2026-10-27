# Durable receipt delivery

AuthorityEffect: None.

The public `dispatch-events` command delivers the existing catalog outbox to
the existing SQLite receipt ledger. It uses a stable named SQLite inbox for
idempotent effects, fresh lease tokens for cooperating workers, bounded
exponential retry delays, and a separately retained HMAC-authenticated tip.
Catalog compilation and receipt delivery remain separate explicit operations.

## Run the selected lifecycle

Supply a persistent database, an operator-owned binary key containing at least
32 random bytes, a stable ledger identity and a separately protected tip path.
Keep the key out of the repository. Protect the key and tip directory through
independent OS custody; the application does not manufacture operator trust.

```powershell
python -m operads.frontend.cli --workspace . --db-path C:/oe-data/catalog.sqlite3 --json compile-catalog
python -m operads.frontend.cli --workspace . --db-path C:/oe-data/catalog.sqlite3 --json dispatch-events --tip-path C:/oe-custody/catalog-tip.json --tip-key-file C:/oe-secrets/catalog-tip.key --ledger-id development-catalog
```

Use the paths provisioned for the deployment. Repeating the second command
does not duplicate a receipt. Independent processes may run it against the
same database and retained tip. Each process obtains a fresh worker identity;
an explicit `--worker-id` is also available. A live claim is excluded from
other workers and legacy polling. An expired worker cannot acknowledge a
replacement worker's claim. External subscribers still need idempotent effects.

Embedding hosts use `OeopContainer.configure_receipt_delivery(...)`, then
`container.dispatcher.dispatch_pending(...)`, and finally `container.close()`.
The default in-memory catalog API does not imply persistent delivery.

## Recovery and refusal

Before changing SQLite, the subscriber retains the exact next event and
anticipated tip in a signed pending intent. If the process dies between the
database commit and tip replacement, the next invocation verifies the intent
and either applies that exact event or verifies its already committed result.
It then completes the recorded tip transition. A retry after acknowledgement
loss is a no-op for the same event and refuses changed bytes under that ID.

Missing pins for a populated database, forged pins, foreign identities,
truncated chains, altered pending intents and linked/reparse custody paths
refuse. The command never repairs these by trusting the database's current tip.
Restore independently retained exact bytes or perform an operator-reviewed
recovery; do not delete a pin to force initialization.

SQLite uses WAL with `synchronous=FULL`; retained files are flushed before
atomic replacement, with a directory fsync where the platform supports it.
The focused controls include two real competing processes and a process that
exits after the receipt commit and before tip replacement. They establish
the named process-crash behavior. Physical power-loss durability depends on
the storage stack and remains unmeasured. HMAC cannot detect an attacker who
steals the key or rolls back both independently retained stores.

## Targeted verification

```powershell
python -m pytest -o addopts= operads/tests/integration/test_outbox_worker_leases.py operads/tests/integration/test_anchored_ledger_delivery.py -q
```

Use a writable explicit `--basetemp` when Windows sandbox temporary directories
are unavailable. These checks do not establish arbitrary external exactly-once
delivery, IDE activation or antibody admission.
