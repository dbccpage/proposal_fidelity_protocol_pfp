# Contract and packaging boundary review

Seven files were read in full with hashes checked against the original inventory. Nine public synthetic observations distinguish schema acceptance, runtime admission and receipt replay.

The generated schemas permit negative weights, duplicate vertices, unknown endpoints and malformed rational strings. The actual Pydantic admission path rejects all four, so a schema pass must not be reported as semantic admission. A valid positive case and an unknown-field rejection provide controls. Likewise, a resealed invented final state passes the receipt schema/model but fails replay.

The runtime does expose one narrower defect: `CutIn.section` remains a mutable dictionary inside a frozen model. `get_pack` caches and returns that object; changing the nested dictionary affects a subsequent lookup without admission. The probe restores the dictionary before exiting. No remote mutation path was demonstrated.

Changing and resealing `core_version` does not cause replay rejection when the current outputs agree. That matches a current-core replay check; it does not authenticate the historical implementation named in the receipt.

The default pytest configuration selects only PFP Lab and governance-tool tests. The explicit package list likewise does not install EIS, PCIV or OPERADS. A green default invocation or successful Lab installation therefore says little about the rest of this checkout. No wheel build, package installation, full suite, provider call or protected benchmark access occurred.

Per-file assessments and hashes are in `additional_contracts_and_packaging.json`; executable public cases and observed results are in the corresponding `_probe.py` and `_probe.json`.
