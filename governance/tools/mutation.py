"""Mutation campaigns with the six-outcome accounting of SCORING.md section 3.4.

AuthorityEffect: None.
Contract: urn:pfp-governance:mutation:v1

``python -m governance.tools.mutation NAME --target FILE ... [--equivalent FILE]
-- PYTEST-ARGS`` mutates each target one mutant at a time, runs pytest, and
writes ``governance/evidence/NAME.mutation.json``. With ``--runner command``
the words after ``--`` are run as given (for example ``dotnet run --project
csharp/PfpLab.Tests``), and ``--killed-exit``/``--invalid-exit`` say which exit
codes mean a failing test and a failed build.

Python mutants are made on the AST: comparison flips, ``+``/``-`` and
``*``/``+`` swaps, ``and``/``or`` swaps, ``not`` removal, ``True``/``False``
and integer ``n``/``n+1`` changes, ``return x`` to ``return None`` and
``raise`` to ``pass``. C# mutants are lexical: string and character literals
and ``//`` comments are masked, then each operator occurrence is one site
(``==``/``!=``, ``&&``/``||``, ``<=``/``>``, ``>=``/``<``, spaced ``<``/``>`` so
generics stay untouched, ``true``/``false``, ``throw new`` to ``_ = new``). A
lexical mutant that does not build is recorded INVALID from the build's exit code.
Outcomes: KILLED (a killed exit code, default 1; with the pytest runner also
exit 2 when pytest reports a named test module that failed to import or
collect, which attributes the failure to the mutant), SURVIVED (exit 0), INVALID
(a Python mutant that does not compile, never run, or an invalid exit code such
as a failed C# build), INCONCLUSIVE (timeout or any other exit), UNRUN (beyond
``--max``) and EQUIVALENT (listed in the equivalents file with a written
justification and the target's hash).
R = killed / (killed + survived + inconclusive + unrun); an empty campaign
reports ``null``.

Safety: the original bytes are written to ``governance/evidence/NAME.journal``
before the first edit and restored after every mutant and on any exit; if the
journal exists when a campaign starts, the campaign refuses to run until
``--recover`` restores it. Bytecode goes to a fresh cache directory per
campaign so a stale ``.pyc`` can never stand in for a mutant.
"""

from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import json
import os
import re
import subprocess  # noqa: S404 - runs pytest with a fixed argv, no shell
import sys
import tempfile
import time
from collections.abc import Callable, Iterator, Sequence
from dataclasses import asdict, dataclass
from enum import StrEnum
from fractions import Fraction
from pathlib import Path
from typing import TextIO

from governance.tools.checker import ROOT

EVIDENCE = "governance/evidence"
DEFAULT_TIMEOUT = 300
PYTEST_FAILED = 1
PYTEST_INTERRUPTED = 2
_COLLECTION_MARKERS = (b"ERROR collecting", b"errors during collection")


def _collection_failed(output: bytes) -> bool:
    """pytest stopped because a named test module failed to import or collect."""
    return any(marker in output for marker in _COLLECTION_MARKERS)


_REPLACEMENTS: tuple[tuple[str, str, str], ...] = (
    (r"==", "==", "!="),
    (r"!=", "!=", "=="),
    (r"&&", "&&", "||"),
    (r"\|\|", "||", "&&"),
    (r"<=", "<=", ">"),
    (r"(?<![=>])>=", ">=", "<"),
    (r" < ", " < ", " >= "),
    (r" > ", " > ", " <= "),
    (r"\btrue\b", "true", "false"),
    (r"\bfalse\b", "false", "true"),
    (r"\bthrow new\b", "throw new", "_ = new"),
)
_STRING = re.compile(r'@?\$?"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)\'')


@dataclass(frozen=True, slots=True)
class LexicalSite:
    line: int
    column: int
    old: str
    new: str

    @property
    def description(self) -> str:
        return f"{self.old.strip()} -> {self.new.strip()}"


def mask(line: str) -> str:
    """The line with literal contents and any ``//`` comment replaced by spaces."""
    masked = _STRING.sub(lambda match: '"' + " " * (len(match.group(0)) - 2) + '"', line)
    comment = masked.find("//")
    return masked if comment < 0 else masked[:comment] + " " * (len(masked) - comment)


def lexical_sites(source: str) -> list[LexicalSite]:
    """Every site, line by line, then by operator, then left to right."""
    found: list[LexicalSite] = []
    for number, line in enumerate(source.splitlines(), start=1):
        masked = mask(line)
        for pattern, old, new in _REPLACEMENTS:
            found.extend(LexicalSite(number, match.start(), old, new) for match in re.finditer(pattern, masked))
    return found


def lexical_mutant(source: str, index: int) -> str:
    """``source`` with site ``index`` replaced; line endings are kept."""
    site = lexical_sites(source)[index]
    lines = source.splitlines(keepends=True)
    text = lines[site.line - 1]
    lines[site.line - 1] = text[: site.column] + site.new + text[site.column + len(site.old) :]
    return "".join(lines)


class Outcome(StrEnum):
    KILLED = "killed"
    SURVIVED = "survived"
    EQUIVALENT = "demonstrably_equivalent"
    INVALID = "invalid"
    INCONCLUSIVE = "inconclusive"
    UNRUN = "unrun"


_COMPARE_FLIPS: dict[type[ast.cmpop], type[ast.cmpop]] = {
    ast.Eq: ast.NotEq,
    ast.NotEq: ast.Eq,
    ast.Lt: ast.GtE,
    ast.GtE: ast.Lt,
    ast.Gt: ast.LtE,
    ast.LtE: ast.Gt,
    ast.Is: ast.IsNot,
    ast.IsNot: ast.Is,
    ast.In: ast.NotIn,
    ast.NotIn: ast.In,
}
_BINOP_SWAPS: dict[type[ast.operator], type[ast.operator]] = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Add}

Mutator = Callable[[ast.AST], ast.AST]


@dataclass(frozen=True, slots=True)
class Site:
    """One mutation: where it is and what it does."""

    line: int
    description: str


@dataclass(frozen=True, slots=True)
class Result:
    path: str
    index: int
    line: int
    description: str
    outcome: Outcome
    seconds: float


def _compare(node: ast.AST) -> Iterator[tuple[str, Mutator]]:
    if isinstance(node, ast.Compare) and not _is_main_guard(node):
        for position, operator in enumerate(node.ops):
            flipped = _COMPARE_FLIPS.get(type(operator))
            if flipped is not None:
                yield f"{type(operator).__name__} -> {flipped.__name__}", _replace_op(position, flipped)


def _is_main_guard(node: ast.Compare) -> bool:
    return isinstance(node.left, ast.Name) and node.left.id == "__name__"


def _replace_op(position: int, operator: type[ast.cmpop]) -> Mutator:
    def apply(node: ast.AST) -> ast.AST:
        if isinstance(node, ast.Compare):
            node.ops[position] = operator()
        return node

    return apply


def _binop(node: ast.AST) -> Iterator[tuple[str, Mutator]]:
    if isinstance(node, ast.BinOp):
        swapped = _BINOP_SWAPS.get(type(node.op))
        if swapped is not None:
            yield f"{type(node.op).__name__} -> {swapped.__name__}", _set_attribute("op", swapped)


def _boolop(node: ast.AST) -> Iterator[tuple[str, Mutator]]:
    if isinstance(node, ast.BoolOp):
        swapped: type[ast.boolop] = ast.Or if isinstance(node.op, ast.And) else ast.And
        yield f"{type(node.op).__name__} -> {swapped.__name__}", _set_attribute("op", swapped)


def _set_attribute(name: str, kind: type[ast.AST]) -> Mutator:
    def apply(node: ast.AST) -> ast.AST:
        setattr(node, name, kind())
        return node

    return apply


def _not(node: ast.AST) -> Iterator[tuple[str, Mutator]]:
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        yield "remove not", lambda found: found.operand if isinstance(found, ast.UnaryOp) else found


def _constant(node: ast.AST) -> Iterator[tuple[str, Mutator]]:
    if isinstance(node, ast.Constant) and type(node.value) is bool:
        yield f"{node.value} -> {not node.value}", _set_value(not node.value)
    elif isinstance(node, ast.Constant) and type(node.value) is int:
        yield f"{node.value} -> {node.value + 1}", _set_value(node.value + 1)


def _set_value(value: bool | int) -> Mutator:
    def apply(node: ast.AST) -> ast.AST:
        if isinstance(node, ast.Constant):
            node.value = value
        return node

    return apply


def _statement(node: ast.AST) -> Iterator[tuple[str, Mutator]]:
    if isinstance(node, ast.Return) and node.value is not None and not _is_none(node.value):
        yield "return value -> return None", lambda found: ast.Return(value=None)
    if isinstance(node, ast.Raise):
        yield "raise -> pass", lambda found: ast.Pass()


def _is_none(node: ast.expr) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


OPERATORS = (_compare, _binop, _boolop, _not, _constant, _statement)


def _annotation_ids(tree: ast.Module) -> set[int]:
    """Nodes inside annotations, which are not runtime code."""
    skipped: set[int] = set()
    for node in ast.walk(tree):
        parts = [getattr(node, "annotation", None), getattr(node, "returns", None)]
        for part in parts:
            if isinstance(part, ast.AST):
                skipped.update(id(child) for child in ast.walk(part))
    return skipped


def _candidates(tree: ast.Module) -> Iterator[tuple[ast.AST, str, Mutator]]:
    skipped = _annotation_ids(tree)
    for node in ast.walk(tree):
        if id(node) in skipped:
            continue
        for operator in OPERATORS:
            for description, mutate in operator(node):
                yield node, description, mutate


def sites(source: str, suffix: str = ".py") -> list[Site]:
    """Every mutation site of ``source``, in a stable order."""
    if suffix == ".cs":
        return [Site(site.line, site.description) for site in lexical_sites(source)]
    tree = ast.parse(source)
    return [Site(getattr(node, "lineno", 0), description) for node, description, _ in _candidates(tree)]


class _Replace(ast.NodeTransformer):
    def __init__(self, target: ast.AST, mutate: Mutator) -> None:
        self.target = target
        self.mutate = mutate

    def visit(self, node: ast.AST) -> ast.AST:
        if node is self.target:
            return ast.copy_location(self.mutate(node), node)
        visited: ast.AST = super().visit(node)
        return visited


def mutant(source: str, index: int, suffix: str = ".py") -> str:
    """The source text with mutation ``index`` applied."""
    if suffix == ".cs":
        return lexical_mutant(source, index)
    tree = ast.parse(source)
    node, _, mutate = list(_candidates(tree))[index]
    changed = ast.fix_missing_locations(_Replace(node, mutate).visit(tree))
    return ast.unparse(changed) + "\n"


def compiles(text: str, suffix: str = ".py") -> bool:
    """Python mutants are compiled here; other languages are left to their build."""
    if suffix != ".py":
        return True
    try:
        compile(text, "<mutant>", "exec")
    except SyntaxError:
        return False
    return True


def conservative_ratio(counts: dict[Outcome, int]) -> Fraction | None:
    eligible = counts[Outcome.KILLED] + counts[Outcome.SURVIVED] + counts[Outcome.INCONCLUSIVE] + counts[Outcome.UNRUN]
    return Fraction(counts[Outcome.KILLED], eligible) if eligible else None


def classify(
    exit_status: int | None, killed: frozenset[int] = frozenset({1}), invalid: frozenset[int] = frozenset()
) -> Outcome:
    if exit_status == 0:
        return Outcome.SURVIVED
    if exit_status in killed:
        return Outcome.KILLED
    if exit_status in invalid:
        return Outcome.INVALID
    return Outcome.INCONCLUSIVE


class Campaign:
    """One named campaign over one or more targets, restoring every byte it touches."""

    def __init__(
        self,
        root: Path,
        name: str,
        pytest_args: Sequence[str],
        timeout: int,
        *,
        runner: str = "pytest",
        exits: tuple[frozenset[int], frozenset[int]] = (frozenset({1}), frozenset()),
    ) -> None:
        self.root = root
        self.name = name
        self.pytest_args = list(pytest_args)
        self.timeout = timeout
        self.runner = runner
        self.killed, self.invalid = exits
        self.journal = root / EVIDENCE / f"{name}.journal"
        self.journal.parent.mkdir(parents=True, exist_ok=True)
        self.cache = Path(tempfile.mkdtemp(prefix="pfp-mutation-"))

    def run_tests(self) -> int | None:
        env = dict(os.environ, HYPOTHESIS_PROFILE="mutation", PYTHONPYCACHEPREFIX=str(self.cache))
        command = self.pytest_args
        if self.runner == "pytest":
            command = [sys.executable, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider", *self.pytest_args]
        try:
            completed = subprocess.run(  # noqa: S603 - fixed interpreter and pytest argv
                command,
                cwd=self.root,
                env=env,
                capture_output=True,
                timeout=self.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return None
        if (
            self.runner == "pytest"
            and completed.returncode == PYTEST_INTERRUPTED
            and _collection_failed(completed.stdout)
        ):
            # pytest names the test module the mutant broke at import time: a detected, attributed failure.
            return PYTEST_FAILED
        return completed.returncode

    def mutate_file(self, path: Path, equivalents: set[tuple[str, int, str]], budget: int) -> list[Result]:
        original = path.read_bytes()
        name = path.relative_to(self.root).as_posix()
        source = original.decode("utf-8")
        self.journal.write_text(json.dumps({"path": name, "bytes": base64.b64encode(original).decode()}), "utf-8")
        results: list[Result] = []
        try:
            for index, site in enumerate(sites(source, path.suffix)):
                results.append(self._one(path, name, source, index, site, equivalents, budget - len(results)))
        finally:
            path.write_bytes(original)
            self.journal.unlink()
        return results

    def _one(
        self,
        path: Path,
        name: str,
        source: str,
        index: int,
        site: Site,
        equivalents: set[tuple[str, int, str]],
        remaining: int,
    ) -> Result:
        started = time.monotonic()
        if (name, index, site.description) in equivalents:
            outcome = Outcome.EQUIVALENT
        elif remaining <= 0:
            outcome = Outcome.UNRUN
        else:
            text = mutant(source, index, path.suffix)
            if not compiles(text, path.suffix):
                outcome = Outcome.INVALID
            else:
                path.write_bytes(text.encode("utf-8"))
                outcome = classify(self.run_tests(), self.killed, self.invalid)
        return Result(name, index, site.line, site.description, outcome, round(time.monotonic() - started, 2))


def recover(root: Path, name: str) -> bool:
    """Restore the bytes saved in a leftover journal; True if one was found."""
    journal = root / EVIDENCE / f"{name}.journal"
    if not journal.is_file():
        return False
    saved = json.loads(journal.read_text(encoding="utf-8"))
    (root / saved["path"]).write_bytes(base64.b64decode(saved["bytes"]))
    journal.unlink()
    return True


def load_equivalents(path: Path | None, root: Path) -> set[tuple[str, int, str]]:
    """``(path, index, description)`` triples whose target still has the justified hash."""
    if path is None:
        return set()
    accepted: set[tuple[str, int, str]] = set()
    for item in json.loads(path.read_text(encoding="utf-8"))["equivalents"]:
        if not item.get("justification"):
            continue
        current = hashlib.sha256((root / item["path"]).read_bytes()).hexdigest()
        if current == item["sha256"]:
            accepted.add((item["path"], item["index"], item["description"]))
    return accepted


def summarize(results: Sequence[Result]) -> dict[str, object]:
    counts = {outcome: sum(1 for item in results if item.outcome is outcome) for outcome in Outcome}
    ratio = conservative_ratio(counts)
    return {
        **{outcome.value: counts[outcome] for outcome in Outcome},
        "total": len(results),
        "conservative_ratio": None if ratio is None else f"{ratio.numerator}/{ratio.denominator}",
    }


def build_report(
    root: Path, name: str, targets: Sequence[Path], args: Sequence[str], results: list[Result]
) -> dict[str, object]:
    per_file = {
        path.relative_to(root).as_posix(): summarize(
            [item for item in results if item.path == path.relative_to(root).as_posix()]
        )
        for path in targets
    }
    return {
        "schema_version": "pfp.mutation-report.v1",
        "AuthorityEffect": "None",
        "name": name,
        "pytest_args": list(args),
        "python": sys.version.split()[0],
        "targets": {
            path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in targets
        },
        "per_file": per_file,
        "totals": summarize(results),
        "mutants": [{**asdict(item), "outcome": item.outcome.value} for item in results],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mutation", description="Run a six-outcome mutation campaign.")
    parser.add_argument("name")
    parser.add_argument("--target", action="append", type=Path, default=[])
    parser.add_argument("--equivalent", type=Path)
    parser.add_argument("--max", type=int, default=10_000, help="mutants to run before the rest count as UNRUN")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--recover", action="store_true", help="restore a leftover journal and stop")
    parser.add_argument("--runner", choices=("pytest", "command"), default="pytest")
    parser.add_argument("--killed-exit", type=int, action="append", help="exit codes meaning a test failed")
    parser.add_argument("--invalid-exit", type=int, action="append", help="exit codes meaning the build failed")
    return parser


def split_command(argv: Sequence[str]) -> tuple[list[str], list[str]]:
    """Options before ``--``; the passed-through command after it."""
    items = list(argv)
    if "--" not in items:
        return items, []
    cut = items.index("--")
    return items[:cut], items[cut + 1 :]


def main(argv: Sequence[str] | None = None, out: TextIO | None = None, root: Path = ROOT) -> int:
    stream = out if out is not None else sys.stdout
    options, pytest_args = split_command(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(options)
    if args.recover:
        stream.write("restored\n" if recover(root, args.name) else "no journal\n")
        return 0
    if (root / EVIDENCE / f"{args.name}.journal").exists():
        stream.write("a journal from an interrupted campaign exists; run with --recover first\n")
        return 2
    targets = [path if path.is_absolute() else root / path for path in args.target]
    exits = (frozenset(args.killed_exit or [1]), frozenset(args.invalid_exit or []))
    campaign = Campaign(root, args.name, pytest_args, args.timeout, runner=args.runner, exits=exits)
    if campaign.run_tests() != 0:
        stream.write("the unmutated suite does not pass; refusing to start\n")
        return 2
    equivalents = load_equivalents(args.equivalent, root)
    results: list[Result] = []
    for path in targets:
        results += campaign.mutate_file(path, equivalents, args.max - len(results))
    report = build_report(root, args.name, targets, pytest_args, results)
    target = root / EVIDENCE / f"{args.name}.mutation.json"
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    stream.write(f"{args.name}: {json.dumps(report['totals'])}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
