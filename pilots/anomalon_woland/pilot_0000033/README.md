# Pilot 0000033 (SN09): two-pass numeric packet emission

Rewritten from DEMO-SN-09. Offline only: no network
transport, no model performance claim and no live pricing claim.

The original 20 controls are one gate experiment. The advertised two-pass loop
was not implemented by its single-call runner. Its retained model response lacks
`untrusted_output`, although the retained receipt says PASS. Both historical files
remain unchanged; the new result does not repair their contradiction retroactively.

## Contract

Two **local profile names**, not external standards:

- `sn09-legacy-numeric-v1`: atoms `<51>` and constructors `<<rat><pos><51><2>>`.
- `sn09-hag-numeric-v1`: atoms `<51>` and constructors `<rat<pos><51><2>>`.

No implicit dialect fallback or mixed forms. HAG here is a strict numeric subset of
the authored proposal in `documentation/002_s_n/_docs/glm.md`, not its entire grammar.
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

## Historical evidence and current ownership

The deleted `omega_engine_pfp/python` owner is not restored. This offline
derivative starts from historical blob
`04e8f7303bc56a68c8716730f2bac2bb663c2075`, then changes validation and accounting.
The retained inventory names an education path; identity with the missing PFP
owner has not been proved. The modern Woland SQLite ledger has a different API
and is not substituted into this experiment.

[evidence/manifest.json](evidence/manifest.json) binds the immutable historical
data archive to commit `2653895c8e7382e9657c0c0cabe93b8c1f99599a`, exact Git blobs,
byte lengths and SHA-256 digests. The archive contains the original inventory
and all nine unchanged source snapshots. Tests read these members as data, verify
all hashes, parse the twenty controls with AST/literal evaluation, and check the
retained response/receipt contradiction. They never import or execute archived
code. These checks work without historical Git objects or old monorepo paths;
they establish retained bytes, not a new model or gate replay.

Live OpenRouter integration, current model/price selection and measured model
results remain pending until estate readiness. This migration does not count
toward the 100 new pilots.

## Run and verify

From the repository root with Python 3.12:

```powershell
py -3.12 -m omega_engine_woland.tests.pilots.pilot_0000033.run
```

The default task transcodes `51/2` from the legacy form to the head-atom form.
`--task path.json` accepts exactly `source_profile`, `target_profile`, and
`source_wire`. Default responses are generated locally and labeled scripted.
Every CLI run writes a new directory under `pilots/pilot_output/pilot_0000033`.

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
