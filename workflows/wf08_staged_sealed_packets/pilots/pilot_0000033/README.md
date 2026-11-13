# pilot_0000033: staged numeric packets with an offline reservation ledger

A host freezes a numeric expression and a target packet profile. Stage 1 must
return a typed draft tree that matches the original; only then does stage 2
transcode it, and the result must match both. Both stages draw on one local
reservation ledger with a simulated USD 0.010 cap.

Status: copied from the imported pilot estate. Offline tests only: no network
transport, no model performance claim and no live pricing claim.

Left out: the `evidence/` folder (a hash-pinned archive of the historical
sources) and the one test that read it. The old bytes are in git history at
commit `90228464`.

## Contract

Two **local profile names**, not external standards:

- `sn09-legacy-numeric-v1`: atoms `<51>` and constructors `<<rat><pos><51><2>>`.
- `sn09-hag-numeric-v1`: atoms `<51>` and constructors `<rat<pos><51><2>>`.

No implicit dialect fallback or mixed forms. HAG here is a strict numeric subset of
the authored proposal in the source repository, not its entire grammar.
The pinned `mss-boundary-v1` grammar is not modified or relabeled.

Registered numeric forms are nonnegative integers up to 1,000,000,000, `rat` with
three children (sign, numerator, denominator), and `sum6` with six numeric children.
Fractions must be reduced, denominators positive, zero `pos/0/1`; integers have no
leading zeros. Empty `<>` is outside this numeric profile, not globally illegal.
Wire input: 4,096 bytes, 32 syntactic levels, 512 packets. JSON draft: 65,536 bytes,
32 levels, 512 semantic nodes. Legacy constructor heads count as wire packets but
not semantic children. Bytes are never trimmed or repaired.

The host freezes an original expression and target profile. Stage 1 returns a
typed draft tree and must match the original structure. Only then is stage 2
invoked to transcode that admitted draft. Its parsed tree must match both the
draft and original: numerical equality alone is insufficient. A bad first stage
prevents the second call. Raw task, requests, responses and extracted wire are
retained separately with hashes.

Both stages use the visible pilot-local `budget_ledger.py` with **one simulated
USD 0.010 cap**. All three ledger caps default to, and cannot exceed, 0.010.
Unknown billing retains its reservation; failure after dispatch is not free.
Tests use simulated billing, separately labeled from actual cost (zero). No
automatic retries or resume are implemented. An existing output directory is
refused, not overwritten. The ledger is not a protection against a dishonest
provider charging above its reservation; that condition is recorded as a breach.

Money inputs at this pilot's boundary are plain, nonnegative decimal **strings**
with at most six integer digits and nine fractional digits. A fixed 50-digit local
decimal context makes the two-stage sums exact independently of the caller's
context. Longer mantissas or exponent notation are refused before dispatch, or
held as unknown billing after dispatch. The local ledger also applies this token
boundary and its own fixed context to direct calls and persisted rows. It binds
reservations to amount, request hash, model and pricing identity; validates stored
states; and keeps unknown or breached charges from silently releasing liability.
This does not repair any other ledger implementation globally.

Creation, reads and replacement run under the same platform file lock. A marker
in that lock file detects disappearance of an established ledger while the marker
survives. Deleting or forging both files cannot be detected by this local storage
scheme. The controller therefore still requires a new output directory and
provides no resume or reset authority. Prior-unknown exemptions can name only
charges already unknown when that explicit ledger handle is opened.

## Run and verify

From the repository root:

```powershell
python -m pytest workflows/wf08_staged_sealed_packets/pilots/pilot_0000033 -q -p no:cacheprovider
python -m workflows.wf08_staged_sealed_packets.pilots.pilot_0000033.run
```

The default task transcodes `51/2` from the legacy form to the head-atom form.
`--task path.json` accepts exactly `source_profile`, `target_profile`, and
`source_wire`. Default responses are generated locally and labeled scripted.
Every CLI run writes a new directory under `../pilot_output/pilot_0000033`.

Tests live in `tests/`. Run targeted pytest with this pilot's `pytest.ini` and a
fresh `--basetemp=scratch/sn09_verification`. `coverage.ini` measures both
production files **and the local budget ledger**, with branch coverage and a
98% combined minimum. The platform branches in the ledger remain reported;
they are not hidden with coverage exclusions. Windows locking is tested here;
the separate POSIX locking implementation is not tested on this host.

Fourteen implementation mutations test whitespace laundering, canonical forms,
integer bounds, fraction reduction, arity, both structure checks, the shared cap,
unknown-charge retention, raw custody, ledger exposure/holds and the decimal
boundary. Failed candidate verification runs are retained alongside later results.
