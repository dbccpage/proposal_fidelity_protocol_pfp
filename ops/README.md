# The Symbol Game

A host-checked protocol for tasks that can be stated as relations on a finite
declared carrier. A proposer, which may be a language model, submits a
candidate. An independent host re-derives the step, scores a discrete L1
obstruction, and either admits the move or returns a typed refusal.

This repository holds that host, the Rust workspace behind it, the Lean 4
developments, the education strands, the CODA atlas, and the surrounding
engine packages. Python package metadata is in `pyproject.toml` (`the-symbol-game`
0.1.0, Python >= 3.10). Repository gate commands target Python 3.12.
On Windows, select it with `py -3.12`; on Linux, use the checkout's
`.venv/bin/python` after [`bootstrap_linux.sh`](scripts/bootstrap_linux.sh).
The Linux bootstrap selects 3.12 and refuses a different existing environment
before installing the editable `.[dev]` package or building the native host.
The package metadata's wider version range is a compatibility declaration,
not a claim that every permitted Python version passed the repository gates.
[`windows_setup.ps1`](scripts/windows_setup.ps1) configures Windows long paths,
Git settings and drive substitution; it does not install Python or dependencies.

> **AuthorityEffect: None.** A completed run is not a proof. A passing test
> suite is not a theorem. A host receipt records that declared code ran. No
> prompt, receipt, or model generation mints authority. The proposer proposes.
> The host disposes.

The product-boundary contract on disk is `status: mathematical_wip`:
[`symbol_game.contract.yaml`](governance/contracts/contracts_pfp/symbol_game.contract.yaml).

## Start here

| Door | Where |
| --- | --- |
| Five-minute standard-library walkthrough | [`quickstart.py`](quickstart.py) |
| How to play | [`004_oepfp/_how_to_play`](education/documentation/004_oepfp/_how_to_play/README.md) |
| First paper: S(n), MSS-N, and basic packets | [`000_pfp_introduction`](atlas/coda_atlas/F004_papers/015_pfp/000_pfp_introduction/README.md) |
| PFP curriculum | [`004_oepfp/curriculum`](education/documentation/004_oepfp/curriculum/README.md) |
| Lean 4 index | [`lean4/readme.md`](lean4/readme.md) |
| Plans | [`product_planning_office/plans`](product_planning_office/plans) |
| Licence | [`LICENSING.md`](LICENSING.md) |

`quickstart.py` uses only the Python standard library (`fractions`, `hashlib`).
The how-to-play notebooks use `educational_governor.py` in that same folder.
That governor is a local teaching model. It is not the native host.

The package note is
[`pfp/README.md`](pfp/README.md).
It is not the newcomer entry. Use the doors above.

## The scoring rule

The host scores a candidate by weighted L1 obstruction mass on the declared
carrier:

$$\|\Phi_1\|_{1,\omega} = \sum_{e \in E} \omega_e\,\big|(\delta c_0)(e) - W_E(e)\big|.$$

The stated rule admits a move when that mass does not increase, and a finished
admitted run is mass zero. A typed refusal is the other terminal. For nonnegative weights, zero L1 mass
means that every positively weighted
coordinate has zero residual. L2 norms also prevent cancellation between
coordinates; the norm definition alone establishes no model-performance
advantage. Whether a language model concentrates on a sparse landing remains
an empirical question.

Formal developments live under [`lean4/`](lean4/) and under the paper packages
in
[`015_pfp`](atlas/coda_atlas/F004_papers/015_pfp/README.md).

## Run a bounded session

From the repository root, after `py -3.12 -m pip install -e ".[web]"`:

```powershell
py -3.12 quickstart.py --test
symbol-game search-gauge --input-file pfp/fixtures/gauge_odd_triangle_input.yaml
symbol-game serve --port 8765
symbol-game demo list
```

`search-gauge` streams finite signed-graph gauge candidates from a YAML packet.
`serve` starts the local FastAPI workbench. The optional `web` extra installs
FastAPI and uvicorn. `symbol-game demo list` prints the installed offline
MSS-N catalog. The same console entry point is
`pfp.entrypoints.cli.symbol_game`. A second script,
`level-engine`, is registered in `pyproject.toml`.

`pixi.toml` records tasks for pytest, `cargo check`, and `lake-build-core`
(`lake --dir lean4 build`). `lake-build` and `build-lake` depend on
`lake-build-core`. On Windows, a long checkout path can exceed Lean's path
limit. Run that build from a short copy of `lean4/` when the tool reports a
path error.

Python test, lint and format tasks now require one to three explicit
repository-relative `.py` files; test tasks also accept pytest node IDs
on those files. Select the `dev` environment, for example
`pixi run -e dev test pfp/tests/protocol/test_genesis_levels_cross_references.py`.
Generic `check` performs scoped lint; Cargo and Lean builds remain separate,
explicit tasks.

## Repository map

`main` has no top-level `research/` directory, no top-level `engine/`
directory, and no top-level `knowledge/` directory. The MUB6 knowledge notes
are `atlas/coda_atlas/F004_papers/010_mub6/artifacts/knowledge/`.
The live homes are below.

### Symbol Game and native math

| Path | Role |
| --- | --- |
| `pfp/` | Python Symbol Game package, fixtures, stages, and the `symbol-game` CLI |
| `engine/crates_rs/` | Rust workspace: symbol-game runtime, solvers, homology, functional calculus, certifiers, and related crates |
| `lean4/` | Lean 4 library for the tower, packets, and level developments |
| `adversary/infrastructure/providers/` | Model-provider adapters |
| `education/documentation/004_oepfp/` | Proposal Fidelity Protocol and Symbol Game documentation and how-to-play |

### Education strands

Each row is a directory under
`education/documentation/`. The title is the strand README heading.

| Strand | Subject |
| --- | --- |
| `000_oepregen` | What a language model does with an empty mark |
| `001_oegen` | Genesis foundational primitives |
| `002_oesn` | S(n) presentations and finite examples |
| `003_oemssn` | Minimal Symbol System specification atlas |
| `004_oepfp` | Proposal Fidelity Protocol and the Symbol Game |
| `005_oegenong` | Strand index under that folder name |
| `006_oewdp` | Witnessed Difference Programme |
| `007_oelggr` | Local Green, Global Red |
| `008_oeop` | Engine Operads (formerly workflows, agents, and skills) |
| `009_oeeis` | Epistemic immune system |
| `010_oepciv` | Prompt civilization |
| `011_oeadversary` | Adversary swarm design index |
| `012_oecogops` | Cognitive operations |
| `013_oegov` | Governance curriculum |
| `018_oeos` | Operating system |
| `019_oeops` | Operations, CI, and the skill operad |
| `099_project_sentinel` | Project Sentinel |
| `014_normal_forms` | Normal forms |

`education/` holds the documentation, teaching scripts and
`education_app/`. The runnable PFP package is `pfp/`; its offline
examples and tests are under that owner. Genesis, S(n), and MSS-N are separate
strands. Do not treat their numbering as one pipeline.
The retired education strand directory is already gone. The live stage is `adversary/stage`.

### Atlas, papers, and plans

| Path | Role |
| --- | --- |
| `atlas/coda_atlas/` | CODA atlas. Floors on disk include `F000_finite`, `F001_quantum`, `F002_continuum`, `F003_engine`, and `F004_papers` |
| `research_papers/` | Paper preflight, edition, and review tooling |
| `library/` | CODA library ingest and search |
| `product_planning_office/` | Planning office. Epic plans are under `plans/` |

Paper prose for the Symbol Game is under
[`015_pfp`](atlas/coda_atlas/F004_papers/015_pfp/README.md).
`research_papers` is the tooling package for editing and checking
papers. It is not a second copy of that curriculum.

### Engine packages

| Path | Role |
| --- | --- |
| `adversary/` | Adversary swarm package |
| `governance/` | Councils, contracts, and governance workflows |
| `operations/` | Operations coordination, evidence, and CLIs |
| `operating_system/` | Operating-system package |
| `adversary/stage/` | Adversary stage, the generic swarm runtime |
| `eis/` | Epistemic immune system |
| `cognitive_operations/` | Cognitive operations |
| `pciv/` | Prompt civilization |
| `operads/` | Workflow, agent, and skill package |
| `applications/` | Application front ends, including WDP products |
| `atlas/coda_atlas/F004_papers/006_finite_qm/` | Finite QM paper package |
| `atlas/coda_atlas/F004_papers/010_mub6/` | MUB6 paper package; knowledge notes are `artifacts/knowledge/` |
| `lean4/research_programs/mub6/` | Lean 4 MUB6 development |
| `core_simplex_autop/` | Simplex autop grammar and examples |
| `core_simplex_cache/` | SmplCache diagnostic engine |
| `web_dashboard/` | Dashboard templates |

### Tests, records, and custody

| Path | Role |
| --- | --- |
| `tests/`, `tests_e2e/` | Python tests at the repository root |
| `scripts/`, `tools/` | Maintenance scripts |
| `manifests/`, `artifacts/`, `runs/` | Root manifests, artifact receipts, and run records |
| `product_planning_office/receipts/` | Planning-office receipts |
| `_ic/` | Intelligence-community custody trees (`odni`, `nsa`, `nro`, and the other agency folders on disk) |
| `_ooutwire/` | Ooutwire textbook and product backlog |
| `TEST_INFRA.md`, `TEST_READY.md` | Test-infrastructure note and a dated e2e manifest |

Package tests also live inside each package. A green line in `TEST_READY.md`
is that file's recorded run. It is not a live census of `main`.

## Other root documents

| File | What it is |
| --- | --- |
| `LICENSING.md`, `LICENSE`, `NOTICE` | Licence terms |
| `pyproject.toml`, `uv.lock`, `pixi.toml` | Python package, lockfile, and pixi environments |

## Checks

These commands are the entry points. This README does not record their latest
result.

```powershell
py -3.12 -m pytest pfp/tests -q
cargo check --manifest-path engine/crates_rs/Cargo.toml
lake --dir lean4 build
```

Run a named test file when you are changing one module. The operations
republication checklist is
`py -3.12 -m operations.use_cases.cicd.republication_checklist_gate`.

## Licence

Code is under the PolyForm Noncommercial License 1.0.0 (`LICENSE`): personal,
research, educational, and other noncommercial use. Commercial use needs a
separate licence. Contact Jeremy H. Carroll via
[github.com/dbccpage](https://github.com/dbccpage).

Paper text and figures are CC BY 4.0. A paper package's own `LICENSE` files
govern that package's current deposited version. Details, including which
packages still carry an Apache-2.0 code grant, are in `LICENSING.md`.

`pyproject.toml` and `pixi.toml` record `PolyForm-Noncommercial-1.0.0`.
The grant for code in this repository is `LICENSE`.
