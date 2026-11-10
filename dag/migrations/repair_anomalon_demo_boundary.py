"""Apply the narrowly scoped post-migration import-boundary repair."""
from pathlib import Path

root = Path(r'C:\Users\a343o\source\repos\anomalon').resolve()
path = root / 'omega_engine_pfp/infrastructure/pilot_runners/challenge_host_control.py'
assert path.resolve().is_relative_to(root)
text = path.read_text(encoding='utf-8')
old = '''from omega_engine_pfp.infrastructure.challenge_execution import isolated
from omega_engine_pfp.infrastructure.challenge_live import choose_case
'''
new = '''

def isolated(request: dict, timeout: int) -> dict:
    """Load the relocated-corpus consumer only when this demo executes."""
    from omega_engine_pfp.infrastructure.challenge_execution import isolated as execute

    return execute(request, timeout=timeout)


def choose_case(challenge: str, split: str, ordinal: int) -> dict:
    from omega_engine_pfp.infrastructure.challenge_live import choose_case as choose

    return choose(challenge, split, ordinal)
'''
if old not in text:
    raise RuntimeError('Source precondition changed; inspect before applying')
text = text.replace(old, new, 1)
needle = '    except (ValueError, IndexError, KeyError, OSError) as exc:\n'
replacement = '''    except ModuleNotFoundError as exc:
        missing = exc.name or ""
        if missing != "omega_engine_woland.tests.pilots" and not missing.startswith(
            "omega_engine_woland.tests.pilots."
        ):
            raise
        outcome = dict(
            status="REFUSED",
            reason=(
                "PILOT_CORPUS_RELOCATED: Demo 004 requires the pilot corpus moved to "
                "https://github.com/dbccpage/proposal_fidelity_protocol_pfp "
                "under pilots/anomalon_woland."
            ),
        )
        observed = dict(execution_mode="NO_LLM", provider_calls=0, result=outcome)
''' + needle
if needle not in text:
    raise RuntimeError('Exception boundary changed')
path.write_text(text.replace(needle, replacement, 1), encoding='utf-8', newline='\n')

target = root / 'omega_engine_pfp/tests/test_pilot_corpus_relocation_boundary.py'
assert target.resolve().is_relative_to(root)
if target.exists():
    raise RuntimeError('New regression-test path already exists')
target.write_text('''"""Moved pilot fixtures must not prevent unrelated PFP composition."""
import json

import pytest

from omega_engine_pfp.domain.stages.demos import DemoSpec
from omega_engine_pfp.entrypoints.composition_root import (
    build_pfp_controller,
    create_default_demo_runner,
)
from omega_engine_pfp.infrastructure.pilot_runners import challenge_host_control


def test_default_controller_and_unknown_demo_work_without_pilot_corpus():
    controller = build_pfp_controller()
    assert controller.demo_runner is not None
    result = create_default_demo_runner().run_demo(
        DemoSpec(id="unregistered-relocation-control", title="Unknown", seed="fixture")
    )
    assert result.all_passed is False
    assert result.terminal_status == "Refused"


def test_moved_demo_refuses_without_dispatch_or_false_success(monkeypatch):
    def absent(*args):
        raise ModuleNotFoundError(
            "synthetic missing relocated corpus", name="omega_engine_woland.tests.pilots"
        )

    def forbidden(*args, **kwargs):
        pytest.fail("Relocated corpus must not dispatch a worker")

    monkeypatch.setattr(challenge_host_control, "choose_case", absent)
    monkeypatch.setattr(challenge_host_control, "isolated", forbidden)
    result = create_default_demo_runner().run_demo(
        DemoSpec(id="demo_004", title="Moved finite control", seed="fixture")
    )
    assert result.all_passed is False and result.terminal_status == "REFUSED"
    observed = json.loads(result.checks[0].observed)
    assert observed["provider_calls"] == 0
    assert "PILOT_CORPUS_RELOCATED" in observed["result"]["reason"]
    assert result.authority_effect == "None"


def test_unrelated_missing_dependency_is_not_mislabeled_as_relocation(monkeypatch):
    def unrelated(*args):
        raise ModuleNotFoundError("synthetic dependency defect", name="other_dependency")

    monkeypatch.setattr(challenge_host_control, "choose_case", unrelated)
    with pytest.raises(ModuleNotFoundError, match="dependency defect"):
        challenge_host_control.run_demo_004(
            DemoSpec(id="demo_004", title="Dependency control", seed="fixture")
        )
''', encoding='utf-8', newline='\n')
print('Updated challenge import boundary and added three regression tests.')
