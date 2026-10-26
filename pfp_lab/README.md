# PFP Lab

AuthorityEffect: None.

PFP Lab runs Proposal Fidelity Protocol scenarios and checks their receipts.
A scenario declares a weighted constraint graph and a list of proposals
(ASSERT, CUT, VERIFY, RETRACT). The core recomputes every number itself, admits
or refuses each proposal, and seals the run into a SHA-256 receipt that anyone
can replay.

There are three front ends over one Python core:

| Front end | Start it | Notes |
| --- | --- | --- |
| Command line | `pfp-lab --help` | Scenario files in, tables or JSON receipts out |
| Web page | `pfp-lab-web`, then open <http://127.0.0.1:8765> | Loopback only unless `--allow-remote` |
| Windows app | `dotnet run --project csharp/PfpLab.Desktop` | Starts `python -m pfp_lab stdio` and talks JSON-RPC to it |

## Install

From the repository root, with Python 3.12 or newer:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
```

The Windows app finds `.venv\Scripts\python.exe` above its own folder. Set
`PFP_LAB_PYTHON` to use another interpreter.

## Try it

```powershell
pfp-lab packs
pfp-lab run --pack paper-005-worked-session --receipt receipt.json
pfp-lab verify receipt.json
```

`paper-005-worked-session` is the worked session of the Paper 005 guide. The
other packs show a section repair, every refusal the governor can give, and a
graph with two components.

## Scenario format

```json
{
  "schema": "pfp-lab.scenario.v1",
  "title": "one triangle",
  "vertices": ["a", "b", "c"],
  "edges": [{"source": "a", "target": "b", "weight": 1}],
  "moves": [
    {"move": "ASSERT", "source": "a", "target": "b", "value": "3/2"},
    {"move": "CUT", "claims": [{"source": "a", "target": "b", "value": "0"}]},
    {"move": "CUT", "section": {"a": "0", "b": "1"}},
    {"move": "VERIFY", "obligation": "ZERO_OBSTRUCTION"},
    {"move": "RETRACT", "target_step_id": "step_001", "reason": "undo"}
  ]
}
```

Rationals are strings in lowest terms (`"3"`, `"-2"`, `"3/2"`); floats,
booleans for numbers and unknown fields are refused. VERIFY obligations are
`ZERO_DEFECT`, `ZERO_OBSTRUCTION` and `EDGE_MATCH:u,v`. Limits: 12 vertices,
16 edges, weights 1 to 1000, 256 moves, 256 KiB of JSON. The full contracts
are in `contracts/schema/`.

## Interfaces

* CLI exit codes: 0 ok, 2 usage, 3 refused input, 4 search budget, 5 receipt
  not valid, 6 file error, 7 unknown pack.
* JSON-RPC methods (`pfp-lab stdio`, one message per line): `lab.version`,
  `packs.list`, `packs.get`, `scenario.run`, `receipt.verify`. Errors:
  -32602 refused input, -32001 budget, -32002 unknown pack.
* HTTP (`pfp-lab-web`): `GET /api/version`, `GET /api/packs`,
  `GET /api/packs/{id}`, `POST /api/run`, `POST /api/verify`.

## Quality gate

Every runtime source here is held to the `SCORING.md` acceptance floor (L4D or
better) by `governance/`. See `governance/README.md` for how scores are
recorded and checked, and `pfp_lab/core/PROVENANCE.md` for where the governor
came from.
