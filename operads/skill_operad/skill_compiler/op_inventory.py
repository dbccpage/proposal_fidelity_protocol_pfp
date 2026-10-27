"""Operad v2 op inventory: skills refined into small typed ops and anti-ops, checked as a tree.

The v1 operad (``json/operad_signature.json``) registers each skill as one coarse operation.
``yaml/op_inventory.yaml`` refines a skill into ops with one output each, wired as a planar
tree, and anti-ops that guard one input slot of one op. This module loads the inventory with
typed models and checks it:

- ``OI1_SCHEMA``: the file parses into the models below.
- ``OI2_PORT``: every port is an admitted colour or a declared ``Colour.subcolour``.
- ``OI3_DUPLICATE_OP``: op and anti-op ids are unique across the inventory.
- ``OI4_WIRING``: the wiring names declared ops, and every wire matches arity and port exactly
  (checked by building the tree with ``planar.formal_compose``).
- ``OI5_REFINES``: the tree's leaves, read as base colours, are the coarse op's source colours
  in order, and its root is the coarse op's target colour.
- ``OI6_UNUSED_OP``: every declared op appears in the wiring.
- ``OI7_ANTI_OP``: an anti-op guards a declared op, at a slot it has, with that slot's port.
- ``OI8_BINDING``: a ``binding`` names a tracked file and a symbol defined in it.

``skill_term`` returns the checked tree, so a caller can walk a skill as composable ops;
``wire_term`` does the same for any wiring over a set of ops (the resolver's composites).

Usage::

    python -m operads.skill_operad.skill_compiler.op_inventory \
        --repo-root .

AuthorityEffect: None. Reads the inventory, the v1 signature and bound source files.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from operads.domain.ddc_execution.constants import (
    ADMITTED_FINITE_COLOURS,
)
from operads.skill_operad.domain.planar import (
    ArityMismatch,
    ColoredOp,
    ColorMismatch,
    Term,
    formal_compose,
    nullary,
)

SCHEMA_VERSION = "core.oewas.op_inventory.v3"
INVENTORY_PATH = Path("operads/skill_operad/yaml/op_inventory.yaml")
PRIMARY_SIGNATURE_PATH = Path("operads/skill_operad/json/operad_signature.json")
LEGACY_SIGNATURE_PATH = Path(".agents/skill_operads/operad_signature.json")
SIGNATURE_PATH = PRIMARY_SIGNATURE_PATH


class _Model(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class HostBinding(_Model):
    kind: Literal["host"] = "host"
    target: str = Field(min_length=1)


class PfpTurnBinding(_Model):
    kind: Literal["pfp_turn"] = "pfp_turn"
    role_id: str = Field(min_length=1)
    role_version: str = Field(min_length=1)


class OpSpec(_Model):
    op_id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    inputs: tuple[str, ...] = ()
    output: str
    binding: HostBinding | PfpTurnBinding | str | None = None


class AntiOpSpec(_Model):
    op_id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    guards: str
    slot: int = Field(ge=0)
    inspects: str
    refusal: str = Field(min_length=1)
    binding: str | None = None
    typed_contract_id: str | None = None


class Wire(_Model):
    op: str
    args: tuple[Union["Wire", str], ...] = ()


class SkillDecomposition(_Model):
    skill_id: str = Field(min_length=1)
    ops: tuple[OpSpec, ...] = Field(min_length=1)
    anti_ops: tuple[AntiOpSpec, ...] = ()
    wiring: Wire


class OpInventory(_Model):
    schema_version: Literal["core.oewas.op_inventory.v2", "core.oewas.op_inventory.v3"]
    subcolours: dict[str, tuple[str, ...]] = {}
    skills: tuple[SkillDecomposition, ...]


@dataclass(frozen=True)
class Finding:
    code: str
    where: str
    message: str

    def __str__(self) -> str:
        return f"{self.code} {self.where}: {self.message}"


def load_inventory(path: Path) -> OpInventory:
    return OpInventory.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def base_colour(port: str) -> str:
    return port.split(".", 1)[0]


def _port_error(port: str, subcolours: dict[str, tuple[str, ...]]) -> str | None:
    colour, _, sub = port.partition(".")
    if colour not in ADMITTED_FINITE_COLOURS:
        return f"{port!r}: {colour!r} is not an admitted colour"
    if sub and sub not in subcolours.get(colour, ()):
        return f"{port!r}: subcolour {sub!r} is not declared under {colour}"
    return None


def _colored_op(spec: OpSpec) -> ColoredOp:
    def body(*_: object) -> tuple[object, object]:
        raise NotImplementedError(f"{spec.op_id} is typed here, not executed")

    return ColoredOp(
        name=spec.op_id, source_colors=spec.inputs, target_color=spec.output, body=body
    )


def wire_term(wire: Wire | str, ops: Mapping[str, OpSpec]) -> Term:
    """Build a wiring as a planar term; raises on an unknown op or a mistyped wire."""
    if isinstance(wire, str):
        return Term(nullary(wire, None, name=f"input:{wire}"))
    if wire.op not in ops:
        raise KeyError(f"wiring names undeclared op {wire.op!r}")
    return formal_compose(_colored_op(ops[wire.op]), *(wire_term(arg, ops) for arg in wire.args))


def skill_term(skill: SkillDecomposition) -> Term:
    """Build the skill's wiring as a planar term; raises on an unknown op or a mistyped wire."""
    return wire_term(skill.wiring, {op.op_id: op for op in skill.ops})


def _leaves(node: Wire | str) -> list[str]:
    if isinstance(node, str):
        return [node]
    return [leaf for arg in node.args for leaf in _leaves(arg)]


def _wired_ops(node: Wire | str) -> set[str]:
    if isinstance(node, str):
        return set()
    return {node.op}.union(*(_wired_ops(arg) for arg in node.args))


def _symbol_defined(source: str, symbol: str) -> bool:
    scope: list[ast.stmt] = ast.parse(source).body
    for part in symbol.split("."):
        found = next(
            (
                node
                for node in scope
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and node.name == part
            ),
            None,
        )
        if found is None:
            return False
        scope = found.body
    return True


def _binding_error(repo_root: Path, binding: str) -> str | None:
    path, sep, symbol = binding.partition("::")
    if not sep or not symbol:
        return f"{binding!r} is not path::symbol"
    file = repo_root / path
    if not file.is_file():
        return f"{path} does not exist"
    if not _symbol_defined(file.read_text(encoding="utf-8"), symbol):
        return f"{symbol} is not defined in {path}"
    return None


def _coarse_ops(repo_root: Path) -> dict[str, dict]:
    sig_path = repo_root / PRIMARY_SIGNATURE_PATH
    if not sig_path.exists() and not (
        sig_path.parent.is_dir() or (repo_root / "operads/skills").is_dir()
    ):
        sig_path = repo_root / LEGACY_SIGNATURE_PATH
    data = json.loads(sig_path.read_text(encoding="utf-8"))
    return {op["skill_id"]: op for op in data["operations"]}


def check_inventory(repo_root: Path, inventory: OpInventory) -> list[Finding]:
    findings: list[Finding] = []
    coarse = _coarse_ops(repo_root)
    for colour in inventory.subcolours:
        if colour not in ADMITTED_FINITE_COLOURS:
            findings.append(Finding("OI2_PORT", "subcolours", f"{colour!r} is not admitted"))

    all_ids = [op.op_id for s in inventory.skills for op in (*s.ops, *s.anti_ops)]
    for op_id, count in sorted(Counter(all_ids).items()):
        if count > 1:
            findings.append(Finding("OI3_DUPLICATE_OP", op_id, f"declared {count} times"))

    for skill in inventory.skills:
        where = skill.skill_id
        ports = [p for op in skill.ops for p in (*op.inputs, op.output)]
        ports += [a.inspects for a in skill.anti_ops] + _leaves(skill.wiring)
        for port in dict.fromkeys(ports):
            error = _port_error(port, inventory.subcolours)
            if error:
                findings.append(Finding("OI2_PORT", where, error))

        try:
            term = skill_term(skill)
        except (KeyError, ArityMismatch, ColorMismatch) as exc:
            findings.append(Finding("OI4_WIRING", where, str(exc).strip("'\"")))
            term = None

        op = coarse.get(skill.skill_id)
        if op is None:
            findings.append(Finding("OI5_REFINES", where, "no coarse op in operad_signature.json"))
        elif term is not None:
            leaves = [base_colour(p) for p in _leaves(skill.wiring)]
            if leaves != list(op["source_colours"]):
                findings.append(Finding(
                    "OI5_REFINES", where,
                    f"tree takes {leaves}, coarse op takes {op['source_colours']}",
                ))
            if base_colour(term.color) != op["target_colour"]:
                findings.append(Finding(
                    "OI5_REFINES", where,
                    f"tree yields {term.color}, coarse op yields {op['target_colour']}",
                ))

        for unused in sorted({o.op_id for o in skill.ops} - _wired_ops(skill.wiring)):
            findings.append(Finding("OI6_UNUSED_OP", where, f"{unused} is not wired"))

        ops = {o.op_id: o for o in skill.ops}
        for anti in skill.anti_ops:
            guarded = ops.get(anti.guards)
            if guarded is None:
                findings.append(Finding("OI7_ANTI_OP", anti.op_id, f"guards unknown op {anti.guards}"))
            elif anti.slot >= len(guarded.inputs):
                findings.append(Finding(
                    "OI7_ANTI_OP", anti.op_id, f"{anti.guards} has no slot {anti.slot}"
                ))
            elif guarded.inputs[anti.slot] != anti.inspects:
                findings.append(Finding(
                    "OI7_ANTI_OP", anti.op_id,
                    f"inspects {anti.inspects}, slot {anti.slot} of {anti.guards} "
                    f"is {guarded.inputs[anti.slot]}",
                ))

        for spec in (*skill.ops, *skill.anti_ops):
            if spec.binding:
                binding = spec.binding
                if isinstance(binding, PfpTurnBinding):
                    continue
                error = _binding_error(repo_root, binding.target if isinstance(binding, HostBinding) else binding)
                if error:
                    findings.append(Finding("OI8_BINDING", spec.op_id, error))
    return findings


def summary(inventory: OpInventory) -> str:
    specs = [s for skill in inventory.skills for s in (*skill.ops, *skill.anti_ops)]
    bound = sum(1 for s in specs if s.binding)
    anti = sum(len(skill.anti_ops) for skill in inventory.skills)
    from ..resolver.executors import HOST_EXECUTORS, HOST_DETECTORS, executable_coverage
    coverage=executable_coverage(inventory)
    executable_ops=sum(o.op_id in HOST_EXECUTORS for skill in inventory.skills for o in skill.ops)
    executable_guards=sum(a.op_id in HOST_DETECTORS for skill in inventory.skills for a in skill.anti_ops)
    return (
        f"{len(inventory.skills)} skills, {len(specs) - anti} ops, {anti} anti-ops; "
        f"{bound} declared BOUND, {len(specs) - bound} PROSE; "
        f"registered EXECUTABLE: {executable_ops}/{len(specs)-anti} ops, "
        f"{executable_guards}/{anti} guards, {sum(coverage.values())}/{len(coverage)} skills "
        "(bounded host adapters; declared PFP bindings require injected executors)"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    path = args.repo_root / INVENTORY_PATH
    try:
        inventory = load_inventory(path)
    except (OSError, yaml.YAMLError, ValidationError) as exc:
        print(f"FAIL: OI1_SCHEMA {path}: {exc}")
        return 1
    findings = check_inventory(args.repo_root, inventory)
    for finding in findings:
        print(f"FAIL: {finding}")
    print(("FAIL: " if findings else "PASS: ") + summary(inventory))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
