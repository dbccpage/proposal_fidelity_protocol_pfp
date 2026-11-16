# Funnel survivor replay

Tier 2 lists favorable candidates that lack a supported replay in
`withheld_without_replay`. Tier 3 accepts a survivor with a replayable
`IntegerList → Integer` sum operation. It sends the exact operation and four
integer lists to the native `pfp_operad run` checker and requires one verified
result bearing that operation's ID. The request, outcome, proposal, adopted
genome, and Tier 2 receipt are retained together as canonical JSON.

The replay JSON's SHA-256 appears in the generated Lean theorem name and
statement. Lean checks that summing the same four lists gives `[6, 9, -10, 0]`.
The packet carries that source, the observed axiom report, and the replay JSON
and digest. This is a finite operation check. Atlas and DAG fields are empty
because no published claim has been registered for the individual replays.
A packet has AuthorityEffect None.

The pinned Lean compiler runs with closed stdin, a fresh temporary working
directory, a restricted environment, and a timeout. The runner accepts exact
repository fixtures and internally generated arithmetic. Arbitrary candidate
source is refused before subprocess launch. A missing compiler, failed proof,
or missing or inadmissible axiom report yields no verified packet.
