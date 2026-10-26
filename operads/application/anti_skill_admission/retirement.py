"""Typed refusal for retired Python prompt-civilization entry points."""

from omega_engine_operations.domain.rop.result import Err, Refusal

RUNTIME_RETIRED_CODE = "PROMPT_CIVILIZATION_RUNTIME_RETIRED"
RUNTIME_RETIRED_MESSAGE = (
    "Legacy Python prompt_civilization runtime is retired in favor of "
    "omega_engine/crates_rs/omega_prompt_civilization"
)


def runtime_retired(locus: str) -> Err[Refusal]:
    """A diagnostic refusal; it grants no authority or admission."""
    return Err(
        Refusal(code=RUNTIME_RETIRED_CODE, message=RUNTIME_RETIRED_MESSAGE, locus=locus)
    )
