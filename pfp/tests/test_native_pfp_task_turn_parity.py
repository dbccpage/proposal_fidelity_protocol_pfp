"""One shared native/Python string-role profile; no model or native build required."""
import json
from pathlib import Path

from omega_engine_pfp.infrastructure.task_turn import prepare_task_turn


def test_native_string_role_vectors_match_current_python_backend():
    root = Path(__file__).resolve().parents[2]
    source = root / "omega_engine/crates_rs/tests/omega_symbol_game_runtime/fixtures/pfp_task_turn_v1.json"
    for vector in json.loads(source.read_text(encoding="utf-8")):
        prepared = prepare_task_turn(
            system=vector["system"], user=vector["user"], task_id=vector["task_id"],
            attempt_id=vector["attempt_id"], context=vector["context"],
            checker_id="woland-seat-string-v1",
        )
        assert prepared.binding["input_sha256"] == vector["input_sha256"]


def test_public_legacy_routed_executor_and_subclass_send_nothing():
    from omega_engine_pfp.infrastructure.openrouter_seat_gateway import RoutedSeatExecutor, SeatTurnRefused
    import pytest

    class InheritedExecutor(RoutedSeatExecutor):
        pass

    for cls in (RoutedSeatExecutor, InheritedExecutor):
        executor = object.__new__(cls)
        assert executor.execute(None).unwrap_err().code == "LEGACY_SEAT_TRANSPORT_RETIRED"
        with pytest.raises(SeatTurnRefused) as failure:
            executor(None)
        assert failure.value.refusal.code == "LEGACY_SEAT_TRANSPORT_RETIRED"
