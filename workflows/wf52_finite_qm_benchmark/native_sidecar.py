"""Public affine-matrix sidecar; native exact arithmetic, no provider/evaluator access.

Certifies only det(lambda I - A(J,Delta,K)). The independently supplied affine
matrix interpretation, surrounding prose, projectors and dynamics are unresolved.
The native process is the isolated source-bound wrapper, not the full PFP host.
"""
from __future__ import annotations

from fractions import Fraction
import hashlib
from itertools import product
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
HOST = HERE / "native_sidecar_host"
PARAMETERS = ["J", "Delta", "K"]
OWNER_SHA = "9d78981a19c942a70d4d4262f1df9538024754b2b87c0e0288a46d377cd3916c"
UNRESOLVED = ["public-prose-to-affine-matrix interpretation", "surrounding prose",
              "spectrum projectors", "eigenvectors", "dynamics", "other obligations"]


class Invalid(ValueError):
    pass


class Infrastructure(RuntimeError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def strict_json(raw):
    def pairs(items):
        out = {}
        for key, val in items:
            if key in out:
                raise Invalid("DUPLICATE_JSON_KEY")
            out[key] = val
        return out
    def no_float(_):
        raise Invalid("FLOAT_FORBIDDEN")
    return json.loads(raw, object_pairs_hook=pairs, parse_float=no_float,
                      parse_constant=no_float)


def keys(value, expected, label):
    if type(value) is not dict or set(value) != set(expected):
        raise Invalid(label)


def rational(text, bits=64):
    if type(text) is not str or len(text) > bits * 2 + 4:
        raise Invalid("RATIONAL_WIRE")
    try:
        q = Fraction(text)
    except (ValueError, ZeroDivisionError):
        raise Invalid("RATIONAL_INVALID") from None
    if str(q) != text:
        raise Invalid("RATIONAL_NONCANONICAL")
    if q.numerator.bit_length() > bits or q.denominator.bit_length() > bits:
        raise Invalid("RATIONAL_BIT_LIMIT")
    return q


def admit_public(public):
    if len(canonical(public)) > 32_768:
        raise Invalid("PUBLIC_BYTE_LIMIT")
    keys(public, ["schema", "obligation_id", "parameters", "matrix_coefficients"],
         "PUBLIC_FIELDS")
    if public["schema"] != "pfp.qm-affine-charpoly-public.v1":
        raise Invalid("PUBLIC_SCHEMA")
    if public["parameters"] != PARAMETERS:
        raise Invalid("THREE_PARAMETERS_REQUIRED_IN_ORDER")
    if type(public["obligation_id"]) is not str or not 1 <= len(public["obligation_id"]) <= 128:
        raise Invalid("OBLIGATION_ID")
    matrices = public["matrix_coefficients"]
    keys(matrices, ["constant", *PARAMETERS], "FOUR_AFFINE_COEFFICIENT_MATRICES_REQUIRED")
    first = matrices["constant"]
    if type(first) is not list or not 1 <= len(first) <= 4:
        raise Invalid("MATRIX_DIMENSION")
    n = len(first)
    out = {}
    for name, rows in matrices.items():
        if (type(rows) is not list or len(rows) != n or
            any(type(row) is not list or len(row) != n for row in rows)):
            raise Invalid("MATRIX_SHAPE")
        # Four 16-bit rational coefficients evaluated at |parameter|<=2 have
        # <128-bit numerators/denominators, within the native admission bound.
        out[name] = [[rational(x, bits=16) for x in row] for row in rows]
    return n, out


def admit_coefficients(wire, n):
    if type(wire) is not list or len(wire) != n + 1:
        raise Invalid("LAMBDA_COEFFICIENT_COUNT")
    result = []
    for terms in wire:
        if type(terms) is not list or len(terms) > (n + 1) ** 3:
            raise Invalid("MONOMIAL_LIMIT")
        seen, parsed = set(), []
        for term in terms:
            keys(term, ["powers", "q"], "MONOMIAL_FIELDS")
            powers = term["powers"]
            if (type(powers) is not list or len(powers) != 3 or
                any(type(e) is not int or not 0 <= e <= n for e in powers)):
                raise Invalid("PER_VARIABLE_DEGREE_LIMIT")
            exponents = tuple(powers)
            if exponents in seen:
                raise Invalid("DUPLICATE_MONOMIAL")
            seen.add(exponents)
            q = rational(term["q"])
            if not q:
                raise Invalid("SPARSE_ZERO_TERM")
            parsed.append((exponents, q))
        result.append(parsed)
    if result[-1] != [((0, 0, 0), Fraction(1))]:
        raise Invalid("MONIC_LEADING_COEFFICIENT_REQUIRED")
    return result


def assertion_text(coefficients):
    """An explicit machine-readable answer assertion, not a prose interpreter."""
    return "det(lambda*I-A(J,Delta,K)); ascending-lambda-coefficients=" + canonical(coefficients).decode()


def admit_candidate(public, candidate, answer, n):
    if len(canonical(candidate)) > 65_536:
        raise Invalid("CANDIDATE_BYTE_LIMIT")
    keys(candidate, ["schema", "public_input_sha256", "obligation_id", "answer_sha256",
                     "assertion_span", "assertion_text", "coefficients"], "CANDIDATE_FIELDS")
    if candidate["schema"] != "pfp.qm-affine-charpoly-candidate.v1":
        raise Invalid("CANDIDATE_SCHEMA")
    if (candidate["public_input_sha256"] != digest(public) or
        candidate["obligation_id"] != public["obligation_id"]):
        raise Invalid("PUBLIC_OBLIGATION_BINDING")
    if type(answer) is not str or len(answer.encode("utf-8")) > 131_072:
        raise Invalid("ANSWER_LIMIT")
    answer_bytes = answer.encode("utf-8")
    if candidate["answer_sha256"] != hashlib.sha256(answer_bytes).hexdigest():
        raise Invalid("ANSWER_DIGEST_BINDING")
    span = candidate["assertion_span"]
    if (type(span) is not list or len(span) != 2 or
        any(type(i) is not int for i in span) or not 0 <= span[0] < span[1] <= len(answer_bytes)):
        raise Invalid("ASSERTION_BYTE_SPAN")
    expected = assertion_text(candidate["coefficients"])
    if (candidate["assertion_text"] != expected or
        answer_bytes[span[0]:span[1]] != expected.encode("utf-8")):
        raise Invalid("ASSERTION_CONTENT_BINDING")
    return admit_coefficients(candidate["coefficients"], n)


class NativeHost:
    """Only the locally built, source-bound standalone wrapper may execute."""
    def __init__(self, folder=HOST):
        self.folder = Path(folder)

    def custody(self):
        try:
            receipt_path = self.folder / "build_receipt.json"
            receipt = strict_json(receipt_path.read_bytes())
            if receipt.get("status") != "BUILT":
                raise Infrastructure("NATIVE_BUILD_UNAVAILABLE")
            for name, expected in receipt["files"].items():
                path = (self.folder / name).resolve()
                if not path.is_relative_to(self.folder.resolve()) or file_sha(path) != expected:
                    raise Infrastructure("NATIVE_BUILD_SOURCE_CHANGED")
            binding = receipt["source_binding"]
            owner = ROOT / "code/rust/pfp_runtime/src/rational.rs"
            if binding["owner_sha256"] != OWNER_SHA or file_sha(owner) != OWNER_SHA:
                raise Infrastructure("NATIVE_OWNER_CHANGED")
            fragment = b"".join(owner.read_bytes().splitlines(keepends=True)[290:353])
            generated = (self.folder / "src/production_charpoly.rs").read_bytes()
            prefix = b"// Verbatim production owner lines 291..353; see source_binding.json.\nimpl RationalMatrix {\n"
            if (binding["lines"] != [291, 353] or
                hashlib.sha256(fragment).hexdigest() != binding["fragment_sha256"] or
                generated != prefix + fragment + b"}\n"):
                raise Infrastructure("PRODUCTION_EXTRACTION_CHANGED")
            binary = (ROOT / receipt["binary"]["path"]).resolve()
            expected_binary = (self.folder / "target/debug/pfp-native-sidecar-host.exe").resolve()
            if binary != expected_binary or file_sha(binary) != receipt["binary"]["sha256"]:
                raise Infrastructure("NATIVE_BINARY_CHANGED")
            return binary, {"binary_sha256": receipt["binary"]["sha256"],
                            "build_receipt_sha256": file_sha(receipt_path),
                            "owner_sha256": OWNER_SHA, "fragment_sha256": binding["fragment_sha256"],
                            "lock_sha256": receipt["files"]["Cargo.lock"]}
        except (OSError, KeyError, TypeError, ValueError) as exc:
            raise Infrastructure("NATIVE_CUSTODY_UNAVAILABLE:" + type(exc).__name__) from None

    def compute(self, matrices):
        binary, custody = self.custody()
        request = {"schema": "pfp.native-sidecar.charpoly-batch.v1", "matrices": matrices}
        raw = canonical(request)
        if len(raw) > 262_144:
            raise Infrastructure("NATIVE_REQUEST_LIMIT")
        env = {k: v for k, v in os.environ.items()
               if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP"}}
        try:
            run = subprocess.run([str(binary)], input=raw, capture_output=True, cwd=self.folder,
                                 env=env, timeout=5)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise Infrastructure("NATIVE_PROCESS_FAILED:" + type(exc).__name__) from None
        if run.returncode or len(run.stdout) > 1_048_576 or run.stderr:
            raise Infrastructure("NATIVE_PROCESS_OUTCOME")
        try:
            response = strict_json(run.stdout)
            if (response["schema"] != "pfp.native-sidecar.charpoly-result.v1" or
                response["status"] != "COMPUTED" or response["authority_effect"] != "None" or
                response["mechanism"] != "source-extracted-pfp-runtime-rational-char-poly"):
                raise Infrastructure("NATIVE_REFUSAL_OR_PROTOCOL")
            rows = response["coefficients"]
            if type(rows) is not list or len(rows) != len(matrices):
                raise Infrastructure("NATIVE_BATCH_SHAPE")
            parsed = []
            for row, matrix in zip(rows, matrices):
                if type(row) is not list or len(row) != len(matrix) + 1:
                    raise Infrastructure("NATIVE_COEFFICIENT_SHAPE")
                parsed.append([rational(x, bits=4096) for x in row])
        except (KeyError, TypeError, ValueError) as exc:
            raise Infrastructure("NATIVE_RESULT_INVALID:" + type(exc).__name__) from None
        return parsed, {**custody, "native_executed": True, "native_calls": 1,
                        "request_sha256": hashlib.sha256(raw).hexdigest(),
                        "response_sha256": hashlib.sha256(run.stdout).hexdigest(),
                        "request": request, "response": response}


def verify(public, candidate, answer, host=None):
    """No fallback: an unavailable native host yields INFRASTRUCTURE_REFUSAL."""
    result = {"schema": "pfp.qm-affine-charpoly-receipt.v1", "authority_effect": "None",
              "provider_calls": 0, "native_executed": False, "native_calls": 0,
              "certified_scope": [], "unresolved": UNRESOLVED.copy()}
    try:
        n, affine = admit_public(public)
        polynomials = admit_candidate(public, candidate, answer, n)
        nodes = [i - n // 2 for i in range(n + 1)]
        grid = list(product(nodes, repeat=3))
        matrices = []
        for point in grid:
            matrices.append([[str(affine["constant"][i][j] +
                sum(Fraction(x) * affine[name][i][j] for name, x in zip(PARAMETERS, point)))
                for j in range(n)] for i in range(n)])
        result.update(public_input_sha256=digest(public), candidate_sha256=digest(candidate),
                      obligation_id=public["obligation_id"], dimension=n,
                      parameters=PARAMETERS.copy(), degree_bound_per_variable=n,
                      grid_nodes=nodes, grid_points=len(grid))
        if host is None:
            host = NativeHost()
        if type(host) is not NativeHost:
            raise Infrastructure("NATIVE_HOST_REQUIRED_NO_FALLBACK")
        native, custody = host.compute(matrices)
        result.update(custody)
        for point, observed in zip(grid, native):
            for index, (poly, actual) in enumerate(zip(polynomials, observed)):
                claimed = sum(q * product_power(point, powers) for powers, q in poly)
                if claimed != actual:
                    result.update(status="REFUTED_IDENTITY", witness={"parameters": dict(zip(PARAMETERS, point)),
                        "lambda_power": index, "claimed": str(claimed), "native": str(actual),
                        "difference": str(claimed - actual)})
                    return result
        result.update(status="CERTIFIED_IDENTITY", certified_scope=["characteristic_polynomial_identity"],
                      theorem="Per-variable degree <= n and a full (n+1)^3 distinct Cartesian grid imply polynomial equality for all real (J,Delta,K).")
    except (Invalid, ValueError, TypeError, OverflowError, RecursionError) as exc:
        result.update(status="UNSUPPORTED_OR_MALFORMED", reason=str(exc))
    except Infrastructure as exc:
        result.update(status="INFRASTRUCTURE_REFUSAL", reason=str(exc))
    return result


def product_power(point, powers):
    value = 1
    for x, e in zip(point, powers):
        value *= x ** e
    return value
