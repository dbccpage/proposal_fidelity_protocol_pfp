---
name: state-machine-configs
description: Read, validate and transform declarative state-machine definitions.
---
# State-machine configs

Use this skill for tasks involving states, events and transitions declared in data.

## Rules

- Represent a transition as a record `{from, on, to}`. A nested map `{state: {event: target}}` is the
  same information; convert between the two without losing entries.
- Every `to` and the initial state must name a declared state. Reject unknown names with `ValueError`.
- A terminal state is a declared state with no outgoing transitions. Compute it; do not guess.
- Sort transition lists by `(from, on)` and state lists alphabetically when the format does not give an order.
- Reject duplicate `(from, on)` pairs instead of letting the last one win.
- Do not add implicit self-loops or default transitions.

## Example

`{"idle": {"start": "running"}, "running": {}}` becomes
`[{"from": "idle", "on": "start", "to": "running"}]` with terminal states `["running"]`.
