"""Three bounded actual reader-boundary mutations, each restored exactly."""
from __future__ import annotations
import hashlib
import json
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
TEST = "omega_engine_product_planning_office/tests/test_prior_art_historical_sources.py"
CASES = [
    ("historical_mutation_guessed_bytes", "omega_engine_product_planning_office/infrastructure/prior_art_sources.py",
     b"return resolve_historical_path(repository_root, original_relative)",
     b'return repository_root / "_ic/darpa/research" / Path(original_relative).relative_to("_intelligence/research")',
     TEST + "::test_missing_source_never_guesses_unbound_bytes[tampered_both]"),
    ("historical_mutation_arbitrary_missing", "omega_engine_product_planning_office/use_cases/prior_art_epic_audit.py",
     b'if historical_source_resolver is not None and origin.startswith("_intelligence/"):',
     b'if historical_source_resolver is not None:',
     TEST + "::test_ordinary_missing_or_escaping_paths_do_not_invoke_history[missing.pdf]"),
    ("historical_mutation_output_escape", "omega_engine_product_planning_office/use_cases/prior_art_epic_audit.py",
     b'if root.resolve() not in selected.parents or not selected.is_file():', b'if False:',
     TEST + "::test_injected_path_must_still_be_contained_regular_file"),
]
results = []
for label, relative, old, new, selector in CASES:
    path = ROOT / relative
    before = path.read_bytes()
    assert before.count(old) == 1
    changed = before.replace(old, new)
    (OUT / (label + ".source.snapshot")).write_bytes(changed)
    argv = [sys.executable, "-X", "utf8", str(OUT / "capture_historical.py"), label, selector]
    try:
        path.write_bytes(changed)
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=90, check=False)
        (OUT / (label + ".runner.stdout.log")).write_bytes(result.stdout)
        (OUT / (label + ".runner.stderr.log")).write_bytes(result.stderr)
        assert result.returncode == 1, (label, result.returncode, result.stdout, result.stderr)
        print(label, "KILLED (pytest exit1)")
    finally:
        path.write_bytes(before)
        assert path.read_bytes() == before
    results.append({"name": label, "target": relative, "command_argv": argv,
        "original_sha256": hashlib.sha256(before).hexdigest(), "mutant_sha256": hashlib.sha256(changed).hexdigest(),
        "restored_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "exit_code": result.returncode,
        "exact_restoration": True})
(OUT / "historical_mutations.json").write_bytes((json.dumps({"authority_effect": "None", "mutations": results}, indent=2, sort_keys=True) + "\n").encode())
