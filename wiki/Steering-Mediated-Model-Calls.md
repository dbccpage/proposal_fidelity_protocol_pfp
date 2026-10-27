# Steering: mediated model calls

Every steering technique on these pages assumes that model calls go through one
place where prompts are bound, replies are kept and checks are applied. The
source project enforced that structurally: a run refuses any model transport
that does not speak the PFP exchange protocol, and a static scan forbids
production modules from importing network-capable provider code directly.

## What the source did

Two layers, each with a negative control:

1. **Runtime.** Building a run, or the service behind it, refuses any seat
   transport that is not defined by the PFP package with the expected protocol
   version (`LLM_PROTOCOL_UNMEDIATED`). Older live executors that produced
   machine blocks directly are retired explicitly, even when they claim the
   protocol. A scripted transport is accepted for tests without executing.
2. **Static.** A scan parses every production module and refuses imports of
   network-capable provider code outside the recorded exceptions, and it forbids
   the old import cycle between the swarm and the game packages.

Related rules from the same tests: a public send consumes a freshly admitted
instruction through an accounted PFP call, a changed dispatch identity is
refused before sending, and a held anti-skill screen prevents the provider call
altogether. Each turn rechecks admission without resetting the shared allowance.

## Replicate it here

The runtime check lives in `ops/adversary/runtime.py`, which is not runnable as
a whole yet. The static half is easy to reproduce for your own code with the
standard library. This scan lists modules under a folder that import a network
client directly:

```python
import ast, pathlib

NETWORK = {"requests", "httpx", "urllib.request", "aiohttp", "openai", "anthropic"}
for path in pathlib.Path("pfp_lab").rglob("*.py"):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        names = ([a.name for a in node.names] if isinstance(node, ast.Import)
                 else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
        hits = [n for n in names if n.split(".")[0] in {m.split(".")[0] for m in NETWORK}]
        if hits:
            print(path, hits)
```

Run on `pfp_lab` it prints nothing (checked): the Lab makes no model or network
calls. The repository's own architecture checks are in
`pfp/infrastructure/architecture_fitness.py`, and the
[domain purity scan](Test-Domain-Purity-Scan.md) demo runs a similar AST scan
for disk I/O.

## How it relates to PFP, EIS and PCIV

- **PFP.** The exchange is the only door. Without it, prompt-reply binding,
  byte ceilings and strict decoding can all be bypassed by a side channel.
- **EIS.** Instruction admission and anti-skill screens run at the same door,
  before any provider sees the prompt.
- **PCIV.** Call records in a [prompt family](Steering-Prompt-Families.md) are
  complete only if every call went through the exchange.

## Where the code lives

`ops/adversary/runtime.py`, `ops/adversary/infrastructure/researcher/symbol_game_dispatch.py`,
`ops/adversary/infrastructure/oewas_instruction_ingress.py` and
`pfp/infrastructure/seat_transport/`.
