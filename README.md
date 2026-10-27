# Proposal Fidelity Protocol (PFP)

AuthorityEffect: None.

The Proposal Fidelity Protocol keeps three things apart that are easy to blur
together when a model, a person or a program suggests something:

1. **the proposal**, which is only a candidate;
2. **the check** of a declared property of that candidate, done by something
   other than the proposer; and
3. **the decision** about what the checked candidate may be used for.

A proposal that passes a check gains no authority beyond what the check
covered. A proposal that fails is refused with a typed reason, and the refusal
is kept as evidence. Every run is sealed into a receipt that anyone can replay.
PFP was historically called **The Symbol Game**, and that name still appears in
older papers and code.

PFP is research software and work in progress. A passing test suite is not a
theorem, and a receipt records only that declared code ran. The papers mark
which results are proved, which are finite checks, and which are open.

**Documentation:** the [project wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki)
is the place to start. [Getting started](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Getting-Started)
explains the idea in plain language, and
[Core concepts](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Core-Concepts)
covers packets, obstruction, retraction and receipts.

## Repository layout

| Folder | What is in it |
| --- | --- |
| [`pfp_lab/`](pfp_lab/README.md) | PFP Lab: run PFP scenarios, admit or refuse each proposal, and verify the receipt. One Python core with a command line, a web page and a Windows app |
| [`csharp/`](csharp/README.md) | The Windows app for PFP Lab (WPF), which talks JSON-RPC to the Python core |
| [`contracts/`](contracts/) | JSON schemas for PFP Lab scenarios and receipts |
| [`demos/`](demos/) | Small offline demos, each with its own README and tests: exact LP certificates, Hodge decomposition, clique homology, XOR cycle obstructions, receipt invariants, replay refusal and more. The [test catalog](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Test-Catalog) has a page for each |
| [`code/rust/`](code/rust/) | A Cargo workspace with the native `pfp` and `pfp_runtime` crates and the engine crates they depend on |
| [`pfp/`](pfp/README.md) | The core Python package: packets, evaluators, retraction, receipts and replay |
| [`eis/`](eis/) | Epistemic Immune System: antibodies, screening and custody of rejected proposals |
| [`operads/`](operads/) | Typed composition of capabilities, workflows and skills |
| [`pciv/`](pciv/) | Prompt Civilization: prompt lineage and evolution with recorded ancestry |
| [`ops/`](ops/README.md) | Operations, governance and supporting infrastructure |
| [`papers/`](papers/README.md) | The paper collection, from Paper 000 (introduction) onward. Each deposited paper carries its manuscript, claim ledger, code and checksums |
| [`education/`](education/) | Teaching material for PFP, operads, the immune system and prompt civilization |
| [`governance/`](governance/README.md) | The checker that holds every governed source to the [`SCORING.md`](SCORING.md) acceptance floor |
| [`wiki/`](wiki/) | The source of the GitHub wiki, published with `wiki/publish_wiki.py` |
| [`docs/`](docs/) | Plans and governance notes |

`pfp/`, `eis/`, `operads/`, `pciv/`, `ops/`, `papers/` and `education/` were
brought over from an earlier repository. Some imports, paths and document links
there still use older names and are being renamed gradually, so a link inside
an imported document may point to a path that does not exist here.

## Getting started

You need Python 3.12 or newer. From the repository root:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
```

On Linux or macOS, use `.venv/bin/python` in place of `.venv\Scripts\python`.

Then try PFP Lab:

```powershell
pfp-lab packs
pfp-lab run --pack paper-005-worked-session --receipt receipt.json
pfp-lab verify receipt.json
pfp-lab-web
```

`pfp-lab-web` serves the web page at <http://127.0.0.1:8765>. The scenario
format, exit codes and interfaces are in [`pfp_lab/README.md`](pfp_lab/README.md).

## Running the tests

| What | Command |
| --- | --- |
| PFP Lab and the governance tools | `python -m pytest` |
| Types, lint and import contracts | `mypy`, `ruff check .`, `lint-imports` |
| One demo | `python -m pytest demos/yardstick -q` (each demo README gives its own command) |
| The Windows app | `dotnet run --project csharp/PfpLab.Tests` |
| The Rust crates | `cargo test -p pfp -p pfp_runtime`, run inside `code/rust/` |

In the Rust workspace every library compiles, but six test targets in the
engine crates do not compile yet; test `pfp` and `pfp_runtime` by name as above.

## Quality gate and the governance checker

[`SCORING.md`](SCORING.md) is the code-scoring rubric. Each source gets a
capability level (L1 to L5) and an engineering grade (E to A+), where the grade
is the weakest of five gates: provenance and claim mapping, semantic
correctness, failure behaviour, verification adequacy, and structure.

The repository accepts a runtime source only with a completed score at **L4D
or better**, recorded in a `<stem>.contract.score.json` file next to the source
and bound to the SHA-256 of its exact bytes. Tests need L2D or better. Sources
imported from the earlier repository are grandfathered by
[`governance/baseline.json`](governance/baseline.json) while their bytes are
unchanged; edit one and it needs a score. Run the checker before you commit:

```powershell
python -m governance.tools.checker check
python -m governance.tools.checker check --changed-since origin/main
python -m governance.tools.checker explain path/to/file.py
```

[`governance/README.md`](governance/README.md) explains how to gather evidence
and record a score for a changed file.

## The wiki

The wiki is written in [`wiki/`](wiki/) and changed through pull requests like
any other file. After a change is merged, publish it with:

```powershell
python wiki/publish_wiki.py --dry-run
python wiki/publish_wiki.py
```

The script clones the GitHub wiki, replaces its pages with the Markdown files in
`wiki/`, rewrites relative `Page.md` links into wiki links, and pushes.

## Contributing and licence

See [Contributing](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Contributing)
on the wiki. The repository is licensed under the Apache License 2.0 ([`LICENSE`](LICENSE));
some papers carry their own licence files.
