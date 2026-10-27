"""Explicit operator checker invocation for the registered DDC reuse command."""

from __future__ import annotations

import json
import re
import subprocess
from hashlib import sha256
from pathlib import Path

from operations.domain.rop.result import Err
from adversary.domain.checked_reuse import FreshReuseCheck
from adversary.domain.native_gate_check import decode_native_json
from adversary.infrastructure.native import DefaultNativeOperationPort
from adversary.use_cases.checked_ddc_reuse import (
    apply_checked_ddc_recipe,
    load_checked_reuse_registry,
    registered_reuse_roundtrip_witness,
)


def execute_reuse(parsed) -> int:
    """A registry supplies data; only the CLI operator supplies checker argv."""
    if parsed.receipt.exists() or parsed.output.exists():
        raise ValueError("REUSE_OUTPUT_EXISTS")
    command = tuple(parsed.check_command)
    if not command or not all(marker in "\n".join(command) for marker in (
            "{candidate}", "{seed}", "{premises_json}")):
        raise ValueError("REUSE_CHECK_COMMAND_BINDING_REQUIRED")
    registry = load_checked_reuse_registry(parsed.registry, parsed.registry_sha256)
    recipe = next((row for row in registry.recipes if row.recipe_id == parsed.recipe_id), None)
    if recipe is None:
        raise ValueError("UNREGISTERED_RECIPE")
    raw_premises = parsed.premises.read_bytes()
    if len(raw_premises) > 65_536:
        raise ValueError("REUSE_PREMISES_TOO_LARGE")
    premises = decode_native_json(raw_premises)
    captures = []

    def check(path: Path, seed: str, current_premises: dict):
        substitutions = {"{candidate}": str(path), "{seed}": seed,
            "{premises_json}": json.dumps(current_premises, sort_keys=True, ensure_ascii=False),
            "{contract}": recipe.source_task.contract.path if seed == recipe.source_task.seed
                          else recipe.target_task.contract.path}
        argv = []
        for argument in command:
            argv.append(re.sub(r"\{(?:candidate|seed|premises_json|contract)\}",
                lambda matched: substitutions[matched.group()], argument))
        completed = subprocess.run(argv, shell=False, check=False, capture_output=True, timeout=60)
        captures.append({"argv": argv, "exit_status": completed.returncode,
            "stdout_hex": completed.stdout.hex(), "stderr_hex": completed.stderr.hex(),
            "stdout_sha256": sha256(completed.stdout).hexdigest(),
            "stderr_sha256": sha256(completed.stderr).hexdigest(),
            "authority_effect": "None", "authenticated": False})
        if completed.returncode != 0:
            raise ValueError("REUSE_CHECKER_REFUSED")
        observed = decode_native_json(completed.stdout)
        if type(observed) is not dict or "output_sha256" in observed:
            raise ValueError("REUSE_CHECKER_OUTPUT_SHAPE")
        # The host binds actual captured bytes; the child cannot hash a reply
        # containing its own output digest or attest to its own transport.
        return FreshReuseCheck.model_validate_json(json.dumps({**observed,
            "output_sha256": sha256(completed.stdout).hexdigest()}))

    result = apply_checked_ddc_recipe(registry_path=parsed.registry,
        expected_registry_sha256=parsed.registry_sha256, recipe_id=parsed.recipe_id,
        target_seed=parsed.seed, target_premises=premises,
        target_contract_sha256=parsed.contract_sha256, output_path=parsed.output,
        source_check=check, target_check=check, native_support=DefaultNativeOperationPort())
    receipt = {"provider_calls": 0, "checker_captures": captures,
        "registry_path": str(parsed.registry.absolute()), "registry_sha256": parsed.registry_sha256,
        "authority_effect": "None"}
    if isinstance(result, Err):
        receipt.update(ok=False, refusal={"code": result.error.code, "message": result.error.message})
    else:
        receipt.update(ok=True, result=result.value.model_dump(mode="json"),
            roundtrip=registered_reuse_roundtrip_witness(registry_path=parsed.registry,
                expected_registry_sha256=parsed.registry_sha256, recipe_id=parsed.recipe_id,
                result=result.value, native_support=DefaultNativeOperationPort()))
    with parsed.receipt.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, sort_keys=True, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"ok": not isinstance(result, Err), "provider_calls": 0,
                      "receipt": str(parsed.receipt.absolute())}))
    return 1 if isinstance(result, Err) else 0
