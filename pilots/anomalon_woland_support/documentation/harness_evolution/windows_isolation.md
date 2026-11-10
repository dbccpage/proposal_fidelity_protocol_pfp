# Windows isolation for harness candidates

OEOS owns `WindowsResearchRunner`; Woland selects it for an explicit offline
preflight. The existing evaluator and host judges consume its ordinary execution
receipt. Candidate prompts, search policies, context policies and solution code
execute under the same boundary. The host retains private checks, credentials,
provider admission and the original budget. No provider is constructed by this
Windows preflight; `run`, `resume` and `preflight --live` with Windows arguments
refuse before provider construction.

## Boundary and limits

The adapter derives a fresh AppContainer SID without creating a writable profile.
It opts out of `ALL APPLICATION PACKAGES`, verifies the AppContainer token and
the `WIN://NOALLAPPPKG` token attribute before resuming the suspended process,
and grants that SID read/execute access only to a fresh runtime/work directory.
No repository or private evaluator directory is granted access. The process
receives only explicitly constructed environment values and its stdin/stdout
pipe handles. It cannot inherit a provider key, arbitrary parent handles or a
user profile. Python starts with isolated mode, no site initialization and no
bytecode writes. These Python flags are startup hygiene; the Windows token and
ACLs enforce the file boundary even when candidate code uses `ctypes`.

The sole capability is `registryRead`, needed for Python's Windows loader
initialization on the tested host. No network capability is granted. Windows
system resources accessible to LPAC and this capability remain part of the
trusted platform. This is native OS isolation with a shared kernel, not a VM or
a claim against Windows kernel vulnerabilities.

An atomically assigned Job Object enforces one active process, one CPU affinity,
256 MiB committed memory, 20 seconds of CPU time and kill-on-close. A host wall
deadline is also 20 seconds. Child-process creation is explicitly prohibited.
Combined stdout/stderr is capped at 65,536 bytes; overflow terminates the job.
Setup failures never resume the suspended candidate and never fall back to an
ordinary process. Supervisor termination closes the non-inherited job handle.

The runtime digest binds every interpreter, library and search-path file.
Execution copies the same authenticated bytes into the temporary directory;
candidate inputs are bounded and filenames are allowlisted. Runtime links,
junctions, hardlinks, inventory drift and digest changes refuse. Workspace bytes
are hashed before execution and checked afterward. Existing runtime or source
changes cannot silently resume a frozen experiment.

## Offline reproduction

Use Python 3.12 on x64 Windows. Prepare a runtime from a trusted **standalone**
Python 3.12 installation; Microsoft Store launcher stubs are not portable runtime
executables. The command copies explicit interpreter binaries, standard-library
modules and extensions, excluding site packages. It does not install packages
or use the network. The output directory must be new.

```powershell
py -3.12 -m omega_engine_operating_system.adapters.windows_research_runtime --source C:/path/to/standalone-python312 --output C:/temp/aide2-python312
```

Record the returned `runtime_sha256`. Substitute it for `RUNTIME_SHA256` below.
Use a new offline output directory; never repurpose the historical campaign or
create a fresh wallet to evade an outstanding hold.

```powershell
py -3.12 -m omega_engine_woland.entrypoints.research.harness_cli preflight --windows-runtime C:/temp/aide2-python312 --windows-runtime-sha256 RUNTIME_SHA256 --output C:/temp/aide2-windows-preflight
py -3.12 -m omega_engine_woland.entrypoints.research.harness_cli replay --output C:/temp/aide2-windows-preflight
```

Configuration includes the versioned backend, runtime digest, capabilities and
resource limits. Each fresh isolation observation is retained separately; the
stable preflight summary can be reopened. Failed preflights retain failure
evidence and exit unsuccessfully; earlier observations remain historical evidence.
The campaign report remains
`NOT_RUN`: no independent model trials or paid calls have occurred.

Run the targeted tests from the repository root with an external basetemp:

```powershell
$env:OE_WINDOWS_TEST_RUNTIME='C:/temp/aide2-python312'
$env:OMEGA_CREDENTIAL_DISCOVERY='off'
py -3.12 -m pytest omega_engine_operating_system/tests/research/test_windows_isolation.py omega_engine_woland/tests/research/test_windows_harness.py -q --basetemp=C:/temp/aide2-windows-tests
```

These tests use synthetic private and credential files, a real local TCP listener
with a successful host-side control, an inheritable synthetic file handle, and
actual Python candidate execution. They check denied host reads/writes, LPAC's
additional denial of an `ALL APPLICATION PACKAGES` file, child-process refusal,
memory/output/time limits, supervisor death, runtime substitution, junctions,
path escape, and failure before resume. Actual public-only output can fail host
private grading; a checked workflow result and stdlib SQLite provide benign
execution controls. The fixture transport does not dispatch an Anthropic call.

The [retained verification summary](verification/windows_isolation/summary.json)
binds two passing native preflight observations, 58 passing tests with no skips,
the runtime digest and frozen source/configuration manifests. The accompanying
campaign report records zero provider calls, spend and held liability. This is
evidence for Windows build 26200 on x64; it does not establish coverage of other
Windows versions or independent model-trial results.

The reference and solution entrypoints now use the runner's fixed workspace
directory instead of `/work` literals. Their source/checker identities therefore
change for newly prepared experiments. This does not repair or rewrite historical
source pins, proofs, campaign receipts, paper archives or deposited identities.

## Output capture and runtime allocation repair

The runner rechecks its output pipe after observing process exit. A child can
write its final result between an empty pipe observation and the exit check;
the final drain retains that result and applies the same overflow and wall-time
limits. Two deterministic tests force this ordering against real LPAC children,
covering both final JSON and an output-limit violation. Both failed before the
repair. Runtime loading also checks the cumulative byte budget before opening
each file and bounds the read itself, including growth after the size check.

The [follow-up verification receipt](verification/windows_output_drain/summary.json)
records the focused Windows tests and fresh offline preflight/replay. Its source
hashes identify this repair separately from the original verification above.
The paid campaign remains deferred; these checks make no provider requests.

## Platform references

- [Microsoft: launching AppContainer and LPAC processes](https://learn.microsoft.com/en-us/windows/win32/secauthz/implementing-an-appcontainer)
- [Microsoft: process attributes, handle lists and job lists](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute)
- [Microsoft: Job Object memory limits](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information)
- [Chromium: LPAC capabilities and access boundaries](https://chromium.googlesource.com/chromium/src/+/HEAD/docs/design/sandbox.md)
