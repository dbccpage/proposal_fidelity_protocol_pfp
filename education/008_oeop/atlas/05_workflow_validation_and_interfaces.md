# Workflow Validation and Interfaces

## What the validator does

The workflow handler validates node and edge references, optionally checks colour
compatibility, detects cycles by depth-first search, and computes topological stages
with Kahn’s algorithm.

```text
node/edge shape
  -> endpoint checks
  -> optional colour checks
  -> cycle refusal
  -> topological stage plan
```

This is graph validation and planning. It does not execute operations, schedule
agents, recover from partial effects, or prove that a workflow can complete.

## Known graph gaps

- Duplicate node identifiers overwrite one another.
- Duplicate edges can distort indegrees.
- Referenced operation identifiers are not resolved against a catalog.
- DAG acyclicity does not detect dead tasks, unreachable completion, livelock in an
  extended state machine, or resource/effect conflicts.

Workflow-net soundness research shows why structural acyclicity and behavioral
completion are different questions; see the formal study of
[workflow-net soundness complexity](https://arxiv.org/abs/2201.05588). OEWAS should
borrow the distinction, not claim Petri-net soundness without implementing it.

## Controller and HTTP surface

`OewasApiV3` maps application results to transport DTOs. The FastAPI surface is
narrower than the historical production document. The implemented verification
route is catalog-specific:

```text
/catalogs/{id}:verify
```

The term-compilation route returns the license-witness refusal. Health is liveness,
not readiness, storage integrity, or dependency health.

## Command-line surfaces

The primary CLI covers only part of the application API, and the operad CLI exposes
a separate path. With an in-memory default, separate CLI processes cannot share a
catalog. Operational documentation must distinguish a single-process demonstration
from durable deployment.

## Port consistency

The application defines clocks, estate sources, parsers, operad services, journals,
projections, signing envelopes, and units of work. Multiple result/error families
and port/handler capability mismatches increase adapter ambiguity. Frozen DTOs that
contain mutable dictionaries also weaken the expectation of immutable messages.

Recommended consolidation:

1. one typed result/error algebra at application boundaries;
2. one canonical unit-of-work protocol containing every method handlers use;
3. immutable mappings or defensive copies in DTOs;
4. explicit liveness, readiness, and integrity probes;
5. a catalog-resolving workflow validator before any execution proposal.

## Agent-computer interface lesson

Tool-using agent systems are sensitive to the design of the action/observation
interface. [SWE-agent](https://arxiv.org/abs/2405.15793) treats the interface itself
as an engineering object, while [AgentBench](https://arxiv.org/abs/2308.03688)
evaluates agents in interactive environments. For OEWAS this translates to typed
commands, bounded observations, replayable fixtures, and explicit failure states.
It does not justify autonomous execution or promotion.
