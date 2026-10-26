# PFP Lab: plan for a tool to test Proposal Fidelity Protocol ideas

AuthorityEffect: None.
Status: Phases 0 to 4 implemented on 2026-10-26 (see "What was built" below);
Phases 5 and 6 and the legacy-import track are not started. Date: 2026-10-26.
Rubric: the `SCORING.md` Jeremy attached, Version 2.0.0 with the 2026-10-22
revision (SHA-256 `41f114724413adcc3c1dea465e027531a5665bbf65e748bc02f4005d2e90660f`,
identical to `theory_of_finite_quantum_mechanics/SCORING.md`).

## What was built, and where it differs from this plan

| Plan | Built | Where |
| --- | --- | --- |
| Python core from the Paper 005 governor | As planned; a differential test runs the unmodified Paper 005 file as an oracle | `pfp_lab/core/`, `pfp_lab/core/PROVENANCE.md` |
| CLI and JSON-RPC stdio server | As planned (`python -m pfp_lab.cli.main`, script `pfp-lab`) | `pfp_lab/cli/` |
| Local web page | As planned (`pfp-lab-web`, loopback by default) | `pfp_lab/web/` |
| C# WPF app over the JSON-RPC contract | As planned. The machine's NuGet source mapping blocks the xUnit runner and SonarAnalyzer, so tests use a small self-hosted runner and the build uses only the SDK analyzers (CA1502 cyclomatic limit 10 as an error) | `csharp/` |
| Port `governance/` from the sibling repository | Reimplemented as a small typed Python checker with the same rule (byte-bound companion per source, floor, baseline, pinned boilerplate) so that it could itself be held to L4D; plus evidence capture, Gate 5 metrics and a two-language mutation tool | `governance/` |
| Stryker.NET and cosmic-ray for mutation testing | Not available or not needed; the in-repo tool mutates Python on the AST and C# lexically, with six-outcome accounting and a justified, hash-bound equivalents list | `governance/tools/mutation.py`, `governance/evidence/equivalents.json` |
| One module per concern | Thin modules (error list, receipts, server, pack catalog, records, lexical helpers, small C# types) were merged into the module they serve, because a file that small cannot honestly score L4; packs became JSON data | `pfp_lab/core/packs/*.json` |
| Legacy-name alias shim | Dropped: it would have had to spell the upstream names, which are not to appear in this repository | — |
| Test sources at L4D | Test sources are held to L2D in a `test` support category marked as awaiting the maintainer's approval | `governance/policy.json` |

## 1. What the tool is for

People should be able to take a PFP idea, run it, and see what the protocol
does with it: which proposals are admitted, which are refused and why, how the
defect moves, and what receipt comes out. The repository's own vocabulary
gives the unit of work:

- A **scenario** declares a finite constraint graph (vertices, weighted edges)
  and its edge claims, as in the Paper 005 worked triangle with claims (1,1,1)
  and weights (1,2,3).
- A **proposal** is one move from the four-move vocabulary in
  `papers/005_pfp_practitioners_field_manual/code/l1_symbol_game_governor.py`:
  ASSERT, CUT, VERIFY, RETRACT.
- The **governor** returns a verdict (MonotonicDescent, ExactRepair,
  IdempotentStationary, DefectIncrease, InvariantViolation, CarrierViolation,
  MoveViolation, IncompleteProposal, Refused, Retracted, Verified) with exact
  defect values before and after.
- A **receipt** is a content-addressed record of the scenario, the moves and the
  verdicts, so a run can be replayed and checked by someone else.

Later "idea packs" add the other components: screening proposals against the
epistemic immune system's antibodies (`eis/`), checking typed composition
(`operads/`), and tracking prompt lineage (`pciv/`). The papers supply the first
scenarios and their expected outcomes.

The default mode is offline, with zero provider calls and zero spend, which
matches the NOT_RUN discipline the papers already record. A model-backed
proposer is an optional later phase.

## 2. What is in the repository today

| Area | What it holds | What it means for the tool |
| --- | --- | --- |
| `pfp/` | 3,004 Python files (1,470 tests), 7,744 JSON files, an argparse CLI (`entrypoints/cli/pfp.py`), a FastAPI router (`entrypoints/api/`), and a local finite-gauge web workbench (`entrypoints/web/`, FastAPI plus 595 lines of JS) | Proves the shape of a local web workbench, but its request bodies are `dict[str, Any]`, which misses RULE_PY_001. Too large and too entangled to certify as a whole. |
| `eis/` | Epistemic immune system: antibodies, antiskills, receipts, a CLI front end (110 Python files) | First idea pack: screen a proposal before the governor sees it. |
| `operads/` | Typed composition, registry, skills, StructureBench (673 Python files) | Second idea pack: check that a composed plan type-checks before it runs. |
| `pciv/` | Prompt Civilization lineage and presenters (93 Python files) | Third idea pack: record which proposal descended from which. |
| `ops/` | Operations, governance, the only `pyproject.toml` (package name `the-symbol-game`, Pydantic 2, Hypothesis, FastAPI) | Source of toolchain pins, not a dependency of the core. |
| `papers/` | Papers 000 to 029, each with code, tests, a claim ledger and checksums | Self-contained, standard-library replays. The Paper 005 governor (917 lines) is the cleanest seed for the core, and its worked examples give an independent test basis. |

There is no C# code, no `SCORING.md` and no `governance/` folder in this
repository yet.

### The old import names

The copied code still imports upstream package names (written `<prefix>_*` below). Across `pfp`, `eis`,
`operads`, `pciv` and `ops`, the import statements resolve to these targets:

| Old name | Imports | Present in this repository? |
| --- | --- | --- |
| `<prefix>_pfp` | 2,799 | Yes, as `pfp/` |
| `<prefix>_woland` | 1,242 | **No** (203 non-test `pfp` files import it) |
| `<prefix>_operations` | 1,137 | Yes, under `ops/` |
| `<prefix>_operads` | 905 | Yes, as `operads/` |
| `<prefix>_projects` | 634 | **No** |
| `<prefix>_epistemic_immune_system` | 296 | Yes, as `eis/` |
| `<prefix>_operating_system` | 257 | Yes, under `ops/` |
| `<prefix>_governance` | 87 | Yes, under `ops/` |
| `<prefix>_prompt_civilization` | 79 | Yes, as `pciv/` |
| `<prefix>_workflows_agents_skills` | 70 | **No** |
| others (`product_planning_office`, `applications`, `research_papers`, `education`, `symbol_game`, `providers`) | 64 | Partly |

Files importing old names: 1,240 in `pfp`, 382 in `ops`, 344 in `operads`,
64 in `eis`, 48 in `pciv`. A rename fixes the packages that exist here. It
cannot fix the Woland, projects and workflows imports, because that code was
not copied.

### Where the existing code stands against the rubric

Quick inspection counts, not scores:

- `assert` statements in non-test code: 402 files in `pfp` (368 of them under
  `infrastructure/tower_evidence` and `infrastructure/tower_research`), 42 in
  `ops`, 32 in `operads`, 5 in `eis`, 1 in `pciv`. Calibration scenario 6 puts a
  production assert that carries validation at Gate 3 = E.
- Pydantic imports: 97 files in `pfp`, 14 in `operads`, 40 in `ops`, none in
  `eis` or `pciv`.
- No `mypy` configuration exists anywhere in the repository.

### What the attached rubric adds

Section 1.5 sets the acceptance floor: a **completed** score at L4 or L5 with
composite grade D or better. An unassessed gate is a rejection, not a pass.
Existing sources listed in `governance/baseline.json` with unchanged bytes are
grandfathered; **changing a file removes its exemption**.

That last rule shapes the plan. A mass rename of the 2,078 files that import
old upstream package names would change their bytes, so every renamed file would
then have to meet L4D on its own. The plan therefore keeps the new tool apart
from the legacy estate and leaves legacy bytes untouched (Section 6, parallel
track).

## 3. Web page, CLI and C# app

| | Local CLI | Web page | C# desktop app |
| --- | --- | --- | --- |
| Who can use it | People comfortable in a terminal | Anyone with a browser | Windows users who install it |
| Setup for a new user | `pip install` and Python 3.12+ | None for a hosted static page; `pip install` for the local server | An installer that bundles the Python core |
| Seeing an idea work | Tables and JSON; no graph picture | Graph editor, defect chart, move-by-move trace | Same as web, native Windows feel |
| Reuse of the Python core | Direct import | Direct import (local server) or Pyodide in the browser | Across a process boundary over a JSON contract |
| Scripting, CI, replay | Best | Weak | Weak |
| Extra rubric burden | Python only | Python plus a JS front end | C# rules RULE_CS_001 to 006 and the Section 5 cross-language rules |
| Effort | Low | Medium | High |

**Recommendation.** Build all three on one Python core. The CLI comes first
because it is cheapest and gives replayable receipts that the other two front
ends are tested against. The web page comes second. The C# app comes third.

The C# app must not reimplement the protocol. The core works in exact
rationals (`Fraction`), and .NET has no built-in rational type, so a second
implementation would be a second place for numbers to drift and a second body
of exact code to certify. Instead the C# app starts the Python core as a child
process (`pfp-lab serve --stdio`) and speaks JSON-RPC to it. The JSON Schema of
every message is generated from the Pydantic models and checked in; the C# DTOs
are generated from that schema, so both sides share one definition. Rationals
cross the boundary as canonical strings such as `"3/2"` and are held in C# as
a small `Rational` struct over `System.Numerics.BigInteger` that only parses,
compares and displays (no arithmetic), which satisfies Section 5.1 (interface
type conservation) without re-certifying the math.

A hosted, install-free page is possible later by running the core in the
browser with Pyodide, because the core will have no native dependencies
beyond Pydantic.

## 4. Architecture

```
pfp_lab/                     new Python package; imports nothing from the old upstream package names or the legacy trees
  core/
    domain/                  graph, cochains, Phi_1, governor, moves, verdicts (pure, exact)
    contracts/               Pydantic v2 models for every external input and output
    receipts/                canonical JSON + SHA-256 receipts, replay and verify
    errors.py                typed failure variants; Result[T, E] in the style of pfp's CONTEXT.md
    admission.py             the single place integers and rationals are admitted
  packs/                     idea packs behind one port: scenarios from papers, then eis, operads, pciv
  cli/                       argparse front end, including `serve --stdio` for the C# app
  web/                       FastAPI on 127.0.0.1 plus a static HTML/JS page
  tests/
contracts/schema/            generated JSON Schema for the stdio and HTTP contracts
csharp/PfpLab.Desktop/       WPF app (net8.0-windows), MVVM, no protocol logic
csharp/PfpLab.Client/        generated DTOs, Rational struct, process host, JSON-RPC client
csharp/PfpLab.Tests/         xUnit tests, including contract tests against the real Python core
governance/                  ported from theory_of_finite_quantum_mechanics (Section 5)
SCORING.md                   the attached rubric, byte for byte
```

Design rules:

1. **One direction of dependency.** `cli` and `web` depend on `core`; `core`
   depends on nothing in the repository. An import-linter contract fails the
   build if `core` imports `pfp`, `eis`, `operads`, `pciv`, `ops` or any
   old upstream package name.
2. **Exact arithmetic only.** Values are `Fraction` built from integer pairs or
   strings. JSON carries rationals as strings, never floats, at the CLI, HTTP
   and C# boundaries.
3. **Admission at the edge.** Every scenario, move and request passes through a
   Pydantic v2 model with `strict=True`, `extra="forbid"` and `frozen=True`,
   whose validators reject booleans, floats and non-canonical rational strings.
   Inner code receives only admitted value objects.
4. **Typed failures.** Domain refusals are verdicts, not exceptions. Invalid
   input is a typed admission error. The CLI maps each to a documented exit
   code, the web layer to a documented HTTP status, the stdio server to a
   documented JSON-RPC error code, and the C# client to a typed exception or
   result (Section 5.2, failure translation).
5. **Seeded from Paper 005, with provenance.** The governor is ported from the
   Paper 005 copy, keeping its vendored-from path, commits and SHA-256 header,
   and its documented fixes (R008-04 and the 2026-09-28 changes). The port
   splits large methods so each function meets the complexity ceilings.
6. **Receipts are replayable.** A receipt holds the scenario, every move, every
   verdict and the core version, canonicalised (RFC 8785) and hashed.
   `pfp-lab verify` replays it and refuses if any verdict or hash differs. The
   C# app and the web page save and load the same receipts.

### First version of each front end

- **CLI (`pfp-lab`):** `run SCENARIO`, `step` (interactive), `replay RECEIPT`,
  `verify RECEIPT`, `packs list`, `scenario new`, `serve` (HTTP) and
  `serve --stdio` (JSON-RPC). Output as a table or `--json`.
- **Web:** a graph editor for vertices, edges, weights and claims; a move
  palette; a step trace with each verdict and exact defect; a defect chart;
  receipt download and upload. The server binds to loopback by default and
  refuses a non-loopback bind unless the operator passes an explicit flag.
- **C# app:** the same screens as the web page. It owns the child process: it
  starts it with a pinned interpreter path, passes a `CancellationToken` to
  every call, times out a silent core, and disposes the process on exit or
  error.

## 5. How every component reaches L4D, and how that is checked

### Reuse the governance machinery that already exists

`theory_of_finite_quantum_mechanics/governance/` already enforces this exact
floor: one `<name>.contract.score.yaml` companion per governed source binding
its path and SHA-256 to a contract and a completed score; `policy.json` and
`baseline.json`; a `governance-check` binary with `check`, `explain`, `list`
and `baseline`; `scripts/score_scope_contracts.py record`; and a sequential,
recoverable `governance/tools/mutation_campaign.py` that runs natively on
Windows. Several of those tools already carry L4D scores.

The plan ports it rather than writing a new harness:

- Copy `governance/` and the two scripts, with their companions, and record
  their source hashes for provenance.
- Write a PFP `policy.json` whose populations are `pfp_lab/**/*.py` and
  `csharp/**/*.cs`, with the usual exclusions. The current checker knows Rust,
  Python and Lean; adding a C# population is a small, scored change to it.
- Write `baseline.json` for the legacy trees (`pfp`, `eis`, `operads`, `pciv`,
  `ops`) with their current bytes, so they are grandfathered and frozen, and
  CI fails if any of them changes without a score.
- Use the existing `support_exceptions` mechanism for tests only: test modules
  may be scored at a lower level (the sibling repository uses L2D or L3D for
  regression tests) but keep grade D and full integrity checks. Every runtime
  module in `pfp_lab` and `csharp` must be L4D or better.
- CI runs `governance-check check --changed-since origin/main` in `enforce`
  mode on every pull request, on Windows.

Under Section 5.5 the system score is the minimum over the chain, so the C#
app, the stdio contract and every legacy module an idea pack calls all count.

### Gate by gate for Python

The floor is D. The plan aims at C on every gate so a single slip does not
drop the system to E.

| Gate | What would make it E (must not happen) | What the plan does (target C or better) | How it is checked |
| --- | --- | --- | --- |
| G1 Provenance | Missing provenance; exported behaviour does not match the claim | `AuthorityEffect: None` and a contract URN per module; the Paper 005 provenance header carried over; each public function mapped to its paper claim ledger entry in the companion's `symbols` and `owned_invariants` | `governance-check` binds the path and SHA-256; a header check runs in CI |
| G2 Semantics and numbers | A float in an exact path; truncating division; a bool admitted as an int | Exact profile; `Fraction` from int pairs or strings only (RULE_PY_004); one `admit_int` helper with `type(v) is not bool` (RULE_PY_002); Pydantic strict models at every public boundary (RULE_PY_001) | An AST lint over `core` forbids float literals, `float(...)`, `Fraction(...)` with a non-int, non-string argument, and `isinstance(x, int)` outside `admit_int`; negative tests feed `True`, `1.0`, `"0.1"` and `NaN` and expect refusal |
| G3 Failure behaviour | An unhandled exception on reachable input; a production `assert` doing validation | No `assert` outside tests (RULE_PY_003, Ruff S101); typed errors for every expected failure; no bare or broad `except` in `core`; a node or step budget on every search | Ruff S101, BLE001 and E722; the full suite run again under `python -O`; Hypothesis fuzzing of the admission layer with no unexpected exception allowed |
| G4 Verification | No tests; tautological tests; R < 0.60 | Unit and boundary tests per function; Hypothesis properties (P_S idempotence, Phi_1 ≤ D(s), RETRACT restores the snapshot, a rejected digest cannot re-enter as in `pfp/gate.py`); differential tests against the original Paper 005 governor as an independent oracle; the Paper 005 hand-checked worksheet as golden values; CLI, HTTP and stdio contract tests; a mutation campaign with R ≥ 0.70 targeted | `pytest`; `mutation_campaign.py` reporting killed, survived, equivalent, invalid, inconclusive and unrun, with R computed by the conservative formula and timeouts never counted as kills |
| G5 Structure | CCN > 50, cognitive > 40, nesting ≥ 9 | Target CCN ≤ 10, cognitive ≤ 15, nesting ≤ 3 per function; the 917-line governor split into per-move handlers | Lizard or Radon for CCN, complexipy for cognitive complexity, an AST script for nesting; results cited as evidence in each companion |

Typing: `mypy --strict` with a pinned version and checked-in config
(RULE_PY_006), plus `pydantic.mypy` plugin. Evidence for every tool run goes
through `capture_evidence.py` so each record carries command line, tool
version, working directory, input and report hashes, and exit status.

### Why the level is L4, and how that is shown

L4 asks for intentional API grain, edge-case handling, typed failure modes and
resource lifecycle. The plan meets it with a versioned public contract (the
generated JSON Schema), a typed error enumeration, bounded searches, and
explicit server and child-process lifecycle. Each companion's `level_basis`
records the reasons; the level is not claimed in advance.

### Per component

| Component | Profile | Main risks | Specific checks beyond the table above |
| --- | --- | --- | --- |
| `core/domain` | Exact | Rational drift; the Phi_1 search blowing up | Differential test against Paper 005; documented complexity of the spanning-forest enumeration and a hard budget; property tests on random small graphs |
| `core/contracts`, `admission.py` | Non-Numeric with exact fields | Bool and float admission; extra fields | Adversarial fixture table of bad inputs; schema snapshot test so a contract change is deliberate |
| `core/receipts` | Exact | Non-canonical JSON giving a different hash | RFC 8785 canonicalisation; tamper tests that flip a byte, reorder keys or change a verdict and expect refusal |
| `cli` (incl. stdio server) | Non-Numeric | Exit and error codes that hide failures | Subprocess contract tests for every exit code and JSON-RPC error; end-to-end receipts for the Paper 005 session |
| `web` (Python) | Non-Numeric | Untyped bodies; non-loopback exposure | Pydantic request and response models; TestClient contract tests for each status; a test that a non-loopback bind is refused by default |
| `web` (JS) | Non-Numeric | Outside the governed Python and C# populations | Playwright smoke test of one full session; recorded as evidence on the `web` Python companion |
| `csharp/PfpLab.Client` | Non-Numeric with exact fields | Null from JSON (RULE_CS_002); `!` suppressions; leaked processes (RULE_CS_003); missing cancellation (RULE_CS_004) | `<Nullable>enable</Nullable>` and `TreatWarningsAsErrors`; runtime null and range checks on every deserialized DTO; a build rule banning the null-forgiving operator in this project; `IAsyncDisposable` process host; every async method takes a `CancellationToken`; contract tests run against the real Python core and replay the CLI's receipts |
| `csharp/PfpLab.Desktop` | Non-Numeric | UI thread blocking; unhandled exceptions | View models tested without UI; a global handler that shows and logs typed failures; no logic beyond display and command dispatch |
| each idea pack | Depends on pack | Pulling an unscored legacy module into the chain | A pack is admitted only after the legacy slice it calls has its own L4D companion, or after the needed logic is re-homed into the pack with tests |

C# mutation testing uses Stryker.NET with the same six-outcome accounting,
mapped into the score record by hand where Stryker's categories differ.

## 6. Phases

Each phase ends when `governance-check` passes in `enforce` mode for every file
it added or changed. No phase starts the next until that holds.

**Phase 0: Ground rules (about 2 to 3 days).**
Add the attached `SCORING.md` byte for byte. Port `governance/` and its
scripts from `theory_of_finite_quantum_mechanics`, write the PFP `policy.json`,
and baseline the legacy trees at their current bytes. Add a root
`pyproject.toml` for `pfp_lab` on Python 3.12 or newer (3.14.2 is installed
here) with pinned Ruff, mypy, pytest, Hypothesis, import-linter, Lizard or
Radon, and complexipy. Exit: CI fails on a deliberately unscored new file and
passes on a trivial scored one.

**Phase 1: The core (about 1 to 2 weeks).**
Port the Paper 005 governor into `core/domain` with provenance; write the
contracts, admission, typed errors and receipts. Exit: every `core` module has
a companion at L4D or better (aim L4C), differential tests agree with Paper 005
on all its worked examples, and a receipt from the Paper 005 session replays
byte for byte.

**Phase 2: The CLI and stdio server (about 1 week).**
`pfp-lab` with the commands in Section 4, and the generated JSON Schema for the
stdio contract. Exit: CLI modules at L4D or better; the Paper 005 session runs
end to end from a scenario file to a verified receipt.

**Phase 3: The local web page (about 1 to 2 weeks).**
FastAPI with Pydantic models and the static page. Exit: API modules at L4D or
better, the Playwright smoke test passes.

**Phase 4: The C# app (about 2 to 3 weeks).**
Add the C# population to the governance checker first. Then build
`PfpLab.Client` against the generated schema, then the WPF app. Exit: every
`.cs` file at L4D or better; a receipt produced in the C# app verifies with
`pfp-lab verify`, and the reverse.

**Phase 5: Idea packs (ongoing).**
In this order: scenario packs from Papers 000, 001 and 005, and the 023 to 027
replays with their rejection controls; then EIS screening; then operad
composition checks; then pciv lineage. Each pack enters only with its own
companions and only after the legacy code it calls is scored or re-homed.

**Phase 6: Optional reach.**
A hosted static page running the core under Pyodide; a model-backed proposer
behind a provider port, off by default, with a hard budget and receipts that
record spend.

**Parallel track: legacy imports, without touching legacy bytes.**
Because editing a baselined file removes its exemption, the plan does not
mass-rename imports. Instead, one small scored module installs import aliases
(`<prefix>_pfp` to `pfp`, `<prefix>_epistemic_immune_system` to `eis`,
`<prefix>_operads` to `operads`, `<prefix>_prompt_civilization` to
`pciv`, and the `ops` subpackages) for legacy code that an idea pack needs.
Modules that import Woland, projects or workflows code stay unusable and are
listed as such. A real rename of any legacy file is done only together with
bringing that file up to L4D.

## 7. Decisions for Jeremy

1. **C# UI framework.** The plan assumes WPF on `net8.0-windows`, since
   verification is Windows-only. Avalonia would make the app cross-platform at
   some extra cost. WinUI 3 is the newer Microsoft option but has heavier
   packaging.
2. **Audience for the web page.** If it is for outside readers of the papers,
   the hosted Pyodide page in Phase 6 should move ahead of the C# app.
3. **Grade target.** The floor is L4D. The plan aims at C on every gate for
   margin. Aiming at B would mean R ≥ 0.85 on critical paths and a negative
   test for every error path, adding about a third to Phases 1 to 4.
4. **Porting governance.** The plan copies the governance tooling from
   `theory_of_finite_quantum_mechanics`. If you would rather share one copy
   across repositories, that becomes a separate package first.
