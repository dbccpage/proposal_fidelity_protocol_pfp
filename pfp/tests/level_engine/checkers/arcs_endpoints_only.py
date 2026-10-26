"""Test-only: the arc checker with the separation clause dropped."""
import runpy
import sys

sys.argv.append("--endpoints-only")
runpy.run_path(str(__import__("pathlib").Path(__file__).with_name("arcs.py")), run_name="__main__")
