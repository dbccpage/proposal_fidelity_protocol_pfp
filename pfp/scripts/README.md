# PFP Scripts (`scripts`)

**AuthorityEffect:** `None`

## 1. Role

Holds the executable composition root for the documentation-integrity bounded context.

## 2. Directory Inventory

| Item | Type | Purpose |
|---|---|---|
| [`docs_integrity.py`](docs_integrity.py) | Python entrypoint | Dispatches to the typed application service and outward host adapters. |

## 3. Run

```text
py -3.12 omega_engine_pfp/scripts/docs_integrity.py validate
```

The package form is equivalent: `py -3.12 -m omega_engine_pfp.scripts.docs_integrity validate`.

## 4. Scope

The CLI supports read-only validation and explicit inventory refresh commands. Inventory is the only mutating command; lock refreshes remain explicit opt-ins.
