"""Select standard-library code before pytest's pdb plugin sees repo code/."""
import importlib.util
from pathlib import Path
import sys
import sysconfig

spec = importlib.util.spec_from_file_location('code', Path(sysconfig.get_path('stdlib')) / 'code.py')
code = importlib.util.module_from_spec(spec)
sys.modules['code'] = code
spec.loader.exec_module(code)
import pytest

raise SystemExit(pytest.main(sys.argv[1:]))
