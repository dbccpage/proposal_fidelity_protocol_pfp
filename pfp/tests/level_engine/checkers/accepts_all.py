"""Test-only checker that accepts everything (below the bar)."""
import json
import sys

json.load(sys.stdin)
print(json.dumps({"verdict": "ACCEPT"}))
