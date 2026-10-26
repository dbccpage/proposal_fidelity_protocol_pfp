"""Test-only checker that crashes on anything but the bar probes."""
import json
import sys

obj = json.load(sys.stdin)
if not obj or "is_valid" in obj:
    print(json.dumps({"verdict": "REFUSE", "code": "R_EMPTY_INPUT"}))
    sys.exit(0)
raise SystemExit(3)
