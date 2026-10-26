# Quantum native migration contract

AuthorityEffect: None.

`omega_symbol_game_runtime::stabilizer` owns solving and checking. Its public
wire result is `id`, `status`, `energy` as an integer pair, `degeneracy`,
`basis` as input term IDs, `decomposition` as `id/mask/phase` rows, and
`minimizers` as assignment indices. Basis and decomposition use the deterministic
input order chosen by the native solver; alternate bases are not admitted by
this compact certificate contract. Noncommuting results carry a witnessed
input term pair. Malformed or unrepresentable cases carry a typed `UNKNOWN`
refusal. There is no Python algebra or enumeration fallback.

The domain `solve` and `check_certificate` require explicit `port=` injection.
Without it they return `NATIVE_PORT_UNBOUND`. Current educational composition roots explicitly inject the native adapter;
their compact results replace historical rich alias formats. Historical live
records remain unchanged and are not rescored as new native evidence. The installed Q40 named demo supplies `StabilizerRustAdapter`
through its infrastructure composition root, and `run_benchmark_40` accepts it
as the explicit `stabilizer=` dependency.

The adapter uses the canonical OS `RustSymbolGameHost.invoke_runtime` seam.
Every full native outcome is retained before its result is read. Q40 binds
its input cases and retained outcome array by SHA256 in its receipt, returns
the outcomes and writes them to `native_outcomes.jsonl` when an output directory
is supplied. The runtime envelope provides an action echo, not a cryptographic
request commitment; this custody does not assert an additional native request
binding. Exact checking recomputes the bounded native solve and checks each supplied
coordinate; it does not claim an independently implemented solver algorithm.
It is separate from the optional numerical dense spectrum
cross-check, which remains secondary Python evidence. No provider calls occur.

The original calculator, checker and reference tests remain byte-identical in
this directory as non-executable historical evidence. The current tests use the
native public format and exercise the declared forty cases, eight relabelled
controls, corrupted energy/basis/decomposition/minimizers, malformed JSON
proposals, noncommuting witness forgery, empty Hamiltonians and absent runtime.
They do not assert rich alias or arbitrary-precision output compatibility.
