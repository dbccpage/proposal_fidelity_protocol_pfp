# Proposal Fidelity Protocol (PFP)

**Verification, typed composition and prompt evolution for LLMs and agent systems.**

PFP brings together a proposal/checking protocol, an operad system for composing
capabilities, an Epistemic Immune System for screening failure detectors, Prompt
Civilization for prompt lineage and evolution, and an adversarial execution layer.
The repository also contains exact mathematical checkers, native Rust kernels,
Lean 4 developments, interactive tools, research papers and teaching material.

You can specify what a model must produce, which operations may compose, what a
rewrite must preserve, how an independent host will check the result, how much
an experiment may spend, and which evidence the next attempt may reuse.

**Start here:** [System guides](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki)
· [Workflow chooser](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflows)
· [Run a local example](#try-a-local-example)
· [Mathematical capabilities](#mathematics-and-formal-verification)
· [Papers](papers/README.md)

## What the systems do

| System | Capabilities in this repository | Explore |
| --- | --- | --- |
| **PFP protocol and runtime** | Prepare typed prompts and replies; bind a proposal to its task, input and attempt; apply independent checkers; run bounded stages and research loops; retain actual replies, refusals and replay evidence. | [Runtime layers](pfp/) · [Prompt assembly](pfp/use_cases/pfp_prompt.py) · [Proposal checking](pfp/use_cases/pfp_proposal.py) · [Bounded loops](pfp/use_cases/pfp_derivation_loops.py) |
| **Operads and capability composition** | Describe operations with ordered typed ports; pin sources, schemas and validators; compile compatible operation occurrences into candidate workflows; build skill catalogues and check tool/effect ceilings. | [Operads](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Operads) · [Workflow compiler](operads/application/typed_workflow_compiler.py) · [Full port contracts](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Operads-Typed-Workflows) |
| **Epistemic Immune System (EIS)** | Match known failure patterns; require an independent host damage signal before immune suppression; screen candidate detectors against clean examples; track admission, regulation and retirement of guards. | [EIS guide](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/EIS) · [Two-signal gate](eis/domain/danger_gate.py) · [Negative selection](eis/domain/thymus.py) |
| **Prompt Civilization (PCIV)** | Track prompt genomes and execution lineage; mutate around protected spans; compare fitness with exact Pareto selection; evaluate experimental changes on paired selection/confirmation data; retain custody and causal-taint records. | [PCIV guide](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/PCIV) · [Mutation](pciv/use_cases/forge.py) · [Fitness](pciv/use_cases/fitness.py) · [Experimental selection](pciv/use_cases/research_selection.py) |
| **Adversarial execution and global checking** | Coordinate role panels, provider turns, shared accounting and retained evidence; compare local checks with global requirements through Local Green, Global Red (LGGR) diagnostics. | [Execution sources](ops/adversary/) · [Role-panel guide](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Steering#running-the-local-swarm) · [LGGR adapter](ops/adversary/infrastructure/lggr_adapter.py) |
| **Representations and checked rewriting** | Work with prompt/operation trees, S(n), MSS-N and PFP packets; declare a protected query and decoder; check representation changes, witnesses, finite repairs and typed refusals. | [Rewriting guides](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Rewriting) · [Packet grammar](pfp/domain/tower/grammar.py) · [WDP/DDC](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Rewriting-WDP-DDC) |
| **Proposal-channel experiments** | Study prompt geometry, bounded context profiles, token masking, attention interventions and activation steering, with host checking after the intervention. | [Steering catalogue](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Steering) · [Local model adapters](pfp/infrastructure/adapters/decode_controls/) |
| **Product tools and interfaces** | Inspect prompt/reply risks, seal and replay packets, inspect capability catalogues and export MCP tool definitions; run exact graph scenarios through a CLI, local web interface or Windows application. | [Native CLI](code/rust/pfp_cli/README.md) · [PFP Lab](pfp_lab/README.md) · [Windows app](csharp/README.md) |

These components have separate owners and explicit integration boundaries. Their
guides identify standalone tools, reference implementations, optional native
bindings and experimental paths.

## From an individual answer to a system that retains lessons

The protocol separates **a proposal**, **a check of a declared property**, and
**a decision about using the result**. The surrounding systems make those steps
composable and reusable:

1. **Specify the task.** Keep public inputs and output contracts separate from
   host-only ground truth. Declare checkers and resource limits.
2. **Compose the work.** Name the operations, their port contracts and the
   obligations a representation change must preserve.
3. **Obtain proposals.** Use a person, model, agent panel or program as the
   proposer. Preserve what it actually returned.
4. **Check independently.** Evaluate the original task and any global
   compatibility requirements. A matching type is one check, not the whole task.
5. **Retain the evidence.** Keep successful and failed attempts, source
   identities, costs and replay records.
6. **Evaluate what should change next.** Screen failure-derived guard candidates,
   retain prompt ancestry, and compare proposed prompt or harness changes under
   declared experimental conditions.

Each workflow chooses the mechanisms it needs. For a concrete integration,
the [bounded code-repair study](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Operads-Bounded-Repair)
captures a source snapshot, checks a baseline, applies a supplied patch in a
separate working copy, checks it again, and records observations through immune
and genealogy service interfaces. Missing services remain visible in its record.

## Mathematics and formal verification

The mathematical content supports checkable witnesses and explicit failure
conditions. It includes:

- **Exact optimization and repair:** rational linear programming, primal/dual
  witnesses, Farkas certificates, potential differences and bounded cochain repair.
- **Topology and geometry:** discrete Hodge decomposition, homology and torsion,
  cellular sheaves, cup products, persistence, holonomy and finite obstructions.
- **Quantum information and mathematical physics:** commuting Pauli Hamiltonians,
  stabilizer-code certificates, Clifford constructions, contextuality,
  fermion-to-qubit mappings and finite gauge constraints.
- **Logic and synthesis:** finite proof tasks, SAT certificates, equational
  rewriting, countermodels, finite categories and bounded program constructions.

The [50 challenge packages, C011–C060](demos/certified_challenges/)
provide problem statements, witness formats, reference implementations and
checker tests. The [test catalogue](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Test-Catalog)
explains individual examples and their limitations. Two direct entry points are
[exact LP with dual certificates](demos/certified_challenges/c051_exact_lp_solver_with_duals/README.md)
and [discrete Hodge decomposition](demos/certified_challenges/c014_discrete_hodge_decomposition/CHALLENGE.md).

The [Rust workspace](code/rust/Cargo.toml) contains the native PFP runtime and
supporting kernels for algebra, certifiers, topology, quantum checks, operads,
immune mechanisms, prompt civilization, replay and policy.

The [Lean 4 kernel](lean4/README.md) covers fidelity adequacy, shadow boundaries,
lift/patch semantics, typed packet shadows and operation-tree folds. Its recorded
2026-10-27 axiom census checks **1,144 constants across nine roots** and reports
**375 non-internal theorem constants**. The source, accepted axioms, provenance
and scope of that census are retained with the kernel.

## Try a local example

### PFP Lab: proposals, repair, refusal and replay

From a checkout with Python 3.12+:

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -e .
.venv/Scripts/python -m pfp_lab.cli.main packs
.venv/Scripts/python -m pfp_lab.cli.main run --pack paper-005-worked-session --receipt first-receipt.json
.venv/Scripts/python -m pfp_lab.cli.main verify first-receipt.json
```

On Linux/macOS, replace `.venv/Scripts/python` with `.venv/bin/python`.
This runs a local scenario with supplied proposals and independent recomputation;
it buys no model response. `VALID` means the receipt replays, including any
refused steps it contains. [PFP Lab](pfp_lab/README.md) also documents the optional
web interface, JSON-RPC protocol and Windows front end.

### Native CLI: inspect a prompt/reply and retain its bytes

Download the standalone binary for Linux, macOS or Windows from the
[release page](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/releases/tag/pfp-cli-v0.1.0),
which includes `SHA256SUMS`. Then run:

```sh
pfp demo
pfp check --prompt your_prompt.md model_reply.json
pfp seal your_prompt.md model_reply.json --out packet.json
pfp replay packet.json
```

The CLI has 13 deterministic detectors for issues such as self-certification,
invented receipts, preloaded conclusions and unsupported mathematical claims.
It also inspects skill catalogues, checks role/skill compatibility and exports
catalogue tools as MCP definitions. See the [CLI command reference](code/rust/pfp_cli/README.md).

![The native CLI inspecting a release-agent prompt and JSON reply](code/rust/pfp_cli/demo/demo.gif)

### WF1–WF5: reusable LLM workflow families

| Family | Mechanism | Normal model calls |
| --- | --- | ---: |
| WF1 | One agent, basic P*, typed answer and independent task check | 1 |
| WF2 | WF1 plus all operad slots and emitted operad/DDC collection | 1 |
| WF3 | Screen and freeze mined operads before one solver response | 2 |
| WF4 | One miner, five simultaneous solvers and local/global LGGR checks | 6 |
| WF5 | A full checked PFP grammar seed rewrite before the WF4 structure | 6 |

The [standalone automated runners](pfp/workflows/README.md) are available on
`main`, with each workflow in its own named package. Follow the
[tested installation/run/replay guide](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-Running)
or the [repository runbook](docs/workflows/README.md). The migration evidence
records 201 offline tests and 27 installation checks, with an offline CI run.
The shared historical seed baseline, failed attempts and original budget
records are preserved.

Use the [workflow chooser](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflows)
to pick a family. Future task-specific recipes have their own versions,
checkers and evidence; the integer-sum examples establish that finite integration.

## Research, teaching and source map

| Area | Contents |
| --- | --- |
| [`papers/`](papers/README.md) | Research manuscripts, claim ledgers, implementations, reproduction instructions and publication records. The register distinguishes deposited packages from author-review drafts. |
| [`education/`](education/) | Learning routes for PFP, operads, EIS and Prompt Civilization, including mathematical foundations and worked exercises. |
| [`demos/`](demos/) | Offline demonstrations and certificate-checking challenges. |
| [`pilots/`](pilots/) | Retained model-experiment material and recipes; consult each pilot's runtime and data prerequisites. |
| [`pfp/`](pfp/), [`operads/`](operads/), [`eis/`](eis/), [`pciv/`](pciv/) | The protocol, composition, immune and evolution systems described above. |
| [`ops/`](ops/) | Execution, adversarial panels, provider/accounting adapters, governance and host infrastructure. |
| [`code/rust/`](code/rust/), [`lean4/`](lean4/), [`csharp/`](csharp/) | Native kernels and tools, formal developments, and the Windows application. |
| [`contracts/`](contracts/), [`governance/`](governance/README.md), [`SCORING.md`](SCORING.md) | Wire schemas, source-bound assessments and the repository acceptance policy. |
| [`wiki/`](wiki/), [`docs/`](docs/) | User guides, subsystem references, plans and validation records. |

Useful research routes include [the practitioner field manual](papers/005_pfp_practitioners_field_manual/README.md),
[local-to-global agent composition](papers/025_pfp_local_to_global_agent_composition/paper.md),
[future-faithful compression](papers/026_pfp_future_faithful_compression_and_cost/paper.md),
[proposal-channel interventions](papers/027_pfp_proposal_channels_and_internal_interventions/paper.md),
[operadic bounded repair](papers/028_pfp_operadic_composition_and_bounded_ddc_repair/paper.md)
and [evidence-bound harness evolution](papers/029_pfp_evidence_bound_harness_evolution/paper.md).

## Evidence and development

**AuthorityEffect: None.** A successful check establishes its declared property.
It does not authenticate an operator, authorize deployment or prove unrelated
claims. Pattern detection, exact certificates, formal theorems and model
performance measurements carry different evidence scopes.

The released CLI and PFP Lab have standalone entry points. Larger imported
subsystems contain a mixture of implementations, reference models, native
adapters and research integrations; their own guides state prerequisites and
remaining obligations. Historical namespace references remain in some imported
documents. A component's presence is not a claim that every subsystem installs
through one package extra or that the entire platform has one end-to-end proof.

| Check | Entry point |
| --- | --- |
| PFP Lab and governance tool tests | `python -m pytest` after installing `.[dev]` |
| A certificate challenge | Its README under `demos/certified_challenges/` |
| Native PFP runtime tests | `cargo test -p pfp -p pfp_runtime` from `code/rust/`; check crate-specific prerequisites |
| Lean kernel and axiom census | Build/audit commands in [lean4/README.md](lean4/README.md) |
| Changed-source acceptance policy | `python -m governance.tools.checker check --changed-since origin/main` |

The source assessment floor is L4D for runtime code and L2D for tests, with exact
byte bindings and explicit imported-source baselines. See
[governance/README.md](governance/README.md) for the rubric, evidence records and
assessment process.

For contributions, see the [contributing guide](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Contributing).
Licensing information is in the root [LICENSE](LICENSE), component-specific
license files, paper packages and native workspace metadata.
