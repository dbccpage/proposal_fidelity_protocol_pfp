"""The Python half of compile-time packet contracts, as close as Python gets.

The Rust crate's `build.rs` generates an exhaustive destructure per contracted
type, so a field added, removed or renamed without amending its contract fails
the build. Python has no compile step, so this test is the enforcement point.

That is a **weaker guarantee** and is stated as one: a build failure stops every
consumer, while a test failure stops only whoever runs the tests. It is still
the difference between a contract that binds and a contract that describes.

The gate also refuses to be vacuous. If the contract directory disappears, or
no contract declares a Python structure, the tests fail rather than silently
passing over an empty set -- a gate that enforces nothing while reporting green
is worse than no gate.
"""

from __future__ import annotations

import dataclasses
import enum
import importlib
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

_GOV_CONTRACTS = Path(__file__).resolve().parents[2] / "omega_engine_governance" / "contracts"
CONTRACTS = (
    _GOV_CONTRACTS / "contracts_pfp"
    if (_GOV_CONTRACTS / "contracts_pfp").is_dir()
    else _GOV_CONTRACTS / "contracts_packets" / "symbol_game"
)


def python_contracts() -> list[dict]:
    assert CONTRACTS.is_dir(), (
        f"governance packet contracts not found at {CONTRACTS}; enforcing "
        "nothing is worse than not having the mechanism"
    )
    found = []
    for path in sorted(CONTRACTS.glob("*.contract.yaml")):
        contract = yaml.safe_load(path.read_text(encoding="utf-8"))
        structure = (contract or {}).get("structure") or {}
        if structure.get("language") == "python":
            found.append({"path": path, "contract": contract, "structure": structure})
    return found


CASES = python_contracts()
IDS = [c["structure"]["python_type"] for c in CASES]


def test_the_gate_is_not_vacuous() -> None:
    # A parameterised suite over an empty list reports green while checking
    # nothing. Pin the fact that contracts were actually found.
    assert CASES, (
        f"no contract under {CONTRACTS} declares a Python structure; this "
        "suite would pass while enforcing nothing"
    )


def resolve(structure: dict):
    module = importlib.import_module(structure["python_module"])
    name = structure["python_type"]
    assert hasattr(module, name), (
        f"contract names {structure['python_module']}.{name}, which does not exist"
    )
    return getattr(module, name)


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_the_declared_shape_is_the_real_shape(case: dict) -> None:
    structure = case["structure"]
    urn = case["contract"]["contract_id"]
    subject = resolve(structure)

    if structure["form"] == "dataclass":
        assert dataclasses.is_dataclass(subject), f"{urn}: not a dataclass"
        declared = [field["name"] for field in structure["fields"]]
        actual = [f.name for f in dataclasses.fields(subject)]
        # Order matters as well as membership: these are positional
        # constructors, so a reordering silently changes every call site.
        assert actual == declared, (
            f"{urn}: {structure['python_type']} fields are {actual}, contract "
            f"declares {declared}. Amend the contract, or the type."
        )
    elif structure["form"] == "enum":
        assert issubclass(subject, enum.Enum), f"{urn}: not an Enum"
        declared = list(structure["variants"])
        actual = [member.name for member in subject]
        assert actual == declared, (
            f"{urn}: {structure['python_type']} members are {actual}, contract "
            f"declares {declared}."
        )
    else:
        pytest.fail(f"{urn}: unknown form {structure['form']!r}")


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_every_contract_declares_its_authority_ceiling(case: dict) -> None:
    # A packet contract that forgot to say AuthorityEffect: None is a contract
    # a reader could mistake for a licence.
    descriptor = case["contract"].get("descriptor") or {}
    assert descriptor.get("authority_effect") is None or descriptor.get(
        "authority_effect"
    ) in (None, "None"), f"{case['contract']['contract_id']} claims authority"


def test_no_two_contracts_claim_the_same_python_type() -> None:
    seen: dict[str, str] = {}
    for case in CASES:
        key = f"{case['structure']['python_module']}.{case['structure']['python_type']}"
        previous = seen.get(key)
        assert previous is None, f"{key} is claimed by {previous} and {case['path'].name}"
        seen[key] = case["path"].name
