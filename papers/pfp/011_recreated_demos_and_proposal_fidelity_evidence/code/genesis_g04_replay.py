"""G04's full source-pinned finite rectangle and independent native replay."""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.abc
import importlib.util
import itertools
import json
import subprocess
import sys
import tempfile
import types
from collections import defaultdict
from pathlib import Path

PAPER = Path(__file__).resolve().parent.parent
REPOSITORY = (next((p for p in PAPER.parents if (p / ".git").exists()), None) or PAPER.parents[5])
PACKAGE = PAPER / "code/native_genesis_g04"
AREA = PAPER / "docs/history_recovery/g04"
SEALED = "3100c4ed5ce70d2b6cff6d2ccd3b0251cf918d0a"
HEAD = "b55fc96a94740b0afde78337350a96d293615f3f"
RUSTC = Path("C:/Users/a343o/source/repos/.rustup/toolchains/stable-x86_64-pc-windows-msvc/bin/rustc.exe")
DEPS = REPOSITORY / ".artifacts/epic0-cargo/debug/deps"
PYTHON = Path("C:/Program Files/WindowsApps/PythonSoftwareFoundation.Python.3.12_3.12.2800.0_x64__qbz5n2kfra8p0/python.exe")
PYTHON_SHA = "5365b422ee178f691988eb937b7abca5f48910b148f76fcce6dbaf5585c948d0"
NAMESPACE = "paper011_g04_original"
EXPECTED = {"EMPTY": 577, "L": 3928, "F": 14293}
STAKE_NAMES = ["free", "total_apart", "total_same", "parity", "residue_three", "chain", "one_sided_total"]
MANIFEST_SHA = "8a27d7c245c80b1674d960f647ad6df5d62b456de349a9b1b136afa35eb86fef"
TOKEN_MAP = {token: "G04Opaque" + str(i) for i, token in enumerate(
    ("<>", "<a>", "<ab>", "<n0>", "<n1>", "<n2>", "<n3>", "<n4>", "<z>"))}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def wire(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf8")


def save(path: Path, value: object) -> dict:
    raw = wire(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return {"path": path.relative_to(PAPER).as_posix(), "sha256": sha(raw), "bytes": len(raw)}


def files(paths) -> dict:
    return {str(path.resolve()): sha(path.read_bytes()) for path in sorted(set(paths))}


def git(repository: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(repository), *args], capture_output=True,
                          check=True, timeout=30).stdout


def recover(repository: Path) -> dict:
    requested = [(SEALED, "code/derivation/" + name + ".py")
                 for name in ("__init__", "model", "observe", "candidates", "iso", "engine")]
    requested += [(HEAD, path) for path in (
        "research/identification_dual/dual.py", "research/two_sided_commitment/two_sided.py",
        "research/second_nofirst/nofirst.py", "research/second_index/index.py",
        "research/second_index/receipts/index.json", "research/second_index/test_index.py",
        "research/second_index/STATUS.md", "research/second_index/PREDICTIONS.md",
        "research/second_index/SOURCE_MANIFEST.json", "research/second/SEED.md",
        "research/second_index/lean/SecondIndex/Index.lean",
        "research/second_index/lean/SecondIndex/Countermodel.lean")]
    rows = []
    for commit, path in requested:
        blob = git(repository, "rev-parse", commit + ":" + path).decode().strip()
        raw = git(repository, "cat-file", "blob", blob)
        if hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() != blob:
            raise ValueError("GIT_BLOB_MISMATCH:" + path)
        destination = PACKAGE / "original" / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() and destination.read_bytes() != raw:
            raise ValueError("WOULD_REPLACE_RECOVERED_BYTES:" + path)
        destination.write_bytes(raw)
        rows.append({"commit": commit, "source_path": path, "git_blob": blob,
                     "sha256": sha(raw), "bytes": len(raw), "path": destination.relative_to(PAPER).as_posix()})
    manifest = {"schema": "paper011.g04-source-manifest.v1", "AuthorityEffect": "None",
                "sealed_pin": SEALED, "head_pin": HEAD, "files": rows}
    return save(AREA / "source_manifest.json", manifest)


def verify_sources() -> dict:
    raw_manifest = (AREA / "source_manifest.json").read_bytes()
    if sha(raw_manifest) != MANIFEST_SHA:
        raise ValueError("SOURCE_MANIFEST_CHANGED")
    manifest = json.loads(raw_manifest)
    if manifest["sealed_pin"] != SEALED or manifest["head_pin"] != HEAD:
        raise ValueError("SOURCE_PIN_MISMATCH")
    for row in manifest["files"]:
        raw = (PAPER / row["path"]).read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if sha(raw) != row["sha256"] or blob != row["git_blob"] or len(raw) != row["bytes"]:
            raise ValueError("SOURCE_BYTES_MISMATCH:" + row["path"])
    return manifest


def relocate(raw: bytes, filename: str) -> tuple[ast.Module, dict]:
    """Only remove top-level sys.path rails and qualify sibling imports.

    Every remaining non-import AST node is checked against its original.
    No mathematical function, bound, stake, alphabet or statement is changed.
    """
    tree = ast.parse(raw, filename)
    removed = []
    rewrites = []
    retained = []
    for node in tree.body:
        touches_path = any(isinstance(part, ast.Attribute) and part.attr == "path"
                           and isinstance(part.value, ast.Name) and part.value.id == "sys"
                           for part in ast.walk(node))
        if isinstance(node, (ast.If, ast.For, ast.Expr)) and touches_path:
            removed.append({"line": node.lineno, "ast": ast.dump(node, include_attributes=False)})
            continue
        retained.append(node)
    tree.body = retained
    before_nodes = [ast.dump(node, include_attributes=False) for node in tree.body]
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            root = node.module.split(".")[0]
            if root in {"derivation", "dual", "two_sided", "nofirst"}:
                old = node.module
                node.module = NAMESPACE + "." + old
                rewrites.append({"line": node.lineno, "before": old, "after": node.module})
    # The inverse of every recorded import edit must restore all kept nodes exactly.
    import copy
    restored = copy.deepcopy(tree)
    for node in ast.walk(restored):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith(NAMESPACE + "."):
            node.module = node.module[len(NAMESPACE) + 1:]
    if before_nodes != [ast.dump(node, include_attributes=False) for node in restored.body]:
        raise ValueError("NON_IMPORT_AST_EDIT")
    ast.fix_missing_locations(tree)
    return tree, {"source_sha256": sha(raw), "transformed_ast_sha256": sha(ast.dump(tree, include_attributes=False).encode()),
                  "removed_import_rails": removed, "qualified_imports": rewrites,
                  "allowed_difference": "Top-level sys.path bootstrap removal and import-module qualification only"}


class SourceFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def __init__(self):
        root = PACKAGE / "original"
        self.paths = {NAMESPACE + ".derivation": root / "code/derivation/__init__.py"}
        self.paths.update({NAMESPACE + ".derivation." + name: root / "code/derivation" / (name + ".py")
                           for name in ("model", "observe", "candidates", "iso", "engine")})
        self.paths.update({NAMESPACE + "." + name: root / path for name, path in (
            ("dual", "research/identification_dual/dual.py"),
            ("two_sided", "research/two_sided_commitment/two_sided.py"),
            ("nofirst", "research/second_nofirst/nofirst.py"),
            ("index", "research/second_index/index.py"))})
        self.journal = []

    def find_spec(self, fullname, path=None, target=None):
        if fullname in self.paths:
            return importlib.util.spec_from_loader(fullname, self, is_package=fullname.endswith(".derivation"))
        if fullname.startswith(NAMESPACE + "."):
            raise ImportError("UNDECLARED_ORIGINAL_MODULE:" + fullname)
        return None

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        path = self.paths[module.__name__]
        raw = path.read_bytes()
        module.__file__ = str(path)
        if module.__name__.endswith(".derivation"):
            module.__path__ = []
        tree, receipt = relocate(raw, str(path))
        receipt["path"] = path.relative_to(PAPER).as_posix()
        self.journal.append(receipt)
        exec(compile(tree, str(path), "exec"), module.__dict__)


def load_original():
    verify_sources()
    if sys.version_info[:2] != (3, 12) or sha(PYTHON.read_bytes()) != PYTHON_SHA:
        raise ValueError("PYTHON_IDENTITY_MISMATCH")
    if NAMESPACE in sys.modules:
        raise ValueError("ORIGINAL_NAMESPACE_ALREADY_LOADED")
    sys.pycache_prefix = tempfile.mkdtemp(prefix="paper011-g04-empty-cache-")
    sys.dont_write_bytecode = True
    package = types.ModuleType(NAMESPACE)
    package.__path__ = []
    sys.modules[NAMESPACE] = package
    finder = SourceFinder()
    sys.meta_path.insert(0, finder)
    from importlib import import_module
    modules = {name: import_module(NAMESPACE + "." + name) for name in (
        "derivation.model", "derivation.observe", "derivation.iso", "derivation.engine", "nofirst", "index")}
    return {name.split(".")[-1]: module for name, module in modules.items()}, finder


def event_json(event) -> dict:
    kind = type(event).__name__
    if kind in ("Supply", "AdmitDatum"):
        return {"kind": kind, "token": event.token}
    if kind == "AdmitForm":
        return {"kind": kind, "arity": event.arity}
    if kind == "AdmitInst":
        return {"kind": kind, "form": event.form, "args": list(event.args)}
    if kind == "AdmitRuleAll":
        return {"kind": kind, "form": event.form}
    if kind == "Impose":
        return {"kind": kind, "i": event.i, "j": event.j}
    raise ValueError("UNDECLARED_EVENT:" + kind)


def freeze(value):
    return tuple(freeze(item) for item in value) if isinstance(value, (list, tuple)) else value


def original_rectangle(original: dict) -> dict:
    index, nf, model, iso = (original[name] for name in ("index", "nofirst", "model", "iso"))
    stakes = nf.declared_stakes()
    if [s.name for s in stakes] != STAKE_NAMES:
        raise ValueError("ORIGINAL_STAKES_MISMATCH")
    bases = []
    for name in ("EMPTY", "L", "F"):
        rectangle = index.build_rectangle(name, nf.ALPHABET)
        if len(rectangle.nodes) != EXPECTED[name]:
            raise ValueError("ORIGINAL_POPULATION_MISMATCH:" + name)
        seen = index.Observations()
        rows = []
        traces = []
        for number, node in enumerate(rectangle.nodes):
            prefixes = tuple(model.replay(node.history[:n], rectangle.regime) for n in range(len(node.history) + 1))
            if prefixes[-1] != node.regime:
                raise ValueError("ORIGINAL_NODE_REPLAY_MISMATCH")
            trace = tuple(iso.serialize(r, range(r.n_data()), range(len(r.forms))) for r in prefixes)
            forward = [index.first_index_forward(rectangle.regime, node.history, stake, seen) for stake in stakes]
            backward = [index.first_index_scan(rectangle.regime, node.history, stake, seen) for stake in stakes]
            if forward != backward:
                raise ValueError("ORIGINAL_CLASSIFIER_DISAGREEMENT")
            rows.append({"id": name + ":" + str(number), "history": [event_json(e) for e in node.history],
                         "grown": node.grown, "prefixes": trace, "first_forward": forward,
                         "first_scan": backward})
            traces.append(prefixes)
        bases.append({"name": name, "genesis": [event_json(e) for e in index.base_genesis(name)],
                      "rows": rows, "states": traces, "rectangle": rectangle,
                      "bound_stops": rectangle.bound_stops, "grammar_refusals": rectangle.grammar_refusals})
    return {"bases": bases, "stakes": stakes,
            "labels": [[[stake.label(i, j) for j in range(5)] for i in range(5)] for stake in stakes]}


def legal_prefix_permutation(trace, pi: tuple, phi: tuple) -> bool:
    return all(set(pi[:r.n_data()]) == set(range(r.n_data()))
               and set(phi[:len(r.forms)]) == set(range(len(r.forms))) for r in trace)


def token_signature(genesis: list[dict], history: list[dict]) -> tuple:
    names = {}
    result = []
    for event in genesis + history:
        value = dict(event)
        if "token" in value:
            token = value["token"]
            value["token"] = names.setdefault(token, len(names))
        result.append(tuple(sorted((key, freeze(value)) for key, value in value.items())))
    return len(genesis), tuple(result)


def parse_event(value: dict, model):
    kind = value["kind"]
    if kind in {"Supply", "AdmitDatum"}:
        return getattr(model, kind)(value["token"])
    if kind == "AdmitForm":
        return model.AdmitForm(value["arity"])
    if kind == "AdmitInst":
        return model.AdmitInst(value["form"], tuple(value["args"]))
    if kind == "AdmitRuleAll":
        return model.AdmitRuleAll(value["form"])
    if kind == "Impose":
        return model.Impose(value["i"], value["j"])
    raise ValueError("UNDECLARED_EVENT:" + kind)


def rename_tokens(value: dict) -> dict:
    return {**value, "token": TOKEN_MAP[value["token"]]} if "token" in value else dict(value)


def source_census(original: dict, rectangle: dict) -> dict:
    model, iso, index, nf = (original[name] for name in ("model", "iso", "index", "nofirst"))
    result = []
    for base in rectangle["bases"]:
        rows, states = base["rows"], base["states"]
        groups = {}
        token_groups = defaultdict(list)
        for number, row in enumerate(rows):
            groups.setdefault(freeze(row["prefixes"]), []).append(number)
            token_groups[token_signature(base["genesis"], row["history"])].append(row["id"])
        grouped = []
        relations = []
        seen = index.Observations()
        transport_cache = {}
        for keys, members in groups.items():
            number = members[0]
            trace = states[number]
            grouped.append({"representative": rows[number]["id"],
                            "members": [rows[m]["id"] for m in members], "prefixes": keys})
            if any(rows[m]["first_forward"] != rows[number]["first_forward"] for m in members):
                raise ValueError("EXACT_TRACE_MEMBER_INDEX_DISAGREEMENT")
            last = trace[-1]
            for pi in itertools.permutations(range(last.n_data())):
                for phi in itertools.permutations(range(len(last.forms))):
                    if not legal_prefix_permutation(trace, pi, phi):
                        continue
                    renamed_keys = tuple(iso.serialize(r, pi, phi) for r in trace)
                    if renamed_keys not in groups:
                        continue
                    targets = groups[renamed_keys]
                    target = targets[0]
                    cache_key = (target, pi)
                    if cache_key not in transport_cache:
                        inverse = [pi.index(i) for i in range(len(pi))]
                        transported = [nf.Stake(stake.name + "|G04transport|" + str(pi),
                            lambda i, j, s=stake, inv=inverse: s.label(inv[i], inv[j]))
                            for stake in rectangle["stakes"]]
                        target_h = base["rectangle"].nodes[target].history
                        forward = [index.first_index_forward(base["rectangle"].regime, target_h, s, seen) for s in transported]
                        backward = [index.first_index_scan(base["rectangle"].regime, target_h, s, seen) for s in transported]
                        if forward != backward:
                            raise ValueError("TRANSPORT_CLASSIFIER_DISAGREEMENT")
                        transport_cache[cache_key] = forward
                    relations.append({"source": rows[number]["id"], "target": rows[target]["id"],
                        "pi": pi, "phi": phi, "multiplicity": len(members) * len(targets),
                        "source_first": rows[number]["first_forward"],
                        "fixed_first": rows[target]["first_forward"],
                        "transported_first": transport_cache[cache_key]})
        renamed_genesis = [rename_tokens(e) for e in base["genesis"]]
        renamed_base = model.replay(tuple(parse_event(e, model) for e in renamed_genesis))
        renamed_rows = []
        for row in rows:
            history = [rename_tokens(e) for e in row["history"]]
            h = tuple(parse_event(e, model) for e in history)
            trace = [model.replay(h[:n], renamed_base) for n in range(len(h) + 1)]
            forward = [index.first_index_forward(renamed_base, h, s, seen) for s in rectangle["stakes"]]
            backward = [index.first_index_scan(renamed_base, h, s, seen) for s in rectangle["stakes"]]
            if forward != backward:
                raise ValueError("RENAMED_CLASSIFIER_DISAGREEMENT")
            renamed_rows.append({"id": row["id"], "history": history,
                "prefixes": [iso.serialize(r, range(r.n_data()), range(len(r.forms))) for r in trace], "first": forward})
        reports = {s.name: index.stake_report(base["rectangle"], s, seen) for s in rectangle["stakes"]}
        crosscheck = index.crosscheck(base["name"], nf.ALPHABET, index.CROSSCHECK_DEPTH)
        if not crosscheck["reach_agrees"]:
            raise ValueError("ORIGINAL_SECOND_ENUMERATOR_DISAGREEMENT")
        result.append({"name": base["name"], "genesis": base["genesis"],
            "bound_stops": base["bound_stops"], "grammar_refusals": base["grammar_refusals"],
            "rows": [{"id": row["id"], "history": row["history"], "grown": row["grown"],
                      "prefixes": row["prefixes"], "first": row["first_forward"]} for row in rows],
            "renamed_genesis": renamed_genesis, "renamed_rows": renamed_rows,
            "groups": grouped, "relations": relations,
            "token_partition": [{"members": members} for members in token_groups.values()],
            "colliding_regimes": [reports[s.name].colliding_regimes for s in rectangle["stakes"]],
            "crosscheck": crosscheck,
            "collision_witnesses": {name: report.collision_witness for name, report in reports.items()}})
    return {"schema": "paper011.g04-source-census.v1", "bases": result,
            "source_procedures": "Unchanged original enumerate_rectangle, first_index_forward, first_index_scan, stake_report; original serialize over all full bijections filtered by every prefix range"}


def native_dependencies() -> dict:
    target = subprocess.run([str(RUSTC), "--print", "target-libdir"], capture_output=True, check=True, timeout=30).stdout.decode().strip()
    return files([*DEPS.glob("*.rlib"), *DEPS.glob("*.dll"), *DEPS.glob("*.lib"), RUSTC,
        *RUSTC.parent.glob("*.dll"), *Path(target).glob("*.rlib"), *Path(target).glob("*.lib"),
        *(REPOSITORY / "engine/crates_rs/core_ooutwire_primitives/src").rglob("*.rs"),
        REPOSITORY / "engine/crates_rs/core_ooutwire_primitives/Cargo.toml",
        PAPER / "docs/native_build_receipt.json", PACKAGE / "second_checker.rs", Path(__file__), PYTHON])


def build_native(identity: str) -> dict:
    destination = AREA / identity
    destination.mkdir(parents=True, exist_ok=False)
    before = native_dependencies()
    executable = destination / "g04_second_checker.exe"
    argv = [str(RUSTC), "--edition", "2021", "--crate-name", "paper011_genesis_g04",
        str(PACKAGE / "second_checker.rs"), "-L", "dependency=" + str(DEPS),
        "--extern", "core_ooutwire_primitives=" + str(DEPS / "libcore_ooutwire_primitives-7419c0b1b3d813be.rlib"),
        "--extern", "serde_json=" + str(DEPS / "libserde_json-1a3e70913255bad6.rlib"), "-o", str(executable)]
    process = subprocess.run(argv, capture_output=True, timeout=300, check=False, cwd=PACKAGE)
    after = native_dependencies()
    if before != after:
        raise ValueError("BUILD_INPUT_DRIFT")
    (destination / "stdout.bin").write_bytes(process.stdout)
    (destination / "stderr.bin").write_bytes(process.stderr)
    receipt = {"schema": "paper011.g04-native-build.v1", "AuthorityEffect": "None", "argv": argv,
        "returncode": process.returncode, "inputs_before": before, "inputs_after": after,
        "stdout_sha256": sha(process.stdout), "stderr_sha256": sha(process.stderr),
        "executable": str(executable), "executable_sha256": sha(executable.read_bytes()) if executable.exists() else None,
        "custody_scope": "Exact existing archives/compiler/standard-library archive closure and wrapper bytes; no Cargo, external repo build or owner mathematical source changes. OS/linker installation excluded."}
    bound = save(destination / "receipt.json", receipt)
    return {**bound, "returncode": process.returncode}


def native_call(executable: Path, request: dict, destination: Path, identity: str, expected_error=None) -> dict:
    request_raw = wire(request)
    request_ref = save(destination / (identity + "_request.json"), request)
    before = sha(executable.read_bytes())
    process = subprocess.run([str(executable)], input=request_raw, capture_output=True, check=False, timeout=600)
    stdout, stderr = destination / (identity + "_stdout.json"), destination / (identity + "_stderr.bin")
    stdout.write_bytes(process.stdout)
    stderr.write_bytes(process.stderr)
    if sha(executable.read_bytes()) != before or sha((PAPER / request_ref["path"]).read_bytes()) != request_ref["sha256"]:
        raise ValueError("NATIVE_TRANSPORT_DRIFT")
    value = json.loads(process.stdout)
    if expected_error is None:
        if process.returncode != 0 or value.get("status") not in {"COMPUTED", "ACCEPTED"}:
            raise ValueError("NATIVE_COMPUTATION_REFUSED:" + str(value))
    elif process.returncode != 2 or value.get("status") != "REFUSED" or value.get("id") != request["id"] or value.get("error") != expected_error:
        raise ValueError("TYPED_MUTATION_REFUSAL_MISMATCH:" + str(value))
    receipt = {"id": identity, "request": request_ref, "argv": [str(executable)], "returncode": process.returncode,
        "executable_sha256": before, "stdout_path": stdout.relative_to(PAPER).as_posix(), "stdout_sha256": sha(process.stdout),
        "stderr_path": stderr.relative_to(PAPER).as_posix(), "stderr_sha256": sha(process.stderr),
        "representation": "PHYSICAL_RAW_SUBPROCESS_BYTES", "expected_error": expected_error}
    save(destination / (identity + "_process.json"), receipt)
    return {"value": value, "receipt": receipt}


def verify_comparison(source: dict, native: dict) -> dict:
    summaries = []
    for original, replayed in zip(source["bases"], native["bases"], strict=True):
        name = original["name"]
        for field in ("name", "genesis", "bound_stops", "grammar_refusals", "rows", "renamed_genesis", "renamed_rows", "groups", "relations", "colliding_regimes"):
            if freeze(original[field]) != freeze(replayed[field]):
                raise ValueError("SOURCE_NATIVE_MISMATCH:" + name + ":" + field)
        a = sorted(tuple(group["members"]) for group in original["token_partition"])
        b = sorted(tuple(group["members"]) for group in replayed["token_partition"])
        if a != b:
            raise ValueError("TOKEN_PARTITION_MISMATCH")
        by_id = {row["id"]: row for row in original["rows"]}
        token_pairs = 0
        for group in original["token_partition"]:
            members = group["members"]
            if any(by_id[m]["first"] != by_id[members[0]]["first"] for m in members):
                raise ValueError("TOKEN_RENAMING_COUNTEREXAMPLE")
            token_pairs += len(members) ** 2
        if any(row["prefixes"] != original["rows"][i]["prefixes"] or row["first"] != original["rows"][i]["first"]
               for i, row in enumerate(original["renamed_rows"])):
            raise ValueError("FULL_RECTANGLE_OPAQUE_TOKEN_RENAMING_FAILED")
        b_failures = [r for r in original["relations"] if r["source_first"] != r["transported_first"]]
        c_failures = [r for r in original["relations"] if r["source_first"] != r["fixed_first"]]
        summaries.append({"base": name, "rows": len(original["rows"]), "row_stake_checks": len(original["rows"]) * 7,
            "exact_prefix_trace_classes": len(original["groups"]), "common_bijection_relations": len(original["relations"]),
            "nonidentity_common_bijections": sum(r["pi"] != list(range(len(r["pi"]))) or r["phi"] != list(range(len(r["phi"]))) for r in original["relations"]),
            "represented_ordered_history_mapping_relations": sum(r["multiplicity"] for r in original["relations"]),
            "token_renaming_ordered_pairs_in_original_rectangle": token_pairs,
            "nonidentical_token_pairs_in_original_rectangle": token_pairs - len(original["rows"]),
            "opaque_renaming_supplement_rows": len(original["renamed_rows"]),
            "transported_disagreements": len(b_failures), "fixed_disagreements": len(c_failures),
            "first_fixed_counterexample": c_failures[0] if c_failures else None,
            "colliding_regimes_by_original_stake": dict(zip(STAKE_NAMES, original["colliding_regimes"], strict=True))})
    return {"schema": "paper011.g04-comparison.v1", "bases": summaries,
        "source_native_all_row_history_prefix_indices_equal": True,
        "source_native_all_group_members_and_mapping_relations_equal": True,
        "X3a": "HOLDS_ON_RECTANGLE", "X3b": "COUNTEREXAMPLE" if any(r["transported_disagreements"] for r in summaries) else "HOLDS_ON_RECTANGLE",
        "X3c": "COUNTEREXAMPLE" if any(r["fixed_disagreements"] for r in summaries) else "HOLDS_ON_RECTANGLE"}


def run(identity: str, build_receipt: Path) -> dict:
    destination = AREA / identity
    destination.mkdir(parents=True, exist_ok=False)
    build_raw = build_receipt.read_bytes()
    build = json.loads(build_raw)
    if build["returncode"] != 0 or build["inputs_before"] != build["inputs_after"]:
        raise ValueError("BUILD_NOT_CLOSED")
    for path, digest in build["inputs_after"].items():
        if sha(Path(path).read_bytes()) != digest:
            raise ValueError("BUILD_DEPENDENCY_CHANGED:" + path)
    executable = Path(build["executable"])
    if sha(executable.read_bytes()) != build["executable_sha256"]:
        raise ValueError("NATIVE_EXECUTABLE_CHANGED")
    manifest = verify_sources()
    custody_paths = [PAPER / row["path"] for row in manifest["files"]] + [AREA / "source_manifest.json",
        Path(__file__), PACKAGE / "second_checker.rs", executable, build_receipt, PYTHON,
        PAPER / "docs/history_recovery/recovered_sources/g04_x3_first_demand_iso_invariance.md"]
    before = files(custody_paths)
    original, finder = load_original()
    rectangle = original_rectangle(original)
    source = source_census(original, rectangle)
    source_ref = save(destination / "source_census.json", source)
    request = {"action": "census", "stake_names": STAKE_NAMES, "labels": rectangle["labels"], "token_map": TOKEN_MAP}
    native = native_call(executable, request, destination, "native_census")
    comparison = verify_comparison(json.loads((PAPER / source_ref["path"]).read_bytes()), native["value"])
    comparison_ref = save(destination / "comparison.json", comparison)
    mutations = []
    # A source-bound nonidentity F-root relation changes parity labels even though its first count is already zero.
    f = source["bases"][2]
    rel = next(r for r in f["relations"] if r["source"] == "F:0" and list(r["pi"]) == [1, 0, 2])
    pi = list(rel["pi"])
    inverse = [pi.index(i) for i in range(len(pi))]
    proper = [[rectangle["labels"][3][inverse[i]][inverse[j]] for j in range(len(pi))] for i in range(len(pi))]
    wrong = [row[:len(pi)] for row in rectangle["labels"][3][:len(pi)]]
    assert proper != wrong
    positive = {"action": "audit", "id": "transport_valid", "mutation": "untransported_stake", "pi": pi,
                "stake": 3, "claimed_transported_labels": proper, "source_relation": rel}
    mutations.append(native_call(executable, positive, destination, "transport_valid")["receipt"])
    bad = {**positive, "id": "M01_stake_untransported", "claimed_transported_labels": wrong}
    mutations.append(native_call(executable, bad, destination, bad["id"], "STAKE_TRANSPORT_MISMATCH")["receipt"])
    bad = {"action": "audit", "id": "M02_pi_applied_to_forms", "mutation": "pi_on_forms", "pi": pi,
           "forms": 0, "source_relation": rel}
    mutations.append(native_call(executable, bad, destination, bad["id"], "FORM_BIJECTION_DIMENSION")["receipt"])
    historical = json.loads((PACKAGE / "original/research/second_index/receipts/index.json").read_bytes())
    historical_witness = historical["reports"][0]["stakes"]["total_apart"]["collision_witness"]
    empty = rectangle["bases"][0]
    descriptors = {tuple(original["index"].history_descriptor(n.history)): i for i, n in enumerate(empty["rectangle"].nodes)}
    ids = [descriptors[tuple(h)] for h in historical_witness["histories"]]
    endpoints = [empty["states"][i][-1] for i in ids]
    firsts = [empty["rows"][i]["first_forward"][1] for i in ids]
    if endpoints[0] != endpoints[1] or firsts != historical_witness["indices"] or firsts[0] == firsts[1]:
        raise ValueError("HISTORICAL_ENDPOINT_WITNESS_REPLAY_FAILED")
    witness = {"original_receipt_path": "code/native_genesis_g04/original/research/second_index/receipts/index.json",
        "original_witness": historical_witness, "row_ids": [empty["rows"][i]["id"] for i in ids],
        "histories": [empty["rows"][i]["history"] for i in ids], "firsts": firsts,
        "endpoint_tokens": endpoints[0].data, "endpoint_structure": empty["rows"][ids[0]]["prefixes"][-1],
        "reading": "POISON_ENDPOINT", "status": "OUT_OF_SCOPE", "reason": "Same reached regime has different first counts"}
    witness_ref = save(destination / "endpoint_witness.json", witness)
    bad = {"action": "audit", "id": "M03_endpoint_only", "mutation": "endpoint_only", "pi": [], "histories": witness["histories"], "claimed_endpoint_first": firsts[0]}
    mutations.append(native_call(executable, bad, destination, bad["id"], "ENDPOINT_NOT_FIRST_INDEX:" + json.dumps(firsts, separators=(",", ":")))["receipt"])
    after = files(custody_paths)
    for path, digest in build["inputs_after"].items():
        if sha(Path(path).read_bytes()) != digest:
            raise ValueError("POST_RUN_NATIVE_DEPENDENCY_CHANGED:" + path)
    if before != after:
        raise ValueError("EXECUTION_INPUT_DRIFT")
    receipt = {"schema": "paper011.g04-execution.v1", "AuthorityEffect": "None", "identity": identity,
        "build_receipt": {"path": build_receipt.relative_to(PAPER).as_posix(), "sha256": sha(build_raw)},
        "inputs_before": before, "inputs_after": after, "source_census": source_ref,
        "native_census": native["receipt"], "comparison": comparison_ref, "endpoint_witness": witness_ref,
        "import_adaptation_journal": finder.journal, "mutations": mutations,
        "original_mutations_rejected": 3, "valid_transport_control_accepted": True,
        "empty_cache_prefix": sys.pycache_prefix, "dont_write_bytecode": sys.dont_write_bytecode,
        "provider_calls": 0, "heldout_gate_complete": False,
        "missing_inputs": ["Original operator seed and actual length-five held-out sequence identities from each base", "Two operator-declared stake functions beyond the seven"],
        "model_comparison_completed": False, "external_estate_gates_run": False, "owner_pull_request_created": False,
        "scope": "Complete original finite rectangle; all original row identities, prefix fields, class members and common-bijection relations checked independently. The one opaque-token renaming of every row is supplementary finite coverage, not a theorem for arbitrary token names. Python standard-library/OS images are outside the raw custody map; no third-party Python dependencies imported."}
    return {**save(destination / "receipt.json", receipt), "comparison": comparison, "original_mutations_rejected": 3}


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="action", required=True)
    recovery = sub.add_parser("recover")
    recovery.add_argument("--repository", type=Path, required=True)
    sub.add_parser("pilot")
    build = sub.add_parser("build-native")
    build.add_argument("--identity", required=True)
    census = sub.add_parser("run")
    census.add_argument("--identity", required=True)
    census.add_argument("--build-receipt", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "recover":
        result = recover(args.repository)
    elif args.action == "build-native":
        result = build_native(args.identity)
    elif args.action == "run":
        result = run(args.identity, args.build_receipt)
    else:
        original, finder = load_original()
        rectangle = original_rectangle(original)
        result = {"bases": [{"name": base["name"], "rows": len(base["rows"]),
                             "initial_indices": base["rows"][0]["first_forward"],
                             "unique_traces": len(set(freeze(row["prefixes"]) for row in base["rows"]))}
                            for base in rectangle["bases"]], "imports": len(finder.journal)}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
