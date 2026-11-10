# Frozen role submissions and a separate finite check

Quiz10 rewrite, `pilot_0000035`. Standard-library-only, offline.
It preserves the four puzzles, five drills and eight contextual tags.
The scoped suite passes 118 tests and seventeen implementation mutations, with
99.01% combined statement/branch coverage and no exclusions. Review repaired a
key-order-dependent comparison and retained the exact original exercise inputs.

## What runs

A task contains a claim ID, a proposition, declared required input names and
supplied text. Propositions are either opaque text or the exact predicate
`sum(left) <= sum(right)` on 1–16 integers per side, each bounded by 1,000,000
in absolute value. Booleans, floating point and implicit numeric strings are
not integers. The finite predicate has no external premises or free-text
interpretation: its supplied/required input fields must be empty.

Red and Green are **role-separated submissions**, not independent reasoning
processes. Each names the canonical task digest, a contextual tag, a proposed
stance, observations and an optional separate revised task. Blue compares
`tag`, `stance`, `observations` and `revision` literally. It preserves both
sides of disagreements and every original/revised task. Similar prose is not
assumed equivalent. A revision never replaces the original checker target.

The API freezes canonical ASCII JSON bytes before comparison and requires a
separately held expected digest. The JSON CLI freezes its submitted task and
roles itself. Hashes detect changes against that retained anchor; they do not
authenticate authors or establish independent origins. Supplied input text is
recorded, not semantically validated. Missing named inputs and absence of a
bound checker are separate facts.

An actual host call to the integer checker can yield `CHECKED` or `CONTRADICTED`
for that predicate. Without a call, the claim is `UNVERIFIED`. Opaque claims
remain `UNVERIFIED` even if all named inputs are supplied, both roles agree, or
both use `[STANDARD]`. A requested promotion without a passing check produces
`ref<2>`. Global action-authority requests always produce `ref<2>`, including
after a successful check. The permission to run this local program comes from
its caller, not from a proposal. No supplied PASS or external receipt is trusted.

All eight worksheet tags are contextual proposal labels: `STANDARD`,
`IMPORTED`, `DERIVED`, `CONDITIONAL`, `INTERPRETIVE`, `CONJECTURE`, `Q-HELD`,
`REFUSED`. They do not certify their own appropriateness. `DERIVED` alone
means proposed/pending, not a proved theorem or a checked physical reading.

## Source mapping and corrections

| Source item | Executable counterpart |
|---|---|
| P10.1 / DRILL10.1 | Preserve Red observations and report missing declared definitions/map/argument for the attention/zeta claim |
| P10.2 / DRILL10.2 | Preserve Green's proposed analogy separately; list changed fields and dropped required-input names |
| P10.3 / DRILL10.3 | Refuse consensus-only promotion; positive, false-consensus and disagreement controls execute the actual finite check |
| P10.4 / DRILL10.4 | Preserve the original born_rule_hilbert_lift label, discrete_weights scope and DERIVED tag while keeping the unformalized claim UNVERIFIED |
| DRILL10.5 | Refuse global authority even after a successful finite check |
| Eight contextual tags | Retain each label without altering computed truth or authority |

The attention/zeta source does not supply enough definitions or a map to
establish the proposed category-error diagnosis. The old labels `false_lift`,
`category_error`, `authority_leak` and `analogy_only` are preserved as historical
proposals, not computed conclusions. Replacing identity with analogy does not
establish that analogy. No automatic prose audit or narrowing is claimed.

Role separation does not establish elimination of confirmation bias. The
shared helper advertises Quiz10 but its regression sequence skips it.
Finite weight normalization in `pilot_0000032` is distinct from a physical
Born interpretation or a uniqueness result; this pilot does not repeat or
promote that calculation. The field-change ledger is literal; numerical
semantic/reconstruction loss is `NOT_MEASURED`.

## Run and evidence

From the repository root:

```powershell
py -3.12 omega_engine_woland/tests/pilots/pilot_0000035/run.py
```

Run this folder's `tests/` with Python 3.12 pytest, a fresh isolated `--basetemp`
and `coverage.ini`. The coverage scope is the complete standalone production
module. The only unmeasured in-process main guard is exercised by subprocess.
The default runs every worksheet row and four additional controls. `--input`
accepts one JSON object with exactly `task`, `red`, `green`, `request` and
`execute_check`; the last is a host check switch, not a supplied verdict.
`request` is `record`, `verified` or `global_authority`.

The CLI keeps exact input bytes, result JSON, a summary and their SHA256 receipt.
Default output is `pilots/pilot_output/pilot_0000035/`. Direct JSON duplicate
keys, non-finite numbers, invalid UTF-8, oversized files (64 KiB) and malformed
JSON are refused before execution. Decoded but invalid proposals are retained
with `REJECTED`. Existing run folders are not overwritten.
Exit 0: demonstrated/recorded; 1: rejected/refused proposal; 2: read/decode/write
failure. `RECORDED` does **not** mean its underlying claim was checked.
The built-in demonstration is recorded as `MISMATCH` and exits 1 when any exercise row differs from the protocol and claim status in `EXPECTED_OUTCOMES`.

Supports: the declared finite comparison, refusal and checker behavior.
Does not support: general mathematical/prose truth checking, bias elimination,
independent model reasoning, live-model effectiveness or action authority.
Next test: novel task-bound proposals with independently calculated finite
outcomes. Live model experiments remain deferred until estate readiness.
