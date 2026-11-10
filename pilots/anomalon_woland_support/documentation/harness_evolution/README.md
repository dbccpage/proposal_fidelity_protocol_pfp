# Evidence-bound harness evolution

Current operator scope: verify on Windows; Linux testing is no longer planned.
Paid Anthropic calls remain deferred. In addition to offline replay, contracts,
accounting, learning and publication custody, the new OEOS Windows adapter runs
candidate code in a native LPAC and Job Object. See the
[Windows isolation protocol and reproduction commands](windows_isolation.md).
The original frozen campaign remains Linux-specific; its receipts and budget
are preserved. The Windows entrypoint currently admits only offline isolation
preflight. A future paid campaign requires a separate reviewed protocol decision.
For authorized future Anthropic calls, use the canonical credential resolver and
the main checkout's `.env`; never copy its key into a worktree or receipt.

The explicit research entrypoint is
`python -m omega_engine_woland.entrypoints.research.harness_cli`.
Its commands are `preflight`, `run`, `resume`, `replay`, and `report`.
This experimental path does not publish a PR, admit a production operator or
activate an OEEIS antibody. Ordinary learning hooks keep their existing behavior.

The protocol is defined in `infrastructure/research/harness_protocol.py` and
frozen into the retained campaign journal before discovery. The original $40
budget persists in `budget.sqlite`; do not create a new directory to bypass an
unreconciled hold. Every returned model response, including malformed content,
is retained before parsing. Pricing evidence and its SHA-256 binding accompany
the configuration. No paid calls have run in this delivery. The operator explicitly deferred Linux
testing and paid execution on 2026-10-23.

Since 2026-10-27 (EPIC-OE-PFP-010 M3) every provider call is a PFP task turn.
`HarnessProvider.call` prepares the campaign's system and user text into the
public PFP prompt (task `harness/<role>`, attempt = the occurrence, answer a JSON
object) before admission, and checks the reply against that turn's schema before
any content reaches the campaign. A paid reply outside the schema settles its
cost and is a `TYPED_REFUSAL`. Replay re-derives the turn from the admitted body
and re-runs the check on the retained bytes. Because the provider source changed,
current source is a new campaign; the original frozen campaign still refuses on
current `main`, as above.

## Local preparation and replay

The original campaign belongs to the frozen author-review archive, not to the
latest `main`. At main `e7420ae75737df9dbb0785cc102e8179fa6feb8c`, twenty
previously pinned files differ. Replaying the original journal against that
checkout must refuse; do not refresh its source manifest to make it pass.

To reproduce the original zero-call report from any current checkout, use the
checksum-pinned archive and a **new directory** (existing destinations refuse):

```powershell
py -3.12 omega_engine_woland/documentation/harness_evolution/replay_review_archive.py --output C:/temp/aide2-frozen-replay
```

This verifies the original archive, extracts its source subset, checks the
canonical manifests and archive before and after replay, and retains logs plus
`replay_receipt.json` in the destination. Python runs with isolated startup,
explicit existing dependency directories, no credential environment, and audit
refusals for networking and child processes. This is an offline reproduction
guard, not Linux containment or a fresh dependency installation. The original
archive and repository campaign are not modified. The report stays NOT_RUN.

For a distinct **offline preparation check** of current source, use the following
commands from the repository root. This does not authorize a replacement paid
campaign, carry forward old results, or reset the original campaign budget:

```powershell
py -3.12 -m omega_engine_woland.entrypoints.research.harness_cli preflight --output <new-run-directory>
py -3.12 -m omega_engine_woland.entrypoints.research.harness_cli replay --output <same-run-directory>
py -3.12 -m omega_engine_woland.entrypoints.research.harness_cli report --output <same-run-directory>
```

Offline preflight prepares the source, checker, task and configuration manifests;
it does not claim container isolation, provider compatibility or model success.
Replay requires the frozen source bytes. Changing those bytes requires a new
protocol version and new baseline evidence, not editing old receipts.

## Historical Ubuntu handoff (outside current scope)

The frozen Linux design required an SSH hostname or alias, username and an independently verified
host-key fingerprint. A host key obtained only from an unauthenticated network
scan is not that verification. The proposed machine is a user-provisioned
DigitalOcean Basic Droplet, Ubuntu 24.04 LTS, x86-64, 2 vCPUs, 4 GiB RAM,
80 GiB disk. Hosting is separate from the $40 Anthropic ceiling.

Install rootless Podman, uidmap, slirp4netns, fuse-overlayfs, Python 3.12 with venv,
Git and the repository's Rust build prerequisites. Use an ordinary login user
with subordinate UID/GID ranges and cgroup v2 delegation. Build the native host
from the frozen checkout using the existing Rust workspace. Do not run the
campaign as root. No candidate source is executed on the host.

Pull an official Python 3.12 image during host preparation, record its immutable
local image ID, and pass that ID to the CLI. Execution uses `--pull=never`,
`--network=none`, read-only mounts, no extra capabilities, no new privileges,
one CPU, 256 MiB memory, 32 processes, bounded output and a 20-second timeout.
Only permitted candidate files and that invocation's task inputs are mounted.
The actual preflight must confirm isolation on this host; merely installing
Podman is insufficient. See the [Podman run documentation](https://docs.podman.io/en/latest/markdown/podman-run.1.html).

Refresh the official model/pricing observations before dispatch. The supplied
observation expires after 24 hours; stale pricing fails closed. A refresh may
update observation timestamps and evidence while preserving model IDs, prices,
experiment identity and the original ledger. Changed prices require a reviewed
protocol revision; they cannot silently continue a comparison. Pass the matching
source observation file with --pricing-evidence; its exact hash is checked. Resolve the
Anthropic credential through the existing canonical credential source. Never
copy it into candidate files or the campaign evidence directory.

```bash
python3 -m omega_engine_woland.entrypoints.research.harness_cli preflight --live --image sha256:ACTUAL_IMAGE_ID --prices CURRENT_PRICES.json --pricing-evidence CURRENT_EVIDENCE.json --output RUN
python3 -m omega_engine_woland.entrypoints.research.harness_cli run --image sha256:ACTUAL_IMAGE_ID --prices CURRENT_PRICES.json --pricing-evidence CURRENT_EVIDENCE.json --output RUN
python3 -m omega_engine_woland.entrypoints.research.harness_cli resume --image sha256:ACTUAL_IMAGE_ID --prices CURRENT_PRICES.json --pricing-evidence CURRENT_EVIDENCE.json --output RUN
```

Replace the uppercase arguments with actual paths and the observed image ID.
For a newly prepared host use a fresh directory before any paid dispatch. Once
paid dispatch starts, all subsequent work must keep its original ledger.
An unknown transport outcome requires reconciliation of that occurrence before
resume; the implementation does not invent a zero charge or silently retry it.
The $2 retry reserve is not automatically spent.

## Experimental interpretation

Selection and confirmation are optimization data. Transfer stays untouched until
all three trajectories finish. SQL appears only in transfer. Ablations use a
different panel and the final incumbent of trajectory zero, selected in advance.
Ignition uses three paired short trajectories and remains exploratory.

The current-policy baseline is an explicit projection of sequential propose/check
behavior into the common task adapter, not an assertion that the unchanged
production learning service has executed these tasks. The remote host, live
compatibility, calibration and every paid phase remain pending.

The original dirty checkout's overlapping memory/gateway and operad changes are
listed in `dependencies.json`. They were not copied into this isolated checkout.

Ablations disable observable feature switches; candidate admission probes these
switches and each context is checked again during trials. This does not establish
that a model has forgotten a learned strategy or that an arbitrary prompt has no
implicit diagnostic content. No causal ablation claim is licensed before live
measurements and compliance checks.
