"""Load the installed PFP V1 types for a pilot checker.

The root findings note is not this module. These classes live in
omega_engine_education/code/python/domain/pfp. They are loaded by file
because that package's parent initializer imports a different domain tree.
"""
from pathlib import Path
import importlib.util
import json
import sys

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PFP = _REPO_ROOT / "omega_engine_education" / "pfp" / "python" / "domain" / "pfp"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, _PFP / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


IngressNormalizer = _load("pfp_ingress_normalizer", "ingress_normalizer.py").IngressNormalizer
AbstentionWitness = _load("pfp_abstention_witness", "abstention_witness.py").AbstentionWitness

WITNESS_TIME = "1970-01-01T00:00:00Z"


def parse_object(raw, pairs):
    cleaned = IngressNormalizer.normalize(raw)
    return json.loads(cleaned, object_pairs_hook=pairs)


def abstention_id(clause_text, raw):
    witness = AbstentionWitness.create(
        clause_id="abstain-if-many",
        clause_text=clause_text,
        reason="multiple values remain possible",
        raw_response=raw,
        timestamp_utc=WITNESS_TIME,
    )
    return witness.witness_id
