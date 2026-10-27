# A seat blocked by PROVIDER_HTTP_400 is followed by native gates that do not all pass.

After PROVIDER_HTTP_400, treat that seat's output as absent and do not cite it as a basis. Native gates will likely fail, so report the residual failure code and keep the task open instead of claiming verification.

Seats: scope_guard, scar_chronicler, adversary. Admitted by host replay of recorded runs; guidance only, not a gate.
