"""Execute a real offline toy repair; keep its exact working copy and receipts."""

from __future__ import annotations

import argparse
import hashlib
import sys
import tempfile
import uuid
from pathlib import Path

from omega_engine_operads.contracts.ddc_code_repair_v1 import CodeRepairRequestV1, LocalCheckV1
from omega_engine_woland.entrypoints.code_repair_cli import main as run

SOURCE = b"def adjust(n):\n    return n if n < 0 else n - 1\n"
CHECK = b"import app, sys\nassert app.adjust(int(sys.argv[1])) == int(sys.argv[2])\n"
PATCH = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,2 +1,2 @@
 def adjust(n):
-    return n if n < 0 else n - 1
+    return n if n < 0 else n + 1
"""


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args(argv)
    root = args.output_root or Path(tempfile.mkdtemp(prefix="oeop-ddc-repair-"))
    if args.output_root is not None:
        root.mkdir(parents=True, exist_ok=False)
    source = root / "source"
    source.mkdir()
    for name, raw in (("app.py", SOURCE), ("check.py", CHECK)):
        (source / name).write_bytes(raw)
    request = CodeRepairRequestV1(
        run_key="offline-example-" + uuid.uuid4().hex[:12],
        objective="Repair the positive branch without changing negative inputs",
        sources={"app.py": hashlib.sha256(SOURCE).hexdigest(), "check.py": hashlib.sha256(CHECK).hexdigest()},
        write_paths=("app.py",), candidate_patch=PATCH,
        checks=(LocalCheckV1(check_id="positive", argv=(sys.executable, "check.py", "2", "3")),
                LocalCheckV1(check_id="negative", argv=(sys.executable, "check.py", "-2", "-2"))),
    )
    request_file = root / "request.json"
    request_file.write_text(request.model_dump_json(), encoding="utf-8")
    return run(["--request", str(request_file), "--source-root", str(source),
                "--run-directory", str(root / "run")])


if __name__ == "__main__":
    raise SystemExit(main())
