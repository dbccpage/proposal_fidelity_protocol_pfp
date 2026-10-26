# Native gate unavailable (blocked) predicts native gates still not all pass on later re-execution

If host_native_gates shows blocked NATIVE_GATE_UNAVAILABLE, do not assume a rerun will pass. Fix the native host binding or runtime artifact access first. Otherwise report native gate coverage as incomplete and never claim all-pass.

Seats: woland, hella, bezdomny. Admitted by host replay of recorded runs; guidance only, not a gate.
